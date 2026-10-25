#!/usr/bin/env bash
# Lab 6: block commits whose staged Python code has a function/method with cyclomatic complexity > MAX_CC.
# Called from .githooks/pre-commit (core.hooksPath=.githooks, so .git/hooks/ is not used).
# Checks the STAGED content (git show :file), not the working tree, so partial staging is judged correctly.
MAX_CC=10

RADON=$(command -v radon || echo "$(git rev-parse --show-toplevel)/../.venv3.13/bin/radon")
if [ ! -x "$RADON" ]; then
  echo "pre-commit: radon not found (pip install radon) - commit blocked" >&2
  exit 1
fi

status=0
# -z: NUL-separated names, safe for spaces and '&' in paths
while IFS= read -r -d '' file; do
  [[ $file == *.py ]] || continue
  report=$(git show ":$file" | "$RADON" cc -j -) || { echo "pre-commit: radon failed on $file" >&2; exit 1; }
  violations=$(printf '%s' "$report" | python3 -c '
import json, sys
limit = int(sys.argv[1])
for b in json.load(sys.stdin)["-"]:
    if b["type"] != "class" and b["complexity"] > limit:  # class CC is an aggregate, its methods are listed too
        name = ".".join(filter(None, [b.get("classname"), b["name"]]))
        print("%s (line %d): CC=%d > MAX_CC=%d" % (name, b["lineno"], b["complexity"], limit))
' "$MAX_CC") || { echo "pre-commit: cannot parse radon output for $file" >&2; exit 1; }
  if [ -n "$violations" ]; then
    while IFS= read -r line; do
      printf '\033[31mCOMPLEXITY FAIL: %s: %s\033[0m\n' "$file" "$line" >&2
    done <<< "$violations"
    status=1
  fi
done < <(git diff --cached --name-only --diff-filter=ACM -z)

if [ "$status" -ne 0 ]; then
  printf '\033[31mpre-commit: commit blocked, simplify the functions above (limit MAX_CC=%s)\033[0m\n' "$MAX_CC" >&2
fi
exit "$status"
