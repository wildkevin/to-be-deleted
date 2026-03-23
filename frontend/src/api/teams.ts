import client from './client';

export interface Team {
  id: string;
  name: string;
  description: string;
  mode: 'sequential' | 'orchestrator' | 'loop';
  orchestrator_agent_id?: string;
  loop_max_iterations?: number;
  loop_stop_signal?: string;
  agents: any[];
  created_at: string;
  updated_at: string;
}

export interface TeamsResponse {
  items: Team[];
  total: number;
  page: number;
  limit: number;
}

export const getTeams = (page = 1) =>
  client.get<TeamsResponse>('/teams', { params: { page, limit: 20 } }).then(r => r.data);

export const createTeam = (data: Partial<Team>) =>
  client.post<Team>('/teams', data).then(r => r.data);

export const deleteTeam = (id: string) =>
  client.delete(`/teams/${id}`);
