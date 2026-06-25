import React, { useState, useEffect } from 'react';
import { FileText, Download, Send, RefreshCw, AlertTriangle, CheckCircle, Info, FileSpreadsheet } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

const Reports = () => {
  const { apiCall } = useAuth();
  const { showToast } = useToast();

  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [compiling, setCompiling] = useState(false);
  const [compileFormat, setCompileFormat] = useState('pdf');
  const [sendTelegram, setSendTelegram] = useState(false);
  const [archives, setArchives] = useState([]);

  const loadStats = async () => {
    try {
      const data = await apiCall('/api/stats');
      setStats(data);
    } catch (err) {
      showToast('Failed to retrieve statistics', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const getRiskScore = () => {
    const total = stats?.total_events || 0;
    if (total === 0) return 0;
    const critical = stats?.events_by_severity?.CRITICAL || 0;
    const high = stats?.events_by_severity?.HIGH || 0;
    const medium = stats?.events_by_severity?.MEDIUM || 0;
    const low = stats?.events_by_severity?.LOW || 0;
    return Math.min(100, Math.round(critical * 18 + high * 9 + medium * 3 + low * 1));
  };

  const getRiskRating = (score) => {
    if (score > 80) return { label: 'CRITICAL THREAT LEVEL (Active attacks flagged)', color: '#ef4444' };
    if (score > 50) return { label: 'HIGH THREAT LEVEL (Exploit vectors detected)', color: '#f59e0b' };
    if (score > 25) return { label: 'MEDIUM THREAT LEVEL (Reconnaissance scanned)', color: '#eab308' };
    return { label: 'LOW RISK (Operational status secure)', color: '#10b981' };
  };

  const getRecommendations = () => {
    const recs = [];
    const critical = stats?.events_by_severity?.CRITICAL || 0;
    const high = stats?.events_by_severity?.HIGH || 0;
    
    if (critical > 0 || high > 0) {
      recs.push('Deploy SOAR webhook IP block lists immediately to stop active SSH/API probers.');
      recs.push('Verify credential complexity for admin accounts targeted during login scans.');
    }
    if (stats?.events_by_service?.['demo-ecommerce'] > 0 || stats?.events_by_service?.['DEMO_ECOMMERCE'] > 0) {
      recs.push('Enable web application firewall rules (WAF) to drop payload patterns targeting public portals.');
    }
    recs.push('Ensure encrypted syslog stream connectivity is established on all decoy nodes.');
    recs.push('Validate Telegram alert configuration to maintain real-time notify response loops.');
    
    return recs;
  };

  const handleGenerate = async () => {
    setCompiling(true);
    try {
      const res = await apiCall(`/api/reports/generate?format=${compileFormat}&send_telegram=${sendTelegram}`, {
        method: 'POST'
      });

      let downloadUrl = '';
      if (res.status === 'processing') {
        showToast(`Report generation started (Celery task: ${res.task_id})`, 'info');
        downloadUrl = '#';
      } else if (res.status === 'success') {
        showToast(`${compileFormat.toUpperCase()} report compiled successfully!`, 'success');
        downloadUrl = res.download_url;

        // Auto trigger download if browser permits
        if (res.download_url) {
          const downloadLink = document.createElement('a');
          downloadLink.href = res.download_url;
          const fileName = res.download_url.split('file=')[1] || `report.${compileFormat}`;
          downloadLink.download = fileName;
          document.body.appendChild(downloadLink);
          downloadLink.click();
          document.body.removeChild(downloadLink);
        }
      } else {
        showToast(res.message || 'Report compile failed', 'error');
        setCompiling(false);
        return;
      }

      // Add to session compilation list
      setArchives((prev) => [
        {
          timestamp: new Date().toISOString(),
          format: compileFormat.toUpperCase(),
          channel: sendTelegram ? 'Secure Telegram & Local' : 'Local Download Only',
          status: 'Completed',
          download_url: downloadUrl
        },
        ...prev
      ]);
    } catch (err) {
      showToast(`Compilation failed: ${err.message}`, 'error');
    } finally {
      setCompiling(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <RefreshCw className="animate-spin text-amber-500 mb-4" size={32} />
        <span className="text-sm text-slate-400 font-mono">Loading SOC analytics details...</span>
      </div>
    );
  }

  const score = getRiskScore();
  const rating = getRiskRating(score);
  const totalEvents = stats?.total_events || 0;
  const criticalCount = stats?.events_by_severity?.CRITICAL || 0;
  const highCount = stats?.events_by_severity?.HIGH || 0;

  return (
    <div className="flex-1 p-6 flex flex-col gap-6">
      
      {/* Title */}
      <div className="flex flex-col gap-1 border-b border-slate-800 pb-4">
        <h2 className="text-slate-100 text-lg font-bold">Threat Intelligence Reporting Engine</h2>
        <p className="text-slate-400 text-xs">
          Generate production-grade audit reports on current threat vectors and machine learning metrics.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Report configuration (Leads 2cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-5 justify-between">
          <div className="flex flex-col gap-4">
            <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3">Compile Settings</span>
            
            {/* Format Pickers */}
            <div className="flex flex-col gap-2">
              <span className="text-slate-400 text-xxs font-bold uppercase tracking-wider">Report Output Format</span>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setCompileFormat('pdf')}
                  className={`py-4 rounded-xl border flex flex-col items-center gap-2 transition-all cursor-pointer ${
                    compileFormat === 'pdf'
                      ? 'bg-amber-500/10 border-amber-500 text-amber-500'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <FileText size={24} />
                  <span className="text-xs font-bold font-mono">Adobe PDF Document</span>
                </button>
                <button
                  onClick={() => setCompileFormat('excel')}
                  className={`py-4 rounded-xl border flex flex-col items-center gap-2 transition-all cursor-pointer ${
                    compileFormat === 'excel'
                      ? 'bg-amber-500/10 border-amber-500 text-amber-500'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <FileSpreadsheet size={24} />
                  <span className="text-xs font-bold font-mono">Microsoft Excel Sheet</span>
                </button>
              </div>
            </div>

            {/* Telegram Alert Dispatcher option */}
            <label className="flex items-center gap-3 bg-slate-950/40 p-3 rounded-lg border border-slate-850 hover:border-slate-800 transition-colors mt-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={sendTelegram}
                onChange={(e) => setSendTelegram(e.target.checked)}
                className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-amber-500 focus:ring-amber-500/30"
              />
              <div className="flex flex-col">
                <span className="text-slate-350 text-xs font-semibold flex items-center gap-1.5">
                  <Send size={12} />
                  Dispatch Copy to Telegram Channels
                </span>
                <span className="text-slate-500 text-xxs mt-0.5">Sends PDF/Excel binary output to configured bot chat rooms</span>
              </div>
            </label>
          </div>

          <button
            onClick={handleGenerate}
            disabled={compiling}
            className="w-full bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 cursor-pointer shadow-lg transition-all duration-300 disabled:opacity-50 mt-4"
          >
            {compiling ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                <span>Compiling SOC Analytics Report...</span>
              </>
            ) : (
              <>
                <Download size={16} />
                <span>Compile Intelligence Report</span>
              </>
            )}
          </button>
        </div>

        {/* Risk summary right panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-5 justify-between">
          <div className="flex flex-col gap-4">
            <span className="text-slate-200 text-sm font-semibold border-b border-slate-800 pb-3">Strategic Assessment</span>
            
            {/* Risk Index block */}
            <div className="flex flex-col gap-1">
              <span className="text-slate-500 text-xxs font-bold uppercase tracking-wider">Overall Risk Score</span>
              <div className="text-3xl font-extrabold font-mono" style={{ color: rating.color }}>{score}</div>
              <div className="text-xxs font-bold mt-1 uppercase" style={{ color: rating.color }}>{rating.label}</div>
            </div>

            {/* Narrative summary */}
            <div className="bg-slate-950/80 border border-slate-850 p-3 rounded-lg flex gap-2.5 items-start mt-2">
              <Info className="text-blue-500 shrink-0 mt-0.5" size={14} />
              <p className="text-slate-400 text-xxs leading-relaxed">
                SOC telemetry analysis has logged <b className="text-slate-200">{totalEvents}</b> threat events. The machine learning pipeline identified <b className="text-slate-200">{criticalCount} critical</b> and <b className="text-slate-200">{highCount} high-severity</b> incident vectors requiring administrator review.
              </p>
            </div>
          </div>

          {/* Strategy action lists */}
          <div className="flex flex-col gap-2.5">
            <span className="text-slate-400 text-xxs font-bold uppercase tracking-wider">Strategic Recommendations</span>
            <ul className="text-xxs text-slate-400 list-disc list-inside leading-relaxed flex flex-col gap-2">
              {getRecommendations().map((rec, idx) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* History Grid table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
        <div className="flex flex-col">
          <span className="text-slate-200 text-sm font-semibold">Workspace Report Compiles</span>
          <span className="text-slate-500 text-xxs font-mono">Temporary log of files compiled in this browser session</span>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs text-slate-400 font-mono">
            <thead>
              <tr className="border-b border-slate-850 text-slate-500">
                <th className="py-2 px-3">Compiled Timestamp</th>
                <th className="py-2 px-3">Format</th>
                <th className="py-2 px-3">Notification Channel</th>
                <th className="py-2 px-3">Compile Status</th>
                <th className="py-2 px-3 text-right">Download</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-850">
              {archives.length === 0 ? (
                <tr>
                  <td colSpan="5" className="py-6 text-center text-slate-500">No reports compiled in this session</td>
                </tr>
              ) : (
                archives.map((arch, idx) => (
                  <tr key={idx} className="hover:bg-slate-850/20 transition-colors">
                    <td className="py-2.5 px-3 text-slate-500">{arch.timestamp ? new Date(arch.timestamp.includes('+') || arch.timestamp.endsWith('Z') ? arch.timestamp : arch.timestamp + 'Z').toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-xxs font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20">
                        {arch.format}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">{arch.channel}</td>
                    <td className="py-2.5 px-3 text-emerald-500 font-semibold">{arch.status}</td>
                    <td className="py-2.5 px-3 text-right">
                      {arch.download_url !== '#' ? (
                        <a 
                          href={arch.download_url} 
                          download 
                          className="bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-350 hover:text-slate-100 px-2 py-1 rounded text-xxs cursor-pointer"
                        >
                          Download File
                        </a>
                      ) : (
                        <span className="text-slate-500 text-xxs">Task Pending</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

export default Reports;
