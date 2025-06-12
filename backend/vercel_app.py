"""
Vercel Serverless için optimize edilmiş FastAPI
Production-ready momentum trading signals API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import time
from typing import Dict, List
import os

# Local imports
from forex_data import get_forex_provider
from binance_data import get_binance_provider
from real_strategies import get_real_strategy_manager
from crypto_strategies import get_crypto_strategy_manager
from trade_monitor import get_trade_monitor

app = FastAPI(
    title="Momentum Trading Signals API",
    description="Professional KRO & LMO Trading Strategies with 1.5+ RR",
    version="2.0.0"
)

# CORS middleware for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da specific domain ekle
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global providers (Vercel serverless için cache)
forex_provider = None
binance_provider = None
forex_strategy_manager = None
crypto_strategy_manager = None
trade_monitor = None

def init_providers():
    """Initialize providers lazily"""
    global forex_provider, binance_provider, forex_strategy_manager, crypto_strategy_manager, trade_monitor
    
    if forex_provider is None:
        forex_provider = get_forex_provider()
    
    if binance_provider is None:
        binance_provider = get_binance_provider()
    
    if forex_strategy_manager is None:
        forex_strategy_manager = get_real_strategy_manager(forex_provider)
    
    if crypto_strategy_manager is None:
        crypto_strategy_manager = get_crypto_strategy_manager(binance_provider)
    
    if trade_monitor is None:
        trade_monitor = get_trade_monitor()

@app.get("/")
async def root():
    return {
        "service": "Momentum Trading Signals API",
        "version": "2.0.0",
        "status": "Production Ready",
        "features": ["KRO Strategy", "LMO Strategy", "1.5+ RR Filter", "Real-time Data"]
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "api_version": "2.0.0"
    }

@app.get("/api/forex/signals")
async def get_forex_signals():
    """Get forex trading signals with 1.5+ RR"""
    try:
        init_providers()
        
        forex_symbols = [
            'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 
            'USD/CAD', 'USD/CHF', 'NZD/USD', 'GBP/JPY'
        ]
        
        signals = []
        for symbol in forex_symbols:
            try:
                # Get current price
                current_price = forex_provider.get_current_price(symbol)
                if not current_price:
                    continue
                
                # Get signal
                signal = forex_strategy_manager.get_best_signal(symbol, current_price)
                if signal and signal.get('risk_reward', 0) >= 1.5:
                    signals.append(signal)
                    
            except Exception as e:
                print(f"❌ {symbol} forex signal error: {e}")
                continue
        
        return {
            "status": "success",
            "signals": signals,
            "timestamp": time.time(),
            "total_signals": len(signals)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forex signals error: {str(e)}")

@app.get("/api/crypto/signals")
async def get_crypto_signals():
    """Get crypto trading signals with 1.5+ RR"""
    try:
        init_providers()
        
        crypto_symbols = [
            'BTC/USD', 'ETH/USD', 'SOL/USD', 'ADA/USD',
            'DOT/USD', 'AVAX/USD', 'MATIC/USD', 'LINK/USD'
        ]
        
        signals = []
        for symbol in crypto_symbols:
            try:
                # Get current price from Binance
                current_price = binance_provider.get_current_price(symbol.replace('/', ''))
                if not current_price:
                    continue
                
                # Get signal
                signal = crypto_strategy_manager.get_best_signal(symbol, current_price)
                if signal and signal.get('risk_reward', 0) >= 1.5:
                    signals.append(signal)
                    
            except Exception as e:
                print(f"❌ {symbol} crypto signal error: {e}")
                continue
        
        return {
            "status": "success", 
            "signals": signals,
            "timestamp": time.time(),
            "total_signals": len(signals)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto signals error: {str(e)}")

@app.get("/api/signals/all")
async def get_all_signals():
    """Get all trading signals (forex + crypto) with 1.5+ RR"""
    try:
        # Get both forex and crypto signals concurrently
        forex_response = await get_forex_signals()
        crypto_response = await get_crypto_signals()
        
        all_signals = []
        all_signals.extend(forex_response.get('signals', []))
        all_signals.extend(crypto_response.get('signals', []))
        
        # Sort by reliability score and RR ratio
        all_signals.sort(key=lambda x: (x.get('reliability_score', 0), x.get('risk_reward', 0)), reverse=True)
        
        return {
            "status": "success",
            "signals": all_signals,
            "forex_count": len(forex_response.get('signals', [])),
            "crypto_count": len(crypto_response.get('signals', [])),
            "total_signals": len(all_signals),
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"All signals error: {str(e)}")

@app.get("/api/market/status")
async def get_market_status():
    """Get current market status and prices"""
    try:
        init_providers()
        
        # Sample current prices
        status_data = {}
        
        # Forex majors
        forex_majors = ['EUR/USD', 'GBP/USD', 'USD/JPY']
        status_data['forex'] = {}
        for symbol in forex_majors:
            try:
                price = forex_provider.get_current_price(symbol)
                if price:
                    status_data['forex'][symbol] = price
            except:
                continue
        
        # Crypto majors
        crypto_majors = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        status_data['crypto'] = {}
        for symbol in crypto_majors:
            try:
                price = binance_provider.get_current_price(symbol)
                if price:
                    status_data['crypto'][symbol] = price
            except:
                continue
        
        return {
            "status": "success",
            "market_data": status_data,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market status error: {str(e)}")

# Vercel serverless handler
handler = app 