---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Step 1 Setup Commands

Prepared the first practical setup step for working through ForecastBench without extra subagents: clone the upstream repository into a sibling folder, bootstrap the virtual environment, and stop before private-cloud configuration.

Step 1 goal
- Get a real local checkout of `forecastingresearch/forecastbench` next to the current planning workspace.
- Bootstrap the repo enough to inspect code and build local tooling.
- Do not try to run the full private GCP pipeline yet.

Commands to run
```bash
cd /Users/lochlan/voicetree-evals
git clone --recurse-submodules https://github.com/forecastingresearch/forecastbench.git forecastbench-src
cd forecastbench-src
git status --short --branch
```

Then bootstrap Python:
```bash
cp variables.example.mk variables.mk
make setup-python-env
source .venv/bin/activate
```

Sanity checks after setup:
```bash
pwd
ls
find src -maxdepth 2 -type d | sort | sed -n '1,60p'
```

Expected result
- A new checkout exists at `/Users/lochlan/voicetree-evals/forecastbench-src`.
- `.venv/` exists.
- You can inspect `Makefile`, `variables.mk`, and `src/` locally.

Important note
- `variables.mk` will still contain blank/private values. That is expected. The public repo is enough to inspect code and build a local submission generator, but not enough to run ForecastBench's internal production pipeline.

Learnings
- The main risk at this stage is cloning into the current `ForecastBench/` directory by mistake; that folder is a planning workspace and should stay separate.
- `make setup-python-env` is the repo-native bootstrap entrypoint and is better than inventing a custom environment flow here.
- Success here is local source visibility, not a full benchmark run.

## Related

- [forecastbench-execution-submission-plan-apr-2026](forecastbench-execution-submission-plan-apr-2026.md)

[[1775618897236Woz]]
