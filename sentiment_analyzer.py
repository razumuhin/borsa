from transformers import pipeline
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import requests
from bs4 import BeautifulSoup

nltk.download('vader_lexicon')

class NewsAnalyzer:
    def __init__(self):
        self.bert_analyzer = pipeline("sentiment-analysis")
        self.vader_analyzer = SentimentIntensityAnalyzer()

    def get_news(self, hisse_kodu, source='web'):
        """Örnek haber çekme fonksiyonu"""
        if source == 'mock':
            return [f"{hisse_kodu} için olumlu haber", "Piyasa belirsizliği"]
        
        try:
            url = f"https://www.finansweb.com/hisse/{hisse_kodu}"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            return [n.get_text() for n in soup.select('.news-title')[:3]]
        except:
            return ["Haber alınamadı"]

    def analyze(self, hisse_kodu):
        """Haberleri analiz eder"""
        news = self.get_news(hisse_kodu)
        
        bert_results = self.bert_analyzer(news)
        vader_scores = [self.vader_analyzer.polarity_scores(n) for n in news]
        
        return {
            'news': news,
            'bert': bert_results,
            'vader': vader_scores,
            'avg_score': sum(s['compound'] for s in vader_scores)/len(vader_scores)
        }