import client from './client';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title?: string;
  agent_id?: string;
  team_id?: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export const getConversations = (agentId?: string, teamId?: string) =>
  client.get<{items: Conversation[]}>('/conversations', {
    params: { agent_id: agentId, team_id: teamId }
  }).then(r => r.data);

export const getConversation = (id: string) =>
  client.get<Conversation>(`/conversations/${id}`).then(r => r.data);

export const createConversation = (data: { target_type: string; target_id: string; title?: string }) =>
  client.post<Conversation>('/conversations', data).then(r => r.data);

export interface SSEEvent {
  event: string;
  data: any;
}

export const streamChat = (
  conversationId: string,
  message: string,
  onEvent: (event: SSEEvent) => void
): (() => void) => {
  const eventSource = new EventSource(
    `/api/conversations/${conversationId}/chat?message=${encodeURIComponent(message)}&user=alice`
  );

  eventSource.addEventListener('token', (e: MessageEvent) => {
    onEvent({ event: 'token', data: JSON.parse(e.data) });
  });

  eventSource.addEventListener('step_start', (e: MessageEvent) => {
    onEvent({ event: 'step_start', data: JSON.parse(e.data) });
  });

  eventSource.addEventListener('step_end', (e: MessageEvent) => {
    onEvent({ event: 'step_end', data: JSON.parse(e.data) });
  });

  eventSource.addEventListener('error', (e: MessageEvent) => {
    onEvent({ event: 'error', data: JSON.parse(e.data) });
  });

  eventSource.addEventListener('done', (e: MessageEvent) => {
    onEvent({ event: 'done', data: JSON.parse(e.data) });
  });

  eventSource.onerror = () => {
    eventSource.close();
  };

  return () => eventSource.close();
};

export const uploadFile = (conversationId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return client.post(`/conversations/${conversationId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data);
};
