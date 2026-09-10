 import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import urllib.parse
import sqlite3
from datetime import datetime

st.set_page_config(page_title="S2 Pro - TASI Research Matrix", layout="centered")

# --- تهيئة قاعدة البيانات التراكمية لسجلات الدراسات والأبحاث ---
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

def save_to_master_log(date, asset, ticker, tf, ep, sl, t1, t4, trend, current_p, eval_res):
    conn = sqlite3.connect('s2pro_research_master.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO master_study_log (study_date, asset_name, ticker, timeframe, logged_ep, invalidation_sl, target_t1, target_t4, trend_condition, current_market_price, evaluation_result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, asset, ticker, tf, ep, sl, t1, t4, trend, current_p, eval_res))
    conn.commit()
    conn.close()

# واجهة المستخدم اللغوية
lang = st.sidebar.selectbox("Language / لغة الواجهة", ["العربية", "English"])

if lang == "العربية":
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F; margin-bottom: 15px; text-align: right;" dir="rtl">
    <b>⚠️ إخلاء مسؤولية بحثية:</b> النظام مخصص لأغراض الدراسة الأكاديمية ونمذجة الأسواق المالية ولا يعد استشارة استثمارية.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - Academic Study Log")
    st.markdown("منظومة الرصد والتسجيل التراكمي المعتمد للورقة البحثية (TASI Market Matrix)")

    assets = {
        "سابك (SABIC)": "2010.SR",
        "مصرف الراجحي": "1120.SR",
        "أرامكو السعودية": "2222.SR",
        "الأهلي السعودي": "1180.SR",
        "التصنيع الوطنية": "2130.SR",
        "مؤشر تاسي (TASI)": "^TASI.SR"
    }

    selected_asset_name = st.selectbox("اختر الأصل أو السهم للدراسة:", list(assets.keys()))
    ticker_symbol = assets[selected_asset_name]

    timeframe_options = {
        "يومي (Daily)": {"interval": "1d", "period": "1y"},
        "أسبوعي (Weekly)": {"interval": "1wk", "period": "3y"},
        "شهري (Monthly)": {"interval": "1mo", "period": "5y"},
        "سنوي (Yearly)": {"interval": "1mo", "period": "max"}
    }

    selected_tf_name = st.selectbox("اختر الإطار الزمني للدراسة:", list(timeframe_options.keys()))
    tf_config = timeframe_options[selected_tf_name]

    run_btn = st.button("تنفيذ التحليل وحفظ نقطة الرصد في السجل البحثي")
    
else:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0; font-size: 12px; color: #31333F; margin-bottom: 15px;">
    <b>⚠️ Academic Disclaimer:</b> For academic research and modeling purposes only.
    </div>
    """, unsafe_allow_html=True)

    st.title("🇸🇦 S2 Pro - Academic Study Log")
    st.markdown("Master Research Log & Quantitative Evaluation Matrix for TASI")

    assets = {
        "SABIC": "2010.SR",
        "Al Rajhi Bank": "1120.SR",
        "Saudi Aramco": "2222.SR",
        "SNB (Al Ahli)": "1180.SR",
        "Tasnee": "2130.SR",
        "TASI Index": "^TASI.SR"
    }

    selected_asset_name = st.selectbox("Select Asset for Study:", list(assets.keys()))
    ticker_symbol = assets[selected_asset_name]

    timeframe_options = {
        "Daily": {"interval": "1d", "period": "1y"},
        "Weekly": {"interval": "1wk", "period": "3y"},
        "Monthly": {"interval": "1mo", "period": "5y"},
        "Yearly": {"interval": "1mo", "period": "max"}
    }

    selected_tf_name = st.selectbox("Select Timeframe:", list(timeframe_options.keys()))
    tf_config = timeframe_options[selected_tf_name]

    run_btn = st.button("Run Analysis & Record in Master Study Log")

if run_btn:
    with st.spinner("Processing analytical matrix..." if lang == "English" else "جاري استخراج المعطيات الرياضية وحفظها في السجل الأكاديمي..."):
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
                    trend_status = "مسار صاعد (Bullish)" if is_bullish else "مسار هابط (Bearish)"
                else:
                    trend_status = "Bullish" if is_bullish else "Bearish"
                    
                status_color = "green" if is_bullish else "orange"
                dot_icon = "🟢" if is_bullish else "🔴"
                
                sl = close_price - (1.5 * atr) if is_bullish else close_price + (1.5 * atr)
                risk_distance = abs(close_price - sl)
                
                t1 = close_price + (1.0 * risk_distance) if is_bullish else close_price - (1.0 * risk_distance)
                t4 = close_price + (4.0 * risk_distance) if is_bullish else close_price - (4.0 * risk_distance)

                # تحديد حالة التقييم المبدئي الحالية للمقارنة
                if is_bullish:
                    eval_status = "قيد التتبع الميداني (Pending)"
                else:
                    eval_status = "قيد التتبع الميداني (Pending)"

                # تسجيل المعطيات في السجل التراكمي الرئيسي
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_to_master_log(current_date, selected_asset_name, ticker_symbol, selected_tf_name, close_price, sl, t1, t4, trend_status, close_price, eval_status)

                st.markdown(f"### {selected_asset_name} [{selected_tf_name}] | <span style='color:{status_color};'>{trend_status}</span>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='text-align: center;'>{dot_icon}</h1>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                if lang == "العربية":
                    col1.metric("سعر الرصد الأساسي (EP)", f"{close_price:.2f} ر.س")
                    col2.metric("وقف الفاعلية الهيكلي (SL)", f"{sl:.2f} ر.س")
                    st.markdown("---")
                    st.markdown("#### المستهدفات المعيارية للورقة البحثية:")
                    st.info(f"Target 1 (1x Risk): **{t1:.2f} ر.س**")
                    st.error(f"Target 4 (4x Risk): **{t4:.2f} ر.س**")
                else:
                    col1.metric("Logged Entry Price (EP)", f"{close_price:.2f} SAR")
                    col2.metric("Structural SL", f"{sl:.2f} SAR")
                    st.markdown("---")
                    st.markdown("#### Research Benchmark Targets:")
                    st.info(f"Target 1 (1x Risk): **{t1:.2f} SAR**")
                    st.error(f"Target 4 (4x Risk): **{t4:.2f} SAR**")

                st.success("✅ تم توثيق وحفظ نقطة الرصد بنجاح في السجل التراكمي المعتمد للأبحاث." if lang == "العربية" else "✅ Successfully recorded in the Master Academic Study Log.")

        except Exception as e:
            st.error(f"Error: {e}")

# --- قسم استعراض سجل الأبحاث الرئيسي وتصدير الجداول العلمية ---
st.markdown("---")
if lang == "العربية":
    st.markdown("### 📚 السجل التراكمي المعتمد للأبحاث (Master Study Register)")
    st.caption("هذا السجل يوثق كافة النقاط التي تم رصدها عبر الجلسات الزمنية المختلفة، ويقوم بمقارنتها بالسعر الحقيقي للسوق لقياس كفاءة النموذج بدقة.")
else:
    st.markdown("### 📚 Master Academic Study Register")
    st.caption("This register tracks all logged points across temporalframes and evaluates them against real-time market prices.")

try:
    conn = sqlite3.connect('s2pro_research_master.db')
    master_df = pd.read_sql_query("SELECT * FROM master_study_log ORDER BY id DESC", conn)
    conn.close()

    if not master_df.empty:
        # تحديث الأسعار الحالية وتقييم النجاح والخطأ لكل صف في السجل التراكمي
        updated_rows = []
        success_tally = 0
        failure_tally = 0

        for idx, row in master_df.iterrows():
            ticker = row['ticker']
            logged_ep = row['logged_ep']
            sl = row['invalidation_sl']
            t1 = row['target_t1']
            trend = row['trend_condition']

            # جلب السعر الحقيقي الآن للسوق
            try:
                live_obj = yf.Ticker(ticker)
                hist_df = live_obj.history(period="1d")
                curr_price = float(hist_df['Close'].iloc[-1]) if not hist_df.empty else logged_ep
            except:
                curr_price = logged_ep

            # مقارنة علمية رياضية لتحديد الحالة
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
                "سعر الرصد (EP)": round(logged_ep, 2),
                "السعر الحقيقي اللحظي": round(curr_price, 2),
                "الهدف المعياري (T1)": round(t1, 2),
                "وقف الفاعلية (SL)": round(sl, 2),
                "حالة التقييم الأكاديمي": eval_res
            })

        display_df = pd.DataFrame(updated_rows)
        
        # مؤشرات الأداء الإحصائي للبحث
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
        st.dataframe(display_df, use_container_width=True)

        # زر التحميل المعتمد للإرفاق في الورقة البحثية
        export_csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 تحميل السجل التراكمي المعتمد بصيغة CSV لإرفاقه بالبحث الأكاديمي" if lang == "العربية" else "📥 Download Master Academic Log CSV",
            data=export_csv,
            file_name="s2pro_master_study_register.csv",
            mime="text/csv"
        )
    else:
        st.info("السجل فارغ حالياً. قم بالنقر على زر التشغيل بالأعلى لتسجيل أول نقطة بحثية في قاعدة السجلات." if lang == "العربية" else "Master log is empty. Run an analysis above to record the first point.")

except Exception as db_err:
    st.error(f"Error in master database register: {db_err}")
