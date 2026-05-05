# AI-for-HR 多Agent协作系统（基础版）

> **版本：** 0.1.0 | **最后更新：** 2026-05-05 | **维护者：** Master Agent 🎯
>
> **GitHub仓库：** https://github.com/fancool224/AI-for-HR

---

## 系统概述

这是一套**多 Agent 协作系统**，专为 HR 团队设计，采用主从架构 + 渐进式加载。

**三个核心设计：**

1. **本地是唯一准确来源** — 完整项目在本地 `TOP-HR-Agent-basic/`，GitHub 只存 Agent 配置，腾讯文档存协作存档
2. **渐进式加载** — 说"做人才盘点"才加载对应 Agent，不把所有配置一次性塞进上下文
3. **git 式协作** — Collaborator 完成任务后存档到腾讯文档，Master Agent 每周合并

---

## 目录结构

```
TOP-HR-Agent-basic/
│
├── agents/                          ← Agent 配置挂载区
│   └── future-work-clarifier/      ← 未来工作厘定助手 🧭
│       ├── SOUL.md                 ← Agent 灵魂（行为准则）
│       ├── IDENTITY.md             ← Agent 身份
│       ├── AGENTS.md               ← 启动行为 + 工作流
│       ├── agent-pack.yaml         ← Agent 主配置
│       ├── skills/                 ← 技能包（coe-modeling/future-workshop/hrpb-inventory/idp-design）
│       └── references/             ← 参考文档（框架/模板/样本）
│
├── master-agent/                   ← 主控 Agent（项目发起人专用）
│   ├── SOUL.md                    ← 主控灵魂
│   ├── IDENTITY.md                ← 主控身份
│   └── weekly-merge.py           ← 每周合并脚本
│
├── shared-context/                 ← 共享上下文（不推 GitHub）
│   ├── SHARED_CONTEXT.md          ← 全局共享知识日志
│   └── version-control/           ← 版本控制
│       └── VERSION                ← 版本号
│
├── scripts/                       ← 工具脚本
│   └── scheduled-merge.sh        ← 每周合并 Shell 脚本
│
├── state.json                      ← 系统状态（Agent 注册表）
├── .gitignore                     ← 保护私有文件
├── .gitattributes                 ← 跨平台行尾统一
├── README.md                      ← 本文件
├── PROJECT_LOGIC.md                ← 完整系统逻辑文档
├── AGENT_DISTRIBUTION_GUIDE.md   ← Agent 分发使用指南
└── PERMISSION_GUIDE.md           ← Agent 权限边界指南
```

> 📖 完整架构逻辑请参阅 `PROJECT_LOGIC.md`

---

## 快速开始

### 1. 克隆仓库（必须）

```bash
git clone https://github.com/fancool224/AI-for-HR.git TOP-HR-Agent-basic
```

### 2. 配置 GitHub Token（推送用）

在 WorkBuddy 中执行一次（只需配置一次）：

```bash
# 方式A：用 git 命令配置（推荐）
git config --global credential.helper store
git push  # 首次会提示输入用户名和 Token

# 方式B：直接配置 Token（非公开仓库需要）
git config --global http.extraHeader "Authorization: Bearer ghp_你的Token"
```

> ⚠️ Token 需有该仓库的 `repo` 权限，在 https://github.com/settings/tokens 生成。

### 3. 导入 Agent 配置

克隆后 `agents/` 下已有配置，无需额外操作。如需添加新 Agent，参见下文「添加新 Agent」。

### 4. 启动 Agent 工作

在 WorkBuddy 中对 Master Agent 🎯 说：

```
"我现在想用未来工作厘定功能"
```

Master Agent 会：
1. 匹配触发词 → 找到 `future-work-clarifier`
2. 检查本地 vs GitHub 版本
3. 加载 Agent 配置（SOUL.md + IDENTITY.md + AGENTS.md）
4. 告知"✅ 已激活未来工作厘定助手 🧭，现在可以开始工作"

---

## 已注册的 Agent

| Agent名 | emoji | 路径 | 触发词 | 状态 |
|---------|-------|------|--------|------|
| 未来工作厘定助手 | 🧭 | `agents/future-work-clarifier/` | 未来工作 / 工作厘定 / AI时代HR变化 / 工作重构 | ✅ 就绪 |

---

## 使用指南

### 启动某个 Agent 工作

1. 对 Master Agent 说："我要做 XXX（触发词）"
2. Master Agent 匹配到对应 Agent
3. 渐进式加载该 Agent 的配置
4. 开始工作

### 查看系统状态

```bash
cat TOP-HR-Agent-basic/state.json
```

### 查看全局上下文

```bash
cat TOP-HR-Agent-basic/shared-context/SHARED_CONTEXT.md
```

### 手动触发每周合并

```bash
python TOP-HR-Agent-basic/master-agent/weekly-merge.py
```

---

## 参与者规范

### ① 使用前：必须克隆 GitHub 仓库

每位参与者首次使用前**必须**先将项目仓库克隆到本地（命令见上方「快速开始」）。

### ② 完成后：必须同步到腾讯文档

每次完成项目工作后，**必须**将以下内容同步到腾讯文档空间（**TOP 人事部agent项目**）：

| 同步内容 | 说明 |
|---------|------|
| 项目产出 | 最终交付物、分析报告 |
| 使用记录 | 工作日志、操作步骤、问题记录 |
| 优化建议 | 发现的问题、改进建议、体验反馈 |

> ⚠️ **注意**：请勿将私有文件（`master-agent/`、`shared-context/`、本地脚本等）上传到腾讯文档空间。

---

## 核心机制

### 渐进式加载

```
用户："我要做人才盘点"
   ↓
Master Agent 检查 SHARED_CONTEXT.md（了解过往上下文）
   ↓
渐进式加载：只读取 agents/<agent>/SOUL.md + IDENTITY.md
   ↓
告知用户："已加载 XX Agent，现在可以开始工作"
   ↓
后续对话按该 Agent 的 SOUL.md 规则执行
   ↓
任务完成后 → 存档到腾讯文档
```

**优点：**
- 不加载全部 Agent → 上下文窗口小
- 按需加载 → 响应快
- 每个 Agent 独立 → 互不干扰

### 每周合并（由 Master Agent 发起）

```
每周五 12:00，Master Agent 检查：
  1. 扫描腾讯文档中的工作记录
  2. 读取 shared-context/version-control/VERSION 当前版本号
  3. 决定是否合并（询问用户或直接执行）
  4. 合并后：
      - 更新 VERSION 文件（版本号 +1）
      - 写入 master-agent/merge-log/YYYY-MM-DD.md
      - 标记腾讯文档记录为已合并
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 0.1.0 | 2026-05-05 | 初始化基础版，挂载未来工作厘定助手，补齐发布文档 |

---

## 注意事项

1. **本地是唯一最新准确信息来源**：GitHub 是克隆源，腾讯文档是协作存档
2. **GitHub 不提供共享上下文**：`shared-context/` 和 `master-agent/` 不推 GitHub
3. **渐进式加载**：每次只加载相关 Agent 配置，不加载全部
4. **版本控制类似 git**：VERSION 文件记录版本历史，merge-log 记录每次合并
5. **私有文件不推 GitHub**：`.gitignore` 已配置，私有文件留在维护者本地

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `PROJECT_LOGIC.md` | 完整系统逻辑和架构说明 |
| `AGENT_DISTRIBUTION_GUIDE.md` | 如何分发和导入 Agent 配置 |
| `PERMISSION_GUIDE.md` | 各 Agent 的权限边界 |
| `agents/future-work-clarifier/release/未来工作厘定-HR版-V3.0-项目说明.md` | 未来工作厘定助手详细说明 |

---

*本文档由 Master Agent 🎯 维护，最后更新：2026-05-05*
