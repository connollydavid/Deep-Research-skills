#!/usr/bin/env bash
# Regression checks for the ZCode validator. Run from anywhere; paths are
# resolved against the lane root. Exits nonzero on the first failure.
set -euo pipefail
cd "$(dirname "$0")/.."

EN="skills/research-zcode-en/research/validate_json.py"
ZH="skills/research-zcode-zh/research/validate_json.py"

python3 -m py_compile "$EN" "$ZH"

# Block and flow styles must parse to the same field set and required split.
a=$(python3 "$EN" -f checks/fields_block_style.yaml -j checks/item_full.json 2>&1 | grep '^Total fields:')
b=$(python3 "$EN" -f checks/fields_flow_style.yaml  -j checks/item_full.json 2>&1 | grep '^Total fields:')
[ "$a" = "$b" ] || { echo "FAIL: block and flow styles disagree: [$a] vs [$b]" >&2; exit 1; }

# Full coverage passes on both styles, and at FULL coverage - a pass below
# 100% means descent missed a category (the vacuous-pass failure mode).
for style in block flow; do
  out=$(python3 "$EN" -f "checks/fields_${style}_style.yaml" -j checks/item_full.json 2>&1)
  echo "$out" | grep -q '^\[PASS\]' || { echo "FAIL: ${style} full fixture not PASS" >&2; exit 1; }
  echo "$out" | grep -q '^Coverage: 100.0%' \
    || { echo "FAIL: ${style} full fixture passed below 100% coverage (vacuous pass)" >&2; exit 1; }
done
echo "block/flow styles: identical parse, full-coverage PASS at 100%"

# required: false must stay optional; the missing REQUIRED field must fail.
python3 "$EN" -f checks/fields_block_style.yaml -j checks/item_partial.json >/dev/null 2>&1 \
  && { echo "FAIL: missing-required fixture passed" >&2; exit 1; }
echo "missing-required fixture: FAILs as required"

echo "all validator checks passed"
