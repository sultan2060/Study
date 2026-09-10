import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

st.set_page_config(page_title="S2 Pro - TASI Research Matrix", layout="centered")

def init_db():
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
    conn.commit()
    conn.close()

init_db()

# دالة المسح والتسجيل التلقائي عند فتح التطبيق (إذا لم تكن أصول اليوم مسجلة)
def auto_scan_and_seed_on_startup():
    assets = {
        "سابك (SABIC)": "2010.SR",
        "مصرف الراجحي": "1120.SR",
        "أرامكو السعودية": "2222.SR",
        "الأهلي السعودي": "1180.SR",
        "التصنيع الوطنية": "2130.SR",
        "مؤشر تاسي (TASI)": "^TASI.SR"
    }
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect('s2pro_research_master.db')
    cursor = conn.cursor()
    
    for asset_name, ticker in assets.items():
        # تحقق هل تم رصد هذا السهم اليوم أم لا
        cursor.execute('''
            SELECT id FROM master_study_log 
            WHERE ticker = ? AND study_date LIKE ?
        ''', (ticker, f"{today_str}%"))
        
        exists = cursor.fetchone()
        if not exists:
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
            except Exception as e:
                pass
    conn.close()

# تشغيل الفحص الآلي فور فتح الصفحة
auto_scan_and_seed_on_startup()

lang = st.sidebar.selectbox("Language / لغة الواجهة", ["العربية", "English"])

if lang == "العربية":
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F; margin-bottom: 15px; text-align: right;" dir="rtl">
    <b>⚠️ إخلاء مسؤولية بحثية:</b> النظام يقوم بالرصد والتسجيل الآلي الشامل لأغراض الدراسة الأكاديمية ونمذجة الأسواق المالية.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - Fully Automated Research Matrix")
    st.markdown("منظومة الرصد والتسجيل التراكمي المعتمد (تشغيل آلي بالكامل بدون تدخل بشري)")
else:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F;">
    <b>⚠️ Academic Disclaimer:</b> Fully automated research matrix and market modeling system.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - Fully Automated Research Matrix")
    st.markdown("Automated Master Research Log & Quantitative Evaluation Matrix")

st.markdown("---")
if lang == "العربية":
    st.markdown("### 📚 السجل التراكمي المعتمد للأبحاث (Master Study Register)")
    st.caption("يعرض هذا السجل الأسهم المرصودة آلياً، ويوضح بدقة التمييز بين (سعر الرصد الثابت وقت الدراسة EP) و(السعر الحقيقي اللحظي للسوق).")
else:
    st.markdown("### 📚 Master Academic Study Register")
    st.caption("Automatically tracks assets and distinguishes clearly between Logged Entry Price (EP) and Live Market Price.")

try:
    conn = sqlite3.connect('s2pro_research_master.db')
    master_df = pd.read_sql_query("SELECT * FROM master_study_log ORDER BY id DESC", conn)
    conn.close()

    if not master_df.empty:
        updated_rows = []
        success_tally = 0
        failure_tally = 0

        for idx, row in master_df.iterrows():
            ticker = row['ticker']
            logged_ep = row['logged_ep']
            sl = row['invalidation_sl']
            t1 = row['target_t1']
            trend = row['trend_condition']

            # جلب السعر الحقيقي اللحظي من السوق
            try:
                live_obj = yf.Ticker(ticker)
                hist_df = live_obj.history(period="1d")
                curr_price = float(hist_df['Close'].iloc[-1]) if not hist_df.empty else logged_ep
            except:
                curr_price = logged_ep

            # التقييم الرياضي
            if "صاعد" in trend or "Bullish" in trend:
                if curr_price >= t1:
                    eval_res = "✅ نجح (Target Hit)"
                    success_tally += 1
                elif curr_price <= sl:
                    eval_res = "❌ فشل (Stopped Out)"
                    failure_tally += 1
                else:
                    eval_res = "⏳ قيد المراقبة (Active Tracking)"
            else:
                if curr_price <= t1:
                    eval_res = "✅ نجح هبوطياً (Target Hit)"
                    success_tally += 1
                elif curr_price >= sl:
                    eval_res = "❌ فشل (Stopped Out)"
                    failure_tally += 1
                else:
                    eval_res = "⏳ قيد المراقبة (Active Tracking)"

            updated_rows.append({
                "ID": row['id'],
                "التاريخ والوقت": row['study_date'],
                "الأصل": row['asset_name'],
                "الإطار": row['timeframe'],
                "🎯 سعر الرصد الثابت (EP)": round(logged_ep, 2),
                "📈 السعر الحقيقي اللحظي": round(curr_price, 2),
                "الهدف المعياري (T1)": round(t1, 2),
                "وقف الفاعلية (SL)": round(sl, 2),
                "حالة التقييم الأكاديمي": eval_res
            })

        display_df = pd.DataFrame(updated_rows)
        
        total_closed = success_tally + failure_tally
        hit_ratio = (success_tally / total_closed * 100) if total_closed > 0 else 0.0

        c1, c2, c3, c4 = st.columns(4)
        if lang == "العربية":
            c1.metric("إجمالي نقاط العينة المرصودة", len(display_df))
            c2.metric("الحالات الناجحة ✅", success_tally)
            c3.metric("الحالات المخالفة ❌", failure_tally)
            c4.metric("نسبة النجاح الإحصائية", f"{hit_ratio:.1f}%")
        else:
            c1.metric("Total Sample Points", len(display_df))
            c2.metric("Successful Cases ✅", success_tally)
            c3.metric("Invalidated Cases ❌", failure_tally)
            c4.metric("Statistical Hit Rate", f"{hit_ratio:.1f}%")

        st.markdown("---")
        # عرض الجدول مع تمييز أعمدة السعر الثابت وسعر السوق
        st.dataframe(display_df, use_container_width=True)

        export_csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 تحميل السجل التراكمي المعتمد بصيغة CSV لإرفاقه بالبحث الأكاديمي" if lang == "العربية" else "📥 Download Master Academic Log CSV",
            data=export_csv,
            file_name="s2pro_master_study_register.csv",
            mime="text/csv"
        )
    else:
        st.info("جاري تحميل وإعداد السجل الآلي..." if lang == "العربية" else "Initializing automated master log...")

except Exception as db_err:
    st.error(f"Error in master database register: {db_err}")
