import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add X-CCM-User header for all requests
client.interceptors.request.use((config) => {
  // In a real app, this would come from authentication
  // For now, we use 'alice' as the default user
  config.headers['X-CCM-User'] = 'alice';
  return config;
});

export default client;
