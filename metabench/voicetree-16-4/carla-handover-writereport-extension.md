---
color: cyan
isContextNode: false
agent_name: Cho
---
# Handover code — paste write_report §8/§9/§10 extension into analyze_metacog.py

Copy-paste Python block for the §8/§9/§10 extension of write_report + per-bin CSV emit. Helpers already exist at lines 792–975. Insert directly before the `Script:` footer lines.

# Handover — finish write_report (§8/§9/§10 + metacog_calibration_bins.csv)

## Where to paste

In `kaggle_submission/scripts/analyze_metacog.py`, find the block ending with the caveat starting `'- **64-row set, not 206.**'` and the two trailing lines `Script: ...` / `CSV rollup: ...`. Insert the block below **between** the caveats and the `Script:` footer.

Helpers `_collect_m1_pairs`, `_collect_m2_pairs`, `_calibration_bins`, `_render_calibration_plot`, `_per_class_rollup`, `_pricing_bias` already exist (lines 792–975). DO NOT redefine them.

After pasting, re-run:

```bash
cd /Users/bobbobby/repos/voicetree-evals/metabench
python3 kaggle_submission/scripts/analyze_metacog.py
```

Expected new artifacts: `results/metacog_analysis.md` §8–§10, `results/metacog_calibration_bins.csv` (60 rows = 3 models × 10 bins × 2 metrics).

## Code to paste (write_report extension)

```python
    # --- §8 Calibration plots (Carla / Priority 1) -------------------------------
    lines.append('## 8. Calibration plots (M1 and M2)')
    lines.append('')
    lines.append(
        'Binned reliability diagrams per model. Each row is one 0.1-wide bin of the forecast. '
        "Position `.` marks the bin's mean forecast p\u0304; position `o` marks the bin's observed "
        "frequency y\u0304; `X` means they coincide. The horizontal displacement between `.` and "
        "`o` is the bin's reliability residual. Vertical spread of y\u0304 across bins = resolution."
    )
    lines.append('')
    calibration_bin_rows = []
    for metric, collector in (('M1', _collect_m1_pairs), ('M2', _collect_m2_pairs)):
        for model in MODELS:
            pairs = collector(rows, model=model)
            bins = _calibration_bins(pairs)
            mur = murphy_decomposition(pairs) or {}
            title = f'{metric} calibration — {model}'
            sub = (
                f"Brier={mur.get('brier', float('nan')):.3f}  "
                f"reliability={mur.get('reliability', float('nan')):.3f}  "
                f"resolution={mur.get('resolution', float('nan')):.3f}  "
                f"uncertainty={mur.get('uncertainty', float('nan')):.3f}  "
                f"n={mur.get('n', 0)}"
            )
            lines.append('```text')
            lines.append(_render_calibration_plot(bins, title, sub))
            lines.append('```')
            lines.append('')
            for b in bins:
                calibration_bin_rows.append({
                    'metric': metric, 'model': model,
                    'bin_lo': b['lo'], 'bin_hi': b['hi'],
                    'n': b['n'], 'p_mean': b['p_mean'], 'y_mean': b['y_mean'],
                })

    # --- §9 Per-class Brier (Carla / Priority 2) --------------------------------
    lines.append('## 9. Per-class Brier decomposition (M1 and M2)')
    lines.append('')
    lines.append(
        'Per-(model, class) Murphy decomposition. M1 (p_solve → kept_as_best) skips portfolio. '
        'M2 includes portfolio.'
    )
    lines.append('')
    pc_rollup = _per_class_rollup(rows)
    lines.append('| model | class | M1 n | M1 Brier | M1 rel | M1 res | M2 n | M2 Brier | M2 rel | M2 res |')
    lines.append('|---|---|---|---|---|---|---|---|---|---|')
    for entry in pc_rollup:
        m1 = entry['m1'] or {}
        m2 = entry['m2'] or {}
        def _fmt(v, spec='{:.3f}'):
            return spec.format(v) if v is not None else '—'
        lines.append(
            f"| {entry['model']} | {entry['class']} | "
            f"{m1.get('n', '—') if m1 else '—'} | {_fmt(m1.get('brier') if m1 else None)} | "
            f"{_fmt(m1.get('reliability') if m1 else None)} | "
            f"{_fmt(m1.get('resolution') if m1 else None)} | "
            f"{m2.get('n', '—') if m2 else '—'} | {_fmt(m2.get('brier') if m2 else None)} | "
            f"{_fmt(m2.get('reliability') if m2 else None)} | "
            f"{_fmt(m2.get('resolution') if m2 else None)} |"
        )
    lines.append('')
    lines.append(
        "**Reading the table.** Test Sonnet's M1 resolution by class: high on graphcol/steiner "
        '(feasibility-succeeding) → low on mwis/cjs (feasibility-failing) would show M1 '
        "self-knowledge directly predicts execution — Finding 3's underlying mechanism."
    )
    lines.append('')

    # --- §10 Pricing-bias reconciliation (Carla / Priority 3) -------------------
    lines.append('## 10. Pricing bias vs. stop-rationality reconciliation')
    lines.append('')
    lines.append(
        "Reconciles logistic thresholds (+2.3/+3.6/+4.8) with CF-$ means (−0.26/−1.64/−1.31). "
        'If mean(E[Δ]) − mean(cf_Δ) is large positive, the signals reconcile as pricing bias.'
    )
    lines.append('')
    pb = _pricing_bias(rows)
    lines.append('| model | n turns | mean E[Δ] (all) | n paired | mean E[Δ] (final) | mean cf_Δ | pricing bias |')
    lines.append('|---|---|---|---|---|---|---|')
    for model in MODELS:
        v = pb.get(model, {})
        def _pf(x, spec='{:+.2f}'):
            return spec.format(x) if x is not None else '—'
        lines.append(
            f"| {model} | {v.get('n_all_turns', 0)} | {_pf(v.get('mean_e_all_turns'))} | "
            f"{v.get('n_paired', 0)} | {_pf(v.get('mean_e_paired'))} | "
            f"{_pf(v.get('mean_cf_paired'))} | {_pf(v.get('bias_paired'))} |"
        )
    lines.append('')
    lines.append(
        "**Uniform shift or resolution-dependent?** Split each model's paired final-turn "
        'population at its own median E[Δ]. Flat bias ⇒ bias_low ≈ bias_high. '
        'Scaling bias (emission growing with forecast) ⇒ bias_high > bias_low.'
    )
    lines.append('')
    lines.append('| model | median E[Δ] | n_low | low E[Δ] | low cf_Δ | low bias | n_high | high E[Δ] | high cf_Δ | high bias |')
    lines.append('|---|---|---|---|---|---|---|---|---|---|')
    for model in MODELS:
        v = pb.get(model, {})
        if v.get('split_median_e') is None: continue
        def _pf(x, spec='{:+.2f}'):
            return spec.format(x) if x is not None else '—'
        lines.append(
            f"| {model} | {_pf(v['split_median_e'])} | {v['n_low']} | "
            f"{_pf(v['low_bin_mean_e'])} | {_pf(v['low_bin_mean_cf'])} | "
            f"{_pf(v['low_bin_bias'])} | {v['n_high']} | "
            f"{_pf(v['high_bin_mean_e'])} | {_pf(v['high_bin_mean_cf'])} | "
            f"{_pf(v['high_bin_bias'])} |"
        )
    lines.append('')
    biases = [(m, pb[m]['bias_paired']) for m in MODELS if pb[m].get('bias_paired') is not None]
    low_high = []
    for m in MODELS:
        lb = pb[m].get('low_bin_bias'); hb = pb[m].get('high_bin_bias')
        if lb is not None and hb is not None:
            low_high.append((m, lb, hb, hb - lb))
    interp = []
    if biases:
        interp.append('**Interpretation.** Paired pricing biases are '
            + ', '.join(f"{m.split('-')[0]} {b:+.2f}" for m, b in biases) + '. ')
    if low_high:
        interp.append('Across low/high split, bias changes by '
            + ', '.join(f"{m.split('-')[0]} Δ={d:+.2f}" for m, _, _, d in low_high) + '. ')
    interp.append('Positive paired bias + bias ≈ logistic threshold ⇒ thresholds are inflated '
                  'break-evens, not risk-aversion: models stop when emit-inflated forecast hits ~0, '
                  'landing realized cf_Δ at ≈ −bias. Penalty-Audit direction preserved; magnitude '
                  "reading shifts from 'risk-averse pricing' to 'emissions need de-biasing before "
                  "being read as break-even'.")
    lines.append(''.join(interp))
    lines.append('')

    # Emit per-bin CSV next to rollup
    bin_csv = ROOT / 'results' / 'metacog_calibration_bins.csv'
    with bin_csv.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'model', 'bin_lo', 'bin_hi', 'n', 'p_mean', 'y_mean'])
        for row in calibration_bin_rows:
            w.writerow([
                row['metric'], row['model'],
                f"{row['bin_lo']:.2f}", f"{row['bin_hi']:.2f}", row['n'],
                f"{row['p_mean']:.4f}" if row['p_mean'] is not None else '',
                f"{row['y_mean']:.4f}" if row['y_mean'] is not None else '',
            ])
```

After the block, the existing `Script: ...` / `CSV rollup: ...` lines follow unchanged. Optionally also append:  `lines.append("Calibration bins CSV: \`kaggle_submission/results/metacog_calibration_bins.csv\`")`.

### NOTES
- Script is standalone post-hoc — safe to run any time. Does not re-call LLMs or re-run the harness.
- For user's un-clip-BSS steer: in §3 profile table, also add `M1 BSS raw = 1 - m1_brier / m1_uncertainty` and `M1 Refinement = m1_res / (m1_res + m1_rel)` rows; same for M2. No clipping. Will light up Sonnet-only-positive-BSS story in the report itself.


handover code [[carla-metacog-notable-findings]]
