"""
Veritabanı yönetim modülü
"""
import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "trading_signals.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Veritabanını ve tabloları oluşturur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Signals tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        take_profit REAL NOT NULL,
                        reliability_score INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        status TEXT DEFAULT 'ACTIVE',
                        result TEXT DEFAULT NULL,
                        closed_price REAL DEFAULT NULL,
                        closed_timestamp TEXT DEFAULT NULL,
                        sr_level REAL DEFAULT NULL,
                        liquidity_level REAL DEFAULT NULL
                    )
                ''')
                
                # İndeksler
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON signals(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON signals(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON signals(timestamp)')
                
                conn.commit()
                logger.info("Veritabanı başarıyla oluşturuldu")
                
        except Exception as e:
            logger.error(f"Veritabanı oluşturma hatası: {str(e)}")
    
    def test_connection(self) -> bool:
        """Veritabanı bağlantısını test eder"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                logger.info("Veritabanı bağlantısı başarılı")
                return True
        except Exception as e:
            logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
            return False
    
    def save_signal(self, signal_data: Dict) -> bool:
        """Yeni sinyal kaydeder"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO signals (
                        symbol, strategy, signal_type, entry_price, stop_loss, 
                        take_profit, reliability_score, timestamp, timeframe,
                        sr_level, liquidity_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal_data['symbol'],
                    signal_data['strategy'],
                    signal_data['signal_type'],
                    signal_data['entry_price'],
                    signal_data['stop_loss'],
                    signal_data['take_profit'],
                    signal_data['reliability_score'],
                    signal_data['timestamp'].isoformat(),
                    signal_data['timeframe'],
                    signal_data.get('sr_level'),
                    signal_data.get('liquidity_level')
                ))
                
                conn.commit()
                logger.info(f"Sinyal kaydedildi: {signal_data['symbol']} - {signal_data['signal_type']}")
                return True
                
        except Exception as e:
            logger.error(f"Sinyal kaydetme hatası: {str(e)}")
            return False
    
    def get_signals_by_symbol(self, symbol: str, limit: int = 20) -> List[Dict]:
        """Belirli parite için sinyalleri getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM signals 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (symbol, limit))
                
                columns = [desc[0] for desc in cursor.description]
                signals = []
                
                for row in cursor.fetchall():
                    signal = dict(zip(columns, row))
                    signals.append(signal)
                
                return signals
                
        except Exception as e:
            logger.error(f"Sinyal getirme hatası: {str(e)}")
            return []
    
    def get_active_signals(self) -> List[Dict]:
        """Aktif sinyalleri getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM signals 
                    WHERE status = 'ACTIVE' 
                    ORDER BY timestamp DESC
                ''')
                
                columns = [desc[0] for desc in cursor.description]
                signals = []
                
                for row in cursor.fetchall():
                    signal = dict(zip(columns, row))
                    signals.append(signal)
                
                return signals
                
        except Exception as e:
            logger.error(f"Aktif sinyal getirme hatası: {str(e)}")
            return []
    
    def get_active_signals_count(self) -> int:
        """Aktif sinyal sayısını getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'ACTIVE'")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Aktif sinyal sayısı hatası: {str(e)}")
            return 0
    
    def get_latest_signal(self, symbol: str) -> Optional[Dict]:
        """Belirli parite için en son sinyali getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM signals 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (symbol,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                
                return None
                
        except Exception as e:
            logger.error(f"Son sinyal getirme hatası: {str(e)}")
            return None
    
    def update_signal_status(self, signal_id: int, status: str, result: str = None, closed_price: float = None) -> bool:
        """Sinyal durumunu günceller"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE signals 
                    SET status = ?, result = ?, closed_price = ?, closed_timestamp = ?
                    WHERE id = ?
                ''', (status, result, closed_price, datetime.now().isoformat(), signal_id))
                
                conn.commit()
                logger.info(f"Sinyal durumu güncellendi: {signal_id} - {status}")
                return True
                
        except Exception as e:
            logger.error(f"Sinyal güncelleme hatası: {str(e)}")
            return False
    
    def get_performance_stats(self, symbol: str = None, days: int = 30) -> Dict:
        """Performans istatistiklerini getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Son N günün verilerini al
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                base_query = '''
                    SELECT 
                        COUNT(*) as total_signals,
                        SUM(CASE WHEN result = 'TP' THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN result = 'SL' THEN 1 ELSE 0 END) as failed,
                        AVG(reliability_score) as avg_reliability
                    FROM signals 
                    WHERE timestamp >= ? AND status != 'ACTIVE'
                '''
                
                if symbol:
                    base_query += ' AND symbol = ?'
                    cursor.execute(base_query, (cutoff_date, symbol))
                else:
                    cursor.execute(base_query, (cutoff_date,))
                
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    total, successful, failed, avg_reliability = result
                    win_rate = (successful / total) * 100 if total > 0 else 0
                    
                    return {
                        'total_signals': total,
                        'successful': successful,
                        'failed': failed,
                        'win_rate': round(win_rate, 2),
                        'avg_reliability': round(avg_reliability, 2) if avg_reliability else 0
                    }
                else:
                    return {
                        'total_signals': 0,
                        'successful': 0,
                        'failed': 0,
                        'win_rate': 0,
                        'avg_reliability': 0
                    }
                
        except Exception as e:
            logger.error(f"Performans istatistik hatası: {str(e)}")
            return {
                'total_signals': 0,
                'successful': 0,
                'failed': 0,
                'win_rate': 0,
                'avg_reliability': 0
            }

# Test fonksiyonu
if __name__ == "__main__":
    db = DatabaseManager()
    
    # Test sinyali
    test_signal = {
        'symbol': 'XAUUSD',
        'strategy': 'KRO',
        'signal_type': 'BUY',
        'entry_price': 2000.50,
        'stop_loss': 1995.00,
        'take_profit': 2008.25,
        'reliability_score': 8,
        'timestamp': datetime.now(),
        'timeframe': '15m',
        'sr_level': 2000.00
    }
    
    db.save_signal(test_signal)
    print("Test tamamlandı!") 