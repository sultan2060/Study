import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

print("--- [S2 Pro] Running Automated Background Scan ---")

def run_automated_scan():
    conn = sqlite3.connect('s2pro_research_master.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_study_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_date TEXT,
            asset_name TEXT,
            ticker TEXT,
            timeframe TEXT,
            logged_ep REAL,
            invalidation_sl REAL,
            target_t1 REAL,
            target_t4 REAL,
            trend_condition TEXT,
            current_market_price REAL,
            evaluation_result TEXT
        )
    ''')
    
    assets_dict = {
        "سابك (SABIC)": "2010.SR",
        "مصرف الراجحي": "1120.SR",
        "أرامكو السعودية": "2222.SR",
        "الأهلي السعودي": "1180.SR",
        "التصنيع الوطنية": "2130.SR",
        "مؤشر تاسي (TASI)": "^TASI.SR"
    }
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_records_count = 0
    
    for aname, tk in assets_dict.items():
        cursor.execute('SELECT id FROM master_study_log WHERE ticker = ? AND study_date LIKE ?', (tk, f"{today_str}%"))
        if not cursor.fetchone():
            try:
                s_obj = yf.Ticker(tk)
                cdf = s_obj.history(period="60d", interval="1d")
                if not cdf.empty:
                    cdf = cdf.dropna(subset=['Close'])
                    cp = float(cdf['Close'].iloc[-1])
                    ema50 = float(cdf['Close'].ewm(span=min(50, len(cdf)), adjust=False).mean().iloc[-1])
                    atr = float((cdf['High'] - cdf['Low']).rolling(14).mean().iloc[-1]) if not np.isnan(cdf['High'].iloc[-1]) else cp * 0.02
                    is_bul = cp > ema50
                    tr_stat = "مسار صاعد (Bullish)" if is_bul else "مسار هابط (Bearish)"
                    sl_v = cp - (1.5 * atr) if is_bul else cp + (1.5 * atr)
                    rd = abs(cp - sl_v)
                    t1_v = cp + rd if is_bul else cp - rd
                    t4_v = cp + (4 * rd) if is_bul else cp - (4 * rd)
                    
                    cursor.execute('''
                        INSERT INTO master_study_log (study_date, asset_name, ticker, timeframe, logged_ep, invalidation_sl, target_t1, target_t4, trend_condition, current_market_price, evaluation_result)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (datetime.now().strftime("%Y-%m-%d %H:%M"), aname, tk, "يومي (Daily)", cp, sl_v, t1_v, t4_v, tr_stat, cp, "⏳ قيد المراقبة (Active Tracking)"))
                    conn.commit()
                    new_records_count += 1
            except Exception as e:
                print(f"Error on {aname}: {e}")
                
    conn.close()
    print(f"--- Scan Complete. New added today: {new_records_count} ---")

if __name__ == "__main__":
    run_automated_scan()
