"""
Step 2b: Enrich the clustered dataset with ROA and ln(Total Assets) via yfinance.

The yfinance `sustainability` endpoint is dead, but `info`, `balance_sheet`, and
`financials` still work — that's where ROA and total assets come from.

ROA = Net Income (TTM) / Total Assets (most recent annual)
Size_ln = ln(Total Assets in USD)
"""

import math
import time
import pandas as pd
import yfinance as yf

df = pd.read_csv("data/esg_clustered.csv")
print(f"Loaded {len(df)} clustered companies. Fetching financials...\n")

roa_values = []
size_values = []

for i, ticker in enumerate(df["Ticker"], 1):
    roa = None
    size_ln = None
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        roa = info.get("returnOnAssets")  # already a decimal (e.g. 0.07 = 7%)

        total_assets = info.get("totalAssets")
        if total_assets is None or total_assets <= 0:
            bs = t.balance_sheet
            if bs is not None and not bs.empty and "Total Assets" in bs.index:
                total_assets = float(bs.loc["Total Assets"].iloc[0])

        if total_assets and total_assets > 0:
            size_ln = math.log(total_assets)

        print(f"[{i:3d}/{len(df)}] {ticker:6s} ROA={roa}  ln(Assets)={size_ln}")

    except Exception as e:
        print(f"[{i:3d}/{len(df)}] {ticker:6s} error: {e}")

    roa_values.append(roa)
    size_values.append(size_ln)
    time.sleep(0.15)

df["ROA"] = roa_values
df["Size_ln"] = size_values

before = len(df)
df_complete = df.dropna(subset=["ROA", "Size_ln"])
print(f"\nFinancials retrieved for {len(df_complete)} of {before} companies.")

df.to_csv("data/esg_clustered.csv", index=False)
print("Updated data/esg_clustered.csv with ROA and Size_ln columns.")
