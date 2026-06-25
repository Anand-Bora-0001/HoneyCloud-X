import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Search, Volume2, VolumeX, ShieldAlert, Monitor, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

const Navbar = () => {
  const { user, sseConnected } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [audioEnabled, setAudioEnabled] = useState(false);
  
  // Theme state
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('hc_theme') || 'default';
  });

  // Apply theme class to document element
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('theme-midnight-amber', 'theme-obsidian');
    
    if (theme === 'midnight-amber') {
      root.classList.add('theme-midnight-amber');
    } else if (theme === 'obsidian') {
      root.classList.add('theme-obsidian');
    }
    
    localStorage.setItem('hc_theme', theme);
  }, [theme]);

  // Handle Ctrl+K/Cmd+K to focus search input
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('navbar-search');
        if (searchInput) searchInput.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleAudioToggle = () => {
    const newVal = !audioEnabled;
    setAudioEnabled(newVal);
    showToast(newVal ? 'Audio alerts enabled' : 'Audio alerts muted', 'info');
  };

  // Compute title based on current pathname
  const getBreadcrumbs = () => {
    const path = location.pathname;
    if (path === '/dashboard') return <span className="text-slate-100 font-bold">SOC Dashboard</span>;
    if (path === '/investigations') return <span className="text-slate-100 font-bold">Adversary Investigations</span>;
    if (path === '/reports') return <span className="text-slate-100 font-bold">Reporting Engine</span>;
    if (path === '/recycle-bin') return <span className="text-slate-100 font-bold">Lifecycle Management</span>;
    if (path === '/settings') return <span className="text-slate-100 font-bold">Platform Settings</span>;
    if (path.startsWith('/attack-details/')) {
      return (
        <div className="flex items-center gap-1.5 text-slate-400 text-xs sm:text-sm">
          <span className="hover:text-slate-200 cursor-pointer" onClick={() => navigate('/dashboard')}>Dashboard</span>
          <ChevronRight size={14} />
          <span className="text-amber-500 font-mono">Threat Record</span>
        </div>
      );
    }
    return <span className="text-slate-100 font-bold">HoneyCloud</span>;
  };

  return (
    <header className="bg-slate-950/80 border-b border-slate-800/60 px-6 py-4 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md">
      {/* Page Title / Breadcrumbs */}
      <div className="flex items-center gap-4">
        {getBreadcrumbs()}
      </div>

      {/* Right Navbar Section */}
      <div className="flex items-center gap-4">
        {/* SSE Streaming Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
          <span className={`w-2.5 h-2.5 rounded-full relative shrink-0 ${
            sseConnected 
              ? 'bg-emerald-500 shadow-[0_0_8px_#10B981]' 
              : 'bg-rose-500 shadow-[0_0_8px_#EF4444]'
          }`}>
            {sseConnected && (
              <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-75" />
            )}
          </span>
          <span className="text-xxs font-bold text-slate-300 uppercase tracking-wider select-none hidden sm:inline">
            {sseConnected ? 'SSE Live' : 'Disconnected'}
          </span>
        </div>

        {/* Global Search Box (⌘K) */}
        <div className="relative max-w-xs hidden md:block">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            id="navbar-search"
            placeholder="Search IPs, events... (⌘K)"
            className="bg-slate-900 border border-slate-800 text-slate-200 placeholder-slate-500 pl-10 pr-4 py-1.5 rounded-lg text-xs focus:outline-none focus:border-amber-500/50 w-52 focus:w-64 transition-all duration-300 font-mono"
            aria-label="Global Search"
          />
        </div>

        {/* Audio Alerts Toggle */}
        <button
          onClick={handleAudioToggle}
          className="p-2 bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-400 hover:text-slate-100 rounded-lg transition-colors cursor-pointer"
          aria-label="Toggle Audio Alerts"
        >
          {audioEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
        </button>



        {/* User Card Link */}
        {user && (
          <div
            onClick={() => navigate('/settings')}
            className="flex items-center gap-2 p-1 border border-transparent hover:border-slate-800 hover:bg-slate-900/50 rounded-lg cursor-pointer transition-all"
            role="button"
            tabIndex={0}
            aria-label="Operator Settings"
          >
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-500 font-bold border border-amber-500/20 flex items-center justify-center text-xs select-none">
              {(user.username || 'OP').substring(0, 2).toUpperCase()}
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Navbar;
