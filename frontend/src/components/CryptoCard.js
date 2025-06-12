import React from 'react';
import './CryptoCard.css';

const CryptoCard = ({ symbol, data, signal, statistics }) => {
  // Default değerler
  const currentPrice = data?.price || 0;
  const change24h = data?.change_24h || 0;
  const volume24h = data?.volume_24h || 0;
  const cleanSymbol = symbol?.replace('/USD', '') || 'BTC';
  
  // KRİTİK: Token bazlı başarı oranları
  const tokenStats = statistics || {
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    win_rate: 0.0
  };

  // Sinyal güvenilirlik seviyesi
  const getReliabilityLevel = (strategy) => {
    if (strategy === 'Crypto KRO') return 'HIGH';
    if (strategy === 'Crypto LMO') return 'MEDIUM';
    return 'LOW';
  };



  // Fiyat formatla
  const formatPrice = (price) => {
    if (!price) return '0.00';
    if (price >= 1000) return price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    if (price >= 1) return price.toFixed(4);
    return price.toFixed(6);
  };

  // Risk/Reward hesapla
  const calculateRiskReward = () => {
    if (!signal || !signal.take_profit || !signal.stop_loss || !signal.ideal_entry) return 'N/A';
    
    const entry = signal.ideal_entry;
    const tp = signal.take_profit;
    const sl = signal.stop_loss;
    
    const reward = Math.abs(tp - entry);
    const risk = Math.abs(entry - sl);
    
    if (risk === 0) return 'N/A';
    return (reward / risk).toFixed(1);
  };

  return (
    <div className={`crypto-card ${signal ? 'has-signal' : ''}`}>
      
      {/* Kripto Header */}
      <div className="crypto-header">
        <div className="symbol-info">
          <h3 className="crypto-symbol">{cleanSymbol}<span className="pair">/USD</span></h3>
          <div className="live-indicator">
            <span className="live-dot"></span>
            Binance Live
          </div>
        </div>
        
        <div className="price-change">
          <div className={`price-change ${change24h >= 0 ? 'positive' : 'negative'}`}>
            {change24h >= 0 ? '↗' : '↘'} {Math.abs(change24h).toFixed(2)}% (24h)
          </div>
        </div>
      </div>

      {/* Fiyat */}
      <div className="current-price-section">
        <div className="price">${formatPrice(currentPrice)}</div>
        <div className="price-label">Anlık Fiyat</div>
      </div>

      {/* Sinyal Bölümü */}
      {signal ? (
        <div className="signal-section active">
          <div className="signal-header">
            <div className={`signal-type ${signal.signal_type.toLowerCase()}`}>
              {signal.signal_type === 'BUY' ? '🚀 AL' : '🔻 SAT'}
            </div>
            <div className={`reliability-badge ${getReliabilityLevel(signal.strategy).toLowerCase()}`}>
              GÜVENİLİRLİK {signal.reliability_score || 8}/10
            </div>
          </div>
          
          <div className="signal-details">
            <div className="strategy-info">
              Strateji: {
                signal.strategy === 'Crypto KRO+LMO' ? 'Crypto KRO+LMO Birleşik Konfirmasyon' :
                signal.strategy === 'Crypto KRO (Strong)' ? 'Güçlü Crypto KRO' :
                signal.strategy === 'Crypto LMO (Strong)' ? 'Güçlü Crypto LMO' :
                signal.strategy === 'Crypto KRO' ? 'Kripto Kırılım + Retest + Onay' : 
                'Kripto Likidite Alımı + Mum Onayı'
              } ({signal.timeframe || '1h'})
            </div>
            
            <div className="price-levels">
              <div className="level-row">
                <span className="level-label">Giriş Seviyesi:</span>
                <span className="level-value">${formatPrice(signal.ideal_entry)}</span>
              </div>
              <div className="level-row">
                <span className="level-label">Take Profit:</span>
                <span className="level-value success">${formatPrice(signal.take_profit)} (RR: {calculateRiskReward()})</span>
              </div>
              <div className="level-row">
                <span className="level-label">Stop Loss:</span>
                <span className="level-value danger">${formatPrice(signal.stop_loss)}</span>
              </div>
            </div>

            <div className="signal-status">
              <div className="status-badge active-signal">
                🔥 AKTİF SİNYAL
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="signal-section waiting">
          <div className="waiting-signal">
            <div className="waiting-text">SİNYAL ARANIYOR</div>
            <div className="waiting-description">
              Motor yeni kurulum fırsatları analiz ediyor.
            </div>
          </div>
          <div className="no-signal-info">
            Henüz işlem yok
          </div>
        </div>
      )}

      {/* KRİTİK: İşlem Başarı Oranları */}
      <div className="stats-section">
        <div className="performance-stats">
          <div className="stat-item performance">
            <span className="stat-label">Başarı Oranı:</span>
            <span className={`stat-value ${tokenStats.win_rate >= 70 ? 'success' : tokenStats.win_rate >= 50 ? 'warning' : 'danger'}`}>
              %{tokenStats.win_rate.toFixed(1)}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Toplam İşlem:</span>
            <span className="stat-value">{tokenStats.total_trades}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">✅ Doğru / ❌ Yanlış:</span>
            <span className="stat-value">{tokenStats.winning_trades} / {tokenStats.losing_trades}</span>
          </div>
        </div>
        
        <div className="market-stats">
          <div className="stat-item">
            <span className="stat-label">24s Hacim:</span>
            <span className="stat-value">
              {volume24h >= 1e9 ? `$${(volume24h / 1e9).toFixed(1)}B` : 
               volume24h >= 1e6 ? `$${(volume24h / 1e6).toFixed(1)}M` : 
               `$${(volume24h / 1e3).toFixed(1)}K`}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Kaynak:</span>
            <span className="stat-value">Binance API</span>
          </div>
        </div>
      </div>

      {/* WebSocket Status */}
      <div className="websocket-status">
        <div className="status-indicator live">
          <span className="status-dot"></span>
          <span className="status-text">WebSocket Aktif</span>
        </div>
        <div className="data-source">
          📡 Binance Real-time
        </div>
      </div>

    </div>
  );
};

export default CryptoCard; 