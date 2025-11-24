import { useState, useEffect } from 'react';
import axios from 'axios';

function Settings({ apiUrl, onConfigUpdate, language = 'ko' }) {
  const [config, setConfig] = useState({
    database_path: '',
    save_path: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  // Translations
  const t = {
    title: language === 'ko' ? '설정' : 'Settings',
    dbPathLabel: language === 'ko' ? 'MTGA 데이터베이스 경로 (.mtga 파일)' : 'MTGA Database Path (.mtga file)',
    dbPathHint: language === 'ko' ? 'MTGA 설치 폴더의 MTGA_Data\\Downloads\\Raw에 위치합니다' : 'Usually located in your MTGA installation folder under MTGA_Data\\Downloads\\Raw',
    browse: language === 'ko' ? '찾아보기...' : 'Browse...',
    saveChanges: language === 'ko' ? '변경사항 저장' : 'Save Changes',
    saving: language === 'ko' ? '저장 중...' : 'Saving...',
    loadingSettings: language === 'ko' ? '설정 로딩 중...' : 'Loading settings...',
    saveSuccess: language === 'ko' ? '설정이 성공적으로 저장되었습니다!' : 'Configuration saved successfully!',
    loadFailed: language === 'ko' ? '설정을 불러오지 못했습니다.' : 'Failed to load configuration.',
    browseFailed: language === 'ko' ? '파일 탐색기를 열지 못했습니다.' : 'Failed to open file browser.'
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const res = await axios.get(`${apiUrl}/config`);
      setConfig(res.data);
    } catch (error) {
      console.error("Failed to load config", error);
      setMessage({ type: 'error', text: t.loadFailed });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      // Ensure empty strings are sent as null or handled correctly by backend
      const payload = {
        ...config,
        save_path: config.save_path || null
      };
      await axios.post(`${apiUrl}/config`, payload);
      setMessage({ type: 'success', text: t.saveSuccess });
      // Refresh parent config to update DB status
      if (onConfigUpdate) {
        onConfigUpdate();
      }
    } catch (error) {
      console.error("Failed to save config", error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to save configuration.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setSaving(false);
    }
  };

  const handleBrowse = async (field, type) => {
    try {
      const res = await axios.get(`${apiUrl}/system/browse`, {
        params: { type }
      });
      
      if (res.data.path) {
        setConfig(prev => ({
          ...prev,
          [field]: res.data.path
        }));
      }
    } catch (error) {
      console.error("Browse failed", error);
      setMessage({ type: 'error', text: t.browseFailed });
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
    return <div className="text-center p-8">{t.loadingSettings}</div>;
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="glass-panel p-8">
        <h2 className="text-2xl font-bold mb-6">{t.title}</h2>
        
        <div className="flex flex-col gap-6">
          {/* Database Path */}
          <div className="flex flex-col gap-2">
            <label className="font-semibold text-sm text-[var(--text-muted)]">
              {t.dbPathLabel}
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                name="database_path"
                value={config.database_path}
                onChange={handleChange}
                placeholder="C:\Program Files\Wizards of the Coast\MTGA\MTGA_Data\Downloads\Raw\Raw_CardDatabase_..."
                className="input font-mono text-sm w-full"
              />
              <button 
                className="btn btn-secondary whitespace-nowrap"
                onClick={() => handleBrowse('database_path', 'file')}
              >
                {t.browse}
              </button>
            </div>
            <p className="text-xs text-[var(--text-muted)]">
              {t.dbPathHint}
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
              {saving ? t.saving : t.saveChanges}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
