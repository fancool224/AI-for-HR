# 多Agent协作系统 — 项目逻辑

> **项目名：** 多Agent协作系统  
> **工作区：** `C:\Users\22606\WorkBuddy\TOP-HR-Agent-basic\`  
> **GitHub仓库：** `https://github.com/fancool224/AI-for-HR`  
> **最后更新：** 2026-05-05

---

## 一、项目定位

**目标：** 构建一套**通用多 Agent 协作系统**，让不同用户可以：
1. 通过链接直接获取 Agent 配置
2. 在专用工作区内完成项目任务
3. Collaborator Agent 完成后存档到腾讯文档
4. 每周自动合并项目使用情况和上下文文件，更新腾讯云文档

---

## 二、多 Agent 协作逻辑

### 2.1 系统架构（三端分工）

```
用户A ───┐
用户B ───┼──→ WorkBuddy（加载对应Agent配置）→ 专用工作区：TOP-HR-Agent-basic\
用户C ───┘                                          ├── agents/（Agent配置挂载）
                                                          ├── master-agent/（主Agent 🎯）
                                                          ├── shared-context/（共享上下文）
                                                          └── state.json（系统注册表）
```

| 端 | 定位 | 内容 | 维护者 |
|---|---|---|---|
| **本地** | 唯一最新准确信息来源 | 完整项目文件 | 项目发起人（Master Agent 🎯） |
| **GitHub** | Agent配置存储仓库 | Agent配置（不含共享上下文） | 项目发起人推送 |
| **腾讯文档** | 协作存储 | ①元文件 ②上下文摘要历史 ③项目进展文件 ④Collaborator工作记录 | Collaborator存档 + 发起人每周合并 |

**核心机制：**
- **不是** 多用户共享同一个 Agent 实例
- **而是** 每个用户有自己的 WorkBuddy，但加载**同一套 Agent 配置**
- **Collaborator Agent** 完成项目后，存档到腾讯文档（不是本地 history/）

---

### 2.2 Agent 注册与触发

#### 已注册的 Agent（state.json）

| Agent名 | 路径 | 触发词 | 说明 |
|---------|------|--------|------|
| **主Agent 🎯** | `master-agent/` | 同步/检查更新/状态查询/新增Agent | 项目发起人，负责版本管理 |

#### 触发逻辑（用户三种提问方式）

| 用户说 | 意图 | Agent 动作 |
|--------|------|------------|
| ① "我现在可以调用agent使用什么功能？" | 查询 | 读取 `state.json` → 列出所有 Agent + 触发词 |
| ② "我现在想用XXX功能" | 激活 | 渐进式加载：检查本地 vs GitHub → 克隆最新版 → 配置 → 执行 |
| ③ "用XX功能来完成...工作" | 执行 | 加载配置 + 按 SOUL.md 规则执行任务 |

---

### 2.3 渐进式加载机制

```
用户："我想用XX功能"
    ↓
Master Agent 🎯 匹配触发词 → 对应Agent
    ↓
检查 state.json → 确认路径
    ↓
检查本地 vs GitHub版本
    ↓
最新版？→ 直接加载
不是最新版？→ 克隆Agent到本地 → 配置 → 加载
    ↓
渐进式加载（只加载相关配置）：
  1. 读取 Agent的 SOUL.md + IDENTITY.md
  2. （可选）加载对应的 Skill
    ↓
告知用户："✅ 已激活 XX Agent，现在可以开始工作"
    ↓
按 Agent 的 SOUL.md 规则执行工作
    ↓
任务完成 → 执行后处理
    ↓
更新腾讯文档：
  · 项目执行记录
  · 共享上下文
  · 使用体验、问题点、改进方向
```

**优点：**
- 不加载全部 Agent → 上下文窗口小
- 按需加载 → 响应快
- 每个 Agent 独立 → 互不干扰

---

### 2.4 Collaborator 完成后的存档机制

```
Collaborator Agent 完成任务
    ↓
执行后处理
    ↓
更新腾讯文档：
  ① 项目执行记录
  ② 共享上下文
  ③ 使用体验、问题点、改进方向
    ↓
标记完成，等待 Master Agent 每周合并
```

---

### 2.5 每周合并机制

```
每周五 12:00，Master Agent 🎯 自动发起：
    ↓
1. 检查腾讯文档中的 Collaborator 工作记录
    ↓
2. 读取 shared-context/version-control/VERSION 当前版本号
    ↓
3. 决定是否合并（询问用户或直接执行）
    ↓
4. 合并后：
    ├── 更新 VERSION → 版本号 +1
    ├── 写入 master-agent/merge-log/YYYY-MM-DD.md
    └── 标记腾讯文档记录为 merged
```

---

### 2.6 版本控制

```
shared-context/version-control/VERSION
├── 当前版本：0.1.0
├── 版本历史：
│   └── 0.1.0 | 2026-05-05 | 初始化通用多Agent协作系统 | Master Agent 🎯
└── 合并规则：
    ├── 每周五检查腾讯文档工作记录
    ├── 只合并标记为待合并的记录
    └── 合并前必须更新 VERSION
```

---

## 三、工作区存储规范

### 3.1 目录结构（TOP-HR-Agent-basic\）

```
TOP-HR-Agent-basic\
│
├── agents/                          ← Agent 配置挂载区
│   └── （用户自行添加 Agent）
│
├── master-agent/                   ← 主 Agent 区域
│   ├── SOUL.md                    ← 主 Agent 灵魂（调度器）
│   ├── IDENTITY.md                ← 主 Agent 身份
│   ├── weekly-merge.py           ← 每周合并脚本
│   └── merge-log/                 ← 合并记录
│
├── shared-context/                 ← 共享上下文
│   ├── SHARED_CONTEXT.md          ← 全局共享知识日志（只追加）
│   └── version-control/           ← 版本控制
│       └── VERSION                ← 版本号 + 合并历史
│
├── state.json                      ← 系统状态追踪
├── .gitignore                     ← 保护私有文件
└── README.md
```

### 3.2 存储原则

| 内容 | 存储位置 | 说明 |
|------|------------|------|
| Agent 配置 | `agents/<name>/` | 每个 Agent 独立目录，推送到 GitHub |
| 全局上下文 | `shared-context/SHARED_CONTEXT.md` | 只追加，不覆盖，不推 GitHub |
| 版本控制 | `shared-context/version-control/VERSION` | 版本历史，不推 GitHub |
| 合并记录 | `master-agent/merge-log/` | Master Agent 写入，不推 GitHub |
| 系统状态 | `state.json` | Agent 注册表 + 同步状态，推 GitHub |

---

## 四、GitHub 推送规范

### 4.1 推送内容（公开）

| 文件/目录 | 说明 |
|-----------|------|
| `README.md` | 项目说明 |
| `PROJECT_LOGIC.md` | 项目逻辑文档 |
| `state.json` | 系统状态（Agent 注册表） |
| `scripts/` | 推送脚本等工具 |
| `agents/` | Agent 配置（不含敏感信息） |

### 4.2 不推送内容（私有）

| 文件/目录 | 原因 |
|-----------|------|
| `master-agent/` | 含项目发起人的私有配置 |
| `shared-context/` | 含共享上下文和版本控制 |
| `.git/` | Git 内部文件 |

---

## 五、使用指南

### 5.1 项目发起人（Master Agent 🎯）

```powershell
# 1. 新增 Agent
准备完整 Agent 文件 → 挂载到 agents/<agent-name>/
→ 更新 state.json → 推送到 GitHub

# 2. 每周五 12:00 检查合并
说："执行每周合并"
→ 检查腾讯文档工作记录
→ 询问是否合并
→ 更新 VERSION + 写 merge-log
```

### 5.2 协作者（未来扩展）

```powershell
# 1. 获取项目链接（项目发起人提供）
# 2. 启动 WorkBuddy，说："导入 agent"
#    → 自动触发导入流程
#    → 解压、复制、注册
#
# 3. 说："我现在想用XX功能"
#    → 检查版本、克隆最新、配置
#    → 加载 Agent 配置
#    → 按规则执行任务
#    → 完成后自动存档到腾讯文档
```

---

## 六、注意事项

1. **本地是唯一最新准确信息来源**：GitHub 是克隆源，腾讯文档是协作存档
2. **GitHub 不提供共享上下文**：`shared-context/` 和 `master-agent/` 不推 GitHub
3. **渐进式加载**：每次只加载相关 Agent 配置，不加载全部
4. **Collaborator 存档到腾讯文档**：不修改本地 `master-agent/` 和 `shared-context/`
5. **版本控制类似 git**：VERSION 文件记录版本历史，merge-log 记录每次合并

---

*本文档由 Master Agent 🎯 维护，最后更新：2026-05-05*
