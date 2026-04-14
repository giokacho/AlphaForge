import React, { createContext, useState, useEffect, useContext } from 'react';
import apiClient from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Validate the session token on load silently
  useEffect(() => {
    const bootstrapUser = async () => {
      const token = localStorage.getItem('alphaforge_token');
      if (token) {
        try {
          const response = await apiClient.get('/auth/me');
          setUser(response.data);
        } catch (error) {
          // 401 will automatically intercept and delete the token
          setUser(null);
        }
      }
      setLoading(false);
    };

    bootstrapUser();
  }, []);

  const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const { access_token } = response.data;
    localStorage.setItem('alphaforge_token', access_token);
    
    // Immediately fetch the user payload internally
    const userRes = await apiClient.get('/auth/me');
    setUser(userRes.data);
    return userRes.data;
  };

  const logout = () => {
    localStorage.removeItem('alphaforge_token');
    setUser(null);
    window.location.href = '/login';
  };

  if (loading) {
    return null; // Or a spinner graphic
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
        {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
