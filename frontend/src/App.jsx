import { useState, useEffect } from 'react'
import axios from 'axios'
import './index.css'
import CardBrowser from './components/CardBrowser'
import AssetEditor from './components/AssetEditor'
import Settings from './components/Settings'

const API_URL = 'http://localhost:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('browser'); // 'browser', 'settings'
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCard, setSelectedCard] = useState(null);
  const [language, setLanguage] = useState('ko'); // 'en' or 'ko'

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API_URL}/config`);
      setConfig(res.data);
    } catch (error) {
      console.error("Failed to load config", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)]">
      {/* Header / Navigation */}
      {/* Header / Navigation */}
      <nav className="glass-panel sticky top-4 mx-4 mb-6 p-4 z-50 flex justify-between items-center">
        {/* Left: DB Status and Language Toggle */}
        <div className="flex items-center gap-4">
          <div className={`text-sm font-semibold ${config?.is_db_connected ? 'text-green-500' : 'text-red-500'}`}>
            {config?.is_db_connected ? (language === 'ko' ? 'DB 연결됨' : 'DB Connected') : (language === 'ko' ? 'DB 연결 안 됨' : 'No DB Connection')}
          </div>
          
          {/* Language Toggle Flags */}
          <div className="flex gap-2">
            <button
              onClick={() => setLanguage('en')}
              className={`text-2xl transition-all ${language === 'en' ? 'scale-125' : 'opacity-50 hover:opacity-100'}`}
              title="English"
            >
              🇺🇸
            </button>
            <button
              onClick={() => setLanguage('ko')}
              className={`text-2xl transition-all ${language === 'ko' ? 'scale-125' : 'opacity-50 hover:opacity-100'}`}
              title="한국어"
            >
              🇰🇷
            </button>
          </div>
        </div>

        {/* Right: Card Browser and Settings */}
        <div className="flex justify-end items-center gap-4">
          <button 
            onClick={() => setActiveTab('browser')}
            className={`btn ${activeTab === 'browser' ? 'btn-primary' : 'btn-ghost'} text-lg`}
          >
            {language === 'ko' ? '카드 브라우저' : 'Card Browser'}
          </button>
          <button 
            onClick={() => setActiveTab('settings')}
            className={`btn ${activeTab === 'settings' ? 'btn-primary' : 'btn-ghost'} text-lg`}
          >
            {language === 'ko' ? '설정' : 'Settings'}
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container pb-10">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-pulse text-[var(--primary)]">Loading...</div>
          </div>
        ) : (
          <div className="animate-fade-in">
            {activeTab === 'browser' && (
              <CardBrowser 
                apiUrl={API_URL} 
                onSelectCard={setSelectedCard}
                language={language}
              />
            )}
            {activeTab === 'settings' && (
              <Settings apiUrl={API_URL} onConfigUpdate={fetchConfig} language={language} />
            )}
          </div>
        )}
      </main>

      {/* Asset Editor Modal */}
      {selectedCard && (
        <AssetEditor 
          card={selectedCard} 
          onClose={() => setSelectedCard(null)} 
          apiUrl={API_URL}
          language={language}
        />
      )}
    </div>
  )
}

export default App
