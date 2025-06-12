"""
Trading stratejilerini analiz eden modül
KRO: Kırılım + Retest + Onay (15m)
LMO: Likidite Alımı + Mum Onayı (4h + 15m)
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class StrategyAnalyzer:
    def __init__(self):
        self.kro_rr_ratio = 1.5  # Risk/Reward oranı KRO için
        self.lmo_rr_ratio = 3.0  # Risk/Reward oranı LMO için
        
    def find_sr_levels(self, df: pd.DataFrame, window: int = 20, min_touches: int = 2) -> list:
        """
        Destek/Direnç seviyelerini bulur
        
        Args:
            df (pd.DataFrame): OHLC verileri
            window (int): Analiz penceresi
            min_touches (int): Minimum temas sayısı
            
        Returns:
            list: S/R seviyelerinin listesi
        """
        try:
            levels = []
            
            # Swing High/Low noktalarını bul
            df['swing_high'] = df['high'].rolling(window=window, center=True).max() == df['high']
            df['swing_low'] = df['low'].rolling(window=window, center=True).min() == df['low']
            
            # Swing High seviyeleri
            swing_highs = df[df['swing_high']]['high'].values
            # Swing Low seviyeleri  
            swing_lows = df[df['swing_low']]['low'].values
            
            # Yakın seviyeleri grupla
            all_levels = list(swing_highs) + list(swing_lows)
            all_levels.sort()
            
            # Yakın seviyeleri birleştir (fiyatın %0.05'i kadar tolerans)
            tolerance_pct = 0.0005  # %0.05
            grouped_levels = []
            
            for level in all_levels:
                if not grouped_levels:
                    grouped_levels.append([level])
                else:
                    # Son gruba yakın mı kontrol et
                    last_group_avg = np.mean(grouped_levels[-1])
                    if abs(level - last_group_avg) / last_group_avg < tolerance_pct:
                        grouped_levels[-1].append(level)
                    else:
                        grouped_levels.append([level])
            
            # Her grup için ortalama seviyeyi al ve temas sayısını kontrol et
            for group in grouped_levels:
                if len(group) >= min_touches:
                    avg_level = np.mean(group)
                    levels.append({
                        'level': avg_level,
                        'touches': len(group),
                        'strength': len(group)  # Güç = temas sayısı
                    })
            
            # Güce göre sırala
            levels.sort(key=lambda x: x['strength'], reverse=True)
            
            logger.info(f"S/R seviyesi bulundu: {len(levels)} adet")
            return levels
            
        except Exception as e:
            logger.error(f"S/R seviye bulma hatası: {str(e)}")
            return []
    
    def analyze_kro(self, df: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """
        KRO Stratejisi: Kırılım + Retest + Onay (15m)
        
        Args:
            df (pd.DataFrame): 15m OHLC verileri
            symbol (str): Parite sembolu
            
        Returns:
            Optional[Dict]: Sinyal varsa sinyal bilgileri, yoksa None
        """
        try:
            if len(df) < 50:
                logger.warning(f"Yetersiz veri: {symbol}")
                return None
                
            # S/R seviyelerini bul
            sr_levels = self.find_sr_levels(df, window=10, min_touches=2)
            
            if not sr_levels:
                return None
            
            # Son 3 mumu analiz et
            last_candles = df.tail(3)
            if len(last_candles) < 3:
                return None
                
            breakout_candle = last_candles.iloc[-3]  # Kırılım mumu
            retest_candle = last_candles.iloc[-2]    # Retest mumu  
            confirmation_candle = last_candles.iloc[-1]  # Onay mumu
            
            # Her S/R seviyesi için kırılım kontrolü
            for level_info in sr_levels:
                level = level_info['level']
                level_strength = level_info['strength']
                
                # BULLISH SETUP kontrolü
                bullish_signal = self._check_bullish_kro(
                    breakout_candle, retest_candle, confirmation_candle, 
                    level, df, symbol
                )
                
                if bullish_signal:
                    # Güvenilirlik skoru hesapla
                    reliability_score = self._calculate_kro_reliability(
                        breakout_candle, retest_candle, confirmation_candle,
                        level_strength, df, 'BUY'
                    )
                    
                    if reliability_score >= 5:  # Minimum güvenilirlik
                        return {
                            'symbol': symbol,
                            'strategy': 'KRO',
                            'signal_type': 'BUY',
                            'entry_price': confirmation_candle['close'],
                            'stop_loss': retest_candle['low'] * 0.999,  # Biraz altına
                            'take_profit': confirmation_candle['close'] + (confirmation_candle['close'] - retest_candle['low'] * 0.999) * self.kro_rr_ratio,
                            'reliability_score': reliability_score,
                            'timestamp': datetime.now(),
                            'sr_level': level,
                            'timeframe': '15m'
                        }
                
                # BEARISH SETUP kontrolü
                bearish_signal = self._check_bearish_kro(
                    breakout_candle, retest_candle, confirmation_candle,
                    level, df, symbol
                )
                
                if bearish_signal:
                    # Güvenilirlik skoru hesapla
                    reliability_score = self._calculate_kro_reliability(
                        breakout_candle, retest_candle, confirmation_candle,
                        level_strength, df, 'SELL'
                    )
                    
                    if reliability_score >= 5:  # Minimum güvenilirlik
                        return {
                            'symbol': symbol,
                            'strategy': 'KRO',
                            'signal_type': 'SELL',
                            'entry_price': confirmation_candle['close'],
                            'stop_loss': retest_candle['high'] * 1.001,  # Biraz üstüne
                            'take_profit': confirmation_candle['close'] - (retest_candle['high'] * 1.001 - confirmation_candle['close']) * self.kro_rr_ratio,
                            'reliability_score': reliability_score,
                            'timestamp': datetime.now(),
                            'sr_level': level,
                            'timeframe': '15m'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"KRO analiz hatası {symbol}: {str(e)}")
            return None
    
    def _check_bullish_kro(self, breakout_candle, retest_candle, confirmation_candle, level, df, symbol):
        """Bullish KRO setup kontrolü"""
        try:
            # 1. Kırılım mumu kontrolü
            # Mumun gövdesi direnç seviyesinin üzerinde kapanmalı
            if breakout_candle['close'] <= level:
                return False
            
            # Mum gövdesi güçlü olmalı (toplam mumun %60'ı)
            body_ratio = abs(breakout_candle['close'] - breakout_candle['open']) / (breakout_candle['high'] - breakout_candle['low'])
            if body_ratio < 0.6:
                return False
            
            # 2. Retest mumu kontrolü
            # Mumun düşük fiyatı seviyeye dokunmalı ve altında kapanmamalı
            if retest_candle['low'] > level * 1.002:  # Seviyeye yeterince yaklaşmamış
                return False
            
            if retest_candle['close'] < level * 0.998:  # Seviyenin altında kapanmış
                return False
            
            # 3. Onay mumu kontrolü  
            # Retest mumunun yüksek seviyesinin üzerinde kapanmalı
            if confirmation_candle['close'] <= retest_candle['high']:
                return False
            
            # Onay mumu yükseliş mumu olmalı
            if confirmation_candle['close'] <= confirmation_candle['open']:
                return False
                
            logger.info(f"Bullish KRO setup bulundu: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Bullish KRO kontrol hatası: {str(e)}")
            return False
    
    def _check_bearish_kro(self, breakout_candle, retest_candle, confirmation_candle, level, df, symbol):
        """Bearish KRO setup kontrolü"""
        try:
            # 1. Kırılım mumu kontrolü
            # Mumun gövdesi destek seviyesinin altında kapanmalı
            if breakout_candle['close'] >= level:
                return False
            
            # Mum gövdesi güçlü olmalı
            body_ratio = abs(breakout_candle['close'] - breakout_candle['open']) / (breakout_candle['high'] - breakout_candle['low'])
            if body_ratio < 0.6:
                return False
            
            # 2. Retest mumu kontrolü
            # Mumun yüksek fiyatı seviyeye dokunmalı ve üstünde kapanmamalı
            if retest_candle['high'] < level * 0.998:  # Seviyeye yeterince yaklaşmamış
                return False
            
            if retest_candle['close'] > level * 1.002:  # Seviyenin üstünde kapanmış
                return False
            
            # 3. Onay mumu kontrolü
            # Retest mumunun düşük seviyesinin altında kapanmalı
            if confirmation_candle['close'] >= retest_candle['low']:
                return False
            
            # Onay mumu düşüş mumu olmalı
            if confirmation_candle['close'] >= confirmation_candle['open']:
                return False
                
            logger.info(f"Bearish KRO setup bulundu: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Bearish KRO kontrol hatası: {str(e)}")
            return False
    
    def _calculate_kro_reliability(self, breakout_candle, retest_candle, confirmation_candle, level_strength, df, signal_type):
        """KRO güvenilirlik skoru hesaplar (max 10 puan)"""
        try:
            score = 0
            
            # S/R seviyesinin kalitesi (max 2 puan)
            if level_strength >= 3:
                score += 2
            elif level_strength >= 2:
                score += 1
            
            # Kırılım mumunun hacmi (max 2 puan)
            avg_volume = df['volume'].tail(20).mean()
            if breakout_candle['volume'] > avg_volume * 1.5:
                score += 2
            elif breakout_candle['volume'] > avg_volume * 1.2:
                score += 1
            
            # Kırılım mumunun gövdesi (max 1 puan)
            body_ratio = abs(breakout_candle['close'] - breakout_candle['open']) / (breakout_candle['high'] - breakout_candle['low'])
            if body_ratio > 0.7:
                score += 1
            
            # Retest'in nizamlılığı (max 3 puan)
            if signal_type == 'BUY':
                # Retest seviyeye dokunup geri çekildi mi?
                if retest_candle['close'] > retest_candle['open']:  # Yükseliş retest mumu
                    score += 2
                if abs(retest_candle['low'] - breakout_candle['close']) / breakout_candle['close'] < 0.002:  # Seviyeye yakın
                    score += 1
            else:  # SELL
                if retest_candle['close'] < retest_candle['open']:  # Düşüş retest mumu  
                    score += 2
                if abs(retest_candle['high'] - breakout_candle['close']) / breakout_candle['close'] < 0.002:
                    score += 1
            
            # Onay mumunun gücü (max 2 puan)
            conf_body_ratio = abs(confirmation_candle['close'] - confirmation_candle['open']) / (confirmation_candle['high'] - confirmation_candle['low'])
            if conf_body_ratio > 0.7:
                score += 1
            if confirmation_candle['volume'] > avg_volume:
                score += 1
            
            return min(score, 10)  # Maksimum 10 puan
            
        except Exception as e:
            logger.error(f"KRO güvenilirlik hesaplama hatası: {str(e)}")
            return 0
    
    def analyze_lmo(self, df_4h: pd.DataFrame, df_15m: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """LMO stratejisi analizi"""
        try:
            # Basit LMO implementasyonu
            logger.info(f"LMO analizi yapıldı: {symbol}")
            return None  # Şimdilik basit
        except Exception as e:
            logger.error(f"LMO analiz hatası: {str(e)}")
            return None

# Test fonksiyonu
if __name__ == "__main__":
    analyzer = StrategyAnalyzer()
    logger.info("Strategy Analyzer test edildi") 