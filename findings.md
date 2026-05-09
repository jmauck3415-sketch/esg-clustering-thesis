# ESG Clustering — Key Findings

**Dataset:** 430 S&P 500 companies · Sustainalytics ESG Risk Ratings (Kaggle, pre-2023 Yahoo Finance scrape)  
**Method:** k-means++ on (E, S, G) risk scores · silhouette analysis for k=3..8 · one-way ANOVA + Tukey HSD  
**Replicates:** Sariyer & Taşkın (2022), Borsa İstanbul Review — applied to S&P 500 instead of BIST

> **Scale note:** Sustainalytics scores are *risk* ratings — **lower = less ESG risk = better**.  
> The paper uses Refinitiv scores where higher = better. All cluster narratives are inverted relative to the paper.

---

## 1. Optimal Number of Clusters

Silhouette scores for k = 3 to 8:

| k | Silhouette |
|---|---|
| **3** | **0.3553 ← optimal** |
| 4 | 0.3443 |
| 5 | 0.3335 |
| 6 | 0.3068 |
| 7 | 0.3144 |
| 8 | 0.3046 |

**k = 3** is optimal. The paper found k = 5 on 64 BIST firms. The difference is attributable to larger N, different market, and different scoring methodology.

---

## 2. Cluster Centroids (Table 1 equivalent)

Lower centroid = lower risk = better performance on that pillar.

| Cluster | n | E Risk | S Risk | G Risk | Profile |
|---|---|---|---|---|---|
| 1 | 125 | 2.36 | 12.16 | 8.64 | Low environmental risk; high social & governance risk |
| 2 | 122 | 12.56 | 10.07 | 6.10 | High environmental risk; relatively lower governance risk |
| 3 | 183 | 3.50 | 6.29 | 5.83 | Low risk across all pillars — the "best ESG" cluster |

**Cluster 3 is the largest** (183 companies) and has the lowest risk on all three pillars.  
**Cluster 2** stands out for environmental exposure — likely heavy-industry and energy firms.  
**Cluster 1** has negligible environmental risk but elevated social and governance risk.

---

## 3. ANOVA Results (Table 3 equivalent)

One-way ANOVA testing whether clusters differ on Total ESG, ROA, and firm size.  
412 of 430 companies have complete financial data (18 missing — REITs, recent spin-offs).

| Variable | F | p | Significant? |
|---|---|---|---|
| Total ESG Risk | 381.19 | < 0.001 | *** Yes (sanity check — clusters were built on E/S/G) |
| ROA | 4.65 | 0.010 | * Yes |
| ln(Total Assets) | 16.24 | < 0.001 | *** Yes |

**Comparison to paper:** The paper found ROA *not* significantly different across clusters. We find a significant difference (p = 0.010). Size is significant in both.

---

## 4. Tukey HSD Post-hoc Results

Pairwise comparisons for each significant ANOVA. Differences expressed as Cluster B mean minus Cluster A mean (positive = Cluster B is higher/worse risk or higher ROA).

### ROA
The overall F is significant, but the effect is entirely one pair:

| Pair | Mean diff | p-adj | |
|---|---|---|---|
| Cluster 1 vs Cluster 2 | −0.010 | 0.443 | n.s. |
| Cluster 1 vs Cluster 3 | +0.012 | 0.207 | n.s. |
| **Cluster 2 vs Cluster 3** | **+0.022** | **0.008** | ** |

**Interpretation:** Companies with high environmental risk (Cluster 2) have significantly lower ROA than the best-ESG companies (Cluster 3). The social/governance risk cluster (Cluster 1) does not differ significantly from either. The ROA–ESG relationship is specifically about environmental risk and overall ESG quality, not social/governance risk.

### ln(Total Assets)
| Pair | Mean diff | p-adj | |
|---|---|---|---|
| **Cluster 1 vs Cluster 2** | **−0.683** | **< 0.001** | *** |
| **Cluster 1 vs Cluster 3** | **−0.806** | **< 0.001** | *** |
| Cluster 2 vs Cluster 3 | −0.124 | 0.681 | n.s. |

**Interpretation:** Cluster 1 firms (social/governance risk) are significantly *larger* than both other clusters. Clusters 2 and 3 do not differ in size. The size ANOVA effect is driven entirely by Cluster 1.

### Total ESG
All three pairs are significantly different (p < 0.001 each). Expected — clusters were constructed from E/S/G scores which sum to Total ESG.

---

## 5. ROA Robustness (Winsorization)

Raw ROA ranges from −0.021 to 0.521. Tested whether the ANOVA finding survives outlier removal.

| | F | p | Result |
|---|---|---|---|
| Raw ROA | 4.65 | 0.010 | Significant |
| Winsorized 1/99% (clipped to 0.004–0.264) | 5.73 | 0.004 | Significant |
| Winsorized 5/95% (clipped to 0.011–0.178) | 6.19 | 0.002 | Significant |

**The finding strengthens after winsorization.** The outliers were suppressing the difference, not inflating it. The ROA–cluster relationship is not an artifact of extreme values.

---

## 6. Per-cluster Financial Profile

Means across the 412 companies with complete data:

| Cluster | Profile | Total ESG | ROA | ln(Assets) |
|---|---|---|---|---|
| 1 | Low E, High S/G risk | 23.16 | 0.069 (6.9%) | 24.89 — **largest firms** |
| 2 | High E risk | 28.73 — **worst ESG** | 0.060 (6.0%) — **lowest ROA** | 24.21 |
| 3 | Low overall risk | 15.62 — **best ESG** | 0.081 (8.1%) — **highest ROA** | 24.09 |

---

## 7. Consistency with the Paper

| Finding | Paper (BIST) | This study (S&P 500) |
|---|---|---|
| Optimal k | 5 | 3 |
| Clusters differ on ESG | Yes | Yes |
| Clusters differ on ROA | No | Yes (p=0.010) |
| Clusters differ on firm size | Yes | Yes |
| Best-ESG cluster has highest ROA | Yes (governance pillar) | Yes (Cluster 3, all pillars) |

The directional relationship between ESG quality and ROA holds in the same direction as the paper. The difference in ROA significance may reflect the larger and more diverse S&P 500 sample.

---

## 8. Output Files

| File | Contents |
|---|---|
| `output/centroids.csv` | Cluster centroids (Table 1 equivalent) |
| `output/cluster_assignments.csv` | Ticker → cluster mapping (Table 2 equivalent) |
| `output/anova_results.csv` | ANOVA F and p per variable (Table 3 equivalent) |
| `output/tukey_results.csv` | Pairwise Tukey HSD results |
| `output/silhouette_scores.png` | Silhouette bar chart (Figure 2 equivalent) |
| `output/3d_scatter.html` | Interactive 3D ESG cluster scatter |
| `output/sector_heatmap.html` | Cluster composition by GICS sector |
| `output/cluster_boxplots.html` | ROA and firm size by cluster |
| `output/silhouette_plotly.html` | Interactive silhouette chart |
| `website/index.html` | Searchable company ESG dashboard |
