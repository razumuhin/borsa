import tkinter as tk
from tkinter import messagebox
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime


from veri_cekici import kurum_alim_satim_verisi 


def teknik_analiz(df):
    df = df.copy()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    return df

def analiz_et():
    hisse_kodu = entry.get().strip().upper()
    if not hisse_kodu:
        messagebox.showwarning("Uyarı", "Lütfen bir hisse kodu girin.")
        return

    try:
        hisse = yf.Ticker(f"{hisse_kodu}.IS")
        df = hisse.history(period="3mo")

        if df.empty:
            raise ValueError("Veri alınamadı.")

        df = teknik_analiz(df)
        son = df.iloc[-1]

        analiz = f"""
📈 {hisse_kodu}.IS Analizi - {datetime.now().date()}

🔹 Son Kapanış: {son['Close']:.2f} TL
🔹 Ortalama: {df['Close'].mean():.2f} TL
🔹 En Yüksek: {df['Close'].max():.2f} TL
🔹 En Düşük: {df['Close'].min():.2f} TL

📊 Teknik Göstergeler:
- RSI: {son['RSI']:.2f} {"(Aşırı Alım)" if son['RSI'] > 70 else "(Aşırı Satım)" if son['RSI'] < 30 else ""}
- MACD: {son['MACD']:.2f}
- MACD Sinyal: {son['MACD_signal']:.2f}
- Yorum: {"Al sinyali" if son['MACD'] > son['MACD_signal'] else "Sat sinyali"}
"""
        text_output.delete(1.0, tk.END)
        text_output.insert(tk.END, analiz)

    except Exception as e:
        messagebox.showerror("Hata", f"Hisse verisi alınamadı.\n{str(e)}")

# Arayüz Başlangıç
root = tk.Tk()
root.title("BIST Teknik Analiz")

root.geometry("600x450")
root.resizable(False, False)

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

label = tk.Label(frame, text="Hisse Kodu:")
label.grid(row=0, column=0, sticky="w")

entry = tk.Entry(frame, width=20)
entry.grid(row=0, column=1)

button = tk.Button(frame, text="Analiz Et", command=analiz_et)
button.grid(row=0, column=2, padx=5)

text_output = tk.Text(root, height=20, width=70)
text_output.pack(padx=10, pady=10)

root.mainloop()
