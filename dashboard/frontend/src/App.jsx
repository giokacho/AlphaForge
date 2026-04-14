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

// Protected layout that intercepts navigation and renders sidebar + outlet
const ProtectedLayout = () => {
    const { user, loading } = useAuth();
    
    if (loading) {
        return <div style={{ 
            height: '100vh', 
            background: theme.colors.background.primary,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: theme.colors.text.secondary,
            fontFamily: 'Inter, system-ui, sans-serif'
        }}>Initializing Secure Session...</div>;
    }
    
    if (!user) {
        return <Navigate to="/login" replace />;
    }
    
    return (
        <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: theme.colors.background.primary, fontFamily: 'Inter, system-ui, sans-serif' }}>
            <Sidebar />
            <main style={{ marginLeft: '260px', flex: 1, padding: '32px' }}>
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
                    <Route path="/macro" element={<Macro />} />
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
