"""
Enhanced Volume Analysis - Real Exchange Depth Integration
Gerçek order book depth ve volume profile analizi
"""

import time
import requests
from typing import Dict, List, Optional
from datetime import datetime

class EnhancedVolumeAnalyzer:
    """Gerçek exchange depth ve volume analizi"""
    
    def __init__(self, binance_provider):
        self.binance_provider = binance_provider
        self.cache = {}
        self.cache_duration = 30  # 30 saniye cache
    
    def get_order_book_depth(self, symbol: str, limit: int = 100) -> Dict:
        """Gerçek order book depth analizi"""
        cache_key = f'depth_{symbol}_{limit}'
        
        # Cache kontrolü
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Binance symbol formatına çevir
            binance_symbol = symbol.replace('/USD', 'USDT')
            
            # Order book depth API
            url = f"https://api.binance.com/api/v3/depth"
            params = {'symbol': binance_symbol, 'limit': limit}
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if 'bids' in data and 'asks' in data:
                depth_analysis = self._analyze_order_book_depth(data, symbol)
                
                # Cache'e kaydet
                self.cache[cache_key] = {
                    'data': depth_analysis,
                    'timestamp': time.time()
                }
                
                return depth_analysis
                
        except Exception as e:
            print(f"❌ Order book depth hatası {symbol}: {e}")
        
        return self._get_fallback_depth_analysis(symbol)
    
    def _analyze_order_book_depth(self, order_book: Dict, symbol: str) -> Dict:
        """Order book depth analizi"""
        bids = [[float(price), float(qty)] for price, qty in order_book['bids']]
        asks = [[float(price), float(qty)] for price, qty in order_book['asks']]
        
        # Bid/Ask volume analizi
        total_bid_volume = sum(qty for price, qty in bids)
        total_ask_volume = sum(qty for price, qty in asks)
        
        # Volume imbalance (alıcı/satıcı baskısı)
        volume_imbalance = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume)
        
        # Spread analizi
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0
        
        # Büyük duvarlar (whale levels)
        whale_bid_levels = []
        whale_ask_levels = []
        
        # Top 10% volume concentration
        bid_volumes = [qty for price, qty in bids]
        ask_volumes = [qty for price, qty in asks]
        
        if bid_volumes:
            whale_threshold_bid = sorted(bid_volumes, reverse=True)[min(10, len(bid_volumes)-1)]
            whale_bid_levels = [(price, qty) for price, qty in bids if qty >= whale_threshold_bid]
        
        if ask_volumes:
            whale_threshold_ask = sorted(ask_volumes, reverse=True)[min(10, len(ask_volumes)-1)]
            whale_ask_levels = [(price, qty) for price, qty in asks if qty >= whale_threshold_ask]
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'depth_quality': 'HIGH' if len(bids) >= 50 and len(asks) >= 50 else 'MEDIUM',
            'volume_imbalance': round(volume_imbalance, 4),
            'spread_percentage': round(spread * 100, 4),
            'total_bid_volume': round(total_bid_volume, 2),
            'total_ask_volume': round(total_ask_volume, 2),
            'whale_bid_levels': whale_bid_levels[:5],  # Top 5 whale bids
            'whale_ask_levels': whale_ask_levels[:5],  # Top 5 whale asks
            'market_sentiment': self._determine_market_sentiment(volume_imbalance, spread),
            'liquidity_score': self._calculate_liquidity_score(total_bid_volume, total_ask_volume, spread),
            'source': 'binance_orderbook'
        }
    
    def _determine_market_sentiment(self, volume_imbalance: float, spread: float) -> str:
        """Market sentiment belirleme"""
        if volume_imbalance > 0.2:
            return 'STRONG_BULLISH'
        elif volume_imbalance > 0.05:
            return 'BULLISH'
        elif volume_imbalance < -0.2:
            return 'STRONG_BEARISH'
        elif volume_imbalance < -0.05:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _calculate_liquidity_score(self, bid_vol: float, ask_vol: float, spread: float) -> float:
        """Liquidity score hesaplama (1-10)"""
        total_volume = bid_vol + ask_vol
        
        # Volume puanı (0-5)
        volume_score = min(5, total_volume / 1000)  # Her 1000 BTC/ETH için 1 puan
        
        # Spread puanı (0-5)  
        spread_score = max(0, 5 - (spread * 1000))  # Düşük spread = yüksek puan
        
        return min(10, volume_score + spread_score)
    
    def get_volume_profile(self, symbol: str, timeframe: str = '1h', limit: int = 24) -> Dict:
        """Volume profile analizi"""
        try:
            klines = self.binance_provider.get_klines(symbol, timeframe, limit)
            
            if len(klines) < 10:
                return self._get_fallback_volume_profile(symbol)
            
            # Volume profiling
            volumes = [k['volume'] for k in klines]
            prices = [k['close'] for k in klines]
            
            # Volume-weighted average price (VWAP)
            total_volume = sum(volumes)
            if total_volume > 0:
                vwap = sum(price * vol for price, vol in zip(prices, volumes)) / total_volume
            else:
                vwap = sum(prices) / len(prices)
            
            # Volume distribution
            recent_avg_volume = sum(volumes[-5:]) / 5  # Son 5 periyot ortalaması
            current_volume = volumes[-1]
            volume_ratio = current_volume / recent_avg_volume if recent_avg_volume > 0 else 1
            
            # Volume trend
            early_avg = sum(volumes[:len(volumes)//2]) / (len(volumes)//2)
            late_avg = sum(volumes[len(volumes)//2:]) / (len(volumes) - len(volumes)//2)
            volume_trend = 'INCREASING' if late_avg > early_avg * 1.1 else 'DECREASING' if late_avg < early_avg * 0.9 else 'STABLE'
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'vwap': round(vwap, 6),
                'current_vs_vwap': round((prices[-1] - vwap) / vwap * 100, 2),
                'volume_ratio': round(volume_ratio, 2),
                'volume_trend': volume_trend,
                'total_volume_24h': round(sum(volumes), 2),
                'avg_volume': round(sum(volumes) / len(volumes), 2),
                'volume_spikes': [i for i, vol in enumerate(volumes) if vol > recent_avg_volume * 2],
                'volume_profile_quality': 'HIGH' if len(klines) >= 20 else 'MEDIUM',
                'source': 'binance_klines'
            }
            
        except Exception as e:
            print(f"❌ Volume profile hatası {symbol}: {e}")
            return self._get_fallback_volume_profile(symbol)
    
    def _get_fallback_depth_analysis(self, symbol: str) -> Dict:
        """Fallback depth analizi"""
        return {
            'symbol': symbol,
            'depth_quality': 'LOW',
            'volume_imbalance': 0.0,
            'spread_percentage': 0.1,
            'market_sentiment': 'NEUTRAL',
            'liquidity_score': 5.0,
            'source': 'fallback'
        }
    
    def _get_fallback_volume_profile(self, symbol: str) -> Dict:
        """Fallback volume profile"""
        return {
            'symbol': symbol,
            'volume_ratio': 1.0,
            'volume_trend': 'STABLE',
            'volume_profile_quality': 'LOW',
            'source': 'fallback'
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Cache geçerliliği"""
        if cache_key not in self.cache:
            return False
        return (time.time() - self.cache[cache_key]['timestamp']) < self.cache_duration


class VolumeEnhancedSignalAnalyzer:
    """Volume enhanced signal analysis"""
    
    def __init__(self, volume_analyzer):
        self.volume_analyzer = volume_analyzer
    
    def enhance_signal_with_volume(self, signal: Dict) -> Dict:
        """Sinyali volume analizi ile güçlendir"""
        symbol = signal.get('symbol')
        if not symbol:
            return signal
        
        # Order book depth al
        depth_analysis = self.volume_analyzer.get_order_book_depth(symbol)
        
        # Volume profile al
        volume_profile = self.volume_analyzer.get_volume_profile(symbol)
        
        # Signal enhancement
        volume_bonus = 0
        volume_details = []
        
        # Depth quality bonus
        if depth_analysis['depth_quality'] == 'HIGH':
            volume_bonus += 1
            volume_details.append("High depth quality")
        
        # Volume imbalance bonus
        imbalance = depth_analysis['volume_imbalance']
        signal_type = signal.get('signal_type', 'BUY')
        
        if signal_type == 'BUY' and imbalance > 0.1:
            volume_bonus += 2
            volume_details.append(f"Bullish volume imbalance: {imbalance:.2f}")
        elif signal_type == 'SELL' and imbalance < -0.1:
            volume_bonus += 2
            volume_details.append(f"Bearish volume imbalance: {imbalance:.2f}")
        
        # Volume spike bonus
        if volume_profile['volume_ratio'] > 1.5:
            volume_bonus += 1
            volume_details.append(f"Volume spike: {volume_profile['volume_ratio']:.1f}x")
        
        # Liquidity score bonus
        if depth_analysis['liquidity_score'] >= 8:
            volume_bonus += 1
            volume_details.append(f"High liquidity: {depth_analysis['liquidity_score']:.1f}")
        
        # Signal'ı güncelle
        original_reliability = signal.get('reliability_score', 0)
        enhanced_reliability = min(10, original_reliability + volume_bonus)
        
        signal['volume_enhanced'] = True
        signal['volume_bonus'] = volume_bonus
        signal['original_reliability'] = original_reliability
        signal['reliability_score'] = enhanced_reliability
        signal['volume_analysis'] = {
            'depth_analysis': depth_analysis,
            'volume_profile': volume_profile,
            'enhancement_details': volume_details
        }
        
        return signal


def get_enhanced_volume_analyzer(binance_provider=None):
    """Enhanced volume analyzer factory"""
    if binance_provider:
        return EnhancedVolumeAnalyzer(binance_provider)
    return None 