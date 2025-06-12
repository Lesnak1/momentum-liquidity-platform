"""
Binance WebSocket - Real-time Crypto Prices
En yüksek hacimli 10 kripto token için anlık fiyat akışı
"""

import json
import threading
import time
import urllib.request
from datetime import datetime
import websocket

class BinanceWebSocketStreamer:
    def __init__(self):
        self.ws = None
        self.prices = {}
        self.top_symbols = []
        self.is_running = False
        self.last_update = datetime.now()
        
    def get_top_volume_symbols(self, count=10):
        """Binance'den en yüksek hacimli coinleri çek"""
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
            
            # USDT çiftlerini filtrele ve hacme göre sırala
            usdt_pairs = [
                item for item in data 
                if item['symbol'].endswith('USDT') and 
                not any(x in item['symbol'] for x in ['DOWN', 'UP', 'BEAR', 'BULL'])
            ]
            
            # Hacme göre sırala
            sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
            
            # En yüksek hacimli 10 tanesini al
            top_symbols = [pair['symbol'] for pair in sorted_pairs[:count]]
            
            print(f"📊 En yüksek hacimli {count} kripto:")
            for i, symbol in enumerate(top_symbols, 1):
                volume = float(sorted_pairs[i-1]['quoteVolume'])
                price = float(sorted_pairs[i-1]['lastPrice'])
                print(f"{i}. {symbol}: ${price:.4f} (Volume: ${volume:,.0f})")
            
            return top_symbols
            
        except Exception as e:
            print(f"❌ Binance API hatası: {e}")
            # Fallback - popüler coinler
            return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT', 
                   'LINKUSDT', 'AVAXUSDT', 'UNIUSDT', 'LTCUSDT', 'XRPUSDT']
    
    def on_message(self, ws, message):
        """WebSocket mesajını işle"""
        try:
            data = json.loads(message)
            
            if 'stream' in data and 'data' in data:
                ticker_data = data['data']
                symbol = ticker_data['s']  # Symbol
                price = float(ticker_data['c'])  # Current price
                change_24h = float(ticker_data['P'])  # 24h change percent
                volume = float(ticker_data['q'])  # 24h quote volume
                
                # Fiyatı güncelle
                self.prices[symbol] = {
                    'price': price,
                    'change_24h': change_24h,
                    'volume_24h': volume,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'binance_websocket'
                }
                
                self.last_update = datetime.now()
                
                # Her 30 saniyede bir güncelleme yazdır
                if int(time.time()) % 30 == 0:
                    print(f"💰 {symbol}: ${price:.4f} ({change_24h:+.2f}%)")
                    
        except Exception as e:
            print(f"WebSocket mesaj hatası: {e}")
    
    def on_error(self, ws, error):
        """WebSocket hata durumu"""
        print(f"❌ WebSocket hatası: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket bağlantısı kapandı"""
        print("📡 WebSocket bağlantısı kapandı")
        self.is_running = False
    
    def on_open(self, ws):
        """WebSocket bağlantısı açıldı"""
        print("✅ Binance WebSocket bağlantısı kuruldu")
        self.is_running = True
    
    def start_stream(self):
        """WebSocket akışını başlat"""
        try:
            # En yüksek hacimli coinleri al
            self.top_symbols = self.get_top_volume_symbols(10)
            
            # WebSocket stream URL'si oluştur
            streams = [f"{symbol.lower()}@ticker" for symbol in self.top_symbols]
            stream_names = "/".join(streams)
            
            ws_url = f"wss://stream.binance.com:9443/stream?streams={stream_names}"
            
            print(f"🚀 Binance WebSocket başlatılıyor...")
            print(f"📡 {len(self.top_symbols)} kripto token izleniyor")
            
            # WebSocket oluştur
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # WebSocket'i ayrı thread'de çalıştır
            self.ws.run_forever()
            
        except Exception as e:
            print(f"❌ WebSocket başlatma hatası: {e}")
    
    def stop_stream(self):
        """WebSocket akışını durdur"""
        if self.ws:
            self.ws.close()
        self.is_running = False
    
    def get_current_prices(self):
        """Güncel fiyatları döndür"""
        return {
            'prices': self.prices,
            'symbols': self.top_symbols,
            'last_update': self.last_update.isoformat(),
            'status': 'live' if self.is_running else 'disconnected',
            'source': 'binance_websocket'
        }
    
    def is_healthy(self):
        """WebSocket sağlık durumu"""
        if not self.is_running:
            return False
        
        # Son güncelleme 1 dakikadan eskiyse sağlıksız
        time_diff = (datetime.now() - self.last_update).seconds
        return time_diff < 60

# Global instance
binance_streamer = None

def start_binance_websocket():
    """Global Binance WebSocket'i başlat"""
    global binance_streamer
    
    if binance_streamer is None:
        binance_streamer = BinanceWebSocketStreamer()
        
        # Ayrı thread'de başlat
        thread = threading.Thread(target=binance_streamer.start_stream, daemon=True)
        thread.start()
        
        # Başlaması için bekle
        time.sleep(3)
        
    return binance_streamer

def get_binance_prices():
    """Binance fiyatlarını getir"""
    global binance_streamer
    
    if binance_streamer is None:
        return None
        
    return binance_streamer.get_current_prices()

# Test kodu
if __name__ == "__main__":
    print("🚀 Binance WebSocket test başlatılıyor...")
    
    streamer = BinanceWebSocketStreamer()
    
    try:
        # WebSocket'i başlat
        thread = threading.Thread(target=streamer.start_stream, daemon=True)
        thread.start()
        
        # 30 saniye test et
        time.sleep(30)
        
        # Fiyatları yazdır
        prices = streamer.get_current_prices()
        print(f"\n📊 Toplam {len(prices['prices'])} kripto fiyatı alındı:")
        
        for symbol, data in prices['prices'].items():
            print(f"💰 {symbol}: ${data['price']:.4f} ({data['change_24h']:+.2f}%)")
            
    except KeyboardInterrupt:
        print("\n🛑 Test durduruldu")
        streamer.stop_stream() 