# AI-for-HR 多Agent协作系统（for Master Agent 🎯）

> **版本：** 0.1.2 | **最后更新：** 2026-05-04 23:08 | **维护者：** Master Agent 🎯

---

## 系统概述

这是一套**多 Agent 协作系统**，采用主从架构 + 渐进式加载设计。

**核心思想：**
- Master Agent 🎯本地C盘文件【C:\Users\22606\WorkBuddy\TOP-HR-Agent-basic】作为协作项目的唯一最新准确信息来源，由项目发起人负责更新和推送到github
- 使用github【https://github.com/fancool224/AI-for-HR】作为agent存储仓库，保证不同用户使用统一配置的agent完成工作，但在github上不提供共享上下文
- 使用腾讯云文档【【腾讯文档】❇️⚛️TOP 人事部agent项目⚛️❇️
https://docs.qq.com/space/DRkJuRHhnaUxSTVJu?resourceId=FwHBHKuKiblI&type=folder&scene=53b9bdd624116361a9724058ouFMw1】作为元文件、上下文摘要历史、项目进展文件的存储位置；另外Collaborator Agent完成项目后会向腾讯云文档中存档工作记录：①项目执行记录；②共享上下文；③使用体验、问题点、改进方向等
- 使用**渐进式加载**：用户说"做人才盘点" → 只加载对应 Agent 的配置
- 参考 **git 模式**：Collaborator Agent每次任务完成后进行存档、更新情况每周由主agent+项目负责人进行合并

---