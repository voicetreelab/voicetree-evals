#!/usr/bin/env python3
"""Push a task notebook to Kaggle and poll until completion.

Usage:
    python option_b_push/push_and_wait.py <slug>

Prerequisites:
    - KAGGLE_API_TOKEN and KAGGLE_USERNAME must be set in environment or .env
    - option_b_push/tasks/<slug>/kernel.py must exist
    - kaggle CLI in PATH (from .venv)

Steps:
    1. Regenerate kernel.ipynb from kernel.py
    2. kaggle kernels push -p tasks/<slug>/
    3. Poll kaggle kernels status <user/slug> until terminal state
    4. Download output and print .task.json / .run.json contents
"""
import gzip
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TASKS_DIR = SCRIPT_DIR / "tasks"
TEMPLATE_DIR = SCRIPT_DIR / "template"

TERMINAL_STATES = {"complete", "error", "cancelled"}
POLL_INTERVAL = 30  # seconds
MAX_WAIT = 600  # 10 minutes


def run(cmd: list, check=True, capture=True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"FAILED (exit {result.returncode})")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.exit(result.returncode)
    return result


def require_env() -> str:
    missing = [
        name for name in ("KAGGLE_USERNAME", "KAGGLE_API_TOKEN") if not os.environ.get(name)
    ]
    if missing:
        print(
            f"Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        print("Copy .env.example to .env or export them before pushing.", file=sys.stderr)
        sys.exit(2)
    return os.environ["KAGGLE_USERNAME"].strip()


def read_output_text(path: Path) -> str:
    if path.suffix == ".gz":
        return gzip.decompress(path.read_bytes()).decode("utf-8")
    return path.read_text()


def main():
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    if len(sys.argv) < 2:
        print("Usage: python option_b_push/push_and_wait.py <slug>")
        sys.exit(1)

    slug = sys.argv[1]
    username = require_env()
    task_dir = TASKS_DIR / slug
    kernel_ref = f"{username}/{slug}"

    if not task_dir.exists():
        print(f"Task directory not found: {task_dir}")
        print("Run: python new_task.py <slug>  first.")
        sys.exit(1)

    kernel_py = task_dir / "kernel.py"
    if not kernel_py.exists():
        print(f"kernel.py not found in {task_dir}")
        sys.exit(1)

    print(f"\n=== Option B: push-workflow for {kernel_ref} ===\n")

    # Step 1: Regenerate notebook
    print("[1/4] Generating kernel.ipynb from kernel.py...")
    ipynb_path = task_dir / "kernel.ipynb"
    result = subprocess.run(
        [sys.executable, str(TEMPLATE_DIR / "make_notebook.py"),
         str(kernel_py), str(ipynb_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Notebook generation failed:\n{result.stderr}")
        sys.exit(1)
    print(f"  {result.stdout.strip()}")

    # Step 2: Push
    print("\n[2/4] Pushing to Kaggle...")
    push_result = run(["kaggle", "kernels", "push", "-p", str(task_dir)])
    print(push_result.stdout.strip() if push_result.stdout else "(no stdout)")

    # Step 3: Poll until terminal
    print(f"\n[3/4] Polling status for {kernel_ref}...")
    start = time.time()
    last_status = None
    while True:
        elapsed = time.time() - start
        if elapsed > MAX_WAIT:
            print(f"Timeout after {MAX_WAIT}s. Last status: {last_status}")
            sys.exit(1)

        status_result = run(
            ["kaggle", "kernels", "status", kernel_ref],
            check=False
        )
        status_text = (status_result.stdout or "").strip()

        # Parse status from output like:
        # username/slug has status "KernelWorkerStatus.RUNNING"
        import re as _re
        m = _re.search(r'status\s+"?(\w+(?:\.\w+)?)"?', status_text, _re.IGNORECASE)
        if m:
            raw = m.group(1)
            # Strip KernelWorkerStatus. prefix if present
            current_status = raw.split(".")[-1].lower()
        elif status_result.returncode != 0:
            current_status = "queued"  # Just pushed, CLI may not have indexed it yet
        else:
            current_status = "unknown"

        if current_status != last_status:
            print(f"  [{int(elapsed):3d}s] {current_status}")
            last_status = current_status

        if current_status.lower() in TERMINAL_STATES:
            print(f"\n  Terminal state reached: {current_status}")
            break

        time.sleep(POLL_INTERVAL)

    # Step 4: Download and print output
    print(f"\n[4/4] Downloading output from {kernel_ref}...")
    out_dir = task_dir / "output"
    out_dir.mkdir(exist_ok=True)

    dl_result = run(
        ["kaggle", "kernels", "output", kernel_ref, "-p", str(out_dir)],
        check=False
    )
    if dl_result.returncode != 0:
        print(f"  Output download failed (exit {dl_result.returncode}):")
        print(dl_result.stdout or dl_result.stderr)
    else:
        print(f"  Downloaded to: {out_dir}")

    # Print any .task.json or .run.json files
    found_any = False
    for ext in ["*.task.json", "*.run.json", "*.task.json.gz"]:
        for f in out_dir.glob(ext):
            found_any = True
            print(f"\n--- {f.name} ---")
            try:
                data = json.loads(read_output_text(f))
                print(json.dumps(data, indent=2))
            except Exception:
                print(read_output_text(f)[:2000])

    if not found_any:
        print("\n  No .task.json or .run.json found in output.")
        print("  Files in output dir:")
        for f in out_dir.iterdir():
            print(f"    {f.name}")

    print("\n=== Done ===")
    print(f"Kernel URL: https://www.kaggle.com/code/{kernel_ref}")


if __name__ == "__main__":
    main()
