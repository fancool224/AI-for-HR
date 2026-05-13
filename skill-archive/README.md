# Skill 存档区

> **版本：** v1.0.0 | **更新时间：** 2026-05-13 17:12 | **维护者：** Master Agent 🎯

---

## 目录说明

```
skill-archive/
├── probation-warning/          # 试用期评估预警 Skill
│   ├── SKILL.md               # Skill 定义文件
│   ├── references/             # 参考文档
│   │   ├── api_reference.md   # API 参考
│   │   └── column_mapping.md  # 字段映射
│   └── scripts/                # 脚本
│       └── filter_eval.py     # 筛选评估脚本
│
└── hr-turnover-analysis/       # 员工流失分析 Skill
    ├── SKILL.md               # Skill 定义文件
    ├── references/             # 参考文档
    │   ├── cross-analysis-matrix.md    # 三阶交叉验证矩阵
    │   ├── data-schema.md               # 数据结构定义
    │   ├── intervention-roadmap.md     # 干预路径图
    │   ├── llm-prompt-problem-synthesis.md   # LLM问题合成提示
    │   └── llm-prompt-topic-clustering.md    # LLM主题聚类提示
    └── scripts/                # 分析脚本
        ├── bi_renderer.py      # BI渲染器
        ├── data_loader.py      # 数据加载器
        ├── risk_scanner.py     # 风险扫描器
        ├── run_analysis.py     # 运行分析主脚本
        ├── slicer.py           # 数据切片器
        └── text_analyzer.py    # 文本分析器
```

---

## 状态说明

| Skill名称 | 状态 | 说明 |
|-----------|------|------|
| 试用期评估预警 | 📦 存档中 | 等待形成Agent |
| 员工流失分析 | 📦 存档中 | 等待形成Agent |

---

## 安装说明

当Skill需要激活时：

1. **试用期评估预警** → 使用 agent-importer skill 导入
2. **员工流失分析** → 使用 agent-importer skill 导入

---

## 备注

- 腾讯文档存档区（待创建）：等腾讯文档连接恢复后，将在此目录下创建对应的云端存档
- Skill状态变更时请同步更新本文档

---

_Last updated: 2026-05-13 17:12 | Master Agent 🎯_
