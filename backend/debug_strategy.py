#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from crypto_strategies import CryptoStrategyManager
from real_strategies import RealStrategyManager
from binance_data import BinanceDataProvider
from forex_data import ForexDataProvider

def debug_crypto_strategy():
    print("🔍 CRYPTO STRATEJİ DEBUG")
    print("=" * 50)
    
    try:
        # Crypto provider ve strategy oluştur
        provider = BinanceDataProvider()
        strategy = CryptoStrategyManager(provider)
        
        # Test sembolleri
        symbols = ['BTCUSDT', 'ETHUSDT', 'LTCUSDT']
        
        for symbol in symbols:
            print(f"\n📊 {symbol} analiz ediliyor...")
            
            try:
                # Veri al
                print("   📈 Veriler alınıyor...")
                data = provider.get_klines(symbol, '15m', 100)
                
                if not data or len(data) < 50:
                    print(f"   ❌ Yetersiz veri: {len(data) if data else 0} mum")
                    continue
                    
                print(f"   ✅ {len(data)} mum verisi alındı")
                
                # Strateji analizi
                print("   🎯 Stratejiler test ediliyor...")
                current_price = data[-1]['close'] if data else 100.0
                signals = strategy.analyze_symbol(symbol, current_price)
                
                print(f"   📊 Toplam sinyal: {len(signals)}")
                
                for sig in signals[:2]:  # İlk 2 sinyali göster
                    strategy_name = sig.get('strategy', 'unknown')
                    reliability = sig.get('reliability_score', 0)
                    signal_type = sig.get('signal_type', 'unknown')
                    
                    print(f"      📈 {strategy_name}: {signal_type} - {reliability}/10")
                    
                    if reliability >= 4:  # Crypto için threshold
                        print(f"      ✅ {strategy_name} SİNYALİ VAR!")
                    else:
                        print(f"      ❌ {strategy_name} güvenilirlik düşük")
                    
            except Exception as e:
                print(f"   ❌ Hata: {e}")
                
    except Exception as e:
        print(f"❌ Crypto strategy hatası: {e}")
        import traceback
        traceback.print_exc()

def debug_forex_strategy():
    print("\n🔍 FOREX STRATEJİ DEBUG")
    print("=" * 50)
    
    try:
        # Forex provider ve strategy oluştur
        provider = ForexDataProvider()
        strategy = RealStrategyManager(provider)
        
        # Test sembolleri
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        
        for symbol in symbols:
            print(f"\n📊 {symbol} analiz ediliyor...")
            
            try:
                # Veri al
                print("   📈 Veriler alınıyor...")
                data = provider.get_historical_data(symbol, '15m', 100)
                
                if not data or len(data) < 50:
                    print(f"   ❌ Yetersiz veri: {len(data) if data else 0} mum")
                    continue
                    
                print(f"   ✅ {len(data)} mum verisi alındı")
                
                # Analiz yap
                print("   🎯 Stratejiler test ediliyor...")
                current_price = data[-1]['close'] if data else 1.0
                signals = strategy.analyze_symbol(symbol, current_price)
                
                print(f"   📊 Toplam sinyal: {len(signals)}")
                
                for sig in signals[:2]:  # İlk 2 sinyali göster
                    strategy_name = sig.get('strategy', 'unknown')
                    reliability = sig.get('reliability_score', 0)  # reliability_score kullan
                    signal_type = sig.get('signal_type', 'unknown')
                    
                    print(f"      📈 {strategy_name}: {signal_type} - {reliability}/10")
                    
                    if reliability >= 7:  # Forex için threshold
                        print(f"      ✅ {strategy_name} SİNYALİ VAR!")
                    else:
                        print(f"      ❌ {strategy_name} güvenilirlik düşük")
                    
            except Exception as e:
                print(f"   ❌ Hata: {e}")
                
    except Exception as e:
        print(f"❌ Forex strategy hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_crypto_strategy()
    debug_forex_strategy() 