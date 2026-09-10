import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

st.set_page_config(page_title="S2 Pro - دراسة بحثية للسوق السعودي", layout="centered")

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
    st.title("🇸🇦 S2 Pro - دراسة بحثية للسوق السعودي")
    st.markdown("منظومة القياسات الرقمية والرصد الآلي والأخبار اليومية")
else:
    st.title("🇸🇦 S2 Pro - Saudi Market Research")
    st.markdown("Quantitative Metrics, Automated Logging & Live Asset News")

st.markdown("---")

assets_dict = {
    "سابك (SABIC)": "2010.SR",
    "مصرف الراجحي": "1120.SR",
    "أرامكو السعودية": "2222.SR",
    "الأهلي السعودي": "1180.SR",
    "التصنيع الوطنية": "2130.SR",
    "مؤشر تاسي (TASI)": "^TASI.SR"
}

selected_asset_name = st.sidebar.selectbox("اختر الأصل للدراسة" if lang == "العربية" else "Select Asset", list(assets_dict.keys()))
selected_ticker = assets_dict[selected_asset_name]
timeframe_option = st.sidebar.selectbox("الإطار الزمني" if lang == "العربية" else "Timeframe", ["يومي (Daily)", "أسبوعي (Weekly)"])

# دالة الرصد والتسجيل الآلي التكاملي للأسهم المذكورة
def auto_log_asset(aname, tk, tf):
    conn = sqlite3.connect('s2pro_research_master.db')
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute('SELECT id FROM master_study_log WHERE ticker = ? AND study_date LIKE ?', (tk, f"{today_str}%"))
    if not cursor.fetchone():
        try:
            s_obj = yf.Ticker(tk)
            cdf = s_obj.history(period="60d", interval="1d")
            if not cdf.empty:
                cdf = cdf.dropna(subset=['Close'])
                cp = float(cdf['Close'].iloc[-1])
                ema50 = float(cdf['Close'].ewm(span=min(50, len(cdf)), adjust=False).mean().iloc[-1])
                atr = float((cdf['High'] - cdf['Low']).rolling(14).mean().iloc[-1]) if len(cdf) >= 14 else cp * 0.02
                is_bul = cp > ema50
                tr_stat = "مسار صاعد (Bullish)" if is_bul else "مسار هابط (Bearish)"
                sl_v = cp - (1.5 * atr) if is_bul else cp + (1.5 * atr)
                rd = abs(cp - sl_v)
                t1_v = cp + rd if is_bul else cp - rd
                t4_v = cp + (4 * rd) if is_bul else cp - (4 * rd)
                
                cursor.execute('''
                    INSERT INTO master_study_log (study_date, asset_name, ticker, timeframe, logged_ep, invalidation_sl, target_t1, target_t4, trend_condition, current_market_price, evaluation_result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (datetime.now().strftime("%Y-%m-%d %H:%M"), aname, tk, tf, cp, sl_v, t1_v, t4_v, tr_stat, cp, "⏳ قيد المراقبة (Active Tracking)"))
                conn.commit()
        except Exception as e:
            print(f"Auto log error: {e}")
    conn.close()

auto_log_asset(selected_asset_name, selected_ticker, timeframe_option)

if lang == "العربية":
    st.subheader(f"📊 القياسات الرقمية الحالية: {selected_asset_name}")
else:
    st.subheader(f"📊 Current Numeric Metrics: {selected_asset_name}")

try:
    live_stock = yf.Ticker(selected_ticker)
    live_df = live_stock.history(period="1mo")
    
    if not live_df.empty and 'Close' in live_df.columns:
        live_df = live_df.dropna(subset=['Close'])
        current_p = float(live_df['Close'].iloc[-1])
        prev_p = float(live_df['Close'].iloc[-2]) if len(live_df) > 1 else current_p
        change_pct = ((current_p - prev_p) / prev_p) * 100 if prev_p > 0 else 0.0
        
        ema50 = float(live_df['Close'].ewm(span=min(50, len(live_df)), adjust=False).mean().iloc[-1])
        is_bullish = current_p > ema50
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("السعر اللحظي", f"{current_p:.2f} SAR", f"{change_pct:+.2f}%")
        c2.metric("متوسط الحركة (EMA50)", f"{ema50:.2f} SAR")
        c3.metric("أعلى سعر للفترة", f"{live_df['High'].max():.2f} SAR")
        c4.metric("حالة المسار الفني", "صاعد (Bullish)" if is_bullish else "هابط (Bearish)")
        
except Exception as ex:
    st.warning("تعذر جلب البيانات اللحظية الحالية.")

st.markdown("---")

# قسم الأخبار اليومية للأصل
if lang == "العربية":
    st.markdown(f"📰 **أحدث الأخبار والتحديثات اليومية للأصل: {selected_asset_name}**")
else:
    st.markdown(f"📰 **Latest Daily News for {selected_asset_name}**")

try:
    stock_news = live_stock.news
    if stock_news and len(stock_news) > 0:
        for item in stock_news[:4]:
            title = item.get('title', 'No Title')
            publisher = item.get('publisher', 'Financial Source')
            link = item.get('link', '#')
            
            st.markdown(f"""
            <div style="background-color: #fcfcfc; padding: 10px; border-radius: 5px; border: 1px solid #eef0f2; margin-bottom: 8px;">
                <a href="{link}" target="_blank" style="text-decoration: none; color: #1f77b4; font-weight: bold; font-size: 14px;">{title}</a>
                <br><span style="color: gray; font-size: 11px;">المصدر: {publisher}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("لا توجد أخبار مسجلة لهذا الأصل في الجلسة الحالية.")
except Exception as news_err:
    st.info("خدمة الأخبار اللحظية تتطلب الاتصال المباشر بمزود البيانات.")

st.markdown("---")

if lang == "العربية":
    st.markdown("### 📚 سجل الدراسة الأكاديمية والبحثية")
else:
    st.markdown("### 📚 Academic Study Register")

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
                "سعر الرصد الثابت (EP)": round(logged_ep, 2),
                "السعر الحقيقي اللحظي": round(curr_price, 2),
                "الهدف الأول (T1)": round(t1, 2),
                "وقف الفاعلية (SL)": round(sl, 2),
                "حالة التقييم": eval_res
            })

        display_df = pd.DataFrame(updated_rows)
        
        total_closed = success_tally + failure_tally
        hit_ratio = (success_tally / total_closed * 100) if total_closed > 0 else 0.0

        sc1, sc2, sc3, sc4 = st.columns(4)
        if lang == "العربية":
            sc1.metric("إجمالي العينة", len(display_df))
            sc2.metric("الناجحة ✅", success_tally)
            sc3.metric("المخالفة ❌", failure_tally)
            sc4.metric("نسبة النجاح", f"{hit_ratio:.1f}%")
        else:
            sc1.metric("Total Sample", len(display_df))
            sc2.metric("Successful ✅", success_tally)
            sc3.metric("Invalidated ❌", failure_tally)
            sc4.metric("Hit Rate", f"{hit_ratio:.1f}%")

        st.markdown("---")
        st.dataframe(display_df, use_container_width=True)

        export_csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 تحميل السجل بصيغة CSV لإرفاقه بالبحث" if lang == "العربية" else "📥 Download Study Register CSV",
            data=export_csv,
            file_name="s2pro_research_study_register.csv",
            mime="text/csv"
        )
    else:
        st.info("السجل قيد التحديث الآلي..." if lang == "العربية" else "Register updating...")

except Exception as db_err:
    st.error(f"Error: {db_err}")
