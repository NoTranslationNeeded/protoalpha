import { useState, useEffect } from 'react';
import axios from 'axios';

function AssetEditor({ card, onClose, apiUrl, language = 'ko' }) {
  const [currentImage, setCurrentImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);

  const [activeStyles, setActiveStyles] = useState([]);
  const [loadingStyles, setLoadingStyles] = useState(false);

  // Translations
  const t = {
    currentArt: language === 'ko' ? '현재 아트' : 'Current Art',
    newArt: language === 'ko' ? '새 아트' : 'New Art',
    selectImage: language === 'ko' ? '교체할 이미지를 선택하세요' : 'Select an image to swap',
    recommended: language === 'ko' ? '권장: PNG, JPG' : 'Recommended: PNG, JPG',
    swapArt: language === 'ko' ? '아트 교체' : 'Swap Art',
    swapping: language === 'ko' ? '교체 중...' : 'Swapping...',
    unlockStyle: language === 'ko' ? 'Parallax 스타일 잠금 해제' : 'Unlock Parallax Style',
    unlockConfirm: language === 'ko' ? '이 카드의 Parallax 스타일을 잠금 해제하시겠습니까?' : 'Unlock Parallax Style for this card?',
    swapSuccess: language === 'ko' ? '아트가 성공적으로 교체되었습니다!' : 'Art swapped successfully!',
    unlockSuccess: language === 'ko' ? '스타일이 성공적으로 잠금 해제되었습니다!' : 'Style unlocked successfully!',
    unlockFailed: language === 'ko' ? '스타일 잠금 해제 실패.' : 'Failed to unlock style.',
    noImage: language === 'ko' ? '이미지를 찾을 수 없습니다' : 'No Image Found'
  };

  useEffect(() => {
    // Reset state when card changes
    setSelectedFile(null);
    setPreviewUrl(null);
    setMessage(null);
    
    // Load current image to cache buster
    setCurrentImage(`${apiUrl}/cards/${card.art_id}/image?t=${Date.now()}`);
  }, [card, apiUrl]);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      // Create preview URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleSwap = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await axios.post(`${apiUrl}/cards/${card.art_id}/swap`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setMessage({ type: 'success', text: t.swapSuccess });
      // Refresh current image
      setCurrentImage(`${apiUrl}/cards/${card.art_id}/image?t=${Date.now()}`);
      setSelectedFile(null);
      setPreviewUrl(null);
    } catch (error) {
      console.error("Swap failed", error);
      setMessage({ type: 'error', text: 'Failed to swap art. ' + (error.response?.data?.detail || error.message) });
    } finally {
      setUploading(false);
    }
  };

  const handleUnlockStyle = async () => {
    if (confirm(t.unlockConfirm)) {
      try {
        setMessage(null);
        await axios.post(`${apiUrl}/cards/${card.grp_id}/style/unlock`);
        setMessage({ type: 'success', text: t.unlockSuccess });
      } catch (error) {
        console.error("Unlock failed", error);
        setMessage({ type: 'error', text: t.unlockFailed });
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fade-in">
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] overflow-y-auto flex flex-col">
        
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-[var(--border)]">
          <div>
            <h2 className="text-2xl font-bold">{card.name}</h2>
            <p className="text-[var(--text-muted)]">Set: {card.set_code} | ID: {card.art_id}</p>
          </div>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 flex-1 flex flex-col md:flex-row gap-8">
          
          {/* Current Image */}
          <div className="flex-1 flex flex-col gap-4">
            <h3 className="font-semibold text-lg text-center">{t.currentArt}</h3>
            <div className="aspect-[11/8] bg-[var(--bg-surface)] rounded-lg overflow-hidden border border-[var(--border)] relative group">
              <img 
                src={currentImage} 
                alt="Current Art" 
                className="w-full h-full object-contain"
                onError={(e) => {e.target.style.display='none'; e.target.parentElement.classList.add('flex', 'items-center', 'justify-center'); e.target.parentElement.innerHTML=`<span class="text-gray-500">${t.noImage}</span>`}}
              />
            </div>
          </div>

          {/* New Image / Controls */}
          <div className="flex-1 flex flex-col gap-4">
            <h3 className="font-semibold text-lg text-center">{t.newArt}</h3>
            
            <div className="aspect-[11/8] bg-[var(--bg-surface)] rounded-lg overflow-hidden border border-[var(--border)] flex items-center justify-center relative">
              {previewUrl ? (
                <img src={previewUrl} alt="Preview" className="w-full h-full object-contain" />
              ) : (
                <div className="text-[var(--text-muted)] text-center p-4">
                  <p>{t.selectImage}</p>
                  <p className="text-xs mt-2">{t.recommended}</p>
                </div>
              )}
              
              {/* File Input Overlay */}
              <input 
                type="file" 
                accept="image/*"
                onChange={handleFileSelect}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
            </div>

            <div className="flex flex-col gap-4 mt-auto">
              {message && (
                <div className={`p-3 rounded text-sm ${message.type === 'success' ? 'bg-green-500/20 text-green-200' : 'bg-red-500/20 text-red-200'}`}>
                  {message.text}
                </div>
              )}

              <div className="flex gap-3">
                <button 
                  className={`btn btn-primary flex-1 ${(!selectedFile || uploading) ? 'opacity-50 cursor-not-allowed' : ''}`}
                  onClick={handleSwap}
                  disabled={!selectedFile || uploading}
                >
                  {uploading ? t.swapping : t.swapArt}
                </button>
              </div>

              <div className="border-t border-[var(--border)] pt-4 mt-2">
                <button 
                  className="btn btn-secondary w-full"
                  onClick={handleUnlockStyle}
                >
                  {t.unlockStyle}
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

export default AssetEditor;
