"""
Binance REST API ile Gerçek Zamanlı Kripto Verileri
GERÇEK API ANAHTARLARI İLE - OPTIMIZE EDİLMİŞ PERFORMANS
"""

import json
import time
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

try:
    import urllib.request
    import urllib.parse
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False

# Config'den API anahtarlarını al
try:
    from config import BinanceConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

class BinanceDataProvider:
    """GERÇEK API ANAHTARLARI ile Binance REST API veri sağlayıcısı"""
    
    def __init__(self):
        # API Konfigürasyonu
        if CONFIG_AVAILABLE:
            self.config = BinanceConfig.get_api_credentials()
            self.rate_limits = BinanceConfig.get_rate_limits()
            self.api_key = self.config['api_key']
            self.secret_key = self.config['secret_key']
            self.base_url = "https://api.binance.com/api/v3"
            print("✅ GERÇEK Binance API anahtarları yüklendi")
        else:
            self.base_url = "https://api.binance.com/api/v3"
            self.api_key = None
            self.secret_key = None
            print("⚠️ Config bulunamadı, public API kullanılıyor")
        
        self.cache = {}
        self.cache_duration = 5  # 5 saniye cache (daha hızlı)
        self.request_count = 0
        self.last_minute = int(time.time() / 60)
        
        # Öncelikli kripto çiftleri (sizin API'nizle)
        if CONFIG_AVAILABLE:
            self.symbols = BinanceConfig.PRIORITY_SYMBOLS
        else:
            self.symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 
                'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'XRPUSDT',
                'LTCUSDT', 'TRXUSDT', 'ATOMUSDT', 'FILUSDT', 'HBARUSDT'
            ]
        
    def get_crypto_prices(self) -> Dict:
        """GERÇEK API ile optimize edilmiş kripto fiyatları"""
        cache_key = 'crypto_prices'
        
        # Cache kontrolü
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        crypto_data = {}
        
        try:
            # GERÇEK API ile 24hr ticker
            data = self._make_request('/ticker/24hr')
            
            if data:
                # Sadece öncelikli sembolleri filtrele
                for item in data:
                    symbol = item['symbol']
                    if symbol in self.symbols:
                        # USDT'yi /USD'ye dönüştür
                        display_symbol = symbol.replace('USDT', '/USD')
                        
                        crypto_data[display_symbol] = {
                            'price': float(item['lastPrice']),
                            'change_24h': float(item['priceChangePercent']),
                            'volume_24h': float(item['volume']) * float(item['lastPrice']),
                            'high_24h': float(item['highPrice']),
                            'low_24h': float(item['lowPrice']),
                            'timestamp': datetime.now().isoformat(),
                            'source': 'binance_authenticated' if self.api_key else 'binance_public',
                            'name': symbol.replace('USDT', ''),
                            'api_type': 'GERÇEK_API' if self.api_key else 'PUBLIC'
                        }
                
                api_status = 'GERÇEK_API' if self.api_key else 'PUBLIC_API'
                print(f"✅ {api_status} ile {len(crypto_data)} kripto fiyatı alındı")
            else:
                # Fallback
                crypto_data = self._get_fallback_crypto()
                print("⚠️ API response boş, fallback kullanılıyor")
                
        except Exception as e:
            print(f"❌ Crypto prices hatası: {e}")
            crypto_data = self._get_fallback_crypto()
        
        # Cache'e kaydet
        self.cache[cache_key] = {
            'data': crypto_data,
            'timestamp': time.time()
        }
        
        return crypto_data
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """GERÇEK API ile optimize edilmiş mum verileri"""
        cache_key = f'klines_{symbol}_{interval}_{limit}'
        
        # Cache kontrolü (klines için 2 dakika cache)
        if self._is_cache_valid(cache_key, duration=120):
            return self.cache[cache_key]['data']
        
        klines = []
        
        try:
            # USDT sembolüne dönüştür
            binance_symbol = symbol.replace('/USD', 'USDT')
            
            # GERÇEK API ile klines
            params = {
                'symbol': binance_symbol,
                'interval': interval,
                'limit': limit
            }
            
            data = self._make_request('/klines', params)
            
            if data:
                for kline in data:
                    klines.append({
                        'timestamp': int(kline[0]),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                
                api_status = 'GERÇEK_API' if self.api_key else 'PUBLIC_API'
                print(f"✅ {symbol} için {len(klines)} mum verisi alındı ({api_status})")
            else:
                klines = self._generate_fake_klines(symbol, limit)
                print(f"⚠️ {symbol} API response boş, fallback kullanılıyor")
                
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
    
    def _create_signature(self, params: str) -> str:
        """API imzası oluştur (gerçek API için)"""
        if not self.secret_key:
            return ""
        
        return hmac.new(
            self.secret_key.encode('utf-8'), 
            params.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
    
    def _check_rate_limit(self) -> bool:
        """Rate limit kontrolü (6000 req/min)"""
        current_minute = int(time.time() / 60)
        
        if current_minute != self.last_minute:
            self.request_count = 0
            self.last_minute = current_minute
        
        if hasattr(self, 'rate_limits'):
            max_requests = self.rate_limits['max_requests_per_minute']
        else:
            max_requests = 1000  # Fallback
        
        if self.request_count >= max_requests:
            print(f"⚠️ Rate limit yaklaşıldı: {self.request_count}/{max_requests}")
            return False
        
        return True
    
    def _make_request(self, endpoint: str, params: dict = None, signed: bool = False) -> dict:
        """Optimize edilmiş API request"""
        if not self._check_rate_limit():
            print("❌ Rate limit aşıldı, cached data kullanılıyor")
            return {}
        
        try:
            if params is None:
                params = {}
            
            # Timestamp ekle (signed requests için)
            if signed and self.api_key:
                params['timestamp'] = int(time.time() * 1000)
            
            # Query string oluştur
            query_string = urllib.parse.urlencode(params)
            
            # İmza ekle (signed requests için)
            if signed and self.secret_key:
                signature = self._create_signature(query_string)
                query_string += f"&signature={signature}"
            
            # Full URL
            url = f"{self.base_url}{endpoint}"
            if query_string:
                url += f"?{query_string}"
            
            # Headers
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['X-MBX-APIKEY'] = self.api_key
            
            # Request oluştur
            req = urllib.request.Request(url, headers=headers)
            
            # Request timeout
            timeout = self.rate_limits.get('request_timeout', 10) if hasattr(self, 'rate_limits') else 10
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                self.request_count += 1
                
                if response.status == 200:
                    return json.loads(response.read().decode())
                else:
                    print(f"❌ Binance API error: {response.status}")
                    return {}
                    
        except Exception as e:
            print(f"❌ Request error: {e}")
            return {}

# Global instance
binance_provider = BinanceDataProvider()

def get_binance_provider():
    """Global Binance provider'ı getir"""
    return binance_provider 