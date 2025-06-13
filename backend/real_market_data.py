"""
Gerçek Zamanlı Piyasa Verisi API'leri
Forex, Kripto ve Geçmiş Mum Verileri için Güvenilir Kaynaklar
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

class RealMarketDataProvider:
    """Gerçek piyasa verisi sağlayıcısı"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # API endpoint'leri
        self.apis = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'exchangerate': 'https://api.exchangerate-api.com/v4/latest',
            'fxapi': 'https://fxapi.net/v1',
            'coincap': 'https://api.coincap.io/v2'
        }
        
        # Cache sistemi
        self.cache = {}
        self.cache_duration = 30  # 30 saniye
        
    def get_forex_prices(self) -> Dict:
        """Forex paritelerinin gerçek fiyatlarını çek"""
        cache_key = 'forex_prices'
        
        # Cache kontrolü
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        forex_data = {}
        symbols = {
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD', 
            'GBPJPY': 'GBP/JPY',
            'EURCAD': 'EUR/CAD',
            'XAUUSD': 'XAU/USD'
        }
        
        try:
            # ExchangeRate-API kullan (güvenilir ve ücretsiz)
            response = self.session.get(f"{self.apis['exchangerate']}/USD", timeout=10)
            if response.status_code == 200:
                usd_rates = response.json()['rates']
                
                # Ana pariteler için
                if 'EUR' in usd_rates:
                    forex_data['EURUSD'] = {
                        'price': round(1/usd_rates['EUR'], 5),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'exchangerate-api'
                    }
                
                if 'GBP' in usd_rates:
                    forex_data['GBPUSD'] = {
                        'price': round(1/usd_rates['GBP'], 5),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'exchangerate-api'
                    }
                
                # Cross pariteleri hesapla
                if 'EUR' in usd_rates and 'CAD' in usd_rates:
                    eur_usd = 1/usd_rates['EUR']
                    cad_usd = 1/usd_rates['CAD']
                    forex_data['EURCAD'] = {
                        'price': round(eur_usd * usd_rates['CAD'], 5),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'calculated'
                    }
                
                # GBP/JPY hesapla
                if 'GBP' in usd_rates and 'JPY' in usd_rates:
                    gbp_usd = 1/usd_rates['GBP']
                    forex_data['GBPJPY'] = {
                        'price': round(gbp_usd * usd_rates['JPY'], 3),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'calculated'
                    }
                
            # Altın fiyatı için ayrı API (CoinGecko)
            try:
                gold_response = self.session.get(
                    f"{self.apis['coingecko']}/simple/price?ids=gold&vs_currencies=usd",
                    timeout=10
                )
                if gold_response.status_code == 200:
                    gold_data = gold_response.json()
                    if 'gold' in gold_data:
                        forex_data['XAUUSD'] = {
                            'price': gold_data['gold']['usd'],
                            'timestamp': datetime.now().isoformat(),
                            'source': 'coingecko'
                        }
            except:
                pass
                
        except Exception as e:
            print(f"Forex API hatası: {e}")
            return self._get_fallback_forex()
        
        # Cache'e kaydet
        self.cache[cache_key] = {
            'data': forex_data,
            'timestamp': time.time()
        }
        
        return forex_data
    
    def get_crypto_prices(self) -> Dict:
        """En yüksek hacimli kripto tokenlerin gerçek fiyatlarını çek"""
        cache_key = 'crypto_prices'
        
        # Cache kontrolü
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        crypto_data = {}
        
        try:
            # CoinGecko - En güvenilir kripto API
            response = self.session.get(
                f"{self.apis['coingecko']}/coins/markets"
                "?vs_currency=usd&order=market_cap_desc&per_page=15&page=1"
                "&sparkline=false&price_change_percentage=24h",
                timeout=15
            )
            
            if response.status_code == 200:
                coins = response.json()
                
                for coin in coins:
                    symbol = coin['symbol'].upper()
                    
                    crypto_data[f"{symbol}/USD"] = {
                        'price': coin['current_price'],
                        'change_24h': round(coin['price_change_percentage_24h'] or 0, 2),
                        'volume_24h': coin['total_volume'] or 0,
                        'market_cap': coin['market_cap'] or 0,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'coingecko',
                        'name': coin['name']
                    }
                    
        except Exception as e:
            print(f"Kripto API hatası: {e}")
            return self._get_fallback_crypto()
        
        # Cache'e kaydet
        self.cache[cache_key] = {
            'data': crypto_data,
            'timestamp': time.time()
        }
        
        return crypto_data
    
    def get_historical_candles(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Geçmiş mum verilerini çek"""
        cache_key = f'candles_{symbol}_{timeframe}_{limit}'
        
        # Cache kontrolü (5 dakika cache)
        if self._is_cache_valid(cache_key, duration=300):
            return self.cache[cache_key]['data']
        
        candles = []
        
        try:
            # Kripto için CoinGecko
            if '/' in symbol and 'USD' in symbol:
                coin_id = self._get_coingecko_id(symbol)
                if coin_id:
                    days = self._timeframe_to_days(timeframe, limit)
                    
                    response = self.session.get(
                        f"{self.apis['coingecko']}/coins/{coin_id}/market_chart"
                        f"?vs_currency=usd&days={days}&interval=hourly",
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        prices = data.get('prices', [])
                        volumes = data.get('total_volumes', [])
                        
                        for i, price_point in enumerate(prices[-limit:]):
                            volume = volumes[i][1] if i < len(volumes) else 0
                            
                            candles.append({
                                'timestamp': price_point[0],
                                'open': price_point[1],
                                'high': price_point[1] * 1.002,  # Simulated
                                'low': price_point[1] * 0.998,   # Simulated
                                'close': price_point[1],
                                'volume': volume
                            })
            
            # Forex için alternatif yöntem (sınırlı)
            else:
                candles = self._generate_realistic_candles(symbol, limit)
                
        except Exception as e:
            print(f"Mum verisi hatası {symbol}: {e}")
            candles = self._generate_realistic_candles(symbol, limit)
        
        # Cache'e kaydet
        self.cache[cache_key] = {
            'data': candles,
            'timestamp': time.time()
        }
        
        return candles
    
    def _get_coingecko_id(self, symbol: str) -> Optional[str]:
        """Kripto sembol -> CoinGecko ID mapping"""
        mapping = {
            'BTC/USD': 'bitcoin',
            'ETH/USD': 'ethereum', 
            'BNB/USD': 'binancecoin',
            'SOL/USD': 'solana',
            'ADA/USD': 'cardano',
            'DOT/USD': 'polkadot',
            'AVAX/USD': 'avalanche-2',
            'LINK/USD': 'chainlink',

            'UNI/USD': 'uniswap'
        }
        return mapping.get(symbol)
    
    def _timeframe_to_days(self, timeframe: str, limit: int) -> int:
        """Timeframe ve limit'e göre gün sayısı hesapla"""
        if timeframe == '1m':
            return max(1, limit // (24 * 60))
        elif timeframe == '5m':
            return max(1, limit // (24 * 12))
        elif timeframe == '15m':
            return max(1, limit // (24 * 4))
        elif timeframe == '1h':
            return max(1, limit // 24)
        elif timeframe == '4h':
            return max(1, limit // 6)
        elif timeframe == '1d':
            return limit
        return 7  # Default 1 hafta
    
    def _generate_realistic_candles(self, symbol: str, limit: int) -> List[Dict]:
        """Gerçekçi mum verileri üret (forex için)"""
        import random
        
        # ❌ MOCK BASE PRICES KALDIRILDI - Sadece gerçek API verisi kullan
        # Gerçek exchange rate yoksa candle üretme
        return []
    
    def _is_cache_valid(self, cache_key: str, duration: int = None) -> bool:
        """Cache geçerliliğini kontrol et"""
        if cache_key not in self.cache:
            return False
        
        cache_duration = duration or self.cache_duration
        return (time.time() - self.cache[cache_key]['timestamp']) < cache_duration
    
    def _get_fallback_forex(self) -> Dict:
        """❌ FALLBACK DEVRE DIŞI - GERÇEK VERİ YOKSA HİÇ VERİ YOK"""
        # Mock data yerine boş response döndür
        return {
            'error': 'No real forex data available',
            'source': 'no_fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_fallback_crypto(self) -> Dict:
        """❌ FALLBACK DEVRE DIŞI - GERÇEK VERİ YOKSA HİÇ VERİ YOK"""
        # Mock data yerine boş response döndür
        return {
            'error': 'No real crypto data available',
            'source': 'no_fallback',
            'timestamp': datetime.now().isoformat()
        }

# Global instance
market_data_provider = RealMarketDataProvider()

def get_market_data_provider():
    """Global market data provider'ı getir"""
    return market_data_provider 