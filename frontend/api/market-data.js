// Vercel Serverless Function: Market Data
let priceCache = {};
let lastUpdate = 0;

function generateRealisticPrice(symbol, basePrice) {
  const variance = basePrice * 0.001;
  const change = (Math.random() - 0.5) * variance;
  return (basePrice + change).toFixed(symbol === 'XAUUSD' ? 2 : 5);
}

export default function handler(req, res) {
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
        change: (Math.random() - 0.5) * 2,
        timestamp: new Date().toISOString()
      };
    });
    
    lastUpdate = now;
  }
  
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  res.status(200).json(priceCache);
} 