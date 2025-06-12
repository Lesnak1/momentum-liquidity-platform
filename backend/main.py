"""
Momentum & Liquidity Trade Sinyal Platformu - Ana Backend Dosyası
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import uvicorn

from data_fetcher import DataFetcher
from strategy_analyzer import StrategyAnalyzer
from database import DatabaseManager

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_signals.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# FastAPI uygulaması
app = FastAPI(title="Momentum & Liquidity Sinyal Platformu", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme aşamasında
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global değişkenler
data_fetcher = DataFetcher()
strategy_analyzer = StrategyAnalyzer()
db_manager = DatabaseManager()
scheduler = BackgroundScheduler()

# Analiz edilecek pariteler
SYMBOLS = ["XAUUSD", "GBPJPY", "EURCAD", "EURUSD", "GBPUSD"]

@app.on_event("startup")
async def startup_event():
    """Uygulama başlatıldığında çalışacak fonksiyon"""
    logger.info("Momentum & Liquidity Sinyal Platformu başlatılıyor...")
    
    # Veritabanı bağlantısını test et
    db_manager.test_connection()
    
    # Scheduler'ı başlat
    scheduler.add_job(
        func=analyze_all_symbols,
        trigger="interval",
        minutes=15,  # Her 15 dakikada bir analiz
        id='signal_analysis'
    )
    scheduler.start()
    
    logger.info("Platform başarıyla başlatıldı!")

@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapatıldığında çalışacak fonksiyon"""
    scheduler.shutdown()
    logger.info("Platform kapatıldı")

def analyze_all_symbols():
    """Tüm pariteler için sinyal analizi yapar"""
    logger.info("Sinyal analizi başlatılıyor...")
    
    for symbol in SYMBOLS:
        try:
            # 15m ve 4h verilerini çek
            data_15m = data_fetcher.get_ohlcv_data(symbol, "15min", 100)
            data_4h = data_fetcher.get_ohlcv_data(symbol, "4h", 50)
            
            # KRO stratejisini analiz et (15m)
            kro_signal = strategy_analyzer.analyze_kro(data_15m, symbol)
            if kro_signal:
                db_manager.save_signal(kro_signal)
                logger.info(f"KRO sinyali bulundu: {symbol} - {kro_signal['signal_type']}")
            
            # LMO stratejisini analiz et (4h + 15m)
            lmo_signal = strategy_analyzer.analyze_lmo(data_4h, data_15m, symbol)
            if lmo_signal:
                db_manager.save_signal(lmo_signal)
                logger.info(f"LMO sinyali bulundu: {symbol} - {lmo_signal['signal_type']}")
                
        except Exception as e:
            logger.error(f"Hata oluştu {symbol} için: {str(e)}")

@app.get("/")
async def root():
    """Ana endpoint"""
    return {
        "message": "Momentum & Liquidity Sinyal Platformu",
        "version": "1.0.0",
        "status": "Aktif"
    }

@app.get("/status")
async def get_status():
    """Sistem durumu endpoint'i"""
    return {
        "status": "Çalışıyor",
        "last_analysis": datetime.now().isoformat(),
        "analyzed_symbols": SYMBOLS,
        "active_signals_count": db_manager.get_active_signals_count()
    }

@app.get("/signals/{symbol}")
async def get_signals(symbol: str):
    """Belirli parite için sinyalleri getirir"""
    try:
        signals = db_manager.get_signals_by_symbol(symbol.upper(), limit=20)
        return {
            "symbol": symbol.upper(),
            "signals": signals
        }
    except Exception as e:
        logger.error(f"Sinyal getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/active-signals")
async def get_active_signals():
    """Tüm aktif sinyalleri getirir"""
    try:
        active_signals = db_manager.get_active_signals()
        return {
            "active_signals": active_signals,
            "count": len(active_signals)
        }
    except Exception as e:
        logger.error(f"Aktif sinyal getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals/{symbol}/latest")
async def get_latest_signal(symbol: str):
    """Belirli parite için en son sinyali getirir"""
    try:
        latest_signal = db_manager.get_latest_signal(symbol.upper())
        return {
            "symbol": symbol.upper(),
            "latest_signal": latest_signal
        }
    except Exception as e:
        logger.error(f"Son sinyal getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 