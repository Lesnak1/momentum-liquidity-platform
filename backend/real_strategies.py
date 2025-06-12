"""
GERÇEK KRO & LMO STRATEJİLERİ
Kullanıcının proje planındaki stratejilerin tam implementasyonu
Gerçek mum verileri + Gerçek teknik analiz + Gerçek hesaplamalar
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class RealTechnicalAnalysis:
    """Gerçek mum verilerinden teknik analiz"""
    
    @staticmethod
    def find_support_resistance(candles: List[Dict], lookback: int = 50) -> Dict:
        """Gerçek S/R seviyelerini geçmiş mumlardan tespit et"""
        if len(candles) < lookback:
            return {'support_levels': [], 'resistance_levels': []}
        
        recent_candles = candles[-lookback:]
        support_levels = []
        resistance_levels = []
        
        # Swing high/low noktalarını bul
        for i in range(2, len(recent_candles) - 2):
            current_high = recent_candles[i]['high']
            current_low = recent_candles[i]['low']
            
            # Resistance (Swing High) - Önceki ve sonraki 2 mumdan yüksek
            if (current_high > recent_candles[i-1]['high'] and 
                current_high > recent_candles[i-2]['high'] and
                current_high > recent_candles[i+1]['high'] and 
                current_high > recent_candles[i+2]['high']):
                resistance_levels.append({
                    'level': current_high,
                    'timestamp': recent_candles[i]['timestamp'],
                    'touches': 1
                })
            
            # Support (Swing Low) - Önceki ve sonraki 2 mumdan düşük
            if (current_low < recent_candles[i-1]['low'] and 
                current_low < recent_candles[i-2]['low'] and
                current_low < recent_candles[i+1]['low'] and 
                current_low < recent_candles[i+2]['low']):
                support_levels.append({
                    'level': current_low,
                    'timestamp': recent_candles[i]['timestamp'],
                    'touches': 1
                })
        
        # Benzer seviyeleri birleştir ve touch sayısını artır
        def consolidate_levels(levels, tolerance=0.002):
            if not levels:
                return []
            
            consolidated = []
            for level in levels:
                price = level['level']
                merged = False
                
                for existing in consolidated:
                    if abs(price - existing['level']) / existing['level'] < tolerance:
                        # Ortalama al ve touch sayısını artır
                        existing['level'] = (existing['level'] + price) / 2
                        existing['touches'] += 1
                        merged = True
                        break
                
                if not merged:
                    consolidated.append(level)
            
            return sorted(consolidated, key=lambda x: x['touches'], reverse=True)[:5]
        
        return {
            'support_levels': consolidate_levels(support_levels),
            'resistance_levels': consolidate_levels(resistance_levels)
        }
    
    @staticmethod
    def detect_breakout(current_price: float, sr_levels: Dict, tolerance: float = 0.001) -> Dict:
        """Gerçek kırılım tespiti"""
        result = {
            'breakout_type': None,
            'broken_level': None,
            'breakout_strength': 0
        }
        
        # Resistance kırılımı kontrolü
        for resistance in sr_levels['resistance_levels']:
            level = resistance['level']
            if current_price > level * (1 + tolerance):
                result['breakout_type'] = 'RESISTANCE_BREAK'
                result['broken_level'] = level
                result['breakout_strength'] = resistance['touches']
                break
        
        # Support kırılımı kontrolü (eğer resistance kırılımı yoksa)
        if not result['breakout_type']:
            for support in sr_levels['support_levels']:
                level = support['level']
                if current_price < level * (1 - tolerance):
                    result['breakout_type'] = 'SUPPORT_BREAK'
                    result['broken_level'] = level
                    result['breakout_strength'] = support['touches']
                    break
        
        return result
    
    @staticmethod
    def detect_retest(candles: List[Dict], broken_level: float, tolerance: float = 0.003) -> bool:
        """Retest tespiti - Son 10 mumda kırılan seviyeye dönüş var mı?"""
        if len(candles) < 10:
            return False
        
        recent_candles = candles[-10:]
        for candle in recent_candles:
            # Kırılan seviyeye yaklaşım var mı?
            if (abs(candle['low'] - broken_level) / broken_level < tolerance or
                abs(candle['high'] - broken_level) / broken_level < tolerance):
                return True
        
        return False
    
    @staticmethod
    def confirm_candle_pattern(candles: List[Dict]) -> Dict:
        """Son 3 mumda onay pattern'i var mı?"""
        if len(candles) < 3:
            return {'confirmed': False, 'pattern': None}
        
        last_3 = candles[-3:]
        
        # Bullish onay pattern'i
        green_candles = sum(1 for c in last_3 if c['close'] > c['open'])
        red_candles = sum(1 for c in last_3 if c['close'] < c['open'])
        
        # Son mum büyük body'li mi?
        last_candle = last_3[-1]
        body_size = abs(last_candle['close'] - last_candle['open'])
        total_range = last_candle['high'] - last_candle['low']
        strong_body = body_size > total_range * 0.7 if total_range > 0 else False
        
        if green_candles >= 2 and strong_body and last_candle['close'] > last_candle['open']:
            return {'confirmed': True, 'pattern': 'BULLISH', 'strength': green_candles}
        
        if red_candles >= 2 and strong_body and last_candle['close'] < last_candle['open']:
            return {'confirmed': True, 'pattern': 'BEARISH', 'strength': red_candles}
        
        return {'confirmed': False, 'pattern': None}
    
    @staticmethod
    def detect_liquidity_sweep(candles: List[Dict], current_price: float) -> Dict:
        """Likidite sweep tespiti"""
        if len(candles) < 20:
            return {'sweep_detected': False}
        
        recent_candles = candles[-20:]
        
        # Son 20 mumun en yüksek ve en düşük seviyeleri
        recent_highs = [c['high'] for c in recent_candles]
        recent_lows = [c['low'] for c in recent_candles]
        
        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)
        
        # Equal highs/lows (likidite seviyeleri)
        tolerance = 0.002
        equal_highs = [h for h in recent_highs if abs(h - highest_high) / highest_high < tolerance]
        equal_lows = [l for l in recent_lows if abs(l - lowest_low) / lowest_low < tolerance]
        
        # Sweep tespiti
        if len(equal_highs) >= 2 and current_price > highest_high * (1 + tolerance/2):
            return {
                'sweep_detected': True,
                'sweep_type': 'HIGH_SWEEP',
                'swept_level': highest_high,
                'liquidity_strength': len(equal_highs)
            }
        
        if len(equal_lows) >= 2 and current_price < lowest_low * (1 - tolerance/2):
            return {
                'sweep_detected': True,
                'sweep_type': 'LOW_SWEEP',
                'swept_level': lowest_low,
                'liquidity_strength': len(equal_lows)
            }
        
        return {'sweep_detected': False}
    
    @staticmethod
    def calculate_atr(candles: List[Dict], period: int = 14) -> float:
        """ATR ile gerçek volatilite hesaplama"""
        if len(candles) < period + 1:
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
            return sum(true_ranges[-period:]) / period
        
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0.01

class KROStrategy:
    """
    KRO Stratejisi: Kırılım + Retest + Onay
    Gerçek mum verilerinden tam implementasyon
    """
    
    def __init__(self, data_provider):
        self.name = "KRO"
        self.description = "Kırılım + Retest + Onay (Gerçek Veriler)"
        self.data_provider = data_provider
        self.min_reliability = 7
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """KRO stratejisi tam analizi"""
        try:
            # Geçmiş mum verilerini al (gerçek API'den)
            candles = self.data_provider.get_historical_data(symbol, '15m', 100)
            
            if len(candles) < 50:
                return None
            
            # ADIM 1: Support/Resistance seviyelerini tespit et
            sr_levels = RealTechnicalAnalysis.find_support_resistance(candles)
            
            if not sr_levels['support_levels'] and not sr_levels['resistance_levels']:
                return None
            
            # ADIM 2: Kırılım tespiti
            breakout = RealTechnicalAnalysis.detect_breakout(current_price, sr_levels)
            
            if not breakout['breakout_type']:
                return None
            
            # ADIM 3: Retest kontrolü
            retest_confirmed = RealTechnicalAnalysis.detect_retest(candles, breakout['broken_level'])
            
            # ADIM 4: Candle pattern onayı
            candle_confirm = RealTechnicalAnalysis.confirm_candle_pattern(candles)
            
            # ADIM 5: Güvenilirlik skoru hesaplama
            reliability_score = 0
            analysis_details = []
            
            # Kırılım gücü (touch sayısı)
            reliability_score += min(breakout['breakout_strength'], 4)
            analysis_details.append(f"Kırılım gücü: {breakout['breakout_strength']} touch")
            
            # Retest onayı
            if retest_confirmed:
                reliability_score += 3
                analysis_details.append("Retest onaylandı")
            
            # Candle pattern onayı
            if candle_confirm['confirmed']:
                reliability_score += 2
                analysis_details.append(f"Candle pattern: {candle_confirm['pattern']}")
            
            # Volume onayı (simulated but realistic)
            if len(candles) >= 20:
                recent_volumes = [c['volume'] for c in candles[-20:]]
                avg_volume = sum(recent_volumes) / len(recent_volumes)
                current_volume = candles[-1]['volume']
                
                if current_volume > avg_volume * 1.2:
                    reliability_score += 1
                    analysis_details.append(f"Volume onay: {current_volume/avg_volume:.1f}x")
            
            # Minimum güvenilirlik kontrolü
            if reliability_score < self.min_reliability:
                return None
            
            # ADIM 6: Sinyal yönü belirleme
            signal_type = None
            if breakout['breakout_type'] == 'RESISTANCE_BREAK':
                if candle_confirm.get('pattern') == 'BULLISH' or not candle_confirm['confirmed']:
                    signal_type = "BUY"
            elif breakout['breakout_type'] == 'SUPPORT_BREAK':
                if candle_confirm.get('pattern') == 'BEARISH' or not candle_confirm['confirmed']:
                    signal_type = "SELL"
            
            if not signal_type:
                return None
            
            # ADIM 7: TP/SL hesaplama (ATR bazlı + S/R seviyeleri)
            atr = RealTechnicalAnalysis.calculate_atr(candles)
            broken_level = breakout['broken_level']
            
            if signal_type == "BUY":
                # Giriş: Kırılan resistance üzerinde
                ideal_entry = max(current_price, broken_level * 1.001)
                
                # Stop Loss: Kırılan seviyenin altında
                stop_loss = broken_level * 0.997
                
                # Take Profit: ATR'nin 2 katı + next resistance
                take_profit = ideal_entry + (atr * 2)
                
                # Bir sonraki resistance varsa onu hedef al
                next_resistance = None
                for r in sr_levels['resistance_levels']:
                    if r['level'] > current_price:
                        next_resistance = r['level']
                        break
                
                if next_resistance:
                    take_profit = min(take_profit, next_resistance * 0.995)
            
            else:  # SELL
                # Giriş: Kırılan support altında
                ideal_entry = min(current_price, broken_level * 0.999)
                
                # Stop Loss: Kırılan seviyenin üzerinde
                stop_loss = broken_level * 1.003
                
                # Take Profit: ATR'nin 2 katı + next support
                take_profit = ideal_entry - (atr * 2)
                
                # Bir sonraki support varsa onu hedef al
                next_support = None
                for s in sr_levels['support_levels']:
                    if s['level'] < current_price:
                        next_support = s['level']
                        break
                
                if next_support:
                    take_profit = max(take_profit, next_support * 1.005)
            
            # Risk/Reward hesaplama
            risk = abs(ideal_entry - stop_loss)
            reward = abs(take_profit - ideal_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            # KRİTİK: Minimum 1.5 RR kontrolü - ASLA daha düşük RR kabul etme!
            if risk_reward < 1.5:
                print(f"❌ {symbol} KRO sinyali reddedildi: RR {risk_reward} < 1.5 (Minimum RR standardı)")
                return None
            
            return {
                'id': f"KRO_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'KRO',
                'signal_type': signal_type,
                'current_price': current_price,
                'ideal_entry': round(ideal_entry, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '15m',
                'status': 'NEW',
                'analysis': f"KRO: {', '.join(analysis_details)}",
                'risk_reward': risk_reward,
                'breakout_level': broken_level,
                'atr': round(atr, 6),
                'retest_confirmed': retest_confirmed
            }
            
        except Exception as e:
            print(f"❌ KRO analiz hatası {symbol}: {e}")
            return None

class LMOStrategy:
    """
    LMO Stratejisi: Liquidity Sweep + Candle Onayı
    Gerçek mum verilerinden tam implementasyon
    """
    
    def __init__(self, data_provider):
        self.name = "LMO"
        self.description = "Liquidity Sweep + Candle Onayı (Gerçek Veriler)"
        self.data_provider = data_provider
        self.min_reliability = 6
    
    def analyze(self, symbol: str, current_price: float) -> Optional[Dict]:
        """LMO stratejisi tam analizi"""
        try:
            # Geçmiş mum verilerini al
            candles = self.data_provider.get_historical_data(symbol, '15m', 100)
            
            if len(candles) < 50:
                return None
            
            # ADIM 1: Liquidity sweep tespiti
            sweep = RealTechnicalAnalysis.detect_liquidity_sweep(candles, current_price)
            
            if not sweep['sweep_detected']:
                return None
            
            # ADIM 2: Candle pattern onayı
            candle_confirm = RealTechnicalAnalysis.confirm_candle_pattern(candles)
            
            # ADIM 3: Support/Resistance analizi
            sr_levels = RealTechnicalAnalysis.find_support_resistance(candles)
            
            # ADIM 4: Güvenilirlik skoru hesaplama
            reliability_score = 0
            analysis_details = []
            
            # Sweep gücü
            reliability_score += min(sweep['liquidity_strength'], 3)
            analysis_details.append(f"Liquidity sweep: {sweep['sweep_type']}")
            
            # Candle pattern onayı
            if candle_confirm['confirmed']:
                reliability_score += 3
                analysis_details.append(f"Candle onay: {candle_confirm['pattern']}")
            
            # Volume analizi
            if len(candles) >= 20:
                recent_volumes = [c['volume'] for c in candles[-20:]]
                avg_volume = sum(recent_volumes) / len(recent_volumes)
                current_volume = candles[-1]['volume']
                
                if current_volume > avg_volume * 1.15:
                    reliability_score += 2
                    analysis_details.append(f"Volume onay: {current_volume/avg_volume:.1f}x")
            
            # Market structure onayı
            if len(candles) >= 30:
                trend_candles = candles[-30:]
                trend_direction = (trend_candles[-1]['close'] - trend_candles[0]['close']) / trend_candles[0]['close']
                
                if abs(trend_direction) > 0.01:  # %1'den fazla trend
                    reliability_score += 1
                    analysis_details.append(f"Trend onay: {trend_direction*100:.1f}%")
            
            if reliability_score < self.min_reliability:
                return None
            
            # ADIM 5: Sinyal yönü belirleme
            signal_type = None
            swept_level = sweep['swept_level']
            
            if sweep['sweep_type'] == 'HIGH_SWEEP':
                # Yüksek seviyeleri süpürdü, reversal bekleniyor
                if candle_confirm.get('pattern') == 'BEARISH' or not candle_confirm['confirmed']:
                    signal_type = "SELL"
            
            elif sweep['sweep_type'] == 'LOW_SWEEP':
                # Düşük seviyeleri süpürdü, reversal bekleniyor
                if candle_confirm.get('pattern') == 'BULLISH' or not candle_confirm['confirmed']:
                    signal_type = "BUY"
            
            if not signal_type:
                return None
            
            # ADIM 6: TP/SL hesaplama
            atr = RealTechnicalAnalysis.calculate_atr(candles)
            
            if signal_type == "BUY":
                # Giriş: Sweep seviyesinin üzerinde onay
                ideal_entry = max(current_price, swept_level * 1.002)
                
                # Stop Loss: Sweep seviyesinin altında
                stop_loss = swept_level * 0.996
                
                # Take Profit: ATR'nin 1.5 katı veya next resistance
                take_profit = ideal_entry + (atr * 1.5)
                
                # Next resistance kontrolü
                for r in sr_levels.get('resistance_levels', []):
                    if r['level'] > current_price:
                        take_profit = min(take_profit, r['level'] * 0.998)
                        break
            
            else:  # SELL
                # Giriş: Sweep seviyesinin altında onay
                ideal_entry = min(current_price, swept_level * 0.998)
                
                # Stop Loss: Sweep seviyesinin üzerinde
                stop_loss = swept_level * 1.004
                
                # Take Profit: ATR'nin 1.5 katı veya next support
                take_profit = ideal_entry - (atr * 1.5)
                
                # Next support kontrolü
                for s in sr_levels.get('support_levels', []):
                    if s['level'] < current_price:
                        take_profit = max(take_profit, s['level'] * 1.002)
                        break
            
            # Risk/Reward hesaplama
            risk = abs(ideal_entry - stop_loss)
            reward = abs(take_profit - ideal_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            # KRİTİK: Minimum 1.5 RR kontrolü - ASLA daha düşük RR kabul etme!
            if risk_reward < 1.5:
                print(f"❌ {symbol} LMO sinyali reddedildi: RR {risk_reward} < 1.5 (Minimum RR standardı)")
                return None
            
            return {
                'id': f"LMO_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'LMO',
                'signal_type': signal_type,
                'current_price': current_price,
                'ideal_entry': round(ideal_entry, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'reliability_score': min(reliability_score, 10),
                'timeframe': '15m',
                'status': 'NEW',
                'analysis': f"LMO: {', '.join(analysis_details)}",
                'risk_reward': risk_reward,
                'swept_level': swept_level,
                'sweep_type': sweep['sweep_type'],
                'atr': round(atr, 6)
            }
            
        except Exception as e:
            print(f"❌ LMO analiz hatası {symbol}: {e}")
            return None

class RealStrategyManager:
    """
    Gerçek KRO & LMO Stratejilerini Yönet
    KRİTİK: KRO + LMO birlikte konfirmasyon sistemi
    """
    
    def __init__(self, data_provider):
        self.data_provider = data_provider
        self.kro_strategy = KROStrategy(data_provider)
        self.lmo_strategy = LMOStrategy(data_provider)
        self.min_combined_reliability = 7  # Birleşik minimum güvenilirlik
    
    def analyze_symbol(self, symbol: str, current_price: float) -> List[Dict]:
        """
        KRİTİK: KRO + LMO BİRLİKTE KONFIRMASYON ANALİZİ
        Tek sinyal = İki stratejinin birlikte onayı
        """
        signals = []
        
        try:
            # ADIM 1: KRO analizi yap
            kro_analysis = self.kro_strategy.analyze(symbol, current_price)
            
            # ADIM 2: LMO analizi yap  
            lmo_analysis = self.lmo_strategy.analyze(symbol, current_price)
            
            # ADIM 3: KRO + LMO BİRLİKTE KONFIRMASYON
            combined_signal = self._combine_strategies(kro_analysis, lmo_analysis, symbol, current_price)
            
            if combined_signal:
                signals.append(combined_signal)
                
        except Exception as e:
            print(f"❌ Combined strategy analiz hatası {symbol}: {e}")
        
        return signals
    
    def _combine_strategies(self, kro_result, lmo_result, symbol: str, current_price: float) -> Optional[Dict]:
        """
        KRİTİK: KRO ve LMO'yu birleştirip tek güçlü sinyal oluştur
        
        Kombinasyon kuralları:
        1. Her iki strateji de aynı yöne işaret etmeli (BUY/SELL)
        2. Güvenilirlik skorları toplanıp normalize edilmeli
        3. Giriş, TP, SL birleşik analiz sonucu belirlenmeli
        """
        
        # Eğer sadece biri varsa, tek başına yeterli güvenilirlikte mi kontrol et
        if kro_result and not lmo_result:
            if kro_result['reliability_score'] >= 8 and kro_result['risk_reward'] >= 1.5:  # Yüksek güvenilirlik + RR
                kro_result['strategy'] = 'KRO (Strong)'
                kro_result['analysis'] = f"KRO Güçlü: {kro_result['analysis']}"
                return kro_result
            else:
                return None  # Tek başına yeterli değil
        
        if lmo_result and not kro_result:
            if lmo_result['reliability_score'] >= 8 and lmo_result['risk_reward'] >= 1.5:  # Yüksek güvenilirlik + RR
                lmo_result['strategy'] = 'LMO (Strong)'  
                lmo_result['analysis'] = f"LMO Güçlü: {lmo_result['analysis']}"
                return lmo_result
            else:
                return None  # Tek başına yeterli değil
        
        # Her ikisi de varsa KONFIRMASYON kontrolü
        if kro_result and lmo_result:
            
            # KURAL 1: Aynı yönde mi?
            if kro_result['signal_type'] != lmo_result['signal_type']:
                return None  # Çelişkili sinyaller, pas geç
            
            # KURAL 2: Birleşik güvenilirlik hesapla
            combined_reliability = (kro_result['reliability_score'] + lmo_result['reliability_score']) / 2
            
            # Bonus: Her iki strateji de onayladığı için +2 bonus
            combined_reliability = min(combined_reliability + 2, 10)
            
            if combined_reliability < self.min_combined_reliability:
                return None
            
            # KURAL 3: Birleşik fiyat seviyeleri hesapla
            signal_type = kro_result['signal_type']
            
            # Giriş seviyesi: İki analizin ortalaması
            combined_entry = (kro_result['ideal_entry'] + lmo_result['ideal_entry']) / 2
            
            # Stop Loss: Daha sıkı olanı (daha güvenli)
            if signal_type == 'BUY':
                combined_sl = max(kro_result['stop_loss'], lmo_result['stop_loss'])  # Daha yüksek SL (güvenli)
                combined_tp = min(kro_result['take_profit'], lmo_result['take_profit'])  # Daha yakın TP (güvenli)
            else:  # SELL
                combined_sl = min(kro_result['stop_loss'], lmo_result['stop_loss'])  # Daha düşük SL (güvenli)
                combined_tp = max(kro_result['take_profit'], lmo_result['take_profit'])  # Daha yakın TP (güvenli)
            
            # Risk/Reward yeniden hesapla
            risk = abs(combined_entry - combined_sl)
            reward = abs(combined_tp - combined_entry)
            risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
            
            # KRİTİK: Combined stratejide de minimum 1.5 RR kontrolü!
            if risk_reward < 1.5:
                print(f"❌ {symbol} COMBINED sinyali reddedildi: RR {risk_reward} < 1.5 (Minimum RR standardı)")
                return None
            
            # Birleşik analiz detayları
            combined_analysis = f"KRO+LMO Konfirmasyon: {kro_result['analysis'].split(': ', 1)[1]} | {lmo_result['analysis'].split(': ', 1)[1]}"
            
            return {
                'id': f"COMBINED_{symbol}_{int(time.time())}",
                'symbol': symbol,
                'strategy': 'KRO+LMO',  # KRİTİK: Birleşik strateji
                'signal_type': signal_type,
                'current_price': current_price,
                'ideal_entry': round(combined_entry, 5),
                'stop_loss': round(combined_sl, 5),
                'take_profit': round(combined_tp, 5),
                'reliability_score': round(combined_reliability, 1),
                'timeframe': '15m',
                'status': 'NEW',
                'analysis': combined_analysis,
                'risk_reward': risk_reward,
                'kro_score': kro_result['reliability_score'],
                'lmo_score': lmo_result['reliability_score'],
                'confirmation_type': 'DOUBLE_CONFIRMATION'
            }
        
        return None
    
    def get_best_signal(self, symbol: str, current_price: float) -> Optional[Dict]:
        """En iyi sinyali getir"""
        signals = self.analyze_symbol(symbol, current_price)
        
        if not signals:
            return None
        
        # En yüksek güvenilirlik skoru + risk/reward oranı
        signals.sort(key=lambda x: (x['reliability_score'], x['risk_reward']), reverse=True)
        return signals[0]

def get_real_strategy_manager(data_provider):
    """Gerçek strategy manager'ı getir"""
    return RealStrategyManager(data_provider) 