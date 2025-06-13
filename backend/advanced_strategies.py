"""
Gelişmiş KRO & LMO Strateji Algoritmaları
Gerçek verilerle tutarlı ve yüksek kaliteli trade sinyalleri
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
try:
    from advanced_momentum_analysis import EnhancedLMOAnalyzer, AdvancedMomentumAnalyzer, RSIDivergenceDetector
    ENHANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ENHANCED_ANALYSIS_AVAILABLE = False
    print("⚠️ Enhanced analysis modülü bulunamadı, standart forex analiz kullanılacak")

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
            
            # TP/SL Hesaplama (ATR bazlı) - Forex için optimize
            atr_multiplier = 3.0  # Daha geniş forex risk yönetimi
            
            if signal_type == "BUY":
                stop_loss = current_price - (atr * atr_multiplier)
                take_profit = current_price + (atr * atr_multiplier * 2.5)  # 2.5:1 RR hedefi
            else:
                stop_loss = current_price + (atr * atr_multiplier)
                take_profit = current_price - (atr * atr_multiplier * 2.5)  # 2.5:1 RR hedefi
            
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
    """Gerçek verilerle LMO Stratejisi - 4H TIMEFRAME"""
    
    def __init__(self, forex_provider):
        self.name = "Real-LMO"
        self.description = "Gerçek Forex Verilerle LMO Stratejisi (4H)"
        self.min_reliability = 6
        self.forex_provider = forex_provider
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """4H timeframe ile gerçek LMO stratejisi analizi"""
        try:
            # 4H verileri al - LMO için ideal timeframe
            candles_4h = self.forex_provider.get_historical_data(symbol, '4h', 100)
            
            # 15m verileri al - entry timing için
            candles_15m = self.forex_provider.get_historical_data(symbol, '15m', 50)
            
            if len(candles_4h) < 50 or len(candles_15m) < 20:
                return None
            
            # 4H analiz - Ana trend ve liquidity seviyeleri
            prices_4h = [float(candle['close']) for candle in candles_4h]
            highs_4h = [float(candle['high']) for candle in candles_4h]
            lows_4h = [float(candle['low']) for candle in candles_4h]
            
            # 15M analiz - Entry timing
            prices_15m = [float(candle['close']) for candle in candles_15m]
            
            # 4H Teknik analiz
            rsi_4h = TechnicalIndicators.rsi(prices_4h)
            sr_levels_4h = TechnicalIndicators.support_resistance_levels(prices_4h)
            atr_4h = TechnicalIndicators.calculate_atr(candles_4h)
            
            # 15M Teknik analiz - Momentum konfirmasyonu
            rsi_15m = TechnicalIndicators.rsi(prices_15m)
            
            # LMO 4H Liquidity Sweep Analizi
            reliability_score = 0
            signal_type = None
            analysis_details = []
            
            # 1. 4H Liquidity Sweep Tespiti
            recent_highs_4h = highs_4h[-20:]  # Son 20 x 4h = 80 saat geçmiş
            recent_lows_4h = lows_4h[-20:]
            max_high_4h = max(recent_highs_4h)
            min_low_4h = min(recent_lows_4h)
            
            # Liquidity sweep kontrolü (4H zaman diliminde)
            liquidity_swept = False
            sweep_direction = None
            
            if current_price > max_high_4h * 1.001:  # Yüksek seviyeler temizlendi
                liquidity_swept = True
                sweep_direction = "HIGH_SWEEP"
                reliability_score += 3
                analysis_details.append(f"4H High sweep: {max_high_4h}")
                
            elif current_price < min_low_4h * 0.999:  # Düşük seviyeler temizlendi
                liquidity_swept = True
                sweep_direction = "LOW_SWEEP"
                reliability_score += 3
                analysis_details.append(f"4H Low sweep: {min_low_4h}")
            
            if not liquidity_swept:
                return None
            
            # 2. 4H RSI Kontrolü
            if 30 <= rsi_4h <= 70:  # Aşırı durumlar dışında
                reliability_score += 2
                analysis_details.append(f"4H RSI dengeli: {rsi_4h}")
            elif (rsi_4h > 70 and sweep_direction == "HIGH_SWEEP") or (rsi_4h < 30 and sweep_direction == "LOW_SWEEP"):
                reliability_score += 1  # Divergence durumu
                analysis_details.append(f"4H RSI divergence: {rsi_4h}")
            
            # 3. 15M Momentum Konfirmasyonu
            if len(prices_15m) >= 10:
                momentum_15m = (prices_15m[-1] - prices_15m[-10]) / prices_15m[-10]
                
                if sweep_direction == "HIGH_SWEEP" and momentum_15m < -0.001:  # Reversal momentum
                    reliability_score += 2
                    signal_type = "SELL"
                    analysis_details.append(f"15M reversal momentum: {momentum_15m*100:.2f}%")
                    
                elif sweep_direction == "LOW_SWEEP" and momentum_15m > 0.001:  # Reversal momentum
                    reliability_score += 2
                    signal_type = "BUY"
                    analysis_details.append(f"15M reversal momentum: {momentum_15m*100:.2f}%")
            
            # 4. 15M RSI Konfirmasyonu
            if signal_type == "SELL" and rsi_15m > 60:  # Satış için yüksek RSI
                reliability_score += 1
                analysis_details.append(f"15M RSI sell konfirm: {rsi_15m}")
            elif signal_type == "BUY" and rsi_15m < 40:  # Alış için düşük RSI
                reliability_score += 1
                analysis_details.append(f"15M RSI buy konfirm: {rsi_15m}")
            
            # 5. 4H Trend Yapısı
            if len(prices_4h) >= 20:
                trend_4h = (prices_4h[-1] - prices_4h[-20]) / prices_4h[-20]
                if signal_type == "BUY" and trend_4h < -0.01:  # Düşüş trendinde buy
                    reliability_score += 2
                    analysis_details.append("4H trend karşıtı giriş")
                elif signal_type == "SELL" and trend_4h > 0.01:  # Yükseliş trendinde sell
                    reliability_score += 2
                    analysis_details.append("4H trend karşıtı giriş")
            
            if not signal_type or reliability_score < self.min_reliability:
                return None
            
            # TP/SL Hesaplama (4H ATR bazlı) - Forex için optimize
            atr_multiplier = 2.8  # 4H LMO için daha geniş SL
            
            if signal_type == "BUY":
                # Giriş: 15M onay ile
                ideal_entry = current_price
                
                # Stop Loss: 4H ATR ile daha geniş seviye
                stop_loss = current_price - (atr_4h * atr_multiplier)
                
                # Take Profit: 4H ATR ile 3.0:1 RR (forex için)
                take_profit = current_price + (atr_4h * atr_multiplier * 3.0)
                
                # 4H resistance kontrolü
                for level in sr_levels_4h.get('resistance', []):
                    if level > current_price:
                        take_profit = min(take_profit, level * 0.998)
                        break
                        
            else:  # SELL
                # Giriş: 15M onay ile
                ideal_entry = current_price
                
                # Stop Loss: 4H ATR ile daha geniş seviye
                stop_loss = current_price + (atr_4h * atr_multiplier)
                
                # Take Profit: 4H ATR ile 3.0:1 RR (forex için)
                take_profit = current_price - (atr_4h * atr_multiplier * 3.0)
                
                # 4H support kontrolü
                for level in sr_levels_4h.get('support', []):
                    if level < current_price:
                        take_profit = max(take_profit, level * 1.002)
                        break
            
            risk = abs(ideal_entry - stop_loss)
            reward = abs(take_profit - ideal_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            return {
                'id': f"REAL_LMO_4H_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'Real-LMO',
                'signal_type': signal_type,
                'entry_price': current_price,
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '4H+15M',  # Multi-timeframe
                'status': 'NEW',
                'analysis': f"4H LMO Analiz: {', '.join(analysis_details)}",
                'risk_reward': risk_reward,
                'atr_4h': round(atr_4h, 6),
                'sweep_direction': sweep_direction,
                'rsi_4h': round(rsi_4h, 1),
                'rsi_15m': round(rsi_15m, 1)
            }
            
        except Exception as e:
            print(f"❌ 4H LMO analiz hatası {symbol}: {e}")
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