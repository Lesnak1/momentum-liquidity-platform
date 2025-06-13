#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib.request

def test_all_endpoints():
    print("🔍 Tüm endpoint'ler test ediliyor...")
    
    endpoints = [
        ('/signals', 'Ana sinyaller'),
        ('/crypto/signals', 'Crypto sinyaller'),
        ('/prices', 'Forex fiyatları'),
        ('/crypto/prices', 'Crypto fiyatları'),
        ('/statistics', 'İstatistikler')
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            print(f"\n📡 {name} test ediliyor: {endpoint}")
            url = f'http://127.0.0.1:8000{endpoint}'
            response = urllib.request.urlopen(url, timeout=10)
            data = json.loads(response.read().decode())
            
            print(f"✅ {name}: BAŞARILI")
            
            # Önemli bilgileri göster
            if 'count' in data:
                print(f"   Count: {data['count']}")
            if 'api_status' in data:
                print(f"   Status: {data['api_status']}")
            if 'signals' in data:
                print(f"   Signals: {len(data['signals'])}")
            if 'prices' in data:
                print(f"   Prices: {len(data['prices'])}")
                
            results[endpoint] = 'OK'
            
        except Exception as e:
            print(f"❌ {name}: HATA - {e}")
            results[endpoint] = f'ERROR: {e}'
    
    print(f"\n📊 SONUÇ ÖZETİ:")
    for endpoint, result in results.items():
        status = "✅" if result == 'OK' else "❌"
        print(f"   {status} {endpoint}: {result}")
    
    return results

if __name__ == "__main__":
    test_all_endpoints() 