---
name: research-report
description: 将deep调研结果汇总为markdown报告，覆盖所有字段，跳过不确定值（ZCode/Z.ai 版）。
---

# Research Report - 汇总报告（ZCode / Z.ai 版）

## 触发方式
`/research-report`

## 执行流程

### Step 1: 定位结果目录
在当前工作目录查找 `*/outline.yaml`，读取topic和output_dir配置。

### Step 2: 扫描可选摘要字段
读取所有JSON结果，提取适合在目录中显示的字段（数值型、简短指标），例如：
- github_stars
- google_scholar_cites
- swe_bench_score
- user_scale
- valuation
- release_date

使用AskUserQuestion询问用户：
- 目录中除了item名称外，还需要显示哪些字段？
- 提供动态选项列表（基于实际JSON中存在的字段）

### Step 3: 生成Python转换脚本
在 `{topic}/` 目录生成 `generate_report.py`。脚本将路径作为显式
CLI参数接收（无 YAML 解析依赖；字段结构由技能从 fields.yaml 以
文本读取后经 `--fields-json` 参数传入）：

```
python generate_report.py --results-dir {output_dir} --fields-json {topic}/fields_as_json.json --out {topic}/report.md
```

脚本要求：
- 读取output_dir下所有JSON
- 从fields-json参数读取字段结构
- 覆盖每个JSON的所有字段值
- 跳过值包含[不确定]的字段
- 跳过uncertain数组中列出的字段
- 生成markdown报告格式: 目录（锚点链接 + 用户选择的摘要字段）+ 详细内容（按字段分类）
- 保存到 `{topic}/report.md`

**目录格式要求**：
- 必须包含每个item
- 每个item显示: 编号、名称（锚点链接）、用户选择的摘要字段
- 示例: `1. [GitHub Copilot](#github-copilot) - Stars: 10k | Score: 85%`

#### 脚本技术要求（必须遵守）

**1. JSON结构兼容**
支持两种JSON结构：
- 扁平结构: 字段直接位于顶层 `{"name": "xxx", "release_date": "xxx"}`
- 嵌套结构: 字段位于分类子字典 `{"basic_info": {"name": "xxx"}, "technical_features": {...}}`

字段查找顺序: 顶层 -> 分类映射键 -> 遍历所有嵌套字典

**2. 分类多语言映射**
fields.yaml分类名和JSON键可以是任意组合（中-中、中-英、英-中、英-英）。必须建立双向映射：
```python
CATEGORY_MAPPING = {
    "Basic Info": ["basic_info", "Basic Info"],
    "Technical Features": ["technical_features", "technical_characteristics", "Technical Features"],
    "Performance Metrics": ["performance_metrics", "performance", "Performance Metrics"],
    "Milestone Significance": ["milestone_significance", "milestones", "Milestone Significance"],
    "Business Info": ["business_info", "commercial_info", "Business Info"],
    "Competition & Ecosystem": ["competition_ecosystem", "competition", "Competition & Ecosystem"],
    "History": ["history", "History"],
    "Market Positioning": ["market_positioning", "market", "Market Positioning"],
}
```

**3. 复杂值格式化**
- dict列表（如key_events、funding_history）: 每个dict格式化为一行，kv用 ` | ` 分隔
- 普通列表: 短列表逗号连接，长列表换行显示
- 嵌套dict: 递归格式化，用分号或换行显示
- 长文本字符串（超过100字符）: 加换行 `<br>` 或用引用块格式提高可读性

**4. 额外字段收集**
收集存在于JSON但未在fields.yaml中定义的字段，放入"其他信息"分类。注意过滤：
- 内部字段: `_source_file`、`uncertain`
- 嵌套结构顶层键: `basic_info`、`technical_features` 等
- `uncertain`数组: 每个字段名单独一行显示，不压缩为一行

**5. 不确定值跳过**
跳过条件：
- 字段值包含 `[不确定]` 或 `[uncertain]` 字符串
- 字段名在 `uncertain` 数组中
- 字段值为None或空字符串

### Step 4: 执行脚本
运行 `python {topic}/generate_report.py --results-dir {output_dir} --fields-json {topic}/fields_as_json.json --out {topic}/report.md`

## 输出
- `{topic}/generate_report.py` - 转换脚本
- `{topic}/report.md` - 汇总报告
