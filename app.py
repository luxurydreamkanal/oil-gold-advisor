import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from news_fetcher import fetch_all_news
from price_data import get_price_analysis
from analyzer import (
    calculate_score, get_label_and_color,
    OIL_BULLISH, OIL_BEARISH, GOLD_BULLISH, GOLD_BEARISH,
)
from history import save_today, evaluate_yesterday, get_accuracy_table

st.set_page_config(
    page_title="Ropa & Zlato Advisor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .score-card {
        border-radius: 14px;
        padding: 24px 16px 16px;
        text-align: center;
        margin-bottom: 10px;
    }
    .score-num { font-size: 88px; font-weight: 900; line-height: 1; }
    .score-lbl { font-size: 22px; font-weight: 700; margin-top: 4px; }
    .star-row  { font-size: 28px; margin: 6px 0 0; }
    .news-item { padding: 6px 0; border-bottom: 1px solid #eee; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Advisor")
    st.markdown(f"**Dátum:** {datetime.now().strftime('%d.%m.%Y')}")
    st.markdown(f"**Čas:** {datetime.now().strftime('%H:%M')}")
    st.markdown("---")

    if st.button("🔄 Obnoviť dáta", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("### Stupnica odporúčania")
    st.markdown("""
| Skóre | Signál |
|:-----:|--------|
| **5** | Silná kúpa |
| **4** | Kúpa |
| **3** | Neutrálne |
| **2** | Predaj |
| **1** | Silný predaj |
""")
    st.markdown("---")
    st.markdown("### Čo hodnotíme?")
    st.markdown("""
- Správy o rope / zlate
- Geopolitické udalosti
- Makroekonómia (Fed, dolár)
- Technická analýza (RSI, MA)
""")
    st.markdown("---")
    st.caption("⚠️ Nie je to finančné poradenstvo. Investujte na vlastné riziko.")

# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_all():
    news = fetch_all_news()
    oil_data = get_price_analysis("CL=F")
    gold_data = get_price_analysis("GC=F")
    return news, oil_data, gold_data


st.title("📊 Denný Advisor: Ropa & Zlato")
st.markdown("Denné odporúčania na základe svetových správ a technickej analýzy — **zadarmo, bez registrácie**.")

with st.spinner("Načítavam správy a ceny... (prvé spustenie trvá ~20 s)"):
    try:
        news, oil_data, gold_data = load_all()
    except Exception as exc:
        st.error(f"Chyba pri načítavaní dát: {exc}")
        st.stop()

oil_tech = oil_data["tech_score"] if oil_data else 0.0
gold_tech = gold_data["tech_score"] if gold_data else 0.0

oil_score, oil_reason, oil_headlines = calculate_score(
    news["oil"], news["geo"], news["macro"],
    OIL_BULLISH, OIL_BEARISH, oil_tech, "oil",
)
gold_score, gold_reason, gold_headlines = calculate_score(
    news["gold"], news["geo"], news["macro"],
    GOLD_BULLISH, GOLD_BEARISH, gold_tech, "gold",
)

# ── Save today's signals & evaluate yesterday ──────────────────────────────────
oil_price_now  = oil_data["current_price"]  if oil_data  else None
gold_price_now = gold_data["current_price"] if gold_data else None

if oil_price_now and gold_price_now:
    save_today(oil_score, gold_score, oil_price_now, gold_price_now)

evaluation = evaluate_yesterday(oil_price_now, gold_price_now) if (oil_price_now and gold_price_now) else None

if evaluation:
    st.markdown("---")
    st.subheader("📋 Vyhodnotenie včerajšieho signálu")

    def _eval_block(label, ev):
        chg  = ev["change_pct"]
        icon = "✅ SPRÁVNY" if ev["correct"] else "❌ NESPRÁVNY"
        lbl, color = get_label_and_color(ev["score"])
        direction  = "▲" if chg > 0 else "▼"
        color_chg  = "#00aa00" if chg > 0 else "#cc0000"
        st.markdown(f"""
        <div style="border:2px solid {color}; border-radius:10px; padding:14px; background:{color}11;">
            <b>{label}</b><br>
            Včerajší signál: <span style="color:{color}; font-weight:bold;">{lbl} ({ev['score']:.1f})</span><br>
            Cena včera: <b>${ev['prev_price']:,.2f}</b> →
            Dnes: <b>${ev['today_price']:,.2f}</b>
            <span style="color:{color_chg}; font-weight:bold;"> {direction} {abs(chg):.2f}%</span><br>
            Výsledok: <b>{icon}</b>
        </div>
        """, unsafe_allow_html=True)

    ev_col1, ev_col2 = st.columns(2)
    with ev_col1:
        _eval_block("🛢️ Ropa", evaluation["oil"])
    with ev_col2:
        _eval_block("🥇 Zlato", evaluation["gold"])

# ── History table ──────────────────────────────────────────────────────────────
history_rows = get_accuracy_table()
if len(history_rows) > 1:
    st.markdown("---")
    with st.expander("📅 História signálov (posledných 14 dní)"):
        rows_display = []
        for row in history_rows:
            o_lbl, _ = get_label_and_color(row["oil_score"])
            g_lbl, _ = get_label_and_color(row["gold_score"])
            rows_display.append({
                "Dátum":          row["date"],
                "Ropa – skóre":   f"{row['oil_score']:.1f}  {o_lbl}",
                "Ropa – cena":    f"${row['oil_price']:,.2f}",
                "Zlato – skóre":  f"{row['gold_score']:.1f}  {g_lbl}",
                "Zlato – cena":   f"${row['gold_price']:,.2f}",
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows_display), use_container_width=True, hide_index=True)

st.markdown("---")

# ── Commodity columns ──────────────────────────────────────────────────────────
def stars(score):
    filled = int(score + 0.5)
    return "★" * filled + "☆" * (5 - filled)


def render_commodity(name, emoji, data, score, reason, headlines):
    st.subheader(f"{emoji} {name}")

    # Price metrics
    if data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Cena (USD)", f"${data['current_price']:,.2f}",
                  f"{data['change_pct']:+.2f}% dnes")
        c2.metric("7-dňový trend", f"{data['week_trend']:+.1f}%")
        rsi = data["rsi"]
        rsi_note = "Prepredaný 🟢" if rsi < 30 else ("Prekúpený 🔴" if rsi > 70 else "Normálny")
        c3.metric("RSI", f"{rsi:.0f}", rsi_note)
    else:
        st.warning("Cenové dáta nie sú dostupné.")

    # Score card
    label, color = get_label_and_color(score)
    st.markdown(f"""
    <div class="score-card" style="background:{color}18; border:3px solid {color};">
        <div class="score-num" style="color:{color};">{score:.1f}</div>
        <div class="score-lbl" style="color:{color};">{label}</div>
        <div class="star-row" style="color:{color};">{stars(score)}</div>
    </div>
    """, unsafe_allow_html=True)

    st.caption(f"Dôvod: {reason}")

    # Price chart (candlestick + MA)
    if data and not data["history"].empty:
        df = data["history"].tail(30)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="Cena", increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"].rolling(7).mean(),
            name="MA 7", line=dict(color="orange", width=1.5),
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"].rolling(20).mean(),
            name="MA 20", line=dict(color="#4488ff", width=1.5),
        ))
        fig.update_layout(
            height=280, margin=dict(l=0, r=0, t=10, b=0),
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", y=1.05),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Top headlines
    st.markdown("**Kľúčové správy (posledné 48 h)**")
    if headlines:
        for i, h in enumerate(headlines[:6], 1):
            st.markdown(f"<div class='news-item'>{i}. {h}</div>", unsafe_allow_html=True)
    else:
        st.info("Žiadne relevantné správy.")


col_oil, col_gold = st.columns(2, gap="large")
with col_oil:
    render_commodity("Ropa (Crude Oil / WTI)", "🛢️", oil_data,
                     oil_score, oil_reason, oil_headlines)
with col_gold:
    render_commodity("Zlato (Gold)", "🥇", gold_data,
                     gold_score, gold_reason, gold_headlines)

# ── News feed tabs ─────────────────────────────────────────────────────────────
st.markdown("---")
st.header("📰 Prehľad správ")

tab_oil, tab_gold, tab_geo, tab_macro = st.tabs(
    ["🛢️ Ropa", "🥇 Zlato", "⚔️ Geopolitika", "📈 Makroekonomika"]
)


def show_news(articles, limit=12):
    if not articles:
        st.info("Žiadne správy k dispozícii.")
        return
    for a in articles[:limit]:
        with st.expander(a["title"]):
            if a.get("summary"):
                st.write(a["summary"])
            if a.get("link"):
                st.markdown(f"[Otvoriť článok ↗]({a['link']})")


with tab_oil:
    show_news(news["oil"])
with tab_gold:
    show_news(news["gold"])
with tab_geo:
    show_news(news["geo"])
with tab_macro:
    show_news(news["macro"])

st.markdown("---")
st.caption(
    "Dáta: Google News RSS · Yahoo Finance RSS · yfinance (Yahoo Finance) · "
    "Aktualizácia každú hodinu po kliknutí na Obnoviť. "
    "⚠️ Nie je to finančné poradenstvo — investujte na vlastné riziko."
)
