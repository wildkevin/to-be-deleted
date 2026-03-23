import client from './client';

export interface MarketplaceItem {
  id: string;
  name: string;
  description: string;
  item_type: 'mcp' | 'skill';
  config: any;
  status: 'pending' | 'approved' | 'rejected';
  submitted_by: string;
  created_at: string;
}

export const getMarketplaceItems = (type?: 'mcp' | 'skill') =>
  client.get<{items: MarketplaceItem[]}>('/marketplace', {
    params: type ? { type } : {}
  }).then(r => r.data);

export const submitMCPTool = (data: { name: string; description: string; config: any }) =>
  client.post<{id: string}>('/marketplace/mcp', data).then(r => r.data);

export const submitSkill = (data: { name: string; description: string; code: string }) =>
  client.post<{id: string}>('/marketplace/skill', data).then(r => r.data);

export const approveItem = (id: string) =>
  client.post(`/marketplace/${id}/approve`).then(r => r.data);

export const rejectItem = (id: string) =>
  client.post(`/marketplace/${id}/reject`).then(r => r.data);
