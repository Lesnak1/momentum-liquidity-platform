#!/usr/bin/env python3
"""
Manuel Signal Cache Injection
Server cache'ine zorla signal ekler
"""

import time
from datetime import datetime

def inject_test_signals():
    """Test sinyallerini server cache'ine enjekte et"""
    
    print("🔧 MANUEL SIGNAL ENJEKSİYONU")
    print("============================")
    
    # Manuel test signalleri
    test_signals = {
        "CRYPTO_BTC_USD_1749830000": {
            "id": "CRYPTO_BTC_USD_1749830000",
            "symbol": "BTC/USD", 
            "strategy": "Crypto LMO (Strong)",
            "signal_type": "BUY",
            "current_price": 105200.0,
            "ideal_entry": 105200.0,
            "take_profit": 110000.0,
            "stop_loss": 104800.0,
            "reliability_score": 7,
            "asset_type": "crypto",
            "data_source": "binance",
            "creation_time": datetime.now().isoformat(),
            "status": "ACTIVE",
            "fixed_entry": 105200.0,
            "fixed_tp": 110000.0,
            "fixed_sl": 104800.0,
            "fixed_strategy": "Crypto LMO (Strong)",
            "fixed_signal_type": "BUY",
            "fixed_reliability": 7,
            "ftmo_lot_size": 2.0,
            "ftmo_risk_amount": 100.0,
            "ftmo_risk_percentage": 1.0,
            "ftmo_recommendation": "✅ Düşük Risk - İdeal"
        },
        "CRYPTO_ETH_USD_1749830100": {
            "id": "CRYPTO_ETH_USD_1749830100",
            "symbol": "ETH/USD",
            "strategy": "Crypto KRO (Breakout)",
            "signal_type": "BUY", 
            "current_price": 2540.0,
            "ideal_entry": 2540.0,
            "take_profit": 2650.0,
            "stop_loss": 2510.0,
            "reliability_score": 6,
            "asset_type": "crypto",
            "data_source": "binance",
            "creation_time": datetime.now().isoformat(),
            "status": "ACTIVE",
            "fixed_entry": 2540.0,
            "fixed_tp": 2650.0, 
            "fixed_sl": 2510.0,
            "fixed_strategy": "Crypto KRO (Breakout)",
            "fixed_signal_type": "BUY",
            "fixed_reliability": 6,
            "ftmo_lot_size": 2.0,
            "ftmo_risk_amount": 100.0,
            "ftmo_risk_percentage": 1.0,
            "ftmo_recommendation": "✅ Düşük Risk - İdeal"
        },
        "FOREX_EURUSD_1749830200": {
            "id": "FOREX_EURUSD_1749830200", 
            "symbol": "EURUSD",
            "strategy": "Forex LMO (Smart Money)",
            "signal_type": "SELL",
            "current_price": 1.0890,
            "ideal_entry": 1.0890,
            "take_profit": 1.0850,
            "stop_loss": 1.0910,
            "reliability_score": 5,
            "asset_type": "forex",
            "data_source": "exchangerate-api",
            "creation_time": datetime.now().isoformat(),
            "status": "ACTIVE",
            "fixed_entry": 1.0890,
            "fixed_tp": 1.0850,
            "fixed_sl": 1.0910,
            "fixed_strategy": "Forex LMO (Smart Money)",
            "fixed_signal_type": "SELL",
            "fixed_reliability": 5,
            "ftmo_lot_size": 2.0,
            "ftmo_risk_amount": 100.0,
            "ftmo_risk_percentage": 1.0,
            "ftmo_recommendation": "✅ Düşük Risk - İdeal"
        }
    }
    
    print(f"📊 {len(test_signals)} test sinyali hazırlandı")
    
    # Manuel cache injection - bu global ACTIVE_SIGNALS_CACHE'e direkt eklenmeli
    print("🔧 Manuel cache injection yapılıyor...")
    
    # Cache'i main.py'da manuel güncelle
    import main
    
    # Global cache'e ekle
    for signal_id, signal in test_signals.items():
        main.ACTIVE_SIGNALS_CACHE[signal_id] = signal
        print(f"✅ {signal['symbol']} sinyali cache'e eklendi")
    
    print(f"\n📊 Cache Status: {len(main.ACTIVE_SIGNALS_CACHE)} aktif sinyal")
    
    # Test et
    print("\n🔍 Cache Test:")
    for signal_id, signal in main.ACTIVE_SIGNALS_CACHE.items():
        print(f"   {signal['symbol']} {signal['signal_type']} - Reliability: {signal['fixed_reliability']}")
    
    return len(main.ACTIVE_SIGNALS_CACHE)

if __name__ == '__main__':
    count = inject_test_signals()
    print(f"\n✅ {count} sinyal cache'e enjekte edildi!")
    print("🌐 Frontend'i yenile ve signal'ları gör!") 