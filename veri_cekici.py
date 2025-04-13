import requests
from bs4 import BeautifulSoup

def kurum_alim_satim_verisi(hisse_kodu):
    url = f"https://www.gunlukrapor.tk/hisse/{hisse_kodu.upper()}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")

        if len(tables) < 2:
            return "Veri bulunamadı veya tablo yapısı değişti."

        alici_tablosu = tables[0]
        alici_kurumlar = []
        for row in alici_tablosu.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                kurum = cols[0].text.strip()
                miktar = cols[1].text.strip()
                alici_kurumlar.append(f"{kurum}: {miktar}")

        satici_tablosu = tables[1]
        satici_kurumlar = []
        for row in satici_tablosu.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                kurum = cols[0].text.strip()
                miktar = cols[1].text.strip()
                satici_kurumlar.append(f"{kurum}: {miktar}")

        sonuc = "📈 En Çok Alan Kurumlar:\n" + "\n".join(alici_kurumlar)
        sonuc += "\n\n📉 En Çok Satan Kurumlar:\n" + "\n".join(satici_kurumlar)
        return sonuc

    except Exception as e:
        return f"Hata oluştu: {e}"
