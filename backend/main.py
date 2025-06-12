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

# KRİTİK: SABIT SİNYAL CACHE SİSTEMİ
ACTIVE_SIGNALS_CACHE = {}
SIGNAL_GENERATION_INTERVAL = 300  # 5 dakikada bir yeni sinyal üret
LAST_SIGNAL_GENERATION = 0

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
                
            elif path == '/crypto/signals':
                # Sadece kripto sinyalleri
                response = self.get_crypto_signals()
                
            elif path == '/prices':
                # Market verileri (forex fiyatları)
                response = self.get_market_data()
                
            elif path == '/crypto/prices':
                # Kripto fiyatları
                response = self.get_crypto_prices()
                
            elif path == '/statistics':
                # Trade istatistikleri
                response = self.get_trade_statistics()
                
            else:
                response = {'error': 'Endpoint not found'}
                
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Request hatası: {e}")
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def generate_new_signals_if_needed(self):
        """Sadece gerektiğinde yeni sinyal üret - ENTRY/TP/SL SABİT KALSIN"""
        global ACTIVE_SIGNALS_CACHE, LAST_SIGNAL_GENERATION
        
        current_time = time.time()
        
        # 5 dakikada bir VEYA cache boşsa yeni sinyal üret
        if (current_time - LAST_SIGNAL_GENERATION > SIGNAL_GENERATION_INTERVAL) or len(ACTIVE_SIGNALS_CACHE) == 0:
            
            print(f"🔄 Yeni sinyaller üretiliyor... Son: {datetime.fromtimestamp(LAST_SIGNAL_GENERATION).strftime('%H:%M:%S')}")
            
            # YENİ SİNYALLER ÜRET
            new_signals = {}
            
            # CRYPTO SİNYALLERİ
            try:
                if self.binance_provider and self.crypto_strategies:
                    crypto_prices = self.binance_provider.get_crypto_prices()
                    
                    for symbol, price_data in crypto_prices.items():
                        current_price = price_data['price']
                        
                        # %30 şans ile bu symbol için sinyal üret
                        if random.random() < 0.3:
                            symbol_signals = self.crypto_strategies.analyze_symbol(symbol, current_price)
                            
                            for signal in symbol_signals:
                                signal_id = f"CRYPTO_{symbol}_{int(current_time)}"
                                signal['signal_id'] = signal_id
                                signal['asset_type'] = 'crypto'
                                signal['data_source'] = 'binance'
                                signal['creation_time'] = datetime.now().isoformat()
                                signal['status'] = 'ACTIVE'
                                
                                # SABİT DEĞERLER - BİR DAHA DEĞİŞMEYECEK
                                signal['fixed_entry'] = signal['ideal_entry']
                                signal['fixed_tp'] = signal['take_profit'] 
                                signal['fixed_sl'] = signal['stop_loss']
                                signal['fixed_strategy'] = signal['strategy']
                                signal['fixed_signal_type'] = signal['signal_type']
                                signal['fixed_reliability'] = signal['reliability_score']
                                
                                new_signals[signal_id] = signal
                                
            except Exception as e:
                print(f"❌ Crypto signal generation error: {e}")
            
            # FOREX SİNYALLERİ  
            try:
                if self.forex_provider and self.forex_strategies:
                    forex_prices = self.forex_provider.get_forex_prices()
                    
                    for symbol, price_data in forex_prices.items():
                        current_price = price_data['price']
                        
                        # %25 şans ile bu symbol için sinyal üret
                        if random.random() < 0.25:
                            symbol_signals = self.forex_strategies.analyze_symbol(symbol, current_price)
                            
                            for signal in symbol_signals:
                                signal_id = f"FOREX_{symbol}_{int(current_time)}"
                                signal['signal_id'] = signal_id
                                signal['asset_type'] = 'forex'
                                signal['data_source'] = 'exchangerate-api'
                                signal['creation_time'] = datetime.now().isoformat()
                                signal['status'] = 'ACTIVE'
                                
                                # SABİT DEĞERLER - BİR DAHA DEĞİŞMEYECEK
                                signal['fixed_entry'] = signal['ideal_entry']
                                signal['fixed_tp'] = signal['take_profit']
                                signal['fixed_sl'] = signal['stop_loss'] 
                                signal['fixed_strategy'] = signal['strategy']
                                signal['fixed_signal_type'] = signal['signal_type']
                                signal['fixed_reliability'] = signal['reliability_score']
                                
                                new_signals[signal_id] = signal
                                
            except Exception as e:
                print(f"❌ Forex signal generation error: {e}")
            
            # Cache'i güncelle - ESKİ SİNYALLERİ KORU
            for signal_id, signal in new_signals.items():
                ACTIVE_SIGNALS_CACHE[signal_id] = signal
            
            # Maksimum 10 aktif sinyal tut
            if len(ACTIVE_SIGNALS_CACHE) > 10:
                # En eski sinyalleri sil
                sorted_signals = sorted(ACTIVE_SIGNALS_CACHE.items(), 
                                      key=lambda x: x[1].get('creation_time', ''), 
                                      reverse=True)
                ACTIVE_SIGNALS_CACHE = dict(sorted_signals[:10])
            
            LAST_SIGNAL_GENERATION = current_time
            print(f"✅ {len(new_signals)} yeni sinyal üretildi. Toplam aktif: {len(ACTIVE_SIGNALS_CACHE)}")

    def update_current_prices_only(self):
        """Sadece güncel fiyatları güncelle - ENTRY/TP/SL DOKUNAMİYORUZ"""
        global ACTIVE_SIGNALS_CACHE
        
        completed_trades = []  # Sonuçlanan trade'ler
        
        try:
            # Crypto fiyatları güncelle
            if self.binance_provider:
                crypto_prices = self.binance_provider.get_crypto_prices()
                
                for signal_id, signal in list(ACTIVE_SIGNALS_CACHE.items()):
                    if signal['asset_type'] == 'crypto':
                        symbol = signal['symbol']
                        if symbol in crypto_prices:
                            current_price = crypto_prices[symbol]['price']
                            
                            # SADECE GÜNCEL FİYAT DEĞİŞİR
                            signal['current_price'] = current_price
                            signal['price_update_time'] = datetime.now().isoformat()
                            
                            # TP/SL KONTROLÜ - TRADE SONUÇLANMA
                            trade_result = self.check_trade_completion(signal, current_price)
                            if trade_result:
                                completed_trades.append(trade_result)
                                # Cache'den sil - trade sonuçlandı
                                del ACTIVE_SIGNALS_CACHE[signal_id]
                                print(f"✅ Trade sonuçlandı: {symbol} - {trade_result['result']}")
            
            # Forex fiyatları güncelle  
            if self.forex_provider:
                forex_prices = self.forex_provider.get_forex_prices()
                
                for signal_id, signal in list(ACTIVE_SIGNALS_CACHE.items()):
                    if signal['asset_type'] == 'forex':
                        symbol = signal['symbol']
                        if symbol in forex_prices:
                            current_price = forex_prices[symbol]['price']
                            
                            # SADECE GÜNCEL FİYAT DEĞİŞİR
                            signal['current_price'] = current_price
                            signal['price_update_time'] = datetime.now().isoformat()
                            
                            # TP/SL KONTROLÜ - TRADE SONUÇLANMA
                            trade_result = self.check_trade_completion(signal, current_price)
                            if trade_result:
                                completed_trades.append(trade_result)
                                # Cache'den sil - trade sonuçlandı
                                del ACTIVE_SIGNALS_CACHE[signal_id]
                                print(f"✅ Trade sonuçlandı: {symbol} - {trade_result['result']}")
            
            # Sonuçlanan trade'leri kaydet
            if completed_trades and self.trade_monitor:
                for trade in completed_trades:
                    self.trade_monitor.record_completed_trade(trade)
                    
        except Exception as e:
            print(f"❌ Price update error: {e}")
    
    def check_trade_completion(self, signal, current_price):
        """TP/SL kontrolü ile trade sonuçlanma tespiti"""
        
        entry_price = signal['fixed_entry']
        take_profit = signal['fixed_tp'] 
        stop_loss = signal['fixed_sl']
        signal_type = signal['fixed_signal_type']
        
        # BUY sinyali kontrolü
        if signal_type == 'BUY':
            # TP hit - Kazanç
            if current_price >= take_profit:
                pip_gain = abs(take_profit - entry_price)
                return {
                    'signal_id': signal['signal_id'],
                    'symbol': signal['symbol'],
                    'strategy': signal['fixed_strategy'],
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'result': 'PROFIT',  # KAZANÇ
                    'result_type': 'TP_HIT',
                    'pip_gain': pip_gain,
                    'reliability_score': signal['fixed_reliability'],
                    'entry_time': signal['creation_time'],
                    'exit_time': datetime.now().isoformat(),
                    'asset_type': signal['asset_type']
                }
            
            # SL hit - Kayıp  
            elif current_price <= stop_loss:
                pip_loss = abs(entry_price - stop_loss)
                return {
                    'signal_id': signal['signal_id'],
                    'symbol': signal['symbol'], 
                    'strategy': signal['fixed_strategy'],
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'result': 'LOSS',  # KAYIP
                    'result_type': 'SL_HIT',
                    'pip_loss': pip_loss,
                    'reliability_score': signal['fixed_reliability'],
                    'entry_time': signal['creation_time'],
                    'exit_time': datetime.now().isoformat(),
                    'asset_type': signal['asset_type']
                }
        
        # SAT sinyali kontrolü
        elif signal_type == 'SAT':
            # TP hit - Kazanç (fiyat düştü)
            if current_price <= take_profit:
                pip_gain = abs(entry_price - take_profit)
                return {
                    'signal_id': signal['signal_id'],
                    'symbol': signal['symbol'],
                    'strategy': signal['fixed_strategy'], 
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'result': 'PROFIT',  # KAZANÇ
                    'result_type': 'TP_HIT',
                    'pip_gain': pip_gain,
                    'reliability_score': signal['fixed_reliability'],
                    'entry_time': signal['creation_time'],
                    'exit_time': datetime.now().isoformat(),
                    'asset_type': signal['asset_type']
                }
            
            # SL hit - Kayıp (fiyat yükseldi)
            elif current_price >= stop_loss:
                pip_loss = abs(stop_loss - entry_price)
                return {
                    'signal_id': signal['signal_id'],
                    'symbol': signal['symbol'],
                    'strategy': signal['fixed_strategy'],
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'result': 'LOSS',  # KAYIP
                    'result_type': 'SL_HIT', 
                    'pip_loss': pip_loss,
                    'reliability_score': signal['fixed_reliability'],
                    'entry_time': signal['creation_time'],
                    'exit_time': datetime.now().isoformat(),
                    'asset_type': signal['asset_type']
                }
        
        # Henüz sonuçlanmadı
        return None
    
    def get_real_signals(self):
        """SABİT sinyalleri döndür - Entry/TP/SL asla değişmez"""
        
        # 1. Gerekirse yeni sinyal üret
        self.generate_new_signals_if_needed()
        
        # 2. Sadece current price'ları güncelle
        self.update_current_prices_only()
        
        # 3. Aktif sinyalleri döndür
        active_signals = []
        
        for signal_id, signal in ACTIVE_SIGNALS_CACHE.items():
            # Frontend için uygun format
            formatted_signal = {
                'signal_id': signal_id,
                'symbol': signal['symbol'],
                'strategy': signal['fixed_strategy'],
                'signal_type': signal['fixed_signal_type'],
                'timeframe': signal.get('timeframe', '15m'),
                
                # SABİT DEĞERLER - ASLA DEĞİŞMEZ
                'ideal_entry': signal['fixed_entry'],
                'take_profit': signal['fixed_tp'],
                'stop_loss': signal['fixed_sl'],
                'reliability_score': signal['fixed_reliability'],
                
                # SADECE BU DEĞİŞİR
                'current_price': signal.get('current_price', signal['fixed_entry']),
                
                'status': 'ACTIVE',
                'creation_time': signal['creation_time'],
                'price_update_time': signal.get('price_update_time', signal['creation_time']),
                'asset_type': signal['asset_type'],
                'data_source': signal['data_source']
            }
            
            active_signals.append(formatted_signal)
        
        # Güvenilirlik skoruna göre sırala
        active_signals.sort(key=lambda x: x['reliability_score'], reverse=True)
        
        return {
            'signals': active_signals,
            'total_count': len(active_signals),
            'cache_info': {
                'last_generation': datetime.fromtimestamp(LAST_SIGNAL_GENERATION).isoformat(),
                'next_generation_in': max(0, SIGNAL_GENERATION_INTERVAL - (time.time() - LAST_SIGNAL_GENERATION)),
                'fixed_signals': True,
                'only_prices_update': True
            },
            'timestamp': datetime.now().isoformat(),
            'data_source': 'CACHED_FIXED_SIGNALS'
        }

    def get_crypto_signals(self):
        """Crypto sinyalleri - cache'den al"""
        self.generate_new_signals_if_needed()
        self.update_current_prices_only()
        
        crypto_signals = [signal for signal in ACTIVE_SIGNALS_CACHE.values() 
                         if signal['asset_type'] == 'crypto']
        
        return {
            'signals': crypto_signals,
            'count': len(crypto_signals),
            'asset_type': 'crypto',
            'data_source': 'cached_binance'
        }
    
    def get_forex_signals(self):
        """Forex sinyalleri - cache'den al"""
        self.generate_new_signals_if_needed() 
        self.update_current_prices_only()
        
        forex_signals = [signal for signal in ACTIVE_SIGNALS_CACHE.values()
                        if signal['asset_type'] == 'forex']
        
        return {
            'signals': forex_signals,
            'count': len(forex_signals),
            'asset_type': 'forex', 
            'data_source': 'cached_exchangerate'
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
        """Market verilerini döndür (Forex fiyatları) - Frontend formatında"""
        try:
            if self.forex_provider:
                forex_data = self.forex_provider.get_forex_prices()
                
                return {
                    'prices': forex_data,
                    'last_update': datetime.now().isoformat(),
                    'api_status': 'live',
                    'data_source': 'exchangerate-api'
                }
            else:
                # Fallback data
                base_time = datetime.now().isoformat()
                return {
                    'prices': {
                        "XAUUSD": {"price": 2018.45 + (random.random() - 0.5) * 20, "timestamp": base_time},
                        "GBPJPY": {"price": 198.450 + (random.random() - 0.5) * 2, "timestamp": base_time},
                        "EURCAD": {"price": 1.4825 + (random.random() - 0.5) * 0.02, "timestamp": base_time},
                        "EURUSD": {"price": 1.0892 + (random.random() - 0.5) * 0.02, "timestamp": base_time},
                        "GBPUSD": {"price": 1.2634 + (random.random() - 0.5) * 0.02, "timestamp": base_time}
                    },
                    'last_update': base_time,
                    'api_status': 'fallback'
                }
                
        except Exception as e:
            print(f"❌ Market data error: {e}")
            return {
                'error': str(e),
                'api_status': 'error'
            }
    
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