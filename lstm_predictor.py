import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import os

class PricePredictor:
    def __init__(self, model_path='models/lstm_model.h5'):
        self.model_path = model_path
        self.scaler = MinMaxScaler()
        
    def create_model(self, data):
        """LSTM modelini oluşturur ve eğitir"""
        # Veri ön işleme
        scaled_data = self.scaler.fit_transform(data)
        
        # Model mimarisi
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(60, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        model.fit(self._prepare_data(scaled_data), epochs=5, batch_size=1)
        
        # Modeli kaydet
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        model.save(self.model_path)
        return model

    def predict(self, historical_data, days=7):
        """Gelecek fiyatları tahmin eder"""
        if not os.path.exists(self.model_path):
            self.create_model(historical_data)
            
        model = load_model(self.model_path)
        scaled_data = self.scaler.transform(historical_data[-60:])
        
        predictions = []
        for _ in range(days):
            x = np.array([scaled_data[-60:]])
            pred = model.predict(x)
            predictions.append(pred[0][0])
            scaled_data = np.append(scaled_data, pred)
        
        return self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

    def _prepare_data(self, data):
        """Eğitim verisini hazırlar"""
        x, y = [], []
        for i in range(60, len(data)):
            x.append(data[i-60:i, 0])
            y.append(data[i, 0])
        return np.array(x), np.array(y)