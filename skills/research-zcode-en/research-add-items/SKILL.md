---
name: research-add-items
description: Add items (research objects) to an existing research outline (ZCode/Z.ai edition).
---

# Research Add Items - Supplement Research Objects (ZCode / Z.ai edition)

## Trigger
`/research-add-items`

## Workflow

### Step 1: Auto-locate Outline
Find `*/outline.yaml` file in current working directory, auto-read (including its `search_endpoints` policy).

### Step 2: Get Supplement Sources in Parallel
Use AskUserQuestion to ask both at once:
- **A. User-named items**: What items to supplement? Any specific names?
- **B. Web Search needed?**: Launch a search agent to find more items?

If B is chosen, spawn ONE Agent (`subagent_type: "general-purpose"`): prepend
the full content of `~/.agents/skills/research/web-search-brief.md` to a task
prompt describing the topic, the current items list, the run's endpoint
policy, and a request for additional research objects with sources (no file
writes). Wait with TaskOutput.

### Step 3: Merge and Update
- Append new items to outline.yaml
- Display to user for confirmation
- Avoid duplicates
- Save updated outline

## Output
Updated `{topic}/outline.yaml` file (in-place modification)
