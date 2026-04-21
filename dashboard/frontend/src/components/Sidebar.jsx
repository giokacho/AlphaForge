import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { theme } from '../styles/theme';
import { LayoutDashboard, Activity, Globe, BarChart2, Users, Shield, LogOut, Newspaper } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { logout } = useAuth();
  
  const [lastUpdated, setLastUpdated] = useState(Date.now());
  const [timeAgo, setTimeAgo] = useState('Just now');

  useEffect(() => {
      const handlePoll = (e) => {
          setLastUpdated(e.detail);
          setTimeAgo('Just now');
      };
      window.addEventListener('alphaforge-poll', handlePoll);
      
      const interval = setInterval(() => {
          const mins = Math.floor((Date.now() - lastUpdated) / 60000);
          if (mins === 0) setTimeAgo('Just now');
          else setTimeAgo(`${mins} min${mins > 1 ? 's' : ''} ago`);
      }, 60000);
      
      return () => {
          window.removeEventListener('alphaforge-poll', handlePoll);
          clearInterval(interval);
      };
  }, [lastUpdated]);
  
  const navItems = [
    { name: 'Overview', path: '/overview', icon: LayoutDashboard },
    { name: 'Signals', path: '/signals', icon: Activity },
    { name: 'Macro', path: '/macro', icon: Globe },
    { name: 'News', path: '/news', icon: Newspaper },
    { name: 'CoT Data', path: '/cot', icon: BarChart2 },
    { name: 'Debate', path: '/debate', icon: Users },
  ];

  return (
    <div style={{
      width: '260px',
      height: '100vh',
      backgroundColor: theme.colors.background.card,
      borderRight: `1px solid ${theme.colors.ui.border}`,
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      left: 0,
      top: 0
    }}>
      <div style={{ 
        padding: '24px', 
        borderBottom: `1px solid ${theme.colors.ui.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <Shield color={theme.colors.accent.blue} size={28} />
        <h2 style={{ 
          color: theme.colors.text.primary, 
          margin: 0, 
          fontSize: '20px', 
          fontWeight: 'bold',
          letterSpacing: '-0.5px'
        }}>AlphaForge</h2>
      </div>

      <nav style={{ flex: 1, padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 16px',
              borderRadius: '8px',
              textDecoration: 'none',
              color: isActive ? theme.colors.text.primary : theme.colors.text.secondary,
              backgroundColor: isActive ? theme.colors.accent.blueDark : 'transparent',
              fontWeight: isActive ? '600' : 'normal',
              transition: 'all 0.2s'
            })}
          >
            {({ isActive }) => (
                <>
                  <item.icon size={20} color={isActive ? theme.colors.accent.blue : theme.colors.text.secondary} />
                  <span>{item.name}</span>
                </>
            )}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: '24px 16px', borderTop: `1px solid ${theme.colors.ui.border}`, display: 'flex', flexDirection: 'column', gap: '24px' }}>
         <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px' }}>
            <div className="skeleton-pulse" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: theme.colors.signals.green, boxShadow: `0 0 8px ${theme.colors.signals.green}` }} />
            <span style={{ color: theme.colors.text.secondary, fontSize: '13px' }}>Last updated: {timeAgo}</span>
         </div>
      
         <button 
           onClick={logout}
           style={{
             display: 'flex',
             alignItems: 'center',
             gap: '12px',
             width: '100%',
             padding: '8px',
             backgroundColor: 'transparent',
             border: 'none',
             color: theme.colors.text.secondary,
             cursor: 'pointer',
             fontSize: '15px',
             fontWeight: '500',
             transition: 'color 0.2s',
             textAlign: 'left'
           }}
           onMouseOver={(e) => e.currentTarget.style.color = theme.colors.text.primary}
           onMouseOut={(e) => e.currentTarget.style.color = theme.colors.text.secondary}
           >
           <LogOut size={20} />
           <span>Sign Out</span>
         </button>
      </div>
    </div>
  );
}
