#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRO Stratejisi Debug - Neden sinyal üretmiyor?
"""

from binance_data import get_binance_provider
from crypto_strategies import CryptoKROStrategy, CryptoTechnicalAnalysis

def debug_kro_strategy():
    """KRO stratejisinin neden sinyal üretmediğini debug et"""
    print("🔍 KRO STRATEGY DEBUG")
    print("=" * 50)
    
    # Binance provider'ı başlat
    binance_provider = get_binance_provider()
    
    # KRO strategy'yi başlat
    kro_strategy = CryptoKROStrategy(binance_provider)
    
    print(f"✅ KRO Strategy başlatıldı - Min Reliability: {kro_strategy.min_reliability}")
    
    # Test sembolü
    test_symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
    
    for symbol in test_symbols:
        print(f"\n🔍 {symbol} KRO Debug Analizi:")
        print("-" * 30)
        
        try:
            # Fiyat verisi al
            crypto_prices = binance_provider.get_crypto_prices()
            if symbol not in crypto_prices:
                print(f"❌ {symbol} fiyat verisi bulunamadı")
                continue
            
            current_price = crypto_prices[symbol]['price']
            print(f"💰 Current Price: {current_price}")
            
            # Kline verisi al
            klines = binance_provider.get_klines(symbol, '15m', 100)
            print(f"📊 Klines alındı: {len(klines)} adet")
            
            if len(klines) < 50:
                print(f"❌ Yetersiz kline verisi: {len(klines)} < 50")
                continue
            
            # Teknik analiz
            prices = [k['close'] for k in klines]
            rsi = CryptoTechnicalAnalysis.calculate_rsi(prices)
            sr_levels = CryptoTechnicalAnalysis.find_support_resistance(klines)
            atr = CryptoTechnicalAnalysis.calculate_crypto_atr(klines)
            momentum = CryptoTechnicalAnalysis.analyze_crypto_momentum(klines)
            
            print(f"📈 RSI: {rsi}")
            print(f"📊 ATR: {atr:.6f}")
            print(f"📈 Momentum: {momentum['trend']} ({momentum['momentum']:.2f}%)")
            print(f"🎯 Support Levels: {len(sr_levels['support_levels'])}")
            print(f"🎯 Resistance Levels: {len(sr_levels['resistance_levels'])}")
            
            # Support/Resistance detayları
            print("\n🔍 Support Levels Detayı:")
            for i, support in enumerate(sr_levels['support_levels'][:3]):
                break_price = support['level'] * (1 - 0.008)  # %0.8 tolerance
                vol_imp = support.get('volume_importance', {}).get('importance_score', 1.0)
                distance = abs(current_price - support['level']) / support['level'] * 100
                print(f"   Support[{i}]: {support['level']:.2f} | Break@{break_price:.2f} | Distance: {distance:.1f}% | Touches: {support['touches']} | VolImp: {vol_imp:.2f}")
            
            print("\n🔍 Resistance Levels Detayı:")
            for i, resistance in enumerate(sr_levels['resistance_levels'][:3]):
                break_price = resistance['level'] * (1 + 0.008)  # %0.8 tolerance
                vol_imp = resistance.get('volume_importance', {}).get('importance_score', 1.0)
                distance = abs(current_price - resistance['level']) / resistance['level'] * 100
                print(f"   Resistance[{i}]: {resistance['level']:.2f} | Break@{break_price:.2f} | Distance: {distance:.1f}% | Touches: {resistance['touches']} | VolImp: {vol_imp:.2f}")
            
            # Breakout tespiti
            breakout = CryptoTechnicalAnalysis.detect_crypto_breakout(current_price, sr_levels)
            print(f"\n🔍 Breakout Analysis:")
            print(f"   Type: {breakout['breakout_type']}")
            print(f"   Broken Level: {breakout['broken_level']}")
            print(f"   Strength: {breakout['breakout_strength']}")
            
            # Tam KRO analizi yap
            print(f"\n🎯 Full KRO Analysis:")
            signal = kro_strategy.analyze(symbol, current_price)
            
            if signal:
                print(f"✅ KRO SİNYAL ÜRETİLDİ!")
                print(f"   Signal Type: {signal['signal_type']}")
                print(f"   Entry: {signal['ideal_entry']}")
                print(f"   SL: {signal['stop_loss']}")
                print(f"   TP: {signal['take_profit']}")
                print(f"   Reliability: {signal['reliability_score']}")
                print(f"   RR: {signal['risk_reward']}")
            else:
                print(f"❌ KRO SİNYAL ÜRETİLEMEDİ")
                
                # Neden üretilemediğini analiz et
                print(f"\n🔍 Neden Signal Üretilemedi?")
                
                if not breakout['breakout_type']:
                    print(f"   ❌ Breakout tespit edilmedi")
                    print(f"   💡 Çözüm: Tolerance artırılabilir veya daha yakın S/R seviyeleri aranabilir")
                
                # RSI kontrolü
                if not (25 <= rsi <= 75):
                    print(f"   ❌ RSI aralık dışı: {rsi} (ideal: 25-75)")
                else:
                    print(f"   ✅ RSI uygun: {rsi}")
                
                # Momentum kontrolü
                if momentum['trend'] == 'SIDEWAYS':
                    print(f"   ⚠️ Momentum zayıf: {momentum['trend']}")
                else:
                    print(f"   ✅ Momentum güçlü: {momentum['trend']}")
        
        except Exception as e:
            print(f"❌ {symbol} debug hatası: {e}")

def suggest_kro_improvements():
    """KRO stratejisi iyileştirme önerileri"""
    print(f"\n💡 KRO STRATEGY İYİLEŞTİRME ÖNERİLERİ:")
    print("=" * 50)
    print("1. 🎯 Tolerance artırılabilir: %0.8 -> %1.0")
    print("2. 📉 Min reliability düşürülebilir: 4 -> 3")
    print("3. 📊 RSI bandı genişletilebilir: 25-75 -> 20-80")
    print("4. 🔍 Daha yakın S/R seviyeleri kullanılabilir")
    print("5. 📈 Volume spike eşiği düşürülebilir: 1.3x -> 1.2x")

if __name__ == "__main__":
    debug_kro_strategy()
    suggest_kro_improvements() 