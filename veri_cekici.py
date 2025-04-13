import requests
from bs4 import BeautifulSoup

def kurum_alim_satim_verisi(hisse_kodu):
    """
    Belirtilen hisse koduna ait kurum alım-satım verilerini çeker.
    
    Parametreler:
        hisse_kodu (str): Hisse kodu (Örnek: 'THYAO', 'AKBNK')
    
    Dönen Değer:
        dict: {
            'alici_kurumlar': [{'kurum': str, 'miktar': str}],
            'satici_kurumlar': [{'kurum': str, 'miktar': str}],
            'net_alim': float,
            'alis_satis_orani': float
        } veya hata mesajı
    """
    url = f"https://www.gunlukrapor.tk/hisse/{hisse_kodu.upper()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")

        if len(tables) < 2:
            return {"hata": "Veri bulunamadı veya tablo yapısı değişti"}

        # Alıcı kurumların çekilmesi
        alici_tablosu = tables[0]
        alici_kurumlar = []
        alici_toplam = 0
        
        for row in alici_tablosu.find_all("tr")[1:]:  # Başlık satırını atla
            cols = row.find_all("td")
            if len(cols) >= 2:
                try:
                    miktar = float(cols[1].text.strip().replace('.', '').replace(',', '.'))
                except:
                    miktar = 0
                
                alici_kurumlar.append({
                    "kurum": cols[0].text.strip(),
                    "miktar": cols[1].text.strip()
                })
                alici_toplam += miktar

        # Satıcı kurumların çekilmesi
        satici_tablosu = tables[1]
        satici_kurumlar = []
        satici_toplam = 0
        
        for row in satici_tablosu.find_all("tr")[1:]:  # Başlık satırını atla
            cols = row.find_all("td")
            if len(cols) >= 2:
                try:
                    miktar = float(cols[1].text.strip().replace('.', '').replace(',', '.'))
                except:
                    miktar = 0
                
                satici_kurumlar.append({
                    "kurum": cols[0].text.strip(),
                    "miktar": cols[1].text.strip()
                })
                satici_toplam += miktar

        # Net alım ve alım-satım oranı hesaplama
        net_alim = alici_toplam - satici_toplam
        alis_satis_orani = alici_toplam / satici_toplam if satici_toplam > 0 else 0

        return {
            "alici_kurumlar": alici_kurumlar,
            "satici_kurumlar": satici_kurumlar,
            "net_alim": net_alim,
            "alis_satis_orani": alis_satis_orani,
            "alici_toplam": alici_toplam,
            "satici_toplam": satici_toplam
        }

    except requests.exceptions.RequestException as e:
        return {"hata": f"İstek hatası: {str(e)}"}
    except Exception as e:
        return {"hata": f"Beklenmeyen hata: {str(e)}"}


def format_kurum_verisi(veri):
    """
    Kurum verisini kullanıcı dostu formata dönüştürür.
    
    Parametreler:
        veri (dict): kurum_alim_satim_verisi() fonksiyonundan dönen veri
    
    Dönen Değer:
        str: Formatlanmış metin
    """
    if "hata" in veri:
        return f"⚠ Hata: {veri['hata']}"
    
    try:
        text = "📊 Kurumsal Hareketler:\n\n"
        
        # Alıcılar
        text += "📈 EN ÇOK ALAN KURUMLAR:\n"
        for i, kurum in enumerate(veri["alici_kurumlar"][:5], 1):  # İlk 5 alıcı
            text += f"{i}. {kurum['kurum']}: {kurum['miktar']} TL\n"
        
        # Satıcılar
        text += "\n📉 EN ÇOK SATAN KURUMLAR:\n"
        for i, kurum in enumerate(veri["satici_kurumlar"][:5], 1):  # İlk 5 satıcı
            text += f"{i}. {kurum['kurum']}: {kurum['miktar']} TL\n"
        
        # Özet bilgiler
        text += f"\n🔍 ÖZET:\n"
        text += f"• Toplam Alım: {veri['alici_toplam']:,.2f} TL\n"
        text += f"• Toplam Satım: {veri['satici_toplam']:,.2f} TL\n"
        text += f"• Net Alım: {veri['net_alim']:+,.2f} TL\n"
        text += f"• Alım/Satım Oranı: {veri['alis_satis_orani']:.2f}\n"
        
        # Yorum
        if veri['net_alim'] > 0:
            text += "\n💡 YORUM: Kurumsal net alım pozitif"
        else:
            text += "\n💡 YORUM: Kurumsal net alım negatif"
            
        return text
    
    except Exception as e:
        return f"Veri formatlanırken hata oluştu: {str(e)}"


# Test kısmı (isteğe bağlı)
if __name__ == "__main__":
    test_hisse = "THYAO"
    print(f"Test verisi için {test_hisse} hissesi çekiliyor...\n")
    
    veri = kurum_alim_satim_verisi(test_hisse)
    print("Ham veri:", veri)
    
    print("\nFormatlanmış veri:")
    print(format_kurum_verisi(veri))