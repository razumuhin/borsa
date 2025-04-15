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

from portfolio import Portfolio

class BistAnalizUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("BIST Analiz Uygulaması")
        self.root.geometry("1100x800")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(1000, 700)
        self.portfolio = Portfolio()

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
                font=("Segoe UI", 18, "bold"), fg="white", bg=BUTTON_COLOR).pack(side=tk.LEFT, pady=20, padx=20)

        # Portföy yönetimi butonu
        self.portfolio_button = ttk.Button(self.header, text="Portföy Yönetimi", 
                                         command=self.show_portfolio_window)
        self.portfolio_button.pack(side=tk.RIGHT, padx=10, pady=20)

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

    def show_portfolio_window(self):
        portfolio_window = tk.Toplevel(self.root)
        portfolio_window.title("Portföy Yönetimi")
        portfolio_window.geometry("1200x800")
        portfolio_window.configure(bg="#f8f9fa")
        
        # Ana çerçeveler
        form_frame = tk.Frame(portfolio_window, bg="#ffffff")
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        table_frame = tk.Frame(portfolio_window, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Form elemanları
        tk.Label(form_frame, text="Hisse Kodu:", bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        symbol_var = tk.StringVar()
        symbol_combo = ttk.Combobox(form_frame, textvariable=symbol_var, values=self.hisse_listesi)
        symbol_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="İşlem Tipi:", bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        operation_var = tk.StringVar(value="AL")
        operation_combo = ttk.Combobox(form_frame, textvariable=operation_var, values=["AL", "SAT"], state="readonly")
        operation_combo.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_frame, text="Fiyat (TL):", bg="#ffffff").grid(row=0, column=4, padx=5, pady=5)
        price_entry = ttk.Entry(form_frame)
        price_entry.grid(row=0, column=5, padx=5, pady=5)
        
        tk.Label(form_frame, text="Adet:", bg="#ffffff").grid(row=0, column=6, padx=5, pady=5)
        quantity_entry = ttk.Entry(form_frame)
        quantity_entry.grid(row=0, column=7, padx=5, pady=5)
        
        # Tablo
        columns = ('Hisse', 'Toplam Adet', 'Maliyet', 'Güncel Değer', 'Kar/Zarar')
        portfolio_tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        for col in columns:
            portfolio_tree.heading(col, text=col)
            portfolio_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=portfolio_tree.yview)
        portfolio_tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        portfolio_tree.pack(fill=tk.BOTH, expand=True)
        
        def add_transaction():
            try:
                symbol = symbol_var.get().strip().upper()
                operation = "BUY" if operation_var.get() == "AL" else "SELL"
                price = float(price_entry.get())
                quantity = int(quantity_entry.get())
                
                self.portfolio.add_transaction(symbol, operation, price, quantity)
                update_portfolio_view()
                
                # Form temizleme
                price_entry.delete(0, tk.END)
                quantity_entry.delete(0, tk.END)
                messagebox.showinfo("Başarılı", "İşlem başarıyla eklendi!")
                
            except ValueError as e:
                messagebox.showerror("Hata", "Lütfen geçerli değerler girin!")
        
        def update_portfolio_view():
            for item in portfolio_tree.get_children():
                portfolio_tree.delete(item)
                
            portfolio_data = self.portfolio.get_portfolio()
            for symbol, quantity, cost, date, avg_cost in portfolio_data:
                portfolio_tree.insert('', tk.END, values=(
                    symbol,
                    quantity,
                    f"{cost:,.2f} TL",
                    "Hesaplanıyor...",
                    "Hesaplanıyor..."
                ))
        
        # İşlem ekle butonu
        ttk.Button(form_frame, text="İşlem Ekle", command=add_transaction).grid(row=0, column=8, padx=20, pady=5)
        
        # İlk görünümü güncelle
        update_portfolio_view()
        
        # Ana container
        main_container = tk.Frame(portfolio_window, bg="#f8f9fa")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Sol Panel - İşlem Ekleme Formu
        left_panel = tk.Frame(main_container, bg="#ffffff", relief="ridge", bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10), pady=5)
        
        # Form başlığı
        header_frame = tk.Frame(left_panel, bg="#ffffff")
        header_frame.pack(fill=tk.X, padx=20, pady=15)
        header_label = tk.Label(header_frame, text="Yeni İşlem Ekle", 
                              font=("Segoe UI", 14, "bold"), bg="#ffffff", fg="#2C3E50")
        header_label.pack()
        
        # Form çerçevesi
        form_frame = tk.Frame(left_panel, bg="#ffffff")
        form_frame.pack(fill=tk.BOTH, padx=20, pady=10)
        
        # Form elemanları
        fields = [
            ("Hisse Kodu:", self.hisse_listesi),
            ("İşlem Tipi:", ["AL", "SAT"]),
            ("Fiyat (TL):", None),
            ("Adet:", None),
            ("Tarih:", datetime.now().strftime('%Y-%m-%d %H:%M'))
        ]
        
        entries = {}
        for i, (label_text, values) in enumerate(fields):
            frame = tk.Frame(form_frame, bg="#ffffff")
            frame.pack(fill=tk.X, pady=10)
            
            label = tk.Label(frame, text=label_text, font=("Segoe UI", 11),
                           bg="#ffffff", fg="#2C3E50", width=10, anchor="w")
            label.pack(side=tk.LEFT, padx=(0,10))
            
            if isinstance(values, list):
                var = tk.StringVar(value=values[0])
                entry = ttk.Combobox(frame, values=values, textvariable=var,
                                   state="readonly" if label_text == "İşlem Tipi:" else "normal",
                                   width=20, font=("Segoe UI", 11))
                entries[label_text] = var
            else:
                entry = ttk.Entry(frame, font=("Segoe UI", 11), width=20)
                if values:  # Tarih için varsayılan değer
                    entry.insert(0, values)
                entries[label_text] = entry
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
        def add_transaction():
            try:
                symbol = entries["Hisse Kodu:"].get().strip().upper()
                operation = "BUY" if entries["İşlem Tipi:"].get() == "AL" else "SELL"
                price = float(entries["Fiyat (TL):"].get())
                quantity = int(entries["Adet:"].get())
                date = entries["Tarih:"].get()
                
                self.portfolio.add_transaction(symbol, operation, price, quantity, date)
                update_portfolio_view()
                
                # Form temizleme
                entries["Fiyat (TL):"].delete(0, tk.END)
                entries["Adet:"].delete(0, tk.END)
                entries["Tarih:"].delete(0, tk.END)
                entries["Tarih:"].insert(0, datetime.now().strftime('%Y-%m-%d %H:%M'))
                
                messagebox.showinfo("Başarılı", "İşlem başarıyla eklendi!")
            except ValueError as e:
                messagebox.showerror("Hata", "Lütfen geçerli değerler girin!")
                
        # İşlem ekle butonu
        button_frame = tk.Frame(left_panel, bg="#ffffff")
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        add_button = ttk.Button(button_frame, text="İşlem Ekle", command=add_transaction,
                              style="Accent.TButton")
        add_button.pack(fill=tk.X)
        
        # Sağ Panel - Portföy Tablosu
        right_panel = tk.Frame(main_container, bg="#ffffff", relief="ridge", bd=1)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        
        # Tablo başlığı
        # Özet bilgiler
        summary_frame = tk.Frame(right_panel, bg="#ffffff")
        summary_frame.pack(fill=tk.X, padx=20, pady=10)
        
        total_stocks, total_investment, total_shares = self.portfolio.get_portfolio_summary()
        
        summary_text = f"Toplam Hisse Sayısı: {total_stocks} • " \
                      f"Toplam Yatırım: {total_investment:,.2f} TL • " \
                      f"Toplam Lot: {total_shares:,}"
        
        summary_label = tk.Label(summary_frame, text=summary_text,
                               font=("Segoe UI", 11), bg="#ffffff", fg="#2C3E50")
        summary_label.pack(pady=5)
        
        # Tablo başlığı
        table_header = tk.Frame(right_panel, bg="#ffffff")
        table_header.pack(fill=tk.X, padx=20, pady=15)
        table_label = tk.Label(table_header, text="Portföy Durumu", 
                             font=("Segoe UI", 14, "bold"), bg="#ffffff", fg="#2C3E50")
        table_label.pack()
        
        # Tablo çerçevesi
        table_frame = tk.Frame(right_panel, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,20))
        
        # Tablo
        columns = ('Hisse', 'Toplam Adet', 'Maliyet', 'Güncel Değer', 'Kar/Zarar', 'İşlem Tarihi')
        portfolio_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style="Custom.Treeview")
        
        for col in columns:
            portfolio_tree.heading(col, text=col)
            portfolio_tree.column(col, width=150, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=portfolio_tree.yview)
        portfolio_tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        portfolio_tree.pack(fill=tk.BOTH, expand=True)

        # İşlem detayları grid layout
        tk.Label(form_frame, text="Hisse:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0, padx=5, pady=5)
        symbol_var = tk.StringVar()
        symbol_combo = ttk.Combobox(form_frame, textvariable=symbol_var, values=self.hisse_listesi, width=15)
        symbol_combo.grid(row=0, column=1, padx=5, pady=5)
        symbol_combo.set(self.hisse_listesi[0] if self.hisse_listesi else '')

        tk.Label(form_frame, text="İşlem:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=2, padx=5, pady=5)
        operation_var = tk.StringVar(value="AL")
        operation_combo = ttk.Combobox(form_frame, textvariable=operation_var, values=["AL", "SAT"], 
                                     state="readonly", width=10)
        operation_combo.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Fiyat (TL):", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=4, padx=5, pady=5)
        price_entry = ttk.Entry(form_frame, width=12)
        price_entry.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="Adet:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=6, padx=5, pady=5)
        quantity_entry = ttk.Entry(form_frame, width=12)
        quantity_entry.grid(row=0, column=7, padx=5, pady=5)

        tk.Label(form_frame, text="Tarih:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=8, padx=5, pady=5)
        date_entry = ttk.Entry(form_frame, width=16)
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d %H:%M'))
        date_entry.grid(row=0, column=9, padx=5, pady=5)

        # İşlem ekleme çerçevesi
        ttk.Label(transaction_frame, text="Hisse:").grid(row=0, column=0, padx=5, pady=5)
        symbol_var = tk.StringVar()
        symbol_combo = ttk.Combobox(transaction_frame, textvariable=symbol_var, 
                                  values=self.hisse_listesi, width=15)
        symbol_combo.grid(row=0, column=1, padx=5, pady=5)
        symbol_combo.set(self.hisse_listesi[0] if self.hisse_listesi else '')

        # İşlem Tipi
        operation_frame = tk.Frame(form_frame, bg="#F8F9FA")
        operation_frame.pack(fill=tk.X, pady=5)
        tk.Label(operation_frame, text="İşlem Tipi:", font=("Segoe UI", 11),
                bg="#F8F9FA", fg="#2C3E50").pack(anchor="w")
        operation_var = tk.StringVar(value="AL")
        operation_combo = ttk.Combobox(operation_frame, textvariable=operation_var,
                                     values=["AL", "SAT"], state="readonly",
                                     width=20, font=("Segoe UI", 11))
        operation_combo.pack(fill=tk.X, pady=(5,0))

        # Fiyat
        price_frame = tk.Frame(form_frame, bg="#F8F9FA")
        price_frame.pack(fill=tk.X, pady=5)
        tk.Label(price_frame, text="Fiyat (TL):", font=("Segoe UI", 11),
                bg="#F8F9FA", fg="#2C3E50").pack(anchor="w")
        price_entry = ttk.Entry(price_frame, font=("Segoe UI", 11))
        price_entry.pack(fill=tk.X, pady=(5,0))

        # Adet
        quantity_frame = tk.Frame(form_frame, bg="#F8F9FA")
        quantity_frame.pack(fill=tk.X, pady=5)
        tk.Label(quantity_frame, text="Adet:", font=("Segoe UI", 11),
                bg="#F8F9FA", fg="#2C3E50").pack(anchor="w")
        quantity_entry = ttk.Entry(quantity_frame, font=("Segoe UI", 11))
        quantity_entry.pack(fill=tk.X, pady=(5,0))

        # İşlem butonu
        button_frame = tk.Frame(form_frame, bg="#F8F9FA")
        button_frame.pack(fill=tk.X, pady=20)
        ttk.Button(button_frame, text="İşlemi Kaydet",
                  style="Accent.TButton", command=add_transaction).pack(fill=tk.X)

        # Hisse seçimi
        tk.Label(form_frame, text="Hisse Kodu:", bg="#ffffff", 
                font=("Segoe UI", 10)).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        symbol_var = tk.StringVar()
        symbol_combo = ttk.Combobox(form_frame, textvariable=symbol_var,
                                  values=self.hisse_listesi, width=15, font=("Segoe UI", 10))
        symbol_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        symbol_combo.set(self.hisse_listesi[0] if self.hisse_listesi else '')

        # İşlem tipi
        tk.Label(form_frame, text="İşlem Tipi:", bg="#ffffff",
                font=("Segoe UI", 10)).grid(row=0, column=2, padx=10, pady=5, sticky="e")
        operation_var = tk.StringVar(value="AL")
        operation_combo = ttk.Combobox(form_frame, textvariable=operation_var,
                                     values=["AL", "SAT"], state="readonly", 
                                     width=10, font=("Segoe UI", 10))
        operation_combo.grid(row=0, column=3, padx=10, pady=5, sticky="w")

        # Fiyat
        tk.Label(form_frame, text="Fiyat (TL):", bg="#ffffff",
                font=("Segoe UI", 10)).grid(row=0, column=4, padx=10, pady=5, sticky="e")
        price_entry = ttk.Entry(form_frame, width=12, font=("Segoe UI", 10))
        price_entry.grid(row=0, column=5, padx=10, pady=5, sticky="w")

        # Adet
        tk.Label(form_frame, text="Adet:", bg="#ffffff",
                font=("Segoe UI", 10)).grid(row=0, column=6, padx=10, pady=5, sticky="e")
        quantity_entry = ttk.Entry(form_frame, width=12, font=("Segoe UI", 10))
        quantity_entry.grid(row=0, column=7, padx=10, pady=5, sticky="w")

        def add_transaction():
            try:
                symbol = symbol_var.get().strip().upper()
                operation = operation_var.get()
                price = float(price_entry.get())
                quantity = int(quantity_entry.get())
                date = date_entry.get()

                if operation == "AL":
                    self.portfolio.add_transaction(symbol, "BUY", price, quantity, date)
                else:
                    self.portfolio.add_transaction(symbol, "SELL", price, quantity, date)

                update_portfolio_view()

                symbol_combo.set('')
                price_entry.delete(0, tk.END)
                quantity_entry.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Hata", "Lütfen geçerli değerler girin")

        # İşlem ekle butonu
        add_button = ttk.Button(form_frame, text="İşlem Ekle", command=add_transaction,
                              style="Accent.TButton")
        add_button.grid(row=0, column=9, padx=10, pady=5, sticky="ew")

        # Grid yapısını düzenle
        form_frame.grid_columnconfigure(9, weight=1)


        # İşlem butonu
        ttk.Button(left_panel, text="İşlemi Gerçekleştir", 
                  style="Accent.TButton", command=add_transaction).pack(pady=30)

        # Portföy tablosu
        portfolio_frame = tk.Frame(portfolio_window, bg="#ffffff")
        portfolio_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ('Hisse', 'Toplam Adet', 'Maliyet', 'Güncel Değer', 'Kar/Zarar', 'İşlem Tarihi')
        portfolio_tree = ttk.Treeview(table_frame, columns=columns, show='headings', style="Custom.Treeview")

        for col in columns:
            portfolio_tree.heading(col, text=col)
            portfolio_tree.column(col, width=120, anchor=tk.CENTER)

        portfolio_scroll = ttk.Scrollbar(portfolio_frame, orient=tk.VERTICAL, 
                                       command=portfolio_tree.yview)
        portfolio_tree.configure(yscrollcommand=portfolio_scroll.set)

        portfolio_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        portfolio_tree.pack(fill=tk.BOTH, expand=True)

        def update_portfolio_view():
            for item in portfolio_tree.get_children():
                portfolio_tree.delete(item)

            portfolio_data = self.portfolio.get_portfolio()
            for symbol, quantity, cost, buy_date, avg_cost in portfolio_data:
                try:
                    current_price = yf.Ticker(f"{symbol}.IS").history(period="1d")['Close'].iloc[-1]
                    current_value = current_price * quantity
                    profit_loss = current_value - cost
                    profit_percentage = (profit_loss / cost) * 100
                    formatted_date = datetime.strptime(buy_date, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
                    
                    portfolio_tree.insert('', tk.END, values=(
                        symbol,
                        quantity,
                        f"{avg_cost:,.2f} TL",
                        f"{current_value:,.2f} TL",
                        f"{profit_loss:+,.2f} TL (%{profit_percentage:+.2f})",
                        formatted_date
                    ))
                except:
                    portfolio_tree.insert('', tk.END, values=(
                        symbol,
                        quantity,
                        f"{avg_cost:,.2f} TL",
                        "Veri Yok",
                        "Hesaplanamadı",
                        formatted_date
                    ))

        update_portfolio_view()

        # Otomatik güncelleme
        def auto_update():
            update_portfolio_view()
            portfolio_window.after(60000, auto_update)  # Her 1 dakikada bir güncelle

        portfolio_window.after(60000, auto_update)
        # Klavye kısayolları
        self.hisse_dropdown.bind("<Return>", lambda event: self.analiz_et())
        self.hisse_dropdown.focus()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Ana buton stili
        style.configure("TButton", font=FONT, padding=10, background=BUTTON_COLOR)
        
        # Özel buton stili
        style.configure("Accent.TButton", 
                       font=("Segoe UI", 11),
                       padding=15,
                       background="#4CAF50",
                       foreground="white")
        
        # Treeview stili
        style.configure("Custom.Treeview",
                       font=("Segoe UI", 10),
                       rowheight=35,
                       background="#FFFFFF",
                       fieldbackground="#FFFFFF")
        
        style.configure("Custom.Treeview.Heading",
                       font=("Segoe UI", 10, "bold"),
                       padding=10)
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

            return {
                'Piyasa Değeri': market_cap_str,
                'F/K': info.get('forwardPE', 'N/A'),
                'FD/FAVÖK': info.get('enterpriseToEbitda', 'N/A'),
                'Temettu Verimi': dividend_str,
                'Son Çeyrek Kâr': profit_str,
                '52 Hafta En Yüksek': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52 Hafta En Düşük': info.get('fiftyTwoWeekLow', 'N/A'),

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

            # 4 alt grafik için height_ratios güncellendi
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10), 
                                                        gridspec_kw={'height_ratios': [2, 1], 'width_ratios': [3, 1]})
            fig.patch.set_facecolor(BG_COLOR)

            # Fiyat grafiği (ax1)
            ax1.plot(df.index, df['Close'], label='Kapanış', color='#2e86de', linewidth=2)
            ax1.plot(df.index, df['EMA_20'], label='EMA 20', linestyle='--', color='#ff9f43')
            ax1.plot(df.index, df['SMA_50'], label='SMA 50', linestyle=':', color='#5f27cd')
            ax1.plot(df.index, df['EMA_200'], label='EMA 200', linestyle='-.', color='#ff6b6b')
            ax1.fill_between(df.index, df['BB_upper'], df['BB_lower'], color='#c8d6e5', alpha=0.3)
            ax1.set_title(f'{hisse_kodu} Fiyat Grafiği ({periyot})', fontsize=14, pad=15)
            ax1.set_ylabel('Fiyat (TL)', fontsize=10)
            ax1.legend(loc='upper left', fontsize=9)
            ax1.grid(True, linestyle='--', alpha=0.7)

            # RSI grafiği (ax2)
            ax2.plot(df.index, df['RSI'], label='RSI 14', color='#10ac84', linewidth=2)
            ax2.axhline(70, color='#ff6b6b', linestyle='--', linewidth=1)
            ax2.axhline(30, color='#1dd1a1', linestyle='--', linewidth=1)
            ax2.set_title('RSI (14)', fontsize=12, pad=15)
            ax2.set_ylabel('RSI', fontsize=10)
            ax2.set_ylim(0, 100)
            ax2.legend(loc='upper left', fontsize=9)
            ax2.grid(True, linestyle='--', alpha=0.7)

            # MACD grafiği (ax3)
            ax3.plot(df.index, df['MACD'], label='MACD', color='#9c88ff', linewidth=1.5)
            ax3.plot(df.index, df['MACD_signal'], label='Sinyal', color='#f368e0', linewidth=1.5)
            ax3.bar(df.index, df['MACD'] - df['MACD_signal'], label='Histogram', 
                   color=np.where(df['MACD'] > df['MACD_signal'], '#2ecc71', '#e74c3c'), alpha=0.5)
            ax3.set_title('MACD (12,26,9)', fontsize=12, pad=15)
            ax3.legend(loc='upper left', fontsize=9)
            ax3.grid(True, linestyle='--', alpha=0.7)

            # Hacim grafiği (ax4)
            ax4.bar(df.index, df['Volume']/1000000, color='#3498db', alpha=0.7)
            ax4.set_title('Hacim (Milyon)', fontsize=12, pad=15)
            ax4.set_ylabel('Hacim (M)')
            ax4.grid(True, linestyle='--', alpha=0.5)

            plt.tight_layout()

            grafik_pencere = tk.Toplevel()
            grafik_pencere.title(f"{hisse_kodu} Teknik Grafik - {periyot}")
            grafik_pencere.geometry("1200x900")

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

🔹 FİYAT VE HACİM BİLGİLERİ ({periyot}):
   • Son Fiyat: {son_fiyat:.2f} TL
   • Günlük Değişim: {daily_change:+.2f} TL ({percent_change:+.2f}%)
   • Ortalama Fiyat: {df['Close'].mean():.2f} TL
   • Ortalama Hacim: {df['Volume'].mean()/1000000:.2f} M
   • Son Hacim: {df['Volume'].iloc[-1]/1000000:.2f} M
   • En Yüksek Fiyat: {df['Close'].max():.2f} TL
   • En Düşük Fiyat: {df['Close'].min():.2f} TL
   • En Yüksek Hacim: {df['Volume'].max()/1000000:.2f} M
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
   • Hacim Ortalama/Şimdi: {df['Volume'].mean()/1000000:.1f}M/{son['Volume']/1000000:.1f}M
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

            # Sinyal analizine hacim kontrolü ekleyin
            if son['Volume'] > df['Volume'].mean() * 1.5:  # Ortalamanın 1.5 katından fazla hacim:
                buy_signal += 1
                analiz += "\n   • Yüksek Hacim: Alım satım ilgisinde artış"

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