import React from 'react';
import './CryptoCard.css';

const CryptoCard = ({ symbol, data, signal }) => {
  const formatPrice = (price) => {
    if (price < 1) {
      return `$${price.toFixed(4)}`;
    } else if (price < 100) {
      return `$${price.toFixed(2)}`;
    } else {
      return `$${price.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}`;
    }
  };

  const formatVolume = (volume) => {
    if (volume >= 1e12) return `$${(volume / 1e12).toFixed(1)}T`;
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(1)}B`;
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(1)}M`;
    if (volume >= 1e3) return `$${(volume / 1e3).toFixed(1)}K`;
    return `$${volume}`;
  };

  const formatMarketCap = (marketCap) => {
    if (marketCap >= 1e12) return `$${(marketCap / 1e12).toFixed(1)}T`;
    if (marketCap >= 1e9) return `$${(marketCap / 1e9).toFixed(1)}B`;
    if (marketCap >= 1e6) return `$${(marketCap / 1e6).toFixed(1)}M`;
    return `$${marketCap.toLocaleString()}`;
  };

  const getRiskLevel = (strategy) => {
    if (strategy === 'Crypto KRO') return 'HIGH';
    if (strategy === 'Crypto LMO') return 'MEDIUM';
    return 'UNKNOWN';
  };

  const getSignalIcon = (signalType) => {
    return signalType === 'BUY' ? '📈' : '📉';
  };

  const tokenName = data.name || symbol.split('/')[0];
  const changePercent = data.change_24h || 0;
  const isPositive = changePercent >= 0;

  return (
    <div className={`crypto-card ${signal ? 'has-signal' : ''}`}>
      <div className="crypto-header">
        <div className="crypto-title">
          <h3 className="crypto-symbol">{symbol}</h3>
          <span className="crypto-name">{tokenName}</span>
        </div>
        <div className="crypto-status">
          <span className="data-status live">🟢 CANLI</span>
          {signal && (
            <span className={`signal-badge ${signal.signal_type.toLowerCase()}`}>
              {getSignalIcon(signal.signal_type)} SİNYAL
            </span>
          )}
        </div>
      </div>

      <div className="crypto-price-info">
        <div className="current-price">
          {formatPrice(data.price)}
        </div>
        <div className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? '↗' : '↘'} {Math.abs(changePercent).toFixed(2)}% (24h)
        </div>
      </div>

      <div className="crypto-metrics">
        <div className="metric">
          <span className="metric-label">24h Hacim</span>
          <span className="metric-value">{formatVolume(data.volume_24h)}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Piyasa Değeri</span>
          <span className="metric-value">{formatMarketCap(data.market_cap)}</span>
        </div>
      </div>

      {signal && (
        <div className="crypto-signal-section">
          <div className="signal-header">
            <span className="strategy-badge">{signal.strategy}</span>
            <span className={`risk-level ${getRiskLevel(signal.strategy).toLowerCase()}`}>
              {getRiskLevel(signal.strategy)}
            </span>
          </div>
          
          <div className="signal-details">
            <div className="signal-type">
              <span className="label">Sinyal:</span>
              <span className={`value ${signal.signal_type.toLowerCase()}`}>
                {signal.signal_type === 'BUY' ? '🚀 AL' : '🔻 SAT'}
              </span>
            </div>
            
            <div className="price-levels">
              <div className="level-group">
                <div className="level entry">
                  <span>Giriş: {formatPrice(signal.entry_price)}</span>
                </div>
                <div className="level tp">
                  <span>TP: {formatPrice(signal.take_profit)}</span>
                </div>
                <div className="level sl">
                  <span>SL: {formatPrice(signal.stop_loss)}</span>
                </div>
              </div>
              <div className="risk-reward">
                <span>R/R: {signal.risk_reward || 'N/A'}</span>
              </div>
            </div>
          </div>

          <div className="signal-quality">
            <div className="reliability">
              <span className="reliability-label">Güvenilirlik:</span>
              <div className="reliability-bar">
                <div 
                  className="reliability-fill"
                  style={{ width: `${(signal.reliability_score / 10) * 100}%` }}
                ></div>
              </div>
              <span className="reliability-score">{signal.reliability_score}/10</span>
            </div>
          </div>

          <div className="signal-analysis">
            <p className="analysis-text">{signal.analysis}</p>
            <div className="signal-meta">
              <span className="timeframe">{signal.timeframe}</span>
              <span className="timestamp">
                {new Date(signal.timestamp || Date.now()).toLocaleTimeString('tr-TR')}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CryptoCard; 