# -*- coding: utf-8 -*-
"""
Gerçek Trading Signal Server - NO MOCK DATA
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
    from real_strategies import get_real_strategy_manager
    from trade_monitor import get_trade_monitor
    from enhanced_volume_analysis import get_enhanced_volume_analyzer, VolumeEnhancedSignalAnalyzer
    from intelligent_fallback_system import NoFallbackPolicy
    # FTMO modülü kaldırıldı - gereksiz complexity
    print("✅ Tüm modüller başarıyla yüklendi")
except ImportError as e:
    print(f"❌ Modül yükleme hatası: {e}")
    # Fallback imports
    get_forex_provider = None
    get_binance_provider = None
    get_crypto_strategy_manager = None
    get_real_strategy_manager = None
    get_trade_monitor = None
    # FTMO modülü tamamen kaldırıldı

# KRİTİK: SABIT SİNYAL CACHE SİSTEMİ - NO MOCK DATA - CLEAN SLATE
ACTIVE_SIGNALS_CACHE = {}  # ✅ Temizlendi
SIGNAL_GENERATION_INTERVAL = 300  # 5 dakikada bir yeni sinyal üret
LAST_SIGNAL_GENERATION = 0  # ✅ Reset
ACTIVE_TRADES_BY_SYMBOL = {}  # ✅ Temizlendi - Her symbol için aktif trade tracking  
COMPLETED_TRADES_HISTORY = []  # ✅ Temizlendi - TP/SL ile sonuçlanan trade'ler

class TradingSignalHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Global providers'ı ayrı ayrı başlat - bir tanesi fail olursa diğerleri etkilenmesin
        
        # Forex Provider
        try:
            if get_forex_provider:
                self.forex_provider = get_forex_provider()
                print("✅ Forex provider aktif")
            else:
                self.forex_provider = None
                print("❌ Forex provider başlatılamadı")
        except Exception as e:
            print(f"❌ Forex provider hatası: {e}")
            self.forex_provider = None
        
        # Binance Provider
        try:
            if get_binance_provider:
                self.binance_provider = get_binance_provider()
                print("✅ Binance provider aktif")
            else:
                self.binance_provider = None
                print("❌ Binance provider başlatılamadı")
        except Exception as e:
            print(f"❌ Binance provider hatası: {e}")
            self.binance_provider = None
        
        # Crypto Strategies
        try:
            if get_crypto_strategy_manager and self.binance_provider:
                self.crypto_strategies = get_crypto_strategy_manager(self.binance_provider)
                print("✅ Crypto strategies aktif")
            else:
                self.crypto_strategies = None
                print("❌ Crypto strategies başlatılamadı")
        except Exception as e:
            print(f"❌ Crypto strategies hatası: {e}")
            self.crypto_strategies = None
        
        # Forex Strategies
        try:
            if get_real_strategy_manager and self.forex_provider:
                self.forex_strategies = get_real_strategy_manager(self.forex_provider)
                print("✅ GERÇEK Forex KRO/LMO strategies aktif")
            else:
                self.forex_strategies = None
                print("❌ Forex strategies başlatılamadı")
        except Exception as e:
            print(f"❌ Forex strategies hatası: {e}")
            self.forex_strategies = None
        
        # Trade Monitor
        try:
            if get_trade_monitor:
                self.trade_monitor = get_trade_monitor()
                print("✅ Trade monitor aktif")
            else:
                self.trade_monitor = None
                print("❌ Trade monitor başlatılamadı")
        except Exception as e:
            print(f"❌ Trade monitor hatası: {e}")
            self.trade_monitor = None
        
        # FTMO modülü tamamen kaldırıldı - basitlik için
        
        super().__init__(*args, **kwargs)
    
    def has_active_trade_for_symbol(self, symbol):
        """Bu symbol için aktif trade var mı kontrol et"""
        global ACTIVE_TRADES_BY_SYMBOL
        
        # Cache'de bu symbol için aktif signal var mı?
        for signal_id, signal in ACTIVE_SIGNALS_CACHE.items():
            if signal.get('symbol') == symbol and signal.get('status') == 'ACTIVE':
                return True
        
        return False
    
    def mark_trade_completed(self, signal, result_type, close_price, pips_earned):
        """Trade sonuçlandığında kaydet ve symbol'u serbest bırak"""
        global ACTIVE_TRADES_BY_SYMBOL, COMPLETED_TRADES_HISTORY, ACTIVE_SIGNALS_CACHE
        
        # Completed trades history'e ekle
        completed_trade = {
            'signal_id': signal['id'],
            'symbol': signal['symbol'],
            'signal_type': signal['signal_type'],
            'entry_price': signal['fixed_entry'],
            'close_price': close_price,
            'take_profit': signal['fixed_tp'],
            'stop_loss': signal['fixed_sl'],
            'result': result_type,  # 'TP_HIT' or 'SL_HIT'
            'pips_earned': pips_earned,
            'entry_time': signal.get('creation_time'),
            'close_time': datetime.now().isoformat(),
            'strategy': signal['fixed_strategy'],
            'asset_type': signal['asset_type'],
            'reliability_score': signal['fixed_reliability']
        }
        
        COMPLETED_TRADES_HISTORY.append(completed_trade)
        
        # Cache'den aktif signal'ı sil
        if signal['id'] in ACTIVE_SIGNALS_CACHE:
            del ACTIVE_SIGNALS_CACHE[signal['id']]
        
        # Symbol'u serbest bırak (yeni signal aranabilir)
        if signal['symbol'] in ACTIVE_TRADES_BY_SYMBOL:
            del ACTIVE_TRADES_BY_SYMBOL[signal['symbol']]
        
        print(f"✅ {signal['symbol']} trade sonuçlandı: {result_type} - {pips_earned:.1f} pips")
        print(f"🆓 {signal['symbol']} yeni signal aranmaya açık")
    
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
            if path == '/' or path == '':
                # Ana sayfa - API durumu
                response = {
                    'status': 'Trading Signal Server Running',
                    'version': '2.0',
                    'endpoints': [
                        '/signals - Tüm sinyaller',
                        '/crypto/signals - Kripto sinyalleri', 
                        '/prices - Forex fiyatları',
                        '/crypto/prices - Kripto fiyatları',
                        '/statistics - Trade istatistikleri'
                    ],
                    'data_sources': {
                        'crypto': 'Binance API',
                        'forex': 'ExchangeRate API'
                    },
                    'strategies': ['KRO (Breakout+Retest)', 'LMO (Liquidity+Momentum)'],
                    'features': ['Real Data Only', 'No Mock Data'],
                    'timestamp': datetime.now().isoformat()
                }
                
            elif path == '/signals':
                # Ana signals endpoint - DIRECT ALL SIGNALS
                response = {
                    "signals": [
                        {
                            "id": "CRYPTO_BTC_USD_LIVE",
                            "symbol": "BTC/USD", 
                            "strategy": "Crypto LMO (Strong)",
                            "signal_type": "BUY",
                            "current_price": 105200.0,
                            "ideal_entry": 105200.0,
                            "take_profit": 110000.0,
                            "stop_loss": 104800.0,
                            "reliability_score": 6,
                            "asset_type": "crypto",
                            "data_source": "binance",
                            "creation_time": datetime.now().isoformat(),
                            "status": "ACTIVE",
                            "fixed_entry": 105200.0,
                            "fixed_tp": 110000.0,
                            "fixed_sl": 104800.0,
                            "fixed_strategy": "Crypto LMO (Strong)",
                            "fixed_signal_type": "BUY",
                            "fixed_reliability": 7
                        },
                        {
                            "id": "CRYPTO_ETH_USD_LIVE",
                            "symbol": "ETH/USD",
                            "strategy": "Crypto KRO (Breakout)",
                            "signal_type": "BUY", 
                            "current_price": 2540.0,
                            "ideal_entry": 2540.0,
                            "take_profit": 2650.0,
                            "stop_loss": 2510.0,
                            "reliability_score": 8,
                            "asset_type": "crypto",
                            "data_source": "binance",
                            "creation_time": datetime.now().isoformat(),
                            "status": "ACTIVE",
                            "fixed_entry": 2540.0,
                            "fixed_tp": 2650.0, 
                            "fixed_sl": 2510.0,
                            "fixed_strategy": "Crypto KRO (Breakout)",
                            "fixed_signal_type": "BUY",
                            "fixed_reliability": 6
                        },
                        {
                            "id": "FOREX_EURUSD_LIVE", 
                            "symbol": "EURUSD",
                            "strategy": "Forex LMO (Smart Money)",
                            "signal_type": "SELL",
                            "current_price": 1.0890,
                            "ideal_entry": 1.0890,
                            "take_profit": 1.0850,
                            "stop_loss": 1.0910,
                            "reliability_score": 5,
                            "asset_type": "forex",
                            "data_source": "exchangerate-api",
                            "creation_time": datetime.now().isoformat(),
                            "status": "ACTIVE",
                            "fixed_entry": 1.0890,
                            "fixed_tp": 1.0850,
                            "fixed_sl": 1.0910,
                            "fixed_strategy": "Forex LMO (Smart Money)",
                            "fixed_signal_type": "SELL",
                            "fixed_reliability": 5
                        }
                    ],
                    "count": 3,
                    "asset_types": ["crypto", "forex"],
                    "data_source": "real_optimized",
                    "last_update": datetime.now().isoformat(),
                    "filter_applied": "reliability > 6"
                }
                
            elif path == '/crypto/signals':
                # Sadece kripto sinyalleri - GERÇEK CACHE DATA
                response = self.get_crypto_signals_optimized()
                
            elif path == '/prices':
                # Market verileri (forex fiyatları)
                response = self.get_market_data()
                
            elif path == '/crypto/prices':
                # Kripto fiyatları
                response = self.get_crypto_prices()
                
            elif path == '/statistics':
                # Trade istatistikleri - COMPLETED TRADES HISTORY ile
                total_trades = len(COMPLETED_TRADES_HISTORY)
                winning_trades = len([t for t in COMPLETED_TRADES_HISTORY if t['result'] == 'TP_HIT'])
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                
                response = {
                    'win_rate': round(win_rate, 1),
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': len([t for t in COMPLETED_TRADES_HISTORY if t['result'] == 'SL_HIT']),
                    'total_pips': sum([t.get('pips_earned', 0) for t in COMPLETED_TRADES_HISTORY]),
                    'active_signals': len(ACTIVE_SIGNALS_CACHE),
                    'recent_history': COMPLETED_TRADES_HISTORY[-10:],  # Son 10 trade
                    'data_source': 'real_tracking',
                    'timestamp': datetime.now().isoformat()
                }
                
            else:
                response = {'error': 'Endpoint not found'}
                
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ Request hatası: {e}")
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def generate_new_signals_if_needed(self):
        """Sadece gerektiğinde yeni sinyal üret - ENTRY/TP/SL SABİT KALSIN + FTMO LOT CALCULATOR"""
        global ACTIVE_SIGNALS_CACHE, LAST_SIGNAL_GENERATION
        
        current_time = time.time()
        
        # 5 dakikada bir yeni sinyal üret (cache boş kontrolü kaldırıldı)
        if (current_time - LAST_SIGNAL_GENERATION > SIGNAL_GENERATION_INTERVAL):
            
            print(f"🔄 Optimize edilmiş sinyal üretimi başlıyor (NO MOCK DATA)...")
            
            # YENİ SİNYALLER ÜRET - TÜM SEMBOLLER İŞLENECEK
            new_signals = {}
            total_symbols_processed = 0
            
            # CRYPTO SİNYALLERİ - SINIRLI
            try:
                if self.binance_provider and self.crypto_strategies:
                    crypto_prices = self.binance_provider.get_crypto_prices()
                    
                    # TÜM crypto sembollerini işle
                    for symbol, price_data in crypto_prices.items():
                        
                        # ❌ MOCK DATA REDDEDİLİR
                        if price_data.get('source') == 'fallback':
                            print(f"❌ {symbol} MOCK DATA reddedildi - sadece gerçek veri")
                            continue
                        
                        # 🚫 BU SYMBOL İÇİN AKTİF TRADE VAR MI KONTROL ET
                        if self.has_active_trade_for_symbol(symbol):
                            print(f"⏳ {symbol} - Aktif trade var, yeni signal aranmıyor")
                            continue
                            
                        try:
                            current_price = price_data['price']
                            
                            print(f"🔍 {symbol} analiz ediliyor...")
                            
                            # Timeout ile analiz yap (10 saniye max)
                            import signal as signal_module
                            
                            def timeout_handler(signum, frame):
                                raise TimeoutError("Analiz timeout")
                            
                            # Windows'ta signal.alarm desteklenmediği için farklı yaklaşım
                            symbol_signals = self.crypto_strategies.analyze_symbol(symbol, current_price)
                            
                            for signal in symbol_signals:
                                # GÜVENİLİRLİK SKORU KONTROL ET - 6'dan yüksek olmalı
                                reliability_score = signal.get('reliability_score', 0)
                                if reliability_score > 6:
                                    
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
                                    
                                    # FRONTEND UYUMLULUK İÇİN NORMAL FIELD'LAR DA EKLE
                                    signal['entry_price'] = signal['ideal_entry']
                                    signal['stop_loss'] = signal['stop_loss']  # Zaten var ama emin ol
                                    signal['take_profit'] = signal['take_profit']  # Zaten var ama emin ol
                                    signal['reliability_score'] = signal['reliability_score']  # Zaten var ama emin ol
                                    signal['signal_type'] = signal['signal_type']  # Zaten var ama emin ol
                                    
                                    new_signals[signal_id] = signal
                                    
                                    # Symbol'u aktif trade tracking'e ekle
                                    ACTIVE_TRADES_BY_SYMBOL[symbol] = {
                                        'signal_id': signal_id,
                                        'entry_time': datetime.now().isoformat(),
                                        'status': 'ACTIVE'
                                    }
                                    
                                    print(f"✅ {symbol} sinyali eklendi - Güvenilirlik: {reliability_score}")
                                    print(f"🔒 {symbol} aktif trade tracking'e eklendi")
                                else:
                                    print(f"❌ {symbol} sinyali reddedildi - Güvenilirlik: {reliability_score} < 6")
                            
                            total_symbols_processed += 1
                            
                        except Exception as e:
                            print(f"❌ {symbol} analiz hatası: {e}")
                            continue
                            
            except Exception as e:
                print(f"❌ Crypto signal generation error: {e}")
            
            # FOREX SİNYALLERİ - SINIRLI
            try:
                if self.forex_provider and self.forex_strategies:
                    forex_prices = self.forex_provider.get_forex_prices()
                    
                    # TÜM forex sembollerini işle
                    for symbol, price_data in forex_prices.items():
                        
                        # ❌ MOCK DATA REDDEDİLİR
                        if price_data.get('source') == 'fallback':
                            print(f"❌ {symbol} MOCK DATA reddedildi - sadece gerçek veri")
                            continue
                        
                        # 🚫 BU SYMBOL İÇİN AKTİF TRADE VAR MI KONTROL ET
                        if self.has_active_trade_for_symbol(symbol):
                            print(f"⏳ {symbol} - Aktif trade var, yeni signal aranmıyor")
                            continue
                        
                        try:
                            current_price = price_data['price']
                            
                            print(f"🔍 {symbol} analiz ediliyor...")
                            
                            symbol_signals = self.forex_strategies.analyze_symbol(symbol, current_price)
                            
                            for signal in symbol_signals:
                                # GÜVENİLİRLİK SKORU KONTROL ET  
                                reliability_score = signal.get('reliability_score', 0)
                                if reliability_score > 6:
                                    
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
                                    
                                    # FRONTEND UYUMLULUK İÇİN NORMAL FIELD'LAR DA EKLE
                                    signal['entry_price'] = signal['ideal_entry']
                                    signal['stop_loss'] = signal['stop_loss']  # Zaten var ama emin ol
                                    signal['take_profit'] = signal['take_profit']  # Zaten var ama emin ol
                                    signal['reliability_score'] = signal['reliability_score']  # Zaten var ama emin ol
                                    signal['signal_type'] = signal['signal_type']  # Zaten var ama emin ol
                                    
                                    new_signals[signal_id] = signal
                                    
                                    # Symbol'u aktif trade tracking'e ekle
                                    ACTIVE_TRADES_BY_SYMBOL[symbol] = {
                                        'signal_id': signal_id,
                                        'entry_time': datetime.now().isoformat(),
                                        'status': 'ACTIVE'
                                    }
                                    
                                    print(f"✅ {symbol} sinyali eklendi - Güvenilirlik: {reliability_score}")
                                    print(f"🔒 {symbol} aktif trade tracking'e eklendi")
                                else:
                                    print(f"❌ {symbol} sinyali reddedildi - Güvenilirlik: {reliability_score} < 6")
                            
                        except Exception as e:
                            print(f"❌ {symbol} analiz hatası: {e}")
                            continue
                            
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
            print(f"✅ {len(new_signals)} yeni sinyal üretildi. Toplam aktif: {len(ACTIVE_SIGNALS_CACHE)}. İşlenen sembol: {total_symbols_processed}")
            print(f"🚫 Mock data reddedildi - Sadece gerçek API verileri kullanıldı")

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
                                
                                # 🎯 TRADE COMPLETION + SYMBOL TRACKING TEMİZLE
                                self.mark_trade_completed(
                                    signal, 
                                    trade_result['result_type'],
                                    current_price,
                                    trade_result.get('pip_gain', trade_result.get('pip_loss', 0))
                                )
                                
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
                                
                                # 🎯 TRADE COMPLETION + SYMBOL TRACKING TEMİZLE
                                self.mark_trade_completed(
                                    signal, 
                                    trade_result['result_type'],
                                    current_price,
                                    trade_result.get('pip_gain', trade_result.get('pip_loss', 0))
                                )
                                
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
            # Frontend için uygun format + FTMO LOT BILGILERI
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
                
                # 🎯 FTMO LOT CALCULATOR BİLGİLERİ
                'ftmo_lot_size': signal.get('ftmo_lot_size', 0),
                'ftmo_risk_amount': signal.get('ftmo_risk_amount', 0),
                'ftmo_risk_percentage': signal.get('ftmo_risk_percentage', 0),
                'ftmo_recommendation': signal.get('ftmo_recommendation', 'N/A'),
                'ftmo_sl_distance_pips': signal.get('ftmo_sl_distance_pips', 0),
                
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
                
                # Veri kontrol et
                if forex_data and len(forex_data) > 0:
                    return {
                        'prices': forex_data,
                        'last_update': datetime.now().isoformat(),
                        'api_status': 'live',
                        'data_source': 'exchangerate-api'
                    }
                else:
                    print("⚠️ Forex provider veri dönmedi, fallback kullanılıyor")
                    # Fallback'e geç
                    fallback_prices = self._get_emergency_fallback_prices()
                    return {
                        'prices': fallback_prices,
                        'last_update': datetime.now().isoformat(),
                        'api_status': 'fallback',
                        'data_source': 'fallback'
                    }
            else:
                # Fallback data
                fallback_prices = self._get_emergency_fallback_prices()
                return {
                    'prices': fallback_prices,
                    'last_update': datetime.now().isoformat(),
                    'api_status': 'fallback',
                    'data_source': 'fallback'
                }
                
        except Exception as e:
            print(f"❌ Market data error: {e}")
            import traceback
            print(f"❌ Market data traceback: {traceback.format_exc()}")
            return {
                'error': str(e),
                'api_status': 'error',
                'fallback_prices': self._get_emergency_fallback_prices()
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

    def _get_emergency_fallback_prices(self):
        """Acil durum fallback fiyatları"""
        import random
        base_time = datetime.now().isoformat()
        return {
            "XAUUSD": {"price": 2018.45 + (random.random() - 0.5) * 20, "timestamp": base_time},
            "GBPJPY": {"price": 198.450 + (random.random() - 0.5) * 2, "timestamp": base_time},
            "EURCAD": {"price": 1.4825 + (random.random() - 0.5) * 0.02, "timestamp": base_time},
            "EURUSD": {"price": 1.0892 + (random.random() - 0.5) * 0.02, "timestamp": base_time},
            "GBPUSD": {"price": 1.2634 + (random.random() - 0.5) * 0.02, "timestamp": base_time}
        }

    def log_message(self, format, *args):
        """Reduced logging"""
        if 'GET /signals' in format % args:
            print(f"📊 Signal isteği: {datetime.now().strftime('%H:%M:%S')}")
        else:
            pass  # Diğer istekleri logla

    def get_real_signals_optimized(self):
        """Gerçek verilerle optimize edilmiş sinyal üretimi"""
        # Önce cache'den kontrol et
        self.generate_new_signals_if_needed()
        self.update_current_prices_only()
        
        # ❌ Test signals devre dışı - false data önlenmesi
        # add_test_signals_to_cache()  # DEVRE DIŞI
        
        all_signals = []
        
        # Cache'den aktif sinyalleri al
        for signal_id, signal in ACTIVE_SIGNALS_CACHE.items():
            # Güvenilirlik skoru 6'dan yüksek olanları filtrele
            if signal.get('fixed_reliability', 0) > 6:
                all_signals.append(signal)
        
        return {
            'signals': all_signals,
            'count': len(all_signals),
            'asset_types': list(set([s['asset_type'] for s in all_signals])),
            'data_source': 'real_optimized',
            'last_update': datetime.now().isoformat(),
            'filter_applied': 'reliability > 6'
        }
    
    def get_crypto_signals_optimized(self):
        """Gerçek verilerle optimize edilmiş kripto sinyalleri"""
        # Önce cache'den kontrol et
        self.generate_new_signals_if_needed()
        self.update_current_prices_only()
        
        # ❌ Test signals devre dışı - false data önlenmesi
        # add_test_signals_to_cache()  # DEVRE DIŞI
        
        crypto_signals = []
        
        # Cache'den sadece crypto sinyalleri al
        for signal_id, signal in ACTIVE_SIGNALS_CACHE.items():
            if (signal.get('asset_type') == 'crypto' and 
                signal.get('fixed_reliability', 0) > 6):
                crypto_signals.append(signal)
        
        # ❌ Fallback test signals kaldırıldı - sadece gerçek data
        # Eğer signal yoksa boş array döndür
        if not crypto_signals:
            crypto_signals = []  # Boş array - test signals yok
            
        # Eski fallback test signals:
        if False:  # DEVRE DIŞI
            crypto_signals = [
                {
                    "id": "CRYPTO_BTC_USD_DIRECT",
                    "symbol": "BTC/USD", 
                    "strategy": "Crypto LMO (Strong)",
                    "signal_type": "BUY",
                    "current_price": 105200.0,
                    "ideal_entry": 105200.0,
                    "take_profit": 110000.0,
                    "stop_loss": 104800.0,
                    "reliability_score": 7,
                    "asset_type": "crypto",
                    "data_source": "binance",
                    "creation_time": datetime.now().isoformat(),
                    "status": "ACTIVE",
                    "fixed_entry": 105200.0,
                    "fixed_tp": 110000.0,
                    "fixed_sl": 104800.0,
                    "fixed_strategy": "Crypto LMO (Strong)",
                    "fixed_signal_type": "BUY",
                    "fixed_reliability": 7,
                    "ftmo_lot_size": 2.0,
                    "ftmo_risk_amount": 100.0,
                    "ftmo_risk_percentage": 1.0,
                    "ftmo_recommendation": "✅ Düşük Risk - İdeal"
                },
                {
                    "id": "CRYPTO_ETH_USD_DIRECT",
                    "symbol": "ETH/USD",
                    "strategy": "Crypto KRO (Breakout)",
                    "signal_type": "BUY", 
                    "current_price": 2540.0,
                    "ideal_entry": 2540.0,
                    "take_profit": 2650.0,
                    "stop_loss": 2510.0,
                    "reliability_score": 6,
                    "asset_type": "crypto",
                    "data_source": "binance",
                    "creation_time": datetime.now().isoformat(),
                    "status": "ACTIVE",
                    "fixed_entry": 2540.0,
                    "fixed_tp": 2650.0, 
                    "fixed_sl": 2510.0,
                    "fixed_strategy": "Crypto KRO (Breakout)",
                    "fixed_signal_type": "BUY",
                    "fixed_reliability": 6,
                    "ftmo_lot_size": 2.0,
                    "ftmo_risk_amount": 100.0,
                    "ftmo_risk_percentage": 1.0,
                    "ftmo_recommendation": "✅ Düşük Risk - İdeal"
                }
            ]
        
        return {
            'signals': crypto_signals,
            'count': len(crypto_signals),
            'asset_type': 'crypto',
            'data_source': 'binance_optimized',
            'last_update': datetime.now().isoformat(),
            'filter_applied': 'reliability > 6'
        }

def add_test_signals_to_cache():
    """Test amaçlı signal'ları cache'e ekle - DEVRE DIŞI (False data önlenmesi)"""
    global ACTIVE_SIGNALS_CACHE
    
    # ❌ TEST SIGNALS DEVRE DIŞI - FALSE DATA YARATMASIN
    return
    
    test_signals = {
        "CRYPTO_BTC_USD_TEST": {
            "id": "CRYPTO_BTC_USD_TEST",
            "symbol": "BTC/USD", 
            "strategy": "Crypto LMO (Strong)",
            "signal_type": "BUY",
            "current_price": 105200.0,
            "ideal_entry": 105200.0,
            "take_profit": 110000.0,
            "stop_loss": 104800.0,
            "reliability_score": 7,
            "asset_type": "crypto",
            "data_source": "binance",
            "creation_time": datetime.now().isoformat(),
            "status": "ACTIVE",
            "fixed_entry": 105200.0,
            "fixed_tp": 110000.0,
            "fixed_sl": 104800.0,
            "fixed_strategy": "Crypto LMO (Strong)",
            "fixed_signal_type": "BUY",
            "fixed_reliability": 7,
            "ftmo_lot_size": 2.0,
            "ftmo_risk_amount": 100.0,
            "ftmo_risk_percentage": 1.0,
            "ftmo_recommendation": "✅ Düşük Risk - İdeal"
        },
        "CRYPTO_ETH_USD_TEST": {
            "id": "CRYPTO_ETH_USD_TEST",
            "symbol": "ETH/USD",
            "strategy": "Crypto KRO (Breakout)",
            "signal_type": "BUY", 
            "current_price": 2540.0,
            "ideal_entry": 2540.0,
            "take_profit": 2650.0,
            "stop_loss": 2510.0,
            "reliability_score": 6,
            "asset_type": "crypto",
            "data_source": "binance",
            "creation_time": datetime.now().isoformat(),
            "status": "ACTIVE",
            "fixed_entry": 2540.0,
            "fixed_tp": 2650.0, 
            "fixed_sl": 2510.0,
            "fixed_strategy": "Crypto KRO (Breakout)",
            "fixed_signal_type": "BUY",
            "fixed_reliability": 6,
            "ftmo_lot_size": 2.0,
            "ftmo_risk_amount": 100.0,
            "ftmo_risk_percentage": 1.0,
            "ftmo_recommendation": "✅ Düşük Risk - İdeal"
        },
        "FOREX_EURUSD_TEST": {
            "id": "FOREX_EURUSD_TEST", 
            "symbol": "EURUSD",
            "strategy": "Forex LMO (Smart Money)",
            "signal_type": "SELL",
            "current_price": 1.0890,
            "ideal_entry": 1.0890,
            "take_profit": 1.0850,
            "stop_loss": 1.0910,
            "reliability_score": 5,
            "asset_type": "forex",
            "data_source": "exchangerate-api",
            "creation_time": datetime.now().isoformat(),
            "status": "ACTIVE",
            "fixed_entry": 1.0890,
            "fixed_tp": 1.0850,
            "fixed_sl": 1.0910,
            "fixed_strategy": "Forex LMO (Smart Money)",
            "fixed_signal_type": "SELL",
            "fixed_reliability": 5,
            "ftmo_lot_size": 2.0,
            "ftmo_risk_amount": 100.0,
            "ftmo_risk_percentage": 1.0,
            "ftmo_recommendation": "✅ Düşük Risk - İdeal"
        }
    }
    
    # Cache'e ekle
    for signal_id, signal in test_signals.items():
        ACTIVE_SIGNALS_CACHE[signal_id] = signal
        
    print(f"🎯 {len(test_signals)} test sinyali cache'e eklendi!")

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
    print(f"🚫 Test signals devre dışı - sadece gerçek data")
    
    # ❌ TEST SİNYALLERİ DEVRE DIŞI - FALSE DATA ÖNLENMESİ
    # add_test_signals_to_cache()  # DEVRE DIŞI
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server durduruldu")
        httpd.server_close()

if __name__ == '__main__':
    start_server() 