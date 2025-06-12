// Vercel Serverless Function: Crypto Signals
let cryptoSignalCache = [];

async function generateCryptoSignal(symbol) {
  const signals = ['BUY', 'SAT'];
  const strategies = ['KRO', 'LMO'];
  
  const signal_type = signals[Math.floor(Math.random() * signals.length)];
  const strategy = strategies[Math.floor(Math.random() * strategies.length)];
  
  // Gerçek anlık fiyatları al
  let basePrices = {};
  
  try {
    // Binance API'den güncel fiyatları çek
    const response = await fetch('https://api.binance.com/api/v3/ticker/price');
    if (response.ok) {
      const allPrices = await response.json();
      const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT', 'MATICUSDT', 'DOTUSDT'];
      
      allPrices.forEach(ticker => {
        if (symbols.includes(ticker.symbol)) {
          basePrices[ticker.symbol] = parseFloat(ticker.price);
        }
      });
    }
  } catch (error) {
    console.warn('Binance API failed for signals, using fallback prices');
  }
  
  // Fallback fiyatları
  if (Object.keys(basePrices).length === 0) {
    basePrices = {
      'BTCUSDT': 107000,
      'ETHUSDT': 3900,
      'BNBUSDT': 685,
      'ADAUSDT': 0.91,
      'SOLUSDT': 193.50,
      'DOGEUSDT': 0.315,
      'MATICUSDT': 0.485,
      'DOTUSDT': 7.22
    };
  }
  
  const basePrice = basePrices[symbol] || 1.0000;
  const ideal_entry = basePrice + (Math.random() - 0.5) * basePrice * 0.02;
  
  const percentChange = 0.02 + Math.random() * 0.03; // %2-5 arası
  const take_profit = signal_type === 'BUY' 
    ? ideal_entry * (1 + percentChange)
    : ideal_entry * (1 - percentChange);
    
  const stop_loss = signal_type === 'BUY' 
    ? ideal_entry * (1 - percentChange * 0.5)
    : ideal_entry * (1 + percentChange * 0.5);
  
  return {
    symbol,
    strategy,
    signal_type,
    timeframe: '15m',
    ideal_entry: parseFloat(ideal_entry.toFixed(symbol.includes('USDT') ? 5 : 8)),
    take_profit: parseFloat(take_profit.toFixed(symbol.includes('USDT') ? 5 : 8)),
    stop_loss: parseFloat(stop_loss.toFixed(symbol.includes('USDT') ? 5 : 8)),
    reliability_score: Math.floor(Math.random() * 4) + 7,
    entry_time: new Date().toISOString(),
    status: 'ACTIVE'
  };
}

export default async function handler(req, res) {
  // %25 şans ile yeni kripto sinyali
  if (Math.random() < 0.25) {
    const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT', 'MATICUSDT', 'DOTUSDT'];
    const randomSymbol = symbols[Math.floor(Math.random() * symbols.length)];
    
    const existingIndex = cryptoSignalCache.findIndex(s => s.symbol === randomSymbol);
    const newSignal = await generateCryptoSignal(randomSymbol);
    
    if (existingIndex >= 0) {
      cryptoSignalCache[existingIndex] = newSignal;
    } else {
      cryptoSignalCache.push(newSignal);
    }
    
    if (cryptoSignalCache.length > 2) {
      cryptoSignalCache = cryptoSignalCache.slice(-2);
    }
  }
  
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  res.status(200).json({
    signals: cryptoSignalCache,
    timestamp: new Date().toISOString()
  });
} 