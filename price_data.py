import yfinance as yf
import pandas as pd
import numpy as np


def _calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def get_price_analysis(symbol):
    try:
        df = yf.Ticker(symbol).history(period="30d")
        if df.empty or len(df) < 2:
            return None

        current = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])
        change_pct = ((current - prev) / prev) * 100

        n = len(df)
        ma7 = float(df["Close"].rolling(min(7, n)).mean().iloc[-1])
        ma20 = float(df["Close"].rolling(min(20, n)).mean().iloc[-1])

        rsi_series = _calculate_rsi(df["Close"])
        rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0

        week_ago = float(df["Close"].iloc[-min(8, n)])
        week_trend = ((current - week_ago) / week_ago) * 100

        tech_score = 0.0
        # Price vs MA20
        tech_score += 0.5 if current < ma20 else -0.5
        # RSI signal
        if rsi < 30:
            tech_score += 1.0
        elif rsi > 70:
            tech_score -= 1.0
        elif rsi < 45:
            tech_score += 0.3
        elif rsi > 55:
            tech_score -= 0.3

        return {
            "current_price": current,
            "change_pct": change_pct,
            "ma7": ma7,
            "ma20": ma20,
            "rsi": rsi,
            "week_trend": week_trend,
            "tech_score": float(np.clip(tech_score, -1.5, 1.5)),
            "history": df,
        }
    except Exception:
        return None
