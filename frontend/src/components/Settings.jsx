import { useState, useEffect } from 'react';
import axios from 'axios';

function Settings({ apiUrl }) {
  const [config, setConfig] = useState({
    database_path: '',
    save_path: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const res = await axios.get(`${apiUrl}/config`);
      setConfig(res.data);
    } catch (error) {
      console.error("Failed to load config", error);
      setMessage({ type: 'error', text: 'Failed to load configuration.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await axios.post(`${apiUrl}/config`, config);
      setMessage({ type: 'success', text: 'Configuration saved successfully!' });
    } catch (error) {
      console.error("Failed to save config", error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to save configuration.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  if (loading) {
    return <div className="text-center p-8">Loading settings...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="glass-panel p-8">
        <h2 className="text-2xl font-bold mb-6">Settings</h2>
        
        <div className="flex flex-col gap-6">
          {/* Database Path */}
          <div className="flex flex-col gap-2">
            <label className="font-semibold text-sm text-[var(--text-muted)]">
              MTGA Database Path (.mtga file)
            </label>
            <input
              type="text"
              name="database_path"
              value={config.database_path}
              onChange={handleChange}
              placeholder="C:\Program Files\Wizards of the Coast\MTGA\MTGA_Data\Downloads\Raw\Raw_CardDatabase_..."
              className="input font-mono text-sm w-full"
            />
            <p className="text-xs text-[var(--text-muted)]">
              Usually located in your MTGA installation folder under MTGA_Data\Downloads\Raw
            </p>
          </div>

          {/* Save Path */}
          <div className="flex flex-col gap-2">
            <label className="font-semibold text-sm text-[var(--text-muted)]">
              Image Save Path
            </label>
            <input
              type="text"
              name="save_path"
              value={config.save_path}
              onChange={handleChange}
              placeholder="C:\Users\...\Documents\MTGA_Swapper_Images"
              className="input font-mono text-sm w-full"
            />
            <p className="text-xs text-[var(--text-muted)]">
              Directory where exported images will be saved.
            </p>
          </div>

          {/* Message Area */}
          {message && (
            <div className={`p-3 rounded text-sm ${message.type === 'success' ? 'bg-green-500/20 text-green-200' : 'bg-red-500/20 text-red-200'}`}>
              {message.text}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end pt-4 border-t border-[var(--border)]">
            <button 
              onClick={handleSave}
              disabled={saving}
              className="btn btn-primary min-w-[120px]"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
