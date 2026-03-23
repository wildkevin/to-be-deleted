import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getAgents } from '../../api/agents';
import { createConversation } from '../../api/conversations';
import ChatWindow from '../../components/ChatWindow';

export default function Playground() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const [conversationId, setConversationId] = useState<string>('');

  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => getAgents(),
  });

  const agentOrTeam = agents?.items?.find(a => a.id === id) ||
    { id, name: type === 'team' ? 'Team' : 'Agent', description: '' };

  useEffect(() => {
    const initConversation = async () => {
      try {
        const conv = await createConversation({
          [type === 'team' ? 'team_id' : 'agent_id']: id,
          title: `${agentOrTeam.name} - ${new Date().toLocaleDateString()}`,
        });
        setConversationId(conv.id);
      } catch (error) {
        console.error('Failed to create conversation:', error);
      }
    };
    initConversation();
  }, [id, type, agentOrTeam.name]);

  if (!conversationId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading conversation...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <nav className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <button onClick={() => navigate('/')} className="text-gray-500 hover:text-gray-700 text-sm mb-1">
              ← Back to Hub
            </button>
            <h1 className="text-xl font-bold text-gray-900">{agentOrTeam.name}</h1>
            <p className="text-sm text-gray-600">{agentOrTeam.description}</p>
          </div>
          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium capitalize">
            {type}
          </span>
        </div>
      </nav>

      <div className="flex-1 max-w-4xl mx-auto w-full bg-white shadow-sm">
        <ChatWindow
          conversationId={conversationId}
          onNewMessage={() => {}}
        />
      </div>
    </div>
  );
}
