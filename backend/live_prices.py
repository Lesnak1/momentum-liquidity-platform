"""
Gerçek Anlık Fiyat Kaynakları
Birden fazla API'den fiyat çeker ve en güncel veriyi sağlar
"""

import urllib.request
import json
import time
from datetime import datetime

class LivePriceFeeder:
    def __init__(self):
        self.api_keys = {
            'alpha_vantage': 'YOUR_FREE_KEY',  # alphavantage.co'dan ücretsiz alın
            'finhub': 'YOUR_FREE_KEY',        # finnhub.io'dan ücretsiz alın
            'twelve_data': 'demo'             # sınırlı demo
        }
        
    def get_forex_price_alpha(self, symbol):
        """Alpha Vantage'den forex fiyatı"""
        try:
            from_curr = symbol[:3]
            to_curr = symbol[3:]
            
            url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_curr}&to_currency={to_curr}&apikey={self.api_keys['alpha_vantage']}"
            
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())
            
            if 'Realtime Currency Exchange Rate' in data:
                rate_data = data['Realtime Currency Exchange Rate']
                return {
                    'price': float(rate_data['5. Exchange Rate']),
                    'timestamp': rate_data['6. Last Refreshed'],
                    'source': 'alpha_vantage'
                }
                
        except Exception as e:
            print(f"Alpha Vantage hatası {symbol}: {e}")
            return None
    
    def get_gold_price_finnhub(self):
        """Finnhub'dan altın fiyatı (XAUUSD)"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol=OANDA:XAU_USD&token={self.api_keys['finhub']}"
            
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())
            
            if 'c' in data:  # current price
                return {
                    'price': float(data['c']),
                    'timestamp': datetime.fromtimestamp(data['t']).isoformat(),
                    'source': 'finnhub'
                }
                
        except Exception as e:
            print(f"Finnhub altın hatası: {e}")
            return None
    
    def get_yahoo_finance_price(self, symbol):
        """Yahoo Finance'den fiyat (backup)"""
        try:
            # Yahoo Finance API formatı
            yahoo_symbol = f"{symbol}=X"  # Forex için
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
            
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())
            
            if 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                current_price = result['meta']['regularMarketPrice']
                
                return {
                    'price': float(current_price),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'yahoo_finance'
                }
                
        except Exception as e:
            print(f"Yahoo Finance hatası {symbol}: {e}")
            return None
    
    def get_live_price(self, symbol):
        """En iyi kaynaktan anlık fiyat"""
        price_data = None
        
        # 1. Forex çiftleri için Alpha Vantage dene
        if symbol in ['EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY']:
            price_data = self.get_forex_price_alpha(symbol)
            if price_data:
                return price_data
        
        # 2. Altın için Finnhub dene
        if symbol == 'XAUUSD':
            price_data = self.get_gold_price_finnhub()
            if price_data:
                return price_data
        
        # 3. Backup olarak Yahoo Finance
        price_data = self.get_yahoo_finance_price(symbol)
        if price_data:
            return price_data
        
        # 4. Hiçbiri çalışmazsa simulated
        return self.get_simulated_price(symbol)
    
    def get_simulated_price(self, symbol):
        """Simulated gerçekçi fiyat"""
        import random
        
        base_prices = {
            'XAUUSD': 2018.45,
            'GBPJPY': 198.450,
            'EURCAD': 1.4825,
            'EURUSD': 1.0892,
            'GBPUSD': 1.2634
        }
        
        if symbol in base_prices:
            variation = (random.random() - 0.5) * 0.008  # ±0.8% değişim
            price = base_prices[symbol] * (1 + variation)
            
            return {
                'price': round(price, 5),
                'timestamp': datetime.now().isoformat(),
                'source': 'simulated_realistic'
            }
        
        return None

# Test fonksiyonu
if __name__ == "__main__":
    feeder = LivePriceFeeder()
    
    symbols = ['XAUUSD', 'GBPJPY', 'EURUSD', 'GBPUSD']
    
    print("🔄 Anlık fiyat testleri...")
    for symbol in symbols:
        price_data = feeder.get_live_price(symbol)
        if price_data:
            print(f"✅ {symbol}: {price_data['price']} ({price_data['source']})")
        else:
            print(f"❌ {symbol}: Fiyat alınamadı") 