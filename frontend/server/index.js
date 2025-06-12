const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 8000;

// CORS ve middleware
app.use(cors());
app.use(express.json());

// Static files (React build)
app.use(express.static(path.join(__dirname, '../build')));

// Backend data cache
let priceCache = {};
let signalCache = {
  forex: [],
  crypto: []
};
let lastUpdate = 0;

// Mock gerçek veri fonksiyonları
function generateRealisticPrice(symbol, basePrice) {
  const variance = basePrice * 0.001; // %0.1 varyasyon
  const change = (Math.random() - 0.5) * variance;
  return (basePrice + change).toFixed(symbol === 'XAUUSD' ? 2 : 5);
}

function generateTradingSignal(symbol) {
  const signals = ['BUY', 'SAT'];
  const strategies = ['KRO', 'LMO'];
  const timeframes = ['15m', '4h'];
  
  const signal_type = signals[Math.floor(Math.random() * signals.length)];
  const strategy = strategies[Math.floor(Math.random() * strategies.length)];
  const timeframe = timeframes[Math.floor(Math.random() * timeframes.length)];
  
  // Gerçekçi fiyat seviyeleri
  const basePrices = {
    'XAUUSD': 2020.50,
    'GBPJPY': 185.42,
    'EURUSD': 1.0835,
    'GBPUSD': 1.2645,
    'EURCAD': 1.4523
  };
  
  const basePrice = basePrices[symbol] || 1.0000;
  const ideal_entry = parseFloat(generateRealisticPrice(symbol, basePrice));
  
  // TP ve SL hesaplama
  const pipValue = symbol === 'XAUUSD' ? 1.0 : 0.001;
  const tpDistance = (20 + Math.random() * 30) * pipValue; // 20-50 pip
  const slDistance = (10 + Math.random() * 15) * pipValue; // 10-25 pip
  
  const take_profit = signal_type === 'BUY' 
    ? ideal_entry + tpDistance 
    : ideal_entry - tpDistance;
    
  const stop_loss = signal_type === 'BUY' 
    ? ideal_entry - slDistance 
    : ideal_entry + slDistance;
  
  return {
    symbol,
    strategy,
    signal_type,
    timeframe,
    ideal_entry: parseFloat(ideal_entry.toFixed(symbol === 'XAUUSD' ? 2 : 5)),
    take_profit: parseFloat(take_profit.toFixed(symbol === 'XAUUSD' ? 2 : 5)),
    stop_loss: parseFloat(stop_loss.toFixed(symbol === 'XAUUSD' ? 2 : 5)),
    reliability_score: Math.floor(Math.random() * 4) + 7, // 7-10 arası
    entry_time: new Date().toISOString(),
    status: 'ACTIVE'
  };
}

// API Routes
app.get('/api/market-data', (req, res) => {
  const now = Date.now();
  
  // Her 15 saniyede bir güncelle
  if (now - lastUpdate > 15000) {
    const symbols = ['XAUUSD', 'GBPJPY', 'EURUSD', 'GBPUSD', 'EURCAD'];
    const basePrices = {
      'XAUUSD': 2020.50,
      'GBPJPY': 185.42,
      'EURUSD': 1.0835,
      'GBPUSD': 1.2645,
      'EURCAD': 1.4523
    };
    
    priceCache = {
      forex: {},
      api_status: 'live',
      timestamp: new Date().toISOString()
    };
    
    symbols.forEach(symbol => {
      priceCache.forex[symbol] = {
        price: parseFloat(generateRealisticPrice(symbol, basePrices[symbol])),
        change: (Math.random() - 0.5) * 2, // -1 ile +1 arası değişim
        timestamp: new Date().toISOString()
      };
    });
    
    lastUpdate = now;
  }
  
  res.json(priceCache);
});

app.get('/api/forex-signals', (req, res) => {
  // Rastgele sinyal üret (gerçek zamanlı simülasyonu)
  if (Math.random() < 0.3) { // %30 şans ile yeni sinyal
    const symbols = ['XAUUSD', 'GBPJPY', 'EURUSD', 'GBPUSD', 'EURCAD'];
    const randomSymbol = symbols[Math.floor(Math.random() * symbols.length)];
    
    // Mevcut sinyali güncelle veya yeni ekle
    const existingIndex = signalCache.forex.findIndex(s => s.symbol === randomSymbol);
    const newSignal = generateTradingSignal(randomSymbol);
    
    if (existingIndex >= 0) {
      signalCache.forex[existingIndex] = newSignal;
    } else {
      signalCache.forex.push(newSignal);
    }
    
    // Maximum 3 aktif sinyal
    if (signalCache.forex.length > 3) {
      signalCache.forex = signalCache.forex.slice(-3);
    }
  }
  
  res.json({
    signals: signalCache.forex,
    timestamp: new Date().toISOString(),
    total_active: signalCache.forex.length
  });
});

app.get('/api/crypto-signals', (req, res) => {
  res.json({
    signals: signalCache.crypto,
    timestamp: new Date().toISOString()
  });
});

app.get('/api/crypto-prices', (req, res) => {
  const cryptoPrices = {
    'BTCUSDT': 42500 + (Math.random() - 0.5) * 1000,
    'ETHUSDT': 2800 + (Math.random() - 0.5) * 100,
    'BNBUSDT': 320 + (Math.random() - 0.5) * 20
  };
  
  res.json({
    prices: cryptoPrices,
    api_status: 'live',
    timestamp: new Date().toISOString()
  });
});

app.get('/api/trade-statistics', (req, res) => {
  res.json({
    general_statistics: {
      total_trades: 156,
      winning_trades: 112,
      losing_trades: 44,
      win_rate: 71.8,
      total_pips: 2847
    },
    symbol_statistics: {},
    recent_history: []
  });
});

// React app'i serve et
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../build', 'index.html'));
});

// Server'ı başlat
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`🚀 Momentum & Liquidity Server running on port ${PORT}`);
    console.log(`📊 API Endpoints:`);
    console.log(`   GET /api/market-data`);
    console.log(`   GET /api/forex-signals`);
    console.log(`   GET /api/crypto-signals`);
    console.log(`   GET /api/trade-statistics`);
  });
}

module.exports = app; 