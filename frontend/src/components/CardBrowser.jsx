import { useState, useEffect } from 'react';
import axios from 'axios';

function CardBrowser({ apiUrl, onSelectCard }) {
  const [cards, setCards] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  // Don't load cards on initial mount - only when user searches
  useEffect(() => {
    // Only load if there's a search term
    if (search.trim() === '') {
      setCards([]);
      return;
    }
    
    // Debounce search
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
      {/* Google-style Search Area */}
      <div className="flex flex-col items-center justify-center py-8 min-h-[50vh]" style={{ marginTop: '250px' }}>
        
        {/* Google-style Search Bar */}
        <div className="w-[600px] max-w-2xl mb-8 mx-auto" style={{ marginTop: '-100px' }}>
          <div className="relative">
            <input
              type="text"
              placeholder="Search cards by name, set, or ID..."
              className="search-input w-full px-6 py-4 text-lg rounded-xl border-none shadow-lg focus:outline-none transition-all text-white placeholder-white"
              style={{ background: 'linear-gradient(135deg, var(--primary), var(--accent))', borderRadius: '15px' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>
        </div>

        {/* Google-style Action Buttons */}
        <div className="flex flex-wrap justify-center" style={{ marginTop: '100px' }}>
          <button 
            className="btn btn-primary"
            style={{ margin: '0 60px' }}
            onClick={async () => {
              if (confirm(`Are you sure you want to unlock Parallax Style for ALL cards matching "${search}"?\n(Basic lands will be excluded)`)) {
                try {
                  setLoading(true);
                  const res = await axios.post(`${apiUrl}/cards/style/unlock-batch`, null, {
                    params: { search: search }
                  });
                  alert(res.data.message);
                } catch (error) {
                  console.error("Batch unlock failed", error);
                  alert("Failed to unlock styles. Check console for details.");
                } finally {
                  setLoading(false);
                }
              }
            }}
          >
            Unlock Parallax Styles ({cards.length > 0 ? 'Listed' : 'All'})
          </button>
          
          <button 
            className="btn btn-primary"
            style={{ margin: '0 60px' }}
            onClick={async () => {
              if (confirm('Unlock Parallax Style for ALL TOKEN CARDS?\n\nThis will unlock Parallax for every token card in the database.')) {
                try {
                  setLoading(true);
                  const res = await axios.post(`${apiUrl}/cards/style/unlock-tokens`);
                  alert(res.data.message);
                } catch (error) {
                  console.error("Token unlock failed", error);
                  alert("Failed to unlock token styles. Check console for details.");
                } finally {
                  setLoading(false);
                }
              }
            }}
          >
            Unlock All Tokens
          </button>
          
          <button 
            className="btn btn-primary"
            style={{ margin: '0 60px' }}
            onClick={async () => {
              if (confirm('Reset Parallax Style for ALL TOKEN CARDS?\n\nThis will remove Parallax styling from every token card in the database, reverting them to their original state.')) {
                try {
                  setLoading(true);
                  const res = await axios.post(`${apiUrl}/cards/style/reset-tokens`);
                  alert(res.data.message);
                } catch (error) {
                  console.error("Token reset failed", error);
                  alert("Failed to reset token styles. Check console for details.");
                } finally {
                  setLoading(false);
                }
              }
            }}
          >
            Reset Token Parallax
          </button>
          
          <button 
            className="btn btn-primary"
            style={{ margin: '0 60px' }}
            onClick={async () => {
              if (confirm('Fix Colored Vehicle Text Bug?\n\nThis will reset Parallax for colored mono-colored vehicles that display black rules text.\n\n(Colorless and multicolor vehicles will be unaffected)')) {
                try {
                  setLoading(true);
                  const res = await axios.post(`${apiUrl}/cards/style/reset-colored-vehicles`);
                  alert(res.data.message);
                } catch (error) {
                  console.error("Colored vehicle reset failed", error);
                  alert("Failed to reset colored vehicle styles. Check console for details.");
                } finally {
                  setLoading(false);
                }
              }
            }}
          >
            Fix Colored Vehicle Text Bug
          </button>
        </div>
      </div>

      {/* Card Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 px-4">
        {/* Only show message when search returns no results */}
        {cards.length === 0 && !loading && search.trim() !== '' && (
          <div className="col-span-full text-center py-20">
            <p className="text-[var(--text-muted)] text-lg">
              No cards found matching your search
            </p>
          </div>
        )}
        
        {cards.map((card) => (
          <div 
            key={`${card.grp_id}-${card.art_id}`} 
            className="glass-panel p-3 flex flex-col gap-2 hover:border-[var(--primary)] hover:-translate-y-1 transition-all cursor-pointer group h-full"
            onClick={() => onSelectCard(card)}
          >
            {/* Title */}
            <h3 className="font-bold text-center text-sm truncate px-1 group-hover:text-[var(--primary)] transition-colors" title={card.name}>
              {card.name}
            </h3>

            {/* Image */}
            <div className="aspect-[4/3] w-full bg-[var(--bg-surface)] rounded overflow-hidden relative shadow-inner">
              <img 
                src={`${apiUrl}/cards/${card.art_id}/image`} 
                alt={card.name} 
                className="w-full h-full object-contain"
                loading="lazy"
                onError={(e) => {e.target.style.display='none'; e.target.parentElement.innerHTML='<div class="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] text-xs">No Image</div>'}}
              />
            </div>
            
            {/* Metadata Footer */}
            <div className="flex justify-between items-end text-xs text-[var(--text-muted)] mt-auto pt-2 border-t border-white/5">
              <span className="font-mono uppercase tracking-wider">{card.set_code}</span>
              <span className="font-mono opacity-75">#{card.art_id}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Load More */}
      {hasMore && cards.length > 0 && (
        <div className="flex justify-center mt-6">
          <button 
            className="btn btn-secondary"
            onClick={() => loadCards(false)}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}
    </div>
  );
}

export default CardBrowser;
