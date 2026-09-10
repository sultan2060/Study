import os
from datetime import datetime
import pandas as pd
import yfinance as yf

REGISTER_FILE = 'research_register.csv'


def init_register():
  if not os.path.exists(REGISTER_FILE):
    initial_data = [
        {
            'ID': 1,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Asset': 'سابك (SABIC)',
            'Ticker': '2010.SR',
            'Timeframe': 'يومي (Daily)',
            'Entry (EP)': 49.48,
            'Live Price': 49.48,
            'Target 1 (T1)': 50.73,
            'Target 2 (T2)': 51.98,
            'Target 3 (T3)': 53.23,
            'Target 4 (T4)': 55.00,
            'Stop Loss (SL)': 48.23,
            'Status': 'قيد المراقبة (Active)',
        },
        {
            'ID': 2,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Asset': 'مصرف الراجحي (Al Rajhi)',
            'Ticker': '1120.SR',
            'Timeframe': 'أسبوعي (Weekly)',
            'Entry (EP)': 66.10,
            'Live Price': 66.10,
            'Target 1 (T1)': 67.58,
            'Target 2 (T2)': 69.06,
            'Target 3 (T3)': 70.54,
            'Target 4 (T4)': 72.50,
            'Stop Loss (SL)': 64.62,
            'Status': 'قيد المراقبة (Active)',
        },
        {
            'ID': 3,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Asset': 'مؤشر تاسي (TASI)',
            'Ticker': '^TASI.SR',
            'Timeframe': 'أسبوعي (Weekly)',
            'Entry (EP)': 10720.28,
            'Live Price': 10720.28,
            'Target 1 (T1)': 10621.0,
            'Target 2 (T2)': 10521.72,
            'Target 3 (T3)': 10422.44,
            'Target 4 (T4)': 10250.0,
            'Stop Loss (SL)': 10819.56,
            'Status': 'قيد المراقبة (Active)',
        },
    ]
    df = pd.DataFrame(initial_data)
    df.to_csv(REGISTER_FILE, index=False)


def run_automated_tracking():
  init_register()
  df = pd.read_csv(REGISTER_FILE)
  if df.empty:
    return

  for idx, row in df.iterrows():
    ticker = str(row['Ticker'])
    try:
      stock = yf.Ticker(ticker)
      hist = stock.history(period='1d')
      if not hist.empty:
        curr_p = float(hist['Close'].iloc[-1])
        df.at[idx, 'Live Price'] = round(curr_p, 2)

        t1 = float(row['Target 1 (T1)'])
        sl = float(row['Stop Loss (SL)'])

        # تقييم ذكي للمسار الصاعد أو الهابط
        if 'تاسي' in str(row['Asset']) or 'TASI' in str(row['Asset']):
          if curr_p <= t1:
            df.at[idx, 'Status'] = '✅ نجح هبوطياً (Target Hit)'
          elif curr_p >= sl:
            df.at[idx, 'Status'] = '❌ فشل (Stopped Out)'
          else:
            df.at[idx, 'Status'] = '⏳ قيد المراقبة (Active)'
        else:
          if curr_p >= t1:
            df.at[idx, 'Status'] = '✅ نجح (Target Hit)'
          elif curr_p <= sl:
            df.at[idx, 'Status'] = '❌ فشل (Stopped Out)'
          else:
            df.at[idx, 'Status'] = '⏳ قيد المراقبة (Active)'
    except Exception as e:
      print(f'Error tracking {ticker}: {e}')

  df.to_csv(REGISTER_FILE, index=False)


if __name__ == '__main__':
  run_automated_tracking()
