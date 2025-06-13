#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib.request
import sys
import time
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n🔍 {title}")
    print("-" * 40)

def test_server_status():
    """Sunucu durumunu test et"""
    print_section("Server Status Test")
    
    try:
        url = 'http://127.0.0.1:8000/'
        response = urllib.request.urlopen(url, timeout=5)
        data = response.read().decode()
        print("✅ Server çalışıyor")
        return True
    except Exception as e:
        print(f"❌ Server çalışmıyor: {e}")
        return False

def test_api_endpoints():
    """Tüm API endpoint'lerini test et"""
    print_section("API Endpoints Test")
    
    endpoints = [
        ('/signals', 'Forex Sinyalleri'),
        ('/crypto/signals', 'Crypto Sinyalleri'),
        ('/prices', 'Forex Fiyatları'),
        ('/crypto/prices', 'Crypto Fiyatları'),
        ('/statistics', 'İstatistikler'),
        ('/dashboard/performance', 'Performance'),
        ('/dashboard/analytics', 'Analytics')
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            print(f"📡 {name} test ediliyor...")
            url = f'http://127.0.0.1:8000{endpoint}'
            response = urllib.request.urlopen(url, timeout=15)
            data = json.loads(response.read().decode())
            
            print(f"✅ {name}: BAŞARILI")
            
            # Detaylı bilgi göster
            if 'signals' in data:
                signals = data['signals']
                print(f"   📊 Sinyal sayısı: {len(signals)}")
                if signals:
                    latest_signal = signals[0]
                    print(f"   🎯 Son sinyal: {latest_signal.get('symbol', 'N/A')} - {latest_signal.get('strategy', 'N/A')}")
                    print(f"   📈 Signal type: {latest_signal.get('signal_type', 'N/A')}")
                    print(f"   🔥 Güvenilirlik: {latest_signal.get('reliability_score', 'N/A')}")
                    
            elif 'prices' in data:
                prices = data['prices']
                print(f"   💰 Fiyat sayısı: {len(prices)}")
                if prices:
                    latest_price = prices[0]
                    print(f"   💵 Son fiyat: {latest_price.get('symbol', 'N/A')} = {latest_price.get('price', 'N/A')}")
                    
            elif 'statistics' in data:
                stats = data['statistics']
                print(f"   📈 Toplam işlem: {stats.get('total_trades', 'N/A')}")
                print(f"   💸 Toplam kar: ${stats.get('total_profit', 'N/A')}")
                print(f"   🎯 Kazanma oranı: {stats.get('win_rate', 'N/A')}%")
                
            results[endpoint] = {'status': 'OK', 'data': data}
            
        except Exception as e:
            print(f"❌ {name}: HATA - {str(e)}")
            results[endpoint] = {'status': 'ERROR', 'error': str(e)}
    
    return results

def test_strategy_functionality():
    """Strateji fonksiyonlarını test et"""
    print_section("Strategy Functionality Test")
    
    try:
        # KRO & LMO stratejilerini test et
        url = 'http://127.0.0.1:8000/signals'
        response = urllib.request.urlopen(url, timeout=20)
        data = json.loads(response.read().decode())
        
        signals = data.get('signals', [])
        
        # Strateji analizi
        kro_signals = [s for s in signals if 'KRO' in s.get('strategy', '')]
        lmo_signals = [s for s in signals if 'LMO' in s.get('strategy', '')]
        
        print(f"🎯 KRO sinyalleri: {len(kro_signals)}")
        print(f"🌊 LMO sinyalleri: {len(lmo_signals)}")
        
        # Güvenilirlik skorları
        if signals:
            avg_reliability = sum(s.get('reliability_score', 0) for s in signals) / len(signals)
            print(f"📊 Ortalama güvenilirlik: {avg_reliability:.1f}/10")
            
            # Risk/Reward analizi
            rr_ratios = [s.get('risk_reward', 0) for s in signals if s.get('risk_reward', 0) > 0]
            if rr_ratios:
                avg_rr = sum(rr_ratios) / len(rr_ratios)
                print(f"💰 Ortalama Risk/Reward: {avg_rr:.2f}")
        
        print("✅ Strateji testleri tamamlandı")
        return True
        
    except Exception as e:
        print(f"❌ Strateji test hatası: {e}")
        return False

def test_data_providers():
    """Veri sağlayıcıları test et"""
    print_section("Data Provider Test")
    
    try:
        # Forex test
        print("🌍 Forex verileri test ediliyor...")
        url = 'http://127.0.0.1:8000/prices'
        response = urllib.request.urlopen(url, timeout=10)
        forex_data = json.loads(response.read().decode())
        
        if forex_data.get('api_status') == 'connected':
            print("✅ Forex API: Bağlı")
            print(f"   📊 Mevcut çiftler: {len(forex_data.get('prices', []))}")
        else:
            print("❌ Forex API: Bağlantı sorunu")
        
        # Crypto test
        print("🚀 Crypto verileri test ediliyor...")
        url = 'http://127.0.0.1:8000/crypto/prices'
        response = urllib.request.urlopen(url, timeout=10)
        crypto_data = json.loads(response.read().decode())
        
        if crypto_data.get('api_status') == 'connected':
            print("✅ Binance API: Bağlı")
            print(f"   📊 Mevcut çiftler: {len(crypto_data.get('prices', []))}")
        else:
            print("❌ Binance API: Bağlantı sorunu")
            
        return True
        
    except Exception as e:
        print(f"❌ Veri sağlayıcı test hatası: {e}")
        return False

def test_performance():
    """Performans testi"""
    print_section("Performance Test")
    
    test_endpoints = ['/signals', '/crypto/signals', '/prices']
    
    for endpoint in test_endpoints:
        try:
            start_time = time.time()
            url = f'http://127.0.0.1:8000{endpoint}'
            response = urllib.request.urlopen(url, timeout=30)
            data = json.loads(response.read().decode())
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ms
            print(f"⚡ {endpoint}: {response_time:.0f}ms")
            
            if response_time > 5000:
                print(f"   ⚠️  Yavaş yanıt süresi!")
            elif response_time < 1000:
                print(f"   ✅ Hızlı yanıt")
                
        except Exception as e:
            print(f"❌ {endpoint} performans testi hatası: {e}")

def generate_test_report(endpoint_results):
    """Test raporu oluştur"""
    print_header("TEST RAPORU")
    
    total_tests = len(endpoint_results)
    successful_tests = sum(1 for r in endpoint_results.values() if r['status'] == 'OK')
    
    print(f"📊 Toplam Test: {total_tests}")
    print(f"✅ Başarılı: {successful_tests}")
    print(f"❌ Başarısız: {total_tests - successful_tests}")
    print(f"📈 Başarı Oranı: {(successful_tests/total_tests)*100:.1f}%")
    
    print(f"\n🕒 Test Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Detaylı sonuçlar
    print(f"\n📋 Detaylı Sonuçlar:")
    for endpoint, result in endpoint_results.items():
        status_icon = "✅" if result['status'] == 'OK' else "❌"
        print(f"   {status_icon} {endpoint}: {result['status']}")
        if result['status'] == 'ERROR':
            print(f"      Hata: {result['error']}")

def main():
    """Ana test fonksiyonu"""
    print_header("BACKEND COMPREHENSIVE TEST")
    print(f"🕒 Test başlama zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Server durumu
    if not test_server_status():
        print("❌ Server çalışmadığı için test durduruluyor!")
        print("💡 Önce backend sunucusunu başlatın: python simple_server.py")
        return
    
    # Test 2: API Endpoints
    endpoint_results = test_api_endpoints()
    
    # Test 3: Strateji testleri
    test_strategy_functionality()
    
    # Test 4: Veri sağlayıcıları
    test_data_providers()
    
    # Test 5: Performans
    test_performance()
    
    # Test raporu
    generate_test_report(endpoint_results)
    
    print_header("TEST TAMAMLANDI")

if __name__ == "__main__":
    main() 