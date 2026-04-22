import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { theme } from './styles/theme';
import Login from './pages/Login';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import Signals from './pages/Signals';
import Macro from './pages/Macro';
import COT from './pages/COT';
import Debate from './pages/Debate';
import News from './pages/News';
import Technicals from './pages/Technicals';

// Protected layout that intercepts navigation and renders sidebar + outlet
const ProtectedLayout = () => {
    const { user, loading } = useAuth();
    
    if (loading) {
        return <div style={{
            height: '100vh',
            background: '#0a0a0a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#444',
            fontFamily: "'JetBrains Mono', 'Courier New', monospace",
            fontSize: '12px',
            letterSpacing: '1px'
        }}>INITIALIZING SECURE SESSION...</div>;
    }
    
    if (!user) {
        return <Navigate to="/login" replace />;
    }
    
    return (
        <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0a0a0a', fontFamily: "'JetBrains Mono', 'Courier New', monospace" }}>
            <Sidebar />
            <main style={{ marginLeft: '220px', flex: 1, padding: '20px 24px' }}>
                <Outlet />
            </main>
        </div>
    );
};

// Temp Placeholder component for unbuilt pages
const Placeholder = ({ title }) => (
    <div>
        <h1 style={{ color: theme.colors.text.primary, borderBottom: `1px solid ${theme.colors.ui.border}`, paddingBottom: '16px', marginTop: 0 }}>{title}</h1>
        <p style={{ color: theme.colors.text.secondary, marginTop: '24px' }}>Component currently uninitialized. Connect layout mapping to display data logic.</p>
    </div>
);

function App() {
  return (
    <AuthProvider>
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                
                {/* Protected Section wrapped iteratively */}
                <Route element={<ProtectedLayout />}>
                    <Route path="/" element={<Navigate to="/overview" replace />} />
                    <Route path="/overview" element={<Overview />} />
                    <Route path="/signals" element={<Signals />} />
                    <Route path="/technicals" element={<Technicals />} />
                    <Route path="/macro" element={<Macro />} />
                    <Route path="/news" element={<News />} />
                    <Route path="/cot" element={<COT />} />
                    <Route path="/debate" element={<Debate />} />
                </Route>
                
                {/* Catch-all route to dump back to root safe state */}
                <Route path="*" element={<Navigate to="/overview" replace />} />
            </Routes>
        </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
