import axios from 'axios';

// Initialize the API client connecting back to our FastAPI backend using explicitly defined Vite envs
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Intercept requests to dynamically inject the Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('alphaforge_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept responses entirely to catch token invalidation triggers
apiClient.interceptors.response.use(
  (response) => {
    window.dispatchEvent(new CustomEvent('alphaforge-poll', { detail: Date.now() }));
    return response;
  },
  (error) => {
    // 401 Unauthorized handling
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('alphaforge_token');
      // Hard redirect securely if token expires or validates weirdly
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
