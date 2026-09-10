import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

st.set_page_config(page_title="S2 Pro - Research & Data Matrix", layout="centered")

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

lang = st.sidebar.selectbox("Language / لغة الواجهة", ["العربية", "English"])

if lang == "العربية":
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F; margin-bottom: 15px; text-align: right;" dir="rtl">
    <b>⚠️ إخلاء مسؤولية بحثية:</b> النظام مخصص لأغراض الدراسة الأكاديمية ونمذجة الأسواق المالية (بيانات رقمية بحتة).
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - Quantitative Research Matrix")
    st.markdown("منظومة البيانات الرقمية والبحث الأكاديمي المعتمد للسوق السعودي")
else:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F;">
    <b>⚠️ Academic Disclaimer:</b> Quantitative research matrix and numeric financial modeling system.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - Quantitative Research Matrix")
    st.markdown("Numeric Market Research & Automated Tracking Matrix")

st.markdown("---")

assets_dict = {
    "سابك (SABIC)": "2010.SR",
    "مصرف الراجحي": "1120.SR",
    "أرامكو السعودية": "2222.SR",
    "الأهلي السعودي": "1180.SR",
    "التصنيع الوطنية": "2130.SR",
    "مؤشر تاسي (TASI)": "^TASI.SR"
}

selected_asset_name = st.sidebar.selectbox("اختر الأصل للدراسة الرقمية" if lang == "العربية" else "Select Asset for Study", list(assets_dict.keys()))
selected_ticker = assets_dict[selected_asset_name]
timeframe_option = st.sidebar.selectbox("الإطار الزمني للرصد" if lang == "العربية" else "Study Timeframe", ["يومي (Daily)", "أسبوعي (Weekly)"])

if lang == "العربية":
    st.subheader(f"📊 لوحة القياسات الرقمية: {selected_asset_name}")
else:
    st.subheader(f"📊 Numeric Metrics Panel: {selected_asset_name}")

try:
    live_stock = yf.Ticker(selected_ticker)
    live_df = live_stock.history(period="1mo")
    if not live_df.empty:
        current_p = float(live_df['Close'].iloc[-1])
        prev_p = float(live_df['Close'].iloc[-2]) if len(live_df) > 1 else current_p
        change_pct = ((current_p - prev_p) / prev_p) * 100 if prev_p > 0 else 0.0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("السعر اللحظي", f"{current_p:.2f} SAR", f"{change_pct:+.2f}%")
        c2.metric("أعلى سعر (شهر)", f"{live_df['High'].max():.2f} SAR")
        c3.metric("أدنى سعر (شهر)", f"{live_df['Low'].min():.2f} SAR")
        c4.metric("حالة المسار الفني", "صاعد" if current_p > live_df['Close'].ewm(span=20).mean().iloc[-1] else "هابط")
except Exception as ex:
    st.warning("تعذر جلب البيانات الرقمية اللحظية حالياً.")

st.markdown("---")

if lang == "العربية":
    st.markdown("### 📚 السجل الأكاديمي للبحث والدراسة (Master Study Register)")
    st.caption("يوثق نقاط الرصد الرقمي بانتظام، مع التمييز القاطع بين (سعر الرصد الثابت EP) و(السعر الحقيقي اللحظي للسوق).")
else:
    st.markdown("### 📚 Master Academic Study Register")
    st.caption("Documents numeric study points distinguishing between Logged Entry Price (EP) and Live Market Price.")

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

            try:
                live_obj = yf.Ticker(ticker)
                hist_df = live_obj.history(period="1d")
                curr_price = float(hist_df['Close'].iloc[-1]) if not hist_df.empty and not pd.isna(hist_df['Close'].iloc[-1]) else logged_ep
            except:
                curr_price = logged_ep

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
            c1.metric("إجمالي نقاط العينة", len(display_df))
            c2.metric("الحالات الناجحة ✅", success_tally)
            c3.metric("الحالات المخالفة ❌", failure_tally)
            c4.metric("نسبة النجاح الإحصائية", f"{hit_ratio:.1f}%")
        else:
            c1.metric("Total Sample Points", len(display_df))
            c2.metric("Successful Cases ✅", success_tally)
            c3.metric("Invalidated Cases ❌", failure_tally)
            c4.metric("Statistical Hit Rate", f"{hit_ratio:.1f}%")

        st.markdown("---")
        st.dataframe(display_df, use_container_width=True)

        export_csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 تحميل السجل الأكاديمي بصيغة CSV لإرفاقه بالبحث" if lang == "العربية" else "📥 Download Study Register CSV",
            data=export_csv,
            file_name="s2pro_research_study_register.csv",
            mime="text/csv"
        )
    else:
        st.info("السجل فارغ حالياً بانتظار التحديث الآلي في الخلفية." if lang == "العربية" else "Register is empty.")

except Exception as db_err:
    st.error(f"Error: {db_err}")
