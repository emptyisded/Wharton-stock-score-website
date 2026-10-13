"""
streamlit_app.py - Stock Score Analyzer (Streamlit version, styled to match the original web design)

Run locally:   streamlit run streamlit_app.py
Deploy:        push this folder (incl. .streamlit/config.toml) to GitHub, deploy on share.streamlit.io
"""
import html
import math

import pandas as pd
import streamlit as st

import engine

st.set_page_config(page_title="Stock Score Analyzer", page_icon="📊", layout="wide")

TIMEFRAMES = list(engine.TIMEFRAMES)
FILTERS = ["All 27", "Inside range", "Outside range", "No data"]

# ---------------------------------------------------------------------------
# Styling (same palette / fonts as the original page)
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
:root{
  --ink:#14213d; --paper:#f3f5f8; --card:#fff; --line:#d9dee7; --muted:#5c6679;
  --good:#1c8a5a; --mid:#e0912f; --bad:#c2452f; --none:#c4cad6; --accent:#2b59c3;
  --display:'Bricolage Grotesque',Georgia,sans-serif; --body:'IBM Plex Sans',system-ui,sans-serif;
}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--paper)!important;color:var(--ink);font-family:var(--body)}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
.block-container{max-width:1160px!important;padding:0 22px 40px!important}
[data-testid="stVerticalBlock"]{gap:0}

/* ---------- dark top band ---------- */
.st-key-hero{background:var(--ink);padding:34px 0 38px;box-shadow:0 0 0 100vmax var(--ink);clip-path:inset(0 -100vmax);margin-bottom:6px}
.st-key-hero [data-testid="stVerticalBlock"]{gap:0}
.ss-h1{font-family:var(--display);font-size:clamp(2rem,4.5vw,3.1rem);font-weight:700;color:#fff;margin:0;letter-spacing:-.02em;line-height:1.05}
.ss-sub{margin:10px 0 0;color:#b9c4dc;max-width:620px;font-family:var(--body)}
.st-key-hero [data-testid="stHorizontalBlock"]{margin-top:26px;gap:12px}
.st-key-hero [data-baseweb="input"],.st-key-hero [data-baseweb="base-input"]{background:#fff!important;border:0!important;border-radius:10px!important;min-height:50px}
.st-key-hero input{color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;background:#fff!important;font:500 1.05rem var(--body)!important;padding:0 16px!important;height:50px}
.st-key-hero input::placeholder{color:#8a93a6!important;-webkit-text-fill-color:#8a93a6!important}
.st-key-hero [data-testid="stButtonGroup"]{background:rgba(255,255,255,.12);border-radius:10px;padding:4px;gap:2px;flex-wrap:wrap;width:100%}
.st-key-hero [data-testid="stButtonGroup"] button{background:transparent!important;border:0!important;color:#d3dcf0!important;font:500 .92rem var(--body)!important;min-height:42px;border-radius:7px!important;padding:0 12px!important}
.st-key-hero [data-testid="stButtonGroup"] button[data-testid*="Active"]{background:#fff!important;color:var(--ink)!important;font-weight:600!important}
.st-key-go button{background:#5b8cff!important;color:#fff!important;border:0!important;height:50px;border-radius:10px!important;font:600 1rem var(--body)!important;width:100%}
.st-key-go button:hover{background:#7aa0ff!important}
.st-key-go button p{color:#fff!important}
.st-key-recent [data-testid="stHorizontalBlock"]{margin-top:14px!important;gap:8px!important;flex-wrap:wrap!important;align-items:center}
.st-key-recent [data-testid="stColumn"]{width:auto!important;min-width:0!important;flex:0 0 auto!important}
.ss-recent-label{font-size:.85rem;color:#9fb0d4;font-family:var(--body)}
.st-key-recent button{border:1px solid rgba(255,255,255,.28)!important;background:transparent!important;color:#e7edfb!important;border-radius:999px!important;padding:2px 12px!important;min-height:0!important;font:400 .85rem var(--body)!important}
.st-key-recent button p{color:#e7edfb!important;font-size:.85rem}
.st-key-recent button:hover{background:rgba(255,255,255,.12)!important}

/* ---------- result panels ---------- */
.ss-panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px 28px;margin-top:18px}
.ss-hero{display:grid;grid-template-columns:auto 1fr;gap:34px;align-items:center}
.ss-big{font-family:var(--display);font-size:5.6rem;line-height:.9;font-weight:700;letter-spacing:-.03em}
.ss-big small{font-size:1.3rem;font-weight:500;color:var(--muted);letter-spacing:0}
.ss-rate{font-weight:600;font-size:1.1rem;margin-top:8px}
.ss-name{font-family:var(--display);font-size:1.7rem;font-weight:700;line-height:1.15}
.ss-sym{color:var(--muted);font-weight:500;font-size:1.1rem;margin-left:6px}
.ss-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.ss-tags span{border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:.85rem;background:var(--paper)}
.ss-strip{display:grid;grid-template-columns:repeat(27,1fr);gap:3px;margin-top:24px}
.ss-strip i{height:28px;border-radius:3px}
.ss-legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:.82rem;color:var(--muted)}
.ss-legend b{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.ss-groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-top:24px}
.ss-groups div{border-left:3px solid var(--accent);padding-left:12px}
.ss-groups span{display:block;font-size:.82rem;color:var(--muted)}
.ss-groups strong{font-family:var(--display);font-size:1.6rem}

/* ---------- table panel ---------- */
.st-key-tablepanel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px 28px;margin-top:18px}
.st-key-tablepanel [data-testid="stHorizontalBlock"]{margin-bottom:14px;gap:12px}
.st-key-tablepanel [data-testid="stButtonGroup"]{gap:8px;flex-wrap:wrap}
.st-key-tablepanel [data-testid="stButtonGroup"] button{border:1px solid var(--line)!important;background:#fff!important;border-radius:999px!important;padding:5px 14px!important;font:500 .88rem var(--body)!important;color:var(--ink)!important;min-height:0!important}
.st-key-tablepanel [data-testid="stButtonGroup"] button[data-testid*="Active"]{background:var(--ink)!important;color:#fff!important;border-color:var(--ink)!important}
.st-key-tablepanel [data-testid="stButtonGroup"] button[data-testid*="Active"] p{color:#fff!important}
.st-key-tablepanel [data-testid="stDownloadButton"]{display:flex;justify-content:flex-end}
.st-key-tablepanel [data-testid="stDownloadButton"] button{background:#fff!important;color:var(--accent)!important;border:1px solid var(--line)!important;border-radius:8px!important;font:500 .88rem var(--body)!important;padding:6px 14px!important;min-height:0!important}
.st-key-tablepanel [data-testid="stDownloadButton"] button p{color:var(--accent)!important}
.st-key-tablepanel [data-testid="stDownloadButton"] button:hover{border-color:var(--accent)!important}
.ss-tablewrap{overflow-x:auto}
.ss-tablewrap table{width:100%;border-collapse:collapse;font-size:.93rem;min-width:640px;background:transparent}
.ss-tablewrap th{text-align:left;color:var(--muted);font-weight:500;padding:8px 10px;border:0;border-bottom:2px solid var(--ink);white-space:nowrap;background:transparent}
.ss-tablewrap td{padding:10px;border:0;border-bottom:1px solid var(--line);vertical-align:middle;background:transparent}
.ss-tablewrap tr.ss-grp td{background:var(--paper);font-weight:600;color:var(--accent);padding:7px 10px}
.ss-tablewrap td.ss-ind{cursor:help;text-decoration:underline dotted #b8c0d0;text-underline-offset:3px}
.ss-num{font-variant-numeric:tabular-nums}
.ss-chip{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.78rem;font-weight:600;white-space:nowrap}
.ss-c-Within{background:#d7f0e3;color:#11603f}.ss-c-Below,.ss-c-Above{background:#fbe3c8;color:#8a4d0b}.ss-c-No{background:#e8eaed;color:#4a5262}
.ss-bar{display:inline-block;width:84px;height:6px;border-radius:3px;background:var(--line);margin-right:8px;vertical-align:middle;overflow:hidden}
.ss-bar u{display:block;height:100%;text-decoration:none}
.ss-empty{color:var(--muted);text-align:center;padding:46px 20px}
.ss-empty b{display:block;color:var(--ink);font-family:var(--display);font-size:1.3rem;margin-bottom:4px}
.ss-err{border-left:4px solid var(--bad);background:#fff3f0;color:#7a2616}
.ss-warn{border-left:4px solid var(--mid);background:#fff8ec;color:#6b4208;font-size:.92rem}
.ss-note{color:var(--muted);font-size:.82rem;margin-top:10px}
.ss-foot{color:var(--muted);font-size:.82rem;padding:18px 0 10px}
@media(max-width:820px){.ss-hero{grid-template-columns:1fr;gap:16px}.ss-big{font-size:4rem}.ss-strip i{height:22px}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def esc(s) -> str:
    return html.escape("" if s is None else str(s))


def nn(v):
    """NaN / inf / non-numbers -> None."""
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def col(score) -> str:
    s = nn(score)
    return "var(--none)" if s is None else "var(--good)" if s >= 70 else "var(--mid)" if s >= 40 else "var(--bad)"


@st.cache_data(ttl=600, show_spinner=False)
def run_analysis(ticker: str, timeframe: str):
    # Exceptions are not cached, so a failed Yahoo call is retried on the next click.
    return engine.analyze(ticker, timeframe)


@st.cache_data(ttl=600, show_spinner=False)
def build_excel(ticker: str, timeframe: str) -> bytes:
    meta, df = run_analysis(ticker, timeframe)
    with open(engine.to_excel(meta, df), "rb") as f:
        return f.read()


def summary_html(meta: dict, df: pd.DataFrame) -> str:
    strip = "".join(
        f'<i style="background:{col(r.Score)}" title="{esc(r.Indicator)}: {esc(engine.fmt_val(r.Value, r.Unit))}"></i>'
        for r in df.itertuples()
    )
    groups = "".join(
        f"<div><span>{esc(name)}</span><strong>{'-' if nn(v) is None else round(v)}</strong></div>"
        for name, v in df.groupby("Group", sort=False)["Score"].mean().items()
    )
    price = nn(meta.get("price"))
    price_txt = f"{price:,.2f} {esc(meta.get('currency'))}" if price is not None else "N/A"
    overall = meta["overall"]
    return (
        '<section class="ss-panel"><div class="ss-hero">'
        f'<div><div class="ss-big">{round(overall)}<small>/100</small></div>'
        f'<div class="ss-rate" style="color:{col(overall)}">{esc(meta["rating"])}</div></div>'
        f'<div><div class="ss-name">{esc(meta["name"])}<span class="ss-sym">{esc(meta["symbol"])}</span></div>'
        f'<div class="ss-tags"><span>{esc(meta["sector"])}</span><span>{esc(meta["industry"])}</span>'
        f'<span>{esc(meta["market"])} market</span><span>{esc(meta["timeframe"])}</span>'
        f'<span>{price_txt}</span><span>{esc(meta["coverage"])} indicators scored</span></div></div></div>'
        f'<div class="ss-strip">{strip}</div>'
        '<div class="ss-legend"><span><b style="background:var(--good)"></b>Inside ideal range</span>'
        '<span><b style="background:var(--mid)"></b>Near range</span>'
        '<span><b style="background:var(--bad)"></b>Far from range</span>'
        '<span><b style="background:var(--none)"></b>No data</span></div>'
        f'<div class="ss-groups">{groups}</div></section>'
    )


def table_html(meta: dict, df: pd.DataFrame, view: str) -> str:
    def keep(status):
        return (view == "All 27"
                or (view == "Inside range" and status == "Within")
                or (view == "Outside range" and status in ("Below", "Above"))
                or (view == "No data" and status == "No data"))

    body, last = "", None
    for n, r in enumerate(df.itertuples(), 1):
        if not keep(r.Status):
            continue
        if r.Group != last:
            body += f'<tr class="ss-grp"><td colspan="6">{esc(r.Group)}</td></tr>'
            last = r.Group
        score = nn(r.Score)
        body += (
            f"<tr><td>{n}</td>"
            f'<td class="ss-ind" title="Formula: {esc(r.Formula)}">{esc(r.Indicator)}</td>'
            f'<td class="ss-num">{esc(engine.fmt_val(r.Value, r.Unit))}</td>'
            f"<td>{esc(engine.fmt_range(r.Low, r.High, r.Unit))}</td>"
            f'<td><span class="ss-chip ss-c-{esc(r.Status.split()[0])}">{esc(r.Status)}</span></td>'
            f'<td class="ss-num"><span class="ss-bar"><u style="width:{0 if score is None else score:.0f}%;'
            f'background:{col(score)}"></u></span>{"-" if score is None else round(score)}</td></tr>'
        )
    if not body:
        body = '<tr><td colspan="6" class="ss-empty">No indicators match this filter.</td></tr>'
    return (
        '<div class="ss-tablewrap"><table><thead><tr><th>#</th><th>Indicator</th><th>Value</th>'
        f'<th>Ideal range ({esc(meta["sector"])}, {esc(meta["market"])})</th><th>Status</th><th>Score</th></tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
        '<div class="ss-note">Hover over an indicator name to see its formula.</div>'
    )


# ---------------------------------------------------------------------------
# Header band: title, search box, timeframe, Analyze button, recent searches
# ---------------------------------------------------------------------------
st.session_state.setdefault("q", "")
st.session_state.setdefault("recent", [])


def pick(sym: str):
    st.session_state["q"] = sym


with st.container(key="hero"):
    st.markdown(
        '<div class="ss-h1">Stock Score Analyzer</div>'
        '<p class="ss-sub">Search a company. We find its sector and market, calculate 27 indicators, '
        "and score each one against the ideal range for that sector.</p>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([5, 5.6, 1.5], vertical_alignment="center")
    c1.text_input("Ticker or company name", key="q", label_visibility="collapsed",
                  placeholder="Nvidia, AAPL, RELIANCE.NS, TCS.NS")
    tf = c2.segmented_control("Timeframe", TIMEFRAMES, default="1 Year", key="tf",
                              label_visibility="collapsed") or "1 Year"
    c3.button("Analyze", key="go")
    recent_slot = st.container(key="recent")

query = st.session_state["q"].strip()
if not query:
    st.markdown(
        '<div class="ss-panel ss-empty"><b>Search a ticker to begin</b>'
        "Indian stocks use .NS (NSE) or .BO (BSE), for example INFY.NS.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
try:
    with st.spinner(f"Fetching data for {query} and scoring 27 indicators..."):
        meta, df = run_analysis(query, tf)
except Exception as e:  # ValueError (not found), network errors, Yahoo rate limits
    if engine.is_rate_limit(e):
        msg = ("Yahoo Finance is limiting requests right now. Wait about a minute and try again. "
               "Stocks you searched recently load instantly from cache.")
    else:
        msg = str(e)
    st.markdown(
        f'<div class="ss-panel ss-err"><b>Could not run the analysis.</b><br>{esc(msg)}</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# remember recent searches (shown as chips in the header band)
sym = meta["symbol"]
st.session_state["recent"] = [sym] + [s for s in st.session_state["recent"] if s != sym][:5]
with recent_slot:
    cols = st.columns(len(st.session_state["recent"]) + 1)
    cols[0].markdown('<span class="ss-recent-label">Recent:</span>', unsafe_allow_html=True)
    for i, (c, s) in enumerate(zip(cols[1:], st.session_state["recent"])):
        c.button(s, key=f"rc{i}", on_click=pick, args=(s,))

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if meta.get("note"):
    st.markdown(f'<div class="ss-panel ss-warn">{esc(meta["note"])}</div>', unsafe_allow_html=True)
st.markdown(summary_html(meta, df), unsafe_allow_html=True)

with st.container(key="tablepanel"):
    f1, f2 = st.columns([4, 1.3], vertical_alignment="center")
    view = f1.segmented_control("Filter", FILTERS, default="All 27", key="view",
                                label_visibility="collapsed") or "All 27"
    f2.download_button(
        "Download Excel",
        data=build_excel(query, tf),
        file_name=f"{meta['symbol']}_{meta['timeframe'].replace(' ', '')}_score.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.markdown(table_html(meta, df, view), unsafe_allow_html=True)

st.markdown(
    '<div class="ss-foot">Data from Yahoo Finance and may be delayed or incomplete. '
    "Scores are a screening aid, not investment advice.</div>",
    unsafe_allow_html=True,
)
