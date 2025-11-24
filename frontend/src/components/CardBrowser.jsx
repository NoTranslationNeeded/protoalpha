import { useState, useEffect } from 'react';
import axios from 'axios';
import ConfirmModal from './ConfirmModal';
import ProgressBar from './ProgressBar';

function CardBrowser({ apiUrl, onSelectCard, language = 'ko' }) {
  const [cards, setCards] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [hoveredButton, setHoveredButton] = useState(null);
  
  // Confirmation modal state
  const [confirmModal, setConfirmModal] = useState({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {}
  });
  
  // Progress state for SSE
  const [progress, setProgress] = useState({
    isVisible: false,
    current: 0,
    total: 0,
    message: ''
  });

  // Translations
  const t = {
    searchPlaceholder: language === 'ko' ? '카드 이름, 세트, ID로 검색...' : 'Search cards by name, set, or ID...',
    unlockAll: language === 'ko' ? '모든 Parallax 스타일 잠금 해제' : 'Unlock All Parallax Style',
    unlockAllTooltip: language === 'ko' ? '기본 대지는 영향을 받지 않습니다' : 'Basic lands will not be affected',
    resetToken: language === 'ko' ? '토큰 초기화' : 'Reset Token',
    resetTokenTooltip: language === 'ko' ? '모든 토큰 카드의 Parallax 스타일을 제거합니다' : 'Remove Parallax style from all token cards',
    resetTokenConfirm: language === 'ko' 
      ? '모든 토큰 카드의 Parallax 스타일을 초기화하시겠습니까?\n\n이 작업은 데이터베이스의 모든 토큰 카드에서 Parallax 스타일을 제거하여 원래 상태로 되돌립니다.' 
      : 'Reset Parallax Style for ALL TOKEN CARDS?\n\nThis will remove Parallax styling from every token card in the database, reverting them to their original state.',
    resetVehicle: language === 'ko' ? '단색 탑승물 초기화' : 'Reset Colored Vehicle',
    resetVehicleTooltip: language === 'ko' ? '모든 단색 탑승물 유형 카드의 Parallax 스타일을 제거합니다' : 'Remove Parallax style from all mono-colored vehicle cards',
    resetVehicleConfirm: language === 'ko' 
      ? '단색 탑승물의 텍스트 버그를 수정하시겠습니까?\n\n검은색 규칙 텍스트가 표시되는 단색 탑승물의 Parallax를 초기화합니다.\n\n(무색 및 다색 탑승물은 영향을 받지 않습니다)' 
      : 'Fix Colored Vehicle Text Bug?\n\nThis will reset Parallax for colored mono-colored vehicles that display black rules text.\n\n(Colorless and multicolor vehicles will be unaffected)',
    resetAll: language === 'ko' ? '모든 Parallax 초기화' : 'Reset All Parallax',
    resetAllTooltip: language === 'ko' ? '데이터베이스의 모든 카드에서 Parallax 스타일을 제거합니다' : 'Remove Parallax style from all cards in the database',
    resetAllConfirm: language === 'ko' 
      ? '모든 카드의 Parallax 스타일을 제거하시겠습니까?\n\n이 작업은 데이터베이스의 모든 카드에 적용된 Parallax 효과를 제거합니다.' 
      : 'Remove Parallax style from ALL cards?\n\nThis will remove Parallax effects applied to all cards in the database.',
    noResults: language === 'ko' ? '검색 결과가 없습니다' : 'No cards found matching your search',
    loadMore: language === 'ko' ? '더 보기' : 'Load More',
    loading: language === 'ko' ? '로딩 중...' : 'Loading...',
    failed: language === 'ko' ? '실패했습니다. 콘솔을 확인하세요.' : 'Failed. Check console for details.'
  };

  // Helper function for unlock all confirm message
  const getUnlockAllConfirm = () => {
    return language === 'ko' 
      ? `"${search}"와 일치하는 모든 카드의 Parallax 스타일을 잠금 해제하시겠습니까?\n(기본 대지는 제외됩니다)` 
      : `Are you sure you want to unlock Parallax Style for ALL cards matching "${search}"?\n(Basic lands will be excluded)`;
  };

  // Clean Korean name by removing sprite tags
  const cleanKoreanName = (name) => {
    if (!name) return null;
    return name.replace(/<sprite[^>]*>/gi, '').trim();
  };

  // Helper function to create SSE connection for progress tracking
  const createSSEConnection = (endpoint, onSuccess) => {
    setProgress({
      isVisible: true,
      current: 0,
      total: 0,
      message: language === 'ko' ? '시작 중...' : 'Starting...'
    });
    setLoading(true);
    
    const eventSource = new EventSource(`${apiUrl}${endpoint}`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'progress') {
        setProgress({
          isVisible: true,
          current: data.current,
          total: data.total,
          message: data.message
        });
      } else if (data.type === 'complete') {
        setProgress({
          isVisible: true,
          current: data.total,
          total: data.total,
          message: data.message
        });
        
        // Show completion modal instead of alert
        let displayMessage = data.message;
        if (data.total === 0) {
          displayMessage = language === 'ko' ? '초기화할 카드가 없습니다!' : 'No cards needed resetting!';
        }
        
        setConfirmModal({
          isOpen: true,
          title: language === 'ko' ? '완료' : 'Completed',
          message: displayMessage,
          onConfirm: () => {} // Just close
        });

        eventSource.close();
        setLoading(false);
        setTimeout(() => {
          setProgress({ isVisible: false, current: 0, total: 0, message: '' });
          if (onSuccess) onSuccess();
        }, 2000);
      } else if (data.type === 'error') {
        setConfirmModal({
          isOpen: true,
          title: language === 'ko' ? '오류' : 'Error',
          message: language === 'ko' ? `오류: ${data.message}` : `Error: ${data.message}`,
          onConfirm: () => {}
        });
        eventSource.close();
        setLoading(false);
        setProgress({ isVisible: false, current: 0, total: 0, message: '' });
      }
    };
    
    eventSource.onerror = () => {
      console.error("SSE connection error");
      setConfirmModal({
        isOpen: true,
        title: language === 'ko' ? '오류' : 'Error',
        message: t.failed,
        onConfirm: () => {}
      });
      eventSource.close();
      setLoading(false);
      setProgress({ isVisible: false, current: 0, total: 0, message: '' });
    };
  };

  // Don't load cards on initial mount - only when user searches
  useEffect(() => {
    if (search.trim() === '') {
      setCards([]);
      return;
    }
    
    const timer = setTimeout(() => {
      loadCards(true);
    }, 500);
    return () => clearTimeout(timer);
  }, [search]);

  const loadCards = async (reset = false) => {
    setLoading(true);
    try {
      const currentPage = reset ? 0 : page;
      const res = await axios.get(`${apiUrl}/cards`, {
        params: {
          search: search,
          limit: 50,
          offset: currentPage * 50
        }
      });
      
      if (reset) {
        setCards(res.data.cards);
        setPage(1);
      } else {
        setCards(prev => [...prev, ...res.data.cards]);
        setPage(prev => prev + 1);
      }
      
      setHasMore(res.data.cards.length === 50);
    } catch (error) {
      console.error("Error loading cards:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center justify-center py-8 min-h-[50vh]" style={{ marginTop: '100px' }}>
        
        <div className="w-[600px] max-w-2xl mb-8 mx-auto" style={{ marginTop: '-100px' }}>
          <div className="relative">
            <input
              type="text"
              placeholder={t.searchPlaceholder}
              className="search-input w-full px-6 py-4 text-lg rounded-xl border-none shadow-lg focus:outline-none transition-all text-white placeholder-white"
              style={{ background: 'linear-gradient(135deg, var(--primary), var(--accent))', borderRadius: '15px' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>
        </div>

        <div className="flex flex-col items-center gap-4">
          <div className="flex flex-wrap justify-center gap-4">
            {/* Unlock All Button */}
            <button 
              className="btn btn-primary"
              onMouseEnter={() => setHoveredButton('unlock-all')}
              onMouseLeave={() => setHoveredButton(null)}
              onClick={() => {
                setConfirmModal({
                  isOpen: true,
                  title: t.unlockAll,
                  message: getUnlockAllConfirm(),
                  onConfirm: () => {
                    createSSEConnection(`/cards/style/unlock-batch-stream?search=${encodeURIComponent(search)}`);
                  }
                });
              }}
            >
              {t.unlockAll}
            </button>
            
            {/* Reset Token Button */}
            <button 
              className="btn btn-primary"
              onMouseEnter={() => setHoveredButton('reset-token')}
              onMouseLeave={() => setHoveredButton(null)}
              onClick={() => {
                setConfirmModal({
                  isOpen: true,
                  title: t.resetToken,
                  message: t.resetTokenConfirm,
                  onConfirm: () => {
                    createSSEConnection('/cards/style/reset-tokens-stream');
                  }
                });
              }}
            >
              {t.resetToken}
            </button>
            
            {/* Reset Vehicle Button */}
            <button 
              className="btn btn-primary"
              onMouseEnter={() => setHoveredButton('reset-vehicle')}
              onMouseLeave={() => setHoveredButton(null)}
              onClick={() => {
                setConfirmModal({
                  isOpen: true,
                  title: t.resetVehicle,
                  message: t.resetVehicleConfirm,
                  onConfirm: () => {
                    createSSEConnection('/cards/style/reset-colored-vehicles-stream');
                  }
                });
              }}
            >
              {t.resetVehicle}
            </button>
            
            {/* Reset All Button */}
            <button 
              className="btn btn-primary"
              onMouseEnter={() => setHoveredButton('reset-all')}
              onMouseLeave={() => setHoveredButton(null)}
              onClick={() => {
                setConfirmModal({
                  isOpen: true,
                  title: t.resetAll,
                  message: t.resetAllConfirm,
                  onConfirm: () => {
                    createSSEConnection('/cards/style/reset-all-parallax-stream');
                  }
                });
              }}
            >
              {t.resetAll}
            </button>
          </div>
          
          {/* Progress Bar */}
          {progress.isVisible && (
            <div className="w-[600px] max-w-2xl">
              <ProgressBar
                progress={progress.current}
                total={progress.total}
                message={progress.message}
                language={language}
              />
            </div>
          )}
          
          {/* Tooltip text */}
          <div className="h-6 flex items-center justify-center">
            {hoveredButton === 'unlock-all' && (
              <p className="text-xs text-[var(--text-muted)]">{t.unlockAllTooltip}</p>
            )}
            {hoveredButton === 'reset-token' && (
              <p className="text-xs text-[var(--text-muted)]">{t.resetTokenTooltip}</p>
            )}
            {hoveredButton === 'reset-vehicle' && (
              <p className="text-xs text-[var(--text-muted)]">{t.resetVehicleTooltip}</p>
            )}
            {hoveredButton === 'reset-all' && (
              <p className="text-xs text-[var(--text-muted)]">{t.resetAllTooltip}</p>
            )}
          </div>
        </div>
      </div>

      {/* Card Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 px-4" style={{ marginTop: '-150px' }}>
        {cards.length === 0 && !loading && search.trim() !== '' && (
          <div className="col-span-full text-center py-20">
            <p className="text-[var(--text-muted)] text-lg">
              {t.noResults}
            </p>
          </div>
        )}
        
        {cards.map((card) => {
          const isAlchemy = card.is_alchemy === 1 || card.is_alchemy === true;
          const koreanName = cleanKoreanName(card.korean_name);
          
          return (
            <div 
              key={`${card.grp_id}-${card.art_id}`} 
              className={`glass-panel p-3 flex flex-col gap-2 hover:border-[var(--primary)] hover:-translate-y-1 transition-all cursor-pointer group h-full ${
                isAlchemy ? 'border-blue-500 shadow-lg shadow-blue-500/50' : ''
              }`}
              onClick={() => onSelectCard(card)}
            >
              <h3 className="font-bold text-center text-sm truncate px-1 group-hover:text-[var(--primary)] transition-colors" title={card.name}>
                {card.name}
              </h3>
              
              {koreanName && (
                <p className="text-xs text-center text-[var(--text-muted)] truncate" title={koreanName}>
                  {koreanName}
                </p>
              )}

              <div className="aspect-[5/4.5] w-full bg-[var(--bg-surface)] rounded overflow-hidden relative shadow-inner">
                <img 
                  src={`${apiUrl}/cards/${card.art_id}/image`} 
                  alt={card.name} 
                  className="w-full h-full object-contain"
                  loading="lazy"
                  onError={(e) => {e.target.style.display='none'; e.target.parentElement.innerHTML='<div class="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] text-xs">No Image</div>'}}
                />
              </div>
              
              <div className="flex justify-between items-end text-xs text-[var(--text-muted)] mt-auto pt-2 border-t border-white/5">
                <span className="font-mono uppercase tracking-wider">{card.set_code}</span>
                <span className="font-mono opacity-75">#{card.art_id}</span>
              </div>
            </div>
          );
        })}
      </div>

      {hasMore && cards.length > 0 && (
        <div className="flex justify-center mt-6">
          <button 
            className="btn btn-secondary"
            onClick={() => loadCards(false)}
            disabled={loading}
          >
            {loading ? t.loading : t.loadMore}
          </button>
        </div>
      )}
      
      <ConfirmModal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ ...confirmModal, isOpen: false })}
        onConfirm={confirmModal.onConfirm}
        title={confirmModal.title}
        message={confirmModal.message}
        language={language}
      />
    </div>
  );
}

export default CardBrowser;
