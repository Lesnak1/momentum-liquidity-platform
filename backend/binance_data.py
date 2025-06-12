"""
Binance REST API ile Gerçek Zamanlı Kripto Verileri
WebSocket olmadan - sadece HTTP istekleri ile
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

try:
    import urllib.request
    import urllib.parse
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False

class BinanceDataProvider:
    """Binance REST API veri sağlayıcısı"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.cache = {}
        self.cache_duration = 10  # 10 saniye cache
        
        # En popüler kripto çiftleri
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 
            'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'XRPUSDT',
            'LTCUSDT', 'TRXUSDT', 'ATOMUSDT', 'FILUSDT', 'HBARUSDT'
        ]
        
    def get_crypto_prices(self) -> Dict:
        """Kripto fiyatlarını Binance'den çek"""
        cache_key = 'crypto_prices'
        
        # Cache kontrolü
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        crypto_data = {}
        
        try:
            if URLLIB_AVAILABLE:
                # 24hr ticker statistics (tüm semboller için)
                url = f"{self.base_url}/ticker/24hr"
                
                with urllib.request.urlopen(url, timeout=10) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        
                        # Sadece istediğimiz sembolleri filtrele
                        for item in data:
                            symbol = item['symbol']
                            if symbol in self.symbols:
                                # USDT'yi /USD'ye dönüştür
                                display_symbol = symbol.replace('USDT', '/USD')
                                
                                crypto_data[display_symbol] = {
                                    'price': float(item['lastPrice']),
                                    'change_24h': float(item['priceChangePercent']),
                                    'volume_24h': float(item['volume']) * float(item['lastPrice']),  # USD cinsinden
                                    'high_24h': float(item['highPrice']),
                                    'low_24h': float(item['lowPrice']),
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'binance_rest',
                                    'name': symbol.replace('USDT', '')
                                }
                        
                        print(f"✅ Binance'den {len(crypto_data)} kripto fiyatı alındı")
                        
            else:
                # Fallback
                crypto_data = self._get_fallback_crypto()
                print("⚠️ urllib yok, fallback kullanılıyor")
                
        except Exception as e:
            print(f"❌ Binance API hatası: {e}")
            crypto_data = self._get_fallback_crypto()
        
        # Cache'e kaydet
        self.cache[cache_key] = {
            'data': crypto_data,
            'timestamp': time.time()
        }
        
        return crypto_data
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Binance'den geçmiş mum verilerini çek"""
        cache_key = f'klines_{symbol}_{interval}_{limit}'
        
        # Cache kontrolü
        if self._is_cache_valid(cache_key, duration=300):  # 5 dakika cache
            return self.cache[cache_key]['data']
        
        klines = []
        
        try:
            if URLLIB_AVAILABLE:
                # USDT sembolüne dönüştür
                binance_symbol = symbol.replace('/USD', 'USDT')
                
                url = f"{self.base_url}/klines"
                params = {
                    'symbol': binance_symbol,
                    'interval': interval,
                    'limit': str(limit)
                }
                
                query_string = urllib.parse.urlencode(params)
                full_url = f"{url}?{query_string}"
                
                with urllib.request.urlopen(full_url, timeout=15) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        
                        for kline in data:
                            klines.append({
                                'timestamp': int(kline[0]),
                                'open': float(kline[1]),
                                'high': float(kline[2]),
                                'low': float(kline[3]),
                                'close': float(kline[4]),
                                'volume': float(kline[5])
                            })
                        
                        print(f"✅ {symbol} için {len(klines)} mum verisi alındı")
            else:
                klines = self._generate_fake_klines(symbol, limit)
                
        except Exception as e:
            print(f"❌ Kline verisi hatası {symbol}: {e}")
            klines = self._generate_fake_klines(symbol, limit)
        
        # Cache'e kaydet
        self.cache[cache_key] = {
            'data': klines,
            'timestamp': time.time()
        }
        
        return klines
    
    def _is_cache_valid(self, cache_key: str, duration: int = None) -> bool:
        """Cache geçerliliğini kontrol et"""
        if cache_key not in self.cache:
            return False
        
        cache_duration = duration or self.cache_duration
        return (time.time() - self.cache[cache_key]['timestamp']) < cache_duration
    
    def _get_fallback_crypto(self) -> Dict:
        """Fallback kripto fiyatları"""
        import random
        
        base_prices = {
            'BTC/USD': {'price': 43250.0, 'name': 'Bitcoin'},
            'ETH/USD': {'price': 2840.0, 'name': 'Ethereum'},
            'BNB/USD': {'price': 245.0, 'name': 'BNB'},
            'SOL/USD': {'price': 89.0, 'name': 'Solana'},
            'ADA/USD': {'price': 0.485, 'name': 'Cardano'},
            'DOT/USD': {'price': 7.25, 'name': 'Polkadot'},
            'AVAX/USD': {'price': 38.5, 'name': 'Avalanche'},
            'LINK/USD': {'price': 14.8, 'name': 'Chainlink'},
            'HBAR/USD': {'price': 0.125, 'name': 'Hedera'},
            'UNI/USD': {'price': 6.5, 'name': 'Uniswap'}
        }
        
        result = {}
        for symbol, data in base_prices.items():
            variation = random.uniform(-0.02, 0.02)  # ±2%
            change_24h = random.uniform(-8, 8)
            
            result[symbol] = {
                'price': round(data['price'] * (1 + variation), 4),
                'change_24h': round(change_24h, 2),
                'volume_24h': random.randint(100000000, 5000000000),
                'high_24h': round(data['price'] * (1 + variation + 0.01), 4),
                'low_24h': round(data['price'] * (1 + variation - 0.01), 4),
                'timestamp': datetime.now().isoformat(),
                'source': 'fallback',
                'name': data['name']
            }
        
        return result
    
    def _generate_fake_klines(self, symbol: str, limit: int) -> List[Dict]:
        """Sahte mum verileri üret"""
        import random
        
        # Base fiyat
        base_prices = {
            'BTC/USD': 43250.0,
            'ETH/USD': 2840.0,
            'BNB/USD': 245.0,
            'SOL/USD': 89.0,
            'ADA/USD': 0.485,
        }
        
        base_price = base_prices.get(symbol, 100.0)
        klines = []
        current_price = base_price
        
        # Son N saatlik veri üret
        current_time = int(time.time() * 1000)
        hour_ms = 60 * 60 * 1000
        
        for i in range(limit):
            timestamp = current_time - ((limit - i) * hour_ms)
            
            # Volatilite
            volatility = 0.02  # %2
            change = random.gauss(0, volatility)
            
            open_price = current_price
            close_price = current_price * (1 + change)
            high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, volatility/3)))
            low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, volatility/3)))
            
            klines.append({
                'timestamp': timestamp,
                'open': round(open_price, 4),
                'high': round(high_price, 4),
                'low': round(low_price, 4),
                'close': round(close_price, 4),
                'volume': random.randint(1000, 100000)
            })
            
            current_price = close_price
        
        return klines

# Global instance
binance_provider = BinanceDataProvider()

def get_binance_provider():
    """Global Binance provider'ı getir"""
    return binance_provider 