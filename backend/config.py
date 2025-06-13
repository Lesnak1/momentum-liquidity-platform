"""
Uygulama konfigürasyon ayarları
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'demo')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/trading_signals')

# Application
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Trading Settings
RISK_REWARD_RATIO = 1.5  # KRO stratejisi için
LMO_RISK_REWARD_RATIO = 3.0  # LMO stratejisi için

# Analysis Settings
ANALYSIS_INTERVAL_MINUTES = 15  # Her 15 dakikada analiz
LOOKBACK_PERIODS_15M = 100  # 15m analiz için geçmiş mum sayısı
LOOKBACK_PERIODS_4H = 50   # 4h analiz için geçmiş mum sayısı

# Symbols to analyze
TRADING_SYMBOLS = ["XAUUSD", "GBPJPY", "EURCAD", "EURUSD", "GBPUSD"]

# Binance API Configuration
class BinanceConfig:
    """Gerçek Binance API konfigürasyonu"""
    
    # API Credentials
    API_KEY = "Z76mhJ8P8IzyfUCjbAV0vA27WedNEox4iHnqhWb7VnWN8bd2yMzxagOwD0OlMIgu"
    SECRET_KEY = "kyKTYcuSJM3GuWxENOWyy9w5Irecd0BE4mNuiXePj9U22URid2TXduXPzU7lkzy2"
    
    # API Settings
    BASE_URL = "https://api.binance.com"
    TESTNET = False
    
    # Rate Limit Ayarları (6000 request weight/minute)
    MAX_REQUESTS_PER_MINUTE = 5000  # Güvenlik marjı
    REQUEST_TIMEOUT = 10  # seconds
    
    # Crypto Pairs - Öncelikli listesi
    PRIORITY_SYMBOLS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 
        'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'LINKUSDT',
        'LTCUSDT', 'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT',
        'FILUSDT', 'TRXUSDT', 'HBARUSDT'
    ]
    
    @classmethod
    def get_api_credentials(cls):
        """API kimlik bilgilerini döndür"""
        return {
            'api_key': cls.API_KEY,
            'secret_key': cls.SECRET_KEY,
            'base_url': cls.BASE_URL,
            'testnet': cls.TESTNET
        }
    
    @classmethod
    def get_rate_limits(cls):
        """Rate limit ayarlarını döndür"""
        return {
            'max_requests_per_minute': cls.MAX_REQUESTS_PER_MINUTE,
            'request_timeout': cls.REQUEST_TIMEOUT
        }

# Export
__all__ = ['BinanceConfig'] 