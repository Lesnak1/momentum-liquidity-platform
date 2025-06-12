import React, { useState, useEffect } from 'react';
import TradingCard from './components/TradingCard';
import CryptoCard from './components/CryptoCard';
import TradeStatistics from './components/TradeStatistics';
import './App.css';

function App() {
  const [tradingData, setTradingData] = useState({});

  const [connectionStatus, setConnectionStatus] = useState('bağlanıyor...');
  const [lastUpdate, setLastUpdate] = useState('');
  const [cryptoData, setCryptoData] = useState({});
  const [cryptoStatus, setCryptoStatus] = useState('yükleniyor...');
  const [cryptoSignals, setCryptoSignals] = useState([]);
  const [tradeStatistics, setTradeStatistics] = useState({
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    win_rate: 0,
    total_pips: 0
  });
  const [recentTrades, setRecentTrades] = useState([]);
  // KRİTİK: Symbol bazlı istatistikler
  const [symbolStatistics, setSymbolStatistics] = useState({});

  // Backend'e bağlan ve verileri çek
  useEffect(() => {
    // İlk veri yükleme
    loadInitialData();
    
    // Her 15 saniyede fiyatları güncelle
    const priceInterval = setInterval(updatePrices, 15000);
    
    // Her 30 saniyede sinyalleri güncelle
    const signalInterval = setInterval(updateSignals, 30000);
    
    // Her 5 saniyede kripto fiyatları güncelle (WebSocket)
    const cryptoInterval = setInterval(updateCryptoPrices, 5000);
    
    // Her 30 saniyede trade istatistiklerini güncelle
    const statsInterval = setInterval(updateTradeStatistics, 30000);

    return () => {
      clearInterval(priceInterval);
      clearInterval(signalInterval);
      clearInterval(cryptoInterval);
      clearInterval(statsInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadInitialData = async () => {
    try {
      // Backend'den gerçek forex verilerini yükle
      const forexResponse = await fetch('http://localhost:8000/market-data');
      const forexData = await forexResponse.json();
      
      // Forex verilerini initialize et
      if (forexData.forex) {
        const initialForexData = {};
        Object.entries(forexData.forex).forEach(([symbol, priceInfo]) => {
          initialForexData[symbol] = {
            currentPrice: priceInfo.price,
            signal: null,
            pastTrades: []
          };
        });
        setTradingData(initialForexData);
      }
      
      // Aktif sinyalleri yükle
      await updateSignals();
      
      // İlk kripto fiyatları yükle
      await updateCryptoPrices();
      
      // İlk trade istatistikleri yükle
      await updateTradeStatistics();

      console.log('✅ Backend\'den gerçek veriler yüklendi');
    } catch (error) {
      console.error('❌ Backend veri yükleme hatası:', error);
      setConnectionStatus('hata');
    }
  };

  const updatePrices = async () => {
    try {
      const pricesResponse = await fetch('http://localhost:8000/market-data');
      const pricesData = await pricesResponse.json();
      
      setTradingData(prev => {
        const newData = { ...prev };
        
        // Backend\'den gelen fiyatları güncelle
        if (pricesData && pricesData.forex) {
          Object.entries(pricesData.forex).forEach(([symbol, priceInfo]) => {
            if (newData[symbol]) {
              newData[symbol].currentPrice = priceInfo.price;
            } else {
              // Yeni symbol ekle
              newData[symbol] = {
                currentPrice: priceInfo.price,
                signal: null,
                pastTrades: []
              };
            }
          });
        }
        
        return newData;
      });

      setLastUpdate(new Date().toLocaleTimeString('tr-TR'));
      
      // API durumunu güncelle
      if (pricesData.api_status === 'live') {
        setConnectionStatus('canlı');
      } else if (pricesData.api_status === 'cached') {
        setConnectionStatus('cached');
      } else {
        setConnectionStatus('simüle');
      }
      
    } catch (error) {
      console.error('Fiyat güncelleme hatası:', error);
      setConnectionStatus('hata');
    }
  };

  const updateSignals = async () => {
    try {
      // Forex sinyallerini çek
      const forexResponse = await fetch('http://localhost:8000/forex-signals');
      const forexSignalsData = await forexResponse.json();
      
      // Kripto sinyallerini çek
      const cryptoResponse = await fetch('http://localhost:8000/crypto-signals');
      const cryptoSignalsData = await cryptoResponse.json();
      
      // State'leri güncelle
      const allForexSignals = forexSignalsData.signals || [];
      const allCryptoSignals = cryptoSignalsData.signals || [];
      
      setCryptoSignals(allCryptoSignals);
      
      // Forex sinyallerini trading data'ya ekle
      setTradingData(prev => {
        const newData = { ...prev };
        
        // Önce tüm forex sinyallerini temizle
        Object.keys(newData).forEach(symbol => {
          if (newData[symbol] && newData[symbol].signal) {
            newData[symbol].signal = null;
          }
        });
        
        // Yeni forex sinyallerini ekle
        allForexSignals.forEach(signal => {
          if (newData[signal.symbol]) {
            newData[signal.symbol].signal = {
              strategy: signal.strategy,
              signal_type: signal.signal_type,
              entry_price: signal.ideal_entry,
              take_profit: signal.take_profit,
              stop_loss: signal.stop_loss,
              reliability_score: signal.reliability_score,
              status: 'ACTIVE',
              timeframe: signal.timeframe
            };
          }
        });
        
        return newData;
      });
      
      console.log('🔄 Backend\'den gerçek sinyaller güncellendi');
    } catch (error) {
      console.error('Sinyal güncelleme hatası:', error);
    }
  };

  const updateCryptoPrices = async () => {
    try {
      const cryptoResponse = await fetch('http://localhost:8000/crypto-prices');
      const cryptoPricesData = await cryptoResponse.json();
      
      if (cryptoPricesData.prices) {
        setCryptoData(cryptoPricesData.prices);
        setCryptoStatus(cryptoPricesData.api_status === 'live' ? 'Binance Canlı' : 'Bağlantı Hatası');
      }
      
    } catch (error) {
      console.error('Kripto fiyat güncelleme hatası:', error);
      setCryptoStatus('Bağlantı Hatası');
    }
  };

  const updateTradeStatistics = async () => {
    try {
      const statsResponse = await fetch('http://localhost:8000/trade-statistics');
      const statsData = await statsResponse.json();
      
      // Genel istatistikler
      if (statsData.general_statistics) {
        setTradeStatistics(statsData.general_statistics);
      }
      
      // KRİTİK: Symbol bazlı istatistikler
      if (statsData.symbol_statistics) {
        setSymbolStatistics(statsData.symbol_statistics);
      }
      
      if (statsData.recent_history) {
        setRecentTrades(statsData.recent_history);
      }
      
      // Geçmiş işlemleri trading data'ya ekle (recent_trades kontrolü ile)
      if (statsData.recent_trades && Array.isArray(statsData.recent_trades)) {
        setTradingData(prev => {
          const newData = { ...prev };
          
          // Recent trades'leri symbol'e göre grupla
          const tradesBySymbol = {};
          statsData.recent_trades.forEach(trade => {
            if (!tradesBySymbol[trade.symbol]) {
              tradesBySymbol[trade.symbol] = [];
            }
            tradesBySymbol[trade.symbol].push({
              date: new Date(trade.entry_time).toLocaleDateString('tr-TR', {
                day: '2-digit',
                month: '2-digit',
                year: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
              }),
              signal_type: trade.signal_type === 'BUY' ? 'AL' : 'SAT',
              result: trade.result === 'profit' ? 'TP' : 'SL'
            });
          });
          
          // Her symbol için geçmiş işlemleri güncelle
          Object.keys(newData).forEach(symbol => {
            if (tradesBySymbol[symbol]) {
              newData[symbol].pastTrades = tradesBySymbol[symbol].slice(0, 3); // Son 3 işlem
            }
          });
          
          return newData;
        });
      }
      
    } catch (error) {
      console.error('İstatistik güncelleme hatası:', error);
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🚀 Momentum & Liquidity</h1>
        <h2>Trade Sinyal Platformu</h2>
                 <div className="status-info">
           <span className={`status-badge ${connectionStatus === 'bağlı' || connectionStatus === 'canlı' || connectionStatus === 'simüle' || connectionStatus === 'cached' ? 'active' : 'error'}`}>
             BACKEND: {connectionStatus.toUpperCase()}
           </span>
           <span className="analysis-info">
             Son Güncellenme: {lastUpdate || 'yükleniyor...'}
           </span>
         </div>
      </header>

      <main className="trading-dashboard">
        
        {/* Trade İstatistikleri */}
        <section className="statistics-section">
          <TradeStatistics 
            statistics={tradeStatistics}
            recentTrades={recentTrades}
          />
        </section>
        
        {/* Forex Kartları */}
        <section className="market-section">
          <div className="section-header">
            <h3 className="section-title">📊 FOREX SİNYALLERİ</h3>
            <div className="section-badge">
              <span className="badge-text">KRO & LMO Stratejileri • 📊 Güvenilirlik Sıralı</span>
            </div>
          </div>
          <div className="cards-container">
            {Object.entries(tradingData)
              .sort(([, a], [, b]) => {
                // Sinyali olan kartları önce göster, sonra güvenilirlik skoruna göre sırala
                if (a.signal && !b.signal) return -1;
                if (!a.signal && b.signal) return 1;
                if (a.signal && b.signal) {
                  return (b.signal.reliability_score || 0) - (a.signal.reliability_score || 0);
                }
                return 0;
              })
              .map(([symbol, data]) => (
                <TradingCard
                  key={symbol}
                  symbol={symbol}
                  currentPrice={data.currentPrice}
                  signal={data.signal}
                  pastTrades={data.pastTrades}
                />
              ))}
          </div>
        </section>

        {/* Kripto Kartları */}
        <section className="market-section">
          <div className="section-header">
            <h3 className="section-title">
              🪙 KRİPTO SİNYALLERİ (Binance Canlı)
            </h3>
            <div className="section-badge crypto-badge">
              <span className="badge-text">{cryptoStatus} • {cryptoData ? Object.keys(cryptoData).length : 0} Token • 📊 Güvenilirlik Sıralı</span>
            </div>
          </div>
          <div className="cards-container">
            {cryptoData && Object.entries(cryptoData)
              .map(([symbol, data]) => {
                // Bu kripto için sinyal var mı kontrol et
                const cryptoSignal = cryptoSignals.find(signal => signal.symbol === symbol);
                return { symbol, data, signal: cryptoSignal };
              })
              .sort((a, b) => {
                // Sinyali olan kartları önce göster, sonra güvenilirlik skoruna göre sırala
                if (a.signal && !b.signal) return -1;
                if (!a.signal && b.signal) return 1;
                if (a.signal && b.signal) {
                  return (b.signal.reliability_score || 0) - (a.signal.reliability_score || 0);
                }
                return 0;
              })
              .map(({ symbol, data, signal }) => (
                <CryptoCard
                  key={symbol}
                  symbol={symbol}
                  data={data}
                  signal={signal}
                  statistics={symbolStatistics[symbol]}
                />
              ))}
            {(!cryptoData || Object.keys(cryptoData).length === 0) && (
              <div className="loading-message">
                🔄 Binance API'den kripto verileri yükleniyor...
              </div>
            )}
          </div>
        </section>

      </main>

      <footer className="app-footer">
        <p>© 2024 Momentum & Liquidity Platform - Fonlu Hesap Sinyal Sistemi</p>
        <div className="performance-summary">
          <span>Bu Ay: 72% Başarı Oranı</span>
          <span>•</span>
          <span>Toplam: 156 Sinyal</span>
          <span>•</span>
          <span>Ortalama RR: 2.1</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
