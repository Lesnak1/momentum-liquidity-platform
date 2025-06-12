"""
Gelişmiş KRO & LMO Strateji Algoritmaları
Gerçek verilerle tutarlı ve yüksek kaliteli trade sinyalleri
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random

class TechnicalIndicators:
    """Teknik analiz indikatörleri"""
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """RSI hesaplama (gerçek)"""
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
    def support_resistance_levels(prices: List[float], period: int = 20) -> Dict[str, List[float]]:
        """Support ve Resistance seviyelerini tespit et (gerçek)"""
        if len(prices) < period * 2:
            return {'support': [], 'resistance': []}
        
        # Pivot noktaları bul
        pivots_high = []
        pivots_low = []
        
        for i in range(period, len(prices) - period):
            current_price = prices[i]
            
            # Local high (resistance) kontrolü
            is_high = True
            for j in range(i - period, i + period + 1):
                if j != i and prices[j] > current_price:
                    is_high = False
                    break
            
            if is_high:
                pivots_high.append(current_price)
            
            # Local low (support) kontrolü
            is_low = True
            for j in range(i - period, i + period + 1):
                if j != i and prices[j] < current_price:
                    is_low = False
                    break
            
            if is_low:
                pivots_low.append(current_price)
        
        # Benzer seviyeleri birleştir
        def cluster_levels(levels):
            if not levels:
                return []
            
            tolerance = 0.0015  # %0.15 tolerance
            clustered = []
            sorted_levels = sorted(levels)
            
            for level in sorted_levels:
                added = False
                for i, cluster in enumerate(clustered):
                    if abs(level - cluster) / cluster < tolerance:
                        clustered[i] = (clustered[i] + level) / 2
                        added = True
                        break
                
                if not added:
                    clustered.append(level)
            
            return clustered[-5:]  # Son 5 seviye
        
        return {
            'support': cluster_levels(pivots_low),
            'resistance': cluster_levels(pivots_high)
        }
    
    @staticmethod
    def calculate_atr(candles: List[Dict], period: int = 14) -> float:
        """ATR hesaplama (gerçek volatilite)"""
        if len(candles) < period:
            return 0.01
        
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
            return round(atr, 6)
        
        return 0.01

class RealForexKROStrategy:
    """Gerçek verilerle KRO Stratejisi"""
    
    def __init__(self, forex_provider):
        self.name = "Real-KRO"
        self.description = "Gerçek Forex Verilerle KRO Stratejisi"
        self.min_reliability = 7
        self.forex_provider = forex_provider
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """Gerçek verilerle KRO stratejisi analizi"""
        try:
            # Geçmiş verileri al
            candles = self.forex_provider.get_historical_data(symbol, '15m', 100)
            
            if len(candles) < 50:
                return None
            
            # Fiyat dizisini oluştur
            prices = [float(candle['close']) for candle in candles]
            highs = [float(candle['high']) for candle in candles]
            lows = [float(candle['low']) for candle in candles]
            
            # Teknik analiz
            rsi = TechnicalIndicators.rsi(prices)
            sr_levels = TechnicalIndicators.support_resistance_levels(prices)
            atr = TechnicalIndicators.calculate_atr(candles)
            
            # KRO Kırılım Analizi
            reliability_score = 0
            signal_type = None
            analysis_details = []
            
            # 1. RSI Kontrolü
            if 30 <= rsi <= 70:  # Aşırı alım/satım yok
                reliability_score += 2
                analysis_details.append(f"RSI dengeli: {rsi}")
            
            # 2. Support/Resistance Kırılım
            supports = sr_levels.get('support', [])
            resistances = sr_levels.get('resistance', [])
            
            # Yakın support/resistance seviyeleri
            near_resistance = [r for r in resistances if abs(current_price - r) / current_price < 0.003]
            near_support = [s for s in supports if abs(current_price - s) / current_price < 0.003]
            
            if near_resistance:
                closest_resistance = min(near_resistance, key=lambda x: abs(x - current_price))
                if current_price > closest_resistance:  # Resistance kırıldı
                    reliability_score += 3
                    signal_type = "BUY"
                    analysis_details.append(f"Resistance kırılımı: {closest_resistance}")
            
            if near_support:
                closest_support = max(near_support, key=lambda x: abs(x - current_price))
                if current_price < closest_support:  # Support kırıldı
                    reliability_score += 3
                    signal_type = "SELL"
                    analysis_details.append(f"Support kırılımı: {closest_support}")
            
            # 3. Momentum Kontrolü
            if len(prices) >= 10:
                recent_momentum = (prices[-1] - prices[-10]) / prices[-10]
                if abs(recent_momentum) > 0.002:  # %0.2'den fazla momentum
                    reliability_score += 2
                    if recent_momentum > 0 and signal_type != "SELL":
                        signal_type = "BUY"
                    elif recent_momentum < 0 and signal_type != "BUY":
                        signal_type = "SELL"
                    analysis_details.append(f"Momentum: {recent_momentum*100:.2f}%")
            
            # 4. Volume Spike (simulated but realistic)
            recent_volumes = [candle['volume'] for candle in candles[-20:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            current_volume = candles[-1]['volume']
            
            if current_volume > avg_volume * 1.3:  # %30 fazla volume
                reliability_score += 1
                analysis_details.append(f"Volume spike: {current_volume/avg_volume:.1f}x")
            
            # Signal yoksa veya güvenilirlik düşükse
            if not signal_type or reliability_score < self.min_reliability:
                return None
            
            # TP/SL Hesaplama (ATR bazlı)
            atr_multiplier = 1.5
            
            if signal_type == "BUY":
                stop_loss = current_price - (atr * atr_multiplier)
                take_profit = current_price + (atr * atr_multiplier * 1.5)  # 1.5:1 RR
            else:
                stop_loss = current_price + (atr * atr_multiplier)
                take_profit = current_price - (atr * atr_multiplier * 1.5)
            
            # Risk/Reward hesapla
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            return {
                'id': f"REAL_KRO_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'Real-KRO',
                'signal_type': signal_type,
                'entry_price': current_price,
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '15m',
                'status': 'NEW',
                'analysis': f"KRO Analiz: {', '.join(analysis_details)}",
                'risk_reward': risk_reward,
                'atr': round(atr, 6)
            }
            
        except Exception as e:
            print(f"❌ KRO analiz hatası {symbol}: {e}")
            return None

class RealForexLMOStrategy:
    """Gerçek verilerle LMO Stratejisi"""
    
    def __init__(self, forex_provider):
        self.name = "Real-LMO"
        self.description = "Gerçek Forex Verilerle LMO Stratejisi"
        self.min_reliability = 6
        self.forex_provider = forex_provider
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """Gerçek verilerle LMO stratejisi analizi"""
        try:
            # Geçmiş verileri al
            candles = self.forex_provider.get_historical_data(symbol, '15m', 100)
            
            if len(candles) < 50:
                return None
            
            prices = [float(candle['close']) for candle in candles]
            highs = [float(candle['high']) for candle in candles]
            lows = [float(candle['low']) for candle in candles]
            
            # Teknik analiz
            rsi = TechnicalIndicators.rsi(prices)
            sr_levels = TechnicalIndicators.support_resistance_levels(prices)
            atr = TechnicalIndicators.calculate_atr(candles)
            
            # LMO Liquidity Sweep Analizi
            reliability_score = 0
            signal_type = None
            analysis_details = []
            
            # 1. Liquidity Sweep Tespiti
            recent_highs = highs[-20:]
            recent_lows = lows[-20:]
            max_high = max(recent_highs)
            min_low = min(recent_lows)
            
            # Sweep kontrolü
            if len(prices) >= 10:
                if current_price > max_high * 0.999:  # Yüksek seviye sweep
                    if rsi > 60:  # Aşırı alım bölgesi
                        reliability_score += 3
                        signal_type = "SELL"
                        analysis_details.append(f"High sweep + RSI: {rsi}")
                
                if current_price < min_low * 1.001:  # Düşük seviye sweep
                    if rsi < 40:  # Aşırı satım bölgesi
                        reliability_score += 3
                        signal_type = "BUY"
                        analysis_details.append(f"Low sweep + RSI: {rsi}")
            
            # 2. Candle Pattern Confirmation
            if len(candles) >= 3:
                last_3_candles = candles[-3:]
                
                # Reversal pattern check
                for i, candle in enumerate(last_3_candles):
                    body_size = abs(candle['close'] - candle['open'])
                    full_range = candle['high'] - candle['low']
                    
                    if body_size > full_range * 0.6:  # Strong body
                        reliability_score += 1
                        analysis_details.append(f"Güçlü mum {i+1}")
            
            # 3. Volume Confirmation
            volumes = [candle['volume'] for candle in candles[-20:]]
            avg_volume = sum(volumes) / len(volumes)
            recent_volume = candles[-1]['volume']
            
            if recent_volume > avg_volume * 1.2:
                reliability_score += 1
                analysis_details.append(f"Volume onay: {recent_volume/avg_volume:.1f}x")
            
            # 4. Market Structure
            if len(prices) >= 20:
                recent_trend = (prices[-1] - prices[-20]) / prices[-20]
                if signal_type == "BUY" and recent_trend < -0.005:  # Düşüş trendinde buy
                    reliability_score += 2
                    analysis_details.append("Trend karşıtı girişim")
                elif signal_type == "SELL" and recent_trend > 0.005:  # Yükseliş trendinde sell
                    reliability_score += 2
                    analysis_details.append("Trend karşıtı girişim")
            
            if not signal_type or reliability_score < self.min_reliability:
                return None
            
            # TP/SL Hesaplama (ATR bazlı)
            atr_multiplier = 1.2
            
            if signal_type == "BUY":
                stop_loss = current_price - (atr * atr_multiplier)
                take_profit = current_price + (atr * atr_multiplier * 1.3)
            else:
                stop_loss = current_price + (atr * atr_multiplier)
                take_profit = current_price - (atr * atr_multiplier * 1.3)
            
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            return {
                'id': f"REAL_LMO_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'Real-LMO',
                'signal_type': signal_type,
                'entry_price': current_price,
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '15m',
                'status': 'NEW',
                'analysis': f"LMO Analiz: {', '.join(analysis_details)}",
                'risk_reward': risk_reward,
                'atr': round(atr, 6)
            }
            
        except Exception as e:
            print(f"❌ LMO analiz hatası {symbol}: {e}")
            return None

# ESKI Simulated classes - compatibility için
class KROStrategy:
    """Eski KRO - compatibility için"""
    def __init__(self):
        self.name = "KRO"
        self.description = "Legacy KRO"
        self.min_reliability = 7
    
    def analyze(self, market_data: Dict) -> Optional[Dict]:
        return None  # Artık kullanılmıyor

class LMOStrategy:
    """Eski LMO - compatibility için"""
    def __init__(self):
        self.name = "LMO"
        self.description = "Legacy LMO"
        self.min_reliability = 6
    
    def analyze(self, market_data: Dict) -> Optional[Dict]:
        return None  # Artık kullanılmıyor

class StrategyManager:
    """Gerçek Forex Stratejilerini Yönet"""
    
    def __init__(self, forex_provider):
        self.strategies = []
        self.forex_provider = forex_provider
        
        # Gerçek stratejileri ekle
        self.real_kro = RealForexKROStrategy(forex_provider)
        self.real_lmo = RealForexLMOStrategy(forex_provider)
    
    def analyze_symbol(self, symbol: str, current_price: float) -> List[Dict]:
        """Bir sembol için tüm stratejileri analiz et"""
        signals = []
        
        try:
            # KRO analizi
            kro_signal = self.real_kro.analyze(symbol, current_price)
            if kro_signal:
                signals.append(kro_signal)
            
            # LMO analizi
            lmo_signal = self.real_lmo.analyze(symbol, current_price)
            if lmo_signal:
                signals.append(lmo_signal)
                
        except Exception as e:
            print(f"❌ Strateji analiz hatası {symbol}: {e}")
        
        return signals
    
    def get_best_signal(self, symbol: str, current_price: float) -> Optional[Dict]:
        """En iyi sinyali getir"""
        signals = self.analyze_symbol(symbol, current_price)
        
        if not signals:
            return None
        
        # En yüksek güvenilirlik skoruna göre sırala
        signals.sort(key=lambda x: x['reliability_score'], reverse=True)
        return signals[0]

def get_strategy_manager(forex_provider=None):
    """Strategy manager'ı getir"""
    if forex_provider is None:
        from forex_data import get_forex_provider
        forex_provider = get_forex_provider()
    
    return StrategyManager(forex_provider) 