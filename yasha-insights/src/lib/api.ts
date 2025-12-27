import axios from 'axios';

// Environment variable for API URL (set during build or in .env)
// Fallback to /api/v1 for production (relative path)
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth Interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor (Optional: Handle 401/403)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.error('Access Denied');
      // Maybe redirect to access denied page
    }
    return Promise.reject(error);
  }
);

// --- API Methods ---

export const authTelegram = async (initData: string) => {
  const res = await api.post('/auth/telegram', { initData });
  return res.data; // { token, user }
};

export const getStats = async () => {
  const res = await api.get('/admin/stats');
  return res.data;
};

export const getFeedbackStats = async () => {
  const res = await api.get('/admin/feedback');
  return res.data;
};

export const getAdaptationStats = async () => {
  const res = await api.get('/admin/adaptation');
  return res.data;
};

export const getCostStats = async () => {
  const res = await api.get('/admin/cost');
  return res.data;
};
