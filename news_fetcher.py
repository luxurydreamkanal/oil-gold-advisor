import feedparser
import requests
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# --- Feed definitions (all free, no API key needed) ---

_OIL_FEEDS = [
    "https://news.google.com/rss/search?q=oil+price+crude+WTI&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=OPEC+oil+production+barrel&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=crude+oil+supply+demand+inventory&hl=en&gl=US&ceid=US:en",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=CL%3DF&region=US&lang=en-US",
]

_GOLD_FEEDS = [
    "https://news.google.com/rss/search?q=gold+price+market+bullion&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=gold+inflation+federal+reserve+dollar&hl=en&gl=US&ceid=US:en",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC%3DF&region=US&lang=en-US",
]

_GEO_FEEDS = [
    "https://news.google.com/rss/search?q=war+conflict+Middle+East+energy&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=geopolitical+risk+sanctions+oil+gold&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Russia+Ukraine+war+energy&hl=en&gl=US&ceid=US:en",
]

_MACRO_FEEDS = [
    "https://news.google.com/rss/search?q=federal+reserve+interest+rates+inflation&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=US+economy+GDP+recession+dollar&hl=en&gl=US&ceid=US:en",
]


def _clean_html(text):
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ")[:400]


def _fetch_feed(url, max_items=12):
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=12)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        cutoff = datetime.utcnow() - timedelta(days=3)
        articles = []
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "").strip()
            if not title:
                continue
            summary = _clean_html(entry.get("summary", entry.get("description", "")))
            link = entry.get("link", "")
            pub = entry.get("published_parsed")
            if pub:
                try:
                    pub_dt = datetime(*pub[:6])
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass
            articles.append({"title": title, "summary": summary, "link": link})
        return articles
    except Exception:
        return []


def _dedup(articles):
    seen, out = set(), []
    for a in articles:
        key = a["title"][:80]
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out


def fetch_all_news():
    result = {"oil": [], "gold": [], "geo": [], "macro": []}
    for key, feeds in [
        ("oil", _OIL_FEEDS),
        ("gold", _GOLD_FEEDS),
        ("geo", _GEO_FEEDS),
        ("macro", _MACRO_FEEDS),
    ]:
        for url in feeds:
            result[key].extend(_fetch_feed(url))
            time.sleep(0.3)
        result[key] = _dedup(result[key])
    return result
