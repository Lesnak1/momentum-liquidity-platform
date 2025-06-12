#!/usr/bin/env python3
"""
Binance API Test
"""

import urllib.request
import json

def test_binance_api():
    print("🔍 Binance API Test Başlatılıyor...")
    
    try:
        # 1. Tek token test
        print("\n1. BTC Fiyat Testi:")
        url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            btc_price = float(data['lastPrice'])
            print(f"✅ BTC: ${btc_price:,.2f}")
    
        # 2. Çoklu token test
        print("\n2. Çoklu Token Testi:")
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
        
        for symbol in symbols:
            try:
                url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
                with urllib.request.urlopen(url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    price = float(data['lastPrice'])
                    change = float(data['priceChangePercent'])
                    print(f"✅ {symbol}: ${price:,.4f} ({change:+.2f}%)")
            except Exception as e:
                print(f"❌ {symbol} hatası: {e}")
        
        # 3. Tüm tokenler (24hr endpoint)
        print("\n3. Tüm Tokenlar Test:")
        url = "https://api.binance.com/api/v3/ticker/24hr"
        with urllib.request.urlopen(url, timeout=15) as response:
            all_data = json.loads(response.read().decode())
            
            target_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'HBARUSDT']
            
            found_count = 0
            for item in all_data:
                if item['symbol'] in target_symbols:
                    price = float(item['lastPrice'])
                    change = float(item['priceChangePercent'])
                    symbol_clean = item['symbol'].replace('USDT', '/USD')
                    print(f"✅ {symbol_clean}: ${price:,.4f} ({change:+.2f}%)")
                    found_count += 1
            
            print(f"\n📊 Toplam {found_count} token bulundu")
            
    except Exception as e:
        print(f"❌ API Genel Hatası: {e}")

if __name__ == "__main__":
    test_binance_api() 