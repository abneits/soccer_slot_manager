import axios from 'axios';

const API_URL = '/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (userData) => api.post('/auth/register', userData),
  getCurrentUser: () => api.get('/auth/me'),
};

// Users API
export const usersAPI = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
};

// Slots API
export const slotsAPI = {
  getAll: (page = 1, limit = 10) => api.get(`/slots?page=${page}&limit=${limit}`),
  getNext: () => api.get('/slots/next'),
  getById: (id) => api.get(`/slots/${id}`),
  register: (id, guests) => api.post(`/slots/${id}/register`, { guests }),
  updateRegistration: (id, guests) => api.put(`/slots/${id}/register`, { guests }),
  cancelRegistration: (id) => api.delete(`/slots/${id}/register`),
  updateDetails: (id, details) => api.put(`/slots/${id}/details`, details),
};

// Stats API
export const statsAPI = {
  getAll: () => api.get('/stats'),
  getByUser: (userId) => api.get(`/stats/user/${userId}`),
};

export default api;
