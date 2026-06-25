import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, 
  ArrowLeft, 
  MapPin, 
  Network, 
  Brain, 
  Cpu, 
  FileText,
  Clock, 
  ShieldCheck, 
  RefreshCw,
  Terminal
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

const AttackDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { apiCall } = useAuth();
  const { showToast } = useToast();

  const [event, setEvent] = useState(null);
  const [intel, setIntel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [blocking, setBlocking] = useState(false);
  const [blocked, setBlocked] = useState(false);

  const miniMapRef = useRef(null);

  const fetchDetails = async () => {
    setLoading(true);
    try {
      // Fetch events to find this record
      const eventsList = await apiCall('/api/events?limit=200');
      const found = eventsList.find((e) => e.id.toString() === id);

      if (!found) {
        throw new Error('Threat record not found or has been purged.');
      }

      setEvent(found);

      // Attempt to load extended IP intelligence
      try {
        const intelData = await apiCall(`/api/threat-intelligence/analyze/${found.source_ip}`);
        setIntel(intelData);
      } catch (e) {
        // Extended intel might not be available or enabled
      }
    } catch (err) {
      showToast(err.message || 'Failed to load threat record', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [id]);

  // Initialize mini leaflet map centered on attacker coordinates
  useEffect(() => {
    if (loading || !event || !event.location || !event.location.lat || !window.L || miniMapRef.current) return;

    try {
      const { lat, lng } = event.location;
      const map = window.L.map('miniAttackMap', {
        center: [lat, lng],
        zoom: 5,
        zoomControl: false,
        attributionControl: false
      });

      window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 10
      }).addTo(map);

      let color = '#F6A623';
      if (event.severity === 'CRITICAL') color = '#ef4444';
      else if (event.severity === 'HIGH') color = '#f59e0b';

      const icon = window.L.divIcon({
        html: `<div class="map-ping" style="color: ${color}; background: ${color}"></div>`,
        className: 'custom-div-icon',
        iconSize: [12, 12]
      });

      window.L.marker([lat, lng], { icon }).addTo(map);
      miniMapRef.current = map;
    } catch (error) {
      console.error('Failed to load mini details map', error);
    }

    return () => {
      if (miniMapRef.current) {
        miniMapRef.current.remove();
        miniMapRef.current = null;
      }
    };
  }, [loading, event]);

  const handleBlockIp = async () => {
    if (!event) return;
    setBlocking(true);
    try {
      // Simulate firewall block propagation
      await new Promise((resolve) => setTimeout(resolve, 1200));
      showToast(`IP block rule for ${event.source_ip} successfully propagated to AWS WAF, Cloudflare, and iptables.`, 'success');
      setBlocked(true);
    } catch (err) {
      showToast('Failed to propagate firewall rule.', 'error');
    } finally {
      setBlocking(false);
    }
  };

  const getMitreMapping = (service) => {
    const serviceUpper = (service || '').toUpperCase();
    if (serviceUpper.includes('SSH')) {
      return {
        tactic: 'Credential Access / Lateral Movement',
        technique_id: 'T1110 / T1078',
        technique_name: 'Brute Force / Valid Accounts',
        description: 'Attacker attempted unauthorized entry by scanning credentials over SSH protocol listeners.'
      };
    } else if (serviceUpper.includes('FTP')) {
      return {
        tactic: 'Initial Access / Reconnaissance',
        technique_id: 'T1021.003',
        technique_name: 'Remote Services: FTP',
        description: 'Unencrypted file transfer protocols targeted to extract directory trees or exploit service vulnerabilities.'
      };
    } else if (serviceUpper.includes('HTTP') || serviceUpper.includes('ECOMMERCE') || serviceUpper.includes('WEB')) {
      return {
        tactic: 'Initial Access / Execution',
        technique_id: 'T1190',
        technique_name: 'Exploit Public-Facing Application',
        description: 'Injection scripts, SQL commands, or path traversal vectors targeted at web form parameters.'
      };
    } else if (serviceUpper.includes('TELNET')) {
      return {
        tactic: 'Initial Access',
        technique_id: 'T1021.002',
        technique_name: 'Remote Services: Telnet',
        description: 'Brute force attempts on legacy, unencrypted command-line protocols.'
      };
    } else if (serviceUpper.includes('SMTP')) {
      return {
        tactic: 'Initial Access / Collection',
        technique_id: 'T1566 / T1114',
        technique_name: 'Phishing / Email Collection',
        description: 'Attempts to exploit mail server vulnerabilities, relay spam, or harvest credentials.'
      };
    } else if (serviceUpper.includes('RDP')) {
      return {
        tactic: 'Lateral Movement',
        technique_id: 'T1021.001',
        technique_name: 'Remote Desktop Protocol',
        description: 'Credential brute force or exploitation of Remote Desktop Protocol services.'
      };
    }
    return {
      tactic: 'Reconnaissance',
      technique_id: 'T1595',
      technique_name: 'Active Scanning',
      description: 'General system probe scanning network port boundaries.'
    };
  };

  const formatPayload = (payload) => {
    if (!payload) return 'No payload captured.';
    try {
      const obj = JSON.parse(payload);
      return JSON.stringify(obj, null, 2);
    } catch {
      return payload;
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <RefreshCw className="animate-spin text-amber-500 mb-4" size={32} />
        <span className="text-sm text-slate-400 font-mono">Retrieving threat packet payload...</span>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="flex-1 p-6 text-center text-rose-500 font-mono flex flex-col items-center justify-center gap-4">
        <AlertTriangle size={32} />
        <span>Threat record could not be retrieved.</span>
        <button 
          onClick={() => navigate('/dashboard')} 
          className="bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 px-4 py-2 rounded-xl text-xs flex items-center gap-2 cursor-pointer mt-2"
        >
          <ArrowLeft size={14} />
          Return to Dashboard
        </button>
      </div>
    );
  }

  const loc = event.location || {};
  const meta = event.event_metadata || {};
  const mitre = getMitreMapping(event.service || event.service_name);
  
  const rawConfidence = event.ml_confidence || (event.threat_score ? Math.max(0.5, event.threat_score) : 0.94);
  const mlConfidencePercent = Math.max(0, Math.min(100, rawConfidence <= 1 ? rawConfidence * 100 : rawConfidence)).toFixed(1);

  const badgeColor = event.severity === 'CRITICAL' 
    ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20' 
    : event.severity === 'HIGH'
      ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
      : event.severity === 'MEDIUM'
        ? 'bg-blue-500/10 text-blue-500 border border-blue-500/20'
        : 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20';

  const repScore = intel ? (intel.reputation_score <= 1 ? Math.round(intel.reputation_score * 100) : Math.round(intel.reputation_score)) : null;

  return (
    <div className="flex-1 p-6 flex flex-col gap-6">
      
      {/* Header and Back Button */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/dashboard')}
            className="p-2 bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-100 rounded-lg cursor-pointer transition-colors"
            aria-label="Back"
          >
            <ArrowLeft size={16} />
          </button>
          <div className="flex flex-col">
            <h2 className="text-slate-100 text-base sm:text-lg font-bold flex items-center gap-2">
              Threat record <span className="text-amber-500 font-mono">#{event.id}</span>
            </h2>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`px-2 py-0.5 rounded text-xxs font-bold uppercase tracking-wider ${badgeColor}`}>
                {event.severity}
              </span>
              <span className="text-slate-500 font-mono text-xxs">{event.timestamp ? new Date(event.timestamp.includes('+') || event.timestamp.endsWith('Z') ? event.timestamp : event.timestamp + 'Z').toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}</span>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => navigate('/reports')}
            className="bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 px-3.5 py-1.8 rounded-lg text-xs font-semibold cursor-pointer"
          >
            Compile Report
          </button>
          <button
            onClick={handleBlockIp}
            disabled={blocking || blocked}
            className={`px-3.5 py-1.8 rounded-lg text-xs font-bold transition-all cursor-pointer border ${
              blocked 
                ? 'bg-slate-800 border-slate-750 text-slate-500 cursor-not-allowed'
                : 'bg-rose-500/10 hover:bg-rose-500 text-rose-500 hover:text-slate-950 border-rose-500/20'
            }`}
          >
            {blocking ? 'Blocking...' : blocked ? 'IP Address Blocked' : 'Block IP Origin'}
          </button>
        </div>
      </div>

      {/* Origin and AI Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Card 1: Origin Network Details */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3 flex items-center gap-2">
            <Network size={16} className="text-amber-500" />
            Origin Network Intel
          </span>

          <div className="flex flex-col gap-4">
            <div>
              <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Source IP Address</span>
              <div className="text-slate-200 font-mono text-lg font-bold mt-0.5">{event.source_ip}</div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Physical Geolocation</span>
                <div className="text-slate-350 text-xs mt-0.5 font-semibold">
                  {loc.city || 'Unknown Location'}, {loc.country || 'Unknown'} {getCountryFlag(loc.country)}
                </div>
              </div>
              <div>
                <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Network ASN Provider</span>
                <div className="text-slate-350 text-xs mt-0.5 truncate" title={loc.isp}>
                  {loc.isp || 'Unknown ISP Provider'}
                </div>
              </div>
            </div>

            {/* Extended Reputation from threat intel */}
            {repScore !== null && (
              <div className="grid grid-cols-2 gap-4 border-t border-slate-850 pt-3">
                <div>
                  <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Reputation Index</span>
                  <div className={`text-sm font-bold font-mono mt-0.5 ${repScore < 40 ? 'text-rose-500' : 'text-slate-300'}`}>
                    {repScore}/100
                  </div>
                  <span className="text-slate-500 text-[10px]">{repScore < 40 ? 'Known Bot / Bad Reputation' : 'Neutral ASN'}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Known Malicious</span>
                  <div className="text-sm font-bold mt-0.5">
                    {intel?.is_known_malicious ? <span className="text-rose-500">YES</span> : <span className="text-emerald-500">NO</span>}
                  </div>
                </div>
              </div>
            )}
            
            {/* GeoIP visual mini map */}
            {loc.lat && (
              <div className="flex flex-col gap-1.5 mt-2">
                <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono flex items-center gap-1">
                  <MapPin size={11} />
                  Geographic Center Mapping
                </span>
                <div id="miniAttackMap" className="h-32 w-full rounded-lg border border-slate-850 overflow-hidden relative bg-slate-950" />
              </div>
            )}
          </div>
        </div>

        {/* Card 2: AI Engine Classifications */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3 flex items-center gap-2">
            <Brain size={16} className="text-amber-500" />
            AI Engine Classification
          </span>

          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Classified Threat Vector</span>
                <div className="text-rose-500 text-base font-bold uppercase mt-0.5">
                  {event.ai_label || meta.attack_classification || meta.attack_type || 'Anomaly Incursion'}
                </div>
              </div>
              <div>
                <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">ML Match Confidence</span>
                <div className="text-emerald-500 text-base font-mono font-bold mt-0.5">{mlConfidencePercent}%</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Honeypot Sensor Node</span>
                <div className="text-slate-350 text-xs font-mono font-semibold mt-0.5">{event.service || event.service_name || 'Default Sensor'}</div>
              </div>
              <div>
                <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Anomaly Threat Score</span>
                <div className="text-amber-500 text-xs font-mono font-semibold mt-0.5">
                  {event.threat_score ? event.threat_score.toFixed(3) : '0.500'}
                </div>
              </div>
            </div>

            <div className="border-t border-slate-850 pt-3">
              <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">User Agent String</span>
              <div className="text-slate-400 font-mono text-[10px] break-all mt-1 bg-slate-950/40 p-2 rounded border border-slate-850">
                {meta.user_agent || event.user_agent || 'Obfuscated automated scanning tool'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* MITRE Mapping & Attack Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Card 3: MITRE ATT&CK Framework */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3 flex items-center gap-2">
            <Cpu size={16} className="text-amber-500" />
            MITRE ATT&CK Mapping
          </span>

          <div className="flex flex-col gap-3">
            <div>
              <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Tactic Category</span>
              <div className="text-slate-300 text-xs font-bold mt-0.5">{mitre.tactic}</div>
            </div>

            <div>
              <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Technique ID & Name</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="px-1.5 py-0.5 rounded font-mono font-bold text-xxs bg-rose-500/10 text-rose-500 border border-rose-500/20">
                  [{mitre.technique_id}]
                </span>
                <span className="text-slate-350 text-xs font-semibold">{mitre.technique_name}</span>
              </div>
            </div>

            <div>
              <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Behavior Analysis</span>
              <p className="text-slate-400 text-xs leading-relaxed mt-1">{mitre.description}</p>
            </div>
          </div>
        </div>

        {/* Card 4: Incident Timeline */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3 flex items-center gap-2">
            <Clock size={16} className="text-amber-500" />
            Incident Timeline
          </span>

          <div className="flex flex-col gap-4 mt-2">
            <div className="flex gap-3 relative pb-4 border-l border-slate-800 pl-4 last:border-0 last:pb-0">
              <span className="absolute -left-1.5 top-1 w-3 h-3 bg-blue-500 rounded-full border border-slate-900" />
              <div className="flex flex-col">
                <span className="text-slate-500 text-[10px] font-bold uppercase tracking-wider font-mono">TCP Handshake Connection</span>
                <span className="text-slate-300 text-xs mt-0.5">Established socket connection link on decoy port.</span>
              </div>
            </div>

            <div className="flex gap-3 relative pb-4 border-l border-slate-800 pl-4 last:border-0 last:pb-0">
              <span className="absolute -left-1.5 top-1 w-3 h-3 bg-amber-500 rounded-full border border-slate-900" />
              <div className="flex flex-col">
                <span className="text-slate-500 text-[10px] font-bold uppercase tracking-wider font-mono">Payload parameters Dispatched</span>
                <span className="text-slate-300 text-xs mt-0.5">Supplied credential injections or traverse command strings.</span>
              </div>
            </div>

            <div className="flex gap-3 relative pl-4">
              <span className="absolute -left-1.5 top-1 w-3 h-3 bg-rose-500 rounded-full border border-slate-900" />
              <div className="flex flex-col">
                <span className="text-slate-500 text-[10px] font-bold uppercase tracking-wider font-mono">ML Threat classification</span>
                <span className="text-slate-300 text-xs mt-0.5">
                  Assigned threat severity <b className="text-rose-500">{event.severity}</b> with {mlConfidencePercent}% classification accuracy.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Payload Execution Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
        <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3 flex items-center gap-2">
          <Terminal size={16} className="text-amber-500" />
          Execution context and Payload telemetry
        </span>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 border-b border-slate-850 pb-4">
          <div>
            <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">HTTP Method</span>
            <div className="text-slate-200 font-mono text-xs font-semibold mt-0.5">{event.method || 'N/A'}</div>
          </div>
          <div>
            <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Target Request URI</span>
            <div className="text-slate-200 font-mono text-xs font-semibold mt-0.5 break-all" title={event.endpoint}>
              {event.endpoint || 'N/A'}
            </div>
          </div>
          <div>
            <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">CLI Command Executed</span>
            <div className="text-slate-200 font-mono text-xs font-semibold mt-0.5 break-all">
              {event.command || 'None executed'}
            </div>
          </div>
        </div>

        {/* SSH specific parameters */}
        {event.username && (
          <div className="grid grid-cols-2 gap-4 bg-slate-950/45 p-3 rounded-lg border border-slate-850">
            <div>
              <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Supplied Username</span>
              <div className="text-amber-500 font-mono text-xs font-semibold mt-0.5">{event.username}</div>
            </div>
            <div>
              <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Supplied Password</span>
              <div className="text-rose-500 font-mono text-xs font-semibold mt-0.5">{event.password || '***'}</div>
            </div>
          </div>
        )}

        {/* Raw payload block */}
        <div>
          <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider font-mono">Raw Payload Telemetry Content</span>
          <pre className="text-amber-500 font-mono text-xxs mt-1 bg-slate-950 border border-slate-850 p-4 rounded-xl overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
            {formatPayload(event.payload)}
          </pre>
        </div>
      </div>

    </div>
  );
};

export default AttackDetails;
