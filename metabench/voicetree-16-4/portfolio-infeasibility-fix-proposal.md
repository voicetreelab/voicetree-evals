---
color: blue
isContextNode: false
agent_name: Amit
---
# Fix proposal — ordered by impact

Five fixes; 1+2+3 combined take ~60 LOC across 3 files and should raise portfolio feasibility from 0% to ~70% medium / ~50% hard without touching generators or scorers.

### Fix 1 (highest impact, ~40 LOC) — Inline per-component instance NL + per-class BEST_GUESS schema into the portfolio prompt

Add a portfolio-aware path to `render_nl` that receives the `components` list and emits, for each component:
- the full `sub_instance["problem_statement"]` when present (TSP/CJS/Steiner all embed one), OR the class-specific fallback renderer output;
- a literal `ANSWER SCHEMA for <problem_id>:` block built from `CLASS_TO_BEST_GUESS_SCHEMA[component.class]` plus the `component.sub_instance.answer_contract` when available.

Thread `components` through `run_instance` → `render_nl` (it is already the runner arg) and extend `render_nl(instance, cls, components=None)`:

```python
if cls == "portfolio" and components:
    parts = [instance.get("problem_statement", "").rstrip(), ""]
    for comp in components:
        sub_cls = comp.get("class"); sub_inst = comp.get("sub_instance", {})
        pid = comp.get("problem_id")
        parts.append(f"=== {pid} (class={sub_cls}, value_cap={comp.get('value_cap')}) ===")
        sub_ps = sub_inst.get("problem_statement")
        parts.append(sub_ps if isinstance(sub_ps, str) and sub_ps.strip()
                     else _FALLBACK_RENDERERS.get(sub_cls, _render_generic)(sub_inst))
        schema = CLASS_TO_BEST_GUESS_SCHEMA.get(sub_cls)
        if schema:
            parts.append(f"ANSWER SCHEMA for {pid}:\n{schema}")
        contract = sub_inst.get("answer_contract")
        if contract:
            parts.append(f"Answer contract: {contract}")
        parts.append("")
    return "\n".join(parts)
```

This alone should eliminate MWIS key-mismatch, TSP tour-length, Steiner missing-frequencies, and hallucinated-node-name failures across all 3 models.

### Fix 2 (medium impact, ~10 LOC) — Populate `_best_guess_schema_block` for portfolio

When `cls == "portfolio"` and components are available, emit a combined BEST_GUESS top-level schema:
```
BEST_GUESS schema example for `portfolio`:
{
  "cjs_medium_seed14": {"factory_a": {...}, "factory_b": {...}, "makespan": N},
  "mwis_medium_seed14": {"selected_vertices": [...], "total_weight": N},
  "steiner_medium_seed14": {"edges": [...], "frequencies": {...}}
}
```
Requires threading `components` into `build_exec_prompt`/`build_turn1_prompt`. Trivial.

### Fix 3 (tiny, 4 LOC) — Seed `current_best` with MWIS `baseline_answer` and TSP `baseline_tour`

In `runner.py:_initial_best_guess`, fall back through alternate baseline keys so all 6 solo classes produce a valid seed in CURRENT_BEST_JSON:
```python
val = sub_instance.get("baseline_submission")
if val is None:
    val = sub_instance.get("baseline_answer")
if val is None and sub_instance.get("baseline_tour") is not None:
    val = {"tour": list(sub_instance["baseline_tour"])}
if val is not None:
    answers[problem_id] = val
```
Gives the model a concrete canonical baseline to mimic for every sub-problem — which is what it successfully cribs from on CJS and Steiner today.

### Fix 4 (data/generator-side, ~20 LOC) — Emit `answer_contract` on every generator

Add `answer_contract` to the MWIS, TSP, VE, and Graphcol generators (currently only CJS and Steiner emit one). Complements Fix 1 by making the contract authoritative at the data layer.

### Fix 5 (scorer/reporting, ~5 LOC) — Soften top-level `feasible` to `any()` or drop the AND gate

Optional. `infer_feasible` currently flips False when even one of three components fails. A 2/3-component row still contains signal; consider reporting per-component feasibility and dropping the boolean AND top-level flag (or switching to majority/weighted).

### Impact prediction

Applying Fixes 1+2+3 (no generator or scorer changes):
- Expected portfolio-medium feasibility: **≥70%** across all 3 models (up from 0/36).
- Expected portfolio-hard feasibility: **≥50%** (up from 1/36; hard components may still hit capability limits).
- Biggest lift: portfolios containing MWIS, TSP, or VE (currently near-deterministic fails on schema).

fix proposal [[portfolio-infeasibility-root]]
