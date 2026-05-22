import numpy as np

# --- Domain-specific keyword dictionaries with weights ---

OIL_BULLISH = {
    "opec cut": 1.8, "production cut": 1.6, "supply cut": 1.6, "output cut": 1.6,
    "opec+": 0.5, "quota cut": 1.4, "voluntary cut": 1.2,
    "supply disruption": 1.4, "pipeline attack": 1.4, "refinery attack": 1.2,
    "oil field attack": 1.2, "strait of hormuz": 1.5, "houthi attack": 1.2,
    "iran sanctions": 1.2, "russia sanctions": 1.0, "venezuela sanctions": 0.8,
    "inventory draw": 1.0, "stockpile draw": 1.0, "crude draw": 1.0,
    "strong demand": 0.8, "china demand": 0.9, "economic growth": 0.5,
    "middle east tension": 0.9, "undersupply": 1.1, "supply tight": 0.8,
    "oil rally": 0.6, "crude rises": 0.5, "oil jumps": 0.7,
    "ceasefire fails": 0.8, "escalation": 0.7,
}

OIL_BEARISH = {
    "opec increase": 1.8, "production increase": 1.4, "output increase": 1.4,
    "opec raises": 1.5, "quota increase": 1.4, "supply surge": 1.2,
    "inventory build": 1.0, "stockpile build": 1.0, "crude build": 1.0,
    "recession": 1.0, "demand slowdown": 1.0, "economic slowdown": 0.9,
    "demand weakness": 0.8, "ev adoption": 0.5, "oil glut": 1.2,
    "oversupply": 1.2, "ceasefire": 0.7, "peace deal": 0.6,
    "oil falls": 0.7, "crude drops": 0.7, "oil slides": 0.7,
    "wti drops": 0.7, "rate hike": 0.5, "strong dollar": 0.5,
}

GOLD_BULLISH = {
    "war": 1.0, "military strike": 1.3, "invasion": 1.2, "attack": 0.6,
    "nuclear": 1.0, "conflict escalat": 0.9, "geopolitical": 0.6,
    "sanctions": 0.6, "trade war": 0.8,
    "rate cut": 1.4, "fed cut": 1.4, "interest rate cut": 1.4,
    "rate pause": 0.8, "dovish": 0.8, "quantitative easing": 1.0,
    "inflation high": 1.1, "inflation surge": 1.1, "cpi rises": 0.9,
    "dollar weakness": 0.9, "dollar falls": 0.9, "usd drops": 0.9,
    "stock market crash": 1.3, "market sell-off": 1.0, "equities fall": 0.8,
    "banking crisis": 1.3, "financial crisis": 1.3, "recession": 0.9,
    "uncertainty": 0.6, "safe haven": 1.1, "central bank gold": 1.1,
    "gold demand": 0.8, "gold rally": 0.6, "gold rises": 0.6,
    "buy gold": 0.8, "stagflation": 1.0,
}

GOLD_BEARISH = {
    "rate hike": 1.4, "fed hike": 1.4, "interest rate rise": 1.2,
    "hawkish": 0.9, "tightening": 0.7, "higher for longer": 0.9,
    "dollar strength": 0.9, "dollar rises": 0.9, "usd rallies": 0.9,
    "risk-on": 0.7, "risk appetite": 0.6, "economic recovery": 0.6,
    "ceasefire": 0.7, "peace deal": 0.6, "de-escalation": 0.6,
    "stock market rally": 0.8, "equities rise": 0.7,
    "gold falls": 0.7, "gold drops": 0.7, "sell gold": 0.8,
    "inflation cools": 1.0, "inflation falls": 1.0, "cpi drops": 0.9,
    "strong economy": 0.6, "gdp growth": 0.5,
}


def _count_signals(articles, bull_kw, bear_kw, weight_factor=1.0):
    bull = bear = 0.0
    for a in articles:
        text = (a["title"] + " " + a.get("summary", "")).lower()
        for kw, w in bull_kw.items():
            if kw in text:
                bull += w * weight_factor
        for kw, w in bear_kw.items():
            if kw in text:
                bear += w * weight_factor
    return bull, bear


def calculate_score(commodity_news, geo_news, macro_news,
                    bull_kw, bear_kw, tech_score, commodity_type):
    geo_w = 1.0 if commodity_type == "gold" else 0.6
    macro_w = 0.8 if commodity_type == "gold" else 0.3

    b1, s1 = _count_signals(commodity_news[:20], bull_kw, bear_kw, 1.0)
    b2, s2 = _count_signals(geo_news[:15], bull_kw, bear_kw, geo_w)
    b3, s3 = _count_signals(macro_news[:10], bull_kw, bear_kw, macro_w)

    net = (b1 + b2 + b3) - (s1 + s2 + s3)
    # net=10 → +2 adjustment (max), net=-10 → -2 adjustment
    kw_adj = float(np.clip(net / 5.0, -2.0, 2.0))
    tech_adj = float(np.clip(tech_score, -1.5, 1.5))

    # kw_adj contributes ±1.5, tech_adj contributes ±0.5 → total range [1, 5]
    final = 3.0 + kw_adj * 0.75 + tech_adj * 0.33
    final = float(np.clip(final, 1.0, 5.0))
    # Round to nearest 0.5
    final = round(final * 2) / 2

    reasons = _build_reasons(kw_adj, tech_score, commodity_type)
    top_news = [a["title"] for a in (commodity_news + geo_news)[:10]]
    return final, reasons, top_news


def _build_reasons(kw_adj, tech_score, commodity_type):
    parts = []
    if kw_adj > 0.8:
        parts.append("silné bullish správy (kúpa)")
    elif kw_adj > 0.2:
        parts.append("mierne bullish správy")
    elif kw_adj < -0.8:
        parts.append("silné bearish správy (predaj)")
    elif kw_adj < -0.2:
        parts.append("mierne bearish správy")
    else:
        parts.append("správy sú neutrálne")

    if tech_score > 0.5:
        parts.append("technicky prepredaný (nízke RSI / pod MA)")
    elif tech_score < -0.5:
        parts.append("technicky prekúpený (vysoké RSI / nad MA)")

    return ", ".join(parts) if parts else "neutrálny signál"


def get_label_and_color(score):
    if score >= 4.5:
        return "SILNÁ KÚPA", "#00aa00"
    elif score >= 3.5:
        return "KÚPA", "#66bb00"
    elif score >= 2.5:
        return "NEUTRÁLNE", "#cc9900"
    elif score >= 1.5:
        return "PREDAJ", "#ee5500"
    else:
        return "SILNÝ PREDAJ", "#cc0000"
