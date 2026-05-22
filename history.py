import json
import os
from datetime import date, timedelta

_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signal_history.json")


def _load():
    if os.path.exists(_FILE):
        try:
            with open(_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_today(oil_score, gold_score, oil_price, gold_price):
    history = _load()
    today = str(date.today())
    # Don't overwrite if already saved today (keep first reading of day)
    if today not in history:
        history[today] = {
            "oil_score": oil_score,
            "gold_score": gold_score,
            "oil_price": oil_price,
            "gold_price": gold_price,
        }
    # Keep last 60 days
    for old_key in sorted(history)[:-60]:
        del history[old_key]
    with open(_FILE, "w") as f:
        json.dump(history, f, indent=2)


def evaluate_yesterday(today_oil_price, today_gold_price):
    """Returns evaluation dict for yesterday's signals, or None if no data."""
    history = _load()
    yesterday = str(date.today() - timedelta(days=1))
    rec = history.get(yesterday)
    if not rec:
        return None

    def _eval(score, prev_price, today_price):
        change = ((today_price - prev_price) / prev_price) * 100
        if score > 3.0:
            correct = change > 0.3   # buy signal → price should rise
        elif score < 3.0:
            correct = change < -0.3  # sell signal → price should fall
        else:
            correct = abs(change) < 1.0  # neutral → small movement
        return {"score": score, "prev_price": prev_price,
                "today_price": today_price, "change_pct": change, "correct": correct}

    return {
        "date": yesterday,
        "oil":  _eval(rec["oil_score"],  rec["oil_price"],  today_oil_price),
        "gold": _eval(rec["gold_score"], rec["gold_price"], today_gold_price),
    }


def get_accuracy_table():
    """Returns list of last 14 days sorted newest-first."""
    history = _load()
    rows = []
    for d in sorted(history, reverse=True)[:14]:
        rows.append({"date": d, **history[d]})
    return rows
