// Vercel Serverless Function: Trade Statistics with Persistent Data
let persistentStats = {
  total_trades: 89,          // Profesyonel başlangıç
  winning_trades: 64,        // %72 başarı oranı
  losing_trades: 25,
  total_pips: 1847.5,       // Pozitif pip kazanç
  session_start: new Date().toISOString(),
  trades_history: [
    {
      symbol: 'XAUUSD',
      signal_type: 'SAT', 
      entry_time: new Date(Date.now() - 3600000).toISOString(),
      result: 'profit',
      pips: 42.3
    },
    {
      symbol: 'GBPJPY',
      signal_type: 'BUY',
      entry_time: new Date(Date.now() - 7200000).toISOString(), 
      result: 'profit',
      pips: 38.7
    },
    {
      symbol: 'EURUSD',
      signal_type: 'SAT',
      entry_time: new Date(Date.now() - 10800000).toISOString(),
      result: 'loss',
      pips: -22.1
    }
  ]
};

// Rastgele trade üretme fonksiyonu
function generateRandomTrade() {
  const symbols = ['XAUUSD', 'GBPJPY', 'EURCAD', 'EURUSD', 'GBPUSD'];
  const types = ['BUY', 'SAT'];
  const isWin = Math.random() > 0.28; // %72 kazanç oranı
  
  const symbol = symbols[Math.floor(Math.random() * symbols.length)];
  const signal_type = types[Math.floor(Math.random() * types.length)];
  const pips = isWin ? 
    +(15 + Math.random() * 35).toFixed(1) : // 15-50 pip kazanç
    -(10 + Math.random() * 25).toFixed(1);  // 10-35 pip kayıp
  
  return {
    symbol,
    signal_type,
    entry_time: new Date().toISOString(),
    result: isWin ? 'profit' : 'loss',
    pips
  };
}

export default function handler(req, res) {
  // %15 şans ile yeni trade ekle (sürekli büyüyen veri)
  if (Math.random() < 0.15 && persistentStats.total_trades < 200) {
    const newTrade = generateRandomTrade();
    
    persistentStats.total_trades++;
    persistentStats.total_pips += newTrade.pips;
    
    if (newTrade.result === 'profit') {
      persistentStats.winning_trades++;
    } else {
      persistentStats.losing_trades++;
    }
    
    persistentStats.trades_history.unshift(newTrade);
    
    // Sadece son 50 trade'i tut
    if (persistentStats.trades_history.length > 50) {
      persistentStats.trades_history = persistentStats.trades_history.slice(0, 50);
    }
  }
  
  // Başarı oranını hesapla
  const win_rate = persistentStats.total_trades > 0 ? 
    (persistentStats.winning_trades / persistentStats.total_trades * 100) : 0;
  
  const general_statistics = {
    total_trades: persistentStats.total_trades,
    winning_trades: persistentStats.winning_trades,
    losing_trades: persistentStats.losing_trades,
    win_rate: parseFloat(win_rate.toFixed(1)),
    total_pips: parseFloat(persistentStats.total_pips.toFixed(1)),
    average_rr: 2.1
  };
  
  // Son 5 trade'i recent_history formatında
  const recent_history = persistentStats.trades_history.slice(0, 5).map(trade => ({
    date: new Date(trade.entry_time).toLocaleDateString('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }),
    symbol: trade.symbol,
    signal_type: trade.signal_type,
    pips: trade.pips > 0 ? `+${trade.pips}` : `${trade.pips}`,
    result: trade.result === 'profit' ? 'TP' : 'SL'
  }));
  
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  res.status(200).json({
    general_statistics,
    recent_history,
    recent_trades: persistentStats.trades_history.slice(0, 10),
    session_info: {
      session_start: persistentStats.session_start,
      runtime_minutes: Math.floor((new Date() - new Date(persistentStats.session_start)) / 60000)
    },
    timestamp: new Date().toISOString()
  });
} 