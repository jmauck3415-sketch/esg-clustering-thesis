"""
Step 2: K-means++ clustering on E, S, G risk scores.
Replicates the methodology from Sariyer & Taskin (2022).

NOTE: Sustainalytics scores are RISK scores — lower = better.
The paper uses Refinitiv (higher = better). Cluster narratives must be flipped.
"""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

raw = pd.read_csv("data/SP 500 ESG Risk Ratings.csv")
print(f"Loaded {len(raw)} rows from raw dataset.")

df = raw.rename(columns={
    "Symbol": "Ticker",
    "Environment Risk Score": "E_Score",
    "Social Risk Score": "S_Score",
    "Governance Risk Score": "G_Score",
    "Total ESG Risk score": "Total_ESG",
})

df = df.dropna(subset=["E_Score", "S_Score", "G_Score", "Total_ESG"]).reset_index(drop=True)
print(f"Kept {len(df)} rows with complete E/S/G/Total scores.\n")
print(df[["E_Score", "S_Score", "G_Score", "Total_ESG"]].describe())

X = df[["E_Score", "S_Score", "G_Score"]].values

# --- Silhouette analysis (k = 3..8, matching the paper) ---
silhouette_scores = {}
for k in range(3, 9):
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42)
    labels = km.fit_predict(X)
    silhouette_scores[k] = silhouette_score(X, labels)
    print(f"k={k}: silhouette = {silhouette_scores[k]:.4f}")

optimal_k = max(silhouette_scores, key=silhouette_scores.get)
print(f"\nOptimal k = {optimal_k}")

# --- Bar chart matching paper Figure 2 ---
plt.figure(figsize=(8, 5))
plt.bar(silhouette_scores.keys(), silhouette_scores.values(), color="steelblue")
for k, v in silhouette_scores.items():
    plt.text(k, v + 0.002, f"{v:.4f}", ha="center", fontsize=9)
plt.xlabel("Number of clusters (k)")
plt.ylabel("Silhouette Score")
plt.title("Silhouette Scores for k = 3 to 8")
plt.tight_layout()
plt.savefig("output/silhouette_scores.png", dpi=150)
print("Saved output/silhouette_scores.png")

# --- Final clustering ---
km_final = KMeans(n_clusters=optimal_k, init="k-means++", n_init=10, random_state=42)
df["Cluster"] = km_final.fit_predict(X) + 1  # 1-indexed to match paper

centroids = pd.DataFrame(
    km_final.cluster_centers_,
    columns=["E_centroid", "S_centroid", "G_centroid"],
)
centroids.index = centroids.index + 1
centroids.index.name = "Cluster"
centroids["n"] = df["Cluster"].value_counts().sort_index().values
print("\nCluster Centroids (Table 1 equivalent — RISK scores, lower = better):")
print(centroids.round(2))
centroids.to_csv("output/centroids.csv")

assignments = df[["Ticker", "Cluster"]].sort_values(["Cluster", "Ticker"])
assignments.to_csv("output/cluster_assignments.csv", index=False)
df.to_csv("data/esg_clustered.csv", index=False)
print(f"\nSaved data/esg_clustered.csv ({len(df)} rows) and output/cluster_assignments.csv")
