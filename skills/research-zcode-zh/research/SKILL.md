---
name: research
description: 对目标话题进行初步调研，生成调研outline（ZCode/Z.ai 版）。用于学术调研、benchmark调研、技术选型等场景。通过 Z.ai 的 WebSearch/WebFetch/webReader 后端并行补充检索。
---

# Research Skill - 初步调研（ZCode / Z.ai 版）

## 触发方式
`/research <topic>`

## 平台说明（ZCode，Z.ai 后端）
- 网络发现使用 **WebSearch** 工具（国际端点；基于检索结果作答后，始终以 `Sources:` 列表列出所用链接）。
- 页面内容使用 **WebFetch**（`url` + `prompt`；强制 HTTPS；跨域重定向会被“返回”而不是自动跟随——需用重定向 URL 再次调用 WebFetch；同一 URL 的响应缓存 15 分钟）。当问答式摘要会丢失细节（长表格、规格、论文）时，改用 **mcp__web_reader__webReader** 获取整页 markdown。
- 并行检索 agent 通过 **Agent** 工具启动（`subagent_type: "general-purpose"`）。在同一条消息中发出多个 Agent 调用即可并发执行。
- 交互确认使用 **AskUserQuestion**。
- 任何时间敏感检索前先执行 `date +%Y-%m-%d` 获取当前日期。

## 执行流程

### Step 1: 模型内部知识生成初步框架
基于topic，利用模型已有知识生成：
- 该领域的主要研究对象/items列表
- 建议的调研字段框架

输出{step1_output}，使用AskUserQuestion确认：
- items列表是否需要增减？
- 字段框架是否满足需求？

### Step 2: 选择检索端点
使用AskUserQuestion询问本次调研使用哪个检索端点——严格二选一（单一
Z.ai 账户；每次运行选定一个地区；本版本两个选项始终可用）：
- **国际端点（international）**——国际网页、GitHub、Stack Overflow、学术源
- **中文端点（chinese）**——中文技术社区：CSDN、知乎、掘金、SegmentFault、V2EX（默认）

答案将在 Step 4 作为标量写入 `outline.yaml` 的 `search_endpoints: international | chinese` 字段，并由 `/research-deep` 遵循执行。

随后使用AskUserQuestion询问时间范围（如：最近6个月、2024年至今、不限）。

**参数获取**：
- `{topic}`: 用户输入的调研话题
- `{YYYY-MM-DD}`: 当前日期（`date +%Y-%m-%d`）
- `{step1_output}`: Step 1生成的完整输出内容
- `{time_range}`: 用户指定的时间范围
- `{endpoints_clause}`: `search_endpoints` 为 international 时为 ""；为 chinese 时为："本次运行的端点策略为 chinese：路由 chinese-tech 模块，以双语查询检索中文技术社区（CSDN、知乎、掘金、SegmentFault、V2EX）。"

**硬约束**：以下prompt必须严格复述，仅替换{xxx}中的变量，禁止改写结构或措辞。前置检索agent简报：读取本技能目录下的 `web-search-brief.md`，将其完整内容置于 Agent prompt 中本模板之前。

启动1个检索agent（Agent 工具，`subagent_type: "general-purpose"`，`run_in_background: true`），**Prompt模板**：
```python
prompt = f"""{web_search_brief}

## 任务
调研话题: {topic}
当前日期: {YYYY-MM-DD}

基于以下初步框架，补充最新items和推荐调研字段。

## 已有框架
{step1_output}

## 目标
1. 验证已有items是否遗漏重要对象
2. 根据遗漏对象进行补充items
3. 继续搜索{topic}相关且{time_range}内的items并补充
4. 补充新fields{endpoints_clause}

## 输出要求
直接返回结构化结果（不写文件）：

### 补充Items
- item_name: 简要说明（为什么应该加入）
...

### 推荐补充字段
- field_name: 字段描述（为什么需要这个维度）
...

### Sources
- [Source1](url1)
- [Source2](url2)
"""
```

用 TaskOutput 等待该 agent 完成后整合其结果。

### Step 3: 询问用户已有字段
使用AskUserQuestion询问用户是否已有字段定义文件，如有则读取并合并。

### Step 4: 生成Outline（分文件）
合并{step1_output}、{step2_output}与用户已有字段，生成两个文件：

**outline.yaml**（items + 配置）：
- topic: 调研话题
- items: 调研对象列表
- search_endpoints: `international` 或 `chinese`——二选一，来自 Step 2
- execution:
  - batch_size: 并行agent数量（AskUserQuestion确认）
  - items_per_agent: 每个agent负责的items数（AskUserQuestion确认）
  - output_dir: 结果输出目录（默认: ./results）

**fields.yaml**（字段定义）——用 Write 工具以纯文本写入：
- 字段分类与定义
- 每个字段的name、description、detail_level
- 条目可用流式（`- {name: ...}`）或块式（`- name:` 加缩进键）写法；校验器两者都接受
- detail_level层级: brief -> moderate -> detailed
- uncertain: 不确定字段列表（保留字段，深度调研阶段自动填充）

### Step 5: 输出并确认
- 创建目录: `./{topic_slug}/`
- 保存: `outline.yaml` 和 `fields.yaml`
- 展示给用户确认

## 输出路径
```
{当前工作目录}/{topic_slug}/
  ├── outline.yaml    # items列表 + 端点策略 + execution配置
  └── fields.yaml     # 字段定义
```

## 后续命令
- `/research-add-items` - 补充items
- `/research-add-fields` - 补充fields
- `/research-deep` - 开始深度调研
