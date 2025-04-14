import tkinter as tk
from tkinter import messagebox, ttk
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplfinance as mpf
import numpy as np
import requests
from bs4 import BeautifulSoup
from pazar_bilgisi import get_pazar_bilgisi


# Stil sabitleri
BG_COLOR = "#f0f2f5"
TEXT_COLOR = "black"
LABEL_COLOR = "black"
BUTTON_COLOR = "#4a6fa5"
FONT = ("Segoe UI", 10)

# Varsayılan hisse listesi
DEFAULT_HISSELER = [
    'THYAO', 'AKBNK', 'GARAN', 'ISCTR', 'KOZAA', 'SASA', 'ASELS', 'TCELL', 'PETKM', 'TUPRS',
    'KCHOL', 'ARCLK', 'BIMAS', 'EREGL', 'FROTO', 'HALKB', 'KRDMD', 'SAHOL', 'SISE', 'TKFEN',
    'TOASO', 'VAKBN', 'YKBNK', 'AKSA', 'ALARK', 'ANACM', 'ASUZU', 'BERA', 'BRISA', 'DOHOL'
]

class BistAnalizUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("BIST Analiz Uygulaması")
        self.root.geometry("1100x800")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(1000, 700)
        
        self.hisse_listesi = self.get_bist_hisse_listesi()
        if not self.hisse_listesi:
            messagebox.showwarning("Uyarı", "BIST hisse listesi alınamadı, varsayılan liste kullanılıyor")
            self.hisse_listesi = DEFAULT_HISSELER
        
        self.setup_ui()
        self.setup_styles()

    
    def get_bist_hisse_listesi(self):
        """Asenax API üzerinden BIST hisse listesini çeker, başarısız olursa varsayılan listeyi döndürür."""
        try:
            url = "https://api.asenax.com/bist/list/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # JSON verisini al
            data = response.json()

            # 'data' içindeki 'kod' alanlarını al ve listeye ekle
            if data["code"] == "0":
                hisseler = [item["kod"] for item in data["data"] if "kod" in item]
                if hisseler:
                    return hisseler
                else:
                    print("Asenax API boş liste döndürdü.")
            else:
                print(f"Asenax API başarısız yanıt döndürdü: {data['code']}")
        except Exception as e:
            print(f"Asenax API'den hisse listesi alınırken hata: {e}")

        print("Varsayılan listeye geçiliyor.")
        return DEFAULT_HISSELER

    def setup_ui(self):
        # Başlık
        self.header = tk.Frame(self.root, bg=BUTTON_COLOR, height=80)
        self.header.pack(fill=tk.X, pady=(0, 10))
        tk.Label(self.header, text="BIST ANALİZ UYGULAMASI", 
                font=("Segoe UI", 18, "bold"), fg="white", bg=BUTTON_COLOR).pack(pady=20)

        # Kontrol paneli
        self.control_frame = tk.Frame(self.root, bg=BG_COLOR, padx=15, pady=15)
        self.control_frame.pack(fill=tk.X)

        # Hisse seçim dropdown
        tk.Label(self.control_frame, text="Hisse Kodu:", bg=BG_COLOR, 
                font=FONT, fg=LABEL_COLOR).grid(row=0, column=0, padx=5, sticky="w")
        
        self.hisse_var = tk.StringVar()
        self.hisse_dropdown = ttk.Combobox(self.control_frame, textvariable=self.hisse_var, 
                                         values=self.hisse_listesi, width=15, font=FONT)
        self.hisse_dropdown.grid(row=0, column=1, padx=5)
        self.hisse_dropdown.set('THYAO' if 'THYAO' in self.hisse_listesi else self.hisse_listesi[0])

        # Periyot seçimi
        tk.Label(self.control_frame, text="Periyot:", bg=BG_COLOR, 
                font=FONT, fg=LABEL_COLOR).grid(row=0, column=2, padx=5, sticky="e")
        
        self.periyot_var = tk.StringVar(value="3mo")
        self.periyot_dropdown = ttk.Combobox(self.control_frame, textvariable=self.periyot_var,
                                            values=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"], 
                                            width=8, font=FONT)
        self.periyot_dropdown.grid(row=0, column=3, padx=5)

        # Butonlar
        button_frame = tk.Frame(self.control_frame, bg=BG_COLOR)
        button_frame.grid(row=0, column=4, columnspan=5, padx=10)
        
        ttk.Button(button_frame, text="Analiz Et", command=self.analiz_et).pack(side=tk.LEFT, padx=3)
        ttk.Button(button_frame, text="Çizgi Grafik", command=self.grafik_goster).pack(side=tk.LEFT, padx=3)
        ttk.Button(button_frame, text="Mum Grafiği", command=self.mum_grafigi_goster).pack(side=tk.LEFT, padx=3)
        ttk.Button(button_frame, text="Temizle", command=self.temizle).pack(side=tk.LEFT, padx=3)
        ttk.Button(button_frame, text="Çıkış", command=self.root.quit).pack(side=tk.LEFT, padx=3)

        # Sonuç alanı
        self.result_frame = tk.Frame(self.root, bg=BG_COLOR, padx=15, pady=15)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        self.text_output = tk.Text(self.result_frame, height=30, width=130, wrap=tk.WORD, 
                                 bg="white", fg=TEXT_COLOR, font=("Consolas", 10), 
                                 padx=15, pady=15, relief=tk.FLAT)
        self.scrollbar = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, 
                                     command=self.text_output.yview)
        self.text_output.configure(yscrollcommand=self.scrollbar.set)
        self.text_output.config(state=tk.DISABLED)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_output.pack(fill=tk.BOTH, expand=True)

        # Klavye kısayolları
        self.hisse_dropdown.bind("<Return>", lambda event: self.analiz_et())
        self.hisse_dropdown.focus()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=FONT, padding=6, background=BUTTON_COLOR, 
                      foreground="white")
        style.map("TButton", 
                background=[("active", "#3a5a8a"), ("disabled", "#cccccc")],
                foreground=[("disabled", "#888888")])
        style.configure("TCombobox", font=FONT, padding=6)
        style.configure("Vertical.TScrollbar", background=BUTTON_COLOR)
        
    def temizle(self):
        self.text_output.config(state=tk.NORMAL)
        self.text_output.delete(1.0, tk.END)
        self.text_output.config(state=tk.DISABLED)
        
    def teknik_analiz(self, df):
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
            df['EMA_200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
            
            # Volatilite göstergeleri
            bollinger = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
            df['BB_upper'] = bollinger.bollinger_hband()
            df['BB_middle'] = bollinger.bollinger_mavg()
            df['BB_lower'] = bollinger.bollinger_lband()
            
            # Hacim analizi
            df['OBV'] = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
            
            return df
        except Exception as e:
            print(f"Teknik analiz hatası: {e}")
            return None
            
    def temel_analiz(self, hisse_kodu):
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

            # Pazar Bilgisi
            pazar_bilgisi = get_pazar_bilgisi(hisse_kodu)

            
            return {
                'Piyasa Değeri': market_cap_str,
                'F/K': info.get('forwardPE', 'N/A'),
                'FD/FAVÖK': info.get('enterpriseToEbitda', 'N/A'),
                'Temettu Verimi': dividend_str,
                'Son Çeyrek Kâr': profit_str,
                '52 Hafta En Yüksek': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52 Hafta En Düşük': info.get('fiftyTwoWeekLow', 'N/A'),
                'Pazar': pazar_bilgisi
            }
        except Exception as e:
            print(f"Temel analiz hatası: {e}")
            return None
            
    def grafik_goster(self):
        hisse_kodu = self.hisse_var.get().strip().upper()
        periyot = self.periyot_var.get()
        
        if not hisse_kodu:
            messagebox.showwarning("Uyarı", "Lütfen bir hisse kodu seçin")
            return
            
        try:
            hisse = yf.Ticker(f"{hisse_kodu}.IS")
            df = hisse.history(period=periyot)
            
            if df.empty or len(df) < 5:
                messagebox.showerror("Hata", "Yeterli veri bulunamadı")
                return
                
            df = self.teknik_analiz(df)
            if df is None:
                messagebox.showerror("Hata", "Teknik analiz yapılamadı")
                return
            
            plt.style.use('ggplot')
            
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1, 1]})
            fig.patch.set_facecolor(BG_COLOR)
            
            # Fiyat grafiği
            ax1.plot(df.index, df['Close'], label='Kapanış', color='#2e86de', linewidth=2)
            ax1.plot(df.index, df['EMA_20'], label='EMA 20', linestyle='--', color='#ff9f43')
            ax1.plot(df.index, df['SMA_50'], label='SMA 50', linestyle=':', color='#5f27cd')
            ax1.plot(df.index, df['EMA_200'], label='EMA 200', linestyle='-.', color='#ff6b6b')
            ax1.fill_between(df.index, df['BB_upper'], df['BB_lower'], color='#c8d6e5', alpha=0.3)
            ax1.set_title(f'{hisse_kodu} Fiyat Grafiği ({periyot})', fontsize=14, pad=20)
            ax1.set_ylabel('Fiyat (TL)', fontsize=10)
            ax1.legend(loc='upper left', fontsize=9)
            ax1.grid(True, linestyle='--', alpha=0.7)
            
            # RSI grafiği
            ax2.plot(df.index, df['RSI'], label='RSI 14', color='#10ac84', linewidth=2)
            ax2.axhline(70, color='#ff6b6b', linestyle='--', linewidth=1)
            ax2.axhline(30, color='#1dd1a1', linestyle='--', linewidth=1)
            ax2.set_title('RSI (14)', fontsize=12, pad=20)
            ax2.set_ylabel('RSI', fontsize=10)
            ax2.set_ylim(0, 100)
            ax2.legend(loc='upper left', fontsize=9)
            ax2.grid(True, linestyle='--', alpha=0.7)
            
            # MACD grafiği
            ax3.plot(df.index, df['MACD'], label='MACD', color='#9c88ff', linewidth=1.5)
            ax3.plot(df.index, df['MACD_signal'], label='Sinyal', color='#f368e0', linewidth=1.5)
            ax3.bar(df.index, df['MACD'] - df['MACD_signal'], label='Histogram', 
                   color=np.where(df['MACD'] > df['MACD_signal'], '#2ecc71', '#e74c3c'), alpha=0.5)
            ax3.set_title('MACD (12,26,9)', fontsize=12, pad=20)
            ax3.legend(loc='upper left', fontsize=9)
            ax3.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            
            grafik_pencere = tk.Toplevel()
            grafik_pencere.title(f"{hisse_kodu} Teknik Grafik - {periyot}")
            grafik_pencere.geometry("1100x850")
            
            canvas = FigureCanvasTkAgg(fig, master=grafik_pencere)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            def on_close():
                plt.close(fig)
                grafik_pencere.destroy()
            
            grafik_pencere.protocol("WM_DELETE_WINDOW", on_close)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Grafik oluşturulamadı:\n{str(e)}")
            
    def mum_grafigi_goster(self):
        hisse_kodu = self.hisse_var.get().strip().upper()
        periyot = self.periyot_var.get()

        if not hisse_kodu:
            messagebox.showwarning("Uyarı", "Lütfen bir hisse kodu seçin")
            return

        try:
            hisse = yf.Ticker(f"{hisse_kodu}.IS")
            df = hisse.history(period=periyot)

            if df.empty or len(df) < 5:
                messagebox.showerror("Hata", "Yeterli veri bulunamadı")
                return

            df.index = pd.to_datetime(df.index)
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

            grafik_pencere = tk.Toplevel()
            grafik_pencere.title(f"{hisse_kodu} Mum Grafiği - {periyot}")
            grafik_pencere.geometry("1100x850")

            # Renk ve stil
            mc = mpf.make_marketcolors(
                up='#2ecc71', down='#e74c3c',
                wick={'up':'#2ecc71', 'down':'#e74c3c'},
                edge={'up':'#2ecc71', 'down':'#e74c3c'},
                volume='#3498db'
            )
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', gridcolor='#dddddd')

            # Mum grafiğini çiz, fig ve axes döner
            fig, axes = mpf.plot(df,
                    type='candle',
                    style=s,
                    title=f'\n{hisse_kodu} Mum Grafiği ({periyot})',
                    ylabel='Fiyat (TL)',
                    volume=True,
                    mav=(20, 50, 200),
                    tight_layout=True,
                    returnfig=True,
                    warn_too_much_data=10000,
                    update_width_config=dict(
                        candle_linewidth=1.0,
                        candle_width=0.8,
                        volume_linewidth=1.0
                    ))

            canvas = FigureCanvasTkAgg(fig, master=grafik_pencere)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            def on_close():
                plt.close(fig)
                grafik_pencere.destroy()

            grafik_pencere.protocol("WM_DELETE_WINDOW", on_close)

        except Exception as e:
            messagebox.showerror("Hata", f"Mum grafiği oluşturulamadı:\n{str(e)}")

    
    def analiz_et(self):
        hisse_kodu = self.hisse_var.get().strip().upper()
        periyot = self.periyot_var.get()
        
        if not hisse_kodu:
            messagebox.showwarning("Uyarı", "Lütfen bir hisse kodu seçin")
            return

        try:
            hisse = yf.Ticker(f"{hisse_kodu}.IS")
            df = hisse.history(period=periyot)

            if df.empty or len(df) < 10:
                messagebox.showerror("Hata", f"Yeterli veri bulunamadı (en az 10 iş günü gereklidir)\nSeçilen periyot: {periyot}")
                return

            df = self.teknik_analiz(df)
            if df is None:
                messagebox.showerror("Hata", "Teknik analiz yapılamadı")
                return
                
            son_fiyat = df['Close'].iloc[-1]
            onceki_fiyat = df['Close'].iloc[-2] if len(df) > 1 else son_fiyat
            daily_change = son_fiyat - onceki_fiyat
            percent_change = (son_fiyat/onceki_fiyat-1)*100
            
            son = df.iloc[-1]
            temel = self.temel_analiz(hisse_kodu)
            
            # Analiz raporu oluştur
            analiz = f"""
📈 {hisse_kodu.upper()}.IS ANALİZ RAPORU - {datetime.now().strftime('%d.%m.%Y %H:%M')}
{'='*80}

🔹 FİYAT BİLGİLERİ ({periyot}):
   • Son Fiyat: {son_fiyat:.2f} TL
   • Günlük Değişim: {daily_change:+.2f} TL ({percent_change:+.2f}%)
   • Ortalama: {df['Close'].mean():.2f} TL
   • En Yüksek: {df['Close'].max():.2f} TL
   • En Düşük: {df['Close'].min():.2f} TL
   • Volatilite: {(df['Close'].max() - df['Close'].min())/df['Close'].mean()*100:.2f}%

📊 TEKNİK GÖSTERGELER:
   • RSI (14): {son['RSI']:.2f} {"(Aşırı Alım ⚠)" if son['RSI'] > 70 else "(Aşırı Satım ⚠)" if son['RSI'] < 30 else ""}
   • MACD: {son['MACD']:.2f} {"(Yukarı)" if son['MACD'] > son['MACD_signal'] else "(Aşağı)"}
   • MACD Sinyal: {son['MACD_signal']:.2f}
   • EMA 20: {son['EMA_20']:.2f} {"(Üstünde ▲)" if son['Close'] > son['EMA_20'] else "(Altında ▼)"}
   • SMA 50: {son['SMA_50']:.2f} {"(Üstünde ▲)" if son['Close'] > son['SMA_50'] else "(Altında ▼)"}
   • EMA 200: {son['EMA_200']:.2f} {"(Üstünde ▲)" if son['Close'] > son['EMA_200'] else "(Altında ▼)"}
   • Bollinger Band: {"(Üst Band)" if son['Close'] > son['BB_upper'] else "(Alt Band)" if son['Close'] < son['BB_lower'] else "(Orta Band)"}
   • OBV: {son['OBV']/1000000:+.2f} M
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
   • 52 Hafta En Yüksek: {temel.get('52 Hafta En Yüksek', 'N/A')}
   • 52 Hafta En Düşük: {temel.get('52 Hafta En Düşük', 'N/A')}
   • Pazar: {temel.get('Pazar', 'N/A')}
"""
            else:
                analiz += "\n⚠ Temel analiz verileri alınamadı\n"

            # Sinyal analizi
            analiz += "\n💡 GENEL DEĞERLENDİRME:\n"
            buy_signal = 0
            
            # Al sinyalleri
            if son['RSI'] < 35: buy_signal += 1
            if son['MACD'] > son['MACD_signal']: buy_signal += 1
            if son['Close'] > son['EMA_20']: buy_signal += 1
            if son['Close'] > son['SMA_50']: buy_signal += 1
            if son['Close'] > son['EMA_200']: buy_signal += 1
            if son['Close'] < son['BB_lower']: buy_signal += 1
            
            if buy_signal >= 4:
                analiz += "   • GÜÇLÜ AL SİNYALİ (Çoğunlukla olumlu göstergeler)"
            elif buy_signal >= 2:
                analiz += "   • Orta seviye al sinyali (Bazı olumlu göstergeler)"
            elif buy_signal == 1:
                analiz += "   • Zayıf al sinyali (Sınırlı olumlu gösterge)"
            else:
                analiz += "   • Satış baskısı (Olumsuz göstergeler hakim)"

            # Sonuçları göster
            self.text_output.config(state=tk.NORMAL)
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(tk.END, analiz)
            self.text_output.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Hata", f"Analiz yapılamadı:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BistAnalizUygulamasi(root)
    root.mainloop()