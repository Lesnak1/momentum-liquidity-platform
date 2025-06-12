// Vercel Serverless Function: Crypto Prices
export default function handler(req, res) {
  const cryptoPrices = {
    'BTCUSDT': 42500 + (Math.random() - 0.5) * 1000,
    'ETHUSDT': 2800 + (Math.random() - 0.5) * 100,
    'BNBUSDT': 320 + (Math.random() - 0.5) * 20,
    'ADAUSDT': 0.38 + (Math.random() - 0.5) * 0.05,
    'SOLUSDT': 95.50 + (Math.random() - 0.5) * 8,
    'DOGEUSDT': 0.078 + (Math.random() - 0.5) * 0.01,
    'MATICUSDT': 0.85 + (Math.random() - 0.5) * 0.08,
    'DOTUSDT': 5.25 + (Math.random() - 0.5) * 0.5
  };
  
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  res.status(200).json({
    prices: cryptoPrices,
    api_status: 'live',
    timestamp: new Date().toISOString()
  });
} 