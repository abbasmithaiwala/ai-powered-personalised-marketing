import axios, { type AxiosError, type AxiosInstance } from 'axios';
import type { ErrorResponse } from '@/types/api';

// Create axios instance with base configuration
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: '/api/v1',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor to add API key
  client.interceptors.request.use(
    (config) => {
      const apiKey = localStorage.getItem('api_key');
      if (apiKey) {
        config.headers['X-API-Key'] = apiKey;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ErrorResponse>) => {
      if (error.response?.status === 401) {
        // Clear API key and redirect to login if needed
        localStorage.removeItem('api_key');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return client;
};

export const apiClient = createApiClient();

// Helper to extract error message
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ErrorResponse>;
    return axiosError.response?.data?.detail || axiosError.message || 'An error occurred';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
};

// API Key management
export const setApiKey = (key: string): void => {
  localStorage.setItem('api_key', key);
};

export const getApiKey = (): string | null => {
  return localStorage.getItem('api_key');
};

export const clearApiKey = (): void => {
  localStorage.removeItem('api_key');
};

export const hasApiKey = (): boolean => {
  return !!getApiKey();
};
