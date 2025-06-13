"""
Intelligent Fallback System
Güvenilirlik skorunu düşürmeyen akıllı backup mekanizması
"""

import time
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class IntelligentFallbackSystem:
    """Akıllı fallback sistemi - güvenilirlik koruma odaklı"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 dakika cache
        self.confidence_threshold = 0.8  # Minimum güven eşiği
        
    def get_intelligent_fallback_signal(self, strategy_type: str, symbol: str, 
                                      current_price: float, market_context: Dict) -> Optional[Dict]:
        """Akıllı fallback signal üretimi"""
        
        # ❌ Fallback signal üretmeyi tamamen engelle
        # Ana strateji başarısız olursa hiç sinyal üretme
        print(f"⚠️ {symbol} {strategy_type}: Ana analiz başarısız, fallback reddedildi")
        return None
        
        # Kod aşağıda kalıyor ama hiç çalışmayacak - güvenlik için
        cache_key = f"fallback_{strategy_type}_{symbol}"
        
        # Cache kontrolü
        if self._is_cache_valid(cache_key):
            cached_result = self.cache[cache_key]['data']
            print(f"ℹ️ {symbol} fallback cache'den alındı")
            return cached_result
        
        # Market context analizi
        market_confidence = self._calculate_market_confidence(market_context)
        
        if market_confidence < self.confidence_threshold:
            print(f"❌ {symbol} fallback reddedildi: Market confidence {market_confidence:.2f} < {self.confidence_threshold}")
            return None
        
        # Conservative fallback signal
        fallback_signal = self._generate_conservative_signal(
            strategy_type, symbol, current_price, market_context, market_confidence
        )
        
        if fallback_signal:
            # Cache'e kaydet
            self.cache[cache_key] = {
                'data': fallback_signal,
                'timestamp': time.time()
            }
            
            print(f"⚠️ {symbol} conservative fallback signal oluşturuldu (confidence: {market_confidence:.2f})")
        
        return fallback_signal
    
    def _calculate_market_confidence(self, market_context: Dict) -> float:
        """Market güven seviyesi hesaplama"""
        confidence_factors = []
        
        # API data quality
        if market_context.get('data_quality') == 'HIGH':
            confidence_factors.append(0.3)
        elif market_context.get('data_quality') == 'MEDIUM':
            confidence_factors.append(0.1)
        else:
            confidence_factors.append(-0.2)
        
        # Market volatility
        volatility = market_context.get('volatility', 0.02)
        if volatility < 0.015:  # Düşük volatilite = yüksek güven
            confidence_factors.append(0.2)
        elif volatility > 0.05:  # Yüksek volatilite = düşük güven
            confidence_factors.append(-0.3)
        else:
            confidence_factors.append(0.0)
        
        # Volume confirmation
        volume_ratio = market_context.get('volume_ratio', 1.0)
        if volume_ratio > 1.2:
            confidence_factors.append(0.2)
        elif volume_ratio < 0.8:
            confidence_factors.append(-0.1)
        else:
            confidence_factors.append(0.0)
        
        # Trend clarity
        trend_strength = market_context.get('trend_strength', 0.5)
        confidence_factors.append(trend_strength * 0.3)
        
        # Base confidence
        base_confidence = 0.5
        total_confidence = base_confidence + sum(confidence_factors)
        
        return max(0, min(1, total_confidence))
    
    def _generate_conservative_signal(self, strategy_type: str, symbol: str, 
                                    current_price: float, market_context: Dict,
                                    market_confidence: float) -> Optional[Dict]:
        """Conservative fallback signal üretimi"""
        
        # ❌ CONSERVATIVE SIGNAL BİLE ÜRETMİYORUZ
        # Fallback hiçbir durumda sinyal üretmemeli
        return None
        
        # Kod aşağıda kalıyor ama hiç çalışmayacak
        # Conservative risk parameters
        conservative_atr_multiplier = 1.5  # Daha dar stop loss
        conservative_tp_multiplier = 2.0   # Daha yakın take profit
        
        # Reliability penalty for fallback
        base_reliability = 4  # Fallback max 4 puan başlar
        confidence_bonus = int(market_confidence * 2)  # Max +2 puan
        
        reliability_score = base_reliability + confidence_bonus
        
        # Conservative signal structure
        signal = {
            'id': f"FALLBACK_{strategy_type}_{symbol}_{int(time.time())}",
            'symbol': symbol,
            'strategy': f'{strategy_type} (Conservative)',
            'signal_type': self._determine_conservative_direction(market_context),
            'current_price': current_price,
            'reliability_score': reliability_score,
            'timeframe': '15m',
            'status': 'FALLBACK',
            'fallback_reason': 'Main analysis failed',
            'market_confidence': market_confidence,
            'is_fallback': True,
            'conservative_mode': True
        }
        
        # Conservative TP/SL
        atr_estimate = current_price * 0.02  # %2 ATR estimate
        
        if signal['signal_type'] == 'BUY':
            signal['ideal_entry'] = current_price
            signal['stop_loss'] = current_price - (atr_estimate * conservative_atr_multiplier)
            signal['take_profit'] = current_price + (atr_estimate * conservative_tp_multiplier)
        else:
            signal['ideal_entry'] = current_price
            signal['stop_loss'] = current_price + (atr_estimate * conservative_atr_multiplier)
            signal['take_profit'] = current_price - (atr_estimate * conservative_tp_multiplier)
        
        # Risk/Reward check
        risk = abs(signal['ideal_entry'] - signal['stop_loss'])
        reward = abs(signal['take_profit'] - signal['ideal_entry'])
        risk_reward = reward / risk if risk > 0 else 1.0
        
        signal['risk_reward'] = round(risk_reward, 2)
        
        # Conservative RR requirement
        if risk_reward < 1.3:  # Conservative RR threshold
            print(f"❌ {symbol} fallback reddedildi: RR {risk_reward:.2f} < 1.3")
            return None
        
        return signal
    
    def _determine_conservative_direction(self, market_context: Dict) -> str:
        """Conservative signal direction"""
        trend_direction = market_context.get('trend_direction', 'NEUTRAL')
        
        if trend_direction == 'BULLISH':
            return 'BUY'
        elif trend_direction == 'BEARISH':
            return 'SELL'
        else:
            # Neutral market'te trend'i takip et
            momentum = market_context.get('momentum', 0)
            return 'BUY' if momentum > 0 else 'SELL'
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Cache geçerliliği"""
        if cache_key not in self.cache:
            return False
        return (time.time() - self.cache[cache_key]['timestamp']) < self.cache_duration


class NoFallbackPolicy:
    """No-fallback policy - hiç fallback kullanma"""
    
    @staticmethod
    def should_use_fallback(strategy_result: Optional[Dict], market_context: Dict) -> bool:
        """Fallback kullanılıp kullanılmayacağını belirle"""
        
        # ❌ HİÇBİR DURUMDA FALLBACK KULLANMA
        if strategy_result is None:
            print("❌ Ana strateji başarısız - Fallback reddedildi (No-fallback policy)")
            return False
        
        # ❌ ENHANCED ANALYSIS YOKSA DA FALLBACK KULLANMA  
        if strategy_result.get('enhanced_bonus', 0) == 0:
            print("❌ Enhanced analysis başarısız - Fallback reddedildi (Quality requirement)")
            return False
        
        return False  # Her durumda False döndür
    
    @staticmethod
    def enforce_quality_requirements(signal: Dict) -> bool:
        """Kalite gereksinimlerini zorla"""
        
        # ❌ FALLBACK İŞARETLİ SİNYALLERİ REDDET
        if signal.get('is_fallback', False):
            print(f"❌ {signal.get('symbol')} fallback sinyali reddedildi")
            return False
        
        # ❌ DÜŞÜK GÜVENİLİRLİK SKORLARINI REDDET
        reliability = signal.get('reliability_score', 0)
        if reliability < 6:
            print(f"❌ {signal.get('symbol')} düşük güvenilirlik reddedildi: {reliability}")
            return False
        
        # ❌ ENHANCEment OLMAYAN SİNYALLERİ REDDET (opsiyonel)
        if not signal.get('volume_enhanced', False) and not signal.get('enhanced_analysis', False):
            print(f"⚠️ {signal.get('symbol')} enhancement eksik - risk seviyesi yüksek")
            # return False  # İsteğe bağlı - şimdilik geçelim
        
        return True


def get_intelligent_fallback_system():
    """Intelligent fallback system factory"""
    return IntelligentFallbackSystem() 