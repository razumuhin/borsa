import tkinter as tk
from tkinter import messagebox, ttk
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from veri_cekici import kurum_alim_satim_verisi, format_kurum_verisi

# Stil sabitleri
BG_COLOR = "#f0f2f5"
TEXT_COLOR = "#333333"
BUTTON_COLOR = "#4a6fa5"
FONT = ("Segoe UI", 10)

def teknik_analiz(df):
    """Geliştirilmiş teknik analiz fonksiyonu"""
    try:
        df = df.copy()
        # Momentum göstergeleri
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df['Stoch_%K'] = ta.momentum.StochasticOscillator(
            df['High'], df['Low'], df['Close'], window=14).stoch()
        
        # Trend göstergeleri
        macd = ta.trend.MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['EMA_20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
        df['SMA_50'] = ta.trend.SMAIndicator(df['Close'], window=50).sma_indicator()
        
        # Volatilite göstergeleri
        bollinger = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_upper'] = bollinger.bollinger_hband()
        df['BB_middle'] = bollinger.bollinger_mavg()
        df['BB_lower'] = bollinger.bollinger_lband()
        
        return df
    except Exception as e:
        print(f"Teknik analiz hatası: {e}")
        return None

def temel_analiz(hisse_kodu):
    """Temel analiz verilerini çeker"""
    try:
        hisse = yf.Ticker(f"{hisse_kodu}.IS")
        info = hisse.info
        
        # Market cap kontrolü
        market_cap = info.get('marketCap')
        market_cap_str = f"{market_cap/1000000:,.2f} M TL" if market_cap else 'N/A'
        
        # Temettü verimi kontrolü
        dividend_yield = info.get('dividendYield')
        dividend_str = f"{dividend_yield*100:.2f}%" if dividend_yield else 'N/A'
        
        # Kar marjı kontrolü
        profit_margins = info.get('profitMargins')
        profit_str = f"{profit_margins*100:.2f}%" if profit_margins else 'N/A'
        
        return {
            'Piyasa Değeri': market_cap_str,
            'F/K': info.get('forwardPE', 'N/A'),
            'FD/FAVÖK': info.get('enterpriseToEbitda', 'N/A'),
            'Temettu Verimi': dividend_str,
            'Son Çeyrek Kâr': profit_str
        }
    except Exception as e:
        print(f"Temel analiz hatası: {e}")
        return None

def grafik_goster():
    """Hisse grafiğini gösterir"""
    hisse_kodu = entry.get().strip().upper()
    if not hisse_kodu:
        messagebox.showwarning("Uyarı", "Lütfen bir hisse kodu girin")
        return
        
    try:
        hisse = yf.Ticker(f"{hisse_kodu}.IS")
        df = hisse.history(period="3mo")
        
        if df.empty or len(df) < 5:
            messagebox.showerror("Hata", "Yeterli veri bulunamadı")
            return
            
        df = teknik_analiz(df)
        if df is None:
            messagebox.showerror("Hata", "Teknik analiz yapılamadı")
            return
        
        # Güncel matplotlib stilini kullanma
        plt.style.use('ggplot')  # 'seaborn' yerine alternatif bir stil
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
        fig.patch.set_facecolor(BG_COLOR)
        
        # Fiyat grafiği
        ax1.plot(df.index, df['Close'], label='Kapanış', color='#2e86de', linewidth=2)
        ax1.plot(df.index, df['EMA_20'], label='EMA 20', linestyle='--', color='#ff9f43')
        ax1.plot(df.index, df['SMA_50'], label='SMA 50', linestyle=':', color='#5f27cd')
        ax1.fill_between(df.index, df['BB_upper'], df['BB_lower'], color='#c8d6e5', alpha=0.3)
        ax1.set_title(f'{hisse_kodu} Fiyat Grafiği (3 Ay)', fontsize=12, pad=20)
        ax1.set_ylabel('Fiyat (TL)', fontsize=10)
        ax1.legend(loc='upper left')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # RSI grafiği
        ax2.plot(df.index, df['RSI'], label='RSI 14', color='#10ac84', linewidth=2)
        ax2.axhline(70, color='#ff6b6b', linestyle='--', linewidth=1)
        ax2.axhline(30, color='#1dd1a1', linestyle='--', linewidth=1)
        ax2.set_title('RSI (14)', fontsize=12, pad=20)
        ax2.set_ylabel('RSI', fontsize=10)
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper left')
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        # Grafik penceresi
        grafik_pencere = tk.Toplevel()
        grafik_pencere.title(f"{hisse_kodu} Teknik Grafik")
        grafik_pencere.geometry("900x700")
        
        canvas = FigureCanvasTkAgg(fig, master=grafik_pencere)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        def on_close():
            plt.close(fig)
            grafik_pencere.destroy()
        
        grafik_pencere.protocol("WM_DELETE_WINDOW", on_close)
        
    except Exception as e:
        messagebox.showerror("Hata", f"Grafik oluşturulamadı:\n{str(e)}")

def analiz_et():
    """Geliştirilmiş analiz fonksiyonu"""
    hisse_kodu = entry.get().strip().upper()
    if not hisse_kodu:
        messagebox.showwarning("Uyarı", "Lütfen bir hisse kodu girin (Örnek: THYAO, AKBNK)")
        return

    try:
        # Verileri çek
        hisse = yf.Ticker(f"{hisse_kodu}.IS")
        df = hisse.history(period="3mo")

        if df.empty or len(df) < 10:
            messagebox.showerror("Hata", "Yeterli veri bulunamadı (en az 10 iş günü gereklidir)")
            return

        # Analizleri yap
        df = teknik_analiz(df)
        if df is None:
            messagebox.showerror("Hata", "Teknik analiz yapılamadı")
            return
            
        # Güvenli fiyat hesaplama
        try:
            son_fiyat = df['Close'].iloc[-1]
            onceki_fiyat = df['Close'].iloc[-2]
            daily_change = son_fiyat - onceki_fiyat
            percent_change = (son_fiyat/onceki_fiyat-1)*100
            change_text = f"   • Günlük Değişim: {daily_change:+.2f} TL ({percent_change:+.2f}%)"
        except IndexError:
            change_text = "   • Günlük Değişim: Yeterli veri yok"
        except Exception as e:
            change_text = f"   • Günlük Değişim: Hesaplanamadı"

        son = df.iloc[-1]
        temel = temel_analiz(hisse_kodu)
        kurum_verisi = kurum_alim_satim_verisi(hisse_kodu)
        
        # Analiz raporu oluştur
        analiz = f"""
📈 {hisse_kodu.upper()}.IS ANALİZ RAPORU - {datetime.now().strftime('%d.%m.%Y %H:%M')}
------------------------------------------------------------

🔹 FİYAT BİLGİLERİ:
{change_text}
   • 3 Aylık Ortalama: {df['Close'].mean():.2f} TL
   • 3 Aylık En Yüksek: {df['Close'].max():.2f} TL
   • 3 Aylık En Düşük: {df['Close'].min():.2f} TL

📊 TEKNİK GÖSTERGELER:
   • RSI (14): {son['RSI']:.2f} {"(Aşırı Alım ⚠)" if son['RSI'] > 70 else "(Aşırı Satım ⚠)" if son['RSI'] < 30 else ""}
   • MACD: {son['MACD']:.2f} {"(Yukarı)" if son['MACD'] > son['MACD_signal'] else "(Aşağı)"}
   • MACD Sinyal: {son['MACD_signal']:.2f}
   • EMA 20: {son['EMA_20']:.2f} {"(Üstünde ▲)" if son['Close'] > son['EMA_20'] else "(Altında ▼)"}
   • SMA 50: {son['SMA_50']:.2f} {"(Üstünde ▲)" if son['Close'] > son['SMA_50'] else "(Altında ▼)"}
   • Bollinger Band: {"(Üst Band)" if son['Close'] > son['BB_upper'] else "(Alt Band)" if son['Close'] < son['BB_lower'] else "(Orta Band)"}
"""
        # Temel analiz ekle
        if temel:
            analiz += f"""
💰 TEMEL GÖSTERGELER:
   • Piyasa Değeri: {temel.get('Piyasa Değeri', 'N/A')}
   • F/K: {temel.get('F/K', 'N/A')}
   • FD/FAVÖK: {temel.get('FD/FAVÖK', 'N/A')}
   • Temettu Verimi: {temel.get('Temettu Verimi', 'N/A')}
   • Son Çeyrek Kâr: {temel.get('Son Çeyrek Kâr', 'N/A')}
"""
        else:
            analiz += "\n⚠ Temel analiz verileri alınamadı\n"

        # Kurum verilerini ekle
        if isinstance(kurum_verisi, dict) and 'hata' not in kurum_verisi:
            analiz += f"""
🏦 KURUMSAL HAREKETLER:
   • Net Alım: {kurum_verisi.get('net_alim', 0):+,.2f} TL
   • Alım/Satım Oranı: {kurum_verisi.get('alis_satis_orani', 0):.2f}
"""
        else:
            analiz += "\n⚠ Kurumsal veri alınamadı\n"

        # Son yorumu ekle
        analiz += "\n💡 GENEL DEĞERLENDİRME:\n"
        buy_signal = 0
        
        if son['RSI'] < 35: buy_signal += 1
        if son['MACD'] > son['MACD_signal']: buy_signal += 1
        if son['Close'] > son['EMA_20']: buy_signal += 1
        
        if buy_signal >= 2:
            analiz += "   • Güçlü al sinyali (Çoğunlukla olumlu göstergeler)"
        elif buy_signal == 1:
            analiz += "   • Karışık sinyaller (Dikkatli olunması önerilir)"
        else:
            analiz += "   • Satış baskısı (Olumsuz göstergeler hakim)"

        # Sonuçları göster
        text_output.config(state=tk.NORMAL)
        text_output.delete(1.0, tk.END)
        text_output.insert(tk.END, analiz)
        text_output.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Hata", f"Analiz yapılamadı:\n{str(e)}")

# Ana uygulama
root = tk.Tk()
root.title("BIST 360° Analiz Uygulaması")
root.geometry("850x650")
root.configure(bg=BG_COLOR)
root.minsize(800, 600)

# Başlık
header = tk.Frame(root, bg=BUTTON_COLOR, height=60)
header.pack(fill=tk.X)
tk.Label(header, text="BIST 360° ANALİZ UYGULAMASI", font=("Segoe UI", 16, "bold"), 
         fg="white", bg=BUTTON_COLOR).pack(pady=15)

# Kontrol paneli
control_frame = tk.Frame(root, bg=BG_COLOR, padx=10, pady=10)
control_frame.pack(fill=tk.X)

tk.Label(control_frame, text="Hisse Kodu:", bg=BG_COLOR, font=FONT, fg="black" ).grid(row=0, column=0, padx=5, sticky="w")

entry = ttk.Entry(control_frame, width=15, font=FONT)
entry.grid(row=0, column=1, padx=5)

ttk.Button(control_frame, text="Analiz Et", command=analiz_et).grid(row=0, column=2, padx=5)
ttk.Button(control_frame, text="Grafik Göster", command=grafik_goster).grid(row=0, column=3, padx=5)
ttk.Button(control_frame, text="Temizle", command=lambda: text_output.config(state=tk.NORMAL) or text_output.delete(1.0, tk.END) or text_output.config(state=tk.DISABLED)).grid(row=0, column=4, padx=5)
ttk.Button(control_frame, text="Çıkış", command=root.quit).grid(row=0, column=5, padx=5)

# Sonuç alanı
result_frame = tk.Frame(root, bg=BG_COLOR, padx=10, pady=10)
result_frame.pack(fill=tk.BOTH, expand=True)

text_output = tk.Text(result_frame, height=25, width=90, wrap=tk.WORD, bg="white", 
                     fg=TEXT_COLOR, font=("Consolas", 10), padx=10, pady=10, 
                     relief=tk.FLAT, state=tk.DISABLED)
scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=text_output.yview)
text_output.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
text_output.pack(fill=tk.BOTH, expand=True)

# Stil ayarları
style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", font=FONT, padding=5, background=BUTTON_COLOR, 
               foreground="white", borderwidth=1)
style.map("TButton", 
          background=[("active", "#3a5a8a"), ("disabled", "#cccccc")],
          foreground=[("disabled", "#888888")])

# Başlangıçta odaklanma
entry.focus()
entry.bind("<Return>", lambda event: analiz_et())

root.mainloop()