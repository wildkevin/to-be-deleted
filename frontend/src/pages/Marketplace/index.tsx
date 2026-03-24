import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getMarketplaceItems } from '../../api/marketplace';

export default function Marketplace() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<'mcp' | 'skill'>('mcp');

  const { data: mcpItems } = useQuery({
    queryKey: ['marketplace', 'mcp'],
    queryFn: () => getMarketplaceItems('mcp'),
  });

  const { data: skillItems } = useQuery({
    queryKey: ['marketplace', 'skill'],
    queryFn: () => getMarketplaceItems('skill'),
  });

  const items = tab === 'mcp' ? mcpItems?.items || [] : skillItems?.items || [];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Marketplace</h1>
        <button
          onClick={() => navigate('/marketplace/submit')}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm"
        >
          Submit Item
        </button>
      </div>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setTab('mcp')}
          className={`px-4 py-2 rounded text-sm font-medium ${
            tab === 'mcp' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          MCP Servers
        </button>
        <button
          onClick={() => setTab('skill')}
          className={`px-4 py-2 rounded text-sm font-medium ${
            tab === 'skill' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Skills
        </button>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No {tab === 'mcp' ? 'MCP servers' : 'skills'} available
        </div>
      ) : (
        <div className="space-y-4">
          {items.map(item => (
            <div key={item.id} className="border rounded-lg p-4 hover:shadow-sm transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{item.name}</h3>
                  <p className="text-gray-600 text-sm mt-1">{item.description}</p>
                  {tab === 'mcp' && item.discovered_tools && item.discovered_tools.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500 font-medium">Available Tools:</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {item.discovered_tools.map(tool => (
                          <span key={tool} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  item.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {item.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
