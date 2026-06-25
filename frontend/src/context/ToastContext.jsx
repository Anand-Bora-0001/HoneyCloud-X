import React, { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm pointer-events-none w-full px-4 sm:px-0">
        {toasts.map((toast) => {
          let icon = 'ℹ️';
          let borderClass = 'border-blue-500';
          if (toast.type === 'success') {
            icon = '✅';
            borderClass = 'border-emerald-500';
          } else if (toast.type === 'error') {
            icon = '❌';
            borderClass = 'border-rose-500';
          } else if (toast.type === 'warning') {
            icon = '⚠️';
            borderClass = 'border-amber-500';
          }

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto bg-slate-900/95 border-l-4 ${borderClass} border border-slate-700/50 rounded-lg p-4 shadow-xl flex items-start gap-3 backdrop-blur-md animate-fade-in text-sm text-slate-100`}
              role="alert"
            >
              <span className="text-base select-none">{icon}</span>
              <span className="flex-1 font-medium">{toast.message}</span>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-slate-400 hover:text-slate-100 transition-colors text-base leading-none font-bold"
                aria-label="Close"
              >
                &times;
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};
