---
name: research-add-items
description: 向现有调研outline补充items（调研对象）（ZCode/Z.ai 版）。
---

# Research Add Items - 补充调研对象（ZCode / Z.ai 版）

## 触发方式
`/research-add-items`

## 执行流程

### Step 1: 自动定位Outline
在当前工作目录查找 `*/outline.yaml` 文件，自动读取（含 `search_endpoints` 端点策略）。

### Step 2: 并行获取补充来源
使用AskUserQuestion同时询问：
- **A. 用户指定items**：需要补充哪些items？有具体名称吗？
- **B. 是否需要Web Search**：是否启动检索agent搜索更多items？

若选择B，启动一个Agent（`subagent_type: "general-purpose"`）：将
`~/.agents/skills/research/web-search-brief.md` 的完整内容置于任务
prompt 之前，任务描述包含调研话题、当前items列表、本次运行的端点
策略，以及"补充调研对象并附来源（不写文件）"的要求。用 TaskOutput
等待完成。

### Step 3: 合并更新
- 将新items追加到outline.yaml
- 展示给用户确认
- 避免重复
- 保存更新后的outline

## 输出
更新后的 `{topic}/outline.yaml` 文件（原地修改）
