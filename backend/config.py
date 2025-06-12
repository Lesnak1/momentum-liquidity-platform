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