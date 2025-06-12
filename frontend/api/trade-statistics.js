// Vercel Serverless Function: Trade Statistics
export default function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  res.status(200).json({
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
} 