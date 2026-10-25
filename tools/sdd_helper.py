import os
import re
import subprocess
import sys
from pathlib import Path

def get_repo_root() -> Path:
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    return Path(res.stdout.strip())

def workspace(plan_file: str) -> Path:
    plan_path = Path(plan_file).resolve()
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    slug = plan_path.stem
    root = get_repo_root()
    base = root / ".superpowers" / "sdd"
    base.mkdir(parents=True, exist_ok=True)
    gitignore = base / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n", encoding="utf-8")
    dir_path = base / slug
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def task_brief(plan_file: str, n: int) -> Path:
    ws = workspace(plan_file)
    plan_path = Path(plan_file).resolve()
    content = plan_path.read_text(encoding="utf-8")
    
    # Match ### Task N: until next ### Task or end
    pattern = rf"(### Task {n}:[\s\S]*?)(?=\n### Task \d+:|\Z)"
    match = re.search(pattern, content)
    if not match:
        raise ValueError(f"Task {n} not found in plan {plan_file}")
    
    task_text = match.group(1).strip()
    out_file = ws / f"task-{n}-brief.md"
    out_file.write_text(task_text, encoding="utf-8")
    return out_file

def review_package(plan_file: str, base: str, head: str) -> Path:
    ws = workspace(plan_file)
    base_short = subprocess.run(["git", "rev-parse", "--short", base], capture_output=True, text=True, check=True).stdout.strip()
    head_short = subprocess.run(["git", "rev-parse", "--short", head], capture_output=True, text=True, check=True).stdout.strip()
    
    log_res = subprocess.run(["git", "log", "--oneline", f"{base}..{head}"], capture_output=True, text=True, check=True)
    stat_res = subprocess.run(["git", "diff", "--stat", f"{base}..{head}"], capture_output=True, text=True, check=True)
    diff_res = subprocess.run(["git", "diff", "-U10", f"{base}..{head}"], capture_output=True, text=True, check=True)
    
    out_file = ws / f"review-{base_short}..{head_short}.diff"
    content = (
        f"# Review package: {base}..{head}\n\n"
        f"## Commits\n{log_res.stdout}\n"
        f"## Files changed\n{stat_res.stdout}\n"
        f"## Diff\n{diff_res.stdout}\n"
    )
    out_file.write_text(content, encoding="utf-8")
    return out_file

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "workspace":
        print(workspace(sys.argv[2]))
    elif cmd == "brief":
        print(task_brief(sys.argv[2], int(sys.argv[3])))
    elif cmd == "package":
        print(review_package(sys.argv[2], sys.argv[3], sys.argv[4]))
    else:
        print("Unknown command", file=sys.stderr)
        sys.exit(1)
