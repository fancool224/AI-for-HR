---
name: hr-turnover-analysis
description: 基于流失台账的员工流失分析技能。输入27列结构化流失台账（Excel/CSV），自动产出多维切片(56张)、文本三阶交叉验证、LLM主题聚类、风险预警、BI Markdown 仪表盘。适用于：(1) 用户上传流失台账数据要求做月度流失分析；(2) 需要识别哪个部门/岗位/上级/司龄段流失严重；(3) 需要从员工面谈/上级意见文本里挖隐性原因；(4) 需要产出可放进经营分析报告的流失模块。触发词：流失分析、离职分析、流失台账、流失报告、turnover analysis、attrition analysis。
---

# 流失分析 Skill

## 执行方式（推荐）

**用户提供台账文件后，一条命令跑完全流程**：

```bash
cd skills/hr-turnover-analysis/scripts
python3 run_analysis.py <台账文件路径> --month YYYY-MM --output <输出目录>
```

输出文件：
- `slices.md` — 全部切片（56张交叉表）
- `text_analysis.md` — 三阶交叉验证 + 关键词归类
- `dashboard.md` — BI 可视化仪表盘
- `summary.json` — 结构化摘要（供后续 LLM 收束用）
- `normalized.csv` — 标准化明细

## LLM 介入的 2 个环节（其余全部代码完成）

### 环节 A：文本主题聚类（强制每月跑）
脚本会自动把同月所有 `员工本人离职面谈` 文本聚合后调 LLM。Agent 收到提示时按 `references/llm-prompt-topic-clustering.md` 执行。

### 环节 B：收束 3 条核心问题
脚本会把 `summary.json` 喂给 Agent，Agent 按 `references/llm-prompt-problem-synthesis.md` 收束最多 3 条核心问题。

## 台账字段标准（27列）

输入文件应包含的列见 `references/data-schema.md`。脚本支持字段名模糊匹配，缺字段时自动跳过相关切片。

## 司龄分段（6段）

`<1月` / `1-3月` / `3-6月` / `6-12月` / `12-24月` / `24月+`

## 交叉分析全集（56张，自动按信号强度筛选呈现）

详见 `references/cross-analysis-matrix.md`（仅在 Agent 需要解释切片选择逻辑时阅读）。

## 工作流程

```
台账输入
  ↓
run_analysis.py（一条命令）
  ├─ 数据标准化
  ├─ 56 张切片计算
  ├─ 三阶交叉验证识别
  ├─ 关键词归类（本月真实占比）
  ├─ 风险群体扫描
  └─ BI Markdown 渲染
  ↓
text_analysis.md / slices.md / dashboard.md / summary.json
  ↓
LLM 介入环节 A：主题聚类（用 references/llm-prompt-topic-clustering.md）
LLM 介入环节 B：问题收束（用 references/llm-prompt-problem-synthesis.md）
  ↓
完整月度流失分析报告
```

## 重要约束

1. **不预设占比** — 所有占比都是本月真实算出的，不是基线对比
2. **核心问题最多 3 条** — 强收束，按信号强度排序
3. **每月跑一次 LLM 文本聚类** — 不可省略
4. **报告呈现时按信号强度筛选** — 56 张切片只展示有信号的 8-12 张
