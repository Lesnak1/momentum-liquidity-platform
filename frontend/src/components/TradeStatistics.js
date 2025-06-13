import React from 'react';
import './TradeStatistics.css';

const TradeStatistics = ({ 
    statistics = {
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        win_rate: 0,
        total_pips: 0
    },
    recentTrades = []
}) => {
    
    // Win rate rengini belirle
    const getWinRateColor = () => {
        if (statistics.win_rate >= 70) return '#27ae60';
        if (statistics.win_rate >= 50) return '#f39c12';
        return '#e74c3c';
    };

    // Pips rengini belirle
    const getPipsColor = () => {
        return statistics.total_pips >= 0 ? '#27ae60' : '#e74c3c';
    };

    return (
        <div className="trade-statistics">
            
            {/* Ana İstatistikler */}
            <div className="stats-grid">
                
                {/* Win/Loss Kartı */}
                <div className="stat-card primary">
                    <div className="stat-header">
                        <h3>İşlem Sonuçları</h3>
                        <div className="stat-icon">📊</div>
                    </div>
                    <div className="win-loss-display">
                        <div className="win-section">
                            <div className="count">{statistics.winning_trades}</div>
                            <div className="label">✅ Doğru</div>
                        </div>
                        <div className="vs-divider">vs</div>
                        <div className="loss-section">
                            <div className="count">{statistics.losing_trades}</div>
                            <div className="label">❌ Yanlış</div>
                        </div>
                    </div>
                    <div className="win-rate" style={{color: getWinRateColor()}}>
                        %{statistics.win_rate.toFixed(1)} Başarı Oranı
                    </div>
                </div>

                {/* Toplam Pip Kartı */}
                <div className="stat-card secondary">
                    <div className="stat-header">
                        <h3>Toplam Kazanç</h3>
                        <div className="stat-icon">💰</div>
                    </div>
                    <div className="pip-display" style={{color: getPipsColor()}}>
                        <div className="pip-count">
                            {statistics.total_pips > 0 ? '+' : ''}{statistics.total_pips.toFixed(1)}
                        </div>
                        <div className="pip-label">PİP</div>
                    </div>
                    <div className="pip-trend">
                        {statistics.total_pips >= 0 ? '📈 Pozitif Trend' : '📉 Negatif Trend'}
                    </div>
                </div>

                {/* Toplam İşlem Kartı */}
                <div className="stat-card accent">
                    <div className="stat-header">
                        <h3>Platform Özeti</h3>
                        <div className="stat-icon">🎯</div>
                    </div>
                    <div className="total-trades">
                        <div className="trade-count">{statistics.total_trades}</div>
                        <div className="trade-label">Toplam İşlem</div>
                    </div>
                    <div className="platform-status">
                        <span className="status-dot"></span>
                        Sistem Aktif
                    </div>
                </div>

            </div>



            {/* Performance Badge */}
            <div className="performance-badge">
                <div className="badge-content">
                    <span className="badge-text">Platform Performansı</span>
                    <div className="performance-indicators">
                        <div className="indicator">
                            <span className="indicator-label">Güvenilirlik</span>
                            <span className="indicator-value">⭐ Yüksek</span>
                        </div>
                        <div className="indicator">
                            <span className="indicator-label">Hız</span>
                            <span className="indicator-value">⚡ Real-time</span>
                        </div>
                        <div className="indicator">
                            <span className="indicator-label">Analiz</span>
                            <span className="indicator-value">🧠 AI Destekli</span>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    );
};

export default TradeStatistics; 