#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate that research JSON results cover all fields defined in fields.yaml.

ZCode edition: stdlib only (no pyyaml). Parses the single schema the
research skills emit; anything outside that shape fails loudly instead of
silently passing with zero fields.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

CATEGORY_MAPPING = {
    "basic_info": ["basic_info", "Basic Info"],
    "technical_features": ["technical_features", "technical_characteristics", "Technical Features"],
    "performance_metrics": ["performance_metrics", "performance", "Performance Metrics"],
    "milestone_significance": ["milestone_significance", "milestones", "Milestone Significance"],
    "business_info": ["business_info", "commercial_info", "Business Info"],
    "competition_ecosystem": ["competition_ecosystem", "competition", "Competition Ecosystem"],
    "history": ["history", "History"],
    "market_positioning": ["market_positioning", "market", "Market Positioning"],
}

_SKIP_KEYS = {"_source_file", "uncertain"}

_LIST_ITEM = re.compile(r"^\s*-\s*(.*)$")
_KEY_VALUE = re.compile(r"^([^:]+):\s*(.*)$")


def _parse_inline(s):
    """Parse the flat scalar/list-of-scalars values the schema allows."""
    s = s.strip()
    if not s:
        return None
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [v.strip().strip("'\"") for v in inner.split(",")] if inner else []
    return s.strip("'\"")


def load_fields_yaml(fields_path):
    """Parse fields.yaml in the single schema the research skills emit:

        fields:
          <category>:
            - {name: ..., description: ..., detail_level: ...}
            ...
        uncertain: []

    Required semantics (so the validator can never pass vacuously):
      - if ANY field carries an explicit `required:` key -> opt-in, preserve it
      - else (detail_level-style, no markers) -> ALL fields required, because
        the script's stated purpose is COMPLETE field coverage.
    """
    lines = fields_path.read_text(encoding="utf-8").splitlines()
    defs = []  # (name, category, required_or_None)
    category = None
    in_fields_block = False

    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.strip()

        if indent == 0:
            in_fields_block = stripped == "fields:"
            category = None
            continue
        if not in_fields_block:
            continue

        m_item = _LIST_ITEM.match(raw)
        if m_item and category is not None:
            body = m_item.group(1).strip()
            field = {}
            if body.startswith("{") and body.endswith("}"):
                for pair in body[1:-1].split(","):
                    if ":" in pair:
                        k, v = pair.split(":", 1)
                        field[k.strip().strip("'\"")] = _parse_inline(v)
            if "name" in field:
                defs.append((str(field["name"]), category, field.get("required", None)))
            else:
                print(f"[ERROR] field entry under `{category}` must be a dict with a `name` key; got `{body}`.")
                sys.exit(1)
            continue

        m_kv = _KEY_VALUE.match(stripped)
        if m_kv and stripped.endswith(":"):
            category = m_kv.group(1).strip().strip("'\"")
        elif m_kv and indent <= 2 and stripped.split(":")[0] == "uncertain":
            break  # top-level sibling key: fields block ended
        # category scalar values (if any) are ignored

    if not defs:
        print("[ERROR] fields.yaml parsed zero fields. Ensure the `fields:` block "
              "with `<category>: [- {name: ...}]` entries is present.")
        sys.exit(1)

    all_fields = {n for n, _, _ in defs}
    if any(r is not None for _, _, r in defs):
        required_fields = {n for n, _, r in defs if r}
    else:
        required_fields = set(all_fields)
    field_categories = {n: c for n, c, _ in defs}
    return all_fields, required_fields, field_categories


def extract_json_fields(data, category_mapping=None):
    category_mapping = CATEGORY_MAPPING if category_mapping is None else category_mapping
    nested_keys = {k for keys in category_mapping.values() for k in keys}
    fields = set()
    stack = [(data, True)]
    while stack:
        obj, is_category_level = stack.pop()
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in _SKIP_KEYS:
                    continue
                if is_category_level and k in nested_keys:
                    if isinstance(v, dict):
                        stack.append((v, True))
                    continue
                fields.add(k)
        elif isinstance(obj, list):
            stack.extend((item, is_category_level) for item in obj if isinstance(item, dict))
    return fields


def validate_json(json_path, all_fields, required_fields, field_categories):
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    json_fields = extract_json_fields(data)
    covered = all_fields & json_fields
    missing = all_fields - json_fields
    extra = json_fields - all_fields
    missing_required = missing & required_fields
    missing_by_category = defaultdict(list)
    for field in missing:
        missing_by_category[field_categories.get(field, "Unknown")].append(field)
    return {
        "file": json_path.name,
        "total_defined": len(all_fields),
        "covered": len(covered),
        "missing": len(missing),
        "extra": len(extra),
        "coverage_rate": len(covered) / len(all_fields) * 100 if all_fields else 100,
        "missing_required": sorted(missing_required),
        "missing_optional": sorted(missing - required_fields),
        "missing_by_category": {k: sorted(v) for k, v in missing_by_category.items()},
        "extra_fields": sorted(extra),
        "valid": len(missing_required) == 0,
    }


def print_result(result, verbose=True):
    status = "PASS" if result["valid"] else "FAIL"
    line = "=" * 60
    print(f"\n{line}")
    print(f"[{status}] {result['file']}")
    print(line)
    print(f"Coverage: {result['coverage_rate']:.1f}% ({result['covered']}/{result['total_defined']})")
    if result["missing_required"]:
        print(f"\n[ERROR] Missing required fields ({len(result['missing_required'])}):")
        print("\n".join(f"  - {f}" for f in result["missing_required"]))
    if verbose and result["missing_optional"]:
        missing_required = set(result["missing_required"])
        print(f"\n[WARN] Missing optional fields ({len(result['missing_optional'])}):")
        for cat in sorted(result["missing_by_category"]):
            optional = [f for f in result["missing_by_category"][cat] if f not in missing_required]
            if optional:
                print(f"  [{cat}]: {', '.join(optional)}")
    if verbose and result["extra_fields"]:
        extra = result["extra_fields"]
        print(f"\n[INFO] Extra fields ({len(extra)}):")
        print(f"  {', '.join(extra[:10])}")
        if len(extra) > 10:
            print(f"  ... and {len(extra) - 10} more")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate whether JSON files cover all fields defined in fields.yaml")
    parser.add_argument("--fields", "-f", type=str, help="Path to fields.yaml", default="fields.yaml")
    parser.add_argument("--json", "-j", type=str, nargs="*", help="JSON file paths to validate")
    parser.add_argument("--dir", "-d", type=str, help="Directory containing JSON files", default="results")
    parser.add_argument("--quiet", "-q", action="store_true", help="Show summary only")
    args = parser.parse_args()
    fields_path = Path(args.fields)
    if not fields_path.exists():
        for p in (Path.cwd() / "fields.yaml", Path.cwd().parent / "fields.yaml"):
            if p.exists():
                fields_path = p
                break
    if not fields_path.exists():
        print(f"[ERROR] fields.yaml not found: {fields_path}")
        sys.exit(1)
    print(f"Field definition file: {fields_path}")
    all_fields, required_fields, field_categories = load_fields_yaml(fields_path)
    print(f"Total fields: {len(all_fields)} (required: {len(required_fields)}, optional: {len(all_fields) - len(required_fields)})")
    json_files = (
        [Path(p) for p in args.json]
        if args.json
        else sorted(Path(args.dir).glob("*.json")) if Path(args.dir).exists() else []
    )
    if not json_files:
        print("[WARN] No JSON files found")
        sys.exit(0)
    results = []
    for json_path in json_files:
        if not json_path.exists():
            print(f"[WARN] File not found: {json_path}")
            continue
        result = validate_json(json_path, all_fields, required_fields, field_categories)
        results.append(result)
        print_result(result, verbose=not args.quiet)
    line = "=" * 60
    print(f"\n{line}")
    print("Summary")
    print(line)
    passed = sum(1 for r in results if r["valid"])
    avg_coverage = sum(r["coverage_rate"] for r in results) / len(results) if results else 0
    print(f"Validation passed: {passed}/{len(results)}")
    print(f"Average coverage: {avg_coverage:.1f}%")
    if passed < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
