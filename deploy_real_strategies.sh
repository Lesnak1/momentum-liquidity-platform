#!/bin/bash

echo "🚀 Gerçek Trading Strategies Deploy Script"
echo "Hetzner sunucusuna professional trading system yükleniyor..."

# Sunucu bilgileri
SERVER_IP="91.99.174.108"
SERVER_USER="root"
PROJECT_PATH="/opt/trading-platform/momentum-liquidity-platform"

echo "📡 Sunucuya bağlanılıyor: $SERVER_USER@$SERVER_IP"

# SSH ile sunucuya bağlan ve gerçek dosyaları deploy et
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'

echo "📁 Proje dizinine geçiliyor..."
cd /opt/trading-platform/momentum-liquidity-platform

echo "🔄 GitHub'dan en güncel versiyonu çekiliyor..."
git stash
git pull origin main

echo "📂 Backend dizinine geçiliyor..."
cd backend

echo "🐍 Virtual environment aktifleştiriliyor..."
source trading_env/bin/activate

echo "📦 Eksik modülleri yükleniyor..."
pip install numpy pandas python-binance ccxt websocket-client

echo "🔧 Enhanced Analysis aktifleştiriliyor..."
# crypto_strategies.py'da ENHANCED_ANALYSIS_AVAILABLE = True yap
sed -i 's/ENHANCED_ANALYSIS_AVAILABLE = False/ENHANCED_ANALYSIS_AVAILABLE = True/g' crypto_strategies.py

echo "🔍 Dosya durumunu kontrol ediliyor..."
ls -la crypto_strategies.py real_strategies.py enhanced_volume_analysis.py

echo "🛑 Eski backend'i durdur..."
screen -S trading-backend -X quit 2>/dev/null
pkill -f "python main.py" 2>/dev/null

echo "🚀 Yeni backend'i screen ile başlat..."
screen -dmS trading-backend bash -c 'cd /opt/trading-platform/momentum-liquidity-platform/backend && source trading_env/bin/activate && python main.py'

echo "⏱️ Backend'in başlaması için bekle..."
sleep 5

echo "✅ Backend durumu kontrol ediliyor..."
screen -ls | grep trading-backend

echo "🌐 API test ediliyor..."
curl -s http://localhost:8000/ | head -5

echo "🎯 Deploy tamamlandı!"
echo "📊 Platform erişim: http://91.99.174.108"
echo "🔧 Backend kontrol: screen -r trading-backend"

ENDSSH

echo "✅ Gerçek strategy deployment tamamlandı!"
echo "🌐 Platform: http://91.99.174.108"
echo "📊 API Test: http://91.99.174.108/api/signals" 