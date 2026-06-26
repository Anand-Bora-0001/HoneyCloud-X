import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { useToast } from './ToastContext';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('hc_token') || sessionStorage.getItem('hc_token') || '');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sseConnected, setSseConnected] = useState(false);
  const [liveAttacks, setLiveAttacks] = useState([]);
  const { showToast } = useToast();
  
  const eventSourceRef = useRef(null);

  // Expose base API path. We use absolute URL in production to bypass Render's rewrite proxy
  // which buffers responses and breaks SSE (Server-Sent Events).
  const apiBase = import.meta.env.PROD ? 'https://honeycloud-backend.onrender.com' : '';

  const logout = () => {
    localStorage.removeItem('hc_token');
    sessionStorage.removeItem('hc_token');
    setToken('');
    setUser(null);
    setLiveAttacks([]);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setSseConnected(false);
  };

  const apiCall = async (endpoint, options = {}) => {
    const url = `${apiBase}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Adjust content-type for urlencoded form data / file uploads
    if (options.body instanceof URLSearchParams) {
      headers['Content-Type'] = 'application/x-www-form-urlencoded';
    } else if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);

      if (response.status === 401) {
        logout();
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
  };

  const login = async (username, password, remember = true) => {
    const body = new URLSearchParams();
    body.append('username', username);
    body.append('password', password);

    try {
      const res = await apiCall('/auth/login', {
        method: 'POST',
        body
      });

      const tokenValue = res.access_token;
      if (remember) {
        localStorage.setItem('hc_token', tokenValue);
      } else {
        sessionStorage.setItem('hc_token', tokenValue);
      }

      setToken(tokenValue);
      setUser({ username: res.user, role: res.role });
      showToast(`Welcome back, ${res.user}!`, 'success');
      return res;
    } catch (error) {
      showToast(error.message || 'Login failed', 'error');
      throw error;
    }
  };

  // Fetch user profile on token load
  useEffect(() => {
    const initUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const profile = await apiCall('/auth/me');
        setUser(profile);
      } catch (err) {
        console.error('Failed to restore session', err);
        logout();
      } finally {
        setLoading(false);
      }
    };
    initUser();
  }, [token]);

  // Setup EventSource for real-time logs
  useEffect(() => {
    if (!token || !user) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setSseConnected(false);
      }
      return;
    }

    const connectSse = () => {
      // Connect to the stream endpoint
      const es = new EventSource(`${apiBase}/api/events/stream?token=${token}`);
      eventSourceRef.current = es;

      es.onopen = () => {
        setSseConnected(true);
      };

      es.addEventListener('new_attack', (e) => {
        try {
          const event = JSON.parse(e.data);
          
          setLiveAttacks((prev) => {
            const updated = [event, ...prev];
            // Limit to last 100 logs
            if (updated.length > 100) updated.pop();
            return updated;
          });

          if (event.severity === 'CRITICAL') {
            showToast(`CRITICAL INCURSION: ${event.source_ip} targeting ${event.service || 'deception node'}`, 'error');
          }
        } catch (error) {
          console.error('Failed to parse SSE new_attack event data', error);
        }
      });

      es.onerror = (err) => {
        console.error('EventSource connection encountered error, reconnecting...', err);
        setSseConnected(false);
        es.close();
        
        // Retry connection in 5 seconds if authenticated
        if (token && eventSourceRef.current) {
          setTimeout(connectSse, 5000);
        }
      };
    };

    connectSse();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setSseConnected(false);
      }
    };
  }, [token, user]);

  const value = {
    token,
    user,
    loading,
    sseConnected,
    liveAttacks,
    login,
    logout,
    apiCall
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
