#!/usr/bin/env python3
"""
Cache Debug Script
"""

import main

def debug_cache():
    print("🔍 CACHE DEBUG")
    print("===============")
    print(f"📊 Cache Size: {len(main.ACTIVE_SIGNALS_CACHE)}")
    
    if not main.ACTIVE_SIGNALS_CACHE:
        print("❌ Cache boş!")
        return
        
    for signal_id, signal in main.ACTIVE_SIGNALS_CACHE.items():
        print(f"\n🎯 ID: {signal_id}")
        print(f"   Symbol: {signal.get('symbol', 'N/A')}")
        print(f"   Asset Type: {signal.get('asset_type', 'N/A')}")
        print(f"   Reliability: {signal.get('fixed_reliability', 'N/A')}")
        print(f"   Signal Type: {signal.get('signal_type', 'N/A')}")
        print(f"   Status: {signal.get('status', 'N/A')}")

if __name__ == '__main__':
    debug_cache() 