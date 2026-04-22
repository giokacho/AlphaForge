import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Activity, Globe, BarChart2, Users, LogOut, Newspaper } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

export default function Sidebar() {
  const { logout } = useAuth();

  const [lastUpdated, setLastUpdated] = useState(Date.now());
  const [timeAgo, setTimeAgo] = useState('JUST NOW');

  useEffect(() => {
    const handlePoll = (e) => {
      setLastUpdated(e.detail);
      setTimeAgo('JUST NOW');
    };
    window.addEventListener('alphaforge-poll', handlePoll);

    const interval = setInterval(() => {
      const mins = Math.floor((Date.now() - lastUpdated) / 60000);
      if (mins === 0) setTimeAgo('JUST NOW');
      else setTimeAgo(`${mins}M AGO`);
    }, 60000);

    return () => {
      window.removeEventListener('alphaforge-poll', handlePoll);
      clearInterval(interval);
    };
  }, [lastUpdated]);

  const navItems = [
    { name: 'OVERVIEW', path: '/overview', icon: LayoutDashboard },
    { name: 'SIGNALS', path: '/signals', icon: Activity },
    { name: 'MACRO', path: '/macro', icon: Globe },
    { name: 'NEWS INTEL', path: '/news', icon: Newspaper },
    { name: 'COT DATA', path: '/cot', icon: BarChart2 },
    { name: 'DEBATE', path: '/debate', icon: Users },
  ];

  return (
    <div style={{
      width: '220px',
      height: '100vh',
      backgroundColor: '#0a0a0a',
      borderRight: '1px solid #222',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      left: 0,
      top: 0,
      fontFamily: MONO,
    }}>
      {/* Header */}
      <div style={{ padding: '14px 16px', borderBottom: '1px solid #222' }}>
        <div style={{ color: '#ff6600', fontSize: '15px', fontWeight: '700', letterSpacing: '2px' }}>
          ALPHAFORGE
        </div>
        <div style={{ color: '#333', fontSize: '10px', letterSpacing: '1px', marginTop: '3px' }}>
          TRADING ANALYTICS v2.2
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '6px 0', display: 'flex', flexDirection: 'column' }}>
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '9px 16px',
              textDecoration: 'none',
              color: isActive ? '#ff6600' : '#444',
              backgroundColor: isActive ? '#100800' : 'transparent',
              borderLeft: isActive ? '2px solid #ff6600' : '2px solid transparent',
              fontSize: '11px',
              fontWeight: isActive ? '600' : '400',
              letterSpacing: '1px',
              fontFamily: MONO,
            })}
          >
            {({ isActive }) => (
              <>
                <item.icon size={13} />
                <span>{item.name}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid #222' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <div
            className="terminal-blink"
            style={{ width: '6px', height: '6px', backgroundColor: '#00ff41', flexShrink: 0 }}
          />
          <span style={{ color: '#333', fontSize: '10px', letterSpacing: '0.5px' }}>
            UPD {timeAgo}
          </span>
        </div>
        <button
          onClick={logout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            width: '100%',
            paddingTop: '10px',
            backgroundColor: 'transparent',
            border: 'none',
            borderTop: '1px solid #1a1a1a',
            color: '#333',
            cursor: 'pointer',
            fontSize: '10px',
            fontFamily: MONO,
            letterSpacing: '1px',
            textAlign: 'left',
          }}
          onMouseOver={(e) => e.currentTarget.style.color = '#ff6600'}
          onMouseOut={(e) => e.currentTarget.style.color = '#333'}
        >
          <LogOut size={11} />
          <span>SIGN OUT</span>
        </button>
      </div>
    </div>
  );
}
