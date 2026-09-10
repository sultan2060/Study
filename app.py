import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

st.set_page_config(page_title="S2 Pro - Research & Analysis Matrix", layout="centered")

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
    <b>⚠️ إخلاء مسؤولية بحثية:</b> النظام مخصص لأغراض الدراسة الأكاديمية والبحث المالي ونمذجة الأسواق.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - Research & Analysis Matrix")
    st.markdown("منظومة التحليل الفني والبحث والرصد الأكاديمي للسوق السعودي")
else:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F;">
    <b>⚠️ Academic Disclaimer:</b> Research and technical analysis matrix for market modeling.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - Research & Analysis Matrix")
    st.markdown("Technical Analysis, Market Research & Automated Tracking Matrix")

st.markdown("---")

# القائمة الأساسية للأصول
assets_dict = {
    "سابك (SABIC)": "2010.SR",
    "مصرف الراجحي": "1120.SR",
    "أرامكو السعودية": "2222.SR",
    "الأهلي السعودي": "1180.SR",
    "التصنيع الوطنية": "2130.SR",
    "مؤشر تاسي (TASI)": "^TASI.SR"
}

selected_asset_name = st.sidebar.selectbox("اختر الأصل للتحليل والدراسة" if lang == "العربية" else "Select Asset for Analysis", list(assets_dict.keys()))
selected_ticker = assets_dict[selected_asset_name]
timeframe_option = st.sidebar.selectbox("الإطار الزمني للدراسة" if lang == "العربية" else "Study Timeframe", ["يومي (Daily)", "أسبوعي (Weekly)"])

# زر لتنفيذ الدراسة والتحليل وإضافتها للسجل
run_analysis_btn = st.sidebar.button("🔬 تنفيذ التحليل وإضافته لسجل البحث")

if run_analysis_btn:
    with st.spinner("جاري جلب بيانات السوق وتحليل المؤشرات..." if lang == "العربية" else "Analyzing market data..."):
        try:
            stock_obj = yf.Ticker(selected_ticker)
            df = stock_obj.history(period="1y", interval="1d" if "يومي" in timeframe_option else "1wk")
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

                conn = sqlite3.connect('s2pro_research_master.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO master_study_log (study_date, asset_name, ticker, timeframe, logged_ep, invalidation_sl, target_t1, target_t4, trend_condition, current_market_price, evaluation_result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (current_date_full, selected_asset_name, selected_ticker, timeframe_option, close_price, sl, t1, t4, trend_status, close_price, eval_status))
                conn.commit()
                conn.close()
                st.sidebar.success("تم تحليل وحفظ نقطة الرصد في السجل بنجاح!")
        except Exception as e:
            st.sidebar.error(f"خطأ في التحليل: {e}")

# قسم عرض التحليل الفني المباشر للأصل المختاره
if lang == "العربية":
    st.subheader(f"📊 لوحة التحليل الفني والدراسة: {selected_asset_name}")
else:
    st.subheader(f"📊 Technical Analysis & Study Panel: {selected_asset_name}")

try:
    live_stock = yf.Ticker(selected_ticker)
    live_df = live_stock.history(period="6mo")
    if not live_df.empty:
        current_p = float(live_df['Close'].iloc[-1])
        prev_p = float(live_df['Close'].iloc[-2])
        change_pct = ((current_p - prev_p) / prev_p) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("السعر الحقيقي اللحظي", f"{current_p:.2f} SAR", f"{change_pct:+.2f}%")
        col2.metric("أعلى سعر للفترة", f"{live_df['High'].max():.2f} SAR")
        col3.metric("أدنى سعر للفترة", f"{live_df['Low'].min():.2f} SAR")

        st.line_chart(live_df['Close'])
        
        # قسم الأخبار الخاصة بالأصل إن وجدت
        st.markdown("### 📰 آخر الأخبار والتحديثات المرتبطة")
        news_list = live_stock.news
        if news_list:
            for n in news_list[:3]:
                title = n.get('title', 'No Title')
                publisher = n.get('publisher', 'Financial Source')
                link = n.get('link', '#')
                st.markdown(f"- **[{title}]({link})** — *{publisher}*")
        else:
            st.info("لا توجد أخبار حديثة متاحة حالياً لهذا الأصل.")
except Exception as ex:
    st.warning("تعذر جلب الرسم البياني الحي حالياً.")

st.markdown("---")

# زر مزامنة الرصد الآلي الشامل لجميع الأصول دفعة واحدة
if st.button("🔄 تشغيل ومزامنة الرصد الآلي الشامل لجميع الأصول" if lang == "العربية" else "🔄 Run Full Automated Scan"):
    with st.spinner("جاري مسح جميع الأصول وتحديث السجل..." if lang == "العربية" else "Scanning all assets..."):
        conn = sqlite3.connect('s2pro_research_master.db')
        cursor = conn.cursor()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
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
                except:
                    pass
        conn.close()
    st.success("تمت المزامنة والرصد الشامل بنجاح!")

st.markdown("---")

# عرض السجل الأكاديمي للبحث والدراسة
if lang == "العربية":
    st.markdown("### 📚 السجل الأكاديمي للبحث والدراسة (Master Study Register)")
    st.caption("يوثق نقاط الرصد والتحليل، ويقدم التمييز الدقيق بين (سعر الرصد الثابت EP) و(السعر الحقيقي اللحظي للسوق).")
else:
    st.markdown("### 📚 Master Academic Study Register")
    st.caption("Documents study points distinguishing between Logged Entry Price (EP) and Live Market Price.")

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
                curr_price = float(hist_df['Close'].iloc[-1]) if not hist_df.empty else logged_ep
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
        st.info("السجل فارغ. استخدم القائمة الجانبية لتنفيذ التحليل أو زر المزامنة بالأعلى." if lang == "العربية" else "Register is empty.")

except Exception as db_err:
    st.error(f"Error: {db_err}")
