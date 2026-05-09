"""
Step 3: Evaluate cluster differences using ANOVA + Tukey HSD post-hoc + ROA robustness.
Replicates Table 3 from Sariyer & Taskın (2022) and extends it.

Outputs:
  output/anova_results.csv   — ANOVA F/p per variable (paper Table 3 equivalent)
  output/tukey_results.csv   — pairwise Tukey HSD results for significant variables
"""

import pandas as pd
import numpy as np
from scipy import stats
import scipy.stats as ss

df = pd.read_csv("data/esg_clustered.csv")

eval_cols = [c for c in ["Total_ESG", "ROA", "Size_ln"] if c in df.columns]

if not eval_cols:
    print("No evaluation columns found. Add ROA and Size_ln to esg_clustered.csv first.")
    exit()

cluster_ids = sorted(df["Cluster"].unique())

print("=== Descriptive Statistics and ANOVA by Cluster (Table 3 equivalent) ===\n")

anova_results = []
tukey_rows    = []

for col in eval_cols:
    print(f"--- {col} ---")
    groups = [df[df["Cluster"] == c][col].dropna().values for c in cluster_ids]

    for cid, vals_arr in zip(cluster_ids, groups):
        vals = pd.Series(vals_arr)
        ci   = ss.t.interval(0.95, len(vals) - 1, loc=vals.mean(), scale=ss.sem(vals))
        print(f"  Cluster {cid}: n={len(vals)}, mean={vals.mean():.4f}, "
              f"std={vals.std():.4f}, 95% CI=[{ci[0]:.4f}, {ci[1]:.4f}]")

    f_stat, p_val = stats.f_oneway(*groups)
    sig_flag = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "n.s."
    print(f"  ANOVA: F={f_stat:.3f}, p={p_val:.4f} {sig_flag}\n")
    anova_results.append({"Variable": col, "F_stat": round(f_stat, 3), "p_value": round(p_val, 4)})

    # ── Tukey HSD post-hoc (only for significant ANOVA) ─────────────────────
    if p_val < 0.05:
        try:
            tukey = ss.tukey_hsd(*groups)
            print(f"  Tukey HSD pairwise comparisons:")
            for i in range(len(cluster_ids)):
                for j in range(i + 1, len(cluster_ids)):
                    ci_id, cj_id = cluster_ids[i], cluster_ids[j]
                    p_adj   = float(tukey.pvalue[i][j])
                    diff    = groups[j].mean() - groups[i].mean()
                    sig     = "***" if p_adj < 0.001 else "**" if p_adj < 0.01 else "*" if p_adj < 0.05 else "n.s."
                    print(f"    Cluster {ci_id} vs Cluster {cj_id}: "
                          f"diff={diff:+.4f}, p-adj={p_adj:.4f} {sig}")
                    tukey_rows.append({
                        "Variable":  col,
                        "Cluster_A": ci_id, "Cluster_B": cj_id,
                        "Mean_diff": round(diff, 4),
                        "p_adj":     round(p_adj, 4),
                        "Sig":       sig,
                    })
            print()
        except AttributeError:
            print("  (Tukey HSD requires scipy >= 1.8 — skipping)\n")

pd.DataFrame(anova_results).to_csv("output/anova_results.csv", index=False)
print("Saved output/anova_results.csv")

if tukey_rows:
    pd.DataFrame(tukey_rows).to_csv("output/tukey_results.csv", index=False)
    print("Saved output/tukey_results.csv")

# ── ROA robustness: winsorization ─────────────────────────────────────────────
if "ROA" in df.columns:
    print("\n=== ROA Robustness: Effect of Winsorization ===\n")
    roa_df = df.dropna(subset=["ROA"]).copy()

    # Baseline (raw)
    raw_groups = [roa_df[roa_df["Cluster"] == c]["ROA"].values for c in cluster_ids]
    f0, p0 = stats.f_oneway(*raw_groups)
    print(f"  Raw ROA      : F={f0:.3f}, p={p0:.4f}  "
          f"(max={roa_df['ROA'].max():.3f}, min={roa_df['ROA'].min():.3f})")

    for lo_pct, hi_pct in [(1, 99), (5, 95)]:
        lo = roa_df["ROA"].quantile(lo_pct / 100)
        hi = roa_df["ROA"].quantile(hi_pct / 100)
        winsor = roa_df["ROA"].clip(lower=lo, upper=hi)
        w_groups = [winsor[roa_df["Cluster"] == c].values for c in cluster_ids]
        fw, pw = stats.f_oneway(*w_groups)
        direction = "significant" if pw < 0.05 else "NOT significant"
        print(f"  Winsorized {lo_pct:2d}/{hi_pct:2d}%: F={fw:.3f}, p={pw:.4f}  "
              f"[clipped to {lo:.3f} to {hi:.3f}] -> {direction}")

    print()
    print("  Interpretation: if ROA remains significant after winsorization,")
    print("  the cluster difference is not driven by a few extreme ROA outliers.")
