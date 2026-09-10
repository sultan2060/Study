import sqlite3
import yfinance as yf
import pandas as pd
import numpy as np

def background_evaluate():
    db_path = 's2pro_research_master.db'
    try:
        conn = sqlite3.connect(db_path)
        master_df = pd.read_sql_query("SELECT * FROM master_study_log", conn)
        
        if master_df.empty:
            conn.close()
            return

        cursor = conn.cursor()
        
        for idx, row in master_df.iterrows():
            record_id = row['id']
            ticker = row['ticker']
            logged_ep = row['logged_ep']
            sl = row['invalidation_sl']
            t1 = row['target_t1']
            trend = row['trend_condition']
            current_status = row['evaluation_result']
            
            # إذا كانت النقطة قد حسمت سابقاً (نجاح أو فشل)، تجاوزها لتثبيت السجل التاريخي
            if "نجح" in current_status or "فشل" in current_status:
                continue

            try:
                live_obj = yf.Ticker(ticker)
                hist_df = live_obj.history(period="1d")
                curr_price = float(hist_df['Close'].iloc[-1]) if not hist_df.empty else logged_ep
            except:
                continue

            # تقييم الحالة رياضياً
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

            # تحديث السعر الحالي والنتيجة في قاعدة البيانات
            cursor.execute('''
                UPDATE master_study_log 
                SET current_market_price = ?, evaluation_result = ?
                WHERE id = ?
            ''', (curr_price, new_eval, record_id))

        conn.commit()
        conn.close()
        print("Background academic study log successfully updated.")
    except Exception as e:
        print(f"Error in background tracker: {e}")

if __name__ == "__main__":
    background_evaluate()
