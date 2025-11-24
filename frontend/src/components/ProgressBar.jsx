function ProgressBar({ progress, total, message, language = 'ko' }) {
  const percentage = total > 0 ? ((progress / total) * 100).toFixed(1) : 0;
  
  const t = {
    processing: language === 'ko' ? '처리 중...' : 'Processing...'
  };

  return (
    <div className="w-full">
      {/* Progress Bar */}
      <div className="relative w-full h-8 bg-[var(--bg-surface)] rounded-lg overflow-hidden border border-[var(--border)]">
        {/* Fill */}
        <div 
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
        
        {/* Percentage Text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold text-white drop-shadow-lg">
            {percentage}%
          </span>
        </div>
      </div>
      
      {/* Status Message */}
      {message && (
        <p className="text-xs text-[var(--text-muted)] mt-2 text-center">
          {message}
        </p>
      )}
    </div>
  );
}

export default ProgressBar;
