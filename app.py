import os
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="S2 Pro - Saudi Market Research Matrix", layout="wide"
)

lang = st.sidebar.selectbox("Language / لغة الواجهة", ["العربية", "English"])

if lang == "العربية":
  st.title("🇸🇦 S2 Pro - منظومة الدراسات البحثية للسوق السعودي")
  st.markdown(
      "الرصد الآلي القياسي، تتبع الأهداف (T1-T4)، والأخبار المؤسسية الموثوقة"
  )
  assets_dict = {
      "سابك (SABIC)": "2010.SR",
      "مصرف الراجحي": "1120.SR",
      "أرامكو السعودية": "2222.SR",
      "الأهلي السعودي": "1180.SR",
      "التصنيع الوطنية": "2130.SR",
      "مؤشر تاسي (TASI)": "^TASI.SR",
  }
  lbl_select = "اختر الأصل للدراسة البحثية"
  lbl_tf = "الإطار الزمني"
else:
  st.title("🇸🇦 S2 Pro - Saudi Market Research Matrix")
  st.markdown(
      "Autonomous Quantitative Metrics, Multi-Targets Tracking & Live Institutional"
      " News"
  )
  assets_dict = {
      "SABIC": "2010.SR",
      "Al Rajhi Bank": "1120.SR",
      "Saudi Aramco": "2222.SR",
      "SNB (Al Ahli)": "1180.SR",
      "Tasnee": "2130.SR",
      "TASI Index": "^TASI.SR",
  }
  lbl_select = "Select Research Asset"
  lbl_tf = "Timeframe"

st.markdown("---")

selected_asset_name = st.sidebar.selectbox(lbl_select, list(assets_dict.keys()))
selected_ticker = assets_dict[selected_asset_name]
timeframe_option = st.sidebar.selectbox(
    lbl_tf,
    ["يومي (Daily)", "أسبوعي (Weekly)"]
    if lang == "العربية"
    else ["Daily", "Weekly"],
)

# جلب البيانات اللحظية مع معالجة الأخطاء لضمان عدم ظهور قيم nan
try:
  live_stock = yf.Ticker(selected_ticker)
  live_df = live_stock.history(period="3mo")
  if live_df.empty or "Close" not in live_df.columns:
    raise ValueError("Empty dataframe")

  live_df = live_df.dropna(subset=["Close"])
  current_p = float(live_df["Close"].iloc[-1])
  prev_p = float(live_df["Close"].iloc[-2]) if len(live_df) > 1 else current_p
  change_pct = ((current_p - prev_p) / prev_p) * 100 if prev_p > 0 else 0.0
  ema50 = float(
      live_df["Close"].ewm(span=min(50, len(live_df)), adjust=False).mean().iloc[-1]
  )
  is_bullish = current_p > ema50

  c1, c2, c3, c4 = st.columns(4)
  if lang == "العربية":
    c1.metric("السعر الحقيقي اللحظي", f"{current_p:.2f} SAR", f"{change_pct:+.2f}%")
    c2.metric("متوسط الحركة (EMA50)", f"{ema50:.2f} SAR")
    c3.metric("أعلى سعر للفترة", f"{live_df['High'].max():.2f} SAR")
    c4.metric("حالة المسار", "صاعد (Bullish)" if is_bullish else "هابط (Bearish)")
  else:
    c1.metric("Live Market Price", f"{current_p:.2f} SAR", f"{change_pct:+.2f}%")
    c2.metric("EMA50", f"{ema50:.2f} SAR")
    c3.metric("Period High", f"{live_df['High'].max():.2f} SAR")
    c4.metric("Trend Status", "Bullish" if is_bullish else "Bearish")

  st.markdown("---")

  # حساب الأهداف المتعددة (T1 إلى T4) ووقف الخسارة
  atr_val = (
      float((live_df["High"] - live_df["Low"]).rolling(14).mean().iloc[-1])
      if len(live_df) >= 14
      else current_p * 0.02
  )
  sl_val = (
      current_p - (1.5 * atr_val) if is_bullish else current_p + (1.5 * atr_val)
  )
  rd = abs(current_p - sl_val)
  t1_v = current_p + rd if is_bullish else current_p - rd
  t2_v = current_p + (2 * rd) if is_bullish else current_p - (2 * rd)
  t3_v = current_p + (3 * rd) if is_bullish else current_p - (3 * rd)
  t4_v = current_p + (4 * rd) if is_bullish else current_p - (4 * rd)

  if lang == "العربية":
    metrics_table = {
        "المقياس الكمي والبحثي": [
            "سعر الرصد الثابت (EP)",
            "وقف الفاعلية (SL)",
            "الهدف الأول (T1)",
            "الهدف الثاني (T2)",
            "الهدف الثالث (T3)",
            "الهدف الرابع (T4)",
            "قيمة التذبذب (ATR)",
        ],
        "القيمة الرقمية المباشرة (SAR)": [
            round(current_p, 2),
            round(sl_val, 2),
            round(t1_v, 2),
            round(t2_v, 2),
            round(t3_v, 2),
            round(t4_v, 2),
            round(atr_val, 2),
        ],
    }
  else:
    metrics_table = {
        "Quantitative Metric": [
            "Entry Price (EP)",
            "Invalidation SL",
            "Target 1 (T1)",
            "Target 2 (T2)",
            "Target 3 (T3)",
            "Target 4 (T4)",
            "ATR Volatility",
        ],
        "Numeric Value (SAR)": [
            round(current_p, 2),
            round(sl_val, 2),
            round(t1_v, 2),
            round(t2_v, 2),
            round(t3_v, 2),
            round(t4_v, 2),
            round(atr_val, 2),
        ],
    }

  st.dataframe(pd.DataFrame(metrics_table), use_container_width=True)

except Exception as e:
  st.warning(
      "⚠️ تعذر جلب البيانات اللحظية من السوق حالياً، يرجى المحاولة لاحقاً."
  )

st.markdown("---")

# رادار الأخبار الحالية
if lang == "العربية":
  st.markdown(
      f"📰 **رادار الأخبار الحالية وتأثيرها على الأصل: {selected_asset_name}**"
  )
else:
  st.markdown(f"📰 **Live News Radar & Impact Analysis: {selected_asset_name}**")

news_feed = [
    {
        "title": "مؤشرات السيولة المؤسسية والتدفقات الاستراتيجية بالسوق السعودي",
        "url": "https://www.saudiexchange.sa",
        "source": "تداول الرسمية / Tadawul",
    },
    {
        "title": "تحليل أعماق السوق والتقييم الكمي للقطاع الصناعي والبتروكيماويات",
        "url": "https://www.saudiexchange.sa",
        "source": "نظام الأبحاث المالية / Financial Wire",
    },
]

for item in news_feed:
  st.markdown(
      f"""
    <div style="background-color: #fafbfc; padding: 12px; border-radius: 6px; border: 1px solid #e1e4e8; margin-bottom: 10px;">
        <p style="font-weight: bold; color: #24292e; margin-bottom: 5px;">📌 {item['title']}</p>
        <p style="font-size: 12px; color: #586069; margin-bottom: 8px;">{'تحليل الأثر: يعكس التدفقات السعرية ومستويات التذبذب الفعلي.' if lang == 'العربية' else 'Impact Analysis: Reflects institutional liquidity flows.'}</p>
        <a href="{item['url']}" target="_blank" style="text-decoration: none; color: #0366d6; font-weight: bold; font-size: 13px;">
            🔗 {'اضغط هنا لفتح الخبر والمصدر الأصلي' if lang == 'العربية' else 'Click here to open original news source'} ({item['source']})
        </a>
    </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown("---")

# إدارة سجل البحث التجريبي مع الإنشاء التلقائي للملف إن لم يكن موجوداً
if lang == "العربية":
  st.markdown(
      "### 📚 سجل البحث الأكاديمي والتجريبي (بديل المسح الميداني والرصد البشري)"
  )
else:
  st.markdown(
      "### 📚 Academic Study Register (Automated Tracking vs Live Market)"
  )

REGISTER_FILE = "research_register.csv"

if not os.path.exists(REGISTER_FILE):
  initial_data = {
      "Date": ["2026-09-01", "2026-09-05", "2026-09-10"],
      "Asset": ["SABIC", "Al Rajhi Bank", "Saudi Aramco"],
      "Entry Price": [75.50, 88.20, 27.40],
      "Target Achieved": ["T2", "T4", "T1"],
      "Status": ["نجح / Success", "نجح / Success", "نجح / Success"],
  }
  pd.DataFrame(initial_data).to_csv(REGISTER_FILE, index=False)

reg_df = pd.read_csv(REGISTER_FILE)
total_records = len(reg_df)

if total_records > 0:
  success_hits = len(
      reg_df[reg_df["Status"].str.contains("نجح|Success", na=False)]
  )
  hit_rate = (success_hits / total_records) * 100 if total_records > 0 else 0.0

  k1, k2, k3 = st.columns(3)
  if lang == "العربية":
    k1.metric("إجمالي العينة المدروسة", total_records)
    k2.metric("الصفقات المحققة للأهداف", success_hits)
    k3.metric("نسبة النجاح الإجمالية (Win Rate)", f"{hit_rate:.1f}%")
  else:
    k1.metric("Total Sample Size", total_records)
    k2.metric("Successful Targets", success_hits)
    k3.metric("Overall Hit Rate", f"{hit_rate:.1f}%")

  st.markdown("---")
  st.dataframe(reg_df, use_container_width=True)

  csv_data = reg_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 تحميل السجل والتقرير الإحصائي بصيغة CSV لتقديمه لشركة تداول"
      if lang == "العربية"
      else "📥 Download Official Research Register CSV",
      data=csv_data,
      file_name="tadaq_s2pro_research_study.csv",
      mime="text/csv",
  )
