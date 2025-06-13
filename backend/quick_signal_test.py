#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.request
import json
import sys

def test_signals():
    try:
        print("🔍 Crypto Sinyalleri test ediliyor...")
        response = urllib.request.urlopen('http://localhost:8000/crypto/signals', timeout=10)
        data = json.loads(response.read())
        
        print(f"✅ {len(data.get('signals', []))} adet sinyal bulundu")
        
        for i, signal in enumerate(data.get('signals', [])[:3]):  # İlk 3 sinyali göster
            print(f"\n📊 Sinyal {i+1}:")
            print(f"   💱 Çift: {signal.get('symbol')}")
            print(f"   📈 Yön: {signal.get('signal_type')}")
            print(f"   🎯 Güvenilirlik: {signal.get('reliability', 0)}/10")
            print(f"   💰 Risk/Reward: {signal.get('risk_reward', 0):.2f}")
            print(f"   🔧 Strateji: {signal.get('strategy')}")
            
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    test_signals() 