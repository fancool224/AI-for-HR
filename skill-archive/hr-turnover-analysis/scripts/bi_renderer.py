#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BI Markdown 仪表盘渲染器

输出图表：
1. 顶部摘要卡片（emoji 红绿灯）
2. Mermaid 折线图（近6月趋势）
3. Mermaid 饼图（主动/被动结构、原因构成）
4. ASCII 热力图（部门 × 司龄段）
5. 矛盾型清单卡片
6. 风险预警卡片
"""

import pandas as pd

from data_loader import TENURE_ORDER


def _emoji_for_level(level: str) -> str:
    """根据严重度返回 emoji"""
    return {"🔴": "🔴", "🟠": "🟠", "🟡": "🟡", "🟢": "🟢"}.get(level, "⚪")


def _mermaid_pie(title: str, items: list) -> str:
    """生成 Mermaid 饼图。items=[(label, value), ...]"""
    if not items:
        return ""
    safe_title = title.replace('"', "'")
    lines = ["```mermaid", "pie showData", f'  title {safe_title}']
    for label, value in items:
        if value <= 0:
            continue
        safe_label = str(label).replace('"', "'")
        lines.append(f'  "{safe_label}" : {value}')
    lines.append("```")
    return "\n".join(lines) + "\n\n"


def _mermaid_xy_lines(title: str, x_labels: list, series: dict) -> str:
    """生成 Mermaid xychart-beta 多折线图。series={name: [y...]}"""
    if not x_labels or not series:
        return ""
    safe_title = title.replace('"', "'")
    lines = ["```mermaid", "xychart-beta", f'    title "{safe_title}"']
    x_axis_str = "[" + ", ".join([f'"{x}"' for x in x_labels]) + "]"
    lines.append(f"    x-axis {x_axis_str}")
    all_vals = [v for vs in series.values() for v in vs]
    y_max = max(all_vals) + 5 if all_vals else 10
    lines.append(f"    y-axis \"流失人数\" 0 --> {y_max}")
    for name, ys in series.items():
        ys_str = "[" + ", ".join([str(int(y)) for y in ys]) + "]"
        lines.append(f"    line {ys_str}")
    lines.append("```")
    return "\n".join(lines) + "\n\n"


def _heatmap_md(title: str, df_pivot: pd.DataFrame) -> str:
    """用 emoji 渲染热力图"""
    if df_pivot is None or df_pivot.empty:
        return ""
    max_val = df_pivot.values.max() if df_pivot.values.size else 0
    if max_val == 0:
        return ""

    def emoji(v):
        if v == 0:
            return "⬜"
        ratio = v / max_val
        if ratio >= 0.8:
            return f"🟥{int(v)}"
        if ratio >= 0.5:
            return f"🟧{int(v)}"
        if ratio >= 0.25:
            return f"🟨{int(v)}"
        return f"🟩{int(v)}"

    cols = list(df_pivot.columns)
    lines = [f"#### {title}\n",
             "| 维度 | " + " | ".join(str(c) for c in cols) + " |",
             "| --- | " + " | ".join(["---"] * len(cols)) + " |"]
    for idx, row in df_pivot.iterrows():
        cells = [emoji(v) for v in row.values]
        lines.append(f"| {idx} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n\n"


def render_dashboard(df: pd.DataFrame, target_month: str,
                     slices_data: list, text_data: dict, risks: list) -> str:
    """生成完整 BI 仪表盘 Markdown"""
    df_month = df[df["月份_str"] == target_month].copy()
    total = len(df_month)
    active = int((df_month["流失类别"] == "主动").sum())
    passive = int((df_month["流失类别"] == "被动").sum())

    # 上月对比
    months_sorted = sorted(df["月份_str"].dropna().unique())
    last_total = None
    if target_month in months_sorted:
        idx = months_sorted.index(target_month)
        if idx >= 1:
            last_month = months_sorted[idx - 1]
            last_total = int((df["月份_str"] == last_month).sum())

    mom_str = "—"
    mom_signal = "—"
    if last_total is not None and last_total > 0:
        mom = (total - last_total) / last_total * 100
        mom_str = f"{mom:+.1f}%"
        if mom > 30:
            mom_signal = "🔴 显著上升"
        elif mom > 10:
            mom_signal = "🟠 上升"
        elif mom < -10:
            mom_signal = "🟢 下降"
        else:
            mom_signal = "🟡 平稳"

    md = []
    md.append(f"# 流失分析 BI 仪表盘 — {target_month}\n\n")
    md.append(f"> 自动生成 · 数据样本 {total} 人\n\n")
    md.append("---\n\n")

    # ===== 1. 顶部摘要卡片 =====
    md.append("## 📊 本月概览\n\n")
    md.append("| 指标 | 本月 | 上月 | 环比 | 信号 |\n")
    md.append("| --- | --- | --- | --- | --- |\n")
    md.append(f"| **总流失** | {total} 人 | {last_total if last_total is not None else '—'} 人 | "
              f"{mom_str} | {mom_signal} |\n")
    md.append(f"| **主动流失** | {active} 人 | — | — | "
              f"{f'{active/total*100:.1f}%' if total else '—'} |\n")
    md.append(f"| **被动流失** | {passive} 人 | — | — | "
              f"{f'{passive/total*100:.1f}%' if total else '—'} |\n")

    ts = text_data.get("three_stage", {})
    if ts.get("conflict", 0) or ts.get("consistent", 0):
        md.append(f"| **三阶一致** | {ts.get('consistent', 0)} 人 | — | — | ✅ 真因明确 |\n")
        md.append(f"| **三阶矛盾** | {ts.get('conflict', 0)} 人 | — | — | ⚠️ 待深挖 |\n")
        md.append(f"| **三阶缺失** | {ts.get('missing', 0) + ts.get('partial', 0)} 人 | — | — | ❓ 管理盲区 |\n")
    md.append("\n")

    # ===== 2. 风险预警卡片 =====
    if risks:
        md.append("## 🚨 风险预警\n\n")
        for r in risks:
            md.append(f"- {r['level']} **{r['rule']}** — {r['actual']} （阈值 {r['threshold']}）\n")
            md.append(f"  - 💡 {r['hint']}\n")
        md.append("\n")

    # ===== 3. 主动/被动 饼图 =====
    md.append("## 🥧 流失结构\n\n")
    md.append(_mermaid_pie("主动 vs 被动", [("主动", active), ("被动", passive)]))

    # 司龄结构
    if "司龄段" in df_month.columns:
        tenure_dist = df_month["司龄段"].value_counts()
        tenure_items = [(t, int(tenure_dist.get(t, 0))) for t in TENURE_ORDER
                        if tenure_dist.get(t, 0) > 0]
        if tenure_items:
            md.append(_mermaid_pie("司龄段分布", tenure_items))

    # 原因结构
    cause_dist = text_data.get("cause_distribution", {})
    for ft in ["主动", "被动"]:
        items = cause_dist.get(ft, [])
        if items:
            pie_items = [(r["分类"], r["人数"]) for r in items]
            md.append(_mermaid_pie(f"{ft}流失原因分布", pie_items))

    # ===== 4. 近6月趋势 =====
    md.append("## 📈 近6月趋势\n\n")
    months_sorted = sorted(df["月份_str"].dropna().unique())
    recent6 = months_sorted[-6:] if len(months_sorted) > 6 else months_sorted
    if recent6:
        df_recent = df[df["月份_str"].isin(recent6)]
        # 主动/被动趋势
        pivot = df_recent.groupby(["月份_str", "流失类别"]).size().unstack(fill_value=0)
        pivot = pivot.reindex(recent6).fillna(0)
        series = {}
        if "主动" in pivot.columns:
            series["主动"] = pivot["主动"].tolist()
        if "被动" in pivot.columns:
            series["被动"] = pivot["被动"].tolist()
        if series:
            md.append(_mermaid_xy_lines("主动/被动 流失趋势", recent6, series))

    # ===== 5. 热力图：二级部门 × 司龄段 =====
    if "二级部门" in df_month.columns and "司龄段" in df_month.columns:
        sub = df_month[df_month["二级部门"].notna()]
        if not sub.empty:
            pivot = sub.groupby(["二级部门", "司龄段"]).size().unstack(fill_value=0)
            existing = [t for t in TENURE_ORDER if t in pivot.columns]
            if existing:
                pivot = pivot[existing]
                pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
                md.append("## 🔥 部门 × 司龄段 热力图\n\n")
                md.append(_heatmap_md("数字 = 人数；🟥重灾 🟧中等 🟨关注 🟩轻微", pivot.head(10)))

    # ===== 6. 矛盾型清单（重点关注）=====
    conflict_rows = ts.get("conflict_rows", []) if ts else []
    if conflict_rows:
        md.append("## ⚠️ 三阶矛盾型清单（本月深挖对象）\n\n")
        md.append("| 姓名 | 部门 | 岗位 | 类别 | 员工本人 | 直接上级 |\n")
        md.append("| --- | --- | --- | --- | --- | --- |\n")
        for r in conflict_rows[:10]:
            md.append(f"| {r['姓名']} | {r['二级部门']} | {r['岗位']} | "
                      f"{r['流失类别']} | {r['员工本人']} | {r['直接上级']} |\n")
        md.append("\n")

    # ===== 7. Top 信号切片导航 =====
    if slices_data:
        md.append("## 🔍 强信号切片导航\n\n")
        md.append("详细切片见 [slices.md](./slices.md)。本月强信号 Top10：\n\n")
        top_signals = [s for s in slices_data if s["score"] >= 2][:10]
        for s in top_signals:
            stars = "⭐" * s["score"]
            md.append(f"- `[{s['id']}]` **{s['title']}** {stars}（{s['group']}）\n")
        md.append("\n")

    md.append("---\n\n")
    md.append("> 📁 完整明细：[slices.md](./slices.md) · "
              "[text_analysis.md](./text_analysis.md) · "
              "[summary.json](./summary.json)\n")

    return "".join(md)
