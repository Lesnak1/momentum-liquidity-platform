import React from 'react';
import './TradingCard.css';

const TradingCard = ({ 
    symbol = "GBPJPY", 
    currentPrice = 198.450,
    signal = null,
    pastTrades = []
}) => {
    
    // Sinyal durumunu belirle
    const getSignalStatus = () => {
        if (!signal) return "SİNYAL ARANIYOR";
        if (signal.status === 'ACTIVE') return "AKTİF SİNYAL";
        if (signal.status === 'NEW') return "🆕 YENİ FIRSAT TESPİT EDİLDİ!";
        if (signal.result === 'TP') return "TP ALINDI - DOĞRU";
        if (signal.result === 'SL') return "STOP OLDU - YANLIŞ";
        return "SİNYAL ARANIYOR";
    };

    // Güvenilirlik rengini belirle
    const getReliabilityColor = () => {
        if (!signal) return "#6c757d";
        if (signal.reliability_score >= 8) return "#28a745"; // Yeşil
        if (signal.reliability_score >= 6) return "#ffc107"; // Sarı
        return "#dc3545"; // Kırmızı
    };

    // Sinyal tipine göre arka plan rengini belirle
    const getSignalBackgroundColor = () => {
        if (!signal) return "#f8f9fa";
        if (signal.signal_type === 'BUY') return "#d4edda"; // Açık yeşil
        if (signal.signal_type === 'SELL') return "#f8d7da"; // Açık kırmızı
        return "#f8f9fa";
    };

    // Risk/Reward hesapla
    const calculateRR = () => {
        if (!signal) return "0";
        const risk = Math.abs(signal.entry_price - signal.stop_loss);
        const reward = Math.abs(signal.take_profit - signal.entry_price);
        return (reward / risk).toFixed(1);
    };

    return (
        <div className="trading-card" style={{backgroundColor: getSignalBackgroundColor()}}>
            
            {/* Sinyal Başlığı */}
            <div className="signal-header" style={{backgroundColor: getReliabilityColor()}}>
                <div className="signal-status">
                    {signal ? `${signal.signal_type} SİNYALİ` : "SİNYAL ARANIYOR"}
                </div>
                {signal && (
                    <div className="reliability-score">
                        GÜVENİLİRLİK: {signal.reliability_score}/10
                    </div>
                )}
            </div>

            {/* Parite Bilgileri */}
            <div className="pair-info">
                <div className="pair-name">{symbol}</div>
                <div className="current-price">{currentPrice} (Anlık Fiyat)</div>
                {signal && (
                    <div className="strategy-info">
                        Strateji: {
                            signal.strategy === 'KRO+LMO' ? 'KRO+LMO Birleşik Konfirmasyon' :
                            signal.strategy === 'KRO (Strong)' ? 'Güçlü KRO' :
                            signal.strategy === 'LMO (Strong)' ? 'Güçlü LMO' :
                            signal.strategy === 'KRO' ? 'Kırılım + Retest + Onay' : 
                            'Likidite Alımı + Mum Onayı'
                        } ({signal.timeframe})
                    </div>
                )}
            </div>

            <div className="divider"></div>

            {/* Aktif Sinyal Bilgileri */}
            {signal && (signal.status === 'ACTIVE' || signal.status === 'NEW') && (
                <div className="signal-details">
                    <div className="price-levels">
                        <div className="price-row">
                            <span className="label">Giriş Seviyesi:</span>
                            <span className="value">{signal.entry_price.toFixed(3)}</span>
                        </div>
                        <div className="price-row">
                            <span className="label">Take Profit:</span>
                            <span className="value green">{signal.take_profit.toFixed(3)} (RR: {calculateRR()})</span>
                        </div>
                        <div className="price-row">
                            <span className="label">Stop Loss:</span>
                            <span className="value red">{signal.stop_loss.toFixed(3)}</span>
                        </div>
                    </div>
                    
                    <div className={`signal-badge ${signal.status === 'NEW' ? 'new-signal' : 'active-signal'}`}>
                        {signal.status === 'NEW' ? '🆕 YENİ FIRSAT' : 'AKTİF SİNYAL'}
                    </div>
                </div>
            )}

            {/* Sinyal Sonucu */}
            {signal && signal.status !== 'ACTIVE' && (
                <div className="signal-result">
                    <div className={`result-badge ${signal.result === 'TP' ? 'success' : 'failure'}`}>
                        {getSignalStatus()}
                    </div>
                </div>
            )}

            {/* Sinyal Aranıyor */}
            {!signal && (
                <div className="no-signal">
                    <div className="searching-badge">
                        SİNYAL ARANIYOR...
                    </div>
                    <p>Motor yeni kurulum fırsatları analiz ediyor.</p>
                </div>
            )}

            <div className="divider"></div>

            {/* Geçmiş İşlemler */}
            <div className="past-trades">
                <div className="section-title">GEÇMİŞ İŞLEMLER:</div>
                {pastTrades.length > 0 ? (
                    <div className="trades-list">
                        {pastTrades.slice(0, 3).map((trade, index) => (
                            <div key={index} className="trade-row">
                                <span className="trade-date">{trade.date}</span>
                                <span className={`trade-result ${trade.result === 'TP' ? 'green' : 'red'}`}>
                                    {trade.signal_type} → {trade.result === 'TP' ? 'DOĞRU (TP)' : 'YANLIŞ (SL)'}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="no-trades">Henüz işlem yok</div>
                )}
            </div>

        </div>
    );
};

export default TradingCard; 