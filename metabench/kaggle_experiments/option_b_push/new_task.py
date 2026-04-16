#!/usr/bin/env python3
"""Scaffold a new Kaggle Benchmarks push-workflow task.

Usage:
    python option_b_push/new_task.py <slug>

Creates: option_b_push/tasks/<slug>/
  kernel.py            — task source (edit this)
  kernel.ipynb         — generated notebook (regenerated on push)
  kernel-metadata.json — Kaggle kernel metadata
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TEMPLATE_DIR = SCRIPT_DIR / "template"
TASKS_DIR = SCRIPT_DIR / "tasks"

STUB_TASK = '''\
import kaggle_benchmarks as kbench


@kbench.task(
    name="{task_name}",
    description="TODO: describe what this task measures.",
)
def {func_name}(llm) -> bool:
    """TODO: implement your task here."""
    response = llm.prompt("Say hello.")
    return "hello" in response.lower()
'''


def require_username() -> str:
    username = os.environ.get("KAGGLE_USERNAME", "").strip()
    if username:
        return username
    print(
        "KAGGLE_USERNAME must be set. Copy .env.example to .env or export it first.",
        file=sys.stderr,
    )
    sys.exit(2)


def main():
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    if len(sys.argv) < 2:
        print("Usage: python option_b_push/new_task.py <slug>")
        sys.exit(1)

    slug = sys.argv[1]
    username = require_username()
    task_dir = TASKS_DIR / slug

    if task_dir.exists():
        print(f"Task directory already exists: {task_dir}")
        print("To recreate, delete it first.")
        sys.exit(1)

    task_dir.mkdir(parents=True)

    # Write kernel.py stub
    func_name = slug.replace("-", "_")
    kernel_py = task_dir / "kernel.py"
    kernel_py.write_text(STUB_TASK.format(task_name=slug, func_name=func_name))

    # Write metadata
    meta_template = json.loads((TEMPLATE_DIR / "kernel-metadata.json").read_text())
    meta_template["id"] = f"{username}/{slug}"
    meta_template["title"] = slug.replace("-", " ").title()
    meta_out = task_dir / "kernel-metadata.json"
    meta_out.write_text(json.dumps(meta_template, indent=2))

    # Generate initial notebook
    _make_notebook(kernel_py, task_dir / "kernel.ipynb")

    print(f"\nScaffolded: {task_dir}")
    print(f"\nNext steps:")
    print(f"  1. Edit {task_dir}/kernel.py with your task implementation")
    print(f"  2. Run: cd {SCRIPT_DIR} && python push_and_wait.py {slug}")


def _make_notebook(task_py: Path, out_ipynb: Path) -> None:
    """Generate notebook from task source. Uses make_notebook.py to avoid importing nbformat here."""
    import subprocess, sys as _sys
    result = subprocess.run(
        [_sys.executable, str(TEMPLATE_DIR / "make_notebook.py"), str(task_py), str(out_ipynb)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Warning: notebook generation failed:\n{result.stderr}")
    else:
        print(result.stdout.strip())


if __name__ == "__main__":
    main()
