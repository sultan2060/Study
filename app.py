import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import urllib.parse
import sqlite3
from datetime import datetime

st.set_page_config(page_title="S2 Pro - TASI Quant Matrix", layout="centered")

# --- تهيئة قاعدة البيانات المحلية لتسجيل الأبحاث تلقائياً ---
def init_db():
    conn = sqlite3.connect('s2pro_research.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            asset TEXT,
            timeframe TEXT,
            entry_price REAL,
            stop_loss REAL,
            target_1 REAL,
            target_4 REAL,
            trend_status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_to_research_log(date, asset, tf, ep, sl, t1, t4, trend):
    conn = sqlite3.connect('s2pro_research.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tracking_log (date, asset, timeframe, entry_price, stop_loss, target_1, target_4, trend_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, asset, tf, ep, sl, t1, t4, trend))
    conn.commit()
    conn.close()

# اختيار لغة الواجهة من الشريط الجانبي
lang = st.sidebar.selectbox("Language / لغة الواجهة", ["العربية", "English"])

if lang == "العربية":
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F; margin-bottom: 15px; text-align: right;" dir="rtl">
    <b>⚠️ إخلاء مسؤولية:</b> التطبيق لأغراض الدراسة والبحث العلمي فقط، ولا يقدم أي توصيات أو استشارات مالية.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - TASI Quant Matrix")
    st.markdown("منظومة التحليل الكمي والربط الإخباري للأسهم السعودية")

    assets = {
        "سابك (SABIC)": "2010.SR",
        "مصرف الراجحي": "1120.SR",
        "أرامكو السعودية": "2222.SR",
        "الأهلي السعودي": "1180.SR",
        "التصنيع الوطنية": "2130.SR",
        "مؤشر تاسي (TASI)": "^TASI.SR"
    }

    selected_asset_name = st.selectbox("اختر الأصل أو السهم للتداول:", list(assets.keys()))
    ticker_symbol = assets[selected_asset_name]

    timeframe_options = {
        "يومي (Daily)": {"interval": "1d", "period": "1y"},
        "أسبوعي (Weekly)": {"interval": "1wk", "period": "3y"},
        "شهري (Monthly)": {"interval": "1mo", "period": "5y"},
        "سنوي (Yearly)": {"interval": "1mo", "period": "max"}
    }

    selected_tf_name = st.selectbox("اختر الفريم الزمني (يدعم كافة الأطر اليومية والأسبوعية والشهرية والسنوية):", list(timeframe_options.keys()))
    tf_config = timeframe_options[selected_tf_name]

    run_btn = st.button("تحليـل وتشغيل الرادار الفني والإخباري وتثبيت السجل")
    
else:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F; margin-bottom: 15px;">
    <b>⚠️ Disclaimer:</b> For study and research purposes only; this application does not provide financial or investment advice.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - TASI Quant Matrix")
    st.markdown("Quantitative Analysis & News Matrix for Saudi Equities")

    assets = {
        "SABIC": "2010.SR",
        "Al Rajhi Bank": "1120.SR",
        "Saudi Aramco": "2222.SR",
        "SNB (Al Ahli)": "1180.SR",
        "Tasnee": "2130.SR",
        "TASI Index": "^TASI.SR"
    }

    selected_asset_name = st.selectbox("Select Asset:", list(assets.keys()))
    ticker_symbol = assets[selected_asset_name]

    timeframe_options = {
        "Daily": {"interval": "1d", "period": "1y"},
        "Weekly": {"interval": "1wk", "period": "3y"},
        "Monthly": {"interval": "1mo", "period": "5y"},
        "Yearly": {"interval": "1mo", "period": "max"}
    }

    selected_tf_name = st.selectbox("Select Timeframe:", list(timeframe_options.keys()))
    tf_config = timeframe_options[selected_tf_name]

    run_btn = st.button("Run Technical & News Radar & Log Data")

if run_btn:
    with st.spinner("Processing market data..." if lang == "English" else "جاري معالجة بيانات السوق وتسجيلها في السجل البحثي..."):
        try:
            stock_obj = yf.Ticker(ticker_symbol)
            df = stock_obj.history(period=tf_config["period"], interval=tf_config["interval"])
            
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
                
                if lang == "العربية":
                    trend_status = "مسار صاعد (Bullish Trend)" if is_bullish else "مسار هابط / تصحيحي (Bearish/Correction)"
                else:
                    trend_status = "Bullish Trend" if is_bullish else "Bearish / Correction Trend"
                    
                status_color = "green" if is_bullish else "orange"
                dot_icon = "🟢" if is_bullish else "🔴"
                
                sl = close_price - (1.5 * atr) if is_bullish else close_price + (1.5 * atr)
                risk_distance = abs(close_price - sl)
                
                t1 = close_price + (1.0 * risk_distance) if is_bullish else close_price - (1.0 * risk_distance)
                t2 = close_price + (2.0 * risk_distance) if is_bullish else close_price - (2.0 * risk_distance)
                t3 = close_price + (3.0 * risk_distance) if is_bullish else close_price - (3.0 * risk_distance)
                t4 = close_price + (4.0 * risk_distance) if is_bullish else close_price - (4.0 * risk_distance)

                # حفظ السجل تلقائياً في قاعدة البيانات
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_to_research_log(current_date, selected_asset_name, selected_tf_name, close_price, sl, t1, t4, trend_status)

                st.markdown(f"### {selected_asset_name} [{selected_tf_name}] | <span style='color:{status_color};'>{trend_status}</span>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='text-align: center;'>{dot_icon}</h1>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                if lang == "العربية":
                    col1.metric("السعر الحالي (EP)", f"{close_price:.2f} ر.س")
                    col2.metric("مستوى الارتكاز / وقف الفاعلية (SL)", f"{sl:.2f} ر.س")
                    st.markdown("---")
                    st.markdown("#### الأهداف السعرية الديناميكية:")
                    st.info(f"Target 1 (1x Risk): **{t1:.2f} ر.س**")
                    st.success(f"Target 2 (2x Risk): **{t2:.2f} ر.س**")
                    st.warning(f"Target 3 (3x Risk): **{t3:.2f} ر.س**")
                    st.error(f"Target 4 (4x Risk): **{t4:.2f} ر.س**")
                else:
                    col1.metric("Current Price (EP)", f"{close_price:.2f} SAR")
                    col2.metric("Support / Invalidation (SL)", f"{sl:.2f} SAR")
                    st.markdown("---")
                    st.markdown("#### Dynamic Price Targets:")
                    st.info(f"Target 1 (1x Risk): **{t1:.2f} SAR**")
                    st.success(f"Target 2 (2x Risk): **{t2:.2f} SAR**")
                    st.warning(f"Target 3 (3x Risk): **{t3:.2f} SAR**")
                    st.error(f"Target 4 (4x Risk): **{t4:.2f} SAR**")

                # قسم الأخبار مع معالجة الروابط الآمنة
                st.markdown("---")
                if lang == "العربية":
                    st.markdown("#### 📰 رادار الأخبار الحية وتحليل التأثير:")
                else:
                    st.markdown("#### 📰 Live News Radar & Impact Analysis:")
                
                news_list = stock_obj.news
                if news_list:
                    for item in news_list[:3]:
                        title = item.get('title', 'Corporate News Update')
                        publisher = item.get('publisher', 'Financial Wire')
                        link = item.get('link', '')
                        
                        if not link or not link.startswith("http"):
                            query_str = urllib.parse.quote(f"{selected_asset_name} {title}")
                            link = f"https://www.google.com/search?q={query_str}"
                            publisher_display = f"{publisher} (بحث Google)" if lang == "العربية" else f"{publisher} (Google Search)"
                        else:
                            publisher_display = publisher

                        st.markdown(f"**📌 {title}**")
                        if lang == "العربية":
                            st.caption("🔍 **تحليل التأثير على السهم:** يعكس هذا الخبر تدفقات السيولة المؤسسية ويساهم في توجيه نطاق التذبذب (`ATR`). *(تحليل بحثي غير معتمد)*.")
                            btn_label = f"🔗 فتح المصدر: {publisher_display}"
                        else:
                            st.caption("🔍 **Impact Analysis:** Reflects institutional liquidity and directs volatility (`ATR`). *(Unverified research analysis)*.")
                            btn_label = f"🔗 Open Source: {publisher_display}"
                        
                        st.link_button(btn_label, link)
                        st.markdown("---")
                else:
                    if lang == "العربية":
                        st.info("لا توجد أخبار مسجلة حالياً لهذا السهم.")
                    else:
                        st.info("No current news registered for this asset.")

        except Exception as e:
            if lang == "العربية":
                st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
            else:
                st.error(f"An error occurred while processing data: {e}")

# --- قسم استعراض سجل الأبحاث المحفوظ تلقائياً ---
st.markdown("---")
if lang == "العربية":
    with st.expander("📊 سجل الأبحاث والبيانات المرصودة (Research Log)"):
        try:
            conn = sqlite3.connect('s2pro_research.db')
            log_df = pd.read_sql_query("SELECT * FROM tracking_log ORDER BY id DESC", conn)
            conn.close()
            if not log_df.empty:
                st.dataframe(log_df)
                csv_data = log_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 تحميل السجل البحثي بصيغة CSV للتحليل", csv_data, "s2pro_research_log.csv", "text/csv")
            else:
                st.info("لا توجد بيانات مسجلة حتى الآن. قم بتشغيل التحليل لتسجيل النقطة الأولى.")
        except Exception as db_err:
            st.error(f"تعذر استعراض السجل: {db_err}")
else:
    with st.expander("📊 Research Log & Tracked Data Matrix"):
        try:
            conn = sqlite3.connect('s2pro_research.db')
            log_df = pd.read_sql_query("SELECT * FROM tracking_log ORDER BY id DESC", conn)
            conn.close()
            if not log_df.empty:
                st.dataframe(log_df)
                csv_data = log_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Research Log as CSV", csv_data, "s2pro_research_log.csv", "text/csv")
            else:
                st.info("No data logged yet. Run the analysis to record the first entry.")
        except Exception as db_err:
            st.error(f"Could not load log: {db_err}")
