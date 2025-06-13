#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FTMO Lot Calculator Test
10K FTMO Account için lot size hesaplama testi
"""

from lot_calculator import get_ftmo_calculator

def test_ftmo_calculator():
    """FTMO lot calculator test et"""
    ftmo = get_ftmo_calculator()
    
    print('🎯 FTMO LOT CALCULATOR TEST - 10K ACCOUNT')
    print('=' * 50)
    print(f'💰 Account Balance: ${ftmo.account_balance:,}')
    print(f'📊 Risk per Trade: {ftmo.risk_per_trade*100}%')
    print(f'🔴 Max Daily Risk: {ftmo.max_daily_risk*100}%')
    print()
    
    # Test 1: EURUSD örneği
    result = ftmo.calculate_lot_size('EURUSD', 1.0892, 1.0842)
    print(f'📊 EURUSD Örneği:')
    print(f'   Entry: 1.0892, SL: 1.0842')
    print(f'   ✅ Önerilen Lot: {result["lot_size"]}')
    print(f'   💰 Risk Miktarı: ${result["risk_amount"]}')
    print(f'   📈 Risk %: {result["risk_percentage"]}%')
    print(f'   🎯 Öneri: {result["recommendation"]}')
    print(f'   📏 SL Mesafe: {result["sl_distance_pips"]} pip')
    print()
    
    # Test 2: XAUUSD örneği
    result2 = ftmo.calculate_lot_size('XAUUSD', 2650.0, 2630.0)
    print(f'📊 XAUUSD (Altın) Örneği:')
    print(f'   Entry: $2650, SL: $2630')
    print(f'   ✅ Önerilen Lot: {result2["lot_size"]}')
    print(f'   💰 Risk Miktarı: ${result2["risk_amount"]}')
    print(f'   📈 Risk %: {result2["risk_percentage"]}%')
    print(f'   🎯 Öneri: {result2["recommendation"]}')
    print()
    
    # Test 3: GBPJPY örneği
    result3 = ftmo.calculate_lot_size('GBPJPY', 198.50, 197.00)
    print(f'📊 GBPJPY Örneği:')
    print(f'   Entry: 198.50, SL: 197.00')
    print(f'   ✅ Önerilen Lot: {result3["lot_size"]}')
    print(f'   💰 Risk Miktarı: ${result3["risk_amount"]}')
    print(f'   📈 Risk %: {result3["risk_percentage"]}%')
    print(f'   🎯 Öneri: {result3["recommendation"]}')
    print()
    
    # Test 4: Position value hesaplama
    pos_value = ftmo.calculate_position_value('EURUSD', 0.5, 1.0892)
    print(f'📊 Position Value Hesaplama (0.5 lot EURUSD):')
    print(f'   Position Value: ${pos_value["position_value"]:,}')
    print(f'   Margin Required: ${pos_value["margin_required"]:,}')
    print(f'   Unit Size: {pos_value["unit_size"]}')
    print()
    
    print('✅ FTMO Calculator çalışıyor!')
    print('🎯 Bu bilgiler artık her sinyalde otomatik hesaplanacak')

if __name__ == "__main__":
    test_ftmo_calculator() 