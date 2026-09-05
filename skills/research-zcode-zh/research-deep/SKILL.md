---
name: research-deep
description: 读取调研outline，为每个item启动独立agent进行深度调研（ZCode/Z.ai 版）。通过 Agent 工具并行分批执行；每个item的结果独立验证。
---

# Research Deep - 深度调研（ZCode / Z.ai 版）

## 触发方式
`/research-deep`

## 平台说明（ZCode，Z.ai 后端）
- 检索 agent 通过 **Agent** 工具启动（`subagent_type: "general-purpose"`）。要并发执行一个批次，在同一条消息中发出多个 Agent 调用。大批次使用 `run_in_background: true` 并用 TaskOutput 等待。
- 发现用 **WebSearch**；页面内容用 **WebFetch**（跨域重定向会被返回——用重定向 URL 再次调用）或 **mcp__web_reader__webReader** 获取整页 markdown。
- 先执行 `date +%Y-%m-%d` 获取当前日期。
- 批次间审批使用 **AskUserQuestion**。

## 执行流程

### Step 1: 自动定位Outline
在当前工作目录查找 `*/outline.yaml` 文件，读取items列表、端点策略（`search_endpoints`）、execution配置（含items_per_agent）。

### Step 2: 断点续传检查
- 检查output_dir下已完成的JSON文件
- 跳过已完成的items

### Step 3: 分批执行
- 按batch_size分批（每批完成后需AskUserQuestion征得用户同意才可进行下一批）
- 每个agent负责items_per_agent个项目
- 在同一条消息中并发启动检索agent（Agent 工具，general-purpose）

**参数获取**：
- `{topic}`: outline.yaml中的topic字段
- `{item_name}`: item的name字段
- `{item_related_info}`: item的完整yaml内容（name + category + description等）
- `{output_dir}`: outline.yaml中execution.output_dir（默认./results）
- `{fields_path}`: {topic}/fields.yaml的绝对路径
- `{output_path}`: {output_dir}/{item_name_slug}.json的绝对路径（slugify处理item_name：空格替换为_，移除特殊字符）
- `{web_search_brief}`: `~/.agents/skills/research/web-search-brief.md` 的完整内容
- `{endpoints_clause}`: outline 的 `search_endpoints` 为 `international` 时为 ""；为 `chinese` 时为："本次运行的端点策略为 chinese：路由 chinese-tech 模块，以双语查询检索中文技术社区（CSDN、知乎、掘金、SegmentFault、V2EX）。"

**硬约束**：以下prompt必须严格复述，仅替换{xxx}中的变量，禁止改写结构或措辞。

**Prompt模板**：
```python
prompt = f"""{web_search_brief}

## 任务
调研 {item_related_info}，输出结构化JSON到 {output_path}

## 字段定义
读取 {fields_path} 获取所有字段定义

## 输出要求
1. 按fields.yaml定义的字段输出JSON
2. 不确定的字段值标注[不确定]
3. JSON末尾添加uncertain数组，列出所有不确定的字段名
4. 所有字段值必须使用中文输出（调研过程可用英文，但最终JSON值为中文）{endpoints_clause}

## 输出路径
{output_path}

## 验证
完成JSON输出后，运行验证脚本确保字段完整覆盖：
python ~/.agents/skills/research/validate_json.py -f {fields_path} -j {output_path}
验证通过后才算完成任务。
"""
```

**One-shot示例**（假设调研GitHub Copilot）：
```
## 任务
调研 name: GitHub Copilot
category: 国际产品
description: Microsoft/GitHub开发，首个主流AI编程助手，市场份额约40%，输出结构化JSON到 {project_dir}/results/GitHub_Copilot.json

## 字段定义
读取 {project_dir}/fields.yaml 获取所有字段定义

## 输出要求
1. 按fields.yaml定义的字段输出JSON
2. 不确定的字段值标注[不确定]
3. JSON末尾添加uncertain数组，列出所有不确定的字段名
4. 所有字段值必须使用中文输出（调研过程可用英文，但最终JSON值为中文）

## 输出路径
{project_dir}/results/GitHub_Copilot.json

## 验证
完成JSON输出后，运行验证脚本确保字段完整覆盖：
python ~/.agents/skills/research/validate_json.py -f {project_dir}/fields.yaml -j {project_dir}/results/GitHub_Copilot.json
验证通过后才算完成任务。
```

### Step 4: 等待与监控
- 等待当前批次完成（对每个后台agent调用TaskOutput）
- AskUserQuestion同意后启动下一批
- 显示进度

### Step 5: 汇总报告
全部完成后输出：
- 完成数量
- 失败/不确定标记的items
- 输出目录

## Agent配置（ZCode 映射）
- 后台执行: 大批次用 `run_in_background: true`
- 输出: 每个agent写自己的JSON文件（其最终消息仅为完成摘要）
- 断点续传: 是（Step 2 跳过规则）
