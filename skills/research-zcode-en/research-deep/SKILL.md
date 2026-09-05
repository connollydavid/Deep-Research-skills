---
name: research-deep
description: Read the research outline and launch an independent agent for each item for deep research (ZCode/Z.ai edition). Parallel batches via the Agent tool; results validated per item.
---

# Research Deep - Deep Research (ZCode / Z.ai edition)

## Trigger
`/research-deep`

## Platform notes (ZCode, Z.ai backends)
- Search agents are spawned with the **Agent** tool (`subagent_type: "general-purpose"`). To run a batch concurrently, emit several Agent invokes in ONE message. For long batches use `run_in_background: true` and wait with TaskOutput.
- Discovery via **WebSearch**; page content via **WebFetch** (cross-host redirects are returned — re-call with the redirect URL) or **mcp__web_reader__webReader** for full-page markdown.
- Get the current date with `date +%Y-%m-%d`.
- Batch approval gates use **AskUserQuestion**.

## Workflow

### Step 1: Auto-locate Outline
Find `*/outline.yaml` file in current working directory, read items list, endpoint policy (`search_endpoints`), execution config (including items_per_agent).

### Step 2: Resume Check
- Check completed JSON files in output_dir
- Skip completed items

### Step 3: Batch Execution
- Batch by batch_size (need AskUserQuestion approval before each next batch)
- Each agent handles items_per_agent items
- Launch search agents concurrently in one message (Agent tool, general-purpose)

**Parameter Retrieval**:
- `{topic}`: topic field from outline.yaml
- `{item_name}`: item's name field
- `{item_related_info}`: item's complete yaml content (name + category + description etc.)
- `{output_dir}`: execution.output_dir from outline.yaml (default: ./results)
- `{fields_path}`: absolute path to {topic}/fields.yaml
- `{output_path}`: absolute path to {output_dir}/{item_name_slug}.json (slugify item_name: replace spaces with _, remove special chars)
- `{web_search_brief}`: full content of `~/.agents/skills/research/web-search-brief.md`
- `{endpoints_clause}`: "" when outline `search_endpoints` is `international`; when it is `chinese`: "This run's endpoint policy is chinese: route the chinese-tech module and target Chinese tech communities (CSDN, Zhihu, Juejin, SegmentFault, V2EX) with bilingual queries."

**Hard Constraint**: The following prompt must be strictly reproduced, only replacing variables in {xxx}, do not modify structure or wording.

**Prompt Template**:
```python
prompt = f"""{web_search_brief}

## Task
Research {item_related_info}, output structured JSON to {output_path}

## Field Definitions
Read {fields_path} to get all field definitions

## Output Requirements
1. Output JSON according to fields defined in fields.yaml
2. Mark uncertain field values with [uncertain]
3. Add uncertain array at the end of JSON, listing all uncertain field names
4. All field values must be in English{endpoints_clause}

## Output Path
{output_path}

## Validation
After completing JSON output, run validation script to ensure complete field coverage:
python ~/.agents/skills/research/validate_json.py -f {fields_path} -j {output_path}
Task is complete only after validation passes.
"""
```

**One-shot Example** (assuming researching GitHub Copilot):
```
## Task
Research name: GitHub Copilot
category: International Product
description: Developed by Microsoft/GitHub, first mainstream AI coding assistant, ~40% market share, output structured JSON to {project_dir}/results/GitHub_Copilot.json

## Field Definitions
Read {project_dir}/fields.yaml to get all field definitions

## Output Requirements
1. Output JSON according to fields defined in fields.yaml
2. Mark uncertain field values with [uncertain]
3. Add uncertain array at the end of JSON, listing all uncertain field names
4. All field values must be in English

## Output Path
{project_dir}/results/GitHub_Copilot.json

## Validation
After completing JSON output, run validation script to ensure complete field coverage:
python ~/.agents/skills/research/validate_json.py -f {project_dir}/fields.yaml -j {project_dir}/results/GitHub_Copilot.json
Task is complete only after validation passes.
```

### Step 4: Wait and Monitor
- Wait for the current batch (TaskOutput on each background agent)
- Launch next batch after AskUserQuestion approval
- Display progress

### Step 5: Summary Report
After all complete, output:
- Completion count
- Failed/uncertain marked items
- Output directory

## Agent Config (ZCode mapping)
- Background execution: `run_in_background: true` for large batches
- Output: each agent writes its own JSON file (its final message is only a completion summary)
- Resume support: Yes (Step 2 skip rule)
