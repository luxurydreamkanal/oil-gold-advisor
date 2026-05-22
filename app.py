import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

from news_fetcher import fetch_all_news
from price_data import get_price_analysis
from analyzer import (
    calculate_score, get_label_and_color,
    OIL_BULLISH, OIL_BEARISH, GOLD_BULLISH, GOLD_BEARISH,
)
from history import save_today, evaluate_yesterday, get_accuracy_table

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Oil & Gold Advisor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #080d17;
}
.stApp { background: linear-gradient(160deg, #080d17 0%, #0a1220 50%, #080d17 100%); }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem !important; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1425 0%, #080d17 100%) !important;
    border-right: 1px solid rgba(0,180,255,0.12) !important;
}
[data-testid="stSidebar"] * { color: #c8d8e8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #ffffff !important; }

/* ── Cards ── */
.card {
    background: linear-gradient(135deg, rgba(15,22,36,0.95) 0%, rgba(10,16,28,0.95) 100%);
    border: 1px solid rgba(0,180,255,0.18);
    border-radius: 20px;
    padding: 28px 24px 22px;
    margin-bottom: 16px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(0,180,255,0.06);
    backdrop-filter: blur(10px);
}
.card-sm {
    background: rgba(15,22,36,0.8);
    border: 1px solid rgba(0,180,255,0.12);
    border-radius: 14px;
    padding: 18px 16px;
    margin-bottom: 10px;
}

/* ── Score display ── */
.score-wrap {
    text-align: center;
    padding: 20px 10px 16px;
    border-radius: 16px;
    margin: 14px 0;
    position: relative;
    overflow: hidden;
}
.score-number {
    font-size: 96px;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -4px;
    display: block;
}
.score-label {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
    display: block;
}
.score-stars {
    font-size: 22px;
    margin-top: 8px;
    display: block;
    letter-spacing: 2px;
}

/* ── Metric boxes ── */
.metric-row { display: flex; gap: 10px; margin: 14px 0; }
.metric-box {
    flex: 1;
    background: rgba(0,180,255,0.06);
    border: 1px solid rgba(0,180,255,0.14);
    border-radius: 12px;
    padding: 14px 12px;
    text-align: center;
}
.metric-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #6b8aaa;
    display: block;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    display: block;
    line-height: 1.2;
}
.metric-change {
    font-size: 11px;
    font-weight: 500;
    margin-top: 2px;
    display: block;
}
.up   { color: #00e5a0; }
.down { color: #ff4d6d; }
.neu  { color: #6b8aaa; }

/* ── Section header ── */
.section-header {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #00b4ff;
    margin: 22px 0 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(0,180,255,0.3), transparent);
}

/* ── News items ── */
.news-item {
    padding: 10px 0;
    border-bottom: 1px solid rgba(0,180,255,0.08);
    font-size: 13px;
    color: #9ab0c8;
    line-height: 1.5;
}
.news-item:last-child { border-bottom: none; }
.news-dot {
    display: inline-block;
    width: 6px; height: 6px;
    background: #00b4ff;
    border-radius: 50%;
    margin-right: 8px;
    vertical-align: middle;
}

/* ── Eval cards ── */
.eval-card {
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 12px;
    border: 1px solid;
}
.eval-correct   { background: rgba(0,229,160,0.07); border-color: rgba(0,229,160,0.25); }
.eval-incorrect { background: rgba(255,77,109,0.07); border-color: rgba(255,77,109,0.25); }
.eval-title  { font-size: 13px; font-weight: 600; color: #6b8aaa; letter-spacing: 1px; text-transform: uppercase; }
.eval-signal { font-size: 22px; font-weight: 800; margin: 4px 0; }
.eval-price  { font-size: 13px; color: #9ab0c8; margin: 2px 0; }
.eval-result { font-size: 14px; font-weight: 700; margin-top: 8px; }

/* ── History table ── */
.stDataFrame { background: transparent !important; }
.stDataFrame th {
    background: rgba(0,180,255,0.1) !important;
    color: #00b4ff !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
.stDataFrame td { color: #c8d8e8 !important; font-size: 13px !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15,22,36,0.8) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(0,180,255,0.12) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #6b8aaa !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,180,255,0.15) !important;
    color: #00b4ff !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(15,22,36,0.6) !important;
    border: 1px solid rgba(0,180,255,0.1) !important;
    border-radius: 10px !important;
    color: #9ab0c8 !important;
    font-size: 13px !important;
}
.streamlit-expanderContent {
    background: rgba(10,14,24,0.6) !important;
    border: 1px solid rgba(0,180,255,0.08) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    color: #9ab0c8 !important;
    font-size: 13px !important;
}

/* ── Button ── */
.stButton > button {
    background: linear-gradient(135deg, #0066cc, #00b4ff) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.5px !important;
    padding: 10px 0 !important;
    box-shadow: 0 4px 16px rgba(0,180,255,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    box-shadow: 0 6px 24px rgba(0,180,255,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #00b4ff !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #080d17; }
::-webkit-scrollbar-thumb { background: rgba(0,180,255,0.3); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:8px 0 20px;">
        <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.5px;">
            📊 Oil & Gold
        </div>
        <div style="font-size:11px;font-weight:600;letter-spacing:2px;
                    text-transform:uppercase;color:#00b4ff;margin-top:2px;">
            Daily Advisor
        </div>
    </div>
    <div style="font-size:12px;color:#6b8aaa;margin-bottom:4px;">
        {datetime.now().strftime('%A, %d %B %Y')}
    </div>
    <div style="font-size:28px;font-weight:700;color:#fff;margin-bottom:20px;">
        {datetime.now().strftime('%H:%M')}
    </div>
    """, unsafe_allow_html=True)

    if st.button("⟳  Obnoviť dáta", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("""
    <div style="margin-top:28px;">
        <div class="section-header">Stupnica</div>
    </div>
    """, unsafe_allow_html=True)

    for score, label, color in [
        (5, "Silná kúpa",   "#00e5a0"),
        (4, "Kúpa",         "#00b4ff"),
        (3, "Neutrálne",    "#f59e0b"),
        (2, "Predaj",       "#ff6b35"),
        (1, "Silný predaj", "#ff4d6d"),
    ]:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;
                    padding:7px 10px;border-radius:8px;margin-bottom:4px;
                    background:rgba(255,255,255,0.03);">
            <div style="width:28px;height:28px;border-radius:8px;
                        background:{color}22;border:1.5px solid {color};
                        display:flex;align-items:center;justify-content:center;
                        font-size:13px;font-weight:800;color:{color};">{score}</div>
            <span style="font-size:13px;color:#c8d8e8;">{label}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:24px;padding:12px;background:rgba(255,77,109,0.06);
                border:1px solid rgba(255,77,109,0.15);border-radius:10px;
                font-size:11px;color:#ff8099;line-height:1.5;">
        ⚠️ Nie je to finančné poradenstvo. Investujte na vlastné riziko.
    </div>
    """, unsafe_allow_html=True)


# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_all():
    news     = fetch_all_news()
    oil_data = get_price_analysis("CL=F")
    gold_data= get_price_analysis("GC=F")
    return news, oil_data, gold_data

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="margin-bottom:24px;">'
    '<div style="font-size:12px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:#00b4ff;margin-bottom:6px;">Denný prehľad trhu</div>'
    '<div style="font-size:30px;font-weight:800;color:#ffffff;letter-spacing:-1px;line-height:1.1;">Ropa &amp; Zlato Advisor</div>'
    '<div style="font-size:13px;color:#4a6a8a;margin-top:6px;">Analýza svetových správ · Technická analýza · Odporúčanie 1–5</div>'
    '</div>',
    unsafe_allow_html=True
)

with st.spinner("Načítavam správy a ceny..."):
    try:
        news, oil_data, gold_data = load_all()
    except Exception as e:
        st.error(f"Chyba: {e}")
        st.stop()

oil_tech  = oil_data["tech_score"]  if oil_data  else 0.0
gold_tech = gold_data["tech_score"] if gold_data else 0.0

oil_score,  oil_reason,  oil_headlines  = calculate_score(
    news["oil"],  news["geo"], news["macro"], OIL_BULLISH,  OIL_BEARISH,  oil_tech,  "oil")
gold_score, gold_reason, gold_headlines = calculate_score(
    news["gold"], news["geo"], news["macro"], GOLD_BULLISH, GOLD_BEARISH, gold_tech, "gold")

# Save & evaluate
oil_p  = oil_data["current_price"]  if oil_data  else None
gold_p = gold_data["current_price"] if gold_data else None
if oil_p and gold_p:
    save_today(oil_score, gold_score, oil_p, gold_p)
evaluation = evaluate_yesterday(oil_p, gold_p) if (oil_p and gold_p) else None


# ── Helper: stars ──────────────────────────────────────────────────────────────
def stars(score):
    n = int(score + 0.5)
    return "★" * n + "☆" * (5 - n)


# ── Helper: mini spark chart ───────────────────────────────────────────────────
def spark_chart(df, color):
    series = df["Close"].tail(14)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(series))),
        y=series.values,
        mode="lines",
        line=dict(color=color, width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
    ))
    fig.update_layout(
        height=80, margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# ── Helper: candlestick chart ──────────────────────────────────────────────────
def candle_chart(df, accent):
    d = df.tail(30)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=d.index, open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"],
        increasing=dict(line=dict(color="#00e5a0"), fillcolor="rgba(0,229,160,0.5)"),
        decreasing=dict(line=dict(color="#ff4d6d"), fillcolor="rgba(255,77,109,0.5)"),
        name="Cena",
    ))
    fig.add_trace(go.Scatter(
        x=d.index, y=d["Close"].rolling(7).mean(),
        name="MA7", line=dict(color="#f59e0b", width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(
        x=d.index, y=d["Close"].rolling(20).mean(),
        name="MA20", line=dict(color=accent, width=1.5)))
    fig.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=8, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", color="#4a6a8a",
                   rangeslider_visible=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", color="#4a6a8a"),
        legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#6b8aaa", size=11)),
    )
    return fig


# ── Commodity card renderer ────────────────────────────────────────────────────
def render_card(name, emoji, accent, data, score, reason, headlines):
    label, color = get_label_and_color(score)

    if score >= 4:
        glow = "0 0 60px rgba(0,229,160,0.12)"
    elif score <= 2:
        glow = "0 0 60px rgba(255,77,109,0.12)"
    else:
        glow = "0 0 40px rgba(0,180,255,0.08)"

    # Card header — single compact lines, no HTML comments
    h = (
        f'<div style="background:linear-gradient(135deg,rgba(15,22,36,0.97),rgba(10,16,28,0.97));'
        f'border:1px solid rgba(0,180,255,0.16);border-radius:20px;'
        f'padding:22px 20px 18px;box-shadow:{glow},0 4px 24px rgba(0,0,0,0.5);margin-bottom:2px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        f'<div>'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#4a6a8a;">{emoji} Komodita</div>'
        f'<div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.5px;margin-top:3px;">{name}</div>'
        f'</div>'
        f'<div style="background:rgba(0,180,255,0.08);border:1px solid rgba(0,180,255,0.2);border-radius:10px;padding:6px 14px;text-align:right;">'
        f'<div style="font-size:9px;color:#4a6a8a;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">Signál</div>'
        f'<div style="font-size:15px;font-weight:800;color:{color};margin-top:2px;">{label}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(h, unsafe_allow_html=True)

    # Metrics row
    if data:
        chg_color = "#00e5a0" if data["change_pct"] >= 0 else "#ff4d6d"
        chg_arrow = "▲" if data["change_pct"] >= 0 else "▼"
        wk_color  = "#00e5a0" if data["week_trend"] >= 0 else "#ff4d6d"
        wk_arrow  = "▲" if data["week_trend"] >= 0 else "▼"
        rsi       = data["rsi"]
        rsi_color = "#00e5a0" if rsi < 35 else ("#ff4d6d" if rsi > 65 else "#f59e0b")
        rsi_lbl   = "Prepredaný" if rsi < 35 else ("Prekúpený" if rsi > 65 else "Normálny")

        m = (
            f'<div class="metric-row">'
            f'<div class="metric-box"><span class="metric-label">Cena USD</span><span class="metric-value">${data["current_price"]:,.2f}</span><span class="metric-change" style="color:{chg_color};">{chg_arrow} {abs(data["change_pct"]):.2f}% dnes</span></div>'
            f'<div class="metric-box"><span class="metric-label">7-dňový trend</span><span class="metric-value" style="color:{wk_color};">{wk_arrow} {abs(data["week_trend"]):.1f}%</span><span class="metric-change neu">za týždeň</span></div>'
            f'<div class="metric-box"><span class="metric-label">RSI</span><span class="metric-value" style="color:{rsi_color};">{rsi:.0f}</span><span class="metric-change" style="color:{rsi_color};">{rsi_lbl}</span></div>'
            f'</div>'
        )
        st.markdown(m, unsafe_allow_html=True)

        # Spark line
        if not data["history"].empty:
            st.plotly_chart(spark_chart(data["history"], accent),
                            use_container_width=True, config={"displayModeBar": False})

    # Score display
    sc = (
        f'<div class="score-wrap" style="background:{color}0d;border:2px solid {color}40;">'
        f'<span class="score-number" style="color:{color};text-shadow:0 0 40px {color}55;">{score:.1f}</span>'
        f'<span class="score-label" style="color:{color};">{label}</span>'
        f'<span class="score-stars" style="color:{color};">{stars(score)}</span>'
        f'</div>'
    )
    st.markdown(sc, unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:12px;color:#4a6a8a;margin:6px 4px 14px;"><span style="color:#00b4ff;">◈</span> {reason}</div>', unsafe_allow_html=True)

    # Candlestick chart
    if data and not data["history"].empty:
        st.markdown('<div class="section-header">Graf (30 dní)</div>', unsafe_allow_html=True)
        st.plotly_chart(candle_chart(data["history"], accent),
                        use_container_width=True, config={"displayModeBar": False})

    # Headlines
    st.markdown('<div class="section-header">Kľúčové správy</div>', unsafe_allow_html=True)
    news_html = ""
    for h in headlines[:6]:
        news_html += f'<div class="news-item"><span class="news-dot"></span>{h}</div>'
    if not headlines:
        news_html = '<div class="news-item" style="color:#4a6a8a;">Žiadne správy k dispozícii.</div>'
    st.markdown(f'<div style="padding:4px 0;">{news_html}</div>', unsafe_allow_html=True)


# ── Main columns ───────────────────────────────────────────────────────────────
col1, col2 = st.columns(2, gap="large")
with col1:
    render_card("Ropa (WTI)", "🛢️", "#00b4ff",
                oil_data, oil_score, oil_reason, oil_headlines)
with col2:
    render_card("Zlato (Gold)", "🥇", "#f59e0b",
                gold_data, gold_score, gold_reason, gold_headlines)


# ── Yesterday evaluation ───────────────────────────────────────────────────────
if evaluation:
    st.markdown('<div style="margin:28px 0 12px;"><div class="section-header">📋 Vyhodnotenie včerajšieho signálu</div></div>', unsafe_allow_html=True)

    ec1, ec2 = st.columns(2, gap="large")

    def render_eval(col, label, emoji, ev):
        lbl, color = get_label_and_color(ev["score"])
        correct    = ev["correct"]
        cls        = "eval-correct" if correct else "eval-incorrect"
        res_color  = "#00e5a0" if correct else "#ff4d6d"
        res_text   = "✅  SIGNÁL BOL SPRÁVNY" if correct else "❌  SIGNÁL BOL NESPRÁVNY"
        chg        = ev["change_pct"]
        chg_arrow  = "▲" if chg > 0 else "▼"
        chg_color  = "#00e5a0" if chg > 0 else "#ff4d6d"

        with col:
            ev_h = (
                f'<div class="eval-card {cls}">'
                f'<div class="eval-title">{emoji} {label}</div>'
                f'<div class="eval-signal" style="color:{color};">{lbl} &nbsp;{ev["score"]:.1f}</div>'
                f'<div class="eval-price">Včera: <b style="color:#fff">${ev["prev_price"]:,.2f}</b> → Dnes: <b style="color:#fff">${ev["today_price"]:,.2f}</b> <span style="color:{chg_color};font-weight:700;">{chg_arrow} {abs(chg):.2f}%</span></div>'
                f'<div class="eval-result" style="color:{res_color};">{res_text}</div>'
                f'</div>'
            )
            st.markdown(ev_h, unsafe_allow_html=True)

    render_eval(ec1, "Ropa",  "🛢️", evaluation["oil"])
    render_eval(ec2, "Zlato", "🥇", evaluation["gold"])


# ── History table ──────────────────────────────────────────────────────────────
history_rows = get_accuracy_table()
if len(history_rows) > 1:
    with st.expander("📅  História signálov — posledných 14 dní"):
        rows_display = []
        for row in history_rows:
            o_lbl, _ = get_label_and_color(row["oil_score"])
            g_lbl, _ = get_label_and_color(row["gold_score"])
            rows_display.append({
                "Dátum":         row["date"],
                "Ropa skóre":    f"{row['oil_score']:.1f}  {o_lbl}",
                "Ropa cena":     f"${row['oil_price']:,.2f}",
                "Zlato skóre":   f"{row['gold_score']:.1f}  {g_lbl}",
                "Zlato cena":    f"${row['gold_price']:,.2f}",
            })
        st.dataframe(pd.DataFrame(rows_display), use_container_width=True, hide_index=True)


# ── News tabs ──────────────────────────────────────────────────────────────────
st.markdown('<div style="margin-top:32px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">Správy</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🛢️  Ropa", "🥇  Zlato", "⚔️  Geopolitika", "📈  Makro"])

def show_news(articles):
    if not articles:
        st.markdown('<p style="color:#4a6a8a;font-size:13px;">Žiadne správy.</p>',
                    unsafe_allow_html=True)
        return
    for a in articles[:12]:
        with st.expander(a["title"]):
            if a.get("summary"):
                st.markdown(f'<span style="color:#9ab0c8;font-size:13px;">{a["summary"]}</span>',
                            unsafe_allow_html=True)
            if a.get("link"):
                st.markdown(f'<a href="{a["link"]}" target="_blank" '
                            f'style="color:#00b4ff;font-size:12px;">Čítať viac ↗</a>',
                            unsafe_allow_html=True)

with tab1: show_news(news["oil"])
with tab2: show_news(news["gold"])
with tab3: show_news(news["geo"])
with tab4: show_news(news["macro"])


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:40px;padding-top:20px;
            border-top:1px solid rgba(0,180,255,0.08);
            text-align:center;font-size:11px;color:#2a4060;letter-spacing:0.5px;">
    Dáta: Google News RSS · Yahoo Finance · Aktualizácia každú hodinu &nbsp;·&nbsp;
    ⚠️ Nie je to finančné poradenstvo
</div>
""", unsafe_allow_html=True)
