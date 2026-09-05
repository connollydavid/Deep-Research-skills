---
name: research
description: Conduct preliminary research on a topic and generate a research outline (ZCode/Z.ai edition). For academic research, benchmark research, technology selection, etc. Runs web supplementation through a parallel search agent on Z.ai's WebSearch/WebFetch/webReader backends.
---

# Research Skill - Preliminary Research (ZCode / Z.ai edition)

## Trigger
`/research <topic>`

## Platform notes (ZCode, Z.ai backends)
- Web discovery uses the **WebSearch** tool (international endpoints; end every answer built from results with a `Sources:` list of markdown links).
- Page content uses **WebFetch** (`url` + `prompt`; HTTPS is enforced; a cross-host redirect is RETURNED, not followed — call WebFetch again with the redirect URL; responses are cached 15 min per URL). When the prompt-Q&A summary would lose detail (long tables, specs, papers), use the **mcp__web_reader__webReader** backend for full-page markdown.
- Parallel search agents are spawned with the **Agent** tool (`subagent_type: "general-purpose"`). Multiple Agent invokes in ONE message run concurrently.
- Interactive checkpoints use **AskUserQuestion**.
- Get the current date with `date +%Y-%m-%d` before any time-sensitive search.

## Workflow

### Step 1: Generate Initial Framework from Model Knowledge
Based on topic, use model's existing knowledge to generate:
- Main research objects/items list in this domain
- Suggested research field framework

Output {step1_output}, use AskUserQuestion to confirm:
- Need to add/remove items?
- Does field framework meet requirements?

### Step 2: Choose Search Endpoint
Use AskUserQuestion to ask which search endpoint this run uses — strictly
either/or (single Z.ai account; pick one region for the run; both choices
are always available in this edition):
- **international** — international web, GitHub, Stack Overflow, academic sources (default)
- **chinese** — Chinese tech communities: CSDN, Zhihu, Juejin, SegmentFault, V2EX

Record the answer — it is written to `outline.yaml` as the scalar
`search_endpoints: international | chinese` in Step 4 and honored by
`/research-deep`.

Then use AskUserQuestion to ask for time range (e.g., last 6 months, since 2024, unlimited).

**Parameter Retrieval**:
- `{topic}`: User input research topic
- `{YYYY-MM-DD}`: Current date (`date +%Y-%m-%d`)
- `{step1_output}`: Complete output from Step 1
- `{time_range}`: User specified time range
- `{endpoints_clause}`: "" when `search_endpoints` is international; when chinese: "This run's endpoint policy is chinese: route the chinese-tech module and target Chinese tech communities (CSDN, Zhihu, Juejin, SegmentFault, V2EX) with bilingual queries."

**Hard Constraint**: The following prompt must be strictly reproduced, only replacing variables in {xxx}, do not modify structure or wording. Prepend the search-agent brief: read `web-search-brief.md` (in this skill's directory) and place its full content above this template in the Agent prompt.

Launch 1 search agent (Agent tool, `subagent_type: "general-purpose"`, `run_in_background: true`), **Prompt Template**:
```python
prompt = f"""{web_search_brief}

## Task
Research topic: {topic}
Current date: {YYYY-MM-DD}

Based on the following initial framework, supplement latest items and recommended research fields.

## Existing Framework
{step1_output}

## Goals
1. Verify if existing items are missing important objects
2. Supplement items based on missing objects
3. Continue searching for {topic} related items within {time_range} and supplement
4. Supplement new fields{endpoints_clause}

## Output Requirements
Return structured results directly (do not write files):

### Supplementary Items
- item_name: Brief explanation (why it should be added)
...

### Recommended Supplementary Fields
- field_name: Field description (why this dimension is needed)
...

### Sources
- [Source1](url1)
- [Source2](url2)
"""
```

Wait for the agent with TaskOutput, then integrate its results.

### Step 3: Ask User for Existing Fields
Use AskUserQuestion to ask if user has existing field definition file, if so read and merge.

### Step 4: Generate Outline (Separate Files)
Merge {step1_output}, {step2_output} and user's existing fields, generate two files:

**outline.yaml** (items + config):
- topic: Research topic
- items: Research objects list
- search_endpoints: `international` or `chinese` — either/or, from Step 2
- execution:
  - batch_size: Number of parallel agents (confirm with AskUserQuestion)
  - items_per_agent: Items per agent (confirm with AskUserQuestion)
  - output_dir: Results output directory (default: ./results)

**fields.yaml** (field definitions) — write with the Write tool as plain text:
- Field categories and definitions
- Each field's name, description, detail_level
- detail_level hierarchy: brief -> moderate -> detailed
- uncertain: Uncertain fields list (reserved field, auto-filled in deep phase)

### Step 5: Output and Confirm
- Create directory: `./{topic_slug}/`
- Save: `outline.yaml` and `fields.yaml`
- Show to user for confirmation

## Output Path
```
{current_working_directory}/{topic_slug}/
  ├── outline.yaml    # items list + endpoint + execution config
  └── fields.yaml     # field definitions
```

## Follow-up Commands
- `/research-add-items` - Supplement items
- `/research-add-fields` - Supplement fields
- `/research-deep` - Start deep research
