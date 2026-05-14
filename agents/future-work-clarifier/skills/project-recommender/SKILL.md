# SKILL.md — 项目推荐 🎯

## 功能概述

根据用户的HR项目需求，在GitHub上搜索相似的成熟案例，提供可参考的开源项目、最佳实践和实施路径。

---

## 触发条件

当用户提到以下意图时，激活此功能：
- "有没有类似的项目"
- "参考案例"
- "成熟方案"
- "GitHub上有相关项目吗"
- "别人怎么做的"
- "推荐一些项目"

---

## 执行流程

### 第一步：理解用户需求

与用户确认：
1. **项目类型**：是想做人才盘点？胜任力建模？IDP？还是其他HR项目？
2. **关注重点**：是关注技术实现？实施流程？还是工具体系？
3. **技术栈偏好**：是否对特定技术（Python/R/React/Vue等）有偏好？

### 第二步：多层次GitHub搜索

使用以下层次进行搜索：

#### 层次1：直接关键词搜索
```
# 示例搜索词（根据需求替换）
- "HR talent review"
- "competency model"
- "IDP individual development plan"
- "performance management system"
- "HR analytics"
```

#### 层次2：相关领域搜索
```
# 扩展到相关领域
- "people analytics"
- "HR tech"
- "org development"
- "talent management"
```

#### 层次3：工具和框架搜索
```
# 搜索工具和框架
- "HR dashboard"
- "performance review tool"
- "competency assessment"
```

### 第三步：筛选和排序

对搜索结果进行筛选：
1. **Star数**：优先推荐 >100 stars的项目
2. **更新频率**：优先推荐近1年有更新的项目
3. **文档完整性**：优先推荐有完整README、使用手册的项目
4. **许可证**：标注MIT/Apache等可商用许可证

### 第四步：生成推荐报告

输出格式：

```
## 🎯 项目推荐报告

### 需求理解
[复述用户需求]

### 推荐项目

#### 1. [项目名](GitHub链接)
- **Stars**: XX ⭐
- **最后更新**: YYYY-MM-DD
- **技术栈**: Python/React/...
- **核心功能**:
  - 功能1
  - 功能2
- **适合场景**: [说明适合什么情况使用]
- **参考价值**: [说明为什么推荐这个项目]

#### 2. [项目名](GitHub链接)
[同上格式]

### 实施建议
1. [基于推荐项目，给出实施路径建议]
2. [注意要点]
3. [可复用组件]

### 风险提示
- [开源协议限制]
- [技术栈匹配度]
- [本地化改造工作量]
```

---

## 工具使用

### GitHub搜索

使用 `gh` CLI 或 GitHub API 进行搜索：

```bash
# 搜索仓库
gh search repos "HR talent review" --limit 20 --json name,description,stargazersCount,updatedAt,url

# 搜索代码
gh search code "competency model" --repo fancool224/AI-for-HR --limit 10
```

### 网页抓取（备选）

如果CLI工具不可用，使用WebFetch工具抓取GitHub搜索结果页面。

---

## 输出原则

1. **务实优先**：优先推荐有完整文档、可运行的项目
2. **标注风险**：明确说明开源协议限制、技术栈要求
3. **本地化提示**：提醒用户需要根据公司实际情况进行改造
4. **不止于代码**：也推荐方法论、最佳实践文档

---

## 与现有功能的协同

- **与未来工作坊协同**：推荐的项目可作为工作坊的参考案例
- **与胜任力建模协同**：推荐的项目可能包含胜任力模型实现
- **与IDP协同**：推荐的项目可能包含IDP工具和实践

---

_Last updated: 2026-05-15 | Master Agent 🎯_
