---
name: research-add-fields
description: Add field definitions to an existing research outline (ZCode/Z.ai edition).
---

# Research Add Fields - Supplement Research Fields (ZCode / Z.ai edition)

## Trigger
`/research-add-fields`

## Workflow

### Step 1: Auto-locate Fields File
Find `*/fields.yaml` file in current working directory, auto-read existing fields definitions.

### Step 2: Get Supplement Source
Use AskUserQuestion to let the user choose:
- **A. User direct input**: User provides field names and descriptions
- **B. Web Search**: Launch an agent to search common fields in this domain

If B is chosen, spawn ONE Agent (`subagent_type: "general-purpose"`): prepend
the full content of `~/.agents/skills/research/web-search-brief.md` to a task
prompt describing the topic, the existing field categories, the run's
endpoint policy (from the sibling outline.yaml), and a request for commonly
researched field definitions with sources (no file writes). Wait with
TaskOutput.

### Step 3: Display and Confirm
- Display suggested new fields list
- User confirms which fields to add
- User specifies field category and detail_level

### Step 4: Save Update
Append confirmed fields to fields.yaml, save file.

## Output
Updated `{topic}/fields.yaml` file (in-place modification, requires user confirmation)
