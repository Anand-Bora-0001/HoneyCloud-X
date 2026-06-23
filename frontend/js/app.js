/**
 * HoneyCloud-X Frontend Core v3.0
 * Handles API communication, authentication, notifications, sidebar/topbar injection, 
 * loading skeletons, animated counters, and keyboard navigation.
 */

// Initialize config if not present
if (!window.CONFIG) {
    window.CONFIG = {
        API_BASE: window.location.protocol === 'file:' ? 'http://localhost:8000' : '',
        VERSION: '3.0.0'
    };
}

class HoneyCloudApp {
    constructor() {
        this.apiBase = window.CONFIG.API_BASE;
        this.tokenKey = 'hc_token';
        this.sidebarCollapsedKey = 'hc_sidebar_collapsed';
        this.applyTheme();
        this.initKeyboardNav();
    }

    applyTheme() {
        const theme = localStorage.getItem('hc_theme') || 'default';
        if (theme === 'midnight-amber') {
            document.documentElement.style.setProperty('--accent', '#FFC14D');
            document.documentElement.style.setProperty('--accent-hover', '#F6A623');
            document.documentElement.style.setProperty('--accent-light', 'rgba(255,193,77,0.1)');
            document.documentElement.style.setProperty('--border-active', 'rgba(255,193,77,0.5)');
            document.documentElement.style.setProperty('--bg-primary', '#070A0E');
            document.documentElement.style.setProperty('--bg-surface', '#0D1117');
        } else if (theme === 'obsidian') {
            document.documentElement.style.setProperty('--accent', '#C47B1A');
            document.documentElement.style.setProperty('--accent-hover', '#A3620F');
            document.documentElement.style.setProperty('--accent-light', 'rgba(196,123,26,0.1)');
            document.documentElement.style.setProperty('--border-active', 'rgba(196,123,26,0.5)');
            document.documentElement.style.setProperty('--bg-primary', '#050505');
            document.documentElement.style.setProperty('--bg-surface', '#0C0C0C');
        } else {
            // default Honey Gold
            document.documentElement.style.setProperty('--accent', '#F6A623');
            document.documentElement.style.setProperty('--accent-hover', '#E8912D');
            document.documentElement.style.setProperty('--accent-light', 'rgba(246,166,35,0.1)');
            document.documentElement.style.setProperty('--border-active', 'rgba(246,166,35,0.5)');
            document.documentElement.style.setProperty('--bg-primary', '#0B0F14');
            document.documentElement.style.setProperty('--bg-surface', '#111827');
        }

        const grid = localStorage.getItem('hc_grid') === 'true';
        if (document.body) {
            if (grid) {
                document.body.style.backgroundImage = 'radial-gradient(var(--border) 1px, transparent 1px)';
                document.body.style.backgroundSize = '24px 24px';
            } else {
                document.body.style.backgroundImage = 'none';
            }
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                if (grid) {
                    document.body.style.backgroundImage = 'radial-gradient(var(--border) 1px, transparent 1px)';
                    document.body.style.backgroundSize = '24px 24px';
                } else {
                    document.body.style.backgroundImage = 'none';
                }
            });
        }
    }

    /* ============================================================
       AUTHENTICATION
       ============================================================ */

    getToken() {
        return localStorage.getItem(this.tokenKey) || sessionStorage.getItem(this.tokenKey);
    }

    setToken(token, remember = true) {
        if (remember) {
            localStorage.setItem(this.tokenKey, token);
            sessionStorage.removeItem(this.tokenKey);
        } else {
            sessionStorage.setItem(this.tokenKey, token);
            localStorage.removeItem(this.tokenKey);
        }
    }

    clearToken() {
        localStorage.removeItem(this.tokenKey);
        sessionStorage.removeItem(this.tokenKey);
    }

    isAuthenticated() {
        return !!this.getToken();
    }

    logout() {
        this.clearToken();
        window.location.href = 'login.html';
    }

    /* ============================================================
       API CLIENT
       ============================================================ */

    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Handle form data which shouldn't have Content-Type set manually (browser sets it with boundary)
        if (options.body instanceof URLSearchParams || options.body instanceof FormData) {
            delete headers['Content-Type'];
            if (options.body instanceof URLSearchParams) {
                 headers['Content-Type'] = 'application/x-www-form-urlencoded';
            }
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);

            // Handle unauthorized globally
            if (response.status === 401) {
                this.logout();
                throw new Error('Session expired. Please log in again.');
            }

            const isJson = response.headers.get('content-type')?.includes('application/json');
            
            if (!response.ok) {
                const errorData = isJson ? await response.json() : await response.text();
                const errorMessage = isJson ? (errorData.detail || errorData.message || 'API Error') : errorData;
                throw new Error(errorMessage);
            }

            if (isJson) {
                return await response.json();
            }
            return await response.text();

        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error(`[API Error] ${endpoint}:`, error);
            }
            throw error;
        }
    }

    /* ============================================================
       UI HELPERS
       ============================================================ */

    showToast(message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            container.setAttribute('role', 'alert');
            container.setAttribute('aria-live', 'polite');
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-slide-up`;
        
        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        if (type === 'error') icon = '❌';
        if (type === 'warning') icon = '⚠️';

        toast.innerHTML = `
            <span>${icon}</span>
            <span style="flex:1">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()" aria-label="Close notification">&times;</button>
        `;

        container.appendChild(toast);

        // Auto remove
        setTimeout(() => {
            if (document.body.contains(toast)) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(20px)';
                toast.style.transition = 'all 200ms ease';
                setTimeout(() => toast.remove(), 200);
            }
        }, 5000);
    }

    /* ============================================================
       SIDEBAR & NAVBAR INJECTION
       ============================================================ */

    injectSidebar(activePage = null) {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;

        // Auto-detect active page from URL/hash if not provided
        if (!activePage) {
            const path = window.location.pathname;
            const hash = window.location.hash;
            if (path.includes('dashboard.html')) {
                activePage = hash.includes('feed') ? 'live-threats' : 'dashboard';
            } else if (path.includes('investigations.html')) {
                activePage = 'investigations';
            } else if (path.includes('reports.html')) {
                activePage = 'reports';
            } else if (path.includes('recycle-bin.html')) {
                activePage = 'recycle-bin';
            } else if (path.includes('settings.html')) {
                activePage = 'settings';
            } else if (path.includes('attack-details.html')) {
                activePage = 'attack-details';
            } else {
                activePage = 'dashboard'; // fallback
            }
        }

        const isCollapsed = localStorage.getItem(this.sidebarCollapsedKey) === 'true';
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
        } else {
            sidebar.classList.remove('collapsed');
        }

        sidebar.innerHTML = `
            <div class="sidebar-brand">
                <div class="sidebar-brand-icon">
                    <img src="assets/logo-sidebar.svg" alt="" width="22" height="22">
                </div>
                <div class="flex-col">
                    <span class="sidebar-brand-text">HoneyCloud<span style="color:var(--honey)">-X</span></span>
                    <span class="sidebar-brand-version">Threat Intelligence</span>
                </div>
            </div>
            
            <button id="sidebarCollapseBtn" class="sidebar-collapse-btn" aria-label="Collapse sidebar">
                ${isCollapsed ? '❯' : '❮'}
            </button>
            
            <nav class="sidebar-nav">
                <div class="sidebar-section-label">Monitoring</div>
                <a href="dashboard.html" class="sidebar-link ${activePage === 'dashboard' ? 'active' : ''}" ${activePage === 'dashboard' ? 'aria-current="page"' : ''}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>
                    <span>Overview</span>
                    <span class="sidebar-tooltip">Overview</span>
                </a>
                <a href="dashboard.html#feed" class="sidebar-link ${activePage === 'live-threats' ? 'active' : ''}" ${activePage === 'live-threats' ? 'aria-current="page"' : ''}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20v-6M6 20V10M18 20V4"></path></svg>
                    <span>Live Threats</span>
                    <span class="sidebar-tooltip">Live Threats</span>
                </a>
                
                <div class="sidebar-section-label" style="margin-top:20px;">Intelligence</div>
                <a href="investigations.html" class="sidebar-link ${activePage === 'investigations' ? 'active' : ''}" ${activePage === 'investigations' ? 'aria-current="page"' : ''}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <span>Investigations</span>
                    <span class="sidebar-tooltip">Investigations</span>
                </a>
                
                <div class="sidebar-section-label" style="margin-top:20px;">Operations</div>
                <a href="reports.html" class="sidebar-link ${activePage === 'reports' ? 'active' : ''}" ${activePage === 'reports' ? 'aria-current="page"' : ''}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                    <span>Reports</span>
                    <span class="sidebar-tooltip">Reports</span>
                </a>
                <a href="recycle-bin.html" class="sidebar-link ${activePage === 'recycle-bin' ? 'active' : ''}" ${activePage === 'recycle-bin' ? 'aria-current="page"' : ''}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    <span>Recycle Bin</span>
                    <span class="sidebar-tooltip">Recycle Bin</span>
                </a>
                <a href="settings.html" class="sidebar-link ${activePage === 'settings' ? 'active' : ''}" ${activePage === 'settings' ? 'aria-current="page"' : ''}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    <span>Settings</span>
                    <span class="sidebar-tooltip">Settings</span>
                </a>
            </nav>
            
            <div class="sidebar-footer">
                <a href="#" onclick="app.logout(); return false;" class="sidebar-link" style="color:var(--danger);">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                    <span>Sign Out</span>
                    <span class="sidebar-tooltip" style="color:var(--danger);">Sign Out</span>
                </a>
            </div>
        `;

        // Setup collapse button
        const collapseBtn = document.getElementById('sidebarCollapseBtn');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => {
                const nowCollapsed = sidebar.classList.toggle('collapsed');
                localStorage.setItem(this.sidebarCollapsedKey, nowCollapsed);
                collapseBtn.innerHTML = nowCollapsed ? '❯' : '❮';
            });
        }
    }

    injectTopbar(title, options = {}) {
        const topbar = document.querySelector('header.topbar') || document.getElementById('topbar');
        if (!topbar) return;

        const showSearch = options.showSearch !== false;
        const extraActions = options.extraActions || '';

        topbar.innerHTML = `
            <div class="flex items-center gap-16">
                <button id="mobileMenuBtn" class="mobile-menu-btn topbar-icon-btn" aria-label="Toggle navigation menu">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                </button>
                <div class="topbar-title">${title}</div>
            </div>
            
            <div class="topbar-right">
                ${extraActions}
                
                ${showSearch ? `
                <div class="topbar-search">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <input type="text" id="globalSearchInput" placeholder="Search IPs, events... (⌘K)" aria-label="Search">
                </div>
                ` : ''}
                
                <button class="topbar-icon-btn" onclick="app.showToast('Audio alerts disabled', 'info')" aria-label="Toggle audio alerts">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5z"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                </button>

                <div class="topbar-user" onclick="window.location.href='settings.html'" role="button" tabindex="0" aria-label="User settings">
                    <div class="topbar-avatar" id="topbarAvatar">OP</div>
                    <span class="topbar-username" id="topbarUsername">Operator</span>
                </div>
            </div>
        `;

        // Re-setup mobile menu toggle event listener
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const sidebar = document.getElementById('sidebar');
        if (mobileMenuBtn && sidebar) {
            mobileMenuBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
        }

        // Initialize user info in topbar
        this.initUser();
    }


    /* ============================================================
       USER INFO
       ============================================================ */

    async initUser() {
        if (!this.isAuthenticated()) return;
        
        const usernameEl = document.getElementById('topbarUsername');
        const avatarEl = document.getElementById('topbarAvatar');
        
        if (!usernameEl && !avatarEl) return;

        try {
            const user = await this.apiCall('/auth/me');
            if (usernameEl) usernameEl.textContent = user.username;
            if (avatarEl) avatarEl.textContent = user.username.substring(0, 2).toUpperCase();
        } catch (error) {
            // Error handled by apiCall (might logout if 401)
        }
    }

    /* ============================================================
       LOADING SKELETONS
       ============================================================ */

    showLoadingSkeleton(containerId, type = 'cards', count = 3) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let html = '';
        if (type === 'metrics') {
            html = Array(count).fill(0).map(() => `
                <div class="skeleton skeleton-metric"></div>
            `).join('');
        } else if (type === 'cards') {
            html = Array(count).fill(0).map(() => `
                <div class="skeleton skeleton-card"></div>
            `).join('');
        } else if (type === 'table') {
            html = `
                <div style="padding: 16px; display: flex; flex-direction: column; gap: 12px;">
                    ${Array(count).fill(0).map(() => `<div class="skeleton skeleton-text"></div>`).join('')}
                </div>
            `;
        }
        container.innerHTML = html;
    }

    /* ============================================================
       ANIMATED COUNTER
       ============================================================ */

    animateCounter(element, targetValue, duration = 800) {
        if (!element) return;
        const start = parseInt(element.textContent) || 0;
        const diff = targetValue - start;
        if (diff === 0) {
            element.textContent = targetValue;
            return;
        }

        const startTime = performance.now();
        
        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = Math.round(start + diff * eased);
            
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        
        requestAnimationFrame(step);
    }

    /* ============================================================
       KEYBOARD NAVIGATION
       ============================================================ */

    initKeyboardNav() {
        document.addEventListener('keydown', (e) => {
            // Escape closes modals
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal-overlay.open');
                if (openModal) {
                    openModal.classList.remove('open');
                }
                // Close mobile sidebar
                const sidebar = document.getElementById('sidebar');
                if (sidebar && sidebar.classList.contains('open')) {
                    sidebar.classList.remove('open');
                }
            }

            // Cmd/Ctrl+K for search focus
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('.topbar-search input');
                if (searchInput) searchInput.focus();
            }
        });
    }
    
    /* ============================================================
       UTILITIES
       ============================================================ */

    formatDate(isoString) {
        if (!isoString) return 'N/A';
        const date = new Date(isoString);
        return date.toLocaleString(undefined, { 
            year: 'numeric', month: 'short', day: 'numeric', 
            hour: '2-digit', minute: '2-digit', second: '2-digit' 
        });
    }

    formatRelativeTime(isoString) {
        if (!isoString) return 'N/A';
        const date = new Date(isoString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return `${diff}s ago`;
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
        return this.formatDate(isoString);
    }

    // Clamp ML confidence to 0-100%
    clampConfidence(value) {
        if (!value && value !== 0) return 0;
        let pct = value <= 1 ? value * 100 : value;
        return Math.max(0, Math.min(100, pct));
    }

    // Get severity badge class
    getSeverityBadge(severity) {
        const s = (severity || '').toUpperCase();
        if (s === 'CRITICAL') return 'badge-critical';
        if (s === 'HIGH') return 'badge-high';
        if (s === 'MEDIUM') return 'badge-medium';
        return 'badge-low';
    }

    // Generate a country flag emoji from country code or name
    getCountryFlag(country) {
        const flagMap = {
            'United States': '🇺🇸', 'US': '🇺🇸', 'China': '🇨🇳', 'CN': '🇨🇳',
            'Russia': '🇷🇺', 'RU': '🇷🇺', 'Germany': '🇩🇪', 'DE': '🇩🇪',
            'France': '🇫🇷', 'FR': '🇫🇷', 'United Kingdom': '🇬🇧', 'GB': '🇬🇧',
            'India': '🇮🇳', 'IN': '🇮🇳', 'Brazil': '🇧🇷', 'BR': '🇧🇷',
            'Japan': '🇯🇵', 'JP': '🇯🇵', 'South Korea': '🇰🇷', 'KR': '🇰🇷',
            'Netherlands': '🇳🇱', 'NL': '🇳🇱', 'Canada': '🇨🇦', 'CA': '🇨🇦',
            'Australia': '🇦🇺', 'AU': '🇦🇺', 'Iran': '🇮🇷', 'IR': '🇮🇷',
            'North Korea': '🇰🇵', 'KP': '🇰🇵', 'Vietnam': '🇻🇳', 'VN': '🇻🇳',
            'Ukraine': '🇺🇦', 'UA': '🇺🇦', 'Turkey': '🇹🇷', 'TR': '🇹🇷',
            'Romania': '🇷🇴', 'RO': '🇷🇴', 'Indonesia': '🇮🇩', 'ID': '🇮🇩',
        };
        return flagMap[country] || '🌍';
    }
}

// Instantiate globally
window.app = new HoneyCloudApp();

// Automatically inject sidebar when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app.injectSidebar();
});
