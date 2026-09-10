import sqlite3
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def run_fully_automated_system():
    db_path = 's2pro_research_master.db'
    
    # القائمة الأساسية للأصول المستهدفة بالرصد الآلي
    assets = {
        "سابك (SABIC)": "2010.SR",
        "مصرف الراجحي": "1120.SR",
        "أرامكو السعودية": "2222.SR",
        "الأهلي السعودي": "1180.SR",
        "التصنيع الوطنية": "2130.SR",
        "مؤشر تاسي (TASI)": "^TASI.SR"
    }
    
    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # التأكد من وجود الجدول
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
        conn.commit()

        # 1. المرحلة الأولى: الرصد والتسجيل الآلي للأسهم إذا لم يتم رصدها اليوم
        for asset_name, ticker in assets.items():
            # التحقق هل يوجد رصد نشط لهذا السهم في نفس اليوم
            cursor.execute('''
                SELECT id FROM master_study_log 
                WHERE ticker = ? AND study_date LIKE ? AND evaluation_result LIKE '%قيد المراقبة%'
            ''', (ticker, f"{today_str}%"))
            
            existing = cursor.fetchone()
            
            if not existing:
                try:
                    stock_obj = yf.Ticker(ticker)
                    df = stock_obj.history(period="60d", interval="1d")
                    if not df.empty:
                        df = df.dropna(subset=['Close'])
                        span_val = min(50, len(df))
                        df['EMA_50'] = df['Close'].ewm(span=span_val, adjust=False).mean()
                        
                        df['H-L'] = df['High'] - df['Low']
                        df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
                        df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
                        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
                        df['ATR'] = df['TR'].rolling(window=min(14, len(df))).mean()
                        
                        last_row = df.iloc[-1]
                        close_price = float(last_row['Close'])
                        ema_50 = float(last_row['EMA_50']) if not np.isnan(last_row['EMA_50']) else close_price
                        atr_val = last_row['ATR']
                        atr = float(atr_val) if not np.isnan(atr_val) else (close_price * 0.02)
                        
                        is_bullish = close_price > ema_50
                        trend_status = "مسار صاعد (Bullish)" if is_bullish else "مسار هابط (Bearish)"
                        
                        sl = close_price - (1.5 * atr) if is_bullish else close_price + (1.5 * atr)
                        risk_distance = abs(close_price - sl)
                        t1 = close_price + (1.0 * risk_distance) if is_bullish else close_price - (1.0 * risk_distance)
                        t4 = close_price + (4.0 * risk_distance) if is_bullish else close_price - (4.0 * risk_distance)
                        
                        eval_status = "⏳ قيد المراقبة (Active Tracking)"
                        current_date_full = datetime.now().strftime("%Y-%m-%d %H:%M")

                        cursor.execute('''
                            INSERT INTO master_study_log (study_date, asset_name, ticker, timeframe, logged_ep, invalidation_sl, target_t1, target_t4, trend_condition, current_market_price, evaluation_result)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (current_date_full, asset_name, ticker, "يومي (Daily)", close_price, sl, t1, t4, trend_status, close_price, eval_status))
                        conn.commit()
                except Exception as ex_inner:
                    print(f"Error auto-logging {ticker}: {ex_inner}")

        # 2. المرحلة الثانية: تحديث ومتابعة جميع النقاط السابقة والجديدة آلياً
        master_df = pd.read_sql_query("SELECT * FROM master_study_log", conn)
        
        for idx, row in master_df.iterrows():
            record_id = row['id']
            ticker = row['ticker']
            logged_ep = row['logged_ep']
            sl = row['invalidation_sl']
            t1 = row['target_t1']
            trend = row['trend_condition']
            current_status = row['evaluation_result']
            
            # إذا حُسمت النقطة سابقاً لا داعي لإعادة فحصها لتثبيت السجل التاريخي
            if "نجح" in current_status or "فشل" in current_status:
                continue

            try:
                live_obj = yf.Ticker(ticker)
                hist_df = live_obj.history(period="1d")
                curr_price = float(hist_df['Close'].iloc[-1]) if not hist_df.empty else logged_ep
            except:
                continue

            # تقييم حالة السعر الحالي مقارنة بالهدف ووقف الفاعلية
            if "صاعد" in trend or "Bullish" in trend:
                if curr_price >= t1:
                    new_eval = "✅ نجح (Target Hit)"
                elif curr_price <= sl:
                    new_eval = "❌ فشل (Stopped Out)"
                else:
                    new_eval = "⏳ قيد المراقبة (Active Tracking)"
            else:
                if curr_price <= t1:
                    new_eval = "✅ نجح هبوطياً (Target Hit)"
                elif curr_price >= sl:
                    new_eval = "❌ فشل (Stopped Out)"
                else:
                    new_eval = "⏳ قيد المراقبة (Active Tracking)"

            cursor.execute('''
                UPDATE master_study_log 
                SET current_market_price = ?, evaluation_result = ?
                WHERE id = ?
            ''', (curr_price, new_eval, record_id))

        conn.commit()
        conn.close()
        print("Fully automated academic study scan and tracking completed successfully.")
    except Exception as e:
        print(f"Error in automated system: {e}")

if __name__ == "__main__":
    run_fully_automated_system()
