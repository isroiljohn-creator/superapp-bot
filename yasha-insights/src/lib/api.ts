import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth Interceptor
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  getToken: () => localStorage.getItem('token'),

  setToken: (token: string) => localStorage.setItem('token', token),

  clearToken: () => localStorage.removeItem('token'),

  authenticate: async (initData: string) => {
    const res = await axiosInstance.post('/admin/auth/telegram', { initData });
    if (res.data.token) {
      localStorage.setItem('token', res.data.token);
    }
    return res.data;
  },

  getOverview: async () => {
    const res = await axiosInstance.get('/admin/stats');
    return res.data;
  },

  getRetention: async (days: number = 30) => {
    const res = await axiosInstance.get(`/admin/retention?days=${days}`);
    return res.data;
  },

  getAICosts: async (range: string = '7d') => {
    const res = await axiosInstance.get('/admin/cost');
    return res.data;
  },

  getFeedback: async (range: string = '7d') => {
    const res = await axiosInstance.get('/admin/feedback');
    return res.data;
  },

  getAdaptation: async (range: string = '14d') => {
    const res = await axiosInstance.get('/admin/adaptation');
    return res.data;
  },
};
