"""Repository checks run by CI: Python syntax, notebook files, YAML files and a simple secret scan."""
import json
import py_compile
import re
import subprocess
import sys
import os

import yaml

errors = []


def tracked(pattern):
    """List the files Git tracks that match a pattern (for example '*.py')."""
    out = subprocess.check_output(["git", "ls-files", pattern], text=True)
    return [f for f in out.splitlines() if f]


# 1. Python files must compile
py_files = tracked("*.py")
for f in py_files:
    try:
        py_compile.compile(f, doraise=True)
    except py_compile.PyCompileError as e:
        errors.append(f"Python syntax error in {f}: {e}")
print(f"Python files checked: {len(py_files)}")

# 2. Notebooks must be valid JSON
nb_files = tracked("*.ipynb")
for f in nb_files:
    try:
        with open(f, encoding="utf-8") as fh:
            json.load(fh)
    except Exception as e:
        errors.append(f"Invalid notebook file {f}: {e}")
print(f"Notebooks checked: {len(nb_files)}")

# 3. YAML files must parse
yaml_files = tracked("*.yml") + tracked("*.yaml")
for f in yaml_files:
    try:
        with open(f, encoding="utf-8") as fh:
            yaml.safe_load(fh)
    except Exception as e:
        errors.append(f"Invalid YAML in {f}: {e}")
print(f"YAML files checked: {len(yaml_files)}")

# 4. No secrets in the code
secret_patterns = {
    "Databricks token": r"dapi[0-9a-f]{32}",
    "GitHub classic token": r"ghp_[A-Za-z0-9]{36}",
    "GitHub fine-grained token": r"github_pat_[A-Za-z0-9_]{20,}",
}
text_files = []
for pattern in ["*.py", "*.ipynb", "*.yml", "*.yaml", "*.md", "*.sql", "*.txt", "*.json"]:
    text_files += tracked(pattern)
for f in sorted(set(text_files)):
    with open(f, encoding="utf-8", errors="ignore") as fh:
        content = fh.read()
    for label, regex in secret_patterns.items():
        if re.search(regex, content):
            errors.append(f"Possible {label} found in {f}")
print(f"Files scanned for secrets: {len(set(text_files))}")

# 4b. Files referenced by the bundle must exist
def collect_paths(node, found):
    """Collect notebook_path and library file paths from a YAML structure."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "notebook_path" and isinstance(value, str):
                found.append(value)
            elif key == "file" and isinstance(value, dict) and isinstance(value.get("path"), str):
                found.append(value["path"])
            else:
                collect_paths(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_paths(item, found)

bundle_files = [f for f in yaml_files if f.startswith("resources/")]
referenced = 0
for f in bundle_files:
    with open(f, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    paths = []
    collect_paths(doc, paths)
    for p in paths:
        referenced += 1
        target = os.path.normpath(os.path.join(os.path.dirname(f), p))
        if not os.path.exists(target):
            errors.append(f"{f} refers to a missing file: {p}")
print(f"Bundle file references checked: {referenced}")

# 5. Sanity check: a check that looks at nothing must not pass
minimums = {
    "Python files": (len(py_files), 1),
    "Notebooks": (len(nb_files), 5),
    "YAML files": (len(yaml_files), 1),
}
for label, (found, minimum) in minimums.items():
    if found < minimum:
        errors.append(
            f"Only {found} {label} found (expected at least {minimum}). "
            "Is this a full checkout of the repo?"
        )

# Final result
if errors:
    print("\nFAILED:")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("\nAll checks passed")
