#!/usr/bin/env python3
"""
Test amaçlı zorla signal üretme
Tolerance düşürüp sideways market'te bile sinyal alabilelim
"""

import time
from crypto_strategies import get_crypto_strategy_manager, CryptoTechnicalAnalysis
from binance_data import get_binance_provider

def force_generate_signals():
    """Test amaçlı tolerance düşürüp signal üret"""
    
    print("🔧 ZORLA SIGNAL ÜRETME TESTI")
    print("==========================")
    
    # Binance provider başlat
    binance_provider = get_binance_provider()
    crypto_strategy = get_crypto_strategy_manager(binance_provider)
    
    print(f"🎯 Normal tolerance: 0.8%")
    print(f"🎯 Test için minimum reliability'yi düşürüyoruz")
    
    # Min reliability'yi düşür
    original_min_rel = crypto_strategy.kro_strategy.min_reliability
    crypto_strategy.kro_strategy.min_reliability = 1  # Çok düşük
    
    # Crypto fiyatlarını al
    crypto_prices = binance_provider.get_crypto_prices()
    
    all_signals = []
    
    # Sadece BTC test et
    if 'BTC/USD' in crypto_prices:
        symbol = 'BTC/USD'
        price_data = crypto_prices[symbol]
        
        if price_data.get('source') != 'fallback':
            current_price = price_data['price']
            print(f"\n🔍 {symbol} test ediliyor - Fiyat: {current_price}")
            
            try:
                signals = crypto_strategy.analyze_symbol(symbol, current_price)
                
                if signals:
                    print(f"✅ {symbol}: {len(signals)} sinyal üretildi!")
                    for signal in signals:
                        print(f"   📊 {signal['signal_type']} - Güvenilirlik: {signal['reliability_score']}")
                        print(f"   💰 Entry: {signal['ideal_entry']}, TP: {signal['take_profit']}, SL: {signal['stop_loss']}")
                    all_signals.extend(signals)
                else:
                    print(f"❌ {symbol}: Sinyal üretilemedi")
                    
            except Exception as e:
                print(f"❌ {symbol} hatası: {e}")
    
    # Min reliability'yi geri al
    crypto_strategy.kro_strategy.min_reliability = original_min_rel
    
    print(f"\n📊 SONUÇ: {len(all_signals)} toplam sinyal")
    
    if all_signals:
        print("\n🎯 Üretilen Sinyaller:")
        for signal in all_signals:
            print(f"   {signal['symbol']} {signal['signal_type']} - Güvenilirlik: {signal['reliability_score']}")
    else:
        print("\n❌ Hiç sinyal üretilemedi. Manuel test deneyelim:")
        # Manuel BTC testi
        test_manual_btc()
    
    return all_signals

def test_manual_btc():
    """Manuel BTC breakout testi"""
    print("\n🔧 MANUEL BTC BREAKOUT TEST")
    print("===========================")
    
    binance_provider = get_binance_provider()
    crypto_prices = binance_provider.get_crypto_prices()
    
    btc_price = crypto_prices.get('BTC/USD', {}).get('price', 0)
    if not btc_price:
        print("❌ BTC fiyatı alınamadı")
        return
    
    print(f"💰 BTC/USD Price: {btc_price}")
    
    # Manuel S/R seviyeleri oluştur - DOĞRU FORMAT
    sr_levels = {
        'support_levels': [
            {'level': btc_price * 0.995, 'touches': 3},  # %0.5 altında
            {'level': btc_price * 0.99, 'touches': 2}    # %1 altında
        ],
        'resistance_levels': [
            {'level': btc_price * 1.002, 'touches': 4},  # %0.2 üstünde - BREAKOUT POTANSİYELİ
            {'level': btc_price * 1.01, 'touches': 2}    # %1 üstünde
        ]
    }
    
    # Test farklı tolerance değerleri
    tolerances = [0.001, 0.003, 0.005, 0.008]
    
    for tolerance in tolerances:
        breakout = CryptoTechnicalAnalysis.detect_crypto_breakout(btc_price, sr_levels, tolerance)
        print(f"🎯 Tolerance {tolerance*100:.1f}%: {breakout['breakout_type']} (Level: {breakout.get('broken_level', 'None')})")
        
        if breakout['breakout_type'] != 'none':
            print(f"   ✅ BREAKOUT DETECTED! Type: {breakout['breakout_type']}")
            print(f"   💰 Broken Level: {breakout['broken_level']}")
            print(f"   📊 Strength: {breakout['breakout_strength']}")

if __name__ == '__main__':
    force_generate_signals() 