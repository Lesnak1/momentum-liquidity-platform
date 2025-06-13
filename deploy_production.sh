#!/bin/bash

# Production Deployment Script for FTMO Trading Server
# 7/24 Sunucu Kurulumu

echo "🚀 FTMO Trading Server Production Deployment"
echo "=============================================="

# 1. Sistem güncellemeleri
echo "📦 Sistem güncellemeleri yapılıyor..."
sudo apt update && sudo apt upgrade -y

# 2. Python ve pip kurulumu
echo "🐍 Python kurulumu kontrol ediliyor..."
sudo apt install python3 python3-pip python3-venv -y

# 3. Screen kurulumu (7/24 çalışma için)
echo "🖥️ Screen kurulumu..."
sudo apt install screen -y

# 4. Proje dizinine git
echo "📁 Proje dizinine geçiliyor..."
cd /home/ubuntu/trading_server || exit 1

# 5. Virtual environment oluştur
echo "🏗️ Virtual environment oluşturuluyor..."
python3 -m venv venv
source venv/bin/activate

# 6. Dependencies kur
echo "📚 Python dependencies kuruluyor..."
pip install -r requirements.txt

# 7. Log dizini oluştur
echo "📝 Log dizinleri oluşturuluyor..."
mkdir -p backend/logs
mkdir -p frontend/build

# 8. Frontend build (eğer varsa)
echo "🎨 Frontend build işlemi..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    npm run build
    cd ..
fi

# 9. Environment variables ayarla
echo "🔧 Environment variables ayarlanıyor..."
cat > .env << EOF
# FTMO Production Environment
BINANCE_API_KEY=Z76mhJ8P8IzyfUCjbAV0vA27WedNEox4iHnqhWb7VnWN8bd2yMzxagOwD0OlMIgu
BINANCE_SECRET_KEY=kyKTYcuSJM3GuWxENOWyy9w5Irecd0BE4mNuiXePj9U22URid2TXduXPzU7lkzy2
EXCHANGERATE_API_KEY=your_forex_api_key_here
PRODUCTION_MODE=true
LOG_LEVEL=INFO
MAX_SIGNALS=15
SIGNAL_INTERVAL=180
ACCOUNT_SIZE=10000
RISK_PER_TRADE=1.0
EOF

# 10. Firewall ayarları
echo "🔥 Firewall ayarları..."
sudo ufw allow 8000/tcp
sudo ufw --force enable

# 11. Systemd service oluştur
echo "⚙️ Systemd service oluşturuluyor..."
sudo tee /etc/systemd/system/ftmo-trading.service > /dev/null << EOF
[Unit]
Description=FTMO Trading Signal Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trading_server
Environment=PATH=/home/ubuntu/trading_server/venv/bin
ExecStart=/home/ubuntu/trading_server/venv/bin/python backend/production_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 12. Service'i etkinleştir
echo "🔄 Service etkinleştiriliyor..."
sudo systemctl daemon-reload
sudo systemctl enable ftmo-trading.service

# 13. Screen session başlat (alternatif method)
echo "🖥️ Screen session hazırlanıyor..."
cat > start_server.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/trading_server
source venv/bin/activate
screen -dmS ftmo_trading python backend/production_server.py
echo "✅ FTMO Trading Server started in screen session 'ftmo_trading'"
echo "📱 Bağlanmak için: screen -r ftmo_trading"
echo "🔍 Logları görmek için: tail -f backend/logs/trading_server_*.log"
EOF

chmod +x start_server.sh

# 14. Stop script
cat > stop_server.sh << 'EOF'
#!/bin/bash
echo "🛑 FTMO Trading Server durduruluyor..."
screen -S ftmo_trading -X quit
sudo systemctl stop ftmo-trading.service
echo "✅ Server durduruldu"
EOF

chmod +x stop_server.sh

# 15. Health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
echo "🏥 FTMO Trading Server Health Check"
echo "==================================="

# Server durumu
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "📊 System Resources:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "Memory: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
echo "Disk: $(df -h | awk '$NF=="/"{printf "%s", $5}')"

echo ""
echo "📝 Son 10 log satırı:"
tail -10 backend/logs/trading_server_$(date +%Y%m%d).log
EOF

chmod +x health_check.sh

# 16. Monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash

while true; do
    # Health check
    HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null)
    
    if [ "$HEALTH" != "healthy" ]; then
        echo "⚠️ $(date): Server health issue detected: $HEALTH"
        
        # Restart attempt
        echo "🔄 $(date): Attempting restart..."
        ./stop_server.sh
        sleep 5
        ./start_server.sh
        
        # Wait and check again
        sleep 30
        HEALTH_AFTER=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null)
        echo "📊 $(date): Health after restart: $HEALTH_AFTER"
    else
        echo "✅ $(date): Server healthy"
    fi
    
    # Wait 5 minutes
    sleep 300
done
EOF

chmod +x monitor.sh

# 17. Crontab backup oluştur
echo "📅 Crontab backup job oluşturuluyor..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd /home/ubuntu/trading_server && tar -czf backup_$(date +\%Y\%m\%d).tar.gz backend/logs/ backend/*.db") | crontab -

# 18. Final instructions
echo ""
echo "🎉 FTMO Trading Server Deployment Tamamlandı!"
echo "============================================="
echo ""
echo "📋 Kullanım Komutları:"
echo "• Server başlat: ./start_server.sh"
echo "• Server durdur: ./stop_server.sh"
echo "• Health check: ./health_check.sh"
echo "• Monitor başlat: nohup ./monitor.sh &"
echo "• Screen'e bağlan: screen -r ftmo_trading"
echo "• Systemd ile başlat: sudo systemctl start ftmo-trading"
echo ""
echo "🌐 Server Endpoints:"
echo "• Ana API: http://your-server-ip:8000/signals"
echo "• Health Check: http://your-server-ip:8000/health"
echo "• Crypto Signals: http://your-server-ip:8000/crypto-signals"
echo "• Market Data: http://your-server-ip:8000/market-data"
echo ""
echo "📊 FTMO Özellikler:"
echo "• 10K hesap lot calculator aktif"
echo "• Risk management: %1 per trade"
echo "• Auto-recovery: 5 hata sonrası"
echo "• Signal interval: 3 dakika"
echo "• Max signals: 15"
echo ""
echo "💡 İlk Çalıştırma:"
echo "1. ./start_server.sh"
echo "2. ./health_check.sh"
echo "3. Frontend'den bağlanmayı test et"
echo "" 