#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Breakout Detection Debug - Tam problem analizi
"""

from binance_data import get_binance_provider
from crypto_strategies import CryptoTechnicalAnalysis

def debug_breakout_detection():
    """Breakout detection'ın neden çalışmadığını debug et"""
    print("🔍 BREAKOUT DETECTION DEBUG")
    print("=" * 50)
    
    # Test case: SOL/USD - fiyat resistance'ın üzerinde
    current_price = 145.68
    resistance_level = 145.66
    
    print(f"📊 Test Case:")
    print(f"   Current Price: {current_price}")
    print(f"   Resistance Level: {resistance_level}")
    print(f"   Fark: {current_price - resistance_level:.2f}")
    print(f"   Yüzde Fark: {((current_price - resistance_level) / resistance_level * 100):.4f}%")
    
    # Farklı tolerance değerleri test et
    tolerances = [0.001, 0.002, 0.003, 0.005, 0.008, 0.010]
    
    print(f"\n🔍 Tolerance Test:")
    for tolerance in tolerances:
        break_price = resistance_level * (1 + tolerance)
        is_breakout = current_price > break_price
        print(f"   Tolerance {tolerance*100:.1f}%: Break@{break_price:.2f} -> {'✅ BREAKOUT' if is_breakout else '❌ NO BREAK'}")
    
    # Gerçek veri ile test
    print(f"\n🔍 Gerçek Veri Test:")
    binance_provider = get_binance_provider()
    
    try:
        # SOL fiyat verisi al
        crypto_prices = binance_provider.get_crypto_prices()
        sol_price = crypto_prices['SOL/USD']['price']
        print(f"📊 SOL/USD Real Price: {sol_price}")
        
        # Klines al ve S/R hesapla
        klines = binance_provider.get_klines('SOL/USD', '15m', 100)
        sr_levels = CryptoTechnicalAnalysis.find_support_resistance(klines)
        
        print(f"\n🎯 Real S/R Levels:")
        print(f"   Supports: {len(sr_levels['support_levels'])}")
        for i, support in enumerate(sr_levels['support_levels'][:3]):
            print(f"     Support[{i}]: {support['level']:.2f} (touches: {support['touches']})")
        
        print(f"   Resistances: {len(sr_levels['resistance_levels'])}")
        for i, resistance in enumerate(sr_levels['resistance_levels'][:3]):
            print(f"     Resistance[{i}]: {resistance['level']:.2f} (touches: {resistance['touches']})")
        
        # Manual breakout test
        print(f"\n🔍 Manual Breakout Test:")
        for tolerance in tolerances:
            breakout = CryptoTechnicalAnalysis.detect_crypto_breakout(sol_price, sr_levels, tolerance)
            print(f"   Tolerance {tolerance*100:.1f}%: {breakout['breakout_type']} (Level: {breakout['broken_level']})")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_current_all_symbols():
    """Tüm sembollerde mevcut breakout durumunu test et"""
    print(f"\n🔍 TÜM SEMBOLLER BREAKOUT TEST:")
    print("=" * 50)
    
    binance_provider = get_binance_provider()
    
    try:
        crypto_prices = binance_provider.get_crypto_prices()
        test_symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'ADA/USD', 'DOT/USD']
        
        for symbol in test_symbols:
            if symbol in crypto_prices:
                current_price = crypto_prices[symbol]['price']
                print(f"\n📊 {symbol}: {current_price}")
                
                klines = binance_provider.get_klines(symbol, '15m', 100)
                if len(klines) >= 50:
                    sr_levels = CryptoTechnicalAnalysis.find_support_resistance(klines)
                    
                    # En yakın resistance/support'u bul
                    closest_resistance = None
                    closest_support = None
                    
                    for r in sr_levels['resistance_levels']:
                        if r['level'] >= current_price:
                            if closest_resistance is None or r['level'] < closest_resistance['level']:
                                closest_resistance = r
                    
                    for s in sr_levels['support_levels']:
                        if s['level'] <= current_price:
                            if closest_support is None or s['level'] > closest_support['level']:
                                closest_support = s
                    
                    if closest_resistance:
                        distance = ((closest_resistance['level'] - current_price) / current_price * 100)
                        print(f"   Closest Resistance: {closest_resistance['level']:.2f} (distance: {distance:.2f}%)")
                    
                    if closest_support:
                        distance = ((current_price - closest_support['level']) / current_price * 100)
                        print(f"   Closest Support: {closest_support['level']:.2f} (distance: {distance:.2f}%)")
                    
                    # Breakout test
                    breakout = CryptoTechnicalAnalysis.detect_crypto_breakout(current_price, sr_levels, 0.005)
                    if breakout['breakout_type']:
                        print(f"   ✅ BREAKOUT: {breakout['breakout_type']} @ {breakout['broken_level']:.2f}")
                    else:
                        print(f"   ❌ No breakout detected")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_breakout_detection()
    test_current_all_symbols() 