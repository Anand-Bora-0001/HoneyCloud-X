import React, { useState, useEffect } from 'react';
import { Search, ChevronDown, ChevronUp, FileText, Download, Fingerprint, Calendar, ShieldAlert, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

const Investigations = () => {
  const { apiCall, token } = useAuth();
  const { showToast } = useToast();
  
  const [investigations, setInvestigations] = useState([]);
  const [details, setDetails] = useState({}); // Stores detailed report by attacker_id
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState({});

  const loadInvestigations = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/investigations/');
      setInvestigations(data);
    } catch (err) {
      showToast(err.message || 'Failed to fetch investigations list', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvestigations();
  }, []);

  const toggleAccordion = async (attackerId) => {
    if (expandedId === attackerId) {
      setExpandedId(null);
      return;
    }

    setExpandedId(attackerId);

    // Fetch details if not already loaded
    if (!details[attackerId]) {
      setDetailsLoading((prev) => ({ ...prev, [attackerId]: true }));
      try {
        const reportDetails = await apiCall(`/api/investigations/${attackerId}`);
        setDetails((prev) => ({ ...prev, [attackerId]: reportDetails }));
      } catch (err) {
        showToast(`Failed to retrieve profile details for Adversary #${attackerId}`, 'error');
      } finally {
        setDetailsLoading((prev) => ({ ...prev, [attackerId]: false }));
      }
    }
  };

  const getSeverityBadge = (mitreMapping) => {
    if (!mitreMapping) return 'bg-blue-500/10 text-blue-500 border border-blue-500/20';
    const keys = Object.keys(mitreMapping).join(' ').toUpperCase();
    if (keys.includes('T1190') || keys.includes('EXPLOIT')) {
      return 'bg-rose-500/10 text-rose-500 border border-rose-500/20';
    }
    if (keys.includes('T1110') || keys.includes('BRUTE')) {
      return 'bg-amber-500/10 text-amber-500 border border-amber-500/20';
    }
    return 'bg-blue-500/10 text-blue-500 border border-blue-500/20';
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <Fingerprint className="animate-spin text-amber-500 mb-4" size={32} />
        <span className="text-sm text-slate-400 font-mono">Loading adversary database...</span>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 flex flex-col gap-6">
      
      {/* Title block */}
      <div className="flex flex-col gap-1 border-b border-slate-800 pb-4">
        <h2 className="text-slate-100 text-lg font-bold">Cognitive Adversary Profiles</h2>
        <p className="text-slate-400 text-xs">
          Advanced profiles aggregated by honeypot telemetry and classified by machine learning models.
        </p>
      </div>

      {/* Accordion container */}
      <div className="flex flex-col gap-4">
        {investigations.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500">
            No adversary investigations active. Wait for honeypot alert triggers or simulate traffic.
          </div>
        ) : (
          investigations.map((inv) => {
            const isExpanded = expandedId === inv.attacker_id;
            const itemDetails = details[inv.attacker_id];
            const isItemLoading = detailsLoading[inv.attacker_id];
            
            // Format title
            let summaryText = inv.summary || '';
            let ip = 'Unknown Adversary';
            let persona = 'APT Threat Group';

            const match = summaryText.match(/Profile ([\d\.]+) is classified as ([\w\s]+) with/);
            if (match) {
              ip = match[1];
              persona = match[2];
              summaryText = `The actor at IP origin ${ip} performed anomalous behavior patterns consistent with a ${persona} profile. Behavior indicates targeted activity requiring immediate SOC review.`;
            }

            return (
              <div 
                key={inv.attacker_id}
                className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-750 transition-colors shadow-lg"
              >
                {/* Accordion Header */}
                <div 
                  onClick={() => toggleAccordion(inv.attacker_id)}
                  className="px-5 py-4 flex items-center justify-between cursor-pointer select-none bg-slate-900/40 hover:bg-slate-850/20"
                >
                  <div className="flex items-center gap-3">
                    <Fingerprint className="text-amber-500 shrink-0" size={20} />
                    <div className="flex flex-col">
                      <span className="text-slate-200 text-sm font-semibold">Report #{inv.attacker_id} — {ip}</span>
                      <span className="text-slate-500 text-xxs font-mono mt-0.5 flex items-center gap-1">
                        <Calendar size={11} />
                        Updated: {inv.updated_at ? new Date(inv.updated_at.includes('+') || inv.updated_at.endsWith('Z') ? inv.updated_at : inv.updated_at + 'Z').toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 rounded text-xxs font-bold uppercase tracking-wider bg-slate-800 border border-slate-700 text-slate-350">
                      {persona}
                    </span>
                    {isExpanded ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
                  </div>
                </div>

                {/* Accordion Content */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-3 border-t border-slate-800/80 bg-slate-950/20 flex flex-col gap-4">
                    {/* Basic Description */}
                    <p className="text-slate-350 text-xs leading-relaxed" dangerouslySetInnerHTML={{ __html: summaryText }} />
                    
                    {/* Dynamic Loader */}
                    {isItemLoading ? (
                      <div className="flex items-center justify-center py-6 gap-2">
                        <RefreshCw className="animate-spin text-amber-500" size={16} />
                        <span className="text-slate-500 text-xxs font-mono">Analyzing intelligence logs...</span>
                      </div>
                    ) : itemDetails ? (
                      <div className="flex flex-col gap-5 mt-2">
                        
                        {/* Narrative grid details */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                          {/* Executive Narrative block */}
                          <div className="bg-slate-900/60 border border-slate-850 rounded-xl p-4 flex flex-col gap-2">
                            <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider">Executive Narrative</span>
                            <p className="text-slate-300 text-xs leading-relaxed">
                              {itemDetails.executive || 'Executive report summary compile in progress.'}
                            </p>
                          </div>

                          {/* Technical impact analysis */}
                          <div className="bg-slate-900/60 border border-slate-850 rounded-xl p-4 flex flex-col gap-2">
                            <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider">Technical Impact Analysis</span>
                            <p className="text-slate-300 text-xs leading-relaxed">
                              {itemDetails.technical || 'Technical analysis compile in progress.'}
                            </p>
                          </div>
                        </div>

                        {/* MITRE Mapping & Attack Paths */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                          {/* MITRE Framework block */}
                          <div className="bg-slate-900/60 border border-slate-850 rounded-xl p-4 flex flex-col gap-3">
                            <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider">MITRE ATT&CK Mapping</span>
                            
                            <div className="flex flex-col gap-2">
                              {itemDetails.mitre_mapping && Object.keys(itemDetails.mitre_mapping).length > 0 ? (
                                Object.entries(itemDetails.mitre_mapping).map(([tid, desc]) => (
                                  <div key={tid} className="bg-slate-950/80 border border-slate-850 rounded-lg p-2.5 flex items-start gap-3">
                                    <span className="bg-rose-500/10 text-rose-500 border border-rose-500/20 px-2 py-0.5 rounded text-xxs font-bold font-mono">
                                      {tid}
                                    </span>
                                    <span className="text-slate-300 text-xxs leading-relaxed font-medium">{desc}</span>
                                  </div>
                                ))
                              ) : (
                                <span className="text-slate-500 text-xxs font-mono">No MITRE ATT&CK matrix mappings logged.</span>
                              )}
                            </div>
                          </div>

                          {/* Attack paths mapping */}
                          <div className="bg-slate-900/60 border border-slate-850 rounded-xl p-4 flex flex-col gap-3">
                            <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider">Attack Paths Progression</span>
                            
                            <div className="flex flex-col gap-2.5 pl-2">
                              {itemDetails.attack_paths && itemDetails.attack_paths.length > 0 ? (
                                itemDetails.attack_paths.map((p, idx) => (
                                  <div key={idx} className="flex flex-col gap-1 text-xxs font-mono border-l-2 border-slate-800 pl-3 ml-1">
                                    <div className="flex items-center gap-2 text-slate-300 font-bold">
                                      <span className="text-emerald-500">{p.from}</span>
                                      <span className="text-slate-500">→</span>
                                      <span className="text-rose-400">{p.to}</span>
                                      <span className="ml-2 px-1.5 py-0.5 bg-slate-800 rounded text-[9px] text-slate-400 tracking-wider uppercase border border-slate-700">{p.action}</span>
                                    </div>
                                    {p.payload && (
                                      <span className="text-slate-500 italic">└ {p.payload}</span>
                                    )}
                                  </div>
                                ))
                              ) : (
                                <span className="text-slate-500 text-xxs font-mono">No advanced path progression sequences.</span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Raw evidence logs */}
                        {itemDetails.evidence && (
                          <div className="bg-slate-950 border border-slate-850 rounded-xl p-4 flex flex-col gap-2">
                            <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider">Evidence Telemetry</span>
                            <pre className="text-amber-500/90 font-mono text-xxs bg-black/20 p-3 rounded border border-slate-900/60 overflow-x-auto leading-relaxed max-h-40 overflow-y-auto whitespace-pre-wrap">
                              {typeof itemDetails.evidence === 'object' ? JSON.stringify(itemDetails.evidence, null, 2) : itemDetails.evidence}
                            </pre>
                          </div>
                        )}

                        {/* Report Export Button Triggers */}
                        <div className="flex items-center gap-3 mt-1.5">
                          <a 
                            href={`/api/investigations/${inv.attacker_id}/report?format=csv`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-350 hover:text-slate-100 px-3.5 py-1.8 rounded-lg text-xs font-semibold flex items-center gap-2 cursor-pointer transition-colors"
                          >
                            <Download size={13} />
                            Export CSV
                          </a>
                          <a 
                            href={`/api/investigations/${inv.attacker_id}/report?format=json`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-350 hover:text-slate-100 px-3.5 py-1.8 rounded-lg text-xs font-semibold flex items-center gap-2 cursor-pointer transition-colors"
                          >
                            <Download size={13} />
                            Export JSON
                          </a>
                        </div>

                      </div>
                    ) : (
                      <div className="text-center py-4 text-xxs text-rose-400/90">
                        Failed to gather adversary profile analysis.
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

    </div>
  );
};

export default Investigations;
