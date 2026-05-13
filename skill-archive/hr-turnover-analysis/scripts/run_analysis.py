#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流失分析主入口 — 一条命令跑完全流程

Usage:
    python3 run_analysis.py <台账.xlsx|csv> --month YYYY-MM [--output ./out]

输出：
    slices.md          — 56张交叉切片
    text_analysis.md   — 三阶交叉验证 + 关键词归类
    dashboard.md       — BI Markdown 仪表盘
    summary.json       — 结构化摘要（供 LLM 后续使用）
    normalized.csv     — 标准化明细

依赖：pandas, openpyxl
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# 本目录加入 path 以便导入子模块
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import load_taizhang, preprocess
from slicer import generate_all_slices
from text_analyzer import run_text_analysis
from risk_scanner import scan_risk_groups
from bi_renderer import render_dashboard


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="流失台账文件路径 (xlsx/csv)")
    ap.add_argument("--month", required=True, help="目标分析月份 YYYY-MM")
    ap.add_argument("--output", default="./out", help="输出目录")
    ap.add_argument("--sheet", help="Excel sheet 名（可选）")
    args = ap.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 加载 + 标准化
    print(f"[1/5] 加载台账: {args.input}", file=sys.stderr)
    df_raw = load_taizhang(args.input, sheet_name=args.sheet)
    df = preprocess(df_raw)
    df.to_csv(out_dir / "normalized.csv", index=False, encoding="utf-8-sig")
    print(f"      -> {len(df)} 行已标准化", file=sys.stderr)

    # 2. 56 张切片
    print(f"[2/5] 生成切片矩阵...", file=sys.stderr)
    slices_md, slices_data = generate_all_slices(df, args.month)
    (out_dir / "slices.md").write_text(slices_md, encoding="utf-8")
    print(f"      -> {len(slices_data)} 张切片已生成", file=sys.stderr)

    # 3. 文本分析（关键词归类 + 三阶验证）
    print(f"[3/5] 文本分析...", file=sys.stderr)
    text_md, text_data = run_text_analysis(df, args.month)
    (out_dir / "text_analysis.md").write_text(text_md, encoding="utf-8")
    print(f"      -> 三阶验证: 一致型 {text_data['three_stage']['consistent']}, "
          f"矛盾型 {text_data['three_stage']['conflict']}, "
          f"缺失型 {text_data['three_stage']['missing']}", file=sys.stderr)

    # 4. 风险群体扫描
    print(f"[4/5] 风险群体扫描...", file=sys.stderr)
    risks = scan_risk_groups(df, args.month)
    print(f"      -> {len(risks)} 条风险预警", file=sys.stderr)

    # 5. BI Markdown 仪表盘
    print(f"[5/5] 渲染 BI 仪表盘...", file=sys.stderr)
    dashboard_md = render_dashboard(df, args.month, slices_data, text_data, risks)
    (out_dir / "dashboard.md").write_text(dashboard_md, encoding="utf-8")

    # 输出结构化摘要（供 LLM 收束用）
    summary = {
        "month": args.month,
        "total_records": len(df),
        "month_records": int((df["月份_str"] == args.month).sum()),
        "slices_signal": slices_data,           # 已按信号强度排序的切片摘要
        "text_analysis": text_data,             # 三阶验证 + 归类占比 + 待 LLM 聚类的文本
        "risks": risks,                         # 风险群体预警
        "files": {
            "slices_md": str(out_dir / "slices.md"),
            "text_analysis_md": str(out_dir / "text_analysis.md"),
            "dashboard_md": str(out_dir / "dashboard.md"),
            "normalized_csv": str(out_dir / "normalized.csv"),
        },
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )

    print(f"\n✅ 完成。输出目录: {out_dir}/", file=sys.stderr)
    print(f"   - slices.md ({len(slices_data)} 张切片)", file=sys.stderr)
    print(f"   - text_analysis.md", file=sys.stderr)
    print(f"   - dashboard.md", file=sys.stderr)
    print(f"   - summary.json (供 LLM 收束问题用)", file=sys.stderr)
    print(f"\n下一步：", file=sys.stderr)
    print(f"  1) Agent 读取 text_analysis.md 中的 LLM_INPUT 段做主题聚类", file=sys.stderr)
    print(f"  2) Agent 读取 summary.json 收束 3 条核心问题", file=sys.stderr)


if __name__ == "__main__":
    main()
