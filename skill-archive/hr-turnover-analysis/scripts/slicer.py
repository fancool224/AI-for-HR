#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
切片引擎 — 56 张交叉表

设计原则：
- 全部自动生成，不依赖配置
- 每张切片附带"信号强度"评分（≥3=强信号、2=中等、1=弱、0=无信号）
- 输出时按信号强度排序，弱信号折叠

信号强度规则：
- 样本量 N >= 5
- 集中度（Top1 占比） >= 40%
- 部门/岗位/上级 出现"流失 >= 3 人"
- 时间趋势出现"环比 >= 30%"
"""

from collections import OrderedDict

import pandas as pd

from data_loader import TENURE_ORDER


# ============================================================
# Markdown 表格生成（不依赖 tabulate）
# ============================================================
def _md_table(df: pd.DataFrame, max_rows=None) -> str:
    if df is None or df.empty:
        return "_(无数据)_\n"
    if max_rows:
        df = df.head(max_rows)
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |",
             "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        cells = []
        for v in row.values:
            if pd.isna(v):
                cells.append("")
            else:
                cells.append(str(v).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _signal_score(df: pd.DataFrame, value_col="合计") -> int:
    """评估切片信号强度。"""
    if df is None or df.empty or value_col not in df.columns:
        return 0
    total = df[value_col].sum()
    if total < 3:
        return 0
    score = 0
    if total >= 10:
        score += 1
    if total >= 20:
        score += 1
    top1 = df[value_col].max() if len(df) else 0
    if top1 / max(total, 1) >= 0.4:
        score += 1
    if (df[value_col] >= 3).sum() >= 2:
        score += 1
    return score


def _has_col(df, *cols):
    return all(c in df.columns and df[c].notna().any() for c in cols)


# ============================================================
# 切片构造器
# ============================================================
def _single_dim(df, col, sort_order=None):
    """单维分布。"""
    if not _has_col(df, col):
        return None
    sub = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
    if sub.empty:
        return None
    out = sub.groupby(col).size().reset_index(name="合计")
    out["占比"] = (out["合计"] / out["合计"].sum() * 100).round(1).astype(str) + "%"
    if sort_order:
        cat = pd.CategoricalDtype(sort_order, ordered=True)
        out[col] = out[col].astype(cat)
        out = out.sort_values(col).dropna(subset=[col])
    else:
        out = out.sort_values("合计", ascending=False)
    return out.reset_index(drop=True)


def _two_dim(df, row_col, col_col, row_order=None, topn=None):
    """二维交叉。"""
    if not _has_col(df, row_col, col_col):
        return None
    sub = df[df[row_col].notna() & df[col_col].notna()]
    sub = sub[(sub[row_col].astype(str).str.strip() != "") &
              (sub[col_col].astype(str).str.strip() != "")]
    if sub.empty:
        return None
    out = sub.groupby([row_col, col_col]).size().unstack(fill_value=0)
    out["合计"] = out.sum(axis=1)
    if row_order:
        out = out.reindex([x for x in row_order if x in out.index])
    else:
        out = out.sort_values("合计", ascending=False)
    if topn:
        out = out.head(topn)
    return out.reset_index()


def _three_dim(df, dim_a, dim_b, dim_c, topn=15):
    """三维交叉。"""
    if not _has_col(df, dim_a, dim_b, dim_c):
        return None
    sub = df[df[dim_a].notna() & df[dim_b].notna() & df[dim_c].notna()]
    if sub.empty:
        return None
    out = sub.groupby([dim_a, dim_b, dim_c]).size().reset_index(name="人数")
    out = out.sort_values("人数", ascending=False).head(topn)
    return out


# ============================================================
# 全集切片定义（56 张）
# ============================================================
def _build_all_slices(df_month: pd.DataFrame, df_all: pd.DataFrame):
    """构建所有切片，返回 OrderedDict[slice_id] = {title, df, score, group}"""
    R = OrderedDict()

    def add(sid, title, group, df_slice, value_col="合计"):
        R[sid] = {
            "title": title,
            "group": group,
            "df": df_slice,
            "score": _signal_score(df_slice, value_col) if df_slice is not None else 0,
        }

    # ===== 单维分布（10）=====
    add("A1", "流失类别分布", "单维分布", _single_dim(df_month, "流失类别"))
    add("A2", "司龄段分布", "单维分布", _single_dim(df_month, "司龄段", TENURE_ORDER))
    add("A3", "二级部门分布", "单维分布", _single_dim(df_month, "二级部门"))
    add("A4", "岗位分布 Top5", "单维分布",
        _single_dim(df_month, "岗位").head(5) if _single_dim(df_month, "岗位") is not None else None)
    add("A5", "门店分布 Top5", "单维分布",
        _single_dim(df_month, "门店").head(5) if _single_dim(df_month, "门店") is not None else None)
    add("A6", "全职/兼职分布", "单维分布", _single_dim(df_month, "全职兼职"))
    add("A7", "是否高潜分布", "单维分布", _single_dim(df_month, "是否高潜"))
    add("A8", "年龄段分布", "单维分布", _single_dim(df_month, "年龄段"))
    add("A9", "学历分布", "单维分布", _single_dim(df_month, "学历"))
    add("A10", "类别（门店/物流/总部）分布", "单维分布", _single_dim(df_month, "类别"))

    # ===== 一级交叉：核心轴 × 核心轴（5）=====
    add("B1", "流失类别 × 司龄段", "核心交叉",
        _two_dim(df_month, "司龄段", "流失类别", TENURE_ORDER))
    add("B2", "流失原因分类 × 流失类别", "核心交叉",
        _two_dim(df_month, "流失原因分类", "流失类别"))
    add("B3", "流失原因分类 × 司龄段", "核心交叉",
        _two_dim(df_month, "流失原因分类", "司龄段"))
    add("B4", "月份 × 流失类别（近6月）", "时间趋势",
        _two_dim(df_all, "月份_str", "流失类别"))
    add("B5", "月份 × 流失原因分类（近6月）", "时间趋势",
        _two_dim(df_all, "月份_str", "流失原因分类"))

    # ===== 二级交叉：核心轴 × 组织轴（12）=====
    add("C1", "流失类别 × 类别", "组织交叉", _two_dim(df_month, "类别", "流失类别"))
    add("C2", "流失类别 × 一级部门", "组织交叉", _two_dim(df_month, "一级部门", "流失类别"))
    add("C3", "流失类别 × 二级部门", "组织交叉", _two_dim(df_month, "二级部门", "流失类别"))
    add("C4", "流失类别 × 岗位 Top10", "组织交叉", _two_dim(df_month, "岗位", "流失类别", topn=10))
    add("C5", "流失类别 × 门店 Top10", "组织交叉", _two_dim(df_month, "门店", "流失类别", topn=10))
    add("C6", "流失类别 × 全职兼职", "组织交叉", _two_dim(df_month, "全职兼职", "流失类别"))
    add("C7", "司龄段 × 二级部门", "组织交叉", _two_dim(df_month, "二级部门", "司龄段"))
    add("C8", "司龄段 × 岗位 Top10", "组织交叉", _two_dim(df_month, "岗位", "司龄段", topn=10))
    add("C9", "司龄段 × 门店 Top10", "组织交叉", _two_dim(df_month, "门店", "司龄段", topn=10))
    add("C10", "司龄段 × 全职兼职", "组织交叉", _two_dim(df_month, "全职兼职", "司龄段"))
    add("C11", "流失原因分类 × 二级部门", "组织交叉", _two_dim(df_month, "二级部门", "流失原因分类"))
    add("C12", "流失原因分类 × 岗位 Top10", "组织交叉", _two_dim(df_month, "岗位", "流失原因分类", topn=10))

    # ===== 三级交叉：核心轴 × 人物轴（10）=====
    add("D1", "流失类别 × 是否高潜", "人物交叉", _two_dim(df_month, "是否高潜", "流失类别"))
    add("D2", "流失类别 × 年龄段", "人物交叉", _two_dim(df_month, "年龄段", "流失类别"))
    add("D3", "流失类别 × 学历", "人物交叉", _two_dim(df_month, "学历", "流失类别"))
    add("D4", "流失类别 × 是否完成面谈", "人物交叉", _two_dim(df_month, "是否完成面谈", "流失类别"))
    add("D5", "司龄段 × 是否高潜", "人物交叉", _two_dim(df_month, "是否高潜", "司龄段"))
    add("D6", "司龄段 × 年龄段", "人物交叉", _two_dim(df_month, "年龄段", "司龄段"))
    add("D7", "司龄段 × 学历", "人物交叉", _two_dim(df_month, "学历", "司龄段"))
    add("D8", "流失原因分类 × 是否高潜", "人物交叉", _two_dim(df_month, "是否高潜", "流失原因分类"))
    add("D9", "流失原因分类 × 年龄段", "人物交叉", _two_dim(df_month, "年龄段", "流失原因分类"))
    add("D10", "流失原因分类 × 学历", "人物交叉", _two_dim(df_month, "学历", "流失原因分类"))

    # ===== 四级交叉：核心轴 × 关系轴（4）=====
    add("E1", "直接上级 × 流失类别 Top10", "管理者画像",
        _two_dim(df_month, "直接上级", "流失类别", topn=10))
    add("E2", "直接上级 × 流失原因分类 Top10", "管理者画像",
        _two_dim(df_month, "直接上级", "流失原因分类", topn=10))
    add("E3", "隔级上级 × 流失类别 Top10", "管理者画像",
        _two_dim(df_month, "隔级上级", "流失类别", topn=10))
    add("E4", "直接上级 × 司龄段 Top10", "管理者画像",
        _two_dim(df_month, "直接上级", "司龄段", topn=10))

    # ===== 五级交叉：核心轴 × 流程轴（6）=====
    add("F1", "流失类别 × 工作交接表", "流程合规", _two_dim(df_month, "工作交接表", "流失类别"))
    add("F2", "流失类别 × 离职流程进度", "流程合规", _two_dim(df_month, "离职流程进度", "流失类别"))
    add("F3", "流失类别 × 社保是否解除", "流程合规", _two_dim(df_month, "社保是否解除", "流失类别"))
    add("F4", "流失类别 × 是否正常", "流程合规", _two_dim(df_month, "是否正常", "流失类别"))
    add("F5", "司龄段 × 是否正常", "流程合规", _two_dim(df_month, "是否正常", "司龄段"))
    add("F6", "二级部门 × 是否正常", "流程合规", _two_dim(df_month, "是否正常", "二级部门"))

    # ===== 三维交叉（5）=====
    add("G1", "二级部门 × 司龄段 × 流失类别", "三维定位",
        _three_dim(df_month, "二级部门", "司龄段", "流失类别"), value_col="人数")
    add("G2", "岗位 × 司龄段 × 流失原因分类", "三维定位",
        _three_dim(df_month, "岗位", "司龄段", "流失原因分类"), value_col="人数")
    add("G3", "二级部门 × 岗位 × 流失类别", "三维定位",
        _three_dim(df_month, "二级部门", "岗位", "流失类别"), value_col="人数")
    add("G4", "直接上级 × 司龄段 × 流失类别", "三维定位",
        _three_dim(df_month, "直接上级", "司龄段", "流失类别"), value_col="人数")
    add("G5", "月份 × 二级部门 × 流失类别（近6月）", "三维定位",
        _three_dim(df_all, "月份_str", "二级部门", "流失类别"), value_col="人数")

    # ===== 时间趋势（4）=====
    add("H1", "近6月二级部门趋势", "时间趋势",
        _two_dim(df_all, "月份_str", "二级部门"))
    add("H2", "近6月岗位趋势 Top10", "时间趋势",
        _two_dim(df_all, "月份_str", "岗位", topn=10))
    add("H3", "近6月流失原因分类趋势", "时间趋势",
        _two_dim(df_all, "月份_str", "流失原因分类"))
    add("H4", "近6月司龄段趋势", "时间趋势",
        _two_dim(df_all, "月份_str", "司龄段"))

    return R


# ============================================================
# 主入口
# ============================================================
def generate_all_slices(df: pd.DataFrame, target_month: str):
    """生成所有切片。
    返回：
        slices_md: 全部切片的 Markdown（按 group 分组、按 score 排序）
        slices_data: List[Dict]（结构化摘要，供 summary.json 使用）
    """
    df_month = df[df["月份_str"] == target_month].copy()

    # 近6月数据
    months_sorted = sorted(df["月份_str"].dropna().unique())
    recent6 = months_sorted[-6:] if len(months_sorted) > 6 else months_sorted
    df_recent = df[df["月份_str"].isin(recent6)].copy()

    slices = _build_all_slices(df_month, df_recent)

    # 按 group 分组并按 score 排序
    by_group = OrderedDict()
    for sid, info in slices.items():
        by_group.setdefault(info["group"], []).append((sid, info))
    for g in by_group:
        by_group[g].sort(key=lambda x: -x[1]["score"])

    # 生成 Markdown
    md_parts = [
        f"# 流失切片报告（{target_month}）\n\n",
        f"**本月样本数**：{len(df_month)} 人\n",
        f"**近6月样本数**：{len(df_recent)} 人\n",
        f"**信号强度图例**：⭐⭐⭐⭐ 强 / ⭐⭐⭐ 较强 / ⭐⭐ 中 / ⭐ 弱 / ☆ 无信号\n\n",
    ]
    for group, items in by_group.items():
        md_parts.append(f"\n## {group}\n\n")
        for sid, info in items:
            stars = "⭐" * info["score"] if info["score"] > 0 else "☆"
            md_parts.append(f"\n### [{sid}] {info['title']} {stars}\n\n")
            md_parts.append(_md_table(info["df"]))

    # 结构化摘要
    slices_data = []
    for sid, info in slices.items():
        if info["df"] is None or info["df"].empty:
            continue
        slices_data.append({
            "id": sid,
            "title": info["title"],
            "group": info["group"],
            "score": info["score"],
            "rows": info["df"].head(15).to_dict(orient="records"),
        })
    slices_data.sort(key=lambda x: -x["score"])

    return "".join(md_parts), slices_data
