# Agent 分发与使用指南

> 适用于：通过 WorkBuddy 使用本项目的其他成员（Collaborator）。

---

## 快速开始

### 方式一：通过 hr-agent-participant Skill 加入（推荐）

1. 在 WorkBuddy 中说："加入TOP项目" / "参与人事部项目"
2. 系统加载 `hr-agent-participant` Skill，自动注册到项目
3. 可立即使用小绿 🌱 等已配置的 Agent

### 方式二：导入完整 Agent 配置包

1. 获取项目维护者提供的 `.tar.gz` 配置包
2. 在 WorkBuddy 中导入（agent-importer Skill）
3. 适用于需要完整控制 Agent 配置的场景

### 方式三：只读参考

- 直接阅读本项目中的 `.md` 文件和 prompt 设计
- 复制适合自己场景的 prompt 到自己的 Agent 使用

---

## 目录结构说明

```
TOP-HR-Agent-basic/
├── agents/              # 各专业 Agent 配置（小绿 🌱 等）
├── master-agent/        # 主控 Agent（项目发起人使用）
├── shared-context/      # 协作共享上下文（仅本地，不推送）
├── scripts/             # 辅助脚本
├── state.json           # Agent 注册表（自动维护）
├── PROJECT_LOGIC.md     # 系统逻辑文档
└── README.md            # 项目说明
```

---

## 触发 Agent 的方式

| 触发词 | 加载的 Agent |
|--------|-------------|
| "人才盘点"、"落位"、"九宫格" | hrbp-inventory Skill |
| "生成IDP"、"培养方案" | idp-design Skill |
| "胜任力"、"怎么评"、"能力词典" | coe-modeling Skill |
| "同步"、"检查更新" | agent-syncer Skill |
| "导入配置" | agent-importer Skill |

---

## 常见问题

**Q: 加入后我的 WorkBuddy 原有配置会丢失吗？**
> 不会。使用 hr-agent-participant 方式不覆盖原有身份，Agent 之间相互独立。

**Q: GitHub Token 怎么配置？**
> 在导入流程中按提示配置，或参考项目 README 中的 Token 设置说明。

**Q: 腾讯文档是什么用途？**
> 存放 Collaborator 的工作记录、进展、上下文摘要，由 Master Agent 每周合并到本地。

---

_本文件由 Master Agent 维护，版本跟随 state.json 的 system_version。_
