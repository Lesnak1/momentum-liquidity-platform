#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gelişmiş Momentum ve RSI Divergence Analizi
KRİTİK: İstatistiksel olarak anlamlı sinyal tespiti
"""

import statistics
from typing import List, Dict, Optional
import numpy as np

class AdvancedMomentumAnalyzer:
    """
    Adaptif Momentum Analizi
    Sabit eşikler yerine istatistiksel anlamlılık
    """
    
    @staticmethod
    def calculate_adaptive_momentum_threshold(prices: List[float], lookback: int = 100) -> Dict:
        """
        Son X periyodun momentum değerlerini analiz edip
        dinamik eşik hesapla
        """
        if len(prices) < lookback + 10:
            return {
                'threshold_bullish': 0.001,  # Default %0.1
                'threshold_bearish': -0.001,
                'volatility_factor': 1.0,
                'statistical_significance': False
            }
        
        # Son lookback periyodun momentum değerlerini hesapla
        momentum_values = []
        for i in range(lookback, len(prices)):
            momentum = (prices[i] - prices[i-10]) / prices[i-10]  # 10 periyot momentum
            momentum_values.append(momentum)
        
        if len(momentum_values) < 10:
            return {
                'threshold_bullish': 0.001,
                'threshold_bearish': -0.001,
                'volatility_factor': 1.0,
                'statistical_significance': False
            }
        
        # İstatistiksel analiz
        mean_momentum = statistics.mean(momentum_values)
        std_momentum = statistics.stdev(momentum_values) if len(momentum_values) > 1 else 0.001
        
        # Adaptif eşikler: Ortalama ± 1.5 standart sapma
        threshold_bullish = mean_momentum + (1.5 * std_momentum)
        threshold_bearish = mean_momentum - (1.5 * std_momentum)
        
        # Volatilite faktörü: Standart sapma bazlı
        volatility_factor = max(1.0, std_momentum / 0.001)  # Min 1x, volatil piyasada daha yüksek
        
        return {
            'threshold_bullish': threshold_bullish,
            'threshold_bearish': threshold_bearish,
            'volatility_factor': volatility_factor,
            'statistical_significance': True,
            'mean_momentum': mean_momentum,
            'std_momentum': std_momentum,
            'sample_size': len(momentum_values)
        }
    
    @staticmethod
    def analyze_15m_momentum_significance(prices_15m: List[float], current_momentum: float) -> Dict:
        """
        15M momentum'un istatistiksel anlamlılığını test et
        """
        if len(prices_15m) < 50:
            return {'significant': False, 'confidence': 0}
        
        # Adaptif eşikleri hesapla
        thresholds = AdvancedMomentumAnalyzer.calculate_adaptive_momentum_threshold(prices_15m)
        
        if not thresholds['statistical_significance']:
            return {'significant': False, 'confidence': 0}
        
        # Momentum'un istatistiksel anlamlılığını kontrol et
        is_significantly_bullish = current_momentum > thresholds['threshold_bullish']
        is_significantly_bearish = current_momentum < thresholds['threshold_bearish']
        
        if is_significantly_bullish:
            # Ne kadar güçlü? Z-score hesapla
            z_score = (current_momentum - thresholds['mean_momentum']) / thresholds['std_momentum']
            confidence = min(abs(z_score) / 1.5, 3.0)  # Max 3x confidence
            
            return {
                'significant': True,
                'direction': 'BULLISH',
                'confidence': round(confidence, 2),
                'z_score': round(z_score, 2),
                'threshold_used': thresholds['threshold_bullish']
            }
        
        elif is_significantly_bearish:
            z_score = (current_momentum - thresholds['mean_momentum']) / thresholds['std_momentum']
            confidence = min(abs(z_score) / 1.5, 3.0)  # Max 3x confidence
            
            return {
                'significant': True,
                'direction': 'BEARISH',
                'confidence': round(confidence, 2),
                'z_score': round(z_score, 2),
                'threshold_used': thresholds['threshold_bearish']
            }
        
        else:
            return {
                'significant': False,
                'confidence': 0,
                'reason': 'Momentum istatistiksel olarak anlamsız'
            }

class RSIDivergenceDetector:
    """
    Profesyonel RSI Divergence (Uyumsuzluk) Tespiti
    KRİTİK: Liquidity Sweep sonrası en güçlü konfirmasyon
    """
    
    @staticmethod
    def detect_rsi_divergence(prices: List[float], rsi_values: List[float], lookback: int = 20) -> Dict:
        """
        RSI Divergence tespit et
        """
        if len(prices) < lookback or len(rsi_values) < lookback or len(prices) != len(rsi_values):
            return {'divergence_detected': False}
        
        # Son lookback periyotta swing high/low bul
        swing_highs = RSIDivergenceDetector._find_swing_highs(prices, lookback)
        swing_lows = RSIDivergenceDetector._find_swing_lows(prices, lookback)
        
        # En az 2 swing point gerekli
        if len(swing_highs) < 2 and len(swing_lows) < 2:
            return {'divergence_detected': False}
        
        # Bearish Divergence (Higher High in Price, Lower High in RSI)
        bearish_div = RSIDivergenceDetector._check_bearish_divergence(prices, rsi_values, swing_highs)
        
        # Bullish Divergence (Lower Low in Price, Higher Low in RSI)
        bullish_div = RSIDivergenceDetector._check_bullish_divergence(prices, rsi_values, swing_lows)
        
        if bearish_div['detected']:
            return {
                'divergence_detected': True,
                'type': 'BEARISH',
                'strength': bearish_div['strength'],
                'signal_direction': 'SELL',
                'confidence_bonus': min(bearish_div['strength'] * 2, 4),  # Max +4 puan
                'analysis': f"Bearish Divergence: Price HH @ {bearish_div['price_high']}, RSI LH @ {bearish_div['rsi_high']}"
            }
        
        elif bullish_div['detected']:
            return {
                'divergence_detected': True,
                'type': 'BULLISH',
                'strength': bullish_div['strength'],
                'signal_direction': 'BUY',
                'confidence_bonus': min(bullish_div['strength'] * 2, 4),  # Max +4 puan
                'analysis': f"Bullish Divergence: Price LL @ {bullish_div['price_low']}, RSI HL @ {bullish_div['rsi_low']}"
            }
        
        else:
            return {'divergence_detected': False}
    
    @staticmethod
    def _find_swing_highs(prices: List[float], lookback: int = 20) -> List[Dict]:
        """Swing high'ları bul"""
        swing_highs = []
        
        for i in range(5, len(prices) - 5):  # 5 periyot confirmation
            is_swing_high = True
            current_price = prices[i]
            
            # Önceki ve sonraki 5 periyodu kontrol et
            for j in range(i - 5, i + 6):
                if j != i and prices[j] >= current_price:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    'index': i,
                    'price': current_price
                })
        
        # Son lookback period içindeki swing high'ları filtrele
        recent_highs = [h for h in swing_highs if h['index'] >= len(prices) - lookback]
        
        # En yüksek 3 swing high'ı al
        recent_highs.sort(key=lambda x: x['price'], reverse=True)
        return recent_highs[:3]
    
    @staticmethod
    def _find_swing_lows(prices: List[float], lookback: int = 20) -> List[Dict]:
        """Swing low'ları bul"""
        swing_lows = []
        
        for i in range(5, len(prices) - 5):  # 5 periyot confirmation
            is_swing_low = True
            current_price = prices[i]
            
            # Önceki ve sonraki 5 periyodu kontrol et
            for j in range(i - 5, i + 6):
                if j != i and prices[j] <= current_price:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    'index': i,
                    'price': current_price
                })
        
        # Son lookback period içindeki swing low'ları filtrele
        recent_lows = [l for l in swing_lows if l['index'] >= len(prices) - lookback]
        
        # En düşük 3 swing low'ı al
        recent_lows.sort(key=lambda x: x['price'])
        return recent_lows[:3]
    
    @staticmethod
    def _check_bearish_divergence(prices: List[float], rsi_values: List[float], swing_highs: List[Dict]) -> Dict:
        """Bearish divergence kontrol et"""
        if len(swing_highs) < 2:
            return {'detected': False}
        
        # En son 2 swing high'ı al
        latest_high = swing_highs[0]  # En yüksek fiyat
        previous_high = swing_highs[1]  # İkinci en yüksek
        
        # Fiyatlarda Higher High var mı?
        price_higher_high = latest_high['price'] > previous_high['price']
        
        if not price_higher_high:
            return {'detected': False}
        
        # RSI'da Lower High var mı?
        latest_rsi = rsi_values[latest_high['index']]
        previous_rsi = rsi_values[previous_high['index']]
        rsi_lower_high = latest_rsi < previous_rsi
        
        if rsi_lower_high:
            # Divergence strength hesapla
            price_diff = (latest_high['price'] - previous_high['price']) / previous_high['price']
            rsi_diff = (previous_rsi - latest_rsi) / previous_rsi
            
            strength = min((price_diff + rsi_diff) * 10, 3.0)  # Max 3.0 strength
            
            return {
                'detected': True,
                'strength': round(strength, 2),
                'price_high': latest_high['price'],
                'rsi_high': latest_rsi,
                'divergence_magnitude': round(price_diff + rsi_diff, 4)
            }
        
        return {'detected': False}
    
    @staticmethod
    def _check_bullish_divergence(prices: List[float], rsi_values: List[float], swing_lows: List[Dict]) -> Dict:
        """Bullish divergence kontrol et"""
        if len(swing_lows) < 2:
            return {'detected': False}
        
        # En son 2 swing low'ı al
        latest_low = swing_lows[0]  # En düşük fiyat
        previous_low = swing_lows[1]  # İkinci en düşük
        
        # Fiyatlarda Lower Low var mı?
        price_lower_low = latest_low['price'] < previous_low['price']
        
        if not price_lower_low:
            return {'detected': False}
        
        # RSI'da Higher Low var mı?
        latest_rsi = rsi_values[latest_low['index']]
        previous_rsi = rsi_values[previous_low['index']]
        rsi_higher_low = latest_rsi > previous_rsi
        
        if rsi_higher_low:
            # Divergence strength hesapla
            price_diff = (previous_low['price'] - latest_low['price']) / previous_low['price']
            rsi_diff = (latest_rsi - previous_rsi) / previous_rsi
            
            strength = min((price_diff + rsi_diff) * 10, 3.0)  # Max 3.0 strength
            
            return {
                'detected': True,
                'strength': round(strength, 2),
                'price_low': latest_low['price'],
                'rsi_low': latest_rsi,
                'divergence_magnitude': round(price_diff + rsi_diff, 4)
            }
        
        return {'detected': False}

class EnhancedLMOAnalyzer:
    """
    Gelişmiş LMO Analizi
    Adaptif momentum + RSI divergence ile
    """
    
    @staticmethod
    def enhanced_lmo_analysis(prices_4h: List[float], prices_15m: List[float], 
                            rsi_4h_values: List[float], current_price: float,
                            liquidity_sweep: Dict) -> Dict:
        """
        Gelişmiş LMO analizi yapar
        """
        if not liquidity_sweep.get('sweep_detected'):
            return {'enhanced_signal': False, 'reason': 'No liquidity sweep'}
        
        analysis_details = []
        bonus_score = 0
        
        # 1. Adaptif 15M Momentum Analizi
        if len(prices_15m) >= 50:
            current_momentum = (prices_15m[-1] - prices_15m[-11]) / prices_15m[-11]  # 10 periyot momentum
            momentum_analysis = AdvancedMomentumAnalyzer.analyze_15m_momentum_significance(prices_15m, current_momentum)
            
            if momentum_analysis['significant']:
                bonus_score += int(momentum_analysis['confidence'])
                analysis_details.append(f"Adaptif 15M momentum: {momentum_analysis['direction']} (confidence: {momentum_analysis['confidence']})")
            else:
                analysis_details.append("15M momentum istatistiksel olarak anlamsız")
        
        # 2. RSI Divergence Analizi
        if len(prices_4h) >= 50 and len(rsi_4h_values) >= 50:
            divergence = RSIDivergenceDetector.detect_rsi_divergence(prices_4h, rsi_4h_values)
            
            if divergence['divergence_detected']:
                # Sweep direction ile divergence uyumlu mu?
                sweep_type = liquidity_sweep['sweep_type']
                divergence_signal = divergence['signal_direction']
                
                # HIGH_SWEEP sonrası BEARISH divergence = Mükemmel sinyal
                # LOW_SWEEP sonrası BULLISH divergence = Mükemmel sinyal
                if ((sweep_type == 'HIGH_SWEEP' and divergence_signal == 'SELL') or 
                    (sweep_type == 'LOW_SWEEP' and divergence_signal == 'BUY')):
                    
                    bonus_score += divergence['confidence_bonus']
                    analysis_details.append(f"🎯 PERFECT RSI DIVERGENCE: {divergence['analysis']}")
                else:
                    analysis_details.append(f"RSI Divergence tespit edildi ama sweep ile çelişkili")
            else:
                analysis_details.append("RSI divergence tespit edilmedi")
        
        # 3. Birleşik Değerlendirme
        if bonus_score >= 3:  # Minimum bonus için yüksek eşik
            return {
                'enhanced_signal': True,
                'bonus_score': min(bonus_score, 6),  # Max +6 bonus
                'analysis_details': analysis_details,
                'signal_quality': 'A+' if bonus_score >= 5 else 'A',
                'statistical_significance': True
            }
        else:
            return {
                'enhanced_signal': False,
                'bonus_score': bonus_score,
                'analysis_details': analysis_details,
                'reason': f'Bonus score {bonus_score} < 3 minimum'
            }

def get_enhanced_lmo_analyzer():
    """Enhanced LMO analyzer'ı getir"""
    return EnhancedLMOAnalyzer() 