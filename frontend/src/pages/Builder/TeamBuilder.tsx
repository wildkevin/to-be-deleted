import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getAgents, createTeam } from '../../api/agents';
import { createTeam as createTeamAPI } from '../../api/teams';

type Mode = 'sequential' | 'orchestrator' | 'loop';

export default function TeamBuilder() {
  const navigate = useNavigate();
  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => getAgents(),
  });

  const [form, setForm] = useState({
    name: '',
    description: '',
    mode: 'sequential' as Mode,
    selectedAgentIds: [] as string[],
    orchestrator_agent_id: '',
    loop_max_iterations: 5,
    loop_stop_signal: '',
  });

  const selectedAgents = agents?.items?.filter(a => form.selectedAgentIds.includes(a.id)) || [];

  const toggleAgent = (id: string) => {
    setForm(f => ({
      ...f,
      selectedAgentIds: f.selectedAgentIds.includes(id)
        ? f.selectedAgentIds.filter(i => i !== id)
        : [...f.selectedAgentIds, id]
    }));
  };

  const save = useMutation({
    mutationFn: async () => {
      return createTeamAPI({
        ...form,
        agents: selectedAgents.map((a, i) => ({
          agent_id: a.id,
          position: i + 1,
        })),
      });
    },
    onSuccess: () => navigate('/'),
  });

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-xl font-bold mb-6">New Team</h1>

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
          <label className="block text-sm font-medium text-gray-700 mb-2">Collaboration Mode</label>
          <div className="grid grid-cols-3 gap-3">
            {(['sequential', 'orchestrator', 'loop'] as Mode[]).map(m => (
              <button
                key={m}
                onClick={() => setForm(f => ({ ...f, mode: m }))}
                className={`border rounded p-3 text-sm text-left transition-colors ${
                  form.mode === m ? 'border-purple-600 bg-purple-50 text-purple-700' : 'hover:bg-gray-50'
                }`}
              >
                <div className="font-medium capitalize">{m}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {m === 'sequential' && 'Agents run in order'}
                  {m === 'orchestrator' && 'Lead agent routes tasks'}
                  {m === 'loop' && 'Agents cycle until done'}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select Agents {form.selectedAgentIds.length > 0 && `(${form.selectedAgentIds.length} selected)`}
          </label>
          <div className="space-y-1 max-h-48 overflow-y-auto border rounded p-2">
            {agents?.items?.map(a => (
              <label key={a.id} className="flex items-center gap-2 text-sm cursor-pointer p-1 hover:bg-gray-50 rounded">
                <input
                  type="checkbox"
                  checked={form.selectedAgentIds.includes(a.id)}
                  onChange={() => toggleAgent(a.id)}
                />
                <span className="font-medium">{a.name}</span>
                <span className="text-gray-400 text-xs">{a.model}</span>
              </label>
            ))}
          </div>
        </div>

        {form.mode === 'orchestrator' && selectedAgents.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lead Agent (Orchestrator)</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm"
              value={form.orchestrator_agent_id || ''}
              onChange={e => setForm(f => ({ ...f, orchestrator_agent_id: e.target.value }))}
            >
              <option value="">Select lead agent...</option>
              {selectedAgents.map((a: any) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {form.mode === 'loop' && (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Iterations</label>
              <input
                type="number"
                min={1}
                max={20}
                className="w-full border rounded px-3 py-2 text-sm"
                value={form.loop_max_iterations}
                onChange={e => setForm(f => ({ ...f, loop_max_iterations: +e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stop Signal <span className="text-gray-400 font-normal">(optional keyword to stop early)</span>
              </label>
              <input
                className="w-full border rounded px-3 py-2 text-sm"
                placeholder="e.g. APPROVED"
                value={form.loop_stop_signal}
                onChange={e => setForm(f => ({ ...f, loop_stop_signal: e.target.value }))}
              />
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            onClick={() => save.mutate()}
            disabled={save.isPending || form.selectedAgentIds.length === 0}
            className="bg-purple-600 text-white px-6 py-2 rounded hover:bg-purple-700 text-sm disabled:opacity-50"
          >
            {save.isPending ? 'Saving...' : 'Save Team'}
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
