"""Generate a starter kernel.ipynb from a task Python source file.

Usage:
    python make_notebook.py <task_source.py> <output.ipynb>

The task source must define exactly one @kbench.task function.
This script wraps it in a minimal notebook: one setup cell + one task cell + one run cell.
"""
import sys
import nbformat


INSTALL_CELL = """\
# Install kaggle-benchmarks SDK (and ensure compatible protobuf)
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "kaggle-benchmarks", "protobuf>=5.29.6"])
"""

SETUP_CELL = """\
# Auto-generated — do not edit the run cell below
import kaggle_benchmarks as kbench
"""

RUN_CELL = """\
# Explicitly invoke the registered task so kbench writes a .run.json alongside
# the .task.json. The @kbench.task decorator only REGISTERS the task; execution
# (which produces the run artifact) requires Task.run() / Task.evaluate().
import inspect
import kaggle_benchmarks as kbench
from kaggle_benchmarks import kaggle as _kbk

if not _kbk.is_configured():
    raise RuntimeError(
        "Kaggle model proxy is not configured (MODEL_PROXY_URL / MODEL_PROXY_API_KEY "
        "missing). Join the hackathon and re-run this kernel."
    )

_tasks = [t for t in kbench.client.registry.values()]
if len(_tasks) != 1:
    raise RuntimeError(f"Expected exactly one registered @kbench.task, found {len(_tasks)}: "
                       f"{[t.name for t in _tasks]}")
_t = _tasks[0]
_nparams = len(inspect.signature(_t.func).parameters)
_run = _t.run(kbench.llm) if _nparams >= 1 else _t.run()
print(f"task={_t.name} status={getattr(_run.status, 'name', _run.status)} "
      f"passed={_run.passed} result={_run.result!r}")
"""


def make_notebook(task_source_path: str, out_path: str) -> None:
    with open(task_source_path) as f:
        task_code = f.read()

    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {
        "name": "python",
        "version": "3.12.0",
    }
    nb.cells = [
        nbformat.v4.new_code_cell(INSTALL_CELL.strip()),
        nbformat.v4.new_code_cell(SETUP_CELL.strip()),
        nbformat.v4.new_code_cell(task_code),
        nbformat.v4.new_code_cell(RUN_CELL.strip()),
    ]
    with open(out_path, "w") as f:
        nbformat.write(nb, f)
    print(f"Notebook written to: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python make_notebook.py <task_source.py> <output.ipynb>")
        sys.exit(1)
    make_notebook(sys.argv[1], sys.argv[2])
