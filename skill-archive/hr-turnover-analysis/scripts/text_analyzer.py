#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本分析模块

三步走：
1. 关键词归类（本月真实占比，不预设基线）
2. 三阶交叉验证（员工本人 / 直接上级 / 隔级上级）—— 自动判一致/矛盾/缺失
3. 准备 LLM 输入文本块（供 Agent 后续调用 LLM 做主题聚类）
"""

import re

import pandas as pd

# ============================================================
# 关键词归类规则（仅用于"归类"，不预设占比）
# ============================================================
ACTIVE_CAUSE_RULES = [
    ("职业发展",    ["晋升", "发展", "前景", "成长", "上升", "路径", "机会"]),
    ("薪酬福利",    ["薪", "工资", "福利", "待遇", "钱", "收入", "奖金"]),
    ("工作压力",    ["累", "压力", "加班", "强度", "辛苦", "繁重"]),
    ("工作时间",    ["夜班", "倒班", "排班", "时间长", "上夜", "早班", "通勤"]),
    ("工作环境",    ["环境", "氛围", "同事", "上级", "领导", "管理", "团队"]),
    ("工作内容",    ["内容", "配合", "协同", "不喜欢", "兴趣"]),
    ("家庭原因",    ["家", "结婚", "生育", "搬", "异地", "照顾", "老人", "孩子"]),
    ("身体原因",    ["身体", "健康", "怀孕", "病", "腰", "颈椎"]),
    ("学习深造",    ["考研", "考公", "学习", "进修", "读书"]),
    ("创业",        ["创业", "自己干", "自主"]),
    ("外部机会",    ["新工作", "新机会", "offer", "跳槽", "更好"]),
]

PASSIVE_CAUSE_RULES = [
    ("违规违纪",    ["违纪", "违规", "旷工", "偷", "打架", "过失", "处分"]),
    ("岗位不胜任",  ["不胜任", "能力不", "业绩不达", "完不成", "效率低", "差错"]),
    ("评估未通过",  ["评估", "考核未", "晋升评估", "试用期评估"]),
    ("身体不胜任",  ["身体"]),
    ("制度不认可",  ["制度", "不认可", "拒绝", "不愿"]),
    ("薪酬调整",    ["薪酬调整", "降薪"]),
    ("职业匹配",    ["匹配", "方向不一致"]),
]


def _normalize_text(s):
    if pd.isna(s):
        return ""
    return re.sub(r"\s+", " ", str(s).strip())


def _classify_cause(raw_text, flow_type):
    text = _normalize_text(raw_text)
    if not text or text.lower() in ["nan", "none", "/", "-"]:
        return "未分类"
    rules = ACTIVE_CAUSE_RULES if flow_type == "主动" else PASSIVE_CAUSE_RULES
    for std, kws in rules:
        if any(kw in text for kw in kws):
            return std
    return "其他"


# ============================================================
# 三阶交叉验证
# ============================================================
def _three_stage_pattern(stage1, stage2, stage3):
    """根据三段文本判断模式：一致 / 矛盾 / 缺失"""
    has1 = bool(_normalize_text(stage1))
    has2 = bool(_normalize_text(stage2))
    has3 = bool(_normalize_text(stage3))
    missing_count = 3 - (has1 + has2 + has3)
    if missing_count >= 2:
        return "缺失"
    if missing_count == 1:
        return "部分缺失"

    # 三段都有 → 看关键词重合度（粗判）
    t1 = set(re.findall(r"[\u4e00-\u9fff]+", str(stage1)))
    t2 = set(re.findall(r"[\u4e00-\u9fff]+", str(stage2)))
    t3 = set(re.findall(r"[\u4e00-\u9fff]+", str(stage3)))
    overlap_12 = len(t1 & t2) / max(min(len(t1), len(t2)), 1)
    overlap_13 = len(t1 & t3) / max(min(len(t1), len(t3)), 1)
    overlap_23 = len(t2 & t3) / max(min(len(t2), len(t3)), 1)
    avg_overlap = (overlap_12 + overlap_13 + overlap_23) / 3

    if avg_overlap >= 0.3:
        return "一致"
    return "矛盾"


# ============================================================
# 主入口
# ============================================================
def run_text_analysis(df: pd.DataFrame, target_month: str):
    """
    返回：
        text_md: 文本分析报告 Markdown
        text_data: 结构化数据（含三阶验证统计 + LLM_INPUT 文本块）
    """
    df_month = df[df["月份_str"] == target_month].copy()

    # ------- Step 1: 关键词归类 -------
    if "流失原因" in df_month.columns:
        df_month["流失原因_自动归类"] = df_month.apply(
            lambda r: _classify_cause(r.get("流失原因"), r.get("流失类别", "未知")),
            axis=1,
        )
    else:
        df_month["流失原因_自动归类"] = "未分类"

    # 本月真实占比
    cause_dist = {}
    for ft in ["主动", "被动"]:
        sub = df_month[df_month["流失类别"] == ft]
        if not sub.empty:
            d = sub["流失原因_自动归类"].value_counts()
            cause_dist[ft] = [
                {"分类": k, "人数": int(v), "占比": f"{v/len(sub)*100:.1f}%"}
                for k, v in d.items()
            ]
        else:
            cause_dist[ft] = []

    # 用户已有"流失原因分类"列 vs 自动归类对比
    consistency = None
    if "流失原因分类" in df_month.columns:
        both = df_month[df_month["流失原因分类"].notna()]
        if not both.empty:
            match = (both["流失原因分类"].astype(str).str.strip() ==
                     both["流失原因_自动归类"]).sum()
            consistency = {
                "已分类人数": int(len(both)),
                "归类一致": int(match),
                "归类一致率": f"{match/len(both)*100:.1f}%",
            }

    # ------- Step 2: 三阶交叉验证 -------
    three_stage_stats = {"一致": 0, "矛盾": 0, "部分缺失": 0, "缺失": 0}
    three_stage_rows = []
    if all(c in df_month.columns for c in ["员工本人离职面谈", "直接上级意见", "隔级上级意见"]):
        for _, r in df_month.iterrows():
            pattern = _three_stage_pattern(
                r.get("员工本人离职面谈"),
                r.get("直接上级意见"),
                r.get("隔级上级意见"),
            )
            three_stage_stats[pattern] += 1
            three_stage_rows.append({
                "姓名": r.get("姓名", ""),
                "二级部门": r.get("二级部门", ""),
                "岗位": r.get("岗位", ""),
                "流失类别": r.get("流失类别", ""),
                "模式": pattern,
                "员工本人": _normalize_text(r.get("员工本人离职面谈"))[:80],
                "直接上级": _normalize_text(r.get("直接上级意见"))[:80],
                "隔级上级": _normalize_text(r.get("隔级上级意见"))[:80],
            })

    # ------- Step 3: 准备 LLM 输入（供 Agent 后续做主题聚类）-------
    # 为节省 token，只保留必要字段
    llm_input_records = []
    if "员工本人离职面谈" in df_month.columns:
        for _, r in df_month.iterrows():
            text = _normalize_text(r.get("员工本人离职面谈"))
            if not text or len(text) < 5:
                continue
            llm_input_records.append({
                "姓名": str(r.get("姓名", "")),
                "司龄段": str(r.get("司龄段", "")),
                "二级部门": str(r.get("二级部门", "")),
                "岗位": str(r.get("岗位", "")),
                "流失类别": str(r.get("流失类别", "")),
                "面谈摘要": text[:500],  # 截断防止token爆炸
            })

    # ------- 生成 Markdown -------
    md = [f"# 文本分析报告（{target_month}）\n\n",
          f"**本月样本数**：{len(df_month)} 人\n\n"]

    # Step 1
    md.append("## 1. 关键词归类（本月真实占比）\n\n")
    md.append("> ⚠️ 此处占比为本月数据真实算出，不预设基线。\n\n")
    for ft in ["主动", "被动"]:
        md.append(f"### {ft}流失\n\n")
        rows = cause_dist.get(ft, [])
        if rows:
            md.append("| 分类 | 人数 | 占比 |\n| --- | --- | --- |\n")
            for r in rows:
                md.append(f"| {r['分类']} | {r['人数']} | {r['占比']} |\n")
        else:
            md.append("_(无数据)_\n")
        md.append("\n")

    if consistency:
        md.append("### 自动归类 vs 用户已分类 一致性\n\n")
        md.append(f"- 已分类人数：{consistency['已分类人数']}\n")
        md.append(f"- 归类一致：{consistency['归类一致']}\n")
        md.append(f"- 一致率：**{consistency['归类一致率']}**\n\n")

    # Step 2
    md.append("\n## 2. 三阶交叉验证\n\n")
    total_ts = sum(three_stage_stats.values())
    if total_ts > 0:
        md.append("| 模式 | 人数 | 占比 | 含义 |\n| --- | --- | --- | --- |\n")
        meanings = {
            "一致":     "三方口径一致 → 真因明确",
            "矛盾":     "员工与上级口径不一致 → **本月深挖对象**",
            "部分缺失": "1阶未给意见 → 信息不完整",
            "缺失":     "≥2阶无意见 → **管理盲区**",
        }
        for k in ["一致", "矛盾", "部分缺失", "缺失"]:
            v = three_stage_stats[k]
            pct = f"{v/total_ts*100:.1f}%" if total_ts else "-"
            md.append(f"| {k} | {v} | {pct} | {meanings[k]} |\n")
        md.append("\n")

        # 矛盾型清单（重点）
        conflict_rows = [r for r in three_stage_rows if r["模式"] == "矛盾"]
        if conflict_rows:
            md.append("### ⚠️ 矛盾型清单（本月深挖对象）\n\n")
            md.append("| 姓名 | 部门 | 岗位 | 类别 | 员工本人 | 直接上级 | 隔级上级 |\n")
            md.append("| --- | --- | --- | --- | --- | --- | --- |\n")
            for r in conflict_rows[:20]:
                md.append(f"| {r['姓名']} | {r['二级部门']} | {r['岗位']} | "
                          f"{r['流失类别']} | {r['员工本人']} | {r['直接上级']} | "
                          f"{r['隔级上级']} |\n")
            md.append("\n")

        # 缺失型清单（管理盲区）
        missing_rows = [r for r in three_stage_rows if r["模式"] in ["缺失", "部分缺失"]]
        if missing_rows:
            md.append("### ❓ 缺失/部分缺失清单（管理盲区）\n\n")
            md.append("| 姓名 | 部门 | 岗位 | 类别 | 模式 |\n| --- | --- | --- | --- | --- |\n")
            for r in missing_rows[:20]:
                md.append(f"| {r['姓名']} | {r['二级部门']} | {r['岗位']} | "
                          f"{r['流失类别']} | {r['模式']} |\n")
            md.append("\n")
    else:
        md.append("_(无三阶数据，请检查台账"
                  "员工本人离职面谈/直接上级意见/隔级上级意见 三列)_\n\n")

    # Step 3: LLM 输入提示
    md.append("\n## 3. LLM 主题聚类输入（待 Agent 调用）\n\n")
    md.append(f"**待聚类文本数**：{len(llm_input_records)} 条\n\n")
    md.append("> Agent 应读取 summary.json 中的 `text_analysis.llm_input_records` 字段，\n")
    md.append("> 按 `references/llm-prompt-topic-clustering.md` 中的提示词进行主题聚类。\n\n")

    text_data = {
        "month": target_month,
        "cause_distribution": cause_dist,
        "consistency": consistency,
        "three_stage": {
            "consistent": three_stage_stats["一致"],
            "conflict":   three_stage_stats["矛盾"],
            "partial":    three_stage_stats["部分缺失"],
            "missing":    three_stage_stats["缺失"],
            "conflict_rows": [r for r in three_stage_rows if r["模式"] == "矛盾"],
            "missing_rows":  [r for r in three_stage_rows if r["模式"] in ["缺失", "部分缺失"]],
        },
        "llm_input_records": llm_input_records,
    }

    return "".join(md), text_data
