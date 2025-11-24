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
        {/* Left: DB Status */}
        <div className="flex justify-start">
          <div className="text-xs text-[var(--text-muted)]">
            {config?.database_path ? 'DB Connected' : 'No DB'}
          </div>
        </div>

        {/* Right: Card Browser and Settings */}
        <div className="flex justify-end items-center gap-4">
          <button 
            onClick={() => setActiveTab('browser')}
            className={`btn ${activeTab === 'browser' ? 'btn-primary' : 'btn-ghost'} text-lg`}
          >
            Card Browser
          </button>
          <button 
            onClick={() => setActiveTab('settings')}
            className={`btn ${activeTab === 'settings' ? 'btn-primary' : 'btn-ghost'} text-lg`}
          >
            Settings
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
              />
            )}
            {activeTab === 'settings' && (
              <Settings apiUrl={API_URL} />
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
        />
      )}
    </div>
  )
}

export default App
