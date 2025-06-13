"""
Kripto KRO & LMO Stratejileri
Forex ile aynı seviyede detaylı teknik analiz
Gerçek Binance verilerinden TP/SL/ideal giriş hesaplamaları
"""

import time
import random
from datetime import datetime
from typing import Dict, List, Optional
try:
    from advanced_momentum_analysis import EnhancedLMOAnalyzer, AdvancedMomentumAnalyzer, RSIDivergenceDetector
    ENHANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ENHANCED_ANALYSIS_AVAILABLE = False
    print("⚠️ Enhanced analysis modülü bulunamadı, standart analiz kullanılacak")

class CryptoTechnicalAnalysis:
    """Kripto için gerçek teknik analiz"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """RSI hesaplama"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) >= period:
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return round(rsi, 2)
        
        return 50
    
    @staticmethod
    def _calculate_volume_importance(candles: List[Dict], pivot_index: int, lookback_window: int = 5) -> Dict:
        """
        🎯 Volume Cluster Analysis - S/R Seviyelerin Önemini Hesapla
        Swing High/Low etrafındaki volume kümelenmesini analiz eder
        """
        if pivot_index < lookback_window or pivot_index >= len(candles) - lookback_window:
            return {'cluster_strength': 1.0, 'relative_volume': 1.0, 'importance_score': 1.0}
        
        # Pivot noktası ve çevresindeki volume'ler
        pivot_volume = candles[pivot_index]['volume']
        surrounding_volumes = []
        
        # Pivot etrafındaki ±5 periyotluk volume'leri topla
        for i in range(pivot_index - lookback_window, pivot_index + lookback_window + 1):
            if 0 <= i < len(candles):
                surrounding_volumes.append(candles[i]['volume'])
        
        # Genel volume ortalaması (büyük pencere)
        general_window = min(20, len(candles))
        start_idx = max(0, pivot_index - general_window)
        end_idx = min(len(candles), pivot_index + general_window)
        general_volumes = [candles[i]['volume'] for i in range(start_idx, end_idx)]
        
        avg_general_volume = sum(general_volumes) / len(general_volumes) if general_volumes else 1
        avg_surrounding_volume = sum(surrounding_volumes) / len(surrounding_volumes) if surrounding_volumes else 1
        
        # Volume Cluster Strength: Çevre volume'ün genel volume'e oranı
        cluster_strength = avg_surrounding_volume / avg_general_volume if avg_general_volume > 0 else 1.0
        
        # Relative Volume: Pivot volume'ün çevre volume'e oranı  
        relative_volume = pivot_volume / avg_surrounding_volume if avg_surrounding_volume > 0 else 1.0
        
        # Importance Score: Birleşik önem skoru (1.0-5.0 arası)
        importance_score = min(5.0, (cluster_strength * 0.6 + relative_volume * 0.4))
        
        return {
            'cluster_strength': round(cluster_strength, 2),
            'relative_volume': round(relative_volume, 2), 
            'importance_score': round(importance_score, 2),
            'pivot_volume': pivot_volume,
            'avg_surrounding_volume': round(avg_surrounding_volume, 2),
            'avg_general_volume': round(avg_general_volume, 2)
        }
    
    @staticmethod
    def find_support_resistance(candles: List[Dict], lookback: int = 50) -> Dict:
        """Kripto için gerçek S/R seviyeleri"""
        if len(candles) < lookback:
            return {'support_levels': [], 'resistance_levels': []}
        
        recent_candles = candles[-lookback:]
        support_levels = []
        resistance_levels = []
        
        # Swing points - kripto için daha hassas
        for i in range(3, len(recent_candles) - 3):
            current_high = recent_candles[i]['high']
            current_low = recent_candles[i]['low']
            
            # Resistance (3 periyotluk swing high)
            is_swing_high = True
            for j in range(i-3, i+4):
                if j != i and recent_candles[j]['high'] > current_high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                # 🎯 Volume Cluster Analysis for S/R Importance
                volume_importance = CryptoTechnicalAnalysis._calculate_volume_importance(recent_candles, i)
                
                resistance_levels.append({
                    'level': current_high,
                    'timestamp': recent_candles[i]['timestamp'],
                    'touches': 1,
                    'volume': recent_candles[i]['volume'],
                    'volume_importance': volume_importance,  # Yeni: Volume önem skoru
                    'volume_cluster_strength': volume_importance['cluster_strength']  # Çevre volume gücü
                })
            
            # Support (3 periyotluk swing low)
            is_swing_low = True
            for j in range(i-3, i+4):
                if j != i and recent_candles[j]['low'] < current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                # 🎯 Volume Cluster Analysis for S/R Importance
                volume_importance = CryptoTechnicalAnalysis._calculate_volume_importance(recent_candles, i)
                
                support_levels.append({
                    'level': current_low,
                    'timestamp': recent_candles[i]['timestamp'],
                    'touches': 1,
                    'volume': recent_candles[i]['volume'],
                    'volume_importance': volume_importance,  # Yeni: Volume önem skoru
                    'volume_cluster_strength': volume_importance['cluster_strength']  # Çevre volume gücü
                })
        
        # Kripto için daha hassas clustering (volatilite yüksek)
        def consolidate_levels(levels, tolerance=0.015):  # %1.5 tolerance
            if not levels:
                return []
            
            consolidated = []
            for level in levels:
                price = level['level']
                merged = False
                
                for existing in consolidated:
                    if abs(price - existing['level']) / existing['level'] < tolerance:
                        # Volume + Importance ağırlıklı ortalama
                        existing_weight = existing['volume'] * existing['volume_importance']['importance_score']
                        new_weight = level['volume'] * level['volume_importance']['importance_score']
                        total_weight = existing_weight + new_weight
                        
                        existing['level'] = ((existing['level'] * existing_weight) + 
                                           (price * new_weight)) / total_weight
                        existing['touches'] += 1
                        existing['volume'] = existing['volume'] + level['volume']
                        
                        # Volume importance'ı birleştir (daha yüksek olanı al)
                        if level['volume_importance']['importance_score'] > existing['volume_importance']['importance_score']:
                            existing['volume_importance'] = level['volume_importance']
                            existing['volume_cluster_strength'] = level['volume_cluster_strength']
                        
                        merged = True
                        break
                
                if not merged:
                    consolidated.append(level)
            
            # 🎯 Volume Importance bazlı akıllı sıralama
            # Öncelik: touches * volume_importance_score * volume
            def calculate_priority(level):
                importance = level['volume_importance']['importance_score']
                return level['touches'] * importance * (level['volume'] / 1000000)  # Volume normalizasyonu
            
            return sorted(consolidated, key=calculate_priority, reverse=True)[:6]
        
        return {
            'support_levels': consolidate_levels(support_levels),
            'resistance_levels': consolidate_levels(resistance_levels)
        }
    
    @staticmethod
    def detect_crypto_breakout(current_price: float, sr_levels: Dict, tolerance: float = 0.008) -> Dict:
        """
        Multi-timeframe destekli crypto breakout tespiti
        Priority: 1D > 4H > 15M
        """
        breakout_result = {
            'breakout_type': None,
            'broken_level': None,
            'breakout_strength': 0,
            'volume_importance_score': 1.0,
            'broken_level_info': None  # Yeni: hangi TF'den geldiği bilgisi
        }
        
        # Kırılım toleransı
        upper_tolerance = 1 + tolerance
        lower_tolerance = 1 - tolerance
        
        # Priority sırasına göre kontrol et (HIGH > MEDIUM > LOW)
        for priority_level in ['HIGH', 'MEDIUM', 'LOW']:
            
            # RESISTANCE BREAK kontrolü (priority sırasına göre)
            resistance_candidates = []
            for resistance in sr_levels.get('resistance_levels', []):
                if resistance.get('priority') == priority_level:
                    resistance_candidates.append(resistance)
            
            # En yakın resistance'ı bul (bu priority seviyesinde)
            resistance_candidates.sort(key=lambda r: abs(r['level'] - current_price))
            
            for resistance in resistance_candidates:
                resistance_level = resistance['level']
                break_threshold = resistance_level * upper_tolerance
                
                if current_price > break_threshold:
                    # Kırılım tespit edildi!
                    touches = resistance.get('touches', 1)
                    volume_importance = resistance.get('volume_importance', {}).get('importance_score', 1.0)
                    strength = touches * volume_importance
                    
                    # Priority bonus ekle
                    if priority_level == 'HIGH':
                        strength *= 1.5  # Daily level kırılımı daha güçlü
                    elif priority_level == 'MEDIUM':
                        strength *= 1.2  # 4H level kırılımı orta güçlü
                    
                    breakout_result.update({
                        'breakout_type': 'RESISTANCE_BREAK',
                        'broken_level': resistance_level,
                        'breakout_strength': min(strength, 10),  # Max 10
                        'volume_importance_score': volume_importance,
                        'broken_level_info': {
                            'timeframe': resistance.get('timeframe', '15M'),
                            'priority': priority_level,
                            'touches': touches
                        }
                    })
                    return breakout_result
            
            # SUPPORT BREAK kontrolü (priority sırasına göre)
            support_candidates = []
            for support in sr_levels.get('support_levels', []):
                if support.get('priority') == priority_level:
                    support_candidates.append(support)
            
            # En yakın support'ı bul (bu priority seviyesinde)
            support_candidates.sort(key=lambda s: abs(s['level'] - current_price))
            
            for support in support_candidates:
                support_level = support['level']
                break_threshold = support_level * lower_tolerance
                
                if current_price < break_threshold:
                    # Kırılım tespit edildi!
                    touches = support.get('touches', 1)
                    volume_importance = support.get('volume_importance', {}).get('importance_score', 1.0)
                    strength = touches * volume_importance
                    
                    # Priority bonus ekle
                    if priority_level == 'HIGH':
                        strength *= 1.5  # Daily level kırılımı daha güçlü
                    elif priority_level == 'MEDIUM':
                        strength *= 1.2  # 4H level kırılımı orta güçlü
                    
                    breakout_result.update({
                        'breakout_type': 'SUPPORT_BREAK',
                        'broken_level': support_level,
                        'breakout_strength': min(strength, 10),  # Max 10
                        'volume_importance_score': volume_importance,
                        'broken_level_info': {
                            'timeframe': support.get('timeframe', '15M'),
                            'priority': priority_level,
                            'touches': touches
                        }
                    })
                    return breakout_result
        
        return breakout_result
    
    @staticmethod
    def detect_liquidity_sweep(candles: List[Dict], current_price: float) -> Dict:
        """
        DAHA ESNEK Liquidity Sweep Tespiti
        KRİTİK: Crypto volatilitesi için gevşetilmiş SMC kuralları
        """
        if len(candles) < 30:  # Daha az veri gereksinimi
            return {'sweep_detected': False}
        
        # Son 30 mumun analizi (12.5 saat 4H veya 7.5 saat 15M)
        recent_candles = candles[-30:]
        
        # Equal Highs/Lows tespiti - ULTRA ESNEK tolerans
        tolerance = 0.025  # %2.5 - Ultra esnek crypto standart
        
        # Swing High/Low seviyeleri - 3 periyot confirmation (daha esnek)
        swing_highs = []
        swing_lows = []
        
        for i in range(3, len(recent_candles) - 3):
            current_high = recent_candles[i]['high']
            current_low = recent_candles[i]['low']
            
            # Swing High: 3 periyot öncesi ve sonrası kontrol
            is_swing_high = True
            for j in range(i-3, i+4):
                if j != i and recent_candles[j]['high'] >= current_high:
                    is_swing_high = False
                    break
            if is_swing_high:
                swing_highs.append({
                    'price': current_high,
                    'index': i,
                    'volume': recent_candles[i]['volume']
                })
            
            # Swing Low: 3 periyot öncesi ve sonrası kontrol  
            is_swing_low = True
            for j in range(i-3, i+4):
                if j != i and recent_candles[j]['low'] <= current_low:
                    is_swing_low = False
                    break
            if is_swing_low:
                swing_lows.append({
                    'price': current_low,
                    'index': i,
                    'volume': recent_candles[i]['volume']
                })
        
        # Equal Highs clustering - minimum 1 touch bile yeterli (ultra esnek)
        equal_high_clusters = []
        for high in swing_highs:
            cluster = [h for h in swing_highs if abs(h['price'] - high['price']) / high['price'] < tolerance]
            if len(cluster) >= 1:  # Minimum 1 dokunuş bile yeterli (ultra esnek)
                avg_price = sum(h['price'] for h in cluster) / len(cluster)
                total_volume = sum(h['volume'] for h in cluster)
                equal_high_clusters.append({
                    'level': avg_price,
                    'touches': len(cluster),
                    'volume': total_volume
                })
        
        # Equal Lows clustering - minimum 1 touch bile yeterli (ultra esnek)
        equal_low_clusters = []
        for low in swing_lows:
            cluster = [l for l in swing_lows if abs(l['price'] - low['price']) / low['price'] < tolerance]
            if len(cluster) >= 1:  # Minimum 1 dokunuş bile yeterli (ultra esnek)
                avg_price = sum(l['price'] for l in cluster) / len(cluster)
                total_volume = sum(l['volume'] for l in cluster)
                equal_low_clusters.append({
                    'level': avg_price,
                    'touches': len(cluster),
                    'volume': total_volume
                })
        
        # 🚀 PROFESYONEL ATR Bazlı Liquidity Sweep Kontrolü
        # 4H ATR hesapla (volatiliteye göre dinamik sweep detection)
        atr_4h = CryptoTechnicalAnalysis.calculate_crypto_atr(candles, 14)
        atr_multiplier_for_sweep = 0.3  # ATR'nin %30'u kadar aşma yeterli
        
        # Dinamik penetration amount - volatiliteye göre adaptif
        penetration_amount = atr_4h * atr_multiplier_for_sweep
        
        # 🔍 DEBUG: Liquidity Sweep tespiti detayları
        print(f"🔍 LMO Debug: Swings High={len(swing_highs)}, Low={len(swing_lows)}")
        print(f"🔍 LMO Debug: Clusters High={len(equal_high_clusters)}, Low={len(equal_low_clusters)}")
        print(f"🔍 LMO Debug: ATR={atr_4h:.2f}, Penetration={penetration_amount:.2f}")
        print(f"🔍 LMO Debug: Current Price={current_price}")
        
        for cluster in equal_high_clusters:
            # ATR bazlı dinamik aşma kontrolü - piyasa volatilitesine uyumlu
            if current_price > cluster['level'] + penetration_amount:
                return {
                    'sweep_detected': True,
                    'sweep_type': 'HIGH_SWEEP',
                    'swept_level': cluster['level'],
                    'liquidity_strength': cluster['touches'],
                    'volume_confirmation': cluster['volume'] > 5000,
                    'penetration_amount': round(penetration_amount, 2),  # Debug için
                    'atr_4h': round(atr_4h, 2)  # Debug için
                }
        
        for cluster in equal_low_clusters:
            # ATR bazlı dinamik düşüş kontrolü - piyasa volatilitesine uyumlu
            if current_price < cluster['level'] - penetration_amount:
                return {
                    'sweep_detected': True,
                    'sweep_type': 'LOW_SWEEP',
                    'swept_level': cluster['level'],
                    'liquidity_strength': cluster['touches'],
                    'volume_confirmation': cluster['volume'] > 5000,
                    'penetration_amount': round(penetration_amount, 2),  # Debug için
                    'atr_4h': round(atr_4h, 2)  # Debug için
                }
        
        return {'sweep_detected': False}
    
    @staticmethod
    def calculate_crypto_atr(candles: List[Dict], period: int = 14) -> float:
        """Kripto ATR - volatilite hesaplama"""
        if len(candles) < period + 1:
            return 0.05  # Kripto için default %5
        
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        if len(true_ranges) >= period:
            atr = sum(true_ranges[-period:]) / period
            return atr
        
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0.05
    
    @staticmethod
    def analyze_crypto_momentum(candles: List[Dict]) -> Dict:
        """Kripto momentum analizi"""
        if len(candles) < 20:
            return {'momentum': 0, 'trend': 'SIDEWAYS'}
        
        # Fiyat momentum (20 periyot)
        prices = [c['close'] for c in candles[-20:]]
        price_momentum = (prices[-1] - prices[0]) / prices[0] * 100
        
        # Volume trend
        volumes = [c['volume'] for c in candles[-10:]]
        volume_trend = sum(volumes[-5:]) / sum(volumes[:5]) if sum(volumes[:5]) > 0 else 1
        
        # Trend belirleme
        if price_momentum > 2:
            trend = 'BULLISH'
        elif price_momentum < -2:
            trend = 'BEARISH'
        else:
            trend = 'SIDEWAYS'
        
        return {
            'momentum': round(price_momentum, 2),
            'volume_trend': round(volume_trend, 2),
            'trend': trend
        }

class CryptoKROStrategy:
    """
    Kripto KRO Stratejisi: Kırılım + Retest + Onay - 15M TIMEFRAME
    Forex ile aynı detay seviyesinde
    """
    
    def __init__(self, binance_provider):
        self.name = "Crypto KRO"
        self.description = "Kripto Kırılım + Retest + Onay (15M Binance Verileri)"
        self.binance_provider = binance_provider
        self.min_reliability = 7  # FTMO Professional: Yüksek kalite sinyal
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """15M timeframe ile gerçek kripto KRO analizi"""
        try:
            print(f"🔍 {symbol} KRO analizi başlıyor - Fiyat: {current_price}")
            
            # PROFESYONEL MULTI-TIMEFRAME VERİ TOPLAMA
            # 15M ana analiz için genişletilmiş veri seti
            klines_15m = self.binance_provider.get_klines(symbol, '15m', 300)  # 300 -> 75 saat
            
            # Daily context için 1D veriler
            klines_1d = self.binance_provider.get_klines(symbol, '1d', 90)    # 90 gün günlük
            
            # 4H veriler majör S/R için
            klines_4h = self.binance_provider.get_klines(symbol, '4h', 200)   # 200 -> 33 gün
            
            if len(klines_15m) < 100 or len(klines_1d) < 30 or len(klines_4h) < 50:
                print(f"❌ {symbol} KRO: Yetersiz multi-timeframe verisi (15M:{len(klines_15m)}, 1D:{len(klines_1d)}, 4H:{len(klines_4h)})")
                return None
            
            print(f"✅ {symbol} KRO Professional: 15M:{len(klines_15m)}, 1D:{len(klines_1d)}, 4H:{len(klines_4h)} mum verisi")
            
            # DAILY TREND CONTEXT ANALİZİ
            daily_prices = [k['close'] for k in klines_1d]
            daily_trend = 'BULLISH' if daily_prices[-1] > daily_prices[-10] else 'BEARISH'
            weekly_trend = 'BULLISH' if daily_prices[-1] > daily_prices[-30] else 'BEARISH'
            
            print(f"📊 {symbol} Context: Daily={daily_trend}, Weekly={weekly_trend}")
            
            # MAJÖR SUPPORT/RESISTANCE (4H + 1D kombine)
            sr_levels_4h = CryptoTechnicalAnalysis.find_support_resistance(klines_4h, lookback=100)
            sr_levels_1d = CryptoTechnicalAnalysis.find_support_resistance(klines_1d, lookback=60)
            
            # 15M için detaylı analiz
            sr_levels_15m = CryptoTechnicalAnalysis.find_support_resistance(klines_15m, lookback=150)
            
            # Teknik analiz
            prices = [k['close'] for k in klines_15m]
            rsi = CryptoTechnicalAnalysis.calculate_rsi(prices)
            atr = CryptoTechnicalAnalysis.calculate_crypto_atr(klines_15m)
            momentum = CryptoTechnicalAnalysis.analyze_crypto_momentum(klines_15m)
            
            print(f"🔍 {symbol} KRO Teknik: RSI={rsi}, ATR={atr:.6f}, Momentum={momentum['trend']}")
            print(f"🔍 {symbol} KRO S/R: 15M={len(sr_levels_15m['support_levels'])}, 4H={len(sr_levels_4h['support_levels'])}, 1D={len(sr_levels_1d['support_levels'])}")
            
            # MAJÖR LEVEL PRIORITY SİSTEMİ
            # 1D > 4H > 15M priority sıralaması
            all_support_levels = []
            all_resistance_levels = []
            
            # Daily levels (en yüksek priority)
            for level in sr_levels_1d['support_levels']:
                level['priority'] = 'HIGH'
                level['timeframe'] = '1D'
                all_support_levels.append(level)
                
            for level in sr_levels_1d['resistance_levels']:
                level['priority'] = 'HIGH' 
                level['timeframe'] = '1D'
                all_resistance_levels.append(level)
            
            # 4H levels (orta priority)
            for level in sr_levels_4h['support_levels']:
                level['priority'] = 'MEDIUM'
                level['timeframe'] = '4H'
                all_support_levels.append(level)
                
            for level in sr_levels_4h['resistance_levels']:
                level['priority'] = 'MEDIUM'
                level['timeframe'] = '4H'
                all_resistance_levels.append(level)
            
            # 15M levels (düşük priority)
            for level in sr_levels_15m['support_levels']:
                level['priority'] = 'LOW'
                level['timeframe'] = '15M'
                all_support_levels.append(level)
                
            for level in sr_levels_15m['resistance_levels']:
                level['priority'] = 'LOW'
                level['timeframe'] = '15M'
                all_resistance_levels.append(level)
            
            # Kombine S/R levels
            combined_sr_levels = {
                'support_levels': all_support_levels,
                'resistance_levels': all_resistance_levels
            }
            
            # KRO 15M Analizi - MULTI-TIMEFRAME Kırılım tespiti
            breakout = CryptoTechnicalAnalysis.detect_crypto_breakout(current_price, combined_sr_levels)
            
            # 🔍 DEBUG: KRO Breakout tespiti detayları
            print(f"🔍 KRO Debug: Current Price={current_price}")
            for i, support in enumerate(sr_levels_15m['support_levels']):
                break_price = support['level'] * (1 - 0.008)  # %0.8 tolerance (optimal for crypto)
                vol_imp = support.get('volume_importance', {}).get('importance_score', 1.0)
                print(f"🔍 KRO Debug: Support[{i}]={support['level']:.2f}, Break@={break_price:.2f}, Touches={support['touches']}, VolImp={vol_imp}")
            for i, resistance in enumerate(sr_levels_15m['resistance_levels']):
                break_price = resistance['level'] * (1 + 0.008)  # %0.8 tolerance (optimal for crypto)
                vol_imp = resistance.get('volume_importance', {}).get('importance_score', 1.0)
                print(f"🔍 KRO Debug: Resistance[{i}]={resistance['level']:.2f}, Break@={break_price:.2f}, Touches={resistance['touches']}, VolImp={vol_imp}")
            
            if not breakout['breakout_type']:
                print(f"❌ {symbol} KRO: 15M kırılım tespit edilmedi")
                return None
            
            print(f"✅ {symbol} KRO: {breakout['breakout_type']} tespit edildi - Seviye: {breakout['broken_level']}")
            
            # Güvenilirlik skoru
            reliability_score = 0
            signal_type = None
            analysis_details = []
            
            # 🎯 MULTI-TIMEFRAME BREAKOUT BONUS SYSTEM
            volume_enhanced_strength = breakout['breakout_strength']
            reliability_score += min(volume_enhanced_strength, 3)  # 4'ten 3'e düşür
            
            # MAJOR TIMEFRAME KIRIILIM BONUSU - AZALTILDI
            major_tf_bonus = 0
            if breakout.get('broken_level_info'):
                broken_level_tf = breakout['broken_level_info'].get('timeframe', '15M')
                broken_level_priority = breakout['broken_level_info'].get('priority', 'LOW')
                
                if broken_level_priority == 'HIGH':  # 1D level break
                    major_tf_bonus += 2  # 3'ten 2'ye düşür
                    analysis_details.append(f"🔥 DAILY LEVEL BREAK: {broken_level_tf}")
                elif broken_level_priority == 'MEDIUM':  # 4H level break  
                    major_tf_bonus += 1  # 2'den 1'e düşür
                    analysis_details.append(f"⚡ 4H LEVEL BREAK: {broken_level_tf}")
                else:  # 15M level break
                    major_tf_bonus += 0.5  # 1'den 0.5'e düşür
                    analysis_details.append(f"📊 15M Level Break")
            
            reliability_score += major_tf_bonus
            
            # TREND ALIGNMENT BONUS - AZALTILDI
            trend_alignment_bonus = 0
            if breakout['breakout_type'] == 'RESISTANCE_BREAK':
                if daily_trend == 'BULLISH' and weekly_trend == 'BULLISH':
                    trend_alignment_bonus = 2  # 3'ten 2'ye
                    analysis_details.append("🎯 Full Trend Alignment (Daily+Weekly Bullish)")
                elif daily_trend == 'BULLISH':
                    trend_alignment_bonus = 1  # Aynı
                    analysis_details.append("📈 Daily Trend Alignment")
            elif breakout['breakout_type'] == 'SUPPORT_BREAK':
                if daily_trend == 'BEARISH' and weekly_trend == 'BEARISH':
                    trend_alignment_bonus = 2  # 3'ten 2'ye
                    analysis_details.append("🎯 Full Trend Alignment (Daily+Weekly Bearish)")
                elif daily_trend == 'BEARISH':
                    trend_alignment_bonus = 1  # Aynı
                    analysis_details.append("📉 Daily Trend Alignment")
            
            reliability_score += trend_alignment_bonus
            
            vol_score = breakout.get('volume_importance_score', 1.0)
            analysis_details.append(f"Multi-TF Kırılım: {breakout['breakout_type']} (VolImp:{vol_score})")
            
            # RSI kontrolü (15M) - Azaltılmış skorlama
            if 25 <= rsi <= 75:  # Crypto için geniş bant
                reliability_score += 1  # 2'den 1'e düşür
                analysis_details.append(f"15M RSI uygun: {rsi}")
            elif 15 <= rsi <= 85:  # Orta düzey uygun
                reliability_score += 1  # Küsurat yerine tam sayı
                analysis_details.append(f"15M RSI kabul edilebilir: {rsi}")
            
            # Momentum kontrolü (15M) - Tam sayı skorlama
            if momentum['trend'] == 'BULLISH' or momentum['trend'] == 'BEARISH':
                reliability_score += 1  # Aynı kalsın
                analysis_details.append(f"15M Güçlü momentum: {momentum['trend']}")
            elif momentum['trend'] == 'SIDEWAYS':
                reliability_score += 1  # Küsurat yerine tam sayı
                analysis_details.append(f"15M Nötr momentum")
            
            # Volume kontrolü - Tam sayı puan
            if len(klines_15m) >= 20:
                recent_volumes = [k['volume'] for k in klines_15m[-20:]]
                avg_volume = sum(recent_volumes) / len(recent_volumes)
                current_volume = klines_15m[-1]['volume']
                
                if current_volume > avg_volume * 1.3:  # %30 fazla volume
                    reliability_score += 1  # Aynı kalsın
                    analysis_details.append(f"15M Volume spike: {current_volume/avg_volume:.1f}x")
                elif current_volume > avg_volume * 1.1:  # %10 fazla volume
                    reliability_score += 1  # Küsurat yerine tam sayı
                    analysis_details.append(f"15M Volume artışı: {current_volume/avg_volume:.1f}x")
            
            # ATR bazlı volatilite puanı - Tam sayı
            volatility_ratio = atr / current_price
            if 0.01 <= volatility_ratio <= 0.05:  # İdeal volatilite
                reliability_score += 1  # Küsurat yerine tam sayı
                analysis_details.append(f"İdeal volatilite: {volatility_ratio*100:.1f}%")
            
            # Price action konfirmasyonu - Tam sayı
            if len(klines_15m) >= 3:
                last_3_candles = klines_15m[-3:]
                green_candles = sum(1 for c in last_3_candles if c['close'] > c['open'])
                red_candles = sum(1 for c in last_3_candles if c['close'] < c['open'])
                
                if (breakout['breakout_type'] == 'RESISTANCE_BREAK' and green_candles >= 2) or \
                   (breakout['breakout_type'] == 'SUPPORT_BREAK' and red_candles >= 2):
                    reliability_score += 1  # Küsurat yerine tam sayı
                    analysis_details.append("Price action onayı")
            
            # Sinyal yönü belirleme
            if breakout['breakout_type'] == 'RESISTANCE_BREAK':
                signal_type = "BUY"
            elif breakout['breakout_type'] == 'SUPPORT_BREAK':
                signal_type = "SELL"
            
            print(f"🔍 {symbol} KRO Güvenilirlik: {reliability_score} (min: {self.min_reliability})")
            
            if reliability_score < self.min_reliability:
                print(f"❌ {symbol} KRO: Güvenilirlik düşük ({reliability_score} < {self.min_reliability})")
                return None
            
            # Crypto KRO TP/SL (15M bazlı - sıkı ama iyi RR ile)
            broken_level = breakout['broken_level']
            
            # Volatilite bazlı hesaplama
            volatility_factor = max(atr / current_price, 0.015)  # Min %1.5 volatilite
            
            if signal_type == "BUY":
                # Giriş: Kırılım seviyesinin biraz üzerinde
                ideal_entry = max(current_price, broken_level * 1.005)  # %0.5 buffer
                
                # 🎯 ATR-Based Adaptive Stop Loss (Profesyonel Kripto Standartları)
                # broken_level ± (ATR * 1.0) - piyasa volatilitesine adaptif
                atr_based_sl = broken_level - (atr * 1.0)  # ATR 1.0x multiplier
                percentage_based_sl = broken_level * 0.992  # %0.8 minimum buffer
                
                # Güvenlik için her iki hesabın daha geniş olanını kullan
                stop_loss = min(atr_based_sl, percentage_based_sl)
                
                print(f"🔍 {symbol} BUY SL: ATR-based={atr_based_sl:.2f}, Fixed-based={percentage_based_sl:.2f}, Final={stop_loss:.2f}")
                
                # Take Profit: Volatiliteye göre dinamik TP
                # ATR'nin 3 katı VEYA %2.5 volatilite - hangisi büyükse
                tp_atr_based = ideal_entry + (atr * 3.0)
                tp_volatility_based = ideal_entry * (1 + volatility_factor * 2.5)
                take_profit = max(tp_atr_based, tp_volatility_based)
                
                # Next resistance varsa ve çok uzaksa TP'yi limitle
                for r in sr_levels_15m['resistance_levels']:
                    if r['level'] > current_price:
                        # Resistance çok uzaksa (>%5) TP'yi sınırla
                        if (r['level'] - current_price) / current_price > 0.05:
                            take_profit = min(take_profit, r['level'] * 0.998)
                        break
                        
            else:  # SELL
                # Giriş: Kırılım seviyesinin biraz altında
                ideal_entry = min(current_price, broken_level * 0.995)  # %0.5 buffer
                
                # 🎯 ATR-Based Adaptive Stop Loss (Profesyonel Kripto Standartları)
                # broken_level ± (ATR * 1.0) - piyasa volatilitesine adaptif
                atr_based_sl = broken_level + (atr * 1.0)  # ATR 1.0x multiplier
                percentage_based_sl = broken_level * 1.008  # %0.8 minimum buffer
                
                # Güvenlik için her iki hesabın daha geniş olanını kullan
                stop_loss = max(atr_based_sl, percentage_based_sl)
                
                print(f"🔍 {symbol} SELL SL: ATR-based={atr_based_sl:.2f}, Fixed-based={percentage_based_sl:.2f}, Final={stop_loss:.2f}")
                
                # Take Profit: Volatiliteye göre dinamik TP
                tp_atr_based = ideal_entry - (atr * 3.0)
                tp_volatility_based = ideal_entry * (1 - volatility_factor * 2.5)
                take_profit = min(tp_atr_based, tp_volatility_based)
                
                # Next support varsa ve çok uzaksa TP'yi limitle
                for s in sr_levels_15m['support_levels']:
                    if s['level'] < current_price:
                        # Support çok uzaksa (>%5) TP'yi sınırla
                        if (current_price - s['level']) / current_price > 0.05:
                            take_profit = max(take_profit, s['level'] * 1.002)
                        break
            
            # Risk/Reward kontrolü ve iyileştirme
            risk = abs(ideal_entry - stop_loss)
            reward = abs(take_profit - ideal_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            # Eğer RR düşükse TP'yi genişlet
            if risk_reward < 1.3:
                if signal_type == "BUY":
                    # TP'yi %20 daha genişlet
                    take_profit = ideal_entry + (reward * 1.5)
                else:
                    # TP'yi %20 daha genişlet
                    take_profit = ideal_entry - (reward * 1.5)
                
                # Yeni RR hesapla
                reward = abs(take_profit - ideal_entry)
                risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            print(f"✅ {symbol} KRO sinyali oluşturuldu: {signal_type} RR:{risk_reward} Güvenilirlik:{reliability_score}")
            
            return {
                'id': f"CRYPTO_KRO_15M_{symbol.replace('/', '')}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'Crypto KRO',
                'signal_type': signal_type,
                'current_price': current_price,
                'ideal_entry': round(ideal_entry, 6),
                'stop_loss': round(stop_loss, 6),
                'take_profit': round(take_profit, 6),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '15m',  # KRO için 15M
                'status': 'NEW',
                'analysis': f"15M Crypto KRO: {', '.join(analysis_details)}",
                'risk_reward': risk_reward,
                'breakout_level': broken_level,
                'atr': round(atr, 6),
                'momentum': momentum['momentum'],
                'asset_type': 'crypto'
            }
            
        except Exception as e:
            print(f"❌ Crypto KRO analiz hatası {symbol}: {e}")
            return None

class CryptoLMOStrategy:
    """
    Kripto LMO Stratejisi: Liquidity Sweep + Momentum Onayı - 4H TIMEFRAME
    Forex ile aynı detay seviyesinde
    """
    
    def __init__(self, binance_provider):
        self.name = "Crypto LMO"
        self.description = "Kripto Liquidity Sweep + Momentum Onayı (4H Binance Verileri)"
        self.binance_provider = binance_provider
        self.min_reliability = 6  # FTMO Professional: Smart Money tespit için yüksek kalite
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """4H timeframe ile gerçek kripto LMO analizi"""
        try:
            print(f"🔍 {symbol} LMO analizi başlıyor - Fiyat: {current_price}")
            
            # PROFESYONEL MULTI-TIMEFRAME VERİ TOPLAMA
            # 4H ana analiz için genişletilmiş veri seti
            klines_4h = self.binance_provider.get_klines(symbol, '4h', 200)   # 200 -> 33 gün
            
            # Weekly context için 1W veriler
            klines_1w = self.binance_provider.get_klines(symbol, '1w', 52)    # 52 hafta = 1 yıl
            
            # Daily context için 1D veriler  
            klines_1d = self.binance_provider.get_klines(symbol, '1d', 120)   # 120 gün = 4 ay
            
            # Entry timing için 15M veriler
            klines_15m = self.binance_provider.get_klines(symbol, '15m', 100)  # 100 -> 25 saat
            
            if len(klines_4h) < 100 or len(klines_1d) < 60 or len(klines_15m) < 50 or len(klines_1w) < 20:
                print(f"❌ {symbol} LMO: Yetersiz multi-timeframe verisi (4H:{len(klines_4h)}, 1D:{len(klines_1d)}, 1W:{len(klines_1w)}, 15M:{len(klines_15m)})")
                return None
            
            print(f"✅ {symbol} LMO Professional: 4H:{len(klines_4h)}, 1D:{len(klines_1d)}, 1W:{len(klines_1w)}, 15M:{len(klines_15m)} mum verisi")
            
            # WEEKLY/DAILY TREND CONTEXT ANALİZİ
            weekly_prices = [k['close'] for k in klines_1w]
            daily_prices = [k['close'] for k in klines_1d]
            
            weekly_trend = 'BULLISH' if weekly_prices[-1] > weekly_prices[-8] else 'BEARISH'  # 8 hafta
            monthly_trend = 'BULLISH' if weekly_prices[-1] > weekly_prices[-16] else 'BEARISH'  # 16 hafta ~ 4 ay
            daily_trend = 'BULLISH' if daily_prices[-1] > daily_prices[-14] else 'BEARISH'  # 14 gün
            
            print(f"📊 {symbol} LMO Context: Weekly={weekly_trend}, Monthly={monthly_trend}, Daily={daily_trend}")
            
            # MAJÖR LIQUIDITY ZONES (1W + 1D + 4H kombine)
            # Weekly zones - en güçlü liquidity seviyeleri
            weekly_highs = [k['high'] for k in klines_1w[-20:]]  # Son 20 hafta
            weekly_lows = [k['low'] for k in klines_1w[-20:]]
            major_weekly_high = max(weekly_highs)
            major_weekly_low = min(weekly_lows)
            
            # Daily zones
            daily_highs = [k['high'] for k in klines_1d[-30:]]  # Son 30 gün
            daily_lows = [k['low'] for k in klines_1d[-30:]]
            
            # 4H teknik analiz
            prices_4h = [k['close'] for k in klines_4h]
            highs_4h = [k['high'] for k in klines_4h]
            lows_4h = [k['low'] for k in klines_4h]
            
            # 15M teknik analiz  
            prices_15m = [k['close'] for k in klines_15m]
            
            rsi_4h = CryptoTechnicalAnalysis.calculate_rsi(prices_4h)
            rsi_15m = CryptoTechnicalAnalysis.calculate_rsi(prices_15m)
            sr_levels_4h = CryptoTechnicalAnalysis.find_support_resistance(klines_4h)
            atr_4h = CryptoTechnicalAnalysis.calculate_crypto_atr(klines_4h)
            momentum_4h = CryptoTechnicalAnalysis.analyze_crypto_momentum(klines_4h)
            
            print(f"🔍 {symbol} LMO Teknik: 4H RSI={rsi_4h}, 15M RSI={rsi_15m}, 4H ATR={atr_4h:.6f}")
            
            # LMO 4H Analizi - DETAYLI Liquidity sweep
            sweep = CryptoTechnicalAnalysis.detect_liquidity_sweep(klines_4h, current_price)
            
            if not sweep['sweep_detected']:
                print(f"❌ {symbol} LMO: 4H liquidity sweep tespit edilmedi")
                return None
            
            # ATR ve penetration debug
            if 'penetration_amount' in sweep and 'atr_4h' in sweep:
                print(f"🔍 {symbol} LMO Sweep Debug: ATR={sweep['atr_4h']}, Penetration={sweep['penetration_amount']}")
            
            print(f"✅ {symbol} LMO: {sweep['sweep_type']} sweep tespit edildi - Seviye: {sweep['swept_level']}")
            
            # Güvenilirlik skoru
            reliability_score = 0
            signal_type = None
            analysis_details = []
            
            # 4H Sweep gücü
            reliability_score += min(sweep['liquidity_strength'], 3)
            analysis_details.append(f"4H {sweep['sweep_type']} sweep")
            
            # 4H RSI kontrolü
            if 30 <= rsi_4h <= 70:
                reliability_score += 2
                analysis_details.append(f"4H RSI dengeli: {rsi_4h}")
            elif (rsi_4h > 70 and sweep['sweep_type'] == 'HIGH_SWEEP') or (rsi_4h < 30 and sweep['sweep_type'] == 'LOW_SWEEP'):
                reliability_score += 1
                analysis_details.append(f"4H RSI divergence: {rsi_4h}")
            
            # 🎯 GELİŞMİŞ MOMENTUM VE RSI DIVERGENCe ANALİZİ
            enhanced_bonus = 0
            
            if ENHANCED_ANALYSIS_AVAILABLE:
                print(f"🚀 {symbol} Enhanced LMO analizi başlatılıyor...")
                
                # Gelişmiş analiz çalıştır
                enhanced_result = EnhancedLMOAnalyzer.enhanced_lmo_analysis(
                    prices_4h=prices_4h,
                    prices_15m=prices_15m, 
                    rsi_4h_values=[rsi_4h] * len(prices_4h),  # RSI array simulation
                    current_price=current_price,
                    liquidity_sweep=sweep
                )
                
                if enhanced_result['enhanced_signal']:
                    enhanced_bonus = enhanced_result['bonus_score']
                    reliability_score += enhanced_bonus
                    
                    for detail in enhanced_result['analysis_details']:
                        analysis_details.append(f"📊 {detail}")
                    
                    # Enhanced analiz sonucu signal direction belirleme
                    if sweep['sweep_type'] == 'HIGH_SWEEP':
                        signal_type = "SELL"
                    elif sweep['sweep_type'] == 'LOW_SWEEP':
                        signal_type = "BUY"
                        
                    analysis_details.append(f"🎯 Enhanced Analysis Bonus: +{enhanced_bonus} (Quality: {enhanced_result['signal_quality']})")
                    print(f"✅ {symbol} Enhanced LMO: +{enhanced_bonus} bonus, Quality: {enhanced_result['signal_quality']}")
                else:
                    print(f"⚠️ {symbol} Enhanced LMO: {enhanced_result.get('reason', 'Criteria not met')}")
                    analysis_details.append(f"Enhanced analysis: {enhanced_result.get('reason', 'Not significant')}")
            
            # Fallback: Klasik momentum analizi (Enhanced yoksa veya başarısızsa)
            if not signal_type and len(prices_15m) >= 10:
                momentum_15m = (prices_15m[-1] - prices_15m[-10]) / prices_15m[-10]
                print(f"🔍 {symbol} LMO Momentum Debug: 15M momentum={momentum_15m*100:.2f}%, Sweep={sweep['sweep_type']}")
                
                if sweep['sweep_type'] == 'HIGH_SWEEP' and momentum_15m < -0.002:  # Reversal
                    reliability_score += 2  # Enhanced'dan daha düşük bonus
                    signal_type = "SELL"
                    analysis_details.append(f"15M classic momentum: {momentum_15m*100:.2f}%")
                    
                elif sweep['sweep_type'] == 'LOW_SWEEP' and momentum_15m > 0.002:  # Reversal
                    reliability_score += 2  # Enhanced'dan daha düşük bonus
                    signal_type = "BUY"
                    analysis_details.append(f"15M classic momentum: {momentum_15m*100:.2f}%")
            
            # FALLBACK 2: Sweep varsa bile signal direction belirle (esnek)
            if not signal_type:
                if sweep['sweep_type'] == 'HIGH_SWEEP':
                    signal_type = "SELL"  # High sweep -> bearish reversal
                    reliability_score += 1  # Minimum puan
                    analysis_details.append("High sweep -> SELL (default)")
                elif sweep['sweep_type'] == 'LOW_SWEEP':
                    signal_type = "BUY"   # Low sweep -> bullish reversal
                    reliability_score += 1  # Minimum puan
                    analysis_details.append("Low sweep -> BUY (default)")
                    
                print(f"🔍 {symbol} LMO Fallback: {sweep['sweep_type']} -> {signal_type}")
            
            # 15M RSI konfirmasyonu (sadece enhanced yoksa)
            if not enhanced_bonus:
                if signal_type == "SELL" and rsi_15m > 55:
                    reliability_score += 1
                    analysis_details.append(f"15M RSI sell konfirm: {rsi_15m}")
                elif signal_type == "BUY" and rsi_15m < 45:
                    reliability_score += 1
                    analysis_details.append(f"15M RSI buy konfirm: {rsi_15m}")
            
            # 4H Trend yapısı
            if len(prices_4h) >= 20:
                trend_4h = (prices_4h[-1] - prices_4h[-20]) / prices_4h[-20]
                if signal_type == "BUY" and trend_4h < -0.05:  # Güçlü düşüş trendinde buy
                    reliability_score += 2
                    analysis_details.append("4H trend karşıtı giriş")
                elif signal_type == "SELL" and trend_4h > 0.05:  # Güçlü yükseliş trendinde sell
                    reliability_score += 2
                    analysis_details.append("4H trend karşıtı giriş")
            
            print(f"🔍 {symbol} LMO Güvenilirlik: {reliability_score} (min: {self.min_reliability})")
            
            if reliability_score < self.min_reliability:
                print(f"❌ {symbol} LMO: Güvenilirlik düşük ({reliability_score} < {self.min_reliability})")
                return None
            
            # Crypto LMO TP/SL (4H bazlı - geniş)
            swept_level = sweep['swept_level']
            volatility_multiplier = max(atr_4h / current_price, 0.02)  # Min %2
            
            if signal_type == "BUY":
                # Giriş: 15M momentum ile
                ideal_entry = current_price
                
                # Stop Loss: 4H sweep seviyesinin altı
                stop_loss = swept_level * 0.995
                
                # Take Profit: 4H volatiliteye göre
                take_profit = ideal_entry * (1 + volatility_multiplier * 3.0)
                
                # 4H Next resistance check
                for r in sr_levels_4h['resistance_levels']:
                    if r['level'] > current_price:
                        take_profit = min(take_profit, r['level'] * 0.995)
                        break
            
            else:  # SELL
                # Giriş: 15M momentum ile
                ideal_entry = current_price
                
                # Stop Loss: 4H sweep seviyesinin üstü
                stop_loss = swept_level * 1.005
                
                # Take Profit: 4H volatiliteye göre
                take_profit = ideal_entry * (1 - volatility_multiplier * 3.0)
                
                # 4H Next support check
                for s in sr_levels_4h['support_levels']:
                    if s['level'] < current_price:
                        take_profit = max(take_profit, s['level'] * 1.005)
                        break
            
            # Risk/Reward
            risk = abs(ideal_entry - stop_loss)
            reward = abs(take_profit - ideal_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            # KRİTİK: Crypto LMO için minimum 1.5 RR kontrolü (4H için daha yüksek)
            if risk_reward < 1.5:
                print(f"❌ {symbol} Crypto LMO sinyali reddedildi: RR {risk_reward} < 1.5 (Minimum RR standardı)")
                return None
            
            print(f"✅ {symbol} LMO sinyali oluşturuldu: {signal_type} RR:{risk_reward} Güvenilirlik:{reliability_score}")
            
            return {
                'id': f"CRYPTO_LMO_4H_{symbol.replace('/', '')}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'Crypto LMO',
                'signal_type': signal_type,
                'current_price': current_price,
                'ideal_entry': round(ideal_entry, 6),
                'stop_loss': round(stop_loss, 6),
                'take_profit': round(take_profit, 6),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '4H+15M',  # Multi-timeframe LMO
                'status': 'NEW',
                'analysis': f"4H Crypto LMO: {', '.join(analysis_details)}",
                'risk_reward': risk_reward,
                'swept_level': swept_level,
                'sweep_type': sweep['sweep_type'],
                'atr_4h': round(atr_4h, 6),
                'momentum_4h': momentum_4h['momentum'],
                'rsi_4h': round(rsi_4h, 1),
                'rsi_15m': round(rsi_15m, 1),
                'asset_type': 'crypto'
            }
            
        except Exception as e:
            print(f"❌ Crypto LMO analiz hatası {symbol}: {e}")
            return None

class CryptoStrategyManager:
    """
    Gelişmiş Kripto Strateji Yöneticisi
    KRİTİK: Crypto KRO + LMO birlikte konfirmasyon sistemi
    """
    
    def __init__(self, binance_provider):
        self.binance_provider = binance_provider
        self.kro_strategy = CryptoKROStrategy(binance_provider)
        self.lmo_strategy = CryptoLMOStrategy(binance_provider)
        self.min_combined_reliability = 4  # Kripto için daha düşük eşik
    
    def analyze_symbol(self, symbol: str, current_price: float) -> List[Dict]:
        """
        KRİTİK: Crypto KRO + LMO BİRLİKTE KONFIRMASYON ANALİZİ
        Tek sinyal = İki stratejinin birlikte onayı
        """
        signals = []
        
        try:
            print(f"🚀 {symbol} COMBINED analizi başlıyor - Fiyat: {current_price}")
            
            # ADIM 1: Crypto KRO analizi yap
            kro_analysis = self.kro_strategy.analyze(symbol, current_price)
            
            # ADIM 2: Crypto LMO analizi yap  
            lmo_analysis = self.lmo_strategy.analyze(symbol, current_price)
            
            print(f"🔍 {symbol} Sonuçlar: KRO={'✅' if kro_analysis else '❌'}, LMO={'✅' if lmo_analysis else '❌'}")
            
            # ADIM 3: KRO + LMO BİRLİKTE KONFIRMASYON
            combined_signal = self._combine_crypto_strategies(kro_analysis, lmo_analysis, symbol, current_price)
            
            if combined_signal:
                signals.append(combined_signal)
                print(f"✅ {symbol} COMBINED SİNYAL ÜRETİLDİ: {combined_signal['strategy']} - Güvenilirlik: {combined_signal['reliability_score']}")
            else:
                print(f"❌ {symbol} COMBINED: Sinyal üretilemedi")
                
        except Exception as e:
            print(f"❌ Combined crypto strategy analiz hatası {symbol}: {e}")
        
        return signals
    
    def _combine_crypto_strategies(self, kro_result, lmo_result, symbol: str, current_price: float) -> Optional[Dict]:
        """
        KRİTİK: Crypto KRO ve LMO'yu birleştirip tek güçlü sinyal oluştur
        """
        
        # Eğer sadece biri varsa, tek başına yeterli güvenilirlikte mi kontrol et
        if kro_result and not lmo_result:
            if kro_result['reliability_score'] >= 4 and kro_result['risk_reward'] >= 1.2:  # Crypto için daha esnek
                kro_result['strategy'] = 'Crypto KRO (Strong)'
                kro_result['analysis'] = f"Güçlü Crypto KRO: {kro_result['analysis']}"
                return kro_result
            else:
                return None
        
        if lmo_result and not kro_result:
            if lmo_result['reliability_score'] >= 3 and lmo_result['risk_reward'] >= 1.2:  # Crypto için daha esnek
                lmo_result['strategy'] = 'Crypto LMO (Strong)'  
                lmo_result['analysis'] = f"Güçlü Crypto LMO: {lmo_result['analysis']}"
                return lmo_result
            else:
                return None
        
        # Her ikisi de varsa KONFIRMASYON kontrolü
        if kro_result and lmo_result:
            
            # KURAL 1: Aynı yönde mi?
            if kro_result['signal_type'] != lmo_result['signal_type']:
                print(f"❌ {symbol} COMBINED: Çelişkili sinyaller KRO={kro_result['signal_type']}, LMO={lmo_result['signal_type']}")
                return None  # Çelişkili sinyaller
            
            # KURAL 2: Birleşik güvenilirlik hesapla - GELIŞMIŞ BONUS SİSTEMİ
            combined_reliability = (kro_result['reliability_score'] + lmo_result['reliability_score']) / 2
            
            # 🎯 BONUS 1: Temel Konfirmasyon (+1.5 crypto için)
            basic_bonus = 1.5
            combined_reliability += basic_bonus
            
            # 🎯 BONUS 2: Multi-Timeframe Confluence Analizi
            confluence_bonus = self._calculate_confluence_bonus(kro_result, lmo_result, symbol)
            combined_reliability += confluence_bonus
            
            # 🎯 BONUS 3: Risk/Reward Uyum Bonusu  
            rr_harmony_bonus = self._calculate_rr_harmony_bonus(kro_result, lmo_result)
            combined_reliability += rr_harmony_bonus
            
            # 🎯 BONUS 4: Teknik Seviye Kesişim Bonusu
            level_intersection_bonus = self._calculate_level_intersection_bonus(kro_result, lmo_result, current_price)
            combined_reliability += level_intersection_bonus
            
            combined_reliability = min(combined_reliability, 10)  # Max 10
            
            print(f"🔍 {symbol} Bonus Detayı: Basic={basic_bonus}, Confluence={confluence_bonus}, RR={rr_harmony_bonus}, Level={level_intersection_bonus}")
            print(f"🔍 {symbol} Final Güvenilirlik: {combined_reliability:.1f} (KRO={kro_result['reliability_score']} + LMO={lmo_result['reliability_score']})")
            
            if combined_reliability < self.min_combined_reliability:
                return None
            
            # KURAL 3: Birleşik fiyat seviyeleri hesapla
            signal_type = kro_result['signal_type']
            
            # Giriş seviyesi: İki analizin ortalaması
            combined_entry = (kro_result['ideal_entry'] + lmo_result['ideal_entry']) / 2
            
            # Stop Loss ve Take Profit: Daha konservatif olanları seç
            if signal_type == 'BUY':
                combined_sl = max(kro_result['stop_loss'], lmo_result['stop_loss'])  # Daha yüksek SL
                combined_tp = min(kro_result['take_profit'], lmo_result['take_profit'])  # Daha yakın TP
            else:  # SELL
                combined_sl = min(kro_result['stop_loss'], lmo_result['stop_loss'])  # Daha düşük SL
                combined_tp = max(kro_result['take_profit'], lmo_result['take_profit'])  # Daha yakın TP
            
            # Risk/Reward yeniden hesapla
            risk = abs(combined_entry - combined_sl)
            reward = abs(combined_tp - combined_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            # KRİTİK: Combined Crypto stratejide de minimum 1.2 RR kontrolü (daha esnek)
            if risk_reward < 1.2:
                print(f"❌ {symbol} Crypto COMBINED sinyali reddedildi: RR {risk_reward} < 1.2 (Minimum RR standardı)")
                return None
            
            # Birleşik analiz detayları
            kro_clean = kro_result['analysis'].replace('Crypto KRO: ', '')
            lmo_clean = lmo_result['analysis'].replace('Crypto LMO: ', '')
            combined_analysis = f"Crypto KRO+LMO Konfirmasyon: {kro_clean} | {lmo_clean}"
            
            return {
                'id': f"CRYPTO_COMBINED_{symbol.replace('/', '')}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'Crypto KRO+LMO',  # KRİTİK: Birleşik strateji
                'signal_type': signal_type,
                'current_price': current_price,
                'ideal_entry': round(combined_entry, 6),
                'stop_loss': round(combined_sl, 6),
                'take_profit': round(combined_tp, 6),
                'reliability_score': int(round(combined_reliability)),
                'timeframe': '15M+4H',  # Multi-timeframe gösterimi
                'status': 'NEW',
                'analysis': combined_analysis,
                'risk_reward': risk_reward,
                'kro_score': kro_result['reliability_score'],
                'lmo_score': lmo_result['reliability_score'],
                'basic_bonus': basic_bonus,
                'confluence_bonus': confluence_bonus,
                'rr_harmony_bonus': rr_harmony_bonus,
                'level_intersection_bonus': level_intersection_bonus,
                'total_bonus': basic_bonus + confluence_bonus + rr_harmony_bonus + level_intersection_bonus,
                'confirmation_type': 'CRYPTO_DOUBLE_CONFIRMATION',
                'asset_type': 'crypto'
            }
        
        return None
    
    def _calculate_confluence_bonus(self, kro_result: Dict, lmo_result: Dict, symbol: str) -> float:
        """
        🎯 Multi-Timeframe Confluence Bonus
        KRO'nun 15M kırdığı seviye, LMO'nun 4H tespit ettiği likidite seviyesine yakınsa +2 puan
        """
        bonus = 0.0
        
        try:
            # KRO'nun kırdığı seviye
            if 'broken_level' in kro_result:
                kro_level = kro_result['broken_level']
                
                # LMO'nun sweep seviyesi
                if 'swept_level' in lmo_result:
                    lmo_level = lmo_result['swept_level']
                    
                    # Seviyeler arasındaki fark %2'den azsa = Perfect Confluence
                    level_diff_pct = abs(kro_level - lmo_level) / min(kro_level, lmo_level)
                    
                    if level_diff_pct < 0.02:  # %2 içinde
                        bonus = 2.0
                        print(f"🎯 {symbol} PERFECT CONFLUENCE: KRO Level={kro_level:.2f}, LMO Level={lmo_level:.2f} (Fark: {level_diff_pct*100:.1f}%)")
                    elif level_diff_pct < 0.05:  # %5 içinde
                        bonus = 1.0
                        print(f"🎯 {symbol} Good Confluence: KRO Level={kro_level:.2f}, LMO Level={lmo_level:.2f} (Fark: {level_diff_pct*100:.1f}%)")
                    
        except Exception as e:
            print(f"⚠️ {symbol} Confluence bonus hesaplama hatası: {e}")
        
        return bonus
    
    def _calculate_rr_harmony_bonus(self, kro_result: Dict, lmo_result: Dict) -> float:
        """
        🎯 Risk/Reward Uyum Bonusu
        Her iki strateji de yüksek RR'ye sahipse +1 puan
        """
        bonus = 0.0
        
        try:
            kro_rr = kro_result.get('risk_reward', 0)
            lmo_rr = lmo_result.get('risk_reward', 0)
            
            # Her ikisi de 2.0+ RR'ye sahipse mükemmel
            if kro_rr >= 2.0 and lmo_rr >= 2.0:
                bonus = 1.5
            elif kro_rr >= 1.5 and lmo_rr >= 1.5:
                bonus = 1.0
            elif kro_rr >= 1.2 and lmo_rr >= 1.2:
                bonus = 0.5
                
        except Exception as e:
            print(f"⚠️ RR harmony bonus hesaplama hatası: {e}")
        
        return bonus
    
    def _calculate_level_intersection_bonus(self, kro_result: Dict, lmo_result: Dict, current_price: float) -> float:
        """
        🎯 Teknik Seviye Kesişim Bonusu
        Giriş seviyeleri birbirine yakınsa +1 puan
        """
        bonus = 0.0
        
        try:
            kro_entry = kro_result.get('ideal_entry', current_price)
            lmo_entry = lmo_result.get('ideal_entry', current_price)
            
            # Giriş seviyeleri arasındaki fark
            entry_diff_pct = abs(kro_entry - lmo_entry) / min(kro_entry, lmo_entry)
            
            if entry_diff_pct < 0.01:  # %1 içinde = Perfect Entry Confluence
                bonus = 1.0
            elif entry_diff_pct < 0.03:  # %3 içinde = Good Entry Confluence
                bonus = 0.5
                
        except Exception as e:
            print(f"⚠️ Level intersection bonus hesaplama hatası: {e}")
        
        return bonus
    
    def get_best_signal(self, symbol: str, current_price: float) -> Optional[Dict]:
        """En iyi kripto sinyali getir"""
        signals = self.analyze_symbol(symbol, current_price)
        
        if not signals:
            return None
        
        # Güvenilirlik + risk/reward'a göre sırala
        signals.sort(key=lambda x: (x['reliability_score'], x['risk_reward']), reverse=True)
        return signals[0]

def get_crypto_strategy_manager(binance_provider=None):
    """Gelişmiş crypto strategy manager'ı getir"""
    if binance_provider is None:
        from binance_data import get_binance_provider
        binance_provider = get_binance_provider()
    
    return CryptoStrategyManager(binance_provider) 