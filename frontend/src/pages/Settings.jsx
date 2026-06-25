import React, { useState, useEffect } from 'react';
import { 
  User, 
  Cpu, 
  Bell, 
  Sliders, 
  Plus, 
  Eye, 
  EyeOff, 
  Copy, 
  RefreshCw, 
  Check, 
  AlertCircle,
  Mail,
  Send,
  Save
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

const Settings = () => {
  const { apiCall } = useAuth();
  const { showToast } = useToast();

  const [activeTab, setActiveTab] = useState('decoys');
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  // Decoy Sensors state
  const [sensors, setSensors] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [newSensor, setNewSensor] = useState({ name: '', service_type: 'ssh', description: '' });
  const [visibleKeys, setVisibleKeys] = useState({}); // { id: boolean }

  // Telegram state
  const [tgConfig, setTgConfig] = useState({ configured: false, chat_id: '', bot_token_set: false });
  const [tgToken, setTgToken] = useState('');
  const [tgChat, setTgChat] = useState('');
  const [tgValidated, setTgValidated] = useState(false);

  // SMTP Email state
  const [emailAddress, setEmailAddress] = useState('');
  const [smtpLog, setSmtpLog] = useState('');
  const [smtpLogOpen, setSmtpLogOpen] = useState(false);

  // Preferences state
  const [prefs, setPrefs] = useState({
    telegram_enabled: false,
    email_enabled: false,
    alert_on_critical: true,
    alert_on_high: false,
    daily_summary_enabled: false,
    weekly_report_enabled: false
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileData, sensorsData, tgConfigData, prefsData] = await Promise.all([
        apiCall('/auth/me'),
        apiCall('/api/saas/services'),
        apiCall('/api/telegram/config'),
        apiCall('/api/alerts/config')
      ]);

      setProfile(profileData);
      setSensors(sensorsData);
      setTgConfig(tgConfigData);
      setPrefs({
        telegram_enabled: prefsData.telegram_enabled || false,
        email_enabled: prefsData.email_enabled || false,
        alert_on_critical: prefsData.alert_on_critical && !prefsData.alert_on_high,
        alert_on_high: prefsData.alert_on_critical && prefsData.alert_on_high,
        daily_summary_enabled: prefsData.daily_summary_enabled || false,
        weekly_report_enabled: prefsData.weekly_report_enabled || false
      });

      if (tgConfigData.configured) {
        setTgChat(tgConfigData.chat_id || '');
      }

      if (prefsData.saved_emails && prefsData.saved_emails.length > 0) {
        setEmailAddress(prefsData.saved_emails[0]);
      }
    } catch (err) {
      showToast('Failed to load settings configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // --- Decoys Management ---
  const handleToggleKey = (id) => {
    setVisibleKeys((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopyKey = (key) => {
    navigator.clipboard.writeText(key)
      .then(() => showToast('Sensor API Key copied to clipboard', 'success'))
      .catch(() => showToast('Failed to copy key', 'error'));
  };

  const handleCreateSensor = async (e) => {
    e.preventDefault();
    if (!newSensor.name.trim()) {
      showToast('Decoy name is required', 'warning');
      return;
    }

    try {
      await apiCall('/api/saas/services', {
        method: 'POST',
        body: JSON.stringify({
          name: newSensor.name.trim(),
          service_type: newSensor.service_type,
          description: newSensor.description.trim()
        })
      });
      showToast('Decoy sensor registered successfully!', 'success');
      setModalOpen(false);
      setNewSensor({ name: '', service_type: 'ssh', description: '' });
      // reload sensors
      const sensorsData = await apiCall('/api/saas/services');
      setSensors(sensorsData);
    } catch (err) {
      showToast(err.message || 'Sensor registration failed', 'error');
    }
  };

  const handleRegenerateKey = async (id) => {
    if (!window.confirm('Regenerate credentials key? Legacy sensors using the old key will lock out immediately.')) return;
    try {
      const res = await apiCall(`/api/saas/services/${id}/regenerate-key`, { method: 'POST' });
      showToast(`Credentials key regenerated for ${res.name}`, 'success');
      const sensorsData = await apiCall('/api/saas/services');
      setSensors(sensorsData);
    } catch (err) {
      showToast(err.message || 'Key regeneration failed', 'error');
    }
  };

  const handleDeleteSensor = async (id) => {
    if (!window.confirm('Deactivate decoy sensor? Action is permanent.')) return;
    try {
      await apiCall(`/api/saas/services/${id}`, { method: 'DELETE' });
      showToast('Decoy sensor deactivated successfully', 'success');
      const sensorsData = await apiCall('/api/saas/services');
      setSensors(sensorsData);
    } catch (err) {
      showToast(err.message || 'Deactivation failed', 'error');
    }
  };

  // --- Telegram Integration ---
  const handleValidateTelegram = async () => {
    if (!tgToken || !tgChat) {
      showToast('Bot Token and Chat ID are required for validation', 'warning');
      return;
    }
    try {
      const res = await apiCall('/api/telegram/validate', {
        method: 'POST',
        body: JSON.stringify({ bot_token: tgToken, chat_id: tgChat })
      });
      showToast(`Verified bot @${res.bot_username}`, 'success');
      setTgValidated(true);
    } catch (err) {
      showToast(err.message || 'Telegram bot validation failed', 'error');
      setTgValidated(false);
    }
  };

  const handleSaveTelegram = async () => {
    try {
      await apiCall('/api/telegram/configure', {
        method: 'POST',
        body: JSON.stringify({ bot_token: tgToken, chat_id: tgChat })
      });
      showToast('Telegram integration configured successfully', 'success');
      setTgValidated(false);
      setTgToken('');
      // Reload config
      const tgConfigData = await apiCall('/api/telegram/config');
      setTgConfig(tgConfigData);
    } catch (err) {
      showToast(err.message || 'Telegram configure failed', 'error');
    }
  };

  const handleTestTelegram = async () => {
    try {
      await apiCall('/api/alerts/test-telegram', { method: 'POST' });
      showToast('Test alert dispatched to Telegram bot chat room', 'success');
    } catch (err) {
      try {
        await apiCall('/api/telegram/test', { method: 'POST' });
        showToast('Test alert dispatched to Telegram bot chat room', 'success');
      } catch (err2) {
        showToast(err.message || err2.message || 'Telegram test failed', 'error');
      }
    }
  };

  // --- SMTP Email Integration ---
  const handleTestEmail = async () => {
    if (!emailAddress) {
      showToast('Enter a destination email address', 'warning');
      return;
    }

    setSmtpLog('');
    setSmtpLogOpen(false);
    showToast('Dispatching SMTP test alert...', 'info');

    try {
      const res = await apiCall('/api/alerts/test-email', {
        method: 'POST',
        body: JSON.stringify({ email_address: emailAddress, save_email: true })
      });

      if (res.status === 'success') {
        showToast('Email delivered successfully.', 'success');
      } else {
        showToast('Email delivery failed.', 'error');
        setSmtpLog(`Error: ${res.message}\nDetails: ${res.details || 'N/A'}`);
        setSmtpLogOpen(true);
      }
    } catch (err) {
      showToast('Email delivery failed.', 'error');
      setSmtpLog(`Exception: ${err.message}`);
      setSmtpLogOpen(true);
    }
  };

  // --- Preferences ---
  const handleSavePrefs = async () => {
    const payload = {
      telegram_enabled: prefs.telegram_enabled,
      email_enabled: prefs.email_enabled,
      alert_on_critical: true,
      alert_on_high: prefs.alert_on_high,
      alert_on_medium: false,
      alert_on_low: false,
      daily_summary_enabled: prefs.daily_summary_enabled,
      weekly_report_enabled: prefs.weekly_report_enabled,
      saved_emails: emailAddress ? [emailAddress] : []
    };

    try {
      await apiCall('/api/alerts/config', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      showToast('Notification preferences updated successfully', 'success');
    } catch (err) {
      showToast('Failed to save preferences', 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh]">
        <RefreshCw className="animate-spin text-amber-500 mb-4" size={32} />
        <span className="text-sm text-slate-400 font-mono">Loading config menus...</span>
      </div>
    );
  }

  const tabs = [
    { id: 'decoys', label: 'Decoy Sensors', icon: Cpu },
    { id: 'notifications', label: 'Alert Integrations', icon: Bell },
    { id: 'preferences', label: 'System Preferences', icon: Sliders },
    { id: 'profile', label: 'Operator Profile', icon: User }
  ];

  return (
    <div className="flex-1 p-6 flex flex-col gap-6">
      
      {/* Title */}
      <div className="flex flex-col gap-1 border-b border-slate-800 pb-4">
        <h2 className="text-slate-100 text-lg font-bold">Platform settings</h2>
        <p className="text-slate-400 text-xs">
          Manage integrations alerts, registered sensors keys, and SOC dashboard preferences.
        </p>
      </div>

      {/* Tabs Menu Header */}
      <div className="flex border-b border-slate-800 gap-1 overflow-x-auto select-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-3 text-xs font-semibold flex items-center gap-2 border-b-2 cursor-pointer transition-all ${
                activeTab === tab.id
                  ? 'border-amber-500 text-amber-500'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content Panel */}
      <div className="flex flex-col gap-6">
        
        {/* TAB 1: Decoys Sensors */}
        {activeTab === 'decoys' && (
          <div className="flex flex-col gap-5">
            <div className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-slate-200 text-sm font-semibold">Active Decoy Sensors</span>
                <span className="text-slate-500 text-xxs font-mono">Sensors registered on the SaaS architecture</span>
              </div>
              <button
                onClick={() => setModalOpen(true)}
                className="bg-amber-500 hover:bg-amber-400 text-slate-950 px-3.5 py-1.8 rounded-lg text-xs font-bold flex items-center gap-1.5 cursor-pointer shadow-lg"
              >
                <Plus size={14} />
                Register Decoy Node
              </button>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="overflow-x-auto w-full">
                <table className="w-full text-left text-xs text-slate-400 font-mono">
                  <thead>
                    <tr className="border-b border-slate-850 text-slate-500">
                      <th className="py-2.5 px-3">Decoy Target Name</th>
                      <th className="py-2.5 px-3">Type</th>
                      <th className="py-2.5 px-3">API Token Key</th>
                      <th className="py-2.5 px-3">Created At</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {sensors.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="py-8 text-center text-slate-500">No decoys nodes active. Register one above.</td>
                      </tr>
                    ) : (
                      sensors.map((svc) => (
                        <tr key={svc.id} className="hover:bg-slate-850/20 transition-colors">
                          <td className="py-2.5 px-3 text-slate-200 font-semibold">{svc.name}</td>
                          <td className="py-2.5 px-3">
                            <span className="px-1.5 py-0.5 rounded text-xxs font-bold uppercase tracking-wider bg-slate-800 border border-slate-700 text-slate-400">
                              {svc.service_type}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            <div className="flex items-center gap-2">
                              <input
                                type={visibleKeys[svc.id] ? 'text' : 'password'}
                                value={svc.api_key}
                                readOnly
                                className="bg-slate-950 border border-slate-850 text-xxs text-amber-500 font-mono px-2 py-1 rounded w-44 focus:outline-none select-all"
                              />
                              <button
                                onClick={() => handleToggleKey(svc.id)}
                                className="text-slate-400 hover:text-slate-200 cursor-pointer"
                                title="Toggle Visibility"
                              >
                                {visibleKeys[svc.id] ? <EyeOff size={13} /> : <Eye size={13} />}
                              </button>
                              <button
                                onClick={() => handleCopyKey(svc.api_key)}
                                className="text-slate-400 hover:text-slate-200 cursor-pointer"
                                title="Copy Key"
                              >
                                <Copy size={13} />
                              </button>
                            </div>
                          </td>
                          <td className="py-2.5 px-3 text-slate-500">{svc.created_at ? new Date(svc.created_at.includes('+') || svc.created_at.endsWith('Z') ? svc.created_at : svc.created_at + 'Z').toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}</td>
                          <td className="py-2.5 px-3 text-right flex justify-end gap-2">
                            <button
                              onClick={() => handleRegenerateKey(svc.id)}
                              className="bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-350 hover:text-slate-100 px-2 py-1 rounded text-xxs cursor-pointer"
                            >
                              Regenerate
                            </button>
                            <button
                              onClick={() => handleDeleteSensor(svc.id)}
                              className="bg-slate-800 hover:bg-rose-500/10 text-slate-350 hover:text-rose-500 border border-slate-700 hover:border-rose-500/20 px-2 py-1 rounded text-xxs cursor-pointer"
                            >
                              Deactivate
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: Alert Integrations */}
        {activeTab === 'notifications' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Telegram Setup Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-slate-200 text-sm font-semibold flex items-center gap-1.5">
                  <Send size={15} className="text-blue-500" />
                  Telegram Notifications
                </span>
                {tgConfig.configured && (
                  <span className="px-2 py-0.5 rounded text-xxs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                    Bot Active
                  </span>
                )}
              </div>

              <div className="flex flex-col gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400 text-xxs font-semibold uppercase tracking-wider">Bot Token ID</label>
                  <input
                    type="password"
                    value={tgToken}
                    onChange={(e) => setTgToken(e.target.value)}
                    placeholder={tgConfig.bot_token_set ? '••••••••••••••••••••••••••••••••' : 'Enter Bot Token'}
                    className="bg-slate-950 border border-slate-800 text-slate-200 text-xs px-3.5 py-2.5 rounded-xl font-mono focus:outline-none focus:border-amber-500/50"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-slate-400 text-xxs font-semibold uppercase tracking-wider">Chat Room ID</label>
                  <input
                    type="text"
                    value={tgChat}
                    onChange={(e) => setTgChat(e.target.value)}
                    placeholder="e.g. -100123456789"
                    className="bg-slate-950 border border-slate-800 text-slate-200 text-xs px-3.5 py-2.5 rounded-xl font-mono focus:outline-none focus:border-amber-500/50"
                  />
                </div>
              </div>

              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleValidateTelegram}
                  className="bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 px-3.5 py-1.8 rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Verify Token
                </button>
                <button
                  onClick={handleSaveTelegram}
                  disabled={!tgValidated}
                  className="bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-bold px-3.5 py-1.8 rounded-lg text-xs cursor-pointer disabled:opacity-40"
                >
                  Save Integration
                </button>
                <button
                  onClick={handleTestTelegram}
                  disabled={!tgConfig.configured}
                  className="bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 px-3.5 py-1.8 rounded-lg text-xs font-semibold cursor-pointer disabled:opacity-40 ml-auto"
                >
                  Dispatch Test Msg
                </button>
              </div>
            </div>

            {/* Email Setup Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-slate-200 text-sm font-semibold flex items-center gap-1.5">
                  <Mail size={15} className="text-blue-500" />
                  SMTP Email Alerts
                </span>
              </div>

              <div className="flex flex-col gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400 text-xxs font-semibold uppercase tracking-wider">Destination Email Address</label>
                  <input
                    type="email"
                    value={emailAddress}
                    onChange={(e) => setEmailAddress(e.target.value)}
                    placeholder="soc_admin@domain.com"
                    className="bg-slate-950 border border-slate-800 text-slate-200 text-xs px-3.5 py-2.5 rounded-xl font-mono focus:outline-none focus:border-amber-500/50"
                  />
                </div>
              </div>

              <div className="flex gap-2 mt-2 justify-between">
                <button
                  onClick={handleTestEmail}
                  className="bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 px-3.5 py-1.8 rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Test Delivery
                </button>
              </div>

              {smtpLogOpen && (
                <div className="bg-slate-950 border border-slate-850 p-3 rounded-lg flex flex-col gap-2 mt-2 animate-fade-in">
                  <span className="text-slate-500 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                    <AlertCircle size={12} className="text-rose-500" />
                    Delivery Log trace
                  </span>
                  <pre className="text-rose-400 font-mono text-xxs overflow-x-auto whitespace-pre-wrap leading-normal bg-black/10 p-2 rounded">
                    {smtpLog}
                  </pre>
                </div>
              )}
            </div>

          </div>
        )}

        {/* TAB 3: System Preferences */}
        {activeTab === 'preferences' && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-slate-200 text-sm font-semibold">Incident notification Routing criteria</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-1">
              
              {/* Integration Switches */}
              <div className="flex flex-col gap-4">
                <span className="text-slate-400 text-xxs font-bold uppercase tracking-wider border-b border-slate-850 pb-2">Active Notifications Channels</span>
                
                <label className="flex items-center justify-between p-2 hover:bg-slate-850/20 rounded-lg cursor-pointer">
                  <span className="text-xs text-slate-350 font-semibold">Telegram Bot Dispatcher</span>
                  <input
                    type="checkbox"
                    checked={prefs.telegram_enabled}
                    onChange={(e) => setPrefs((prev) => ({ ...prev, telegram_enabled: e.target.checked }))}
                    className="w-4.5 h-4.5 rounded text-amber-500 bg-slate-950 border-slate-800 focus:ring-amber-500/30"
                  />
                </label>

                <label className="flex items-center justify-between p-2 hover:bg-slate-850/20 rounded-lg cursor-pointer">
                  <span className="text-xs text-slate-350 font-semibold">SMTP Email Dispatcher</span>
                  <input
                    type="checkbox"
                    checked={prefs.email_enabled}
                    onChange={(e) => setPrefs((prev) => ({ ...prev, email_enabled: e.target.checked }))}
                    className="w-4.5 h-4.5 rounded text-amber-500 bg-slate-950 border-slate-800 focus:ring-amber-500/30"
                  />
                </label>
              </div>

              {/* Filtering Switches */}
              <div className="flex flex-col gap-4">
                <span className="text-slate-400 text-xxs font-bold uppercase tracking-wider border-b border-slate-850 pb-2">Severity threshold Filters</span>

                <label className="flex items-center justify-between p-2 hover:bg-slate-850/20 rounded-lg cursor-pointer">
                  <span className="text-xs text-slate-350 font-semibold">Only Critical Severity Incidents</span>
                  <input
                    type="checkbox"
                    checked={prefs.alert_on_critical && !prefs.alert_on_high}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setPrefs((prev) => ({ ...prev, alert_on_critical: true, alert_on_high: false }));
                      }
                    }}
                    className="w-4.5 h-4.5 rounded text-amber-500 bg-slate-950 border-slate-800 focus:ring-amber-500/30"
                  />
                </label>

                <label className="flex items-center justify-between p-2 hover:bg-slate-850/20 rounded-lg cursor-pointer">
                  <span className="text-xs text-slate-350 font-semibold">High & Critical Severity Incidents</span>
                  <input
                    type="checkbox"
                    checked={prefs.alert_on_high}
                    onChange={(e) => {
                      setPrefs((prev) => ({ 
                        ...prev, 
                        alert_on_high: e.target.checked,
                        alert_on_critical: true 
                      }));
                    }}
                    className="w-4.5 h-4.5 rounded text-amber-500 bg-slate-950 border-slate-800 focus:ring-amber-500/30"
                  />
                </label>
              </div>
            </div>

            {/* Digest summaries */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-slate-850 pt-4 mt-2">
              <div className="flex flex-col gap-4">
                <span className="text-slate-400 text-xxs font-bold uppercase tracking-wider border-b border-slate-850 pb-2">Scheduled summaries</span>
                
                <label className="flex items-center justify-between p-2 hover:bg-slate-850/20 rounded-lg cursor-pointer">
                  <span className="text-xs text-slate-350 font-semibold">Daily digests summaries report</span>
                  <input
                    type="checkbox"
                    checked={prefs.daily_summary_enabled}
                    onChange={(e) => setPrefs((prev) => ({ ...prev, daily_summary_enabled: e.target.checked }))}
                    className="w-4.5 h-4.5 rounded text-amber-500 bg-slate-950 border-slate-800 focus:ring-amber-500/30"
                  />
                </label>

                <label className="flex items-center justify-between p-2 hover:bg-slate-850/20 rounded-lg cursor-pointer">
                  <span className="text-xs text-slate-350 font-semibold">Weekly aggregate telemetry report</span>
                  <input
                    type="checkbox"
                    checked={prefs.weekly_report_enabled}
                    onChange={(e) => setPrefs((prev) => ({ ...prev, weekly_report_enabled: e.target.checked }))}
                    className="w-4.5 h-4.5 rounded text-amber-500 bg-slate-950 border-slate-800 focus:ring-amber-500/30"
                  />
                </label>
              </div>
            </div>

            <button
              onClick={handleSavePrefs}
              className="bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-bold py-2.5 px-5 rounded-xl text-xs flex items-center justify-center gap-1.5 cursor-pointer shadow-lg transition-all duration-300 w-fit self-end mt-2"
            >
              <Save size={13} />
              Save Preferences
            </button>
          </div>
        )}

        {/* TAB 4: Operator Profile */}
        {activeTab === 'profile' && profile && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4 max-w-lg">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-slate-200 text-sm font-semibold">Operator Profile Information</span>
            </div>

            <div className="flex flex-col gap-4 mt-2">
              <div className="flex flex-col gap-1">
                <label className="text-slate-500 text-xxs font-semibold uppercase tracking-wider font-mono">User Name</label>
                <input
                  type="text"
                  readOnly
                  value={profile.username}
                  className="bg-slate-950 border border-slate-850 text-slate-200 text-xs px-3.5 py-2.5 rounded-xl font-mono focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-slate-500 text-xxs font-semibold uppercase tracking-wider font-mono">System Email address</label>
                <input
                  type="text"
                  readOnly
                  value={profile.email || 'soc_operator@honeycloud.lan'}
                  className="bg-slate-950 border border-slate-850 text-slate-200 text-xs px-3.5 py-2.5 rounded-xl font-mono focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-slate-500 text-xxs font-semibold uppercase tracking-wider font-mono">Assigned SOC Role</label>
                <input
                  type="text"
                  readOnly
                  value={(profile.role || 'administrator').toUpperCase()}
                  className="bg-slate-950 border border-slate-850 text-amber-500 text-xs px-3.5 py-2.5 rounded-xl font-mono font-bold focus:outline-none"
                />
              </div>
            </div>
          </div>
        )}

      </div>

      {/* Decoy Registration Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-850 w-full max-w-md rounded-2xl overflow-hidden shadow-2xl animate-scale-in">
            <div className="px-5 py-4 border-b border-slate-850 flex items-center justify-between">
              <span className="text-slate-200 text-xs font-bold uppercase tracking-wider">Register Decoy Sensor Node</span>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-500 hover:text-slate-200 text-base leading-none cursor-pointer"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateSensor} className="p-5 flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-slate-400 text-xxs font-semibold uppercase tracking-wider">Decoy Sensor Name</label>
                <input
                  type="text"
                  required
                  value={newSensor.name}
                  onChange={(e) => setNewSensor((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g. SF-Proxy-01"
                  className="bg-slate-950 border border-slate-800 text-slate-250 text-xs px-3.5 py-2.5 rounded-xl focus:outline-none focus:border-amber-500/50 font-mono"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-slate-400 text-xxs font-semibold uppercase tracking-wider">Sensor Emulation Protocol</label>
                <select
                  value={newSensor.service_type}
                  onChange={(e) => setNewSensor((prev) => ({ ...prev, service_type: e.target.value }))}
                  className="bg-slate-950 border border-slate-800 text-slate-250 text-xs px-3.5 py-2.5 rounded-xl focus:outline-none focus:border-amber-500/50 cursor-pointer font-mono"
                >
                  <option value="ssh">SSH Listener (Port 22)</option>
                  <option value="telnet">Telnet Gateway (Port 23)</option>
                  <option value="ftp">FTP Server (Port 21)</option>
                  <option value="http">HTTP Admin Portal (Port 80)</option>
                  <option value="smtp">SMTP Mail Server (Port 25)</option>
                  <option value="rdp">RDP Gateway (Port 3389)</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-slate-400 text-xxs font-semibold uppercase tracking-wider">Sensor Description</label>
                <textarea
                  value={newSensor.description}
                  onChange={(e) => setNewSensor((prev) => ({ ...prev, description: e.target.value }))}
                  placeholder="Details about decoy deployment deployment region"
                  className="bg-slate-950 border border-slate-800 text-slate-250 text-xs px-3.5 py-2.5 rounded-xl h-20 resize-none focus:outline-none focus:border-amber-500/50 font-sans"
                />
              </div>

              <div className="flex gap-2 justify-end mt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs cursor-pointer shadow-lg"
                >
                  Register Node
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default Settings;
