import { useEffect } from 'react';

function ConfirmModal({ isOpen, onClose, onConfirm, title, message, language = 'ko' }) {
  const t = {
    confirm: language === 'ko' ? '확인' : 'Confirm',
    cancel: language === 'ko' ? '취소' : 'Cancel'
  };

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm p-4 animate-fade-in">
      <div className="glass-panel w-full max-w-md p-6 flex flex-col gap-4">
        {/* Title */}
        {title && (
          <h3 className="text-xl font-bold">{title}</h3>
        )}
        
        {/* Message */}
        <p className="text-[var(--text-muted)] whitespace-pre-line">
          {message}
        </p>

        {/* Buttons */}
        <div className="flex gap-3 mt-4">
          <button
            className="btn btn-secondary flex-1"
            onClick={onClose}
          >
            {t.cancel}
          </button>
          <button
            className="btn btn-primary flex-1"
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            {t.confirm}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;
