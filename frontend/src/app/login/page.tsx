"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Lock, Mail, Activity } from 'lucide-react';
import api from '@/lib/api';
import ThemeToggle from '@/components/ThemeToggle';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Check backend health on mount
  useEffect(() => {
    api.get('/health')
      .then(() => setBackendStatus('online'))
      .catch((err) => {
        console.error("Health check failed:", err);
        setBackendStatus('offline');
      });
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log("Attempting login for:", email);
      
      const res = await api.post('/auth/login', {
        email: email,
        password: password
      });

      console.log("Login response received:", res.status);

      // Backend returns { "user": ..., "tokens": { "access_token": ..., ... } }
      const token = res.data.tokens?.access_token;
      
      if (!token) {
        throw new Error("No access token received from server");
      }
      
      // Store locally
      localStorage.setItem('access_token', token);
      
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err: any) {
      console.error("Detailed Login Error:", err);
      const message = err.response?.data?.message || err.response?.data?.detail || err.message || "Invalid email or password.";
      setError(typeof message === 'string' ? message : JSON.stringify(message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ position: 'absolute', top: '2rem', right: '2rem' }}>
        <ThemeToggle />
      </div>

      <div className="glass-panel" style={{ padding: '2.5rem', display: 'flex', flexDirection: 'column', gap: '2rem', width: '100%', maxWidth: '450px' }}>
      
      <div style={{ textAlign: 'center' }}>
        <h1 className="heading-1" style={{ marginBottom: '0.5rem', background: 'linear-gradient(to right, var(--brand-500), var(--accent-primary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Hatron Solutions
        </h1>
        <p className="text-muted">Transforming Business with AI Automation</p>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: 'var(--error)', borderRadius: 'var(--radius-md)' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ position: 'relative' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>Email or Username</label>
          <div style={{ position: 'relative' }}>
            <div style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }}>
              <Mail size={18} />
            </div>
            <input 
              type="text" 
              className="input" 
              style={{ paddingLeft: '2.75rem' }} 
              placeholder="admin@hatron.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        </div>

        <div style={{ position: 'relative' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>Password</label>
          <div style={{ position: 'relative' }}>
            <div style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }}>
              <Lock size={18} />
            </div>
            <input 
              type="password" 
              className="input" 
              style={{ paddingLeft: '2.75rem' }} 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
        </div>

        <button type="submit" className="btn btn-primary" style={{ marginTop: '0.5rem', background: 'linear-gradient(135deg, var(--brand-500), var(--brand-600))' }} disabled={loading}>
          {loading ? <Loader2 size={18} className="animate-spin" /> : "Sign In to Terminal"}
        </button>
      </form>
      
      <div style={{ textAlign: 'center', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '1rem' }} className="text-muted">
        <div>
          New to Hatron? <span style={{ color: 'var(--brand-500)', cursor: 'pointer', fontWeight: 500 }}>Request Access</span>
        </div>
        
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          gap: '0.5rem',
          padding: '0.25rem 0.75rem',
          borderRadius: '100px',
          background: backendStatus === 'online' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          color: backendStatus === 'online' ? 'var(--success)' : 'var(--error)',
          width: 'fit-content',
          margin: '0 auto',
          fontSize: '0.75rem',
          fontWeight: 600
        }}>
          <Activity size={12} />
          System Status: {backendStatus === 'online' ? 'Online' : backendStatus === 'checking' ? 'Checking...' : 'Offline'}
        </div>
      </div>
    </div>
  </div>
  );
}
