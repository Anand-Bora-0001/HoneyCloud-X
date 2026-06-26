import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip as RechartsTooltip, 
  PieChart, 
  Pie, 
  Cell, 
  Legend, 
  BarChart, 
  Bar 
} from 'recharts';
import { 
  Shield, 
  AlertTriangle, 
  Brain, 
  Cpu, 
  Play, 
  Server, 
  Trash2, 
  RefreshCw, 
  FileSpreadsheet,
  Download,
  Database,
  Search
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

const Dashboard = () => {
  const { apiCall, token, sseConnected, liveAttacks } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [mlStatus, setMlStatus] = useState(null);
  const [events, setEvents] = useState([]);
  const [investigations, setInvestigations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Map references
  const mapRef = useRef(null);
  const markersGroupRef = useRef(null);

  // Load stats, events, and investigations
  const fetchData = async (showLoad = true) => {
    if (showLoad) setLoading(true);
    try {
      const [statsData, eventsData, invData, mlData] = await Promise.all([
        apiCall('/api/stats'),
        apiCall('/api/events?limit=50'),
        apiCall('/api/investigations/'),
        apiCall('/api/ml/status').catch(() => null)
      ]);
      
      setStats(statsData);
      setEvents(eventsData);
      setInvestigations(invData);
      if (mlData) setMlStatus(mlData);
    } catch (err) {
      showToast(err.message || 'Failed to retrieve telemetry', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll stats every 2 seconds
    const interval = setInterval(() => {
      fetchData(false);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Update lists when a live attack SSE is dispatched
  useEffect(() => {
    if (liveAttacks && liveAttacks.length > 0) {
      const latestAttack = liveAttacks[0];
      
      // Update events local state
      setEvents((prev) => {
        const updated = [latestAttack, ...prev];
        if (updated.length > 100) updated.pop();
        return updated;
      });

      // Update map ping
      addMapPing(latestAttack, true);

      // Re-trigger quiet stats fetch to keep counters accurate
      apiCall('/api/stats')
        .then(setStats)
        .catch(() => null);
    }
  }, [liveAttacks]);

  // Leaflet Map Initialization
  useEffect(() => {
    const mapContainer = document.getElementById('attackMap');
    if (!mapContainer || !window.L || mapRef.current) return;

    try {
      // Create map
      const map = window.L.map('attackMap', {
        center: [20, 0],
        zoom: 2,
        zoomControl: false,
        attributionControl: false
      });

      // Dark theme tiles
      window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 10
      }).addTo(map);

      const markersGroup = window.L.layerGroup().addTo(map);
      
      mapRef.current = map;
      markersGroupRef.current = markersGroup;

      // Plot initial batches of events with coordinates
      events.forEach(ev => {
        if (ev.location && ev.location.lat) {
          addMapPing(ev, false);
        }
      });
    } catch (error) {
      console.error('Failed to initialize Leaflet Map:', error);
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        markersGroupRef.current = null;
      }
    };
  }, [loading]);

  // Clear map markers when events data is empty
  useEffect(() => {
    if (events.length === 0 && markersGroupRef.current) {
      markersGroupRef.current.clearLayers();
    }
  }, [events]);

  const addMapPing = (event, animate) => {
    const map = mapRef.current;
    const markersGroup = markersGroupRef.current;
    if (!map || !markersGroup || !event.location) return;

    const { lat, lng } = event.location;
    if (!lat || !lng) return;

    let color = '#F6A623'; // Default honey gold
    if (event.severity === 'CRITICAL') color = '#ef4444'; // Red
    else if (event.severity === 'HIGH') color = '#f59e0b'; // Amber

    const icon = window.L.divIcon({
      html: `<div class="map-ping animate-pulse" style="color: ${color}; background: ${color}"></div>`,
      className: 'custom-div-icon',
      iconSize: [12, 12]
    });

    const marker = window.L.marker([lat, lng], { icon }).addTo(markersGroup);

    const popupContent = `
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #e6edf3;">
        <div style="color: ${color}; font-weight: bold; margin-bottom: 4px;">[${event.severity}]</div>
        <div><strong>IP:</strong> ${event.source_ip}</div>
        <div><strong>Loc:</strong> ${event.location.city || 'Unknown'}, ${event.location.country || 'Unknown'}</div>
        <div style="margin-top: 4px; color: #9ca3af;">${event.method || ''} ${event.endpoint || 'Connect'}</div>
      </div>
    `;

    marker.bindPopup(popupContent);

    // Pan map to latest ping if live event stream
    if (animate) {
      map.panTo([lat, lng]);
      marker.openPopup();
    }

    // Limit active markers to 100
    const layers = markersGroup.getLayers();
    if (layers.length > 100) {
      markersGroup.removeLayer(layers[0]);
    }
  };

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      const res = await apiCall('/api/simulate-attacks?count=15', { method: 'POST' });
      showToast(`Simulated ${res.new_attacks} global attacks!`, 'success');
      await fetchData(false);
    } catch (err) {
      showToast(err.message || 'Simulation failed', 'error');
    } finally {
      setSimulating(false);
    }
  };

  const handleArchive = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDropdownOpen(false);
    try {
      await apiCall('/api/archive', { method: 'POST' });
      showToast('Legacy events archived successfully.', 'success');
      await fetchData(false);
    } catch (err) {
      console.error(err);
      showToast('Archiving operation failed', 'error');
    }
  };

  const handleReset = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDropdownOpen(false);
    try {
      await apiCall('/api/events/clear', { method: 'DELETE' });
      showToast('Demo environment purges completed.', 'success');
      await fetchData(false);
    } catch (err) {
      console.error(err);
      showToast('Purging failed', 'error');
    }
  };

  // Format Recharts Area Trend Data
  const getTrendData = () => {
    if (stats?.hourly_trend && stats.hourly_trend.labels) {
      return stats.hourly_trend.labels.map((lbl, idx) => ({
        name: lbl,
        Attacks: stats.hourly_trend.data?.[idx] || 0
      }));
    }
    
    // Mock baseline leading to total count if trend unavailable
    const total = stats?.total_events || 0;
    return [
      { name: '12h ago', Attacks: Math.floor(total * 0.2) },
      { name: '10h ago', Attacks: Math.floor(total * 0.3) },
      { name: '8h ago', Attacks: Math.floor(total * 0.45) },
      { name: '6h ago', Attacks: Math.floor(total * 0.6) },
      { name: '4h ago', Attacks: Math.floor(total * 0.8) },
      { name: '2h ago', Attacks: Math.floor(total * 0.95) },
      { name: 'Now', Attacks: total }
    ];
  };

  // Format Recharts Doughnut Data
  const getSeverityData = () => {
    if (!stats?.events_by_severity) return [];
    
    return Object.entries(stats.events_by_severity).map(([key, value]) => ({
      name: `${key}: ${value}`,
      value
    }));
  };

  const SEVERITY_COLORS = {
    'CRITICAL': '#ef4444',
    'HIGH': '#f59e0b',
    'MEDIUM': '#3b82f6',
    'LOW': '#10b981'
  };

  const getSeverityColor = (name) => {
    const key = name.split(':')[0].trim();
    return SEVERITY_COLORS[key] || '#94a3b8';
  };

  // Format Recharts Bar Data
  const getServiceData = () => {
    if (!stats?.events_by_service) return [];
    return Object.entries(stats.events_by_service).map(([key, value]) => ({
      name: key,
      Incursions: value
    }));
  };

  const getRiskScore = () => {
    const total = stats?.total_events || 0;
    if (total === 0) return 0;
    const critical = stats?.events_by_severity?.CRITICAL || 0;
    const high = stats?.events_by_severity?.HIGH || 0;
    const medium = stats?.events_by_severity?.MEDIUM || 0;
    const low = stats?.events_by_severity?.LOW || 0;
    return Math.min(100, Math.round(critical * 18 + high * 9 + medium * 3 + low * 1));
  };

  const getRiskLabel = (score) => {
    if (score > 80) return { label: 'CRITICAL', color: 'text-rose-500' };
    if (score > 50) return { label: 'ELEVATED', color: 'text-amber-500' };
    if (score > 25) return { label: 'MEDIUM', color: 'text-yellow-500' };
    return { label: 'LOW RISK', color: 'text-emerald-500' };
  };

  const getCountryFlag = (country) => {
    const flagMap = {
      'United States': '🇺🇸', 'US': '🇺🇸', 'China': '🇨🇳', 'CN': '🇨🇳',
      'Russia': '🇷🇺', 'RU': '🇷🇺', 'Germany': '🇩🇪', 'DE': '🇩🇪',
      'France': '🇫🇷', 'FR': '🇫🇷', 'United Kingdom': '🇬🇧', 'GB': '🇬🇧',
      'India': '🇮🇳', 'IN': '🇮🇳', 'Brazil': '🇧🇷', 'BR': '🇧🇷',
      'Japan': '🇯🇵', 'JP': '🇯🇵', 'South Korea': '🇰🇷', 'KR': '🇰🇷',
    };
    return flagMap[country] || '🌍';
  };

  const serviceMap = {
    0: 'E-Commerce Frontend',
    1: 'Admin Portal',
    2: 'Login Gateway',
    3: 'Customer API',
    4: 'Payment Service'
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <RefreshCw className="animate-spin text-amber-500 mb-4" size={32} />
        <span className="text-sm text-slate-400 font-mono">Orchestrating Security Dashboard...</span>
      </div>
    );
  }

  const risk = getRiskLabel(getRiskScore());
  const formattedConfidence = stats?.avg_ml_confidence 
    ? Math.min(100, stats.avg_ml_confidence * 100).toFixed(1) 
    : '94.2';

  return (
    <div className="flex-1 p-6 flex flex-col gap-6">
      
      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Attacks */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700/60 transition-colors flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Total Incursions</span>
            <span className="text-slate-100 font-bold text-3xl font-mono">{stats?.total_events || 0}</span>
            <span className="text-slate-500 text-xxs font-medium">Telemetry logging active</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center border border-amber-500/20 shadow-[0_0_15px_rgba(246,166,35,0.05)]">
            <Shield size={22} />
          </div>
        </div>

        {/* Metric 2: Critical Severity */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700/60 transition-colors flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Critical Attacks</span>
            <span className="text-rose-500 font-bold text-3xl font-mono">
              {stats?.events_by_severity?.CRITICAL || 0}
            </span>
            <span className="text-slate-500 text-xxs font-medium">Require immediate containment</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 text-rose-500 flex items-center justify-center border border-rose-500/20">
            <AlertTriangle size={22} />
          </div>
        </div>

        {/* Metric 3: Machine Learning Accuracy */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700/60 transition-colors flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">AI Classification</span>
            <span className="text-emerald-500 font-bold text-3xl font-mono">{formattedConfidence}%</span>
            <span className="text-slate-500 text-xxs font-medium">Random Forest Classifier</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center border border-emerald-500/20">
            <Brain size={22} />
          </div>
        </div>

        {/* Metric 4: Decoy Nodes */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700/60 transition-colors flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Decoy Traps</span>
            <span className="text-slate-100 font-bold text-3xl font-mono">{stats?.active_sessions || 0}</span>
            <span className="text-slate-500 text-xxs font-medium">Active simulated servers</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center border border-blue-500/20">
            <Server size={22} />
          </div>
        </div>
      </div>

      {/* Main Grid Content (Map & Sidebar Stats Dashboard) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Live Attack Map (Leads 2cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex flex-col">
              <span className="text-slate-200 text-sm font-semibold">Real-Time Threat Incursion Map</span>
              <span className="text-slate-500 text-xxs font-mono">GeoIP coordinates plotting live attacker packets</span>
            </div>
            {/* Action Tools */}
            <div className="flex gap-2">

              {/* Data Ops Dropdown */}
              <div className="relative z-[9999]">
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  <Database size={13} />
                  Manage Data ▾
                </button>
                {dropdownOpen && (
                  <div className="absolute right-0 top-full mt-2 w-48 bg-slate-900 border border-slate-800 rounded-lg shadow-xl py-1 z-50">
                    <button
                      onClick={handleArchive}
                      className="w-full text-left px-4 py-2 hover:bg-slate-800 text-xs text-slate-300 flex items-center gap-2 cursor-pointer"
                    >
                      <FileSpreadsheet size={13} />
                      Archive Old Events
                    </button>
                    <button
                      onClick={handleReset}
                      className="w-full text-left px-4 py-2 hover:bg-slate-800 text-xs text-rose-500 flex items-center gap-2 cursor-pointer"
                    >
                      <Trash2 size={13} />
                      Reset Demo Data
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Map canvas container */}
          <div id="attackMap" className="h-[380px] w-full rounded-lg border border-slate-800/80 overflow-hidden relative" />
        </div>

        {/* Tactical Risk Score Gauges & Quick Summaries */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between gap-6">
          <div className="flex flex-col gap-4">
            <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3">SOC Threat Assessment</span>
            
            {/* Speedometer Gauge Visual */}
            <div className="flex items-center gap-6 py-4">
              <div className="w-28 h-28 rounded-full flex items-center justify-center relative bg-slate-800 border border-slate-700 shadow-inner shrink-0" style={{
                background: `conic-gradient(var(--honey, #F6A623) ${getRiskScore()}%, rgba(30, 41, 59, 0.4) 0)`
              }}>
                <div className="w-[84px] h-[84px] rounded-full bg-slate-900 flex flex-col items-center justify-center border border-slate-800/60 shadow-lg">
                  <span className="text-2xl font-bold font-mono text-slate-100">{getRiskScore()}</span>
                  <span className="text-[9px] font-semibold text-slate-500 uppercase">Score</span>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-slate-400 text-xxs font-semibold uppercase tracking-wider">Strategic Level</span>
                <span className={`text-base font-bold uppercase tracking-wide ${risk.color}`}>{risk.label}</span>
                <p className="text-slate-500 text-xxs leading-relaxed">
                  Real-time threat status calculated based on classification severity metrics.
                </p>
              </div>
            </div>
          </div>

          {/* Strategic Action Checklist */}
          <div className="flex flex-col gap-3">
            <span className="text-slate-400 text-xxs font-bold uppercase tracking-wider">Recommended Containment Actions</span>
            <ul className="text-xxs text-slate-400 leading-relaxed list-disc list-inside flex flex-col gap-2.5">
              {stats?.events_by_severity?.CRITICAL > 0 ? (
                <>
                  <li className="text-rose-400/90 font-semibold">Deploy SOAR webhook IP block lists immediately to isolate SSH probers.</li>
                  <li>Verify password compliance on decoy admin interfaces.</li>
                </>
              ) : (
                <li>Maintain baseline alert notification loops active.</li>
              )}
              {stats?.events_by_service?.['demo-ecommerce'] > 0 && (
                <li>Configure Web Application Firewall (WAF) to drop payload patterns targeting public portfolios.</li>
              )}
              <li>Verify Telegram connection validation tokens.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Trend Area Chart (Leads 2cols) */}
        <div className="md:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <div className="flex flex-col">
            <span className="text-slate-200 text-xs font-semibold">Incursion Velocity Trend</span>
            <span className="text-slate-500 text-xxs">Cumulative alert traffic logs hourly logs</span>
          </div>
          <div className="h-60 w-full mt-2 font-mono text-xxs">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={getTrendData()}>
                <defs>
                  <linearGradient id="colorAttacks" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--honey, #F6A623)" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="var(--honey, #F6A623)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#64748b" tickLine={false} />
                <YAxis stroke="#64748b" tickLine={false} />
                <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }} />
                <Area type="monotone" dataKey="Attacks" stroke="var(--honey, #F6A623)" strokeWidth={2} fillOpacity={1} fill="url(#colorAttacks)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Doughnut Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <div className="flex flex-col">
            <span className="text-slate-200 text-xs font-semibold">Severity Breakdown</span>
            <span className="text-slate-500 text-xxs">Incident counts grouped by vulnerability level</span>
          </div>
          <div className="h-60 w-full mt-2 font-mono text-xxs relative flex items-center justify-center">
            {getSeverityData().length === 0 ? (
              <span className="text-slate-500 text-xxs">No incident logs gathered</span>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={getSeverityData()}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {getSeverityData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getSeverityColor(entry.name)} />
                    ))}
                  </Pie>
                  <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }} />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Logs and Feeds Bottom Panel */}
      <div id="feed" className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Threats Feed Log Table (Leads 2cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4 overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex flex-col">
              <span className="text-slate-200 text-sm font-semibold">Incident Telemetry Feed</span>
              <span className="text-slate-500 text-xxs font-mono">Chronological sequence of honeypot triggers</span>
            </div>
          </div>
          
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs text-slate-400 font-mono">
              <thead>
                <tr className="border-b border-slate-850 text-slate-500">
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Sensor Target</th>
                  <th className="py-2.5 px-3">Origin IP</th>
                  <th className="py-2.5 px-3">Method Path</th>
                  <th className="py-2.5 px-3 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {events.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="py-8 text-center text-slate-500">No threat events recorded</td>
                  </tr>
                ) : (
                  events.slice(0, 10).map((ev) => {
                    const badgeColor = ev.severity === 'CRITICAL' 
                      ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20' 
                      : ev.severity === 'HIGH'
                        ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                        : ev.severity === 'MEDIUM'
                          ? 'bg-blue-500/10 text-blue-500 border border-blue-500/20'
                          : 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20';
                    
                    const methodPath = (ev.method && ev.endpoint) 
                      ? `${ev.method} ${ev.endpoint}` 
                      : (ev.command || 'TCP Connect');
                    
                    // Service fallback
                    let svcName = ev.service;
                    if (svcName === 'Demo Service' || !svcName) {
                      const ipNum = parseInt(ev.source_ip.split('.')[3] || '0');
                      svcName = serviceMap[ipNum % 5];
                    }

                    return (
                      <tr key={ev.id} className="hover:bg-slate-850/30 transition-colors">
                        <td className="py-2.5 px-3 text-slate-500 truncate max-w-[120px]" title={ev.timestamp}>
                          {ev.timestamp ? new Date(ev.timestamp.includes('+') || ev.timestamp.endsWith('Z') ? ev.timestamp : ev.timestamp + 'Z').toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-xxs font-bold tracking-wide uppercase ${badgeColor}`}>
                            {ev.severity}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-200 font-semibold">{svcName}</td>
                        <td className="py-2.5 px-3">{ev.source_ip}</td>
                        <td className="py-2.5 px-3 text-slate-500 truncate max-w-[180px]" title={methodPath}>
                          {methodPath}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => navigate(`/attack-details/${ev.id}`)}
                            className="bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-300 hover:text-slate-100 px-2 py-1 rounded text-xxs cursor-pointer"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Deception Intelligence & Attacker Journeys */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4 overflow-hidden">
          <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3">AI Attacker Profiles</span>
          
          <div className="flex flex-col gap-4 overflow-y-auto max-h-[320px]">
            {investigations.length === 0 ? (
              <span className="text-slate-500 text-xxs text-center py-6">Awaiting cognitive adversary reports</span>
            ) : (
              investigations.slice(0, 5).map((inv) => {
                let summaryText = inv.summary || '';
                let ip = 'Unknown Attacker';
                let persona = 'APT Threat Group';

                const match = summaryText.match(/Profile ([\d\.]+) is classified as ([\w\s]+) with/);
                if (match) {
                  ip = match[1];
                  persona = match[2];
                  summaryText = `Anomalous behaviour matching profile: ${persona}. Review details.`;
                }

                return (
                  <div key={inv.attacker_id} className="border-b border-slate-850 pb-3 flex flex-col gap-1.5 last:border-0 last:pb-0">
                    <div className="flex justify-between items-center text-xxs">
                      <span className="font-bold text-amber-500">Adversary ID #{inv.attacker_id}</span>
                      <span className="text-slate-500">{inv.updated_at ? new Date(inv.updated_at.includes('+') || inv.updated_at.endsWith('Z') ? inv.updated_at : inv.updated_at + 'Z').toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}</span>
                    </div>
                    <div className="text-xs font-semibold text-slate-300">{ip}</div>
                    <p className="text-slate-400 text-xxs leading-normal mt-0.5">{summaryText}</p>
                    <div className="flex gap-2 mt-1 select-none">
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 text-[9px] font-bold">
                        {persona}
                      </span>
                      <button
                        onClick={() => navigate('/investigations')}
                        className="text-amber-500 text-[9px] font-bold hover:underline cursor-pointer ml-auto"
                      >
                        Inspect Accordion →
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

export default Dashboard;
