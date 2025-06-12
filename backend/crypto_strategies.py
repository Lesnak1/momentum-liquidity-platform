"""
Kripto KRO & LMO Stratejileri
Forex ile aynı seviyede detaylı teknik analiz
Gerçek Binance verilerinden TP/SL/ideal giriş hesaplamaları
"""

import time
import random
from datetime import datetime
from typing import Dict, List, Optional

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
                resistance_levels.append({
                    'level': current_high,
                    'timestamp': recent_candles[i]['timestamp'],
                    'touches': 1,
                    'volume': recent_candles[i]['volume']
                })
            
            # Support (3 periyotluk swing low)
            is_swing_low = True
            for j in range(i-3, i+4):
                if j != i and recent_candles[j]['low'] < current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                support_levels.append({
                    'level': current_low,
                    'timestamp': recent_candles[i]['timestamp'],
                    'touches': 1,
                    'volume': recent_candles[i]['volume']
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
                        # Volume ağırlıklı ortalama
                        total_volume = existing['volume'] + level['volume']
                        existing['level'] = ((existing['level'] * existing['volume']) + 
                                           (price * level['volume'])) / total_volume
                        existing['touches'] += 1
                        existing['volume'] = total_volume
                        merged = True
                        break
                
                if not merged:
                    consolidated.append(level)
            
            # Touch sayısı ve volume'e göre sırala
            return sorted(consolidated, key=lambda x: (x['touches'], x['volume']), reverse=True)[:6]
        
        return {
            'support_levels': consolidate_levels(support_levels),
            'resistance_levels': consolidate_levels(resistance_levels)
        }
    
    @staticmethod
    def detect_crypto_breakout(current_price: float, sr_levels: Dict, tolerance: float = 0.008) -> Dict:
        """Kripto kırılım tespiti (daha büyük tolerans)"""
        result = {
            'breakout_type': None,
            'broken_level': None,
            'breakout_strength': 0,
            'volume_confirm': False
        }
        
        # Resistance kırılımı
        for resistance in sr_levels['resistance_levels']:
            level = resistance['level']
            if current_price > level * (1 + tolerance):
                result['breakout_type'] = 'RESISTANCE_BREAK'
                result['broken_level'] = level
                result['breakout_strength'] = resistance['touches']
                result['volume_confirm'] = resistance['volume'] > 10000  # Volume check
                break
        
        # Support kırılımı
        if not result['breakout_type']:
            for support in sr_levels['support_levels']:
                level = support['level']
                if current_price < level * (1 - tolerance):
                    result['breakout_type'] = 'SUPPORT_BREAK'
                    result['broken_level'] = level
                    result['breakout_strength'] = support['touches']
                    result['volume_confirm'] = support['volume'] > 10000
                    break
        
        return result
    
    @staticmethod
    def detect_liquidity_sweep(candles: List[Dict], current_price: float) -> Dict:
        """Kripto liquidity sweep - daha agresif"""
        if len(candles) < 24:  # 24 saatlik data
            return {'sweep_detected': False}
        
        recent_candles = candles[-24:]
        
        # Son 24 saatin highs/lows
        recent_highs = [c['high'] for c in recent_candles]
        recent_lows = [c['low'] for c in recent_candles]
        recent_volumes = [c['volume'] for c in recent_candles]
        
        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        # Equal highs/lows (kripto için geniş tolerans)
        tolerance = 0.01  # %1
        equal_highs = [h for h in recent_highs if abs(h - highest_high) / highest_high < tolerance]
        equal_lows = [l for l in recent_lows if abs(l - lowest_low) / lowest_low < tolerance]
        
        current_volume = candles[-1]['volume']
        volume_spike = current_volume > avg_volume * 1.3
        
        # High sweep
        if len(equal_highs) >= 2 and current_price > highest_high * (1 + tolerance/2):
            return {
                'sweep_detected': True,
                'sweep_type': 'HIGH_SWEEP',
                'swept_level': highest_high,
                'liquidity_strength': len(equal_highs),
                'volume_confirmation': volume_spike
            }
        
        # Low sweep
        if len(equal_lows) >= 2 and current_price < lowest_low * (1 - tolerance/2):
            return {
                'sweep_detected': True,
                'sweep_type': 'LOW_SWEEP',
                'swept_level': lowest_low,
                'liquidity_strength': len(equal_lows),
                'volume_confirmation': volume_spike
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
    Kripto KRO Stratejisi: Kırılım + Retest + Onay
    Forex ile aynı detay seviyesinde
    """
    
    def __init__(self, binance_provider):
        self.name = "Crypto KRO"
        self.description = "Kripto Kırılım + Retest + Onay (Gerçek Binance Verileri)"
        self.binance_provider = binance_provider
        self.min_reliability = 6
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """Gerçek kripto KRO analizi"""
        try:
            # Binance'den geçmiş verileri al
            klines = self.binance_provider.get_klines(symbol, '1h', 100)
            
            if len(klines) < 50:
                return None
            
            # Teknik analiz
            prices = [k['close'] for k in klines]
            rsi = CryptoTechnicalAnalysis.calculate_rsi(prices)
            sr_levels = CryptoTechnicalAnalysis.find_support_resistance(klines)
            atr = CryptoTechnicalAnalysis.calculate_crypto_atr(klines)
            momentum = CryptoTechnicalAnalysis.analyze_crypto_momentum(klines)
            
            # KRO Analizi
            breakout = CryptoTechnicalAnalysis.detect_crypto_breakout(current_price, sr_levels)
            
            if not breakout['breakout_type']:
                return None
            
            # Güvenilirlik skoru
            reliability_score = 0
            analysis_details = []
            
            # Kırılım gücü
            reliability_score += min(breakout['breakout_strength'], 4)
            analysis_details.append(f"Kırılım gücü: {breakout['breakout_strength']} touch")
            
            # Volume onayı
            if breakout['volume_confirm']:
                reliability_score += 2
                analysis_details.append("Volume onay")
            
            # RSI kontrol
            if 25 <= rsi <= 75:  # Kripto için geniş RSI bandı
                reliability_score += 2
                analysis_details.append(f"RSI: {rsi}")
            
            # Momentum onayı
            if momentum['trend'] != 'SIDEWAYS':
                reliability_score += 1
                analysis_details.append(f"Momentum: {momentum['trend']}")
            
            if reliability_score < self.min_reliability:
                return None
            
            # Sinyal yönü
            signal_type = None
            if breakout['breakout_type'] == 'RESISTANCE_BREAK':
                if momentum['trend'] != 'BEARISH':
                    signal_type = "BUY"
            elif breakout['breakout_type'] == 'SUPPORT_BREAK':
                if momentum['trend'] != 'BULLISH':
                    signal_type = "SELL"
            
            if not signal_type:
                return None
            
            # Kripto TP/SL hesaplama (ATR + volatilite bazlı)
            broken_level = breakout['broken_level']
            volatility_multiplier = max(atr / current_price, 0.02)  # Min %2
            
            if signal_type == "BUY":
                # İdeal giriş: Kırılan seviyenin üzerinde
                ideal_entry = max(current_price, broken_level * 1.005)
                
                # Stop Loss: Kırılan seviyenin altında
                stop_loss = broken_level * 0.992
                
                # Take Profit: ATR + volatilite bazlı
                take_profit = ideal_entry * (1 + volatility_multiplier * 3)
                
                # Next resistance varsa hedef ayarla
                for r in sr_levels['resistance_levels']:
                    if r['level'] > current_price:
                        take_profit = min(take_profit, r['level'] * 0.99)
                        break
            
            else:  # SELL
                ideal_entry = min(current_price, broken_level * 0.995)
                stop_loss = broken_level * 1.008
                take_profit = ideal_entry * (1 - volatility_multiplier * 3)
                
                # Next support varsa hedef ayarla
                for s in sr_levels['support_levels']:
                    if s['level'] < current_price:
                        take_profit = max(take_profit, s['level'] * 1.01)
                        break
            
            # Risk/Reward
            risk = abs(ideal_entry - stop_loss)
            reward = abs(take_profit - ideal_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            return {
                'id': f"CRYPTO_KRO_{symbol.replace('/', '')}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'Crypto KRO',
                'signal_type': signal_type,
                'current_price': current_price,
                'ideal_entry': round(ideal_entry, 6),
                'stop_loss': round(stop_loss, 6),
                'take_profit': round(take_profit, 6),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '1h',
                'status': 'NEW',
                'analysis': f"Crypto KRO: {', '.join(analysis_details)}",
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
    Kripto LMO Stratejisi: Liquidity Sweep + Momentum Onayı
    Forex ile aynı detay seviyesinde
    """
    
    def __init__(self, binance_provider):
        self.name = "Crypto LMO"
        self.description = "Kripto Liquidity Sweep + Momentum Onayı (Gerçek Binance Verileri)"
        self.binance_provider = binance_provider
        self.min_reliability = 5
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """Gerçek kripto LMO analizi"""
        try:
            # Binance'den veri al
            klines = self.binance_provider.get_klines(symbol, '1h', 100)
            
            if len(klines) < 50:
                return None
            
            # Teknik analiz
            prices = [k['close'] for k in klines]
            rsi = CryptoTechnicalAnalysis.calculate_rsi(prices)
            sr_levels = CryptoTechnicalAnalysis.find_support_resistance(klines)
            atr = CryptoTechnicalAnalysis.calculate_crypto_atr(klines)
            momentum = CryptoTechnicalAnalysis.analyze_crypto_momentum(klines)
            
            # LMO Analizi
            sweep = CryptoTechnicalAnalysis.detect_liquidity_sweep(klines, current_price)
            
            if not sweep['sweep_detected']:
                return None
            
            # Güvenilirlik skoru
            reliability_score = 0
            analysis_details = []
            
            # Sweep gücü
            reliability_score += min(sweep['liquidity_strength'], 3)
            analysis_details.append(f"Liquidity sweep: {sweep['sweep_type']}")
            
            # Volume onayı
            if sweep.get('volume_confirmation'):
                reliability_score += 3
                analysis_details.append("Volume spike onay")
            
            # RSI ekstrem seviyeleri (reversal için)
            if rsi > 70 or rsi < 30:
                reliability_score += 2
                analysis_details.append(f"RSI ekstrem: {rsi}")
            
            # Momentum karşıtı (reversal beklentisi)
            if momentum['trend'] != 'SIDEWAYS':
                reliability_score += 1
                analysis_details.append(f"Reversal setup: {momentum['trend']}")
            
            if reliability_score < self.min_reliability:
                return None
            
            # Sinyal yönü (reversal expectation)
            signal_type = None
            swept_level = sweep['swept_level']
            
            if sweep['sweep_type'] == 'HIGH_SWEEP':
                # Yüksek seviyeler süpürüldü, SELL beklentisi
                if rsi > 50:  # Överbought bölgede
                    signal_type = "SELL"
            
            elif sweep['sweep_type'] == 'LOW_SWEEP':
                # Düşük seviyeler süpürüldü, BUY beklentisi
                if rsi < 50:  # Oversold bölgede
                    signal_type = "BUY"
            
            if not signal_type:
                return None
            
            # Kripto LMO TP/SL (tighter, reversal stratejisi)
            volatility_multiplier = max(atr / current_price, 0.015)  # Min %1.5
            
            if signal_type == "BUY":
                ideal_entry = max(current_price, swept_level * 1.003)
                stop_loss = swept_level * 0.995
                take_profit = ideal_entry * (1 + volatility_multiplier * 2.5)
                
                # Next resistance check
                for r in sr_levels['resistance_levels']:
                    if r['level'] > current_price:
                        take_profit = min(take_profit, r['level'] * 0.995)
                        break
            
            else:  # SELL
                ideal_entry = min(current_price, swept_level * 0.997)
                stop_loss = swept_level * 1.005
                take_profit = ideal_entry * (1 - volatility_multiplier * 2.5)
                
                # Next support check
                for s in sr_levels['support_levels']:
                    if s['level'] < current_price:
                        take_profit = max(take_profit, s['level'] * 1.005)
                        break
            
            # Risk/Reward
            risk = abs(ideal_entry - stop_loss)
            reward = abs(take_profit - ideal_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            # KRİTİK: Crypto LMO için minimum 1.5 RR kontrolü!
            if risk_reward < 1.5:
                print(f"❌ {symbol} Crypto LMO sinyali reddedildi: RR {risk_reward} < 1.5 (Minimum RR standardı)")
                return None
            
            return {
                'id': f"CRYPTO_LMO_{symbol.replace('/', '')}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'Crypto LMO',
                'signal_type': signal_type,
                'current_price': current_price,
                'ideal_entry': round(ideal_entry, 6),
                'stop_loss': round(stop_loss, 6),
                'take_profit': round(take_profit, 6),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '1h',
                'status': 'NEW',
                'analysis': f"Crypto LMO: {', '.join(analysis_details)}",
                'risk_reward': risk_reward,
                'swept_level': swept_level,
                'sweep_type': sweep['sweep_type'],
                'atr': round(atr, 6),
                'momentum': momentum['momentum'],
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
        self.min_combined_reliability = 6  # Kripto için biraz daha düşük eşik
    
    def analyze_symbol(self, symbol: str, current_price: float) -> List[Dict]:
        """
        KRİTİK: Crypto KRO + LMO BİRLİKTE KONFIRMASYON ANALİZİ
        Tek sinyal = İki stratejinin birlikte onayı
        """
        signals = []
        
        try:
            # ADIM 1: Crypto KRO analizi yap
            kro_analysis = self.kro_strategy.analyze(symbol, current_price)
            
            # ADIM 2: Crypto LMO analizi yap  
            lmo_analysis = self.lmo_strategy.analyze(symbol, current_price)
            
            # ADIM 3: KRO + LMO BİRLİKTE KONFIRMASYON
            combined_signal = self._combine_crypto_strategies(kro_analysis, lmo_analysis, symbol, current_price)
            
            if combined_signal:
                signals.append(combined_signal)
                
        except Exception as e:
            print(f"❌ Combined crypto strategy analiz hatası {symbol}: {e}")
        
        return signals
    
    def _combine_crypto_strategies(self, kro_result, lmo_result, symbol: str, current_price: float) -> Optional[Dict]:
        """
        KRİTİK: Crypto KRO ve LMO'yu birleştirip tek güçlü sinyal oluştur
        """
        
        # Eğer sadece biri varsa, tek başına yeterli güvenilirlikte mi kontrol et
        if kro_result and not lmo_result:
            if kro_result['reliability_score'] >= 7 and kro_result['risk_reward'] >= 1.5:  # Crypto için güvenilirlik + RR
                kro_result['strategy'] = 'Crypto KRO (Strong)'
                kro_result['analysis'] = f"Güçlü Crypto KRO: {kro_result['analysis']}"
                return kro_result
            else:
                return None
        
        if lmo_result and not kro_result:
            if lmo_result['reliability_score'] >= 7 and lmo_result['risk_reward'] >= 1.5:  # Crypto için güvenilirlik + RR
                lmo_result['strategy'] = 'Crypto LMO (Strong)'  
                lmo_result['analysis'] = f"Güçlü Crypto LMO: {lmo_result['analysis']}"
                return lmo_result
            else:
                return None
        
        # Her ikisi de varsa KONFIRMASYON kontrolü
        if kro_result and lmo_result:
            
            # KURAL 1: Aynı yönde mi?
            if kro_result['signal_type'] != lmo_result['signal_type']:
                return None  # Çelişkili sinyaller
            
            # KURAL 2: Birleşik güvenilirlik hesapla
            combined_reliability = (kro_result['reliability_score'] + lmo_result['reliability_score']) / 2
            
            # Bonus: Her iki strateji de onayladığı için +1.5 bonus (crypto için)
            combined_reliability = min(combined_reliability + 1.5, 10)
            
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
            
            # KRİTİK: Combined Crypto stratejide de minimum 1.5 RR kontrolü!
            if risk_reward < 1.5:
                print(f"❌ {symbol} Crypto COMBINED sinyali reddedildi: RR {risk_reward} < 1.5 (Minimum RR standardı)")
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
                'reliability_score': round(combined_reliability, 1),
                'timeframe': '1h',
                'status': 'NEW',
                'analysis': combined_analysis,
                'risk_reward': risk_reward,
                'kro_score': kro_result['reliability_score'],
                'lmo_score': lmo_result['reliability_score'],
                'confirmation_type': 'CRYPTO_DOUBLE_CONFIRMATION',
                'asset_type': 'crypto'
            }
        
        return None
    
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