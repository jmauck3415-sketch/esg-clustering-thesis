"""
Step 4: Plotly-based interactive visualizations for ESG clustering results.
All charts saved as standalone HTML files embeddable in any website.

Charts produced:
  output/3d_scatter.html       — companies in E/S/G risk space, colored by cluster
  output/sector_heatmap.html   — cluster composition % by GICS sector
  output/cluster_boxplots.html — ROA + ln(assets) distribution by cluster
  output/silhouette_plotly.html — silhouette scores for k=3..8

Note: Sustainalytics risk scores — lower = better (inverted vs. the paper).
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

df = pd.read_csv("data/esg_clustered.csv")

CLUSTER_COLORS = {1: "#f4a261", 2: "#e63946", 3: "#2a9d8f"}
CLUSTER_LABELS = {
    1: "Cluster 1 – Low E, High S/G Risk",
    2: "Cluster 2 – High E Risk",
    3: "Cluster 3 – Low Overall Risk (Best)",
}

# ── 1. 3D Scatter ─────────────────────────────────────────────────────────────
fig3d = go.Figure()
for c in sorted(df["Cluster"].unique()):
    sub = df[df["Cluster"] == c]
    fig3d.add_trace(go.Scatter3d(
        x=sub["E_Score"], y=sub["S_Score"], z=sub["G_Score"],
        mode="markers",
        name=CLUSTER_LABELS[c],
        marker=dict(size=5, color=CLUSTER_COLORS[c], opacity=0.8),
        customdata=sub[["Ticker", "Name", "Sector", "Total_ESG"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
            "Sector: %{customdata[2]}<br>"
            "E Risk: %{x:.2f} | S Risk: %{y:.2f} | G Risk: %{z:.2f}<br>"
            "Total ESG Risk: %{customdata[3]:.1f}"
            "<extra></extra>"
        ),
    ))
fig3d.update_layout(
    title="ESG Risk Space — S&P 500 Companies by Cluster<br>"
          "<sub>Sustainalytics risk scores: lower = less risk = better. Hover for details.</sub>",
    scene=dict(
        xaxis_title="Environmental Risk",
        yaxis_title="Social Risk",
        zaxis_title="Governance Risk",
    ),
    legend=dict(x=0, y=1),
    margin=dict(l=0, r=0, t=80, b=0),
)
fig3d.write_html("output/3d_scatter.html")
print("Saved output/3d_scatter.html")

# ── 2. Sector Heatmap ─────────────────────────────────────────────────────────
sector_cluster = (
    df.groupby(["Sector", "Cluster"])
    .size()
    .unstack(fill_value=0)
)
sector_pct = sector_cluster.div(sector_cluster.sum(axis=1), axis=0) * 100
sector_pct.columns = [CLUSTER_LABELS[c] for c in sector_pct.columns]
# Sort sectors by % in "best" cluster (Cluster 3) descending
best_col = CLUSTER_LABELS[3]
sector_pct = sector_pct.sort_values(best_col, ascending=False)

fig_hm = px.imshow(
    sector_pct,
    text_auto=".1f",
    color_continuous_scale="RdYlGn",
    labels=dict(x="Cluster", y="Sector", color="% of Sector"),
    title="Cluster Composition by GICS Sector (% of companies per sector)<br>"
          "<sub>Green = more companies in that cluster. Cluster 3 = lowest ESG risk (best).</sub>",
    aspect="auto",
)
fig_hm.update_xaxes(side="bottom", tickangle=-20)
fig_hm.update_layout(coloraxis_showscale=True)
fig_hm.write_html("output/sector_heatmap.html")
print("Saved output/sector_heatmap.html")

# ── 3. Boxplots (ROA + ln(assets) by cluster) ─────────────────────────────────
df_fin = df.dropna(subset=["ROA", "Size_ln"])

fig_box = make_subplots(
    rows=1, cols=2,
    subplot_titles=[
        "Return on Assets (ROA) by Cluster",
        "Firm Size — ln(Total Assets) by Cluster",
    ],
)

for c in sorted(df_fin["Cluster"].unique()):
    sub = df_fin[df_fin["Cluster"] == c]
    show_legend = bool(c == 1)
    fig_box.add_trace(
        go.Box(
            y=sub["ROA"],
            name=CLUSTER_LABELS[c],
            marker_color=CLUSTER_COLORS[c],
            showlegend=show_legend,
            boxpoints="outliers",
        ),
        row=1, col=1,
    )
    fig_box.add_trace(
        go.Box(
            y=sub["Size_ln"],
            name=CLUSTER_LABELS[c],
            marker_color=CLUSTER_COLORS[c],
            showlegend=False,
            boxpoints="outliers",
        ),
        row=1, col=2,
    )

fig_box.update_layout(
    title="Financial Characteristics by ESG Cluster<br>"
          "<sub>ANOVA: ROA F=4.65 p=0.010 · ln(assets) F=16.24 p<0.001</sub>",
    boxmode="group",
    legend=dict(x=0.5, y=-0.15, xanchor="center", orientation="h"),
)
fig_box.update_yaxes(title_text="ROA", row=1, col=1)
fig_box.update_yaxes(title_text="ln(Total Assets)", row=1, col=2)
fig_box.write_html("output/cluster_boxplots.html")
print("Saved output/cluster_boxplots.html")

# ── 4. Silhouette Score Bar Chart ─────────────────────────────────────────────
silhouette_scores = {3: 0.3553, 4: 0.3443, 5: 0.3335, 6: 0.3068, 7: 0.3144, 8: 0.3046}
bar_colors = ["#2a9d8f" if k == 3 else "#8ecae6" for k in silhouette_scores]

fig_sil = go.Figure(go.Bar(
    x=list(silhouette_scores.keys()),
    y=list(silhouette_scores.values()),
    text=[f"{v:.4f}" for v in silhouette_scores.values()],
    textposition="outside",
    marker_color=bar_colors,
    hovertemplate="k=%{x}: silhouette=%{y:.4f}<extra></extra>",
))
fig_sil.add_annotation(
    x=3, y=0.3553 + 0.012,
    text="Optimal (k=3)",
    showarrow=False,
    font=dict(color="#2a9d8f", size=12),
    yshift=12,
)
fig_sil.update_layout(
    title="Silhouette Scores for k = 3 to 8<br>"
          "<sub>Higher = better-separated clusters. k=3 is optimal for this sample.</sub>",
    xaxis=dict(title="Number of Clusters (k)", tickvals=list(silhouette_scores.keys())),
    yaxis=dict(title="Silhouette Score", range=[0, 0.42]),
    plot_bgcolor="#ffffff",
)
fig_sil.write_html("output/silhouette_plotly.html")
print("Saved output/silhouette_plotly.html")

print("\nAll charts generated. Open any .html file in a browser to view.")
