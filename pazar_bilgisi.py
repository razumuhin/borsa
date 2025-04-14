import requests
from bs4 import BeautifulSoup

def get_pazar_bilgisi(hisse_kodu):
    try:
        url = f"https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse={hisse_kodu}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Deneme 1: Tüm tabloyu bulup içinde arama yapalım
        table = soup.find('table', {'class': 'table-type1'})
        if table:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2 and 'Pazar' in cells[0].text:
                    return cells[1].text.strip()
        
        # Deneme 2: Başka bir yöntem
        pazar_div = soup.find('div', text='Pazar Bilgisi')
        if pazar_div:
            return pazar_div.find_next_sibling('div').text.strip()
            
        # Deneme 3: Daha genel bir arama
        for element in soup.find_all(text=lambda t: 'Pazar' in str(t)):
            if element.parent.name == 'td':
                return element.find_next('td').text.strip()
                
        return "Bilgi bulunamadı"
        
    except Exception as e:
        print(f"Pazar bilgisi alınırken hata: {e}")
        return "Hata"
