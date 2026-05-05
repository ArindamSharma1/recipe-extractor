/**
 * Axios client configured for the Recipe Extractor API.
 * Uses the Vite proxy in development (/api → backend:8000).
 */

import axios from 'axios';

const API_BASE = '/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120_000, // 2 min — LLM calls can be slow
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for consistent error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';

    return Promise.reject(new Error(message));
  }
);

export default client;
