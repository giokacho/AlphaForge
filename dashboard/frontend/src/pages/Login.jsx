import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

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
      setError('AUTH FAILED — INVALID CREDENTIALS');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '8px 10px',
    backgroundColor: '#0a0a0a',
    border: 'none',
    borderBottom: '1px solid #ff6600',
    color: '#cccccc',
    fontSize: '13px',
    fontFamily: MONO,
    outline: 'none',
    boxSizing: 'border-box',
    letterSpacing: '0.5px',
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#0a0a0a',
      fontFamily: MONO,
    }}>
      <div style={{ width: '380px' }}>
        {/* Terminal title bar */}
        <div style={{
          backgroundColor: '#ff6600',
          padding: '7px 14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ color: '#000', fontWeight: '700', fontSize: '12px', letterSpacing: '1.5px' }}>
            ALPHAFORGE TRADING SYSTEM
          </span>
          <span style={{ color: '#0007', fontSize: '10px' }}>v2.2</span>
        </div>

        <div style={{ border: '1px solid #222', borderTop: 'none', backgroundColor: '#0d0d0d', padding: '24px' }}>
          <div style={{ borderBottom: '1px solid #1a1a1a', paddingBottom: '16px', marginBottom: '20px' }}>
            <div style={{ color: '#444', fontSize: '10px', letterSpacing: '1.5px', marginBottom: '5px' }}>
              SECURE ACCESS TERMINAL
            </div>
            <div style={{ color: '#666', fontSize: '11px' }}>
              Institutional Analytics Core — Authorized Personnel Only
            </div>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', color: '#ff6600', fontSize: '10px', letterSpacing: '1.5px', marginBottom: '6px' }}>
                USER ID
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={{ display: 'block', color: '#ff6600', fontSize: '10px', letterSpacing: '1.5px', marginBottom: '6px' }}>
                PASSWORD
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                style={inputStyle}
              />
            </div>

            {error && (
              <div style={{
                color: '#ff3333',
                fontSize: '11px',
                padding: '8px 10px',
                border: '1px solid #ff333333',
                backgroundColor: '#1a0000',
                letterSpacing: '0.5px',
              }}>
                ■ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                backgroundColor: loading ? '#0d0d0d' : '#ff6600',
                color: loading ? '#ff6600' : '#000',
                border: '1px solid #ff6600',
                padding: '10px',
                fontSize: '11px',
                fontFamily: MONO,
                fontWeight: '700',
                letterSpacing: '2px',
                cursor: loading ? 'not-allowed' : 'pointer',
                marginTop: '4px',
              }}
            >
              {loading ? 'AUTHENTICATING...' : 'AUTHENTICATE'}
            </button>
          </form>
        </div>

        <div style={{ color: '#222', fontSize: '10px', letterSpacing: '0.5px', textAlign: 'center', marginTop: '12px' }}>
          ALPHAFORGE PROPRIETARY SYSTEM — UNAUTHORIZED ACCESS PROHIBITED
        </div>
      </div>
    </div>
  );
}
