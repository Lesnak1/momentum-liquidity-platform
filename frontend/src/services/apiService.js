/**
 * Backend API servisleri
 */

const API_BASE_URL = 'http://localhost:8000';

class ApiService {
    /**
     * Canlı fiyatları getirir
     */
    async getCurrentPrices() {
        try {
            const response = await fetch(`${API_BASE_URL}/prices`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Fiyat verisi alma hatası:', error);
            // Fallback olarak önceki verileri kullan
            return this.getFallbackPrices();
        }
    }

    /**
     * Aktif sinyalleri getirir
     */
    async getActiveSignals() {
        try {
            const response = await fetch(`${API_BASE_URL}/signals`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Aktif sinyal alma hatası:', error);
            return { active_signals: [], count: 0 };
        }
    }

    /**
     * Belirli parite için sinyalleri getirir
     */
    async getSignalsForSymbol(symbol) {
        try {
            const response = await fetch(`${API_BASE_URL}/signals/${symbol}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`${symbol} sinyal alma hatası:`, error);
            return { symbol, signals: [] };
        }
    }

    /**
     * API bağlantısını test eder
     */
    async testConnection() {
        try {
            const response = await fetch(`${API_BASE_URL}/prices`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('✅ Backend bağlantısı başarılı:', data);
            return true;
        } catch (error) {
            console.error('❌ Backend bağlantı hatası:', error);
            return false;
        }
    }

    /**
     * ❌ FALLBACK DEVRE DIŞI - GERÇEK VERİ YOKSA HİÇ VERİ YOK
     */
    getFallbackPrices() {
        return {
            error: "Real data unavailable, no fallback used",
            api_status: "no_data",
            last_update: new Date().toISOString()
        };
    }
}

export default new ApiService(); 