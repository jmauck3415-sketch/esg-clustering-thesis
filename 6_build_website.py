"""
Step 6: Generate website data files.

Creates:
  website/data.js      — all 430 companies as JS variables (file://-safe, no server needed)
  website/charts/      — copies of the 4 overview HTML charts

Run this once after any changes to esg_clustered.csv, then open website/index.html.
"""

import json, shutil, os, math
import pandas as pd

os.makedirs("website/charts", exist_ok=True)

df = pd.read_csv("data/esg_clustered.csv")

METRICS = ["E_Score", "S_Score", "G_Score", "Total_ESG", "Controversy Score"]
MKEY    = {"E_Score": "e", "S_Score": "s", "G_Score": "g",
            "Total_ESG": "total_esg", "Controversy Score": "controversy"}
present = [m for m in METRICS if m in df.columns]

mn  = {m: float(df[m].min())  for m in present}
mx  = {m: float(df[m].max())  for m in present}
avg = {m: float(df[m].mean()) for m in present}

def norm10(val, m):
    if mx[m] == mn[m]:
        return 5.0
    return round(10 * (val - mn[m]) / (mx[m] - mn[m]), 3)

def safe(v):
    if v is None:
        return None
    try:
        f = float(v)
        return None if math.isnan(f) else round(f, 4)
    except (TypeError, ValueError):
        return None

def safe_str(v):
    return str(v) if pd.notna(v) else ""

pct_ranks = {m: df[m].rank(pct=True, na_option="keep") for m in present}

def safe_pct(m, idx):
    if m not in pct_ranks:
        return None
    v = pct_ranks[m].iloc[idx]
    return round(float(v) * 100, 1) if pd.notna(v) else None

CLUSTER_COLORS = {1: "#f4a261", 2: "#e63946", 3: "#2a9d8f"}
CLUSTER_LABELS = {
    1: "Cluster 1 – Low E, High S/G Risk",
    2: "Cluster 2 – High E Risk",
    3: "Cluster 3 – Low Overall Risk (Best)",
}

records = []
for idx in range(len(df)):
    row = df.iloc[idx]
    records.append({
        "ticker":              safe_str(row["Ticker"]),
        "name":                safe_str(row["Name"]),
        "sector":              safe_str(row.get("Sector", "")),
        "industry":            safe_str(row.get("Industry", "")),
        "cluster":             int(row["Cluster"]),
        "e_score":             safe(row["E_Score"]),
        "s_score":             safe(row["S_Score"]),
        "g_score":             safe(row["G_Score"]),
        "total_esg":           safe(row["Total_ESG"]),
        "controversy_score":   safe(row.get("Controversy Score")),
        "controversy_level":   safe_str(row.get("Controversy Level", "")),
        "esg_risk_level":      safe_str(row.get("ESG Risk Level", "")),
        "esg_risk_percentile": safe_str(row.get("ESG Risk Percentile", "")),
        "roa":                 safe(row.get("ROA")),
        "size_ln":             safe(row.get("Size_ln")),
        # pre-computed normalized scores (0–10, higher = more risk)
        "e_norm":              norm10(float(row["E_Score"]), "E_Score"),
        "s_norm":              norm10(float(row["S_Score"]), "S_Score"),
        "g_norm":              norm10(float(row["G_Score"]), "G_Score"),
        "total_esg_norm":      norm10(float(row["Total_ESG"]), "Total_ESG"),
        "controversy_norm":    norm10(float(row["Controversy Score"]), "Controversy Score")
                               if "Controversy Score" in present and pd.notna(row.get("Controversy Score")) else None,
        # pre-computed percentile ranks (0 = lowest risk = best, 100 = worst)
        "e_pct":               safe_pct("E_Score", idx),
        "s_pct":               safe_pct("S_Score", idx),
        "g_pct":               safe_pct("G_Score", idx),
        "total_esg_pct":       safe_pct("Total_ESG", idx),
        "controversy_pct":     safe_pct("Controversy Score", idx),
    })

# Cluster centroids (normalized) + labels/colors
cluster_stats = {}
for c in [1, 2, 3]:
    sub = df[df["Cluster"] == c]
    entry = {"label": CLUSTER_LABELS[c], "color": CLUSTER_COLORS[c], "n": int(len(sub))}
    for m in present:
        entry[MKEY[m] + "_norm"] = round(norm10(float(sub[m].mean()), m), 3)
    cluster_stats[str(c)] = entry

avg_entry = {MKEY[m] + "_norm": round(norm10(avg[m], m), 3) for m in present}

stats_obj = {
    "clusters": cluster_stats,
    "average":  avg_entry,
    "n_companies": len(df),
}

with open("website/data.js", "w", encoding="utf-8") as f:
    f.write("const ESG_DATA=")
    json.dump(records, f, separators=(",", ":"))
    f.write(";\nconst ESG_STATS=")
    json.dump(stats_obj, f, separators=(",", ":"))
    f.write(";\n")

size_kb = os.path.getsize("website/data.js") // 1024
print(f"Saved website/data.js  ({len(records)} companies, {size_kb} KB)")

for fname in ["3d_scatter.html", "sector_heatmap.html", "cluster_boxplots.html", "silhouette_plotly.html"]:
    shutil.copy(f"output/{fname}", f"website/charts/{fname}")
    print(f"Copied  output/{fname} -> website/charts/{fname}")

print("\nOpen website/index.html in your browser.")
