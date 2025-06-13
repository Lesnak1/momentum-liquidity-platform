#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Production Trading Signal Server
FTMO Funded Trading için 7/24 Sunucu
Auto-Recovery + Logging + Error Handling
"""

import json
import time
import logging
import signal
import sys
import os
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import requests
from pathlib import Path

# Production logging setup
def setup_production_logging():
    """Production logging kurulumu"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler
    file_handler = logging.FileHandler(
        log_dir / f"trading_server_{datetime.now().strftime('%Y%m%d')}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Console handler  
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Logger setup
    logger = logging.getLogger('TradingServer')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Global logger
production_logger = setup_production_logging()

# Production imports with error handling
try:
    from forex_data import get_forex_provider
    from binance_data import get_binance_provider
    from crypto_strategies import get_crypto_strategy_manager
    from real_strategies import get_real_strategy_manager
    from trade_monitor import get_trade_monitor
    from lot_calculator import get_ftmo_calculator
    production_logger.info("✅ Tüm modüller başarıyla yüklendi - PRODUCTION MODE")
except ImportError as e:
    production_logger.error(f"❌ Kritik modül yükleme hatası: {e}")
    sys.exit(1)

# Production cache sistemi
PRODUCTION_SIGNALS_CACHE = {}
SIGNAL_GENERATION_INTERVAL = 180  # 3 dakikada bir (production için daha sık)
LAST_SIGNAL_GENERATION = 0
HEALTH_CHECK_INTERVAL = 60  # 1 dakikada bir health check
LAST_HEALTH_CHECK = 0

# Auto-recovery settings
MAX_CONSECUTIVE_ERRORS = 5
CONSECUTIVE_ERRORS = 0
RECOVERY_DELAY = 30  # 30 saniye recovery delay

class ProductionTradingHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Initialize providers with auto-recovery
        self.initialize_providers()
        super().__init__(*args, **kwargs)
    
    def initialize_providers(self):
        """Provider'ları güvenli şekilde başlat"""
        try:
            self.forex_provider = get_forex_provider()
            self.binance_provider = get_binance_provider()
            self.crypto_strategies = get_crypto_strategy_manager(self.binance_provider)
            self.forex_strategies = get_real_strategy_manager(self.forex_provider)
            self.trade_monitor = get_trade_monitor()
            self.ftmo_calculator = get_ftmo_calculator()
            
            production_logger.info("✅ Tüm provider'lar başarıyla başlatıldı")
            
        except Exception as e:
            production_logger.error(f"❌ Provider başlatma hatası: {e}")
            # Fallback mode
            self.forex_provider = None
            self.binance_provider = None
            self.crypto_strategies = None
            self.forex_strategies = None
            self.trade_monitor = None
            self.ftmo_calculator = None
    
    def do_OPTIONS(self):
        """CORS pre-flight"""
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        except Exception as e:
            production_logger.error(f"OPTIONS request error: {e}")
    
    def do_GET(self):
        """Production GET handler with error recovery"""
        global CONSECUTIVE_ERRORS
        
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            path = urlparse(self.path).path
            
            # Health check endpoint
            if path == '/health':
                response = self.get_health_status()
            elif path == '/signals':
                response = self.get_production_signals()
            elif path == '/crypto-signals':
                response = self.get_crypto_signals()
            elif path == '/forex-signals':
                response = self.get_forex_signals()
            elif path == '/statistics':
                response = self.get_trade_statistics()
            elif path == '/market-data':
                response = self.get_market_data()
            elif path == '/crypto/prices':
                response = self.get_crypto_prices()
            elif path == '/crypto/signals':
                response = self.get_crypto_signals()
            else:
                response = {'error': 'Endpoint not found'}
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
            # Reset error counter on success
            CONSECUTIVE_ERRORS = 0
            
        except Exception as e:
            CONSECUTIVE_ERRORS += 1
            production_logger.error(f"❌ Request handling error (#{CONSECUTIVE_ERRORS}): {e}")
            
            try:
                error_response = {
                    'error': str(e),
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'consecutive_errors': CONSECUTIVE_ERRORS
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
            except:
                pass  # Son çare - sessizce geç
            
            # Auto-recovery trigger
            if CONSECUTIVE_ERRORS >= MAX_CONSECUTIVE_ERRORS:
                production_logger.warning("🔄 Auto-recovery triggered - reinitializing providers")
                self.trigger_auto_recovery()
    
    def trigger_auto_recovery(self):
        """Auto-recovery mechanism"""
        global CONSECUTIVE_ERRORS
        
        try:
            production_logger.info("🔄 Starting auto-recovery process...")
            time.sleep(RECOVERY_DELAY)
            
            # Reinitialize providers
            self.initialize_providers()
            
            # Reset error counter
            CONSECUTIVE_ERRORS = 0
            
            production_logger.info("✅ Auto-recovery completed successfully")
            
        except Exception as e:
            production_logger.error(f"❌ Auto-recovery failed: {e}")
    
    def get_health_status(self):
        """System health check"""
        global LAST_HEALTH_CHECK
        
        current_time = time.time()
        LAST_HEALTH_CHECK = current_time
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': current_time,
            'consecutive_errors': CONSECUTIVE_ERRORS,
            'signal_cache_size': len(PRODUCTION_SIGNALS_CACHE),
            'last_signal_generation': datetime.fromtimestamp(LAST_SIGNAL_GENERATION).isoformat() if LAST_SIGNAL_GENERATION > 0 else 'never',
            'providers': {
                'forex': self.forex_provider is not None,
                'binance': self.binance_provider is not None,
                'crypto_strategies': self.crypto_strategies is not None,
                'forex_strategies': self.forex_strategies is not None,
                'trade_monitor': self.trade_monitor is not None,
                'ftmo_calculator': self.ftmo_calculator is not None
            }
        }
        
        # Check if any provider is down
        if not all(health_status['providers'].values()):
            health_status['status'] = 'degraded'
        
        if CONSECUTIVE_ERRORS > 0:
            health_status['status'] = 'warning'
        
        if CONSECUTIVE_ERRORS >= MAX_CONSECUTIVE_ERRORS:
            health_status['status'] = 'critical'
        
        return health_status
    
    def get_production_signals(self):
        """Production signal generation with auto-recovery"""
        try:
            # Generate new signals if needed
            self.generate_production_signals()
            
            # Update current prices
            self.update_production_prices()
            
            # Get filtered signals (reliability > 6)
            filtered_signals = []
            for signal_id, signal in PRODUCTION_SIGNALS_CACHE.items():
                if signal.get('fixed_reliability', 0) >= 6:
                    filtered_signals.append(signal)
            
            return {
                'signals': filtered_signals,
                'total_signals': len(PRODUCTION_SIGNALS_CACHE),
                'filtered_signals': len(filtered_signals),
                'last_update': datetime.now().isoformat(),
                'api_status': 'live',
                'server_mode': 'production'
            }
            
        except Exception as e:
            production_logger.error(f"Production signals error: {e}")
            return {
                'signals': [],
                'error': str(e),
                'api_status': 'error',
                'server_mode': 'production'
            }
    
    def generate_production_signals(self):
        """Production sinyal üretimi - GERÇEK STRATEJI"""
        global PRODUCTION_SIGNALS_CACHE, LAST_SIGNAL_GENERATION
        
        current_time = time.time()
        
        if (current_time - LAST_SIGNAL_GENERATION > SIGNAL_GENERATION_INTERVAL):
            production_logger.info("🔄 Production signal generation started")
            
            new_signals = {}
            
            # CRYPTO SİNYALLERİ
            try:
                if self.binance_provider and self.crypto_strategies:
                    crypto_prices = self.binance_provider.get_crypto_prices()
                    
                    for symbol, price_data in crypto_prices.items():
                        current_price = price_data['price']
                        
                        # HER SYMBOL'Ü ANALİZ ET (random değil)
                        symbol_signals = self.crypto_strategies.analyze_symbol(symbol, current_price)
                        
                        for signal in symbol_signals:
                            # Sadece güvenilirlik > 4 olan sinyalleri al
                            if signal.get('reliability_score', 0) >= 4:
                                signal_id = f"CRYPTO_{symbol}_{int(current_time)}"
                                signal['signal_id'] = signal_id
                                signal['asset_type'] = 'crypto'
                                signal['data_source'] = 'binance'
                                signal['creation_time'] = datetime.now().isoformat()
                                signal['status'] = 'ACTIVE'
                                
                                # SABİT DEĞERLER
                                signal['fixed_entry'] = signal['ideal_entry']
                                signal['fixed_tp'] = signal['take_profit']
                                signal['fixed_sl'] = signal['stop_loss']
                                signal['fixed_strategy'] = signal['strategy']
                                signal['fixed_signal_type'] = signal['signal_type']
                                signal['fixed_reliability'] = signal['reliability_score']
                                
                                # FTMO LOT SIZE HESAPLAMA
                                if self.ftmo_calculator:
                                    lot_calc = self.ftmo_calculator.calculate_position_size_for_signal(signal)
                                    signal['ftmo_lot_size'] = lot_calc.get('lot_size', 0.01)
                                    signal['ftmo_risk_amount'] = lot_calc.get('risk_amount_used', 100)
                                    signal['ftmo_risk_percentage'] = lot_calc.get('risk_percentage', 1.0)
                                    signal['ftmo_recommendation'] = lot_calc.get('recommendation', 'Hesaplanamadı')
                                    signal['ftmo_compliant'] = lot_calc.get('ftmo_compliant', False)
                                    signal['pip_distance'] = lot_calc.get('pip_distance', 0)
                                    signal['potential_loss'] = lot_calc.get('potential_loss', 0)
                                
                                new_signals[signal_id] = signal
                                
            except Exception as e:
                production_logger.error(f"Crypto signal generation error: {e}")
            
            # FOREX SİNYALLERİ
            try:
                if self.forex_provider and self.forex_strategies:
                    forex_prices = self.forex_provider.get_forex_prices()
                    
                    for symbol, price_data in forex_prices.items():
                        current_price = price_data['price']
                        
                        # HER SYMBOL'Ü ANALİZ ET (random değil)
                        symbol_signals = self.forex_strategies.analyze_symbol(symbol, current_price)
                        
                        for signal in symbol_signals:
                            # Sadece güvenilirlik > 4 olan sinyalleri al
                            if signal.get('reliability_score', 0) >= 4:
                                signal_id = f"FOREX_{symbol}_{int(current_time)}"
                                signal['signal_id'] = signal_id
                                signal['asset_type'] = 'forex'
                                signal['data_source'] = 'exchangerate-api'
                                signal['creation_time'] = datetime.now().isoformat()
                                signal['status'] = 'ACTIVE'
                                
                                # SABİT DEĞERLER
                                signal['fixed_entry'] = signal['ideal_entry']
                                signal['fixed_tp'] = signal['take_profit']
                                signal['fixed_sl'] = signal['stop_loss']
                                signal['fixed_strategy'] = signal['strategy']
                                signal['fixed_signal_type'] = signal['signal_type']
                                signal['fixed_reliability'] = signal['reliability_score']
                                
                                # FTMO LOT SIZE HESAPLAMA
                                if self.ftmo_calculator:
                                    lot_calc = self.ftmo_calculator.calculate_position_size_for_signal(signal)
                                    signal['ftmo_lot_size'] = lot_calc.get('lot_size', 0.01)
                                    signal['ftmo_risk_amount'] = lot_calc.get('risk_amount_used', 100)
                                    signal['ftmo_risk_percentage'] = lot_calc.get('risk_percentage', 1.0)
                                    signal['ftmo_recommendation'] = lot_calc.get('recommendation', 'Hesaplanamadı')
                                    signal['ftmo_compliant'] = lot_calc.get('ftmo_compliant', False)
                                    signal['pip_distance'] = lot_calc.get('pip_distance', 0)
                                    signal['potential_loss'] = lot_calc.get('potential_loss', 0)
                                
                                new_signals[signal_id] = signal
                                
            except Exception as e:
                production_logger.error(f"Forex signal generation error: {e}")
            
            # Cache'i güncelle
            for signal_id, signal in new_signals.items():
                PRODUCTION_SIGNALS_CACHE[signal_id] = signal
            
            # Maksimum 15 aktif sinyal tut (production için daha fazla)
            if len(PRODUCTION_SIGNALS_CACHE) > 15:
                sorted_signals = sorted(PRODUCTION_SIGNALS_CACHE.items(),
                                      key=lambda x: x[1].get('creation_time', ''),
                                      reverse=True)
                PRODUCTION_SIGNALS_CACHE = dict(sorted_signals[:15])
            
            LAST_SIGNAL_GENERATION = current_time
            production_logger.info(f"✅ {len(new_signals)} yeni sinyal üretildi. Toplam: {len(PRODUCTION_SIGNALS_CACHE)}")
    
    def update_production_prices(self):
        """Production fiyat güncelleme"""
        global PRODUCTION_SIGNALS_CACHE
        
        completed_trades = []
        
        try:
            # Crypto fiyatları
            if self.binance_provider:
                crypto_prices = self.binance_provider.get_crypto_prices()
                
                for signal_id, signal in list(PRODUCTION_SIGNALS_CACHE.items()):
                    if signal['asset_type'] == 'crypto':
                        symbol = signal['symbol']
                        if symbol in crypto_prices:
                            current_price = crypto_prices[symbol]['price']
                            signal['current_price'] = current_price
                            signal['price_update_time'] = datetime.now().isoformat()
                            
                            # TP/SL kontrolü
                            trade_result = self.check_trade_completion(signal, current_price)
                            if trade_result:
                                completed_trades.append(trade_result)
                                del PRODUCTION_SIGNALS_CACHE[signal_id]
                                production_logger.info(f"✅ Trade completed: {symbol} - {trade_result['result']}")
            
            # Forex fiyatları
            if self.forex_provider:
                forex_prices = self.forex_provider.get_forex_prices()
                
                for signal_id, signal in list(PRODUCTION_SIGNALS_CACHE.items()):
                    if signal['asset_type'] == 'forex':
                        symbol = signal['symbol']
                        if symbol in forex_prices:
                            current_price = forex_prices[symbol]['price']
                            signal['current_price'] = current_price
                            signal['price_update_time'] = datetime.now().isoformat()
                            
                            # TP/SL kontrolü
                            trade_result = self.check_trade_completion(signal, current_price)
                            if trade_result:
                                completed_trades.append(trade_result)
                                del PRODUCTION_SIGNALS_CACHE[signal_id]
                                production_logger.info(f"✅ Trade completed: {symbol} - {trade_result['result']}")
            
            # Sonuçlanan trade'leri kaydet
            if completed_trades and self.trade_monitor:
                for trade in completed_trades:
                    self.trade_monitor.record_completed_trade(trade)
                    
        except Exception as e:
            production_logger.error(f"Price update error: {e}")
    
    def check_trade_completion(self, signal, current_price):
        """TP/SL kontrolü"""
        entry_price = signal['fixed_entry']
        take_profit = signal['fixed_tp']
        stop_loss = signal['fixed_sl']
        signal_type = signal['fixed_signal_type']
        
        if signal_type == 'BUY':
            if current_price >= take_profit:
                return {
                    'signal_id': signal['signal_id'],
                    'symbol': signal['symbol'],
                    'strategy': signal['fixed_strategy'],
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'result': 'PROFIT',
                    'result_type': 'TP_HIT',
                    'pip_gain': abs(take_profit - entry_price),
                    'reliability_score': signal['fixed_reliability'],
                    'entry_time': signal['creation_time'],
                    'exit_time': datetime.now().isoformat(),
                    'asset_type': signal['asset_type']
                }
            elif current_price <= stop_loss:
                return {
                    'signal_id': signal['signal_id'],
                    'symbol': signal['symbol'],
                    'strategy': signal['fixed_strategy'],
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'result': 'LOSS',
                    'result_type': 'SL_HIT',
                    'pip_loss': abs(entry_price - stop_loss),
                    'reliability_score': signal['fixed_reliability'],
                    'entry_time': signal['creation_time'],
                    'exit_time': datetime.now().isoformat(),
                    'asset_type': signal['asset_type']
                }
        
        elif signal_type == 'SELL':
            if current_price <= take_profit:
                return {
                    'signal_id': signal['signal_id'],
                    'symbol': signal['symbol'],
                    'strategy': signal['fixed_strategy'],
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'result': 'PROFIT',
                    'result_type': 'TP_HIT',
                    'pip_gain': abs(entry_price - take_profit),
                    'reliability_score': signal['fixed_reliability'],
                    'entry_time': signal['creation_time'],
                    'exit_time': datetime.now().isoformat(),
                    'asset_type': signal['asset_type']
                }
            elif current_price >= stop_loss:
                return {
                    'signal_id': signal['signal_id'],
                    'symbol': signal['symbol'],
                    'strategy': signal['fixed_strategy'],
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'result': 'LOSS',
                    'result_type': 'SL_HIT',
                    'pip_loss': abs(stop_loss - entry_price),
                    'reliability_score': signal['fixed_reliability'],
                    'entry_time': signal['creation_time'],
                    'exit_time': datetime.now().isoformat(),
                    'asset_type': signal['asset_type']
                }
        
        return None
    
    def get_crypto_signals(self):
        """Crypto sinyalleri"""
        try:
            crypto_signals = [signal for signal in PRODUCTION_SIGNALS_CACHE.values() 
                            if signal['asset_type'] == 'crypto' and signal.get('fixed_reliability', 0) >= 6]
            
            return {
                'signals': crypto_signals,
                'total': len(crypto_signals),
                'api_status': 'live'
            }
        except Exception as e:
            production_logger.error(f"Crypto signals error: {e}")
            return {'signals': [], 'error': str(e)}
    
    def get_forex_signals(self):
        """Forex sinyalleri"""
        try:
            forex_signals = [signal for signal in PRODUCTION_SIGNALS_CACHE.values() 
                           if signal['asset_type'] == 'forex' and signal.get('fixed_reliability', 0) >= 6]
            
            return {
                'signals': forex_signals,
                'total': len(forex_signals),
                'api_status': 'live'
            }
        except Exception as e:
            production_logger.error(f"Forex signals error: {e}")
            return {'signals': [], 'error': str(e)}
    
    def get_trade_statistics(self):
        """Trade istatistikleri"""
        try:
            if self.trade_monitor:
                stats = self.trade_monitor.get_statistics()
                return stats
            else:
                return {'error': 'Trade monitor unavailable'}
        except Exception as e:
            production_logger.error(f"Statistics error: {e}")
            return {'error': str(e)}
    
    def get_market_data(self):
        """Market verileri"""
        try:
            market_data = {}
            
            if self.forex_provider:
                market_data['forex'] = self.forex_provider.get_forex_prices()
            
            if self.binance_provider:
                market_data['crypto'] = self.binance_provider.get_crypto_prices()
            
            return market_data
        except Exception as e:
            production_logger.error(f"Market data error: {e}")
            return {'error': str(e)}
    
    def get_crypto_prices(self):
        """Crypto fiyatları"""
        try:
            if self.binance_provider:
                prices = self.binance_provider.get_crypto_prices()
                return {
                    'prices': prices,
                    'api_status': 'live',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'error': 'Binance provider unavailable'}
        except Exception as e:
            production_logger.error(f"Crypto prices error: {e}")
            return {'error': str(e)}
    
    def log_message(self, format, *args):
        """Suppress default server logging"""
        pass

def signal_handler(signum, frame):
    """Graceful shutdown handler"""
    production_logger.info("🛑 Production server shutting down gracefully...")
    sys.exit(0)

def start_production_server():
    """Production server başlatma"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server = HTTPServer(('0.0.0.0', 8000), ProductionTradingHandler)
    
    production_logger.info("🚀 PRODUCTION Trading Signal Server started")
    production_logger.info("🌐 Server: http://0.0.0.0:8000")
    production_logger.info("💰 FTMO Mode: 10K Account Lot Calculator Active")
    production_logger.info("🔧 Features: Auto-Recovery, Error Handling, Logging")
    production_logger.info("⏰ Signal Interval: 3 minutes")
    production_logger.info("📊 Health Check: /health endpoint")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        production_logger.info("🛑 Server interrupted by user")
    except Exception as e:
        production_logger.error(f"❌ Server error: {e}")
    finally:
        server.server_close()
        production_logger.info("✅ Production server stopped")

if __name__ == '__main__':
    start_production_server() 