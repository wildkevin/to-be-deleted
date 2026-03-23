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
  // For now, we use a default user
  config.headers['X-CCM-User'] = 'default-user';
  return config;
});

export default client;
