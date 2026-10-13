"""
app.py  -  web server.   Run locally:  python app.py   ->  open http://localhost:5000
Production (Render / Railway / any server):  gunicorn app:app
"""
import io, os, time, math
from flask import Flask, jsonify, request, send_file, send_from_directory

import engine

app = Flask(__name__, static_folder="static", static_url_path="/static")

_CACHE, TTL = {}, 600          # keep results 10 minutes so repeat clicks and Excel export don't re-fetch


def clean(v):
    """NaN / numpy values -> plain JSON-safe values."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return v


def run_analysis(ticker: str, timeframe: str):
    key = (ticker.strip().upper(), timeframe)
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < TTL:
        return hit[1], hit[2]
    meta, df = engine.analyze(ticker, timeframe)
    _CACHE[key] = (time.time(), meta, df)
    return meta, df


def to_payload(meta, df):
    rows = []
    for i, r in enumerate(df.itertuples(), 1):
        rows.append(dict(
            n=i, group=r.Group, name=r.Indicator, value=clean(r.Value), unit=r.Unit,
            valueText=engine.fmt_val(clean(r.Value), r.Unit),
            low=clean(r.Low), high=clean(r.High), rangeText=engine.fmt_range(clean(r.Low), clean(r.High), r.Unit),
            status=r.Status, score=clean(r.Score), formula=r.Formula))
    groups = [dict(name=n, score=clean(v)) for n, v in df.groupby("Group", sort=False)["Score"].mean().items()]
    return dict(meta={k: clean(v) for k, v in meta.items()}, indicators=rows, groups=groups)


@app.after_request
def allow_other_origins(resp):          # lets index.html opened from anywhere call this server
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.get("/")
def home():
    if os.path.exists(os.path.join(app.static_folder, "index.html")):
        return send_from_directory("static", "index.html")
    return "Stock Score API is running. Open your frontend page and paste this address into its Server box."


@app.get("/api/analyze")
def api_analyze():
    ticker = request.args.get("ticker", "")
    tf = request.args.get("timeframe", "1 Year")
    if tf not in engine.TIMEFRAMES:
        return jsonify(error=f"Unknown timeframe '{tf}'."), 400
    try:
        meta, df = run_analysis(ticker, tf)
        return jsonify(to_payload(meta, df))
    except ValueError as e:
        return jsonify(error=str(e)), 404
    except Exception as e:                       # network problems, Yahoo rate limits, etc.
        if engine.is_rate_limit(e):
            return jsonify(error="Yahoo Finance is limiting requests right now. Wait about a minute and try again. "
                                 "Stocks you searched recently load instantly from cache."), 429
        return jsonify(error=f"Data provider problem: {e}. Please try again in a moment."), 502


@app.get("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    try:
        import yfinance as yf
        out = []
        for h in yf.Search(q, max_results=7).quotes:
            if h.get("quoteType") in ("EQUITY", "ETF") and h.get("symbol"):
                out.append(dict(symbol=h["symbol"], name=h.get("longname") or h.get("shortname") or "",
                                exchange=h.get("exchDisp") or h.get("exchange") or ""))
        return jsonify(out)
    except Exception:
        return jsonify([])


@app.get("/api/export")
def api_export():
    ticker = request.args.get("ticker", "")
    tf = request.args.get("timeframe", "1 Year")
    try:
        meta, df = run_analysis(ticker, tf)
        path = engine.to_excel(meta, df)
        return send_file(path, as_attachment=True, download_name=os.path.basename(path))
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.get("/api/meta")
def api_meta():
    return jsonify(timeframes=list(engine.TIMEFRAMES), indicators=len(engine.INDICATORS))


if __name__ == "__main__":
    engine.load_ranges()                                    # creates ideal_ranges.csv on first run
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
