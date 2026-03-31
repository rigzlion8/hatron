import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create an Axios instance with base configuration
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT Token and Log
api.interceptors.request.use(
  (config) => {
    console.log(`[API Request] => ${config.method?.toUpperCase()} ${config.url}`);
    
    // Check if we are in browser
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    console.error("[API Request Error]:", error);
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle Unauthorized (401) generically and Log
api.interceptors.response.use(
  (response) => {
     console.log(`[API Response] <= ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`[API Error] <= ${error.response?.status || 'Network Error'} ${error.config?.url}`);
    if (error.response && error.response.status === 401) {
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
