"""
Trade Monitor - TP/SL Otomatik Kapanış Sistemi
Aktif işlemleri izler ve hedef/stop seviyelerine ulaşıldığında otomatik kapatır

KRİTİK KURAL: İşlem oluştuğunda entry_price, take_profit, stop_loss SABİT KALIR!
Sadece current_price güncellenir. TP/SL'ye ulaşana kadar fiyatlar DEĞİŞMEZ!
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class TradeMonitor:
    def __init__(self):
        self.active_trades = {}
        self.trade_history = []
        self.statistics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pips': 0.0,
            'avg_risk_reward': 0.0
        }
        # KRİTİK: Her symbol için ayrı başarı oranı tutulacak
        self.symbol_statistics = {}
        self.load_trade_history()
    
    def start_monitoring(self):
        """Trade monitoring sistemini başlat"""
        print("✅ Trade monitoring sistemi başlatıldı")
        return True
    
    def add_trade(self, trade_data):
        """
        Yeni işlem ekle
        
        KRİTİK: Bu noktada belirlenen entry_price, take_profit, stop_loss
        işlem kapanana kadar SABİT KALACAK! Hiçbir şekilde değişmeyecek!
        """
        trade_id = trade_data.get('id')
        
        # İşlemi aktif listeye ekle - FİYATLAR SABİT!
        self.active_trades[trade_id] = {
            **trade_data,
            'open_time': datetime.now().isoformat(),
            'status': 'ACTIVE',
            'current_price': trade_data.get('ideal_entry', 0),  # Başlangıç current_price
            
            # KRİTİK: Bu fiyatlar artık SABİT - asla değişmeyecek!
            'entry_price': trade_data.get('ideal_entry', 0),  # SABİT
            'take_profit': trade_data.get('take_profit', 0),  # SABİT  
            'stop_loss': trade_data.get('stop_loss', 0),      # SABİT
            
            'pip_movement': 0.0,
            'unrealized_pnl': 0.0
        }
        
        print(f"🟢 Yeni işlem eklendi: {trade_data['symbol']} {trade_data['signal_type']} @ {trade_data['ideal_entry']}")
        print(f"   📌 SABİT TP: {trade_data.get('take_profit')} | SL: {trade_data.get('stop_loss')}")
    
    def update_price(self, symbol: str, current_price: float):
        """
        Fiyat güncellemesi ve TP/SL kontrolü
        
        KRİTİK: Sadece current_price güncellenir!
        entry_price, take_profit, stop_loss değişmez!
        """
        trades_to_close = []
        
        for trade_id, trade in self.active_trades.items():
            if trade['symbol'] == symbol:
                # KRİTİK: Sadece current_price güncellenır - diğer fiyatlar SABİT!
                old_price = trade['current_price']
                trade['current_price'] = current_price
                
                # entry_price, take_profit, stop_loss asla değişmiyor!
                # Bu değerler add_trade() metodunda bir kez belirleniyor!
                
                # Pip hareketi hesapla (SABİT entry_price kullanarak)
                entry_price = trade['entry_price']  # SABİT DEĞER
                if trade['signal_type'] == 'BUY':
                    pip_movement = (current_price - entry_price) * 10000
                else:  # SELL
                    pip_movement = (entry_price - current_price) * 10000
                
                trade['pip_movement'] = round(pip_movement, 1)
                
                # PnL hesapla (SABİT entry_price kullanarak)
                if trade['signal_type'] == 'BUY':
                    trade['unrealized_pnl'] = (current_price - entry_price) / entry_price * 100
                else:
                    trade['unrealized_pnl'] = (entry_price - current_price) / entry_price * 100
                
                # TP/SL kontrolü (SABİT TP/SL seviyeleri kullanarak)
                if self._check_tp_sl(trade, current_price):
                    trades_to_close.append(trade_id)
        
        # İşlemleri kapat
        for trade_id in trades_to_close:
            self._close_trade(trade_id)
    
    def _check_tp_sl(self, trade, current_price) -> bool:
        """
        TP veya SL seviyesine ulaşıp ulaşmadığını kontrol et
        
        KRİTİK: SABİT take_profit ve stop_loss değerleri kullanılır!
        """
        # KRİTİK: Bu değerler işlem açıldığından beri SABİT!
        tp_price = trade['take_profit']  # SABİT DEĞER
        sl_price = trade['stop_loss']    # SABİT DEĞER
        signal_type = trade['signal_type']
        
        if signal_type == 'BUY':
            # BUY işleminde: current_price >= TP (kazanç) veya current_price <= SL (zarar)
            if current_price >= tp_price:
                trade['close_reason'] = 'TP'
                trade['result'] = 'WIN'
                return True
            elif current_price <= sl_price:
                trade['close_reason'] = 'SL'
                trade['result'] = 'LOSS'
                return True
                
        else:  # SELL
            # SELL işleminde: current_price <= TP (kazanç) veya current_price >= SL (zarar)
            if current_price <= tp_price:
                trade['close_reason'] = 'TP'
                trade['result'] = 'WIN'
                return True
            elif current_price >= sl_price:
                trade['close_reason'] = 'SL'
                trade['result'] = 'LOSS'
                return True
        
        return False
    
    def _close_trade(self, trade_id):
        """İşlemi kapat ve geçmişe kaydet"""
        if trade_id not in self.active_trades:
            return
            
        trade = self.active_trades[trade_id]
        
        # Kapanış bilgilerini ekle
        trade['close_time'] = datetime.now().isoformat()
        trade['close_price'] = trade['current_price']
        trade['status'] = 'CLOSED'
        
        # Kazanç/Zarar hesapla
        entry_price = trade['entry_price']
        close_price = trade['close_price']
        
        if trade['signal_type'] == 'BUY':
            pips_earned = (close_price - entry_price) * 10000
        else:
            pips_earned = (entry_price - close_price) * 10000
            
        trade['pips_earned'] = round(pips_earned, 1)
        
        # İstatistikleri güncelle
        self._update_statistics(trade)
        
        # Geçmişe ekle
        self.trade_history.append(trade.copy())
        
        # Aktif listeden çıkar
        del self.active_trades[trade_id]
        
        # Sonucu log'la
        result_emoji = "✅" if trade['result'] == 'WIN' else "❌"
        print(f"{result_emoji} İşlem kapandı: {trade['symbol']} {trade['signal_type']} | "
              f"{trade['close_reason']} | {trade['pips_earned']:+.1f} pips | "
              f"Süre: {self._calculate_duration(trade['open_time'], trade['close_time'])}")
        
        # Trade history'yi kaydet
        self.save_trade_history()
    
    def _update_statistics(self, trade):
        """
        İstatistikleri güncelle
        KRİTİK: Hem genel hem de symbol-bazlı istatistikleri tutar
        """
        symbol = trade['symbol']
        
        # Genel istatistikler
        self.statistics['total_trades'] += 1
        
        if trade['result'] == 'WIN':
            self.statistics['winning_trades'] += 1
        else:
            self.statistics['losing_trades'] += 1
            
        # Win rate hesapla
        total = self.statistics['total_trades']
        wins = self.statistics['winning_trades']
        self.statistics['win_rate'] = round((wins / total) * 100, 1) if total > 0 else 0
        
        # Toplam pip
        self.statistics['total_pips'] += trade.get('pips_earned', 0)
        self.statistics['total_pips'] = round(self.statistics['total_pips'], 1)
        
        # KRİTİK: Symbol-bazlı istatistikler (her token için ayrı)
        if symbol not in self.symbol_statistics:
            self.symbol_statistics[symbol] = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pips': 0.0,
                'strategy_performance': {}  # KRO/LMO ayrı performans
            }
        
        symbol_stats = self.symbol_statistics[symbol]
        symbol_stats['total_trades'] += 1
        
        if trade['result'] == 'WIN':
            symbol_stats['winning_trades'] += 1
        else:
            symbol_stats['losing_trades'] += 1
            
        # Symbol win rate hesapla
        symbol_total = symbol_stats['total_trades']
        symbol_wins = symbol_stats['winning_trades']
        symbol_stats['win_rate'] = round((symbol_wins / symbol_total) * 100, 1) if symbol_total > 0 else 0
        
        # Symbol toplam pip
        symbol_stats['total_pips'] += trade.get('pips_earned', 0)
        symbol_stats['total_pips'] = round(symbol_stats['total_pips'], 1)
        
        # Strateji bazlı performans (KRO+LMO birleşik sistem)
        strategy = trade.get('strategy', 'Unknown')
        if strategy not in symbol_stats['strategy_performance']:
            symbol_stats['strategy_performance'][strategy] = {
                'total': 0, 'wins': 0, 'win_rate': 0.0,
                'kro_score_avg': 0.0, 'lmo_score_avg': 0.0  # Birleşik analiz için
            }
        
        strategy_perf = symbol_stats['strategy_performance'][strategy]
        strategy_perf['total'] += 1
        if trade['result'] == 'WIN':
            strategy_perf['wins'] += 1
        strategy_perf['win_rate'] = round((strategy_perf['wins'] / strategy_perf['total']) * 100, 1)
        
        # Birleşik strateji skorları (eğer varsa)
        if 'kro_score' in trade and 'lmo_score' in trade:
            strategy_perf['kro_score_avg'] = (strategy_perf['kro_score_avg'] * (strategy_perf['total'] - 1) + trade['kro_score']) / strategy_perf['total']
            strategy_perf['lmo_score_avg'] = (strategy_perf['lmo_score_avg'] * (strategy_perf['total'] - 1) + trade['lmo_score']) / strategy_perf['total']
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """İşlem süresini hesapla"""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = end - start
            
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            if hours > 0:
                return f"{hours}s {minutes}dk"
            else:
                return f"{minutes}dk"
                
        except:
            return "Bilinmiyor"
    
    def get_active_trades(self):
        """Aktif işlemleri getir"""
        return list(self.active_trades.values())
    
    def get_statistics(self):
        """İstatistikleri getir"""
        return self.statistics.copy()
    
    def get_symbol_statistics(self, symbol: str = None):
        """
        Symbol bazlı istatistikleri getir
        KRİTİK: Her token için ayrı başarı oranları
        """
        if symbol:
            return self.symbol_statistics.get(symbol, {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pips': 0.0,
                'strategy_performance': {}
            })
        else:
            return self.symbol_statistics.copy()
    
    def get_recent_history(self, limit: int = 10):
        """Son işlem geçmişini getir"""
        return self.trade_history[-limit:] if len(self.trade_history) >= limit else self.trade_history
    
    def record_completed_trade(self, trade_result):
        """
        TP/SL'e ulaşan trade'i kaydet
        Backend'den gelen completed trade sonuçlarını işler
        """
        try:
            # Trade history'ye ekle
            completed_trade = {
                'signal_id': trade_result['signal_id'],
                'symbol': trade_result['symbol'],
                'strategy': trade_result['strategy'],
                'signal_type': trade_result['signal_type'],
                'entry_price': trade_result['entry_price'],
                'exit_price': trade_result['exit_price'],
                'take_profit': trade_result['take_profit'],
                'stop_loss': trade_result['stop_loss'],
                'result': trade_result['result'],  # PROFIT/LOSS
                'result_type': trade_result['result_type'],  # TP_HIT/SL_HIT
                'reliability_score': trade_result['reliability_score'],
                'entry_time': trade_result['entry_time'],
                'exit_time': trade_result['exit_time'],
                'asset_type': trade_result['asset_type'],
                'status': 'COMPLETED',
                
                # Pip hesaplama
                'pips_earned': trade_result.get('pip_gain', 0) if trade_result['result'] == 'PROFIT' 
                              else -trade_result.get('pip_loss', 0),
                
                # Süre hesaplama
                'duration': self._calculate_duration(trade_result['entry_time'], trade_result['exit_time'])
            }
            
            self.trade_history.append(completed_trade)
            
            # İstatistikleri güncelle
            self._update_completed_statistics(trade_result)
            
            # Kaydet
            self.save_trade_history()
            
            # Log
            result_emoji = "🎯" if trade_result['result'] == 'PROFIT' else "🛑"
            pip_change = completed_trade['pips_earned']
            print(f"{result_emoji} Trade kaydedildi: {trade_result['symbol']} {trade_result['signal_type']} | "
                  f"{trade_result['result_type']} | {pip_change:+.1f} pips | "
                  f"Güvenilirlik: {trade_result['reliability_score']}/10")
            
        except Exception as e:
            print(f"❌ Trade kaydetme hatası: {e}")
    
    def _update_completed_statistics(self, trade_result):
        """Tamamlanan trade için istatistik güncelle"""
        symbol = trade_result['symbol']
        
        # Genel istatistikler
        self.statistics['total_trades'] += 1
        
        if trade_result['result'] == 'PROFIT':
            self.statistics['winning_trades'] += 1
            pip_gain = trade_result.get('pip_gain', 0)
            self.statistics['total_pips'] += pip_gain
        else:
            self.statistics['losing_trades'] += 1  
            pip_loss = trade_result.get('pip_loss', 0)
            self.statistics['total_pips'] -= pip_loss
        
        # Win rate hesapla
        total = self.statistics['total_trades']
        wins = self.statistics['winning_trades'] 
        self.statistics['win_rate'] = round((wins / total) * 100, 1) if total > 0 else 0
        
        # Total pips round
        self.statistics['total_pips'] = round(self.statistics['total_pips'], 1)
        
        # Symbol-bazlı istatistikler
        if symbol not in self.symbol_statistics:
            self.symbol_statistics[symbol] = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pips': 0.0,
                'avg_reliability': 0.0,
                'best_strategy': '',
                'strategies': {}
            }
        
        symbol_stats = self.symbol_statistics[symbol]
        symbol_stats['total_trades'] += 1
        
        if trade_result['result'] == 'PROFIT':
            symbol_stats['winning_trades'] += 1
            symbol_stats['total_pips'] += trade_result.get('pip_gain', 0)
        else:
            symbol_stats['losing_trades'] += 1
            symbol_stats['total_pips'] -= trade_result.get('pip_loss', 0)
        
        # Symbol win rate
        symbol_total = symbol_stats['total_trades']
        symbol_wins = symbol_stats['winning_trades']
        symbol_stats['win_rate'] = round((symbol_wins / symbol_total) * 100, 1) if symbol_total > 0 else 0
        
        # Total pips round
        symbol_stats['total_pips'] = round(symbol_stats['total_pips'], 1)
        
        # Average reliability
        symbol_stats['avg_reliability'] = round(
            (symbol_stats.get('avg_reliability', 0) * (symbol_total - 1) + trade_result['reliability_score']) / symbol_total, 1
        )
        
        # Strategy tracking
        strategy = trade_result['strategy']
        if strategy not in symbol_stats['strategies']:
            symbol_stats['strategies'][strategy] = {'wins': 0, 'total': 0}
        
        symbol_stats['strategies'][strategy]['total'] += 1
        if trade_result['result'] == 'PROFIT':
            symbol_stats['strategies'][strategy]['wins'] += 1
        
        # Best strategy
        best_strategy = ''
        best_win_rate = 0
        for strat, data in symbol_stats['strategies'].items():
            if data['total'] >= 3:  # En az 3 trade
                win_rate = (data['wins'] / data['total']) * 100
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_strategy = strat
        symbol_stats['best_strategy'] = best_strategy
    
    def save_trade_history(self):
        """Trade geçmişini dosyaya kaydet"""
        try:
            with open('trade_history.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'trade_history': self.trade_history,
                    'statistics': self.statistics
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Trade history kaydetme hatası: {e}")
    
    def load_trade_history(self):
        """Trade geçmişini yükle"""
        try:
            with open('trade_history.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.trade_history = data.get('trade_history', [])
                self.statistics = data.get('statistics', self.statistics)
        except FileNotFoundError:
            print("Trade history dosyası bulunamadı, yeni başlatılıyor...")
        except Exception as e:
            print(f"Trade history yükleme hatası: {e}")

# Global monitor instance
trade_monitor = TradeMonitor()

def get_trade_monitor():
    """Global trade monitor'ü getir"""
    return trade_monitor 