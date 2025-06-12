# -*- coding: utf-8 -*-
"""
Gerçek Trading Signal Server
Forex (ExchangeRate-API) + Crypto (Binance) + Real KRO/LMO Strategies
"""

import json
import time
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Gerçek veri sağlayıcıları ve GERÇEK STRATEJI SİSTEMLERİ
try:
    from forex_data import get_forex_provider
    from binance_data import get_binance_provider
    from crypto_strategies import get_crypto_strategy_manager
    from real_strategies import get_real_strategy_manager  # YENİ GERÇEK STRATEJİLER
    from trade_monitor import get_trade_monitor
    print("✅ Tüm modüller başarıyla yüklendi")
except ImportError as e:
    print(f"❌ Modül yükleme hatası: {e}")
    # Fallback imports
    get_forex_provider = None
    get_binance_provider = None
    get_crypto_strategy_manager = None
    get_real_strategy_manager = None
    get_trade_monitor = None

class TradingSignalHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Global providers'ı başlat
        try:
            if get_forex_provider:
                self.forex_provider = get_forex_provider()
                print("✅ Forex provider aktif")
            else:
                self.forex_provider = None
                
            if get_binance_provider:
                self.binance_provider = get_binance_provider()
                print("✅ Binance provider aktif")
            else:
                self.binance_provider = None
                
            if get_crypto_strategy_manager:
                self.crypto_strategies = get_crypto_strategy_manager(self.binance_provider)
                print("✅ Crypto strategies aktif")
            else:
                self.crypto_strategies = None
                
            if get_real_strategy_manager:
                self.forex_strategies = get_real_strategy_manager(self.forex_provider)
                print("✅ GERÇEK Forex KRO/LMO strategies aktif")
            else:
                self.forex_strategies = None
                
            if get_trade_monitor:
                self.trade_monitor = get_trade_monitor()
                print("✅ Trade monitor aktif")
            else:
                self.trade_monitor = None
        
        except Exception as e:
            print(f"❌ Provider başlatma hatası: {e}")
            self.forex_provider = None
            self.binance_provider = None
            self.crypto_strategies = None
            self.forex_strategies = None
            self.trade_monitor = None
        
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """CORS pre-flight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """GET requests handler"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        path = urlparse(self.path).path
        query_params = parse_qs(urlparse(self.path).query)
        
        try:
            if path == '/signals':
                # Ana signals endpoint - şimdi tamamen gerçek
                response = self.get_real_signals()
                
            elif path == '/crypto-signals':
                # Sadece kripto sinyalleri
                response = self.get_crypto_signals()
                
            elif path == '/forex-signals':
                # Sadece forex sinyalleri
                response = self.get_forex_signals()
                
            elif path == '/trade-statistics':
                # Trade istatistikleri
                response = self.get_trade_statistics()
                
            elif path == '/market-data':
                # Market verileri
                response = self.get_market_data()
                
            elif path == '/crypto-prices':
                # Kripto fiyatları
                response = self.get_crypto_prices()
                
            else:
                response = {'error': 'Endpoint not found'}
                
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Request hatası: {e}")
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def get_real_signals(self):
        """Tüm gerçek sinyalleri getir"""
        all_signals = []
        
        # CRYPTO SİNYALLERİ (Gerçek Binance verisi)
        crypto_signals = self.get_crypto_signals()
        if crypto_signals.get('signals'):
            all_signals.extend(crypto_signals['signals'])
        
        # FOREX SİNYALLERİ (Gerçek ExchangeRate-API verisi)
        forex_signals = self.get_forex_signals()
        if forex_signals.get('signals'):
            all_signals.extend(forex_signals['signals'])
        
        # Güvenilirlik skoruna göre sırala
        all_signals.sort(key=lambda x: x.get('reliability_score', 0), reverse=True)
        
        return {
            'signals': all_signals[:10],  # En iyi 10 sinyal
            'total_count': len(all_signals),
            'crypto_count': len(crypto_signals.get('signals', [])),
            'forex_count': len(forex_signals.get('signals', [])),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'REAL_APIS',
            'sorted_by': 'reliability_score_desc',
            'top_signals_only': True
        }
    
    def get_crypto_signals(self):
        """Gerçek kripto sinyalleri (Binance)"""
        signals = []
        
        try:
            if self.binance_provider and self.crypto_strategies:
                # Gerçek Binance fiyatları al
                crypto_prices = self.binance_provider.get_crypto_prices()
                
                for symbol, price_data in crypto_prices.items():
                    try:
                        current_price = price_data['price']
                        
                        # Her sembol için stratejileri analiz et
                        symbol_signals = self.crypto_strategies.analyze_symbol(symbol, current_price)
                        
                        for signal in symbol_signals:
                            signal['asset_type'] = 'crypto'
                            signal['data_source'] = 'binance'
                            signal['price_timestamp'] = price_data.get('timestamp')
                            signals.append(signal)
                    
                    except Exception as e:
                        print(f"❌ Crypto signal error {symbol}: {e}")
                        continue
            
        except Exception as e:
            print(f"❌ Crypto signals genel hatası: {e}")
        
        # Güvenilirlik skoruna göre sırala
        signals.sort(key=lambda x: x.get('reliability_score', 0), reverse=True)
        
        return {
            'signals': signals,
            'count': len(signals),
            'asset_type': 'crypto',
            'data_source': 'binance',
            'sorted_by': 'reliability_score'
        }
    
    def get_forex_signals(self):
        """Gerçek forex sinyalleri (ExchangeRate-API)"""
        signals = []
        
        try:
            if self.forex_provider and self.forex_strategies:
                # Gerçek forex fiyatları al
                forex_prices = self.forex_provider.get_forex_prices()
                
                for symbol, price_data in forex_prices.items():
                    try:
                        current_price = price_data['price']
                        
                        # Her sembol için stratejileri analiz et
                        symbol_signals = self.forex_strategies.analyze_symbol(symbol, current_price)
                        
                        for signal in symbol_signals:
                            signal['asset_type'] = 'forex'
                            signal['data_source'] = price_data.get('source', 'forex-api')
                            signal['price_timestamp'] = price_data.get('timestamp')
                            signals.append(signal)
                    
                    except Exception as e:
                        print(f"❌ Forex signal error {symbol}: {e}")
                        continue
            
        except Exception as e:
            print(f"❌ Forex signals genel hatası: {e}")
        
        # Güvenilirlik skoruna göre sırala
        signals.sort(key=lambda x: x.get('reliability_score', 0), reverse=True)
        
        return {
            'signals': signals,
            'count': len(signals),
            'asset_type': 'forex',
            'data_source': 'exchangerate-api',
            'sorted_by': 'reliability_score'
        }
    
    def get_trade_statistics(self):
        """
        Trade istatistikleri
        KRİTİK: Her symbol için ayrı başarı oranları dahil
        """
        try:
            if self.trade_monitor:
                general_stats = self.trade_monitor.get_statistics()
                symbol_stats = self.trade_monitor.get_symbol_statistics()  # KRİTİK
                active_trades = self.trade_monitor.get_active_trades()
                recent_history = self.trade_monitor.get_recent_history(5)
                
                return {
                    'general_statistics': general_stats,
                    'symbol_statistics': symbol_stats,  # KRİTİK: Her token için ayrı
                    'active_trades': active_trades,
                    'recent_history': recent_history,
                    'total_active': len(active_trades),
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'real_trades',
                    'per_symbol_performance': True  # Bu özellik aktif
                }
        except Exception as e:
            print(f"❌ Trade statistics hatası: {e}")
        
        # Fallback stats
        return {
            'general_statistics': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pips': 0
            },
            'symbol_statistics': {},  # Boş symbol stats
            'active_trades': [],
            'recent_history': [],
            'timestamp': datetime.now().isoformat(),
            'data_source': 'fallback'
        }
    
    def get_market_data(self):
        """Genel market verileri"""
        market_data = {
            'crypto': {},
            'forex': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Crypto market data
            if self.binance_provider:
                crypto_prices = self.binance_provider.get_crypto_prices()
                market_data['crypto'] = crypto_prices
                market_data['crypto_source'] = 'binance'
        except Exception as e:
            print(f"❌ Crypto market data hatası: {e}")
        
        try:
            # Forex market data
            if self.forex_provider:
                forex_prices = self.forex_provider.get_forex_prices()
                market_data['forex'] = forex_prices
                market_data['forex_source'] = 'exchangerate-api'
                market_data['api_status'] = 'live'  # Forex API aktif
        except Exception as e:
            print(f"❌ Forex market data hatası: {e}")
            market_data['api_status'] = 'error'
        
        return market_data
    
    def get_crypto_prices(self):
        """Kripto fiyatları ve durum bilgisi"""
        try:
            if self.binance_provider:
                crypto_prices = self.binance_provider.get_crypto_prices()
                
                return {
                    'prices': crypto_prices,
                    'api_status': 'live',  # Gerçek API'den geldiği için live
                    'source': 'binance',
                    'timestamp': datetime.now().isoformat(),
                    'count': len(crypto_prices)
                }
            else:
                return {
                    'prices': {},
                    'api_status': 'error',
                    'source': 'none',
                    'timestamp': datetime.now().isoformat(),
                    'count': 0
                }
        except Exception as e:
            print(f"❌ Crypto prices hatası: {e}")
            return {
                'prices': {},
                'api_status': 'error',
                'source': 'error',
                'timestamp': datetime.now().isoformat(),
                'count': 0
            }

    def log_message(self, format, *args):
        """Reduced logging"""
        if 'GET /signals' in format % args:
            print(f"📊 Signal isteği: {datetime.now().strftime('%H:%M:%S')}")
        else:
            pass  # Diğer istekleri logla

def start_server():
    """Server'ı başlat"""
    
    # Providers'ı test et
    print("\n🔄 Providers test ediliyor...")
    
    try:
        if get_forex_provider:
            forex_provider = get_forex_provider()
            forex_test = forex_provider.get_forex_prices()
            print(f"✅ Forex: {len(forex_test)} parite")
        else:
            print("❌ Forex provider yok")
    except Exception as e:
        print(f"❌ Forex test hatası: {e}")
    
    try:
        if get_binance_provider:
            binance_provider = get_binance_provider()
            crypto_test = binance_provider.get_crypto_prices()
            print(f"✅ Binance: {len(crypto_test)} crypto")
        else:
            print("❌ Binance provider yok")
    except Exception as e:
        print(f"❌ Binance test hatası: {e}")
    
    # Trade monitor'ı başlat
    try:
        if get_trade_monitor:
            trade_monitor = get_trade_monitor()
            trade_monitor.start_monitoring()
            print("✅ Trade monitor başlatıldı")
    except Exception as e:
        print(f"❌ Trade monitor hatası: {e}")
    
    # Server'ı başlat
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, TradingSignalHandler)
    
    print(f"\n🚀 Gerçek Veri Trading Server çalışıyor")
    print(f"📍 http://localhost:8000")
    print(f"🔗 Endpoints:")
    print(f"   - /signals (tüm gerçek sinyaller)")
    print(f"   - /crypto-signals (Binance)")
    print(f"   - /forex-signals (ExchangeRate-API)")
    print(f"   - /trade-statistics")
    print(f"   - /market-data")
    print(f"\n⚡ KRO & LMO stratejileri gerçek verilerle aktif")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server durduruldu")
        httpd.server_close()

if __name__ == '__main__':
    start_server() 