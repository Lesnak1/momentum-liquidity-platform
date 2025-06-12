"""
Finansal veri API'sinden OHLCV verilerini çeken modül
"""
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.api_key = os.getenv('TWELVE_DATA_API_KEY', 'demo')  # Demo key for testing
        self.base_url = "https://api.twelvedata.com"
        
    def get_ohlcv_data(self, symbol: str, interval: str, outputsize: int = 100) -> pd.DataFrame:
        """
        Belirli sembol için OHLCV verilerini getirir
        
        Args:
            symbol (str): Finansal sembol (örn: XAUUSD, GBPJPY)
            interval (str): Zaman dilimi (15min, 4h, 1day)
            outputsize (int): Getirilecek mum sayısı
            
        Returns:
            pd.DataFrame: OHLCV verileri içeren DataFrame
        """
        try:
            # API parametreleri
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key,
                'format': 'JSON'
            }
            
            # API çağrısı
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Hata kontrolü
            if 'code' in data and data['code'] == 400:
                logger.error(f"API hatası: {data.get('message', 'Bilinmeyen hata')}")
                return pd.DataFrame()
                
            if 'values' not in data:
                logger.warning(f"Veri bulunamadı: {symbol}")
                return pd.DataFrame()
            
            # DataFrame oluştur
            df = pd.DataFrame(data['values'])
            
            # Kolon tiplerini düzenle
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            df = df.sort_index()
            
            # Sayısal kolonları float'a çevir
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"Veri başarıyla alındı: {symbol} - {len(df)} mum")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API bağlantı hatası: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Beklenmeyen hata: {str(e)}")
            return pd.DataFrame()
    
    def test_connection(self) -> bool:
        """
        API bağlantısını test eder
        
        Returns:
            bool: Bağlantı başarılı ise True
        """
        try:
            test_data = self.get_ohlcv_data("EURUSD", "15min", 5)
            if not test_data.empty:
                logger.info("API bağlantısı başarılı!")
                return True
            else:
                logger.warning("API bağlantısı başarısız!")
                return False
        except Exception as e:
            logger.error(f"API test hatası: {str(e)}")
            return False
    
    def get_current_price(self, symbol: str) -> float:
        """
        Sembolün anlık fiyatını getirir
        
        Args:
            symbol (str): Finansal sembol
            
        Returns:
            float: Anlık fiyat
        """
        try:
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(f"{self.base_url}/price", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'price' in data:
                return float(data['price'])
            else:
                logger.warning(f"Anlık fiyat alınamadı: {symbol}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Anlık fiyat hatası: {str(e)}")
            return 0.0

# Test fonksiyonu
if __name__ == "__main__":
    fetcher = DataFetcher()
    
    # Bağlantıyı test et
    fetcher.test_connection()
    
    # Test verisi çek
    test_data = fetcher.get_ohlcv_data("XAUUSD", "15min", 10)
    print(f"Test verisi:\n{test_data.head()}")
    
    # Anlık fiyat
    current_price = fetcher.get_current_price("XAUUSD")
    print(f"XAUUSD anlık fiyat: {current_price}") 