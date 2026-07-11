import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Lock, User, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ParticlesBackground from '../components/ParticlesBackground';

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      setErrorMsg('Please specify both username and password.');
      return;
    }
    
    setSubmitting(true);
    setErrorMsg('');
    try {
      await login(username, password, remember);
      navigate('/dashboard');
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-slate-950 px-4 py-12 overflow-hidden">
      {/* Background Particle Animation */}
      <ParticlesBackground />

      {/* Cyber Honeycomb overlay assets */}
      <div className="absolute inset-0 bg-[url('/assets/honeycomb-pattern.svg')] opacity-[0.03] pointer-events-none select-none" />

      {/* Glow Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-[100px] pointer-events-none -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-yellow-500/5 rounded-full blur-[100px] pointer-events-none translate-x-1/2 translate-y-1/2" />

      {/* Login Card */}
      <div className="w-full max-w-md bg-slate-900/60 border border-slate-800 rounded-2xl shadow-2xl p-8 backdrop-blur-lg animate-fade-in relative z-10">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(246,166,35,0.15)]">
            <img 
              src="/assets/logo-main.svg" 
              alt="HoneyCloud" 
              className="w-10 h-10 select-none animate-pulse" 
            />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-1.5 font-sans">
            HoneyCloud
          </h1>
          <p className="text-slate-400 text-xs mt-1.5 font-medium uppercase tracking-wider">
            Honeypot SOC Intelligence Console
          </p>
        </div>

        {/* Error Alert Panel */}
        {errorMsg && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs px-4 py-3 rounded-lg mb-6 leading-relaxed flex items-start gap-2">
            <span className="font-bold select-none">⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {/* Username Input */}
          <div className="flex flex-col gap-1.5">
            <label 
              htmlFor="login-username"
              className="text-slate-400 text-xs font-semibold uppercase tracking-wider"
            >
              Operator Username
            </label>
            <div className="relative">
              <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                id="login-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                className="w-full bg-slate-950/80 border border-slate-800 text-slate-200 placeholder-slate-600 pl-11 pr-4 py-2.5 rounded-xl text-sm focus:outline-none focus:border-amber-500/50 transition-colors font-mono"
                required
                disabled={submitting}
              />
            </div>
          </div>

          {/* Password Input */}
          <div className="flex flex-col gap-1.5">
            <label 
              htmlFor="login-password"
              className="text-slate-400 text-xs font-semibold uppercase tracking-wider"
            >
              Security Password
            </label>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="password"
                id="login-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="admin123"
                className="w-full bg-slate-950/80 border border-slate-800 text-slate-200 placeholder-slate-600 pl-11 pr-4 py-2.5 rounded-xl text-sm focus:outline-none focus:border-amber-500/50 transition-colors font-mono"
                required
                disabled={submitting}
              />
            </div>
          </div>

          {/* Remember Option */}
          <div className="flex items-center justify-between mt-1">
            <label className="flex items-center gap-2 text-slate-400 hover:text-slate-200 text-xs font-medium cursor-pointer select-none">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-amber-500 focus:ring-amber-500/30"
                disabled={submitting}
              />
              <span>Remember this session</span>
            </label>
          </div>

          {/* Action Trigger */}
          <button
            type="submit"
            className="w-full bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-bold py-3 px-4 rounded-xl text-sm flex items-center justify-center gap-2 cursor-pointer shadow-lg hover:shadow-amber-500/10 transition-all duration-300 disabled:opacity-50"
            disabled={submitting}
          >
            {submitting ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                <span>Authenticating Credentials...</span>
              </>
            ) : (
              <>
                <ShieldCheck size={18} />
                <span>Establish Secure Link</span>
              </>
            )}
          </button>
        </form>
      </div>
      
      {/* Footer Info */}
      <div className="absolute bottom-4 left-0 right-0 text-center pointer-events-none select-none z-10">
        <span className="text-slate-600 text-xxs font-mono uppercase tracking-widest">
          &copy; {new Date().getFullYear()} HoneyCloud Systems. All Rights Reserved.
        </span>
      </div>
    </div>
  );
};

export default Login;
