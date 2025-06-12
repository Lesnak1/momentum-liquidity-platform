// Vercel Serverless Function: Real-time Crypto Prices from Binance API
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // Binance API'den gerçek anlık fiyatları çek
    const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT', 'MATICUSDT', 'DOTUSDT'];
    const binanceUrl = `https://api.binance.com/api/v3/ticker/price`;
    
    const response = await fetch(binanceUrl);
    
    if (!response.ok) {
      throw new Error(`Binance API error: ${response.status}`);
    }
    
    const allPrices = await response.json();
    
    // İhtiyacımız olan symbolları filtrele
    const cryptoPrices = {};
    allPrices.forEach(ticker => {
      if (symbols.includes(ticker.symbol)) {
        cryptoPrices[ticker.symbol] = parseFloat(ticker.price);
      }
    });
    
    // Eksik olan symbollar için ikincil çağrı
    const missingSymbols = symbols.filter(symbol => !cryptoPrices[symbol]);
    if (missingSymbols.length > 0) {
      for (const symbol of missingSymbols) {
        try {
          const singleResponse = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${symbol}`);
          if (singleResponse.ok) {
            const singleData = await singleResponse.json();
            cryptoPrices[symbol] = parseFloat(singleData.price);
          }
        } catch (error) {
          console.warn(`Failed to fetch ${symbol}:`, error.message);
        }
      }
    }
    
    // 24h fiyat değişimi için ek API çağrısı
    const statsResponse = await fetch(`https://api.binance.com/api/v3/ticker/24hr`);
    const statsData = await statsResponse.json();
    
    const enrichedPrices = {};
    symbols.forEach(symbol => {
      const price = cryptoPrices[symbol];
      const stats = statsData.find(s => s.symbol === symbol);
      
      if (price) {
        enrichedPrices[symbol] = {
          price: price,
          change_24h: stats ? parseFloat(stats.priceChangePercent) : 0,
          volume_24h: stats ? parseFloat(stats.volume) : 0,
          high_24h: stats ? parseFloat(stats.highPrice) : price,
          low_24h: stats ? parseFloat(stats.lowPrice) : price
        };
      }
    });
    
    res.status(200).json({
      prices: enrichedPrices,
      api_status: 'live',
      source: 'Binance API',
      timestamp: new Date().toISOString(),
      symbols_count: Object.keys(enrichedPrices).length
    });
    
  } catch (error) {
    console.error('Binance API Error:', error);
    
    // Fallback: CoinGecko API
    try {
      const coinGeckoUrl = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,cardano,solana,dogecoin,polygon,polkadot&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true';
      const fallbackResponse = await fetch(coinGeckoUrl);
      
      if (!fallbackResponse.ok) {
        throw new Error(`CoinGecko API error: ${fallbackResponse.status}`);
      }
      
      const coinGeckoData = await fallbackResponse.json();
      
      const cryptoPrices = {
        'BTCUSDT': {
          price: coinGeckoData.bitcoin?.usd || 0,
          change_24h: coinGeckoData.bitcoin?.usd_24h_change || 0,
          volume_24h: coinGeckoData.bitcoin?.usd_24h_vol || 0
        },
        'ETHUSDT': {
          price: coinGeckoData.ethereum?.usd || 0,
          change_24h: coinGeckoData.ethereum?.usd_24h_change || 0,
          volume_24h: coinGeckoData.ethereum?.usd_24h_vol || 0
        },
        'BNBUSDT': {
          price: coinGeckoData.binancecoin?.usd || 0,
          change_24h: coinGeckoData.binancecoin?.usd_24h_change || 0,
          volume_24h: coinGeckoData.binancecoin?.usd_24h_vol || 0
        },
        'ADAUSDT': {
          price: coinGeckoData.cardano?.usd || 0,
          change_24h: coinGeckoData.cardano?.usd_24h_change || 0,
          volume_24h: coinGeckoData.cardano?.usd_24h_vol || 0
        },
        'SOLUSDT': {
          price: coinGeckoData.solana?.usd || 0,
          change_24h: coinGeckoData.solana?.usd_24h_change || 0,
          volume_24h: coinGeckoData.solana?.usd_24h_vol || 0
        },
        'DOGEUSDT': {
          price: coinGeckoData.dogecoin?.usd || 0,
          change_24h: coinGeckoData.dogecoin?.usd_24h_change || 0,
          volume_24h: coinGeckoData.dogecoin?.usd_24h_vol || 0
        },
        'MATICUSDT': {
          price: coinGeckoData.polygon?.usd || 0,
          change_24h: coinGeckoData.polygon?.usd_24h_change || 0,
          volume_24h: coinGeckoData.polygon?.usd_24h_vol || 0
        },
        'DOTUSDT': {
          price: coinGeckoData.polkadot?.usd || 0,
          change_24h: coinGeckoData.polkadot?.usd_24h_change || 0,
          volume_24h: coinGeckoData.polkadot?.usd_24h_vol || 0
        }
      };
      
      res.status(200).json({
        prices: cryptoPrices,
        api_status: 'fallback',
        source: 'CoinGecko API',
        timestamp: new Date().toISOString()
      });
      
    } catch (fallbackError) {
      console.error('Fallback API Error:', fallbackError);
      
      res.status(500).json({
        error: 'Failed to fetch real-time crypto prices',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
} 