// Vercel Serverless Function: Crypto Prices
export default function handler(req, res) {
  const cryptoPrices = {
    'BTCUSDT': 42500 + (Math.random() - 0.5) * 1000,
    'ETHUSDT': 2800 + (Math.random() - 0.5) * 100,
    'BNBUSDT': 320 + (Math.random() - 0.5) * 20
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