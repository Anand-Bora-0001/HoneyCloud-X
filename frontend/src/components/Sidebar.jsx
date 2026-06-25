import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Activity, 
  Search, 
  FileText, 
  Trash2, 
  Settings, 
  LogOut,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('hc_sidebar_collapsed') === 'true';
  });

  useEffect(() => {
    localStorage.setItem('hc_sidebar_collapsed', collapsed);
  }, [collapsed]);

  const navItems = [
    {
      label: 'Overview',
      path: '/dashboard',
      icon: LayoutDashboard,
      section: 'Monitoring'
    },
    {
      label: 'Live Threats',
      path: '/dashboard#feed',
      icon: Activity,
      section: 'Monitoring'
    },
    {
      label: 'Investigations',
      path: '/investigations',
      icon: Search,
      section: 'Intelligence'
    },
    {
      label: 'Reports',
      path: '/reports',
      icon: FileText,
      section: 'Operations'
    },
    {
      label: 'Recycle Bin',
      path: '/recycle-bin',
      icon: Trash2,
      section: 'Operations'
    },
    {
      label: 'Settings',
      path: '/settings',
      icon: Settings,
      section: 'Operations'
    }
  ];

  const handleLogout = (e) => {
    e.preventDefault();
    logout();
    navigate('/');
  };

  return (
    <aside 
      className={`bg-slate-900 border-r border-slate-800 flex flex-col justify-between transition-all duration-300 h-screen sticky top-0 z-50 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      <div>
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-5 py-6 border-b border-slate-800 relative">
          <div className="flex items-center justify-center bg-slate-800/80 rounded-lg p-2 border border-slate-700/50">
            <img 
              src="/assets/logo-sidebar.svg" 
              alt="HoneyCloud" 
              className="w-6 h-6 select-none" 
            />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-slate-100 font-bold text-base leading-none">
                HoneyCloud<span className="text-amber-500">-X</span>
              </span>
              <span className="text-slate-400 text-xxs font-semibold mt-1 uppercase tracking-widest">
                SOC Intel
              </span>
            </div>
          )}
          
          {/* Collapse Button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="absolute -right-3 top-1/2 -translate-y-1/2 bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-100 p-1 rounded-full cursor-pointer transition-colors shadow-lg hidden md:block"
            aria-label="Toggle Sidebar"
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 flex flex-col gap-1">
          {navItems.map((item, idx) => {
            const Icon = item.icon;
            
            // Render section label if it is the first item in the section
            const prevItem = navItems[idx - 1];
            const showSection = !prevItem || prevItem.section !== item.section;

            return (
              <React.Fragment key={item.path + item.label}>
                {showSection && !collapsed && (
                  <div className="text-slate-500 font-semibold text-xxs uppercase tracking-wider mt-5 mb-2 px-3">
                    {item.section}
                  </div>
                )}
                {showSection && collapsed && (
                  <div className="h-[1px] bg-slate-800/80 my-3" />
                )}
                <NavLink
                  to={item.path}
                  end={item.path === '/dashboard'}
                  className={({ isActive }) => 
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative ${
                      isActive 
                        ? 'bg-amber-500/10 text-amber-500 border-l-2 border-amber-500' 
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon size={18} className="shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                  
                  {/* Tooltip on Collapsed */}
                  {collapsed && (
                    <div className="absolute left-full ml-3 bg-slate-900 border border-slate-800 text-slate-100 text-xs px-2.5 py-1.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-xl z-50">
                      {item.label}
                    </div>
                  )}
                </NavLink>
              </React.Fragment>
            );
          })}
        </nav>
      </div>

      {/* Sidebar Footer / User Profile & Signout */}
      <div className="p-4 border-t border-slate-800 flex flex-col gap-3">
        {!collapsed && user && (
          <div className="flex items-center gap-3 bg-slate-800/30 p-2 border border-slate-800 rounded-lg">
            <div className="w-8 h-8 rounded-full bg-amber-500/15 text-amber-500 font-bold flex items-center justify-center text-xs border border-amber-500/30 shrink-0 select-none">
              {(user.username || 'OP').substring(0, 2).toUpperCase()}
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-slate-200 text-xs font-semibold truncate leading-none">
                {user.username}
              </span>
              <span className="text-slate-500 text-xxs font-medium mt-1 truncate uppercase">
                {user.role || 'operator'}
              </span>
            </div>
          </div>
        )}
        
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-rose-500 hover:bg-rose-500/10 w-full transition-colors group relative cursor-pointer"
        >
          <LogOut size={18} className="shrink-0" />
          {!collapsed && <span>Sign Out</span>}
          {collapsed && (
            <div className="absolute left-full ml-3 bg-slate-900 border border-slate-800 text-rose-500 text-xs px-2.5 py-1.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-xl z-50">
              Sign Out
            </div>
          )}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
