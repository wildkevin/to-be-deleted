import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { submitMarketplaceItem } from '../../api/marketplace';

export default function SubmitItem() {
  const navigate = useNavigate();
  const [type, setType] = useState<'mcp' | 'skill'>('mcp');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    serverUrl: '',
    authHeaders: '{}',
    functionName: '',
    inputSchema: '{}',
    outputSchema: '{}',
  });
  const [file, setFile] = useState<File | null>(null);

  const submit = useMutation({
    mutationFn: async () => {
      const data = new FormData();
      data.append('name', formData.name);
      data.append('description', formData.description);
      data.append('type', type);

      if (type === 'mcp') {
        data.append('server_url', formData.serverUrl);
        data.append('auth_headers', formData.authHeaders);
      } else {
        data.append('function_name', formData.functionName);
        data.append('input_schema', formData.inputSchema);
        data.append('output_schema', formData.outputSchema);
        if (file) {
          data.append('file', file);
        }
      }

      return submitMarketplaceItem(data);
    },
    onSuccess: () => {
      alert('Item submitted successfully! It will be available once approved by an admin.');
      navigate('/marketplace');
    },
    onError: (error: any) => {
      alert(`Submission failed: ${error.response?.data?.detail || error.message}`);
    },
  });

  const validateJson = (jsonStr: string) => {
    try {
      JSON.parse(jsonStr);
      return true;
    } catch {
      return false;
    }
  };

  const isSubmitDisabled = !formData.name || !formData.description ||
    (type === 'mcp' && !formData.serverUrl) ||
    (type === 'skill' && (!formData.functionName || !file)) ||
    (type === 'skill' && !validateJson(formData.inputSchema)) ||
    (type === 'skill' && !validateJson(formData.outputSchema)) ||
    (type === 'mcp' && !validateJson(formData.authHeaders));

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Submit to Marketplace</h1>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setType('mcp')}
              className={`px-4 py-2 rounded text-sm font-medium ${
                type === 'mcp' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              MCP Server
            </button>
            <button
              type="button"
              onClick={() => setType('skill')}
              className={`px-4 py-2 rounded text-sm font-medium ${
                type === 'skill' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Skill
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            type="text"
            className="w-full border rounded px-3 py-2 text-sm"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            placeholder="Enter a descriptive name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            className="w-full border rounded px-3 py-2 text-sm h-24"
            value={formData.description}
            onChange={e => setFormData({ ...formData, description: e.target.value })}
            placeholder="Describe what this item does"
          />
        </div>

        {type === 'mcp' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Server URL</label>
              <input
                type="url"
                className="w-full border rounded px-3 py-2 text-sm"
                value={formData.serverUrl}
                onChange={e => setFormData({ ...formData, serverUrl: e.target.value })}
                placeholder="https://your-mcp-server.com"
              />
              <p className="text-xs text-gray-500 mt-1">The system will attempt to discover tools from this URL</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Auth Headers (JSON)
              </label>
              <textarea
                className="w-full border rounded px-3 py-2 text-sm h-24 font-mono"
                value={formData.authHeaders}
                onChange={e => setFormData({ ...formData, authHeaders: e.target.value })}
                placeholder='{"Authorization": "Bearer your-token"}'
              />
              {!validateJson(formData.authHeaders) && (
                <p className="text-xs text-red-600 mt-1">Invalid JSON</p>
              )}
            </div>
          </>
        )}

        {type === 'skill' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Function Name
              </label>
              <input
                type="text"
                className="w-full border rounded px-3 py-2 text-sm"
                value={formData.functionName}
                onChange={e => setFormData({ ...formData, functionName: e.target.value })}
                placeholder="function_to_call"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Input Schema (JSON Schema)
              </label>
              <textarea
                className="w-full border rounded px-3 py-2 text-sm h-24 font-mono"
                value={formData.inputSchema}
                onChange={e => setFormData({ ...formData, inputSchema: e.target.value })}
                placeholder='{"type": "object", "properties": {...}}'
              />
              {!validateJson(formData.inputSchema) && (
                <p className="text-xs text-red-600 mt-1">Invalid JSON</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Output Schema (JSON Schema)
              </label>
              <textarea
                className="w-full border rounded px-3 py-2 text-sm h-24 font-mono"
                value={formData.outputSchema}
                onChange={e => setFormData({ ...formData, outputSchema: e.target.value })}
                placeholder='{"type": "object", "properties": {...}}'
              />
              {!validateJson(formData.outputSchema) && (
                <p className="text-xs text-red-600 mt-1">Invalid JSON</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Python File (.py)
              </label>
              <input
                type="file"
                accept=".py"
                className="w-full border rounded px-3 py-2 text-sm"
                onChange={e => setFile(e.target.files?.[0] || null)}
              />
            </div>
          </>
        )}

        <div className="flex gap-3 pt-2">
          <button
            onClick={() => submit.mutate()}
            disabled={isSubmitDisabled || submit.isPending}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 text-sm disabled:opacity-50"
          >
            {submit.isPending ? 'Submitting...' : 'Submit'}
          </button>
          <button
            onClick={() => navigate('/marketplace')}
            className="border px-6 py-2 rounded hover:bg-gray-50 text-sm"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
