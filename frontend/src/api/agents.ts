import client from './client';

export interface Agent {
  id: string;
  name: string;
  description: string;
  model: string;
  system_prompt: string;
  mcp_tools: any[];
  skills: any[];
  created_at: string;
  updated_at: string;
}

export interface AgentsResponse {
  items: Agent[];
  total: number;
  page: number;
  limit: number;
}

export const getAgents = (page = 1) =>
  client.get<AgentsResponse>('/agents', { params: { page, limit: 20 } }).then(r => r.data);

export const createAgent = (data: Partial<Agent>) =>
  client.post<Agent>('/agents', data).then(r => r.data);

export const updateAgent = (id: string, data: Partial<Agent>) =>
  client.put<Agent>(`/agents/${id}`, data).then(r => r.data);

export const deleteAgent = (id: string) =>
  client.delete(`/agents/${id}`);
