#!/usr/bin/env python3
"""
NSE Risk Monitor - Slow factor computation
Runs via GitHub Actions Mon-Fri 3x daily.
Outputs: data/risk_factors.json
"""
import json, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

PERIOD_RSI     = "2y"
PERIOD_CORE    = "1y"
PERIOD_BREADTH = "3mo"
DELAY = 0.5

BREADTH_TICKERS = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","HINDUNILVR.NS",
    "ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS","ITC.NS",
    "LT.NS","AXISBANK.NS","ASIANPAINT.NS","BAJFINANCE.NS","MARUTI.NS",
    "WIPRO.NS","TITAN.NS","NESTLEIND.NS","ULTRACEMCO.NS","HCLTECH.NS",
    "SUNPHARMA.NS","ONGC.NS","POWERGRID.NS","NTPC.NS","M&M.NS",
    "TATAMOTORS.NS","TECHM.NS","BAJAJFINSV.NS","DIVISLAB.NS","CIPLA.NS",
    "ADANIENT.NS","JSWSTEEL.NS","TATASTEEL.NS","GRASIM.NS","INDUSINDBK.NS",
    "BPCL.NS","EICHERMOT.NS","HEROMOTOCO.NS","BRITANNIA.NS","APOLLOHOSP.NS",
    "DRREDDY.NS","COALINDIA.NS","HINDALCO.NS","ADANIPORTS.NS","SBILIFE.NS",
    "HDFCLIFE.NS","BAJAJ-AUTO.NS","SHREECEM.NS","UPL.NS","PIDILITIND.NS",
]

SECTOR_TICKERS = {
    "Nifty 50":   "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "IT":         "^CNXIT",
    "Pharma":     "^CNXPHARMA",
    "Auto":       "^CNXAUTO",
    "FMCG":       "^CNXFMCG",
    "Metal":      "^CNXMETAL",
    "Realty":     "^CNXREALTY",
    "Energy":     "^CNXENERGY",
    "Infra":      "^CNXINFRA",
}

def wilder_rsi(series, n=14):
    series = series.dropna()
    if len(series) < n + 1: return 50.0
    delta = series.diff().dropna()
    gains = delta.clip(lower=0); losses = -delta.clip(upper=0)
    avg_gain = float(gains.iloc[:n].mean())
    avg_loss = float(losses.iloc[:n].mean())
    for i in range(n, len(gains)):
        avg_gain = (avg_gain*(n-1)+float(gains.iloc[i]))/n
        avg_loss = (avg_loss*(n-1)+float(losses.iloc[i]))/n
    if avg_loss == 0: return 100.0
    return round(100.0 - 100.0/(1.0+avg_gain/avg_loss), 2)

def sma(series, n):
    tail = series.tail(n)
    return float(tail.mean()) if len(tail) >= n else float(series.mean())

def ema_last(series, n):
    series = series.dropna()
    if not len(series): return 0.0
    k = 2.0/(n+1); v = float(series.iloc[0])
    for x in series.iloc[1:]: v = float(x)*k + v*(1-k)
    return v

def pct_chg(series, n):
    if len(series) < n+1: return 0.0
    return float((series.iloc[-1]/series.iloc[-(n+1)]-1)*100)

def clamp(v, lo=0, hi=100): return max(lo, min(hi, int(round(float(v)))))

def dl(ticker, period):
    try:
        raw = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if raw is None or raw.empty: return pd.Series(dtype=float)
        col = raw["Close"]
        if isinstance(col, pd.DataFrame): col = col.iloc[:, 0]
        s = col.dropna()
        print(f"  dl {ticker}: {len(s)} bars")
        return s
    except Exception as e:
        print(f"  WARNING dl({ticker}): {e}")
        return pd.Series(dtype=float)

def dl_batch(tickers, period):
    try:
        raw = yf.download(tickers, period=period, progress=False, auto_adjust=True)
        if raw is None or raw.empty: return pd.DataFrame()
        close = raw["Close"]
        if isinstance(close, pd.Series): close = close.to_frame(name=tickers[0])
        return close.dropna(how="all")
    except Exception as e:
        print(f"  WARNING dl_batch: {e}")
        return pd.DataFrame()

def compute_breadth():
    print("Computing breadth...")
    above20, above50 = [], []
    for i in range(0, len(BREADTH_TICKERS), 10):
        batch = BREADTH_TICKERS[i:i+10]
        frame = dl_batch(batch, PERIOD_BREADTH)
        for ticker in batch:
            if ticker not in frame.columns: continue
            s = frame[ticker].dropna()
            if len(s) >= 50:
                above20.append(1 if s.iloc[-1] > sma(s,20) else 0)
                above50.append(1 if s.iloc[-1] > sma(s,50) else 0)
        time.sleep(DELAY)
    pct20 = float(np.mean(above20)*100) if above20 else 50.0
    pct50 = float(np.mean(above50)*100) if above50 else 50.0
    score = clamp(pct20*0.6+pct50*0.4)
    print(f"  Breadth: {pct20:.1f}% above 20-MA -> score {score}")
    return {"score":score,"raw":{"pct_above_20ma":round(pct20,1),"pct_above_50ma":round(pct50,1),"stocks_sampled":len(above20)}}

def compute_fii_proxy(inr, nifty, midcap):
    inr_chg20 = pct_chg(inr,20) if len(inr)>=21 else 0.0
    inr_score = clamp(50-inr_chg20*5)
    ratio_chg, risk_on_score = 0.0, 50
    if len(nifty)>=21 and len(midcap)>=21:
        ratio_now = float(midcap.iloc[-1])/float(nifty.iloc[-1])
        ratio_20d = float(midcap.iloc[-20])/float(nifty.iloc[-20])
        ratio_chg = (ratio_now/ratio_20d-1)*100
        risk_on_score = clamp(50+ratio_chg*10)
    score = clamp(inr_score*0.5+risk_on_score*0.5)
    print(f"  FII proxy: score {score}")
    return {"score":score,"raw":{"inr_20d_chg_pct":round(inr_chg20,2),"midcap_vs_largecap_20d_chg":round(ratio_chg,2),"inr_component":inr_score,"risk_on_component":risk_on_score}}

def compute_macro(inr, vix):
    tail252 = inr.tail(252) if len(inr)>=252 else inr
    mn,mx = float(tail252.min()), float(tail252.max())
    inr_pct = float((inr.iloc[-1]-mn)/(mx-mn)*100) if mx>mn else 50.0
    inr_score = clamp(100-inr_pct)
    vix_avg = float(vix.tail(20).mean()) if len(vix)>=20 else 16.0
    vix_score = (90 if vix_avg<12 else 75 if vix_avg<15 else 55 if vix_avg<20 else 35 if vix_avg<25 else 15)
    score = clamp(inr_score*0.4+vix_score*0.6)
    print(f"  Macro: VIX_avg={vix_avg:.2f} -> score {score}")
    return {"score":score,"raw":{"inr_vs_1y_range_pct":round(inr_pct,1),"vix_20d_avg":round(vix_avg,2),"inr_component":inr_score,"vix_component":vix_score}}

def compute_sectors():
    print("Computing sectors (2y)...")
    sectors = {}
    for name, ticker in SECTOR_TICKERS.items():
        s = dl(ticker, PERIOD_RSI)
        if len(s)<50: continue
        price,ma20,ma50 = float(s.iloc[-1]),sma(s,20),sma(s,50)
        above20,above50 = price>ma20, price>ma50
        rsi14 = wilder_rsi(s,14)
        trend_pts = (40 if above20 else 0)+(30 if above50 else 0)
        rsi_pts   = max(0.0, min(30.0, (rsi14-30.0)*30.0/40.0))
        score     = clamp(trend_pts+rsi_pts)
        sectors[name] = {"score":score,"change_1d":round(pct_chg(s,1),2),"change_5d":round(pct_chg(s,5),2),
                         "change_20d":round(pct_chg(s,20),2),"rsi":round(rsi14,1),
                         "above_20ma":bool(above20),"above_50ma":bool(above50),
                         "price":round(price,2),"ma20":round(ma20,2),"ma50":round(ma50,2)}
        print(f"  {name}: RSI={rsi14:.1f} score={score}")
        time.sleep(DELAY)
    return sectors

def main():
    print("="*60+f"\nfetch_risk_data.py  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"+"="*60)
    frame = dl_batch(["^NSEI","^NSMIDCP","USDINR=X","^INDIAVIX"], PERIOD_CORE)
    time.sleep(DELAY)
    def gc(sym):
        if sym in frame.columns: return frame[sym].dropna()
        return pd.Series(dtype=float)
    nifty,midcap,inr,vix = gc("^NSEI"),gc("^NSMIDCP"),gc("USDINR=X"),gc("^INDIAVIX")
    breadth = compute_breadth()
    fii     = compute_fii_proxy(inr,nifty,midcap)
    macro   = compute_macro(inr,vix)
    sectors = compute_sectors()
    ctx = {}
    if len(nifty)>=20:
        ctx = {"nifty_ema20":round(ema_last(nifty,20),2),"nifty_ema50":round(ema_last(nifty,min(50,len(nifty))),2),
               "nifty_ema200":round(ema_last(nifty,min(200,len(nifty))),2),"nifty_bars":len(nifty)}
    if len(vix)>=20:  ctx["vix_20d_avg"] = round(float(vix.tail(20).mean()),2)
    if len(inr)>0:    ctx["inr_current"] = round(float(inr.iloc[-1]),4)
    now = datetime.now(timezone.utc)
    output = {"generated_at":now.strftime("%Y-%m-%dT%H:%M:%SZ"),
              "next_update":(now+timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "factors":{"breadth":breadth,"fii_proxy":fii,"macro":macro},
              "sectors":sectors,"market_context":ctx}
    Path("data").mkdir(exist_ok=True)
    with open("data/risk_factors.json","w") as f: json.dump(output,f,indent=2)
    print(f"\nWrote data/risk_factors.json  breadth={breadth['score']} fii={fii['score']} macro={macro['score']}")

if __name__=="__main__":
    main()
