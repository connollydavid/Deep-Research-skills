---
name: research-add-fields
description: 向现有调研outline补充字段定义（ZCode/Z.ai 版）。
---

# Research Add Fields - 补充调研字段（ZCode / Z.ai 版）

## 触发方式
`/research-add-fields`

## 执行流程

### Step 1: 自动定位字段文件
在当前工作目录查找 `*/fields.yaml` 文件，自动读取已有字段定义。

### Step 2: 获取补充来源
使用AskUserQuestion让用户选择：
- **A. 用户直接输入**：用户提供字段名称和描述
- **B. Web Search**：启动agent搜索该领域常用字段

若选择B，启动一个Agent（`subagent_type: "general-purpose"`）：将
`~/.agents/skills/research/web-search-brief.md` 的完整内容置于任务
prompt 之前，任务描述包含调研话题、已有字段分类、端点策略（来自
同目录的outline.yaml），以及"检索常用调研字段定义并附来源（不写
文件）"的要求。用 TaskOutput 等待完成。

### Step 3: 展示并确认
- 展示建议的新字段列表
- 用户确认要添加哪些字段
- 用户指定字段分类和detail_level

### Step 4: 保存更新
将确认的字段追加到fields.yaml，保存文件。

## 输出
更新后的 `{topic}/fields.yaml` 文件（原地修改，需用户确认）
