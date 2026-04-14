import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { theme } from '../styles/theme';
import { Shield } from 'lucide-react';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      await login(username, password);
      navigate('/overview');
    } catch (err) {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.colors.background.primary,
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        backgroundColor: theme.colors.background.card,
        padding: '40px',
        borderRadius: '12px',
        border: `1px solid ${theme.colors.ui.border}`,
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
             <Shield size={48} color={theme.colors.accent.blue} />
          </div>
          <h1 style={{ 
            color: theme.colors.accent.blue, 
            fontSize: '32px', 
            fontWeight: 'bold',
            margin: '0 0 8px 0',
            letterSpacing: '-0.5px'
          }}>AlphaForge</h1>
          <p style={{ color: theme.colors.text.secondary, margin: 0, fontSize: '15px' }}>
            Institutional Trading Analytics Core
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', color: theme.colors.text.secondary, fontSize: '14px', marginBottom: '8px', fontWeight: '500' }}>Username</label>
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              autoComplete="username"
              style={{
                width: '100%',
                padding: '12px 16px',
                backgroundColor: theme.colors.background.secondary,
                border: `1px solid ${theme.colors.ui.border}`,
                borderRadius: '6px',
                color: theme.colors.text.primary,
                fontSize: '15px',
                boxSizing: 'border-box',
                outline: 'none'
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', color: theme.colors.text.secondary, fontSize: '14px', marginBottom: '8px', fontWeight: '500' }}>Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              style={{
                width: '100%',
                padding: '12px 16px',
                backgroundColor: theme.colors.background.secondary,
                border: `1px solid ${theme.colors.ui.border}`,
                borderRadius: '6px',
                color: theme.colors.text.primary,
                fontSize: '15px',
                boxSizing: 'border-box',
                outline: 'none'
              }}
            />
          </div>

          {error && (
            <div style={{ 
              color: theme.colors.signals.red, 
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              padding: '12px',
              borderRadius: '6px',
              textAlign: 'center',
              fontSize: '14px',
              border: `1px solid rgba(239, 68, 68, 0.2)`
            }}>
              {error}
            </div>
          )}

          <button 
            type="submit" 
            disabled={loading}
            style={{
              backgroundColor: theme.colors.accent.blue,
              color: '#ffffff',
              border: 'none',
              padding: '14px',
              borderRadius: '6px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '8px',
              opacity: loading ? 0.7 : 1,
              transition: 'opacity 0.2s'
            }}>
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
