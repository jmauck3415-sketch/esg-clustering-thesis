"""
Step 1: Fetch ESG data from Yahoo Finance via yfinance.

Yahoo Finance ESG scores come from Sustainalytics. Key difference from the paper:
- Refinitiv scores: 0-100, HIGHER = better
- Sustainalytics scores: 0-100 risk score, LOWER = better (less ESG risk)

The three pillars available are the same: E, S, G.
"""

import yfinance as yf
import pandas as pd
import time

# S&P 500 tickers with broad ESG coverage — edit this list to match your target universe
TICKERS = [
    "MSFT", "AAPL", "GOOGL", "AMZN", "META", "NVDA", "JPM", "JNJ", "PG", "UNH",
    "V", "MA", "HD", "CVX", "MRK", "ABBV", "PEP", "KO", "AVGO", "COST",
    "WMT", "BAC", "MCD", "TMO", "CSCO", "ACN", "ABT", "DHR", "NEE", "LIN",
    "TXN", "PM", "UPS", "HON", "AMGN", "QCOM", "IBM", "GE", "CAT", "BA",
    "GS", "MS", "BLK", "SPGI", "AXP", "ISRG", "GILD", "CVS", "ANTM", "CI",
    "SO", "DUK", "AEP", "EXC", "SRE", "XOM", "COP", "SLB", "OXY", "MPC",
    "MMM", "EMR", "ETN", "ITW", "ROK", "DE", "CMI", "PH", "GWW", "FDX",
]

records = []

print(f"Fetching ESG data for {len(TICKERS)} tickers...\n")

for ticker in TICKERS:
    try:
        t = yf.Ticker(ticker)
        esg = t.sustainability

        if esg is None or esg.empty:
            print(f"  {ticker}: no ESG data")
            continue

        # yfinance returns a DataFrame with metric names as index, values in "Value" column
        esg_dict = esg["Value"].to_dict() if "Value" in esg.columns else esg.iloc[:, 0].to_dict()

        env = esg_dict.get("environmentScore")
        soc = esg_dict.get("socialScore")
        gov = esg_dict.get("governanceScore")
        total = esg_dict.get("totalEsg")

        if any(v is None for v in [env, soc, gov, total]):
            print(f"  {ticker}: missing one or more pillar scores")
            continue

        records.append({
            "Ticker": ticker,
            "E_Score": float(env),
            "S_Score": float(soc),
            "G_Score": float(gov),
            "Total_ESG": float(total),
        })
        print(f"  {ticker}: E={env}, S={soc}, G={gov}, Total={total}")

    except Exception as e:
        print(f"  {ticker}: error — {e}")

    time.sleep(0.3)  # be polite to the API

df = pd.DataFrame(records)
print(f"\nCollected ESG data for {len(df)} companies.")

if not df.empty:
    df.to_csv("data/esg_scores.csv", index=False)
    print("Saved to data/esg_scores.csv")
else:
    print("No data collected. Check ticker symbols or internet connection.")
