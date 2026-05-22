import json
import os
import requests
from datetime import date, timedelta

_GIST_TOKEN = os.environ.get("GIST_TOKEN", "")
_GIST_ID    = os.environ.get("GIST_ID", "")
_LOCAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signal_history.json")
_GIST_FILE  = "signal_history.json"


def _use_gist():
    return bool(_GIST_TOKEN and _GIST_ID)


# ── Load ───────────────────────────────────────────────────────────────────────

def _load():
    return _load_gist() if _use_gist() else _load_local()


def _load_local():
    if os.path.exists(_LOCAL_FILE):
        try:
            with open(_LOCAL_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _load_gist():
    try:
        r = requests.get(
            f"https://api.github.com/gists/{_GIST_ID}",
            headers={"Authorization": f"token {_GIST_TOKEN}",
                     "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if r.status_code == 200:
            content = r.json()["files"][_GIST_FILE]["content"]
            return json.loads(content)
    except Exception:
        pass
    return {}


# ── Save ───────────────────────────────────────────────────────────────────────

def _save(history):
    # Keep last 60 days
    for old_key in sorted(history)[:-60]:
        del history[old_key]
    if _use_gist():
        _save_gist(history)
    else:
        _save_local(history)


def _save_local(history):
    with open(_LOCAL_FILE, "w") as f:
        json.dump(history, f, indent=2)


def _save_gist(history):
    try:
        requests.patch(
            f"https://api.github.com/gists/{_GIST_ID}",
            headers={"Authorization": f"token {_GIST_TOKEN}",
                     "Accept": "application/vnd.github+json"},
            json={"files": {_GIST_FILE: {"content": json.dumps(history, indent=2)}}},
            timeout=10,
        )
    except Exception:
        pass


# ── Public API ─────────────────────────────────────────────────────────────────

def save_today(oil_score, gold_score, oil_price, gold_price):
    history = _load()
    today = str(date.today())
    if today not in history:
        history[today] = {
            "oil_score":  oil_score,
            "gold_score": gold_score,
            "oil_price":  oil_price,
            "gold_price": gold_price,
        }
        _save(history)


def evaluate_yesterday(today_oil_price, today_gold_price):
    history = _load()
    yesterday = str(date.today() - timedelta(days=1))
    rec = history.get(yesterday)
    if not rec:
        return None

    def _eval(score, prev_price, today_price):
        change = ((today_price - prev_price) / prev_price) * 100
        if score > 3.0:
            correct = change > 0.3
        elif score < 3.0:
            correct = change < -0.3
        else:
            correct = abs(change) < 1.0
        return {"score": score, "prev_price": prev_price,
                "today_price": today_price, "change_pct": change, "correct": correct}

    return {
        "date": yesterday,
        "oil":  _eval(rec["oil_score"],  rec["oil_price"],  today_oil_price),
        "gold": _eval(rec["gold_score"], rec["gold_price"], today_gold_price),
    }


def get_accuracy_table():
    history = _load()
    rows = []
    for d in sorted(history, reverse=True)[:14]:
        rows.append({"date": d, **history[d]})
    return rows
