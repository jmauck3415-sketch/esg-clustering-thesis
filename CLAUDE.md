# Thesis: ESG Clustering Project

## Goal

Replicate the methodology from **Sariyer & Taşkın (2022)** — "Clustering of firms based on environmental, social, and governance ratings: Evidence from BIST sustainability index" (Borsa İstanbul Review) — but apply it to the **S&P 500** instead of the BIST Sustainability Index, since Refinitiv data is paywalled.

The paper PDF is at the project root: `Clustering-of-firms-based-on-environmental--social--and-gove_2022_Borsa-Ista.pdf`.

## Methodology (from the paper)

1. Pull E, S, G pillar scores for each company in the index.
2. Run k-means++ clustering on the (E, S, G) vectors.
3. Use silhouette scores across k = 3..8 to pick the optimal k (the paper got k=5).
4. Report cluster centroids (paper Table 1) and company assignments (paper Table 2).
5. Test whether clusters differ on Total ESG score, ROA, and firm size (ln assets) using one-way ANOVA (paper Table 3).

## Critical data caveat — read before interpreting results

The paper uses **Refinitiv ESG scores**: 0–100 scale, **higher = better performance**.

This project uses **Sustainalytics ESG Risk Ratings** (Kaggle dataset, originally scraped from Yahoo Finance before Yahoo removed the endpoint in 2023): 0–50+ scale, **lower = less ESG risk (better)**.

**The scales are inverted.** When interpreting results:
- A cluster with low E/S/G "scores" in our data = lower ESG *risk* = roughly equivalent to *high* performance in the paper.
- Cluster labels and narratives must be flipped relative to the paper.
- This must be flagged explicitly in the thesis write-up.

## Data

- **Source**: Kaggle — "S&P 500 ESG Risk Ratings" dataset (Sustainalytics-derived).
- **File**: `data/SP 500 ESG Risk Ratings.csv` (note the spaces in the filename — keep them; pandas handles it fine, scripts already use the literal name).
- **Raw size**: 503 rows. Many companies have empty score columns (Sustainalytics doesn't cover the entire S&P 500).
- **After filtering** to rows with all four scores (E, S, G, Total ESG) present: **430 companies**.
- **Key columns we use**: `Symbol` → `Ticker`, `Environment Risk Score` → `E_Score`, `Social Risk Score` → `S_Score`, `Governance Risk Score` → `G_Score`, `Total ESG Risk score` → `Total_ESG`. The rename happens in [2_cluster.py](2_cluster.py).

## Yahoo Finance / yfinance — what works and what doesn't

Tested with `yfinance==1.3.0` (May 2026):

| Endpoint | Status | Notes |
|---|---|---|
| `Ticker.sustainability` | **DEAD** — returns 404 / empty DataFrame for every ticker | Why we abandoned plan A and switched to Kaggle |
| `Ticker.info["returnOnAssets"]` | **Works** | Already a decimal (0.07 = 7%), no need to divide by 100 |
| `Ticker.info["totalAssets"]` | **Returns None** for most tickers — don't rely on it | |
| `Ticker.balance_sheet.loc["Total Assets"].iloc[0]` | **Works** | Use this as the source of truth for firm size |
| `Ticker.financials`, `Ticker.cashflow` | Work | Available but we don't currently use them |

[2b_add_financials.py](2b_add_financials.py) implements the working pattern: ROA from `info`, total assets from `balance_sheet` with `info.totalAssets` as a fallback (which is the wrong way around, since `info` almost always returns None — but kept for robustness if Yahoo ever restores it).

## Results so far

Running [2_cluster.py](2_cluster.py) on the 430-row cleaned dataset:

| k | Silhouette |
|---|---|
| **3** | **0.3553** ← optimal |
| 4 | 0.3443 |
| 5 | 0.3335 |
| 6 | 0.3068 |
| 7 | 0.3144 |
| 8 | 0.3046 |

**Optimal k = 3** for our sample (the paper got k=5 on 64 BIST firms). The difference is worth discussing in the thesis — larger N + different score distribution likely explains it.

Cluster centroids (remember: lower = less ESG risk = better):

| Cluster | E | S | G | n | Profile |
|---|---|---|---|---|---|
| 1 | 2.36 | 12.16 | 8.64 | 125 | Low environmental risk, high social + governance risk |
| 2 | 12.56 | 10.07 | 6.10 | 122 | High environmental risk, lower governance risk |
| 3 | 3.50 | 6.29 | 5.83 | 183 | Low risk across all three pillars (the "best" cluster) |

After running [2b_add_financials.py](2b_add_financials.py): **412 of 430 companies** have complete ROA + ln(assets) data (18 missing — yfinance returned no financials, mostly REITs and recently spun-off entities).

[3_evaluate.py](3_evaluate.py) ANOVA + Tukey HSD results:

| Variable | F | p | Interpretation |
|---|---|---|---|
| Total ESG risk | 381.2 | <0.001 | Highly significant — sanity check |
| ROA | 4.65 | 0.010 | **Significant** — paper found ROA *not* significant; we do |
| ln(assets) | 16.24 | <0.001 | Significant — paper also found size differs |

Per-cluster means:

| Cluster | Profile | Total ESG | ROA | ln(assets) |
|---|---|---|---|---|
| 1 | Low E, high S+G risk | 23.16 | 0.069 | 24.89 (largest) |
| 2 | High E risk | 28.73 (worst) | 0.060 (lowest) | 24.21 |
| 3 | Low all-around (best) | 15.62 (best) | 0.081 (highest) | 24.09 |

**Tukey HSD post-hoc** (see `output/tukey_results.csv`):
- **ROA**: only Cluster 2 vs Cluster 3 is significant (diff=+0.022, p=0.008). Cluster 1 doesn't differ from either. The ROA effect is specifically about environmental risk vs. overall ESG quality — not social/governance risk.
- **Size**: Cluster 1 is significantly larger than both Clusters 2 and 3. Clusters 2 and 3 don't differ in size (p=0.68). The size ANOVA effect is driven entirely by Cluster 1.

**ROA robustness — winsorization**:
| | F | p |
|---|---|---|
| Raw (max=0.521) | 4.65 | 0.010 |
| Winsorized 1/99% | 5.73 | 0.004 |
| Winsorized 5/95% | 6.19 | 0.002 |

Finding **strengthens** after winsorization — outliers were suppressing, not inflating, the difference. Not an artifact.

**Key finding consistent with the paper**: the cluster with the lowest ESG risk (Cluster 3) has the highest ROA. The paper found the cluster with highest *governance* performance had the highest ROA; in our data, Cluster 3 has both the lowest governance risk and the highest ROA, so the relationship holds in the same direction.

## Repo layout

```
Thesis/
├── CLAUDE.md                          # this file
├── findings.md                        # plain-English summary of all key findings
├── Clustering-...pdf                  # the paper being replicated
├── 1_fetch_data.py                    # OBSOLETE — Yahoo ESG endpoint dead, kept for record
├── 2_cluster.py                       # silhouette + k-means++ + centroids + assignments
├── 2b_add_financials.py               # enriches esg_clustered.csv with ROA + Size_ln via yfinance
├── 3_evaluate.py                      # ANOVA + Tukey HSD + ROA winsorization robustness
├── 4_visualize.py                     # Plotly overview charts → output/*.html
├── 5_company_profile.py               # per-company profile card → output/profile_{TICKER}.html
├── 6_build_website.py                 # exports website/data.js + copies charts; run after any data change
├── data/
│   ├── SP 500 ESG Risk Ratings.csv    # raw Kaggle dataset (503 rows)
│   └── esg_clustered.csv              # cleaned data (430 rows) + Cluster + ROA + Size_ln
├── output/
│   ├── silhouette_scores.png          # matplotlib bar chart (paper Fig. 2 equivalent)
│   ├── silhouette_plotly.html         # interactive Plotly version
│   ├── centroids.csv                  # paper Table 1 equivalent
│   ├── cluster_assignments.csv        # paper Table 2 equivalent (ticker → cluster)
│   ├── anova_results.csv              # paper Table 3 equivalent
│   ├── tukey_results.csv              # Tukey HSD pairwise comparisons
│   ├── 3d_scatter.html                # all 430 companies in E/S/G space by cluster
│   ├── sector_heatmap.html            # cluster % composition by GICS sector
│   ├── cluster_boxplots.html          # ROA + ln(assets) distributions by cluster
│   └── profile_{TICKER}.html          # per-company profile (generated by 5_company_profile.py)
└── website/
    ├── index.html                     # searchable ESG dashboard (works from file://)
    ├── data.js                        # all 430 companies as JS variable (generated by 6_build_website.py)
    └── charts/                        # copies of the 4 overview HTML charts
```

## Tech stack

- Python 3.14, Windows 10, PowerShell
- `pandas`, `scikit-learn` (`KMeans`, `silhouette_score`), `scipy.stats` (`f_oneway`, `tukey_hsd`), `matplotlib`, `plotly`, `yfinance==1.3.0`
- All installed via `python -m pip install ...` (note: `pip` is not on PATH on this machine, must use `python -m pip`)

## How to run

```powershell
cd C:\Users\jmauc\Desktop\Thesis
python 2_cluster.py          # silhouette analysis + k-means++ + centroids + assignments
python 2b_add_financials.py  # enriches with ROA + ln(assets) via yfinance — takes ~1-2 min
python 3_evaluate.py         # ANOVA + Tukey HSD + ROA winsorization robustness
python 4_visualize.py        # Plotly overview charts → output/*.html
python 5_company_profile.py AAPL   # per-company profile → output/profile_AAPL.html
python 6_build_website.py    # regenerate website/data.js after any data change
```

`1_fetch_data.py` is no longer used. Kept as a record of the dead-end Yahoo `sustainability` attempt.

## Open questions / next steps

- Confirm with supervisor that method-replication on a different index (S&P 500 vs BIST) satisfies the thesis requirement.
- Decide how to handle the inverted scale in the write-up — translate to a "performance" frame, or keep risk framing throughout.
- Discuss why our optimal k=3 differs from the paper's k=5 (sample size, market, scoring methodology all differ).
- ✅ Done: 412/430 companies enriched, ANOVA run, governance/ROA relationship confirmed.
- ✅ Done: Tukey HSD post-hoc tests added to `3_evaluate.py` — ROA effect is Cluster 2 vs 3 only.
- ✅ Done: ROA winsorization robustness — finding strengthens, not an outlier artifact.
- ✅ Done: Plotly visualizations (3D scatter, sector heatmap, boxplots, silhouette).
- ✅ Done: Searchable website (`website/index.html`) with company profile cards.
- Write up the empirical chapter using `findings.md` as a reference.

## Conventions / preferences (from this session)

- User asked for CLAUDE.md to capture context for future chats — keep this file current after notable findings.
- Script numbering convention: `1_*`, `2_*`, `2b_*`, `3_*` — preserves run order even when sub-steps get inserted.
- Markdown links to local files use relative paths (e.g. `[2_cluster.py](2_cluster.py)`) so they're clickable in VSCode.
