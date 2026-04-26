class HoneyDashboard {
    constructor(config) {
        this.apiUrl = config.API_URL || 'http://localhost:8000';
        this.updateInterval = config.INTERVAL || 30000;
        this.stats = null;
        this.events = [];
        this.isInitialLoad = true;
        this.audioEnabled = localStorage.getItem('audio_alerts') === 'true';
        this.map = null;
        this.pings = [];
        this.maxPings = 50;
        this.markers = L.layerGroup();
        
        // Audio assets
        this.alertSound = new Audio('static/audio/alert.mp3');
    }

    getAuthHeader() {
        const token = localStorage.getItem('hc_token'); // Use standard token key
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async init() {
        console.log('[HoneyCloud] Initializing dashboard engine...');
        this.initMap();
        this.setupEventListeners();
        await this.refreshData();
        
        // Start Real-time Stream (SSE)
        this.initEventStream();
        
        // Background polling for stats ONLY (slower frequency since map is real-time)
        setInterval(() => this.fetchStats(), this.updateInterval);
    }

    initMap() {
        if (!document.getElementById('attackMap')) return;

        // Dark-themed Sci-Fi Map
        this.map = L.map('attackMap', {
            center: [20, 0],
            zoom: 2,
            zoomControl: false,
            attributionControl: false,
            dragging: true,
            scrollWheelZoom: false
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 10
        }).addTo(this.map);

        this.markers.addTo(this.map);
        console.log('[HoneyCloud] Map initialized');
    }

    initEventStream() {
        const token = localStorage.getItem('hc_token');
        if (!token) return;

        console.log('[HoneyCloud] Connecting to real-time intelligence stream...');
        const eventSource = new EventSource(`${this.apiUrl}/api/events/stream?token=${token}`);

        eventSource.addEventListener('new_attack', (e) => {
            const event = JSON.parse(e.data);
            this.handleNewAttack(event);
        });

        eventSource.onerror = (err) => {
            console.error('[HoneyCloud] Stream error:', err);
            eventSource.close();
            // Reconnect after 5 seconds
            setTimeout(() => this.initEventStream(), 5000);
        };
    }

    handleNewAttack(event) {
        // Add to list (front)
        this.events.unshift(event);
        if (this.events.length > 50) this.events.pop();

        // Update UI components
        this.updateUI();
        
        // Map Ping
        if (event.location && event.location.lat && event.location.lng) {
            this.addMapPing(event);
        }

        // Notification & Sound
        if (event.severity === 'CRITICAL' || event.severity === 'HIGH') {
            if (this.audioEnabled) this.playAlert();
            this.showNotification(`INCURSION DETECTED: ${event.service} from ${event.source_ip}`, 'error');
        }
    }

    addMapPing(event) {
        if (!this.map) return;

        const { lat, lng } = event.location;
        const severity = event.severity;
        
        // Create custom ping icon
        const color = severity === 'CRITICAL' ? '#ef4444' : severity === 'HIGH' ? '#f59e0b' : '#00f2ff';
        const pingHtml = `<div class="attack-ping" style="background: ${color}; box-shadow: 0 0 15px ${color}"></div>`;
        
        const icon = L.divIcon({
            html: pingHtml,
            className: 'custom-div-icon',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });

        const marker = L.marker([lat, lng], { icon }).addTo(this.markers);
        
        // Auto-remove marker after 5 seconds
        setTimeout(() => {
            this.markers.removeLayer(marker);
        }, 5000);
    }

    setupEventListeners() {
        const audioBtn = document.getElementById('toggleAudio');
        if (audioBtn) {
            audioBtn.addEventListener('click', () => {
                this.audioEnabled = !this.audioEnabled;
                localStorage.setItem('audio_alerts', this.audioEnabled);
                this.showNotification(`Audio alerts: ${this.audioEnabled ? 'ON' : 'OFF'}`, 'info');
            });
        }
    }

    async refreshData() {
        try {
            await Promise.all([
                this.fetchStats(),
                this.fetchRecentEvents()
            ]);
            this.updateUI();
            this.isInitialLoad = false;
        } catch (error) {
            console.error('[HoneyCloud] Refresh error:', error);
            if (error.status === 401) window.location.href = 'login.html';
        }
    }

    async fetchStats() {
        const response = await fetch(`${this.apiUrl}/api/stats`, {
            headers: this.getAuthHeader()
        });
        if (response.status === 401) window.location.href = 'login.html';
        if (response.ok) {
            this.stats = await response.json();
            this.updateUI();
        }
    }

    async fetchRecentEvents() {
        const response = await fetch(`${this.apiUrl}/api/events?limit=20`, {
            headers: this.getAuthHeader()
        });
        if (response.status === 401) window.location.href = 'login.html';
        if (response.ok) {
            this.events = await response.json();
            // Plot existing events on map (initial load)
            this.events.forEach(ev => {
                if (ev.location && ev.location.lat) this.addMapPing(ev);
            });
        }
    }

    updateUI() {
        if (!this.stats) return;

        this.safeUpdateText('totalEventsCount', this.stats.total_events || 0);
        this.safeUpdateText('criticalCount', this.stats.events_by_severity?.CRITICAL || 0);
        this.safeUpdateText('activeNodes', Object.keys(this.stats.events_by_service || {}).length);
        this.safeUpdateText('lastUpdate', `${new Date().toLocaleTimeString().toUpperCase()}`);
        
        // Additional metrics
        this.safeUpdateText('maliciousCount', this.stats.events_by_severity?.HIGH || 0);
        this.safeUpdateText('sshCount', this.stats.events_by_service?.SSH || 0);
        this.safeUpdateText('httpCount', this.stats.events_by_service?.HTTP || 0);

        // Call specialized UI updates
        this.updateThreatGauge();
        this.updateTopAttacker();
        this.renderEventsFeed();

        if (window.updateCharts) {
            window.updateCharts(this.stats);
        }
    }

    updateThreatGauge() {
        const dial = document.getElementById('threatDial');
        const percentEl = document.getElementById('threatPercent');
        const labelEl = document.getElementById('threatLabel');
        if (!dial || !percentEl || !labelEl || !this.stats) return;

        const total = this.stats.total_events || 0;
        const critical = this.stats.events_by_severity?.CRITICAL || 0;
        const high = this.stats.events_by_severity?.HIGH || 0;
        
        let score = Math.min((total * 2) + (critical * 15) + (high * 5), 100);
        if (total === 0) score = 0;

        const offset = 502 - (502 * (score / 100));
        dial.style.strokeDashoffset = offset;
        percentEl.innerText = `${Math.round(score)}%`;

        if (score > 80) {
            labelEl.innerText = 'CRITICAL RISK';
            labelEl.className = 'text-[10px] font-bold text-red-500 uppercase mt-1';
            dial.style.stroke = '#ef4444';
        } else if (score > 40) {
            labelEl.innerText = 'HIGH ACTIVITY';
            labelEl.className = 'text-[10px] font-bold text-orange-400 uppercase mt-1';
            dial.style.stroke = '#fbbf24';
        } else {
            labelEl.innerText = 'STABLE';
            labelEl.className = 'text-[10px] font-bold text-cyan-400 uppercase mt-1';
            dial.style.stroke = '#06b6d4';
        }
    }

    updateTopAttacker() {
        const card = document.getElementById('topTarget');
        if (!card || !this.events || this.events.length === 0) return;

        const counts = {};
        this.events.forEach(e => counts[e.source_ip] = (counts[e.source_ip] || 0) + 1);
        const topIp = Object.entries(counts).sort((a,b) => b[1] - a[1])[0][0];
        
        card.innerText = topIp;
        card.classList.add('text-red-500');
    }

    renderEventsFeed() {
        const feed = document.getElementById('liveEventsFeed');
        if (!feed) return;
        
        if (this.events.length === 0) {
            feed.innerHTML = `
                <div class="h-full flex flex-col items-center justify-center space-y-4 opacity-50">
                    <div class="text-4xl">🛡️</div>
                    <p class="text-xs uppercase tracking-widest text-center px-8 text-gray-500">Sector Secure.<br>No incursions detected.</p>
                </div>
            `;
            return;
        }

        feed.innerHTML = this.events.slice(0, 15).map(event => {
            const sevColor = event.severity === 'CRITICAL' ? 'text-red-500' : 
                           event.severity === 'HIGH' ? 'text-orange-400' : 'text-cyan-400';
            
            const eventType = event.method && event.endpoint ? `${event.method} ${event.endpoint}` : 
                             event.command ? `CMD: ${event.command}` : 'Incursion Detected';

            const icon = event.severity === 'CRITICAL' ? '🔥' : 
                        event.severity === 'HIGH' ? '⚠️' : '🎯';

            return `
                <div class="p-3 bg-white/5 border border-white/5 rounded-xl flex justify-between items-center group hover:bg-white/10 transition animate-fade-in">
                    <div class="flex items-center gap-3 text-left">
                        <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm border border-white/5 ${sevColor}">
                            ${icon}
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="text-xs font-bold text-white tracking-tight">${eventType}</span>
                                <span class="text-[9px] text-gray-500 font-mono">${event.source_ip}</span>
                            </div>
                            <div class="text-[9px] text-gray-400 uppercase tracking-widest">${event.service || 'UNKNOWN'} | ${new Date(event.timestamp).toLocaleTimeString()}</div>
                        </div>
                    </div>
                    <button onclick="location.href='dashboard.html'" class="text-[10px] text-cyan-400 font-bold uppercase tracking-tighter opacity-0 group-hover:opacity-100 transition px-2">ANALYZE</button>
                </div>
            `;
        }).join('');
    }

    safeUpdateText(id, value) {
        const el = document.getElementById(id);
        if (el) {
            if (typeof value === 'number' && !this.isInitialLoad) {
                this.animateValue(el, parseInt(el.textContent) || 0, value, 500);
            } else {
                el.textContent = value;
            }
        }
    }

    animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) window.requestAnimationFrame(step);
        };
        window.requestAnimationFrame(step);
    }

    playAlert() {
        this.alertSound.play().catch(e => {});
    }

    showNotification(message, type = 'info') {
        if (window.showNotification) window.showNotification(message, type);
    }
}

window.addEventListener('load', () => {
    const honey = new HoneyDashboard({
        API_URL: window.CONFIG ? CONFIG.API_BASE : 'http://localhost:8000',
        INTERVAL: 2000 // 2 second rapid refresh rate
    });
    window.honey = honey;
    honey.init();
});
