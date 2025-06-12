// Vercel Serverless Function: Forex Signals
let signalCache = [];

function generateRealisticPrice(symbol, basePrice) {
  const variance = basePrice * 0.001;
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
  
  const basePrices = {
    'XAUUSD': 2020.50,
    'GBPJPY': 185.42,
    'EURUSD': 1.0835,
    'GBPUSD': 1.2645,
    'EURCAD': 1.4523
  };
  
  const basePrice = basePrices[symbol] || 1.0000;
  const ideal_entry = parseFloat(generateRealisticPrice(symbol, basePrice));
  
  const pipValue = symbol === 'XAUUSD' ? 1.0 : 0.001;
  const tpDistance = (20 + Math.random() * 30) * pipValue;
  const slDistance = (10 + Math.random() * 15) * pipValue;
  
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
    reliability_score: Math.floor(Math.random() * 4) + 7,
    entry_time: new Date().toISOString(),
    status: 'ACTIVE'
  };
}

export default function handler(req, res) {
  // %30 şans ile yeni sinyal
  if (Math.random() < 0.3) {
    const symbols = ['XAUUSD', 'GBPJPY', 'EURUSD', 'GBPUSD', 'EURCAD'];
    const randomSymbol = symbols[Math.floor(Math.random() * symbols.length)];
    
    const existingIndex = signalCache.findIndex(s => s.symbol === randomSymbol);
    const newSignal = generateTradingSignal(randomSymbol);
    
    if (existingIndex >= 0) {
      signalCache[existingIndex] = newSignal;
    } else {
      signalCache.push(newSignal);
    }
    
    if (signalCache.length > 3) {
      signalCache = signalCache.slice(-3);
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
    signals: signalCache,
    timestamp: new Date().toISOString(),
    total_active: signalCache.length
  });
} 