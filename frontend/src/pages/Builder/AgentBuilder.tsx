import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createAgent, getAgent, updateAgent } from '../../api/agents';
import { getMarketplaceItems } from '../../api/marketplace';

export default function AgentBuilder() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const agentId = searchParams.get('id');
  const isEditing = !!agentId;

  const { data: agent } = useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => getAgent(agentId!),
    enabled: isEditing,
  });

  const { data: mcps } = useQuery({
    queryKey: ['marketplace', 'mcp'],
    queryFn: () => getMarketplaceItems('mcp'),
  });

  const { data: skillItems } = useQuery({
    queryKey: ['marketplace', 'skill'],
    queryFn: () => getMarketplaceItems('skill'),
  });

  const [form, setForm] = useState({
    name: '',
    description: '',
    model: 'gpt-4o',
    system_prompt: '',
    selectedMCPIds: [] as string[],
    selectedSkillIds: [] as string[],
  });

  useEffect(() => {
    if (agent) {
      setForm({
        name: agent.name,
        description: agent.description,
        model: agent.model,
        system_prompt: agent.system_prompt,
        selectedMCPIds: agent.mcp_tools?.map((t: any) => t.id) || [],
        selectedSkillIds: agent.skills?.map((s: any) => s.id) || [],
      });
    }
  }, [agent]);

  const toggleMCP = (id: string) => {
    setForm(f => ({
      ...f,
      selectedMCPIds: f.selectedMCPIds.includes(id)
        ? f.selectedMCPIds.filter(i => i !== id)
        : [...f.selectedMCPIds, id]
    }));
  };

  const toggleSkill = (id: string) => {
    setForm(f => ({
      ...f,
      selectedSkillIds: f.selectedSkillIds.includes(id)
        ? f.selectedSkillIds.filter(i => i !== id)
        : [...f.selectedSkillIds, id]
    }));
  };

  const save = useMutation({
    mutationFn: async () => {
      const mcpTools = mcps?.items
        ?.filter((m: any) => form.selectedMCPIds.includes(m.id))
        .map((m: any) => ({ id: m.id, name: m.name, item_type: m.item_type })) || [];

      const skillTools = skillItems?.items
        ?.filter((s: any) => form.selectedSkillIds.includes(s.id))
        .map((s: any) => ({ id: s.id, name: s.name, item_type: s.item_type })) || [];

      const agentData = {
        ...form,
        mcp_tools: mcpTools,
        skills: skillTools,
      };

      if (isEditing && agentId) {
        return updateAgent(agentId, agentData);
      }

      return createAgent(agentData);
    },
    onSuccess: () => navigate('/'),
  });

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-xl font-bold mb-6">{isEditing ? 'Edit Agent' : 'New Agent'}</h1>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            className="w-full border rounded px-3 py-2 text-sm"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <input
            className="w-full border rounded px-3 py-2 text-sm"
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
          <select
            className="w-full border rounded px-3 py-2 text-sm"
            value={form.model}
            onChange={e => setForm(f => ({ ...f, model: e.target.value }))}
          >
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-4-turbo">GPT-4 Turbo</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
          <textarea
            className="w-full border rounded px-3 py-2 text-sm h-32"
            value={form.system_prompt}
            onChange={e => setForm(f => ({ ...f, system_prompt: e.target.value }))}
            placeholder="Define the agent's role and instructions..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            MCP Tools {form.selectedMCPIds.length > 0 && `(${form.selectedMCPIds.length} selected)`}
          </label>
          <div className="space-y-1 max-h-48 overflow-y-auto border rounded p-2">
            {mcps?.items?.map(m => (
              <label key={m.id} className="flex items-center gap-2 text-sm cursor-pointer p-1 hover:bg-gray-50 rounded">
                <input
                  type="checkbox"
                  checked={form.selectedMCPIds.includes(m.id)}
                  onChange={() => toggleMCP(m.id)}
                />
                <span className="font-medium">{m.name}</span>
                {m.status !== 'approved' && (
                  <span className="text-xs text-gray-400">({m.status})</span>
                )}
              </label>
            ))}
            {!mcps?.items?.length && (
              <div className="text-sm text-gray-500">No MCP tools available</div>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Skills {form.selectedSkillIds.length > 0 && `(${form.selectedSkillIds.length} selected)`}
          </label>
          <div className="space-y-1 max-h-48 overflow-y-auto border rounded p-2">
            {skillItems?.items?.map((s: any) => (
              <label key={s.id} className="flex items-center gap-2 text-sm cursor-pointer p-1 hover:bg-gray-50 rounded">
                <input
                  type="checkbox"
                  checked={form.selectedSkillIds.includes(s.id)}
                  onChange={() => toggleSkill(s.id)}
                />
                <span className="font-medium">{s.name}</span>
                {s.status !== 'approved' && (
                  <span className="text-xs text-gray-400">({s.status})</span>
                )}
              </label>
            ))}
            {!skillItems?.items?.length && (
              <div className="text-sm text-gray-500">No skills available</div>
            )}
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            onClick={() => save.mutate()}
            disabled={save.isPending || !form.name}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 text-sm disabled:opacity-50"
          >
            {save.isPending ? 'Saving...' : 'Save Agent'}
          </button>
          <button
            onClick={() => navigate('/')}
            className="border px-6 py-2 rounded hover:bg-gray-50 text-sm"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
