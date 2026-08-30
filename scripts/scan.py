#!/usr/bin/env python3
"""
ST Weekly Screener — saves data/screener_results.json
SuperTrend(10,2) trigger + SuperTrend(10,2.5) trend judge on weekly chart
3 quality filters: Monthly ST, RSI>50, within 30% of 52W high
Covers: Nifty 100 stocks + indices + USD/INR + commodities
"""
import yfinance as yf, pandas as pd, numpy as np
import json, math, concurrent.futures, warnings
from datetime import datetime, timezone, timedelta
warnings.filterwarnings("ignore")
IST = timezone(timedelta(hours=5, minutes=30))

def sanitize_nan(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_nan(v) for v in obj]
    return obj

# ── Nifty 100 stocks ─────────────────────────────────────────────────────────
NIFTY100 = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "HINDUNILVR.NS","ITC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS",
    "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
    "TITAN.NS","NESTLEIND.NS","WIPRO.NS","ULTRACEMCO.NS","BAJFINANCE.NS",
    "HCLTECH.NS","TECHM.NS","ONGC.NS","NTPC.NS","POWERGRID.NS",
    "BAJAJFINSV.NS","INDUSINDBK.NS","TATAMOTORS.NS","TATASTEEL.NS",
    "ADANIENT.NS","ADANIPORTS.NS","COALINDIA.NS","JSWSTEEL.NS",
    "HINDALCO.NS","CIPLA.NS","DRREDDY.NS","EICHERMOT.NS","GRASIM.NS",
    "HEROMOTOCO.NS","BRITANNIA.NS","APOLLOHOSP.NS","BPCL.NS",
    "TATACONSUM.NS","DIVISLAB.NS","BAJAJ-AUTO.NS","SBILIFE.NS",
    "HDFCLIFE.NS","SHRIRAMFIN.NS","LTIM.NS","M&M.NS",
    "ADANIGREEN.NS","AMBUJACEM.NS","AUROPHARMA.NS","BANKBARODA.NS",
    "BERGEPAINT.NS","BOSCHLTD.NS","CANBK.NS","CHOLAFIN.NS",
    "COLPAL.NS","DABUR.NS","DLF.NS","DMART.NS","GODREJCP.NS",
    "HAVELLS.NS","ICICIPRULI.NS","INDUSTOWER.NS","IRCTC.NS",
    "JINDALSTEL.NS","LUPIN.NS","MARICO.NS","NMDC.NS","NAUKRI.NS",
    "OFSS.NS","PAGEIND.NS","PIDILITIND.NS","PNB.NS","RECLTD.NS",
    "SAIL.NS","SIEMENS.NS","SRF.NS","TORNTPHARM.NS","TRENT.NS",
    "TVSMOTOR.NS","VEDL.NS","VOLTAS.NS","ZOMATO.NS","MOTHERSON.NS",
    "MUTHOOTFIN.NS","LICI.NS","GAIL.NS","IOC.NS","HPCL.NS",
    "CONCOR.NS","CAMS.NS","TATAPOWER.NS","MPHASIS.NS","PERSISTENT.NS",
    "HDFCAMC.NS","PIIND.NS","BALKRISIND.NS","PHOENIXLTD.NS","BAJAJHLDNG.NS",
]

# ── Nifty F&O extra (F&O eligible, not in Nifty 100) ─────────────────────────
# Verified against NSE official F&O eligible stock list (208 underlyings); audited Aug 2026
NIFTY_FO_EXTRA = [
    # ── Banks & Finance ──────────────────────────────────────────────────────
    "AUBANK.NS","BANDHANBNK.NS","BANKINDIA.NS","CANFINHOME.NS","CUB.NS",
    "FEDERALBNK.NS","IDFCFIRSTB.NS","IDFC.NS","LICHSGFIN.NS","MAHABANK.NS",
    "MANAPPURAM.NS","MCX.NS","MOTILALOFS.NS","RBLBANK.NS","YESBANK.NS",
    "ANGELONE.NS","ABCAPITAL.NS","ICICIGI.NS","IREDA.NS","IRFC.NS",
    "JIOFIN.NS","KFINTECH.NS","LTFH.NS","M&MFIN.NS","MFSL.NS",
    "NAM-INDIA.NS","NUVAMA.NS","PEL.NS","PFC.NS","SBICARD.NS","TATAINVEST.NS",
    # ── IT & Technology ──────────────────────────────────────────────────────
    "BSOFT.NS","COFORGE.NS","CYIENT.NS","HFCL.NS","IDEA.NS",
    "INDIAMART.NS","KPITTECH.NS","LTTS.NS","NAZARA.NS","TATACOMM.NS","TATAELXSI.NS",
    # ── Pharma & Healthcare ──────────────────────────────────────────────────
    "ABBOTINDIA.NS","ALKEM.NS","APLLTD.NS","BIOCON.NS","FORTIS.NS",
    "GLENMARK.NS","GRANULES.NS","IPCALAB.NS","LALPATHLAB.NS","METROPOLIS.NS",
    "NATCOPHARM.NS","NAVINFLUOR.NS","SANOFI.NS","SUVENPHAR.NS","SYNGENE.NS",
    # ── Auto & Auto Ancillary ────────────────────────────────────────────────
    "APOLLOTYRE.NS","ASHOKLEY.NS","BHARATFORG.NS","ESCORTS.NS","EXIDEIND.NS",
    "HYUNDAI.NS","MRF.NS","SONACOMS.NS",
    # ── Energy, Power & Gas ──────────────────────────────────────────────────
    "ADANIPOWER.NS","CGPOWER.NS","CESC.NS","IEX.NS","GUJGASLTD.NS",
    "IGL.NS","MGL.NS","NLCINDIA.NS","PETRONET.NS","PREMIERENE.NS",
    "SJVN.NS","TORNTPOWER.NS","WAAREE.NS",
    # ── Oil & Gas ────────────────────────────────────────────────────────────
    "OIL.NS",
    # ── Metals ───────────────────────────────────────────────────────────────
    "HINDCOPPER.NS","JINDALSAW.NS","JSL.NS","NATIONALUM.NS",
    # ── Cement & Commodity ───────────────────────────────────────────────────
    "ACC.NS","BALRAMCHIN.NS","DALBHARAT.NS","EPL.NS","INDIACEM.NS",
    "JKCEMENT.NS","RAMCOCEM.NS","SHREECEM.NS",
    # ── Chemicals ────────────────────────────────────────────────────────────
    "AARTIIND.NS","ATUL.NS","COROMANDEL.NS","DEEPAKNTR.NS","GNFC.NS","UPL.NS",
    # ── Consumer, Retail & Media ─────────────────────────────────────────────
    "ABFRL.NS","BATAINDIA.NS","BLUESTARCO.NS","CROMPTON.NS","DELHIVERY.NS",
    "DIXON.NS","DOMS.NS","GOCOLOR.NS","INDHOTEL.NS","JUBLFOOD.NS",
    "KALYANKJIL.NS","MCDOWELL-N.NS","PVRINOX.NS","SUNTV.NS","SWIGGY.NS",
    "UBL.NS","VBL.NS","VGUARD.NS","WHIRLPOOL.NS","ZEEL.NS",
    # ── Capital Goods & Defence ──────────────────────────────────────────────
    "ABB.NS","BDL.NS","BEL.NS","BHEL.NS","CHAMBLFERT.NS","COCHINSHIP.NS",
    "CUMMINSIND.NS","HAL.NS","HONAUT.NS","KAYNES.NS","KEI.NS",
    "POLYCAB.NS","SUPREMEIND.NS","TIINDIA.NS","TITAGARH.NS",
    # ── Real Estate ──────────────────────────────────────────────────────────
    "GODREJPROP.NS","MAHLIFE.NS","OBEROIRLTY.NS",
    # ── Infrastructure ───────────────────────────────────────────────────────
    "GMRINFRA.NS","INDIGO.NS","NBCC.NS","RVNL.NS",
    # ── Others ───────────────────────────────────────────────────────────────
    "ASTRAL.NS","HUDCO.NS","VIJAYA.NS",
]

# ── Nifty 500 extra (midcaps NOT in F&O — tracked for trend only) ─────────────
NIFTY500_EXTRA = [
    # ── Banks & Finance ──────────────────────────────────────────────────────
    "EQUITASBNK.NS","NIACL.NS",
    "SUNDARMFIN.NS","UJJIVAN.NS","CDSL.NS","IIFL.NS","PNBHOUSING.NS","UTIAMC.NS",
    # ── IT & Technology ──────────────────────────────────────────────────────
    "TATATECH.NS","HAPPSTMNDS.NS","TANLA.NS","AFFLE.NS",
    # ── Pharma & Healthcare ──────────────────────────────────────────────────
    "JBCHEPHARM.NS","SPARC.NS","LAURUSLABS.NS","ZYDUSLIFE.NS",
    # ── Auto & Auto Ancillary ────────────────────────────────────────────────
    "CEATLTD.NS","SUNDRMFAST.NS",
    # ── Energy & Power ───────────────────────────────────────────────────────
    "ATGL.NS","SOLARINDS.NS","NHPC.NS","SUZLON.NS","INOXWIND.NS",
    # ── Metals & Chemicals ───────────────────────────────────────────────────
    "HINDZINC.NS","TATACHEM.NS","DEEPAKFERT.NS",
    # ── Industrials & Capital Goods ──────────────────────────────────────────
    "CARBORUNIV.NS","ELGIEQUIP.NS","GRINDWELL.NS","TRITURBINE.NS",
    "AIAENG.NS","APLAPOLLO.NS","BEML.NS","MAZDOCK.NS","THERMAXLTD.NS",
    # ── Real Estate & Infrastructure ─────────────────────────────────────────
    "BRIGADE.NS","PRESTIGE.NS","SOBHA.NS","ANANTRAJ.NS","KPIL.NS",
    # ── Consumer, Retail & Media ─────────────────────────────────────────────
    "EIHOTEL.NS","KANSAINER.NS","LUXIND.NS","REDINGTON.NS",
    "EMAMI.NS","NYKAA.NS","POLICYBZR.NS",
    # ── Chemicals ────────────────────────────────────────────────────────────
    "FINEORG.NS","NOCIL.NS","SUDARSCHEM.NS","SUMICHEM.NS","VINATIORGA.NS",
    # ── Others ───────────────────────────────────────────────────────────────
    "KRBL.NS","TRIDENT.NS",
]

# ── Non-stock instruments ─────────────────────────────────────────────────────
INSTRUMENTS = [
    # ── NSE Broad Indices (direct tickers — reliable on Yahoo Finance) ────────
    {"symbol": "^NSEI",         "name": "Nifty 50",        "type": "index", "currency": "₹"},
    {"symbol": "^NSEBANK",      "name": "Bank Nifty",      "type": "index", "currency": "₹"},
    {"symbol": "^CNXIT",        "name": "Nifty IT",        "type": "index", "currency": "₹"},
    {"symbol": "^CNXPHARMA",    "name": "Nifty Pharma",    "type": "index", "currency": "₹"},
    {"symbol": "^NSMIDCP",      "name": "Nifty Midcap",    "type": "index", "currency": "₹"},
    {"symbol": "^CNX100",       "name": "Nifty 100",       "type": "index", "currency": "₹"},
    {"symbol": "^CNX200",       "name": "Nifty 200",       "type": "index", "currency": "₹"},
    {"symbol": "^INDIAVIX",     "name": "India VIX",       "type": "index", "currency": "₹"},
    # ── NSE Sector ETFs (Nippon India BeES/IETF — reliable .NS tickers) ───────
    # ETF NAV tracks the sector index; signal accuracy same as direct index.
    {"symbol": "AUTOIETF.NS",   "name": "Nifty Auto",      "type": "index", "currency": "₹"},
    {"symbol": "FMCGIETF.NS",   "name": "Nifty FMCG",     "type": "index", "currency": "₹"},
    {"symbol": "METALIETF.NS",  "name": "Nifty Metal",     "type": "index", "currency": "₹"},
    {"symbol": "REALTYBEES.NS", "name": "Nifty Realty",    "type": "index", "currency": "₹"},
    {"symbol": "ENERGYBEES.NS", "name": "Nifty Energy",    "type": "index", "currency": "₹"},
    {"symbol": "INFRABEES.NS",  "name": "Nifty Infra",     "type": "index", "currency": "₹"},
    {"symbol": "PSUBNKBEES.NS", "name": "Nifty PSU Bank",  "type": "index", "currency": "₹"},
    {"symbol": "FINIETF.NS",    "name": "Nifty Finance",   "type": "index", "currency": "₹"},
    {"symbol": "HEALTHIETF.NS", "name": "Nifty Healthcare","type": "index", "currency": "₹"},
    {"symbol": "OILIETF.NS",    "name": "Nifty Oil & Gas", "type": "index", "currency": "₹"},
    {"symbol": "JUNIORBEES.NS", "name": "Nifty Next 50",   "type": "index", "currency": "₹"},
    {"symbol": "CPSEETF.NS",    "name": "Nifty CPSE",      "type": "index", "currency": "₹"},
    # ── US Indices ───────────────────────────────────────────────────────────
    {"symbol": "^GSPC",       "name": "S&P 500",        "type": "us-index", "currency": "$"},
    {"symbol": "^NDX",        "name": "NASDAQ 100",     "type": "us-index", "currency": "$"},
    {"symbol": "^DJI",        "name": "Dow Jones",      "type": "us-index", "currency": "$"},
    {"symbol": "^RUT",        "name": "Russell 2000",   "type": "us-index", "currency": "$"},
    {"symbol": "^SOX",        "name": "Philadelphia SE","type": "us-index", "currency": "$"},
    {"symbol": "^VIX",        "name": "CBOE VIX",       "type": "us-index", "currency": "$"},
    # ── Currency ─────────────────────────────────────────────────────────────
    {"symbol": "USDINR=X",    "name": "USD/INR",        "type": "currency", "currency": "₹"},
    {"symbol": "EURINR=X",    "name": "EUR/INR",        "type": "currency", "currency": "₹"},
    # ── Commodities (COMEX/NYMEX — price in USD) ─────────────────────────────
    {"symbol": "GC=F",        "name": "Gold",           "type": "commodity", "currency": "$"},
    {"symbol": "SI=F",        "name": "Silver",         "type": "commodity", "currency": "$"},
    {"symbol": "CL=F",        "name": "Crude Oil",      "type": "commodity", "currency": "$"},
    {"symbol": "NG=F",        "name": "Nat Gas",        "type": "commodity", "currency": "$"},
    {"symbol": "HG=F",        "name": "Copper",         "type": "commodity", "currency": "$"},
]
