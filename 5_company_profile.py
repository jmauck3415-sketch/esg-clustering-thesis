"""
Step 5: Per-company ESG profile card.

Usage:
    python 5_company_profile.py AAPL
    python 5_company_profile.py TSLA
    python 5_company_profile.py "Microsoft"   (partial name match also works)

Output:
    output/profile_{TICKER}.html  — radar chart + percentile bars + sector peer scatter

Note: Sustainalytics risk scores — lower = better (inverted vs. the paper).
"""

import sys
import pandas as pd
import plotly.graph_objects as go

CLUSTER_COLORS = {1: "#f4a261", 2: "#e63946", 3: "#2a9d8f"}
CLUSTER_LABELS = {
    1: "Cluster 1 – Low E, High S/G Risk",
    2: "Cluster 2 – High E Risk",
    3: "Cluster 3 – Low Overall Risk (Best)",
}

RADAR_METRICS = ["E_Score", "S_Score", "G_Score", "Total_ESG", "Controversy Score"]
RADAR_LABELS  = ["Environmental\nRisk", "Social\nRisk", "Governance\nRisk",
                  "Total ESG\nRisk", "Controversy\nScore"]

df = pd.read_csv("data/esg_clustered.csv")

# ── Resolve query ─────────────────────────────────────────────────────────────
query = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
match = df[df["Ticker"].str.upper() == query.upper()]
if match.empty:
    match = df[df["Name"].str.contains(query, case=False, na=False)]
if match.empty:
    print(f"No company found for: '{query}'")
    print("Try a ticker (e.g. AAPL) or partial company name (e.g. Apple).")
    sys.exit(1)

company = match.iloc[0]
ticker = company["Ticker"]
cluster_n = int(company["Cluster"])
print(f"Generating profile for: {ticker} — {company['Name']} (Cluster {cluster_n})")

# ── Normalize metric to 0–10 across full dataset ──────────────────────────────
def _norm10(series, value):
    mn, mx = series.min(), series.max()
    if mx == mn:
        return 5.0
    return round(10 * (value - mn) / (mx - mn), 2)

# ── Radar chart ───────────────────────────────────────────────────────────────
present_metrics = [m for m in RADAR_METRICS if m in df.columns and pd.notna(company.get(m))]
present_labels  = [RADAR_LABELS[i] for i, m in enumerate(RADAR_METRICS) if m in present_metrics]

cluster_df = df[df["Cluster"] == cluster_n]

def radar_row(source, metrics):
    return [_norm10(df[m], source[m]) for m in metrics]

company_r = radar_row(company, present_metrics)
centroid_r = radar_row(cluster_df[present_metrics].mean(), present_metrics)
average_r  = radar_row(df[present_metrics].mean(), present_metrics)

# Close the polygon by repeating the first value
def close(vals, labels):
    return vals + [vals[0]], labels + [labels[0]]

c_r, c_l = close(company_r, present_labels)
ct_r, _ = close(centroid_r, present_labels)
av_r, _ = close(average_r, present_labels)

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=av_r, theta=c_l, fill=None,
    name="S&P 500 Average",
    line=dict(color="#adb5bd", dash="dot", width=2),
))
fig_radar.add_trace(go.Scatterpolar(
    r=ct_r, theta=c_l, fill=None,
    name=CLUSTER_LABELS[cluster_n],
    line=dict(color=CLUSTER_COLORS[cluster_n], dash="dash", width=2),
))
fig_radar.add_trace(go.Scatterpolar(
    r=c_r, theta=c_l, fill="toself",
    name=f"{ticker}",
    line=dict(color="#1d3557", width=2),
    fillcolor="rgba(29,53,87,0.15)",
))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(range=[0, 10], showticklabels=True, tickfont=dict(size=9))),
    title=f"ESG Risk Profile: {ticker} — {company['Name']}<br>"
          "<sub>Scale 0–10 normalized within S&amp;P 500 sample. "
          "Higher = more risk. Smaller polygon = lower risk (better).</sub>",
    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.15),
    margin=dict(t=100, b=80),
)

# ── Percentile rank bars ──────────────────────────────────────────────────────
pct_metrics = [m for m in RADAR_METRICS if m in df.columns and pd.notna(company.get(m))]
pct_labels  = [RADAR_LABELS[i] for i, m in enumerate(RADAR_METRICS) if m in pct_metrics]

pct_vals = [
    round(100 * df[m].rank(pct=True, na_option="keep").loc[company.name], 1)
    for m in pct_metrics
]
bar_colors = ["#e63946" if v > 66 else "#f4a261" if v > 33 else "#2a9d8f" for v in pct_vals]

fig_pct = go.Figure(go.Bar(
    x=pct_vals,
    y=pct_labels,
    orientation="h",
    marker_color=bar_colors,
    text=[f"{v:.0f}th percentile" for v in pct_vals],
    textposition="inside",
    insidetextanchor="start",
    hovertemplate="%{y}: %{x:.1f}th percentile<extra></extra>",
))
fig_pct.add_vline(x=50, line_dash="dash", line_color="#6c757d",
                  annotation_text="Median", annotation_position="top")
fig_pct.update_layout(
    title=f"ESG Risk Percentile Ranks: {ticker}<br>"
          "<sub>0th percentile = lowest risk in sample (best). "
          "Green &lt; 33rd · Orange 33–66th · Red &gt; 66th.</sub>",
    xaxis=dict(range=[0, 105], title="Percentile (0 = lowest risk, 100 = highest risk)"),
    yaxis=dict(title="", autorange="reversed"),
    margin=dict(l=140),
)

# ── Sector peer scatter ───────────────────────────────────────────────────────
sector = company["Sector"]
peers = df[df["Sector"] == sector].copy()
others = peers[peers["Ticker"] != ticker]

fig_peers = go.Figure()
for c in sorted(others["Cluster"].unique()):
    sub = others[others["Cluster"] == c]
    fig_peers.add_trace(go.Scatter(
        x=sub["E_Score"], y=sub["S_Score"],
        mode="markers",
        name=CLUSTER_LABELS[c],
        marker=dict(color=CLUSTER_COLORS[c], size=9, opacity=0.65),
        customdata=sub[["Ticker", "Name", "Total_ESG"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
            "E: %{x:.2f} | S: %{y:.2f}<br>"
            "Total ESG: %{customdata[2]:.1f}"
            "<extra></extra>"
        ),
    ))
# Highlight the searched company
fig_peers.add_trace(go.Scatter(
    x=[company["E_Score"]], y=[company["S_Score"]],
    mode="markers+text",
    name=ticker,
    marker=dict(color="#1d3557", size=16, symbol="star",
                line=dict(color="white", width=1)),
    text=[ticker],
    textposition="top center",
    textfont=dict(size=13, color="#1d3557"),
    hovertemplate=(
        f"<b>{ticker}</b> — {company['Name']}<br>"
        f"E: {company['E_Score']:.2f} | S: {company['S_Score']:.2f}<br>"
        f"Total ESG: {company['Total_ESG']:.1f}"
        "<extra></extra>"
    ),
))
fig_peers.update_layout(
    title=f"{ticker} vs. {sector} Sector Peers (Environmental vs. Social Risk)<br>"
          "<sub>Lower scores = less risk. Star = selected company.</sub>",
    xaxis_title="Environmental Risk Score (lower = safer)",
    yaxis_title="Social Risk Score (lower = safer)",
    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.2),
)

# ── Assemble single HTML page ─────────────────────────────────────────────────
roa_str = f"{company['ROA']:.1%}" if pd.notna(company.get("ROA")) else "N/A"
size_str = f"{company['Size_ln']:.2f}" if pd.notna(company.get("Size_ln")) else "N/A"
esg_level = company.get("ESG Risk Level", "")
controversy = company.get("Controversy Level", "")

header_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESG Profile: {ticker}</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px 20px;
      background: #f8f9fa;
      color: #212529;
    }}
    h1 {{ color: #1d3557; margin-bottom: 4px; }}
    .subtitle {{ color: #6c757d; margin-top: 0; margin-bottom: 24px; font-size: 1rem; }}
    .info-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 28px;
    }}
    .card {{
      background: #ffffff;
      border-radius: 10px;
      padding: 14px 18px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    .card .label {{ font-size: .78rem; color: #6c757d; text-transform: uppercase; letter-spacing: .04em; }}
    .card .value {{ font-size: 1.15rem; font-weight: 600; color: #1d3557; margin-top: 4px; }}
    .chart-wrap {{
      background: #ffffff;
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    .note {{
      font-size: .82rem;
      color: #6c757d;
      border-left: 3px solid #dee2e6;
      padding: 8px 12px;
      margin: 0 0 20px;
      background: #fff;
      border-radius: 0 6px 6px 0;
    }}
  </style>
</head>
<body>
  <h1>{ticker} — {company['Name']}</h1>
  <p class="subtitle">{sector} · {company.get('Industry', '')}</p>
  <p class="note">
    <strong>Data source:</strong> Sustainalytics ESG Risk Ratings (Kaggle / Yahoo Finance, pre-2023).
    Scores are <em>risk</em> ratings — <strong>lower = less ESG risk = better</strong>.
    This is the inverse of the Refinitiv scale used in academic literature.
  </p>
  <div class="info-grid">
    <div class="card">
      <div class="label">Total ESG Risk Score</div>
      <div class="value">{company['Total_ESG']:.1f} <span style="font-size:.85rem;font-weight:400;color:#6c757d">/ ~50 max</span></div>
    </div>
    <div class="card">
      <div class="label">ESG Risk Level</div>
      <div class="value">{esg_level}</div>
    </div>
    <div class="card">
      <div class="label">ESG Cluster</div>
      <div class="value" style="color:{CLUSTER_COLORS[cluster_n]}">{CLUSTER_LABELS[cluster_n]}</div>
    </div>
    <div class="card">
      <div class="label">Controversy Level</div>
      <div class="value">{controversy}</div>
    </div>
    <div class="card">
      <div class="label">Return on Assets</div>
      <div class="value">{roa_str}</div>
    </div>
    <div class="card">
      <div class="label">Firm Size ln(Assets)</div>
      <div class="value">{size_str}</div>
    </div>
  </div>
"""

footer_html = "</body></html>"

out_path = f"output/profile_{ticker}.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(header_html)
    for i, fig in enumerate([fig_radar, fig_pct, fig_peers]):
        include_js = "cdn" if i == 0 else False
        f.write('<div class="chart-wrap">\n')
        f.write(fig.to_html(full_html=False, include_plotlyjs=include_js))
        f.write("\n</div>\n")
    f.write(footer_html)

print(f"Saved {out_path}")
