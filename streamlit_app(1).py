"""
streamlit_app.py - Stock Score Analyzer (Streamlit version)

Run locally:   streamlit run streamlit_app.py
Deploy:        push this folder to GitHub, then deploy on https://share.streamlit.io
"""
import math

import pandas as pd
import streamlit as st

import engine

st.set_page_config(page_title="Stock Score Analyzer", page_icon="📊", layout="wide")


# ---------------------------------------------------------------------------
# Cached helpers (results kept 10 minutes, so reruns / downloads don't re-fetch)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def run_analysis(ticker: str, timeframe: str):
    return engine.analyze(ticker, timeframe)


@st.cache_data(ttl=600, show_spinner=False)
def build_excel(ticker: str, timeframe: str) -> bytes:
    meta, df = run_analysis(ticker, timeframe)
    with open(engine.to_excel(meta, df), "rb") as f:
        return f.read()


def band_color(score):
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return "#8a93a6"
    return "#1c8a5a" if score >= 70 else "#e0912f" if score >= 40 else "#c2452f"


# ---------------------------------------------------------------------------
# Header + inputs
# ---------------------------------------------------------------------------
st.title("Stock Score Analyzer")
st.caption(
    "Search a company. We find its sector and market, calculate 27 indicators, "
    "and score each one against the ideal range for that sector."
)

with st.form("search"):
    c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="bottom")
    query = c1.text_input(
        "Ticker or company name",
        placeholder="Nvidia, AAPL, RELIANCE.NS, TCS.NS",
        help="Indian stocks use .NS (NSE) or .BO (BSE), for example INFY.NS.",
    )
    timeframe = c2.selectbox("Timeframe", list(engine.TIMEFRAMES), index=3)
    submitted = c3.form_submit_button("Analyze", type="primary", use_container_width=True)

# Remember the last request so the page survives reruns (e.g. clicking Download)
if submitted and query.strip():
    st.session_state["req"] = (query.strip(), timeframe)
elif submitted:
    st.warning("Enter a ticker or company name first.")

req = st.session_state.get("req")
if not req:
    st.info("Search a ticker to begin.")
    st.stop()

# ---------------------------------------------------------------------------
# Run analysis
# ---------------------------------------------------------------------------
try:
    with st.spinner(f"Fetching data for {req[0]} and scoring 27 indicators..."):
        meta, df = run_analysis(*req)
except ValueError as e:
    st.error(str(e))
    st.stop()
except Exception as e:  # network problems, Yahoo rate limits, etc.
    st.error(f"Data provider problem: {e}. Please try again in a moment.")
    st.stop()

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
left, right = st.columns([1, 3], vertical_alignment="center")
with left:
    st.markdown(
        f"<div style='font-size:4.5rem;font-weight:700;line-height:1;color:{band_color(meta['overall'])}'>"
        f"{round(meta['overall'])}<span style='font-size:1.3rem;color:#8a93a6'>/100</span></div>"
        f"<div style='font-weight:600;font-size:1.1rem;color:{band_color(meta['overall'])}'>{meta['rating']}</div>",
        unsafe_allow_html=True,
    )
with right:
    st.subheader(f"{meta['name']}  ·  {meta['symbol']}")
    price = f"{meta['price']:,.2f} {meta['currency']}" if meta["price"] is not None else "N/A"
    st.write(
        f"**{meta['sector']}** · {meta['industry']} · {meta['market']} market · "
        f"{meta['timeframe']} · Last price {price} · {meta['coverage']} indicators scored"
    )

groups = df.groupby("Group", sort=False)["Score"].mean()
cols = st.columns(len(groups))
for col, (name, val) in zip(cols, groups.items()):
    col.metric(name, "-" if pd.isna(val) else f"{val:.0f}")

# ---------------------------------------------------------------------------
# Indicator table
# ---------------------------------------------------------------------------
st.divider()
f1, f2 = st.columns([3, 1], vertical_alignment="center")
view = f1.radio(
    "Show",
    ["All 27", "Inside range", "Outside range", "No data"],
    horizontal=True,
    label_visibility="collapsed",
)

f2.download_button(
    "Download Excel",
    data=build_excel(*req),
    file_name=f"{meta['symbol']}_{meta['timeframe'].replace(' ', '')}_score.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

table = pd.DataFrame(
    {
        "#": range(1, len(df) + 1),
        "Group": df["Group"],
        "Indicator": df["Indicator"],
        "Value": [engine.fmt_val(r.Value, r.Unit) for r in df.itertuples()],
        f"Ideal range ({meta['sector']}, {meta['market']})": [
            engine.fmt_range(r.Low, r.High, r.Unit) for r in df.itertuples()
        ],
        "Status": df["Status"],
        "Score": df["Score"].round(0),
        "Formula": df["Formula"],
    }
)

mask = {
    "All 27": table["Status"].notna(),
    "Inside range": table["Status"] == "Within",
    "Outside range": table["Status"].isin(["Below", "Above"]),
    "No data": table["Status"] == "No data",
}[view]

st.dataframe(
    table[mask],
    hide_index=True,
    use_container_width=True,
    height=min(900, 38 * (int(mask.sum()) + 1)),
    column_config={
        "#": st.column_config.NumberColumn(width="small"),
        "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
    },
)

st.caption(
    "Data from Yahoo Finance and may be delayed or incomplete. "
    "Scores are a screening aid, not investment advice."
)
