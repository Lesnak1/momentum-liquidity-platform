#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRO Tolerance Problem Solver
Gerçek piyasa koşullarında uygun tolerance bulma
"""

from binance_data import get_binance_provider
from crypto_strategies import CryptoTechnicalAnalysis

def find_optimal_tolerance():
    """Mevcut piyasa koşulları için optimal tolerance bul"""
    print("🔍 KRO TOLERANCE OPTİMİZASYONU")
    print("=" * 50)
    
    binance_provider = get_binance_provider()
    
    try:
        crypto_prices = binance_provider.get_crypto_prices()
        test_symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'ADA/USD', 'DOT/USD']
        
        all_distances = []
        
        for symbol in test_symbols:
            if symbol in crypto_prices:
                current_price = crypto_prices[symbol]['price']
                
                klines = binance_provider.get_klines(symbol, '15m', 100)
                if len(klines) >= 50:
                    sr_levels = CryptoTechnicalAnalysis.find_support_resistance(klines)
                    
                    # En yakın resistance/support mesafelerini hesapla
                    for r in sr_levels['resistance_levels']:
                        if r['level'] >= current_price:
                            distance = (r['level'] - current_price) / current_price
                            all_distances.append({
                                'symbol': symbol,
                                'type': 'resistance',
                                'distance_pct': distance * 100,
                                'current': current_price,
                                'level': r['level'],
                                'touches': r['touches'],
                                'vol_imp': r.get('volume_importance', {}).get('importance_score', 1.0)
                            })
                    
                    for s in sr_levels['support_levels']:
                        if s['level'] <= current_price:
                            distance = (current_price - s['level']) / current_price
                            all_distances.append({
                                'symbol': symbol,
                                'type': 'support',
                                'distance_pct': distance * 100,
                                'current': current_price,
                                'level': s['level'],
                                'touches': s['touches'],
                                'vol_imp': s.get('volume_importance', {}).get('importance_score', 1.0)
                            })
        
        if all_distances:
            # En yakın seviyeleri analiz et
            sorted_distances = sorted(all_distances, key=lambda x: x['distance_pct'])
            
            print(f"\n📊 EN YAKIN S/R SEVİYELERİ:")
            for i, dist in enumerate(sorted_distances[:10]):
                print(f"{i+1:2}. {dist['symbol']:8} {dist['type']:10} Distance: {dist['distance_pct']:5.2f}% | Level: {dist['level']:8.2f} | Touches: {dist['touches']} | VolImp: {dist['vol_imp']:.1f}")
            
            # İstatistikler
            distances_only = [d['distance_pct'] for d in sorted_distances]
            avg_distance = sum(distances_only) / len(distances_only)
            min_distance = min(distances_only)
            max_distance = max(distances_only[:10])  # İlk 10'un max'ı
            
            print(f"\n📈 MESAFE İSTATİSTİKLERİ:")
            print(f"   Min Distance: {min_distance:.2f}%")
            print(f"   Avg Distance: {avg_distance:.2f}%")
            print(f"   Max Distance (top 10): {max_distance:.2f}%")
            
            # Önerilen tolerance
            suggested_tolerance = max(min_distance * 0.8, 0.003)  # Min distance'ın %80'i ama en az %0.3
            
            print(f"\n💡 ÖNERİLEN TOLERANCE:")
            print(f"   Mevcut: 1.2%")
            print(f"   Önerilen: {suggested_tolerance*100:.1f}%")
            print(f"   Açıklama: En yakın mesafenin %80'i ama minimum %0.3")
            
            # Test et
            print(f"\n🔍 BREAKOUT TEST ({suggested_tolerance*100:.1f}% tolerance ile):")
            
            breakout_count = 0
            for symbol in test_symbols[:3]:
                if symbol in crypto_prices:
                    current_price = crypto_prices[symbol]['price']
                    klines = binance_provider.get_klines(symbol, '15m', 100)
                    if len(klines) >= 50:
                        sr_levels = CryptoTechnicalAnalysis.find_support_resistance(klines)
                        breakout = CryptoTechnicalAnalysis.detect_crypto_breakout(current_price, sr_levels, suggested_tolerance)
                        
                        if breakout['breakout_type']:
                            breakout_count += 1
                            print(f"   ✅ {symbol}: {breakout['breakout_type']} @ {breakout['broken_level']:.2f}")
                        else:
                            print(f"   ❌ {symbol}: No breakout")
            
            print(f"\n📊 SONUÇ: {breakout_count}/3 sembol breakout tespit edildi")
            
            return suggested_tolerance
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0.008

def test_with_custom_tolerance(tolerance):
    """Özel tolerance ile test et"""
    print(f"\n🎯 ÖZEL TOLERANCE TEST: {tolerance*100:.1f}%")
    print("-" * 40)
    
    binance_provider = get_binance_provider()
    
    try:
        crypto_prices = binance_provider.get_crypto_prices()
        test_symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        
        for symbol in test_symbols:
            if symbol in crypto_prices:
                current_price = crypto_prices[symbol]['price']
                klines = binance_provider.get_klines(symbol, '15m', 100)
                if len(klines) >= 50:
                    sr_levels = CryptoTechnicalAnalysis.find_support_resistance(klines)
                    breakout = CryptoTechnicalAnalysis.detect_crypto_breakout(current_price, sr_levels, tolerance)
                    
                    print(f"{symbol}: {current_price}")
                    if breakout['breakout_type']:
                        print(f"   ✅ BREAKOUT: {breakout['breakout_type']} @ {breakout['broken_level']:.2f}")
                        print(f"   🎯 Strength: {breakout['breakout_strength']}, Volume Score: {breakout.get('volume_importance_score', 1.0)}")
                    else:
                        print(f"   ❌ No breakout detected")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    optimal_tolerance = find_optimal_tolerance()
    
    # Test different tolerances
    test_tolerances = [0.005, 0.008, 0.010, optimal_tolerance]
    
    for tolerance in test_tolerances:
        test_with_custom_tolerance(tolerance) 