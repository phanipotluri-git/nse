#!/usr/bin/env python3
"""
ST Weekly Screener — saves data/screener_results.json
SuperTrend(10,2) trigger + SuperTrend(10,2.5) trend judge on weekly chart
3 quality filters: Monthly ST, RSI>50, within 30% of 52W high
Covers: Nifty 100 stocks + indices + USD/INR + commodities
"""
import yfinance as yf, pandas as pd, numpy as np
import json, concurrent.futures, warnings
from datetime import datetime, timezone, timedelta
warnings.filterwarnings("ignore")
IST = timezone(timedelta(hours=5, minutes=30))

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
NIFTY_FO_EXTRA = [
    # ── Banks & Finance ──────────────────────────────────────────────────────
    "AUBANK.NS","BANDHANBNK.NS","CANFINHOME.NS","FEDERALBNK.NS","IDFCFIRSTB.NS",
    "LICHSGFIN.NS","MANAPPURAM.NS","MCX.NS","MOTILALOFS.NS","RBLBANK.NS",
    "SUNDARMFIN.NS","UJJIVAN.NS","ANGELONE.NS","NUVAMA.NS","PFC.NS",
    "CDSL.NS","ICICIGI.NS","IIFL.NS","PNBHOUSING.NS","UTIAMC.NS",
    "M&MFIN.NS","LTFH.NS","IREDA.NS","HUDCO.NS",
    # ── IT & Technology ──────────────────────────────────────────────────────
    "BSOFT.NS","COFORGE.NS","HAPPSTMNDS.NS","KPITTECH.NS","LTTS.NS",
    "CYIENT.NS","TANLA.NS","AFFLE.NS",
    # ── Pharma & Healthcare ──────────────────────────────────────────────────
    "BIOCON.NS","GLENMARK.NS","GRANULES.NS","LAURUSLABS.NS","METROPOLIS.NS","NAVINFLUOR.NS",
    "ALKEM.NS","IPCALAB.NS",
    # ── Auto & Auto Ancillary ────────────────────────────────────────────────
    "APOLLOTYRE.NS","ASHOKLEY.NS","ESCORTS.NS","EXIDEIND.NS","SONACOMS.NS",
    "BHARATFORG.NS","CEATLTD.NS","SUNDRMFAST.NS",
    # ── Energy, Power & Gas ──────────────────────────────────────────────────
    "ATGL.NS","CESC.NS","CGPOWER.NS","GUJGASLTD.NS","IEX.NS","MGL.NS",
    "SOLARINDS.NS","TORNTPOWER.NS",
    "ADANIPOWER.NS","NHPC.NS","SUZLON.NS",
    # ── Metals, Cement & Chemicals ───────────────────────────────────────────
    "ACC.NS","DALBHARAT.NS","DEEPAKNTR.NS","GNFC.NS","INDIACEM.NS",
    "JKCEMENT.NS","JSL.NS","TATACHEM.NS",
    "HINDZINC.NS","NATIONALUM.NS","DEEPAKFERT.NS",
    # ── Consumer, Retail & Media ─────────────────────────────────────────────
    "ABFRL.NS","CROMPTON.NS","DELHIVERY.NS","DIXON.NS","JUBLFOOD.NS",
    "KALYANKJIL.NS","NYKAA.NS","SUNTV.NS","UBL.NS","ZEEL.NS",
    "BATAINDIA.NS","PVRINOX.NS",
    # ── Capital Goods & Defence ──────────────────────────────────────────────
    "AIAENG.NS","APLAPOLLO.NS","BHEL.NS","CHAMBLFERT.NS","CUMMINSIND.NS",
    "HAL.NS","KAYNES.NS","SUPREMEIND.NS","TATACOMM.NS","TATATECH.NS",
    "BEL.NS","POLYCAB.NS","BEML.NS","TITAGARH.NS",
    # ── Real Estate ──────────────────────────────────────────────────────────
    "GMRAIRPORT.NS","GODREJPROP.NS","OBEROIRLTY.NS",
    "BRIGADE.NS","PRESTIGE.NS","SOBHA.NS","ANANTRAJ.NS",
    # ── Infrastructure ───────────────────────────────────────────────────────
    "NBCC.NS","RVNL.NS","KPIL.NS",
    # ── Others ───────────────────────────────────────────────────────────────
    "ABCAPITAL.NS","ASTRAL.NS","EMAMI.NS","INOXWIND.NS","MFSL.NS",
    "PEL.NS","POLICYBZR.NS","ZYDUSLIFE.NS",
    "THERMAXLTD.NS","TIINDIA.NS","OIL.NS",
]

# ── Nifty 500 extra (key midcaps not in Nifty 100 or F&O list above) ─────────
NIFTY500_EXTRA = [
    # ── Banks & Finance ──────────────────────────────────────────────────────
    "EQUITASBNK.NS","KFINTECH.NS","NIACL.NS",
    # ── Pharma & Healthcare ──────────────────────────────────────────────────
    "JBCHEPHARM.NS","NATCOPHARM.NS","SPARC.NS",
    # ── Industrials & Capital Goods ──────────────────────────────────────────
    "CARBORUNIV.NS","ELGIEQUIP.NS","GRINDWELL.NS","TRITURBINE.NS",
    # ── Consumer & Retail ────────────────────────────────────────────────────
    "EIHOTEL.NS","KANSAINER.NS","LUXIND.NS","REDINGTON.NS","VGUARD.NS",
    # ── Chemicals ────────────────────────────────────────────────────────────
    "FINEORG.NS","NOCIL.NS","SUDARSCHEM.NS","SUMICHEM.NS","VINATIORGA.NS",
    # ── Others ───────────────────────────────────────────────────────────────
    "KRBL.NS","TRIDENT.NS",
]

# ── Non-stock instruments ─────────────────────────────────────────────────────
INSTRUMENTS = [
    # ── NSE Indices ──────────────────────────────────────────────────────────
    {"symbol": "^NSEI",       "name": "Nifty 50",       "type": "index", "currency": "₹"},
    {"symbol": "^NSEBANK",    "name": "Bank Nifty",     "type": "index", "currency": "₹"},
    {"symbol": "^CNXIT",      "name": "Nifty IT",       "type": "index", "currency": "₹"},
    {"symbol": "^CNXPHARMA",  "name": "Nifty Pharma",   "type": "index", "currency": "₹"},
    {"symbol": "^CNXAUTO",    "name": "Nifty Auto",     "type": "index", "currency": "₹"},
    {"symbol": "^CNXFMCG",    "name": "Nifty FMCG",    "type": "index", "currency": "₹"},
    {"symbol": "^CNXMETAL",   "name": "Nifty Metal",    "type": "index", "currency": "₹"},
    {"symbol": "^CNXREALTY",  "name": "Nifty Realty",   "type": "index", "currency": "₹"},
    {"symbol": "^CNXENERGY",  "name": "Nifty Energy",   "type": "index", "currency": "₹"},
    {"symbol": "^CNXINFRA",   "name": "Nifty Infra",    "type": "index", "currency": "₹"},
    {"symbol": "^NSMIDCP",    "name": "Nifty Midcap",   "type": "index", "currency": "₹"},
    {"symbol": "^CNXPSUBANK",   "name": "Nifty PSU Bank",  "type": "index", "currency": "₹"},
    {"symbol": "^CNXFINANCE",   "name": "Nifty Finance",   "type": "index", "currency": "₹"},
    {"symbol": "^CNX100",       "name": "Nifty 100",       "type": "index", "currency": "₹"},
    {"symbol": "^CNXSMALLCAP",  "name": "Nifty Smallcap",  "type": "index", "currency": "₹"},
    {"symbol": "^CNXMEDIA",     "name": "Nifty Media",     "type": "index", "currency": "₹"},
    {"symbol": "^CNXSERVICE",   "name": "Nifty Services",  "type": "index", "currency": "₹"},
    {"symbol": "^CNXOILGAS",    "name": "Nifty Oil & Gas", "type": "index", "currency": "₹"},
    {"symbol": "^CNXCMDT",      "name": "Nifty Commodities","type": "index","currency": "₹"},
    {"symbol": "^CNXHEALTHCARE","name": "Nifty Healthcare", "type": "index", "currency": "₹"},
    # ── Additional NSE Indices ────────────────────────────────────────────────
    {"symbol": "^CNX200",       "name": "Nifty 200",        "type": "index", "currency": "₹"},
    {"symbol": "^CNX500",       "name": "Nifty 500",        "type": "index", "currency": "₹"},
    {"symbol": "^NIFMDCP100",   "name": "Nifty Midcap 100", "type": "index", "currency": "₹"},
    {"symbol": "^CNXMNC",       "name": "Nifty MNC",        "type": "index", "currency": "₹"},
    {"symbol": "^CNXCPSE",      "name": "Nifty CPSE",       "type": "index", "currency": "₹"},
    {"symbol": "^CNXPSE",       "name": "Nifty PSE",        "type": "index", "currency": "₹"},
    {"symbol": "^CNXCONSUM",    "name": "Nifty Consumption", "type": "index","currency": "₹"},
    {"symbol": "^NIFPVTBNK",    "name": "Nifty Pvt Bank",   "type": "index", "currency": "₹"},
    # ── NSE F&O Indices (speculative Yahoo Finance tickers — skip if unavailable) ──
    {"symbol": "^CNXJUNIOR",    "name": "Nifty Next 50",    "type": "index", "currency": "₹"},
    {"symbol": "^NIFMIDSEL",    "name": "Nifty Midcap Sel", "type": "index", "currency": "₹"},
    {"symbol": "^CNXCONDURAB",  "name": "Nifty Con Durables","type":"index", "currency": "₹"},
    {"symbol": "^CNXDEFENCE",   "name": "Nifty Defence",    "type": "index", "currency": "₹"},
    {"symbol": "^CNXMNFG",      "name": "Nifty Mfg",        "type": "index", "currency": "₹"},
    {"symbol": "^INDIAVIX",     "name": "India VIX",        "type": "index", "currency": "₹"},
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

# ── Stock → Primary NSE sector index tag ─────────────────────────────────────
SECTOR_MAP = {
    # BANK — Bank Nifty / PSU Bank / Private Bank
    "HDFCBANK.NS":"BANK","ICICIBANK.NS":"BANK","KOTAKBANK.NS":"BANK",
    "SBIN.NS":"BANK","AXISBANK.NS":"BANK","INDUSINDBK.NS":"BANK",
    "BANKBARODA.NS":"BANK","PNB.NS":"BANK","CANBK.NS":"BANK",
    "AUBANK.NS":"BANK","BANDHANBNK.NS":"BANK","FEDERALBNK.NS":"BANK",
    "IDFCFIRSTB.NS":"BANK","RBLBANK.NS":"BANK","UJJIVAN.NS":"BANK",
    "EQUITASBNK.NS":"BANK",
    # FIN — Nifty Financial Services
    "BAJFINANCE.NS":"FIN","BAJAJFINSV.NS":"FIN","SHRIRAMFIN.NS":"FIN",
    "CHOLAFIN.NS":"FIN","MUTHOOTFIN.NS":"FIN","HDFCAMC.NS":"FIN",
    "ICICIPRULI.NS":"FIN","HDFCLIFE.NS":"FIN","SBILIFE.NS":"FIN",
    "CAMS.NS":"FIN","CANFINHOME.NS":"FIN","LICHSGFIN.NS":"FIN",
    "MANAPPURAM.NS":"FIN","MCX.NS":"FIN","MOTILALOFS.NS":"FIN",
    "PFC.NS":"FIN","RECLTD.NS":"FIN","ANGELONE.NS":"FIN",
    "NUVAMA.NS":"FIN","SUNDARMFIN.NS":"FIN","ABCAPITAL.NS":"FIN",
    "MFSL.NS":"FIN","PEL.NS":"FIN","POLICYBZR.NS":"FIN",
    "CDSL.NS":"FIN","IIFL.NS":"FIN","KFINTECH.NS":"FIN",
    "NIACL.NS":"FIN","PNBHOUSING.NS":"FIN","UTIAMC.NS":"FIN",
    "LICI.NS":"FIN","BAJAJHLDNG.NS":"FIN",
    # IT — Nifty IT
    "TCS.NS":"IT","INFY.NS":"IT","WIPRO.NS":"IT","HCLTECH.NS":"IT",
    "TECHM.NS":"IT","LTIM.NS":"IT","MPHASIS.NS":"IT","PERSISTENT.NS":"IT",
    "NAUKRI.NS":"IT","OFSS.NS":"IT","COFORGE.NS":"IT","BSOFT.NS":"IT",
    "HAPPSTMNDS.NS":"IT","KPITTECH.NS":"IT","LTTS.NS":"IT",
    "TATATECH.NS":"IT","TATACOMM.NS":"IT",
    # PHARMA — Nifty Pharma
    "SUNPHARMA.NS":"PHARMA","DRREDDY.NS":"PHARMA","CIPLA.NS":"PHARMA",
    "DIVISLAB.NS":"PHARMA","LUPIN.NS":"PHARMA","TORNTPHARM.NS":"PHARMA",
    "AUROPHARMA.NS":"PHARMA","BIOCON.NS":"PHARMA","GLENMARK.NS":"PHARMA",
    "GRANULES.NS":"PHARMA","LAURUSLABS.NS":"PHARMA","NAVINFLUOR.NS":"PHARMA",
    "ALKEM.NS":"PHARMA","IPCALAB.NS":"PHARMA","JBCHEPHARM.NS":"PHARMA",
    "NATCOPHARM.NS":"PHARMA","SPARC.NS":"PHARMA","ZYDUSLIFE.NS":"PHARMA",
    "METROPOLIS.NS":"PHARMA","PIIND.NS":"PHARMA",
    # HLTH — Nifty Healthcare (hospitals, diagnostics)
    "APOLLOHOSP.NS":"HLTH","EIHOTEL.NS":"HLTH",
    # AUTO — Nifty Auto
    "MARUTI.NS":"AUTO","TATAMOTORS.NS":"AUTO","BAJAJ-AUTO.NS":"AUTO",
    "EICHERMOT.NS":"AUTO","HEROMOTOCO.NS":"AUTO","TVSMOTOR.NS":"AUTO",
    "MOTHERSON.NS":"AUTO","APOLLOTYRE.NS":"AUTO","ASHOKLEY.NS":"AUTO",
    "ESCORTS.NS":"AUTO","EXIDEIND.NS":"AUTO","SONACOMS.NS":"AUTO",
    "BALKRISIND.NS":"AUTO",
    # FMCG — Nifty FMCG
    "HINDUNILVR.NS":"FMCG","ITC.NS":"FMCG","NESTLEIND.NS":"FMCG",
    "BRITANNIA.NS":"FMCG","DABUR.NS":"FMCG","MARICO.NS":"FMCG",
    "COLPAL.NS":"FMCG","GODREJCP.NS":"FMCG","TATACONSUM.NS":"FMCG",
    "UBL.NS":"FMCG","EMAMI.NS":"FMCG","KALYANKJIL.NS":"FMCG",
    "PAGEIND.NS":"FMCG","KANSAINER.NS":"FMCG","KRBL.NS":"FMCG",
    # METAL — Nifty Metal
    "TATASTEEL.NS":"METAL","JSWSTEEL.NS":"METAL","HINDALCO.NS":"METAL",
    "COALINDIA.NS":"METAL","VEDL.NS":"METAL","SAIL.NS":"METAL",
    "NMDC.NS":"METAL","JINDALSTEL.NS":"METAL","JSL.NS":"METAL",
    "TRIDENT.NS":"METAL",
    # ENERGY — Nifty Energy / Power
    "NTPC.NS":"ENERGY","POWERGRID.NS":"ENERGY","TATAPOWER.NS":"ENERGY",
    "CESC.NS":"ENERGY","IEX.NS":"ENERGY","SOLARINDS.NS":"ENERGY",
    "TORNTPOWER.NS":"ENERGY","INOXWIND.NS":"ENERGY","ADANIGREEN.NS":"ENERGY",
    # OIL — Nifty Oil & Gas
    "ONGC.NS":"OIL","BPCL.NS":"OIL","GAIL.NS":"OIL","IOC.NS":"OIL",
    "HPCL.NS":"OIL","ATGL.NS":"OIL","MGL.NS":"OIL","GUJGASLTD.NS":"OIL",
    "OIL.NS":"OIL",
    # REALTY — Nifty Realty
    "DLF.NS":"REALTY","GODREJPROP.NS":"REALTY","OBEROIRLTY.NS":"REALTY",
    "BRIGADE.NS":"REALTY","PRESTIGE.NS":"REALTY","SOBHA.NS":"REALTY",
    "PHOENIXLTD.NS":"REALTY",
    # MEDIA — Nifty Media
    "ZEEL.NS":"MEDIA","SUNTV.NS":"MEDIA",
    # INFRA — Nifty Infra
    "LT.NS":"INFRA","ADANIENT.NS":"INFRA","ADANIPORTS.NS":"INFRA",
    "CONCOR.NS":"INFRA","INDUSTOWER.NS":"INFRA","GMRAIRPORT.NS":"INFRA",
    "NBCC.NS":"INFRA","RVNL.NS":"INFRA","IRCTC.NS":"INFRA",
    # CAPGDS — Capital Goods / Engineering / Defence
    "SIEMENS.NS":"CAPGDS","HAVELLS.NS":"CAPGDS","BHEL.NS":"CAPGDS",
    "HAL.NS":"CAPGDS","AIAENG.NS":"CAPGDS","APLAPOLLO.NS":"CAPGDS",
    "CUMMINSIND.NS":"CAPGDS","KAYNES.NS":"CAPGDS","SUPREMEIND.NS":"CAPGDS",
    "DIXON.NS":"CAPGDS","CARBORUNIV.NS":"CAPGDS","ELGIEQUIP.NS":"CAPGDS",
    "GRINDWELL.NS":"CAPGDS","THERMAXLTD.NS":"CAPGDS","TIINDIA.NS":"CAPGDS",
    "TRITURBINE.NS":"CAPGDS","ASTRAL.NS":"CAPGDS",
    # CHEM — Nifty Commodities / Chemicals
    "SRF.NS":"CHEM","PIDILITIND.NS":"CHEM","DEEPAKNTR.NS":"CHEM",
    "GNFC.NS":"CHEM","TATACHEM.NS":"CHEM","CHAMBLFERT.NS":"CHEM",
    "FINEORG.NS":"CHEM","NOCIL.NS":"CHEM","SUDARSCHEM.NS":"CHEM",
    "SUMICHEM.NS":"CHEM","VINATIORGA.NS":"CHEM",
    # CMDT — Nifty Commodities / Cement
    "ULTRACEMCO.NS":"CMDT","AMBUJACEM.NS":"CMDT","ACC.NS":"CMDT",
    "DALBHARAT.NS":"CMDT","INDIACEM.NS":"CMDT","JKCEMENT.NS":"CMDT",
    "GRASIM.NS":"CMDT",
    # CONSUM — Consumer / Retail / Durables
    "TITAN.NS":"CONSUM","ABFRL.NS":"CONSUM","CROMPTON.NS":"CONSUM",
    "DELHIVERY.NS":"CONSUM","JUBLFOOD.NS":"CONSUM","NYKAA.NS":"CONSUM",
    "REDINGTON.NS":"CONSUM","VGUARD.NS":"CONSUM","DMART.NS":"CONSUM",
    "TRENT.NS":"CONSUM","LUXIND.NS":"CONSUM","ASIANPAINT.NS":"CONSUM",
    "BERGEPAINT.NS":"CONSUM","BATAINDIA.NS":"CONSUM","PVRINOX.NS":"CONSUM",
    # FIN additions
    "ICICIGI.NS":"FIN","M&MFIN.NS":"FIN","LTFH.NS":"FIN",
    "IREDA.NS":"FIN","HUDCO.NS":"FIN",
    # IT additions
    "CYIENT.NS":"IT","TANLA.NS":"IT","AFFLE.NS":"IT",
    # AUTO additions
    "BHARATFORG.NS":"AUTO","CEATLTD.NS":"AUTO","SUNDRMFAST.NS":"AUTO",
    # ENERGY additions
    "ADANIPOWER.NS":"ENERGY","NHPC.NS":"ENERGY","SUZLON.NS":"ENERGY",
    # METAL additions
    "HINDZINC.NS":"METAL","NATIONALUM.NS":"METAL",
    # CHEM additions
    "DEEPAKFERT.NS":"CHEM",
    # CAPGDS additions
    "BEL.NS":"CAPGDS","POLYCAB.NS":"CAPGDS","BEML.NS":"CAPGDS","TITAGARH.NS":"CAPGDS",
    # REALTY additions
    "ANANTRAJ.NS":"REALTY",
    # INFRA additions
    "KPIL.NS":"INFRA",
}

# ── SuperTrend ────────────────────────────────────────────────────────────────
def supertrend(high, low, close, period=10, mult=2.0):
    n = len(close)
    if n < period + 5:
        return np.full(n, np.nan), np.zeros(n, dtype=int)
    h,l,c = np.array(high),np.array(low),np.array(close)
    tr = np.zeros(n); tr[0] = h[0]-l[0]
    for i in range(1,n):
        tr[i] = max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    atr = np.zeros(n)
    for i in range(period-1,n):
        atr[i] = np.mean(tr[i-period+1:i+1])
    mid=(h+l)/2.0; ub_r=mid+mult*atr; lb_r=mid-mult*atr
    ub,lb=ub_r.copy(),lb_r.copy()
    for i in range(1,n):
        ub[i]=ub_r[i] if (ub_r[i]<ub[i-1] or c[i-1]>ub[i-1]) else ub[i-1]
        lb[i]=lb_r[i] if (lb_r[i]>lb[i-1] or c[i-1]<lb[i-1]) else lb[i-1]
    st=np.zeros(n); d=np.zeros(n,dtype=int)
    st[0]=ub[0]; d[0]=-1
    for i in range(1,n):
        if st[i-1]==ub[i-1]:
            st[i]=lb[i] if c[i]>ub[i] else ub[i]; d[i]=1 if c[i]>ub[i] else -1
        else:
            st[i]=ub[i] if c[i]<lb[i] else lb[i]; d[i]=-1 if c[i]<lb[i] else 1
    return st,d

def calc_rsi(close,p=14):
    s=pd.Series(close); dif=s.diff()
    g=dif.where(dif>0,0.0); ls=-dif.where(dif<0,0.0)
    rs=g.rolling(p).mean()/ls.rolling(p).mean().replace(0,np.nan)
    return (100-100/(1+rs)).values

RANK={"FRESH ENTRY":0,"RE-ENTRY":1,"RE-ENTRY READY":2,"BULLISH":3,"SOFT EXIT":4,
      "FRESH SHORT":5,"SHORT RE-ENTRY":6,"SHORT READY":7,"BEARISH":8,"SHORT COVER":9}

def classify(d20,d25,dm,rsi_v,pct52):
    if len(d20)<2 or len(d25)<2: return "BEARISH",0,False,False,False
    c20,p20=int(d20[-1]),int(d20[-2]); c25,p25=int(d25[-1]),int(d25[-2])
    cm=int(dm[-1]) if len(dm)>0 else -1
    rsi=float(rsi_v) if not np.isnan(rsi_v) else 50.0
    pct=float(pct52)
    fresh=c25==1 and p25==-1; bear25=c25==-1 and p25==1
    bull20=c20==1 and p20==-1; bear20=c20==-1 and p20==1
    # ── Bullish hierarchy ────────────────────────────────────────────────────────
    if   fresh:              sig="FRESH ENTRY"      # ST2.5 just flipped bullish
    elif bull20 and c25==1:  sig="RE-ENTRY"         # ST2.5 bull, ST2.0 just flipped bull
    elif bear20 and c25==1:  sig="SOFT EXIT"        # ST2.5 bull, ST2.0 just flipped bear
    elif c25==1 and c20==1:  sig="BULLISH"          # both bullish — established uptrend
    elif c25==1 and c20==-1: sig="RE-ENTRY READY"   # ST2.5 bull, ST2.0 still bear (pullback)
    # ── Bearish hierarchy (mirror) ───────────────────────────────────────────────
    elif bear25:             sig="FRESH SHORT"      # ST2.5 just flipped bearish
    elif bear20 and c25==-1: sig="SHORT RE-ENTRY"   # ST2.5 bear, ST2.0 just flipped bear
    elif bull20 and c25==-1: sig="SHORT COVER"      # ST2.5 bear, ST2.0 just flipped bull
    elif c25==-1 and c20==1: sig="SHORT READY"      # ST2.5 bear, ST2.0 still bull (bounce)
    else:                    sig="BEARISH"           # both bearish — established downtrend
    # ── Quality filters (direction-aware) ────────────────────────────────────────
    if c25==1:   # bullish: monthly ST bull, RSI>50, within 30% of 52W high
        f1=cm==1; f2=rsi>50; f3=pct<=30.0
    else:        # bearish: monthly ST bear, RSI<50, at least 20% off 52W high
        f1=cm==-1; f2=rsi<50; f3=pct>=20.0
    fc=int(f1)+int(f2)+int(f3)
    return sig,fc,f1,f2,f3

# ── Analyse any OHLC series (stocks + instruments) ───────────────────────────
def analyse(sym, display_name=None, itype="stock", currency="₹", segment=None):
    try:
        tk=yf.Ticker(sym)
        wk=tk.history(period="3y",interval="1wk",auto_adjust=True)
        mo=tk.history(period="5y",interval="1mo",auto_adjust=True)
        if len(wk)<30 or len(mo)<15: return None
        st20,d20=supertrend(wk.High,wk.Low,wk.Close,10,2.0)
        st25,d25=supertrend(wk.High,wk.Low,wk.Close,10,2.5)
        _,dm    =supertrend(mo.High,mo.Low,mo.Close,10,2.0)
        rsi_arr=calc_rsi(wk.Close.values,14)
        rsi_v=float(rsi_arr[-1]) if not np.isnan(rsi_arr[-1]) else 0.0
        price=float(wk.Close.iloc[-1])
        h52=float(wk.High.rolling(52).max().iloc[-1])
        pct52=round((1-price/h52)*100,1) if h52>0 else 100.0
        sig,fc,f1,f2,f3=classify(d20,d25,dm,rsi_v,pct52)
        cur=int(d25[-1]); age_wks=0
        for i in range(len(d25)-1,-1,-1):
            if int(d25[i])==cur: age_wks+=1
            else: break
        name=display_name or sym.replace(".NS","")
        sector=SECTOR_MAP.get(sym) if itype=="stock" else None
        print(f"  {name:<18} {itype:<10} {sig}")
        return {"symbol":name,"price":round(price,2),"signal":sig,
                "rank":RANK.get(sig,7),"quality":fc,
                "f1":f1,"f2":f2,"f3":f3,"rsi":round(rsi_v,1),
                "pct52w":pct52,"st25":round(float(st25[-1]),2),
                "st20":round(float(st20[-1]),2),
                "dir25":int(d25[-1]),"dir20":int(d20[-1]),
                "type":itype,"currency":currency,
                "segment":segment,"signal_age_wks":age_wks,
                "sector":sector}
    except Exception as e:
        name=display_name or sym
        print(f"  {name:<18} SKIP: {e}"); return None

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    now=datetime.now(IST)
    print(f"\nST SCREENER  {now.strftime('%d %b %Y  %H:%M IST')}\n")

    results=[]

    def scan_parallel(lst, seg, label):
        print(f"\n── {label} ──")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            futs={ex.submit(analyse,s,segment=seg):s for s in lst}
            for fut in concurrent.futures.as_completed(futs):
                r=fut.result()
                if r: results.append(r)

    scan_parallel(NIFTY100,      "nifty100", "Nifty 100 stocks")
    scan_parallel(NIFTY_FO_EXTRA,"fo",       "Nifty F&O extra stocks")
    scan_parallel(NIFTY500_EXTRA,"n500",     "Nifty 500 extra stocks")

    # Scan instruments sequentially
    print("\n── Instruments (indices / currency / commodities) ──")
    for inst in INSTRUMENTS:
        r=analyse(inst["symbol"], inst["name"], inst["type"], inst["currency"])
        if r: results.append(r)

    # Sort: signal rank → quality desc → symbol
    results.sort(key=lambda x:(x["rank"],-x["quality"],x["symbol"]))

    counts={}
    for r in results: counts[r["signal"]]=counts.get(r["signal"],0)+1

    stocks=[r for r in results if r["type"]=="stock"]
    others=[r for r in results if r["type"]!="stock"]
    n100=[r for r in stocks if r.get("segment")=="nifty100"]
    nfo =[r for r in stocks if r.get("segment") in ("nifty100","fo")]
    print(f"\nDone: N100={len(n100)}  F&O={len(nfo)}  N500={len(stocks)}  Instr={len(others)}")
    for s,c in sorted(counts.items(),key=lambda x:RANK.get(x[0],9)):
        print(f"  {s:<20} {c}")

    import os; os.makedirs("data",exist_ok=True)
    json.dump({"scan_time":now.strftime("%d %b %Y  %H:%M IST"),
               "total_scanned":len(stocks),
               "total_instruments":len(others),
               "n100_count":len(n100),
               "fo_count":len(nfo),
               "n500_count":len(stocks),
               "counts":counts,"results":results},
              open("data/screener_results.json","w"),indent=2)
    print("Saved data/screener_results.json")

if __name__=="__main__":
    main()
