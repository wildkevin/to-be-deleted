import client from './client';

export interface MarketplaceItem {
  id: string;
  name: string;
  description: string;
  type: 'mcp' | 'skill';
  config: any;
  file_path?: string;
  status: 'pending' | 'approved' | 'rejected';
  submitted_by: string;
  reviewed_by?: string;
  status_changed_at?: string;
  discovered_tools?: string[];
  created_at: string;
}

export const getMarketplaceItems = (type?: 'mcp' | 'skill') =>
  client.get<{items: MarketplaceItem[], total: number, page: number, limit: number}>('/marketplace', {
    params: type ? { type } : {}
  }).then(r => r.data);

export const getPendingItems = () =>
  client.get<{items: MarketplaceItem[], total: number, page: number, limit: number}>('/marketplace/pending').then(r => r.data);

export const submitMarketplaceItem = (formData: FormData) =>
  client.post<{id: string}>('/marketplace/submit', formData).then(r => r.data);

export const approveItem = (id: string) =>
  client.post(`/marketplace/${id}/approve`).then(r => r.data);

export const rejectItem = (id: string) =>
  client.post(`/marketplace/${id}/reject`).then(r => r.data);
