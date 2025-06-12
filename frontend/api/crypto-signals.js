// Vercel Serverless Function: Crypto Signals
let cryptoSignalCache = [];

// Binance'den gerçek mum verilerini çek
async function fetchBinanceCandleData(symbol, interval = '15m', limit = 100) {
  try {
    const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`;
    const response = await fetch(url);
    
    if (!response.ok) throw new Error('Binance klines API failed');
    
    const klines = await response.json();
    
    const candles = klines.map(kline => ({
      time: kline[0],
      open: parseFloat(kline[1]),
      high: parseFloat(kline[2]),
      low: parseFloat(kline[3]),
      close: parseFloat(kline[4]),
      volume: parseFloat(kline[5])
    }));
    
    return candles;
  } catch (error) {
    console.warn(`Failed to fetch ${symbol} candles from Binance:`, error.message);
    return null;
  }
}

// Kripto KRO Analizi
function analyzeCryptoKRO(candles, currentPrice) {
  if (!candles || candles.length < 50) return null;
  
  const recent = candles.slice(-20);
  const older = candles.slice(-50, -20);
  
  // Direnç/Destek belirleme
  const highs = older.map(c => c.high);
  const lows = older.map(c => c.low);
  
  const resistance = Math.max(...highs);
  const support = Math.min(...lows);
  
  // Kırılım kontrolü
  const lastCandles = recent.slice(-5);
  const breakoutUp = lastCandles.some(c => c.close > resistance);
  const breakoutDown = lastCandles.some(c => c.close < support);
  
  if (!breakoutUp && !breakoutDown) return null;
  
  // Volume onayı (kripto için önemli)
  const avgVolume = older.reduce((sum, c) => sum + c.volume, 0) / older.length;
  const recentVolume = recent.slice(-3).reduce((sum, c) => sum + c.volume, 0) / 3;
  
  if (recentVolume < avgVolume * 1.2) return null; // Volume yetersiz
  
  // Retest kontrolü
  const lastPrice = recent[recent.length - 1].close;
  const retestUp = breakoutUp && lastPrice > resistance * 0.995;
  const retestDown = breakoutDown && lastPrice < support * 1.005;
  
  if (!retestUp && !retestDown) return null;
  
  if (retestUp) {
    const entry = currentPrice;
    const distance = entry - support;
    const tp = entry + distance * 1.5; // Kripto'da daha agresif TP
    const sl = support * 0.99;
    
    return {
      signal_type: 'BUY',
      ideal_entry: entry,
      take_profit: tp,
      stop_loss: sl,
      reliability_score: Math.min(10, Math.floor(7 + (recentVolume / avgVolume))),
      reason: 'Crypto resistance breakout + volume surge'
    };
  }
  
  if (retestDown) {
    const entry = currentPrice;
    const distance = resistance - entry;
    const tp = entry - distance * 1.5;
    const sl = resistance * 1.01;
    
    return {
      signal_type: 'SAT',
      ideal_entry: entry,
      take_profit: tp,
      stop_loss: sl,
      reliability_score: Math.min(10, Math.floor(7 + (recentVolume / avgVolume))),
      reason: 'Crypto support breakdown + volume surge'
    };
  }
  
  return null;
}

// Kripto LMO Analizi
function analyzeCryptoLMO(candles, currentPrice) {
  if (!candles || candles.length < 30) return null;
  
  const recent = candles.slice(-15);
  
  // Wick-based likidite seviyeleri
  const liquidityLevels = [];
  
  for (let i = 2; i < recent.length - 2; i++) {
    const candle = recent[i];
    const bodySize = Math.abs(candle.close - candle.open);
    const totalSize = candle.high - candle.low;
    
    // Büyük wick'li mumlar (kripto'da önemli)
    if (bodySize / totalSize < 0.4) { // Body %40'tan küçük
      if (candle.high - Math.max(candle.open, candle.close) > bodySize) {
        liquidityLevels.push({ level: candle.high, type: 'high', volume: candle.volume });
      }
      if (Math.min(candle.open, candle.close) - candle.low > bodySize) {
        liquidityLevels.push({ level: candle.low, type: 'low', volume: candle.volume });
      }
    }
  }
  
  if (liquidityLevels.length === 0) return null;
  
  // En yüksek volumlu likidite seviyesini bul
  liquidityLevels.sort((a, b) => b.volume - a.volume);
  const mainLiquidity = liquidityLevels[0];
  
  // Likidite süpürme
  const lastCandle = recent[recent.length - 1];
  let isSweep = false;
  
  if (mainLiquidity.type === 'high') {
    isSweep = lastCandle.high > mainLiquidity.level && lastCandle.close < mainLiquidity.level * 0.998;
  } else {
    isSweep = lastCandle.low < mainLiquidity.level && lastCandle.close > mainLiquidity.level * 1.002;
  }
  
  if (!isSweep) return null;
  
  // Crypto-specific confirmation: RSI divergence simulation
  const prices = recent.map(c => c.close);
  const priceChange = (prices[prices.length - 1] - prices[0]) / prices[0];
  const volumeChange = (lastCandle.volume - recent[0].volume) / recent[0].volume;
  
  // Volume ve fiyat uyumsuzluğu
  if (Math.abs(priceChange) < 0.02 && Math.abs(volumeChange) < 0.5) return null;
  
  if (mainLiquidity.type === 'high' && lastCandle.close < lastCandle.open) {
    const entry = currentPrice;
    const distance = mainLiquidity.level - entry;
    const tp = entry - distance * 2.0; // Kripto'da büyük hedefler
    const sl = mainLiquidity.level * 1.005;
    
    return {
      signal_type: 'SAT',
      ideal_entry: entry,
      take_profit: tp,
      stop_loss: sl,
      reliability_score: 8,
      reason: 'Crypto high liquidity sweep + bearish volume divergence'
    };
  }
  
  if (mainLiquidity.type === 'low' && lastCandle.close > lastCandle.open) {
    const entry = currentPrice;
    const distance = entry - mainLiquidity.level;
    const tp = entry + distance * 2.0;
    const sl = mainLiquidity.level * 0.995;
    
    return {
      signal_type: 'BUY',
      ideal_entry: entry,
      take_profit: tp,
      stop_loss: sl,
      reliability_score: 8,
      reason: 'Crypto low liquidity sweep + bullish volume divergence'
    };
  }
  
  return null;
}

async function generateCryptoSignal(symbol) {
  try {
    // 1. Binance'den gerçek mum verilerini çek
    const candles = await fetchBinanceCandleData(symbol, '15m', 100);
    if (!candles) return null;
    
    // 2. Güncel fiyat (son mum close)
    const currentPrice = candles[candles.length - 1].close;
    
    // 3. Her iki stratejiyi analiz et
    const kroSignal = analyzeCryptoKRO(candles, currentPrice);
    const lmoSignal = analyzeCryptoLMO(candles, currentPrice);
    
    // 4. En iyi sinyali seç
    let bestSignal = null;
    
    if (kroSignal && lmoSignal) {
      if (kroSignal.signal_type === lmoSignal.signal_type) {
        bestSignal = {
          ...kroSignal,
          strategy: 'Crypto KRO+LMO',
          reliability_score: Math.min(10, kroSignal.reliability_score + 1),
          reason: `${kroSignal.reason} + ${lmoSignal.reason}`
        };
      } else {
        bestSignal = kroSignal.reliability_score >= lmoSignal.reliability_score ? 
          { ...kroSignal, strategy: 'Crypto KRO' } : 
          { ...lmoSignal, strategy: 'Crypto LMO' };
      }
    } else if (kroSignal) {
      bestSignal = { ...kroSignal, strategy: 'Crypto KRO' };
    } else if (lmoSignal) {
      bestSignal = { ...lmoSignal, strategy: 'Crypto LMO' };
    }
    
    if (!bestSignal) return null;
    
    // 5. Fiyat formatı (kripto için)
    const getDecimals = (price) => {
      if (price >= 1000) return 2;
      if (price >= 1) return 4;
      return 6;
    };
    
    const decimals = getDecimals(bestSignal.ideal_entry);
    
    return {
      symbol,
      strategy: bestSignal.strategy,
      signal_type: bestSignal.signal_type,
      timeframe: '15m',
      ideal_entry: parseFloat(bestSignal.ideal_entry.toFixed(decimals)),
      take_profit: parseFloat(bestSignal.take_profit.toFixed(decimals)),
      stop_loss: parseFloat(bestSignal.stop_loss.toFixed(decimals)),
      reliability_score: bestSignal.reliability_score,
      entry_time: new Date().toISOString(),
      status: 'ACTIVE',
      analysis: bestSignal.reason
    };
    
  } catch (error) {
    console.error(`Failed to generate crypto signal for ${symbol}:`, error.message);
    return null;
  }
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