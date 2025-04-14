from sklearn.ensemble import IsolationForest
import pandas as pd

class AnomalyDetector:
    def __init__(self, contamination=0.05):
        self.model = IsolationForest(
            contamination=contamination, 
            random_state=42
        )
    
    def detect(self, df):
        """DataFrame'deki anomalileri tespit eder"""
        features = self._create_features(df)
        df['anomaly'] = self.model.fit_predict(features)
        return df[df['anomaly'] == -1]
    
    def _create_features(self, df):
        """Analiz için özellikler oluşturur"""
        df = df.copy()
        df['pct_change'] = df['Close'].pct_change()
        df['vol_pct'] = df['Volume'].pct_change()
        df['roll_mean'] = df['Close'].rolling(5).mean()
        df['roll_std'] = df['Close'].rolling(5).std()
        return df.dropna()[['pct_change', 'vol_pct', 'roll_mean', 'roll_std']]