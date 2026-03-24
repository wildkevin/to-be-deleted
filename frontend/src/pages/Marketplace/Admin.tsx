import { useQuery, useMutation } from '@tanstack/react-query';
import { getPendingItems, approveItem, rejectItem } from '../../api/marketplace';

export default function MarketplaceAdmin() {
  const { data: pendingData, refetch } = useQuery({
    queryKey: ['marketplace', 'pending'],
    queryFn: getPendingItems,
  });

  const approve = useMutation({
    mutationFn: approveItem,
    onSuccess: () => refetch(),
  });

  const reject = useMutation({
    mutationFn: rejectItem,
    onSuccess: () => refetch(),
  });

  const items = pendingData?.items || [];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Marketplace Admin</h1>

      {items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No pending items
        </div>
      ) : (
        <div className="space-y-4">
          {items.map(item => (
            <div key={item.id} className="border rounded-lg p-4 bg-white">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                      item.type === 'mcp' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                    }`}>
                      {item.type.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="font-semibold text-lg mt-2">{item.name}</h3>
                  <p className="text-gray-600 text-sm mt-1">{item.description}</p>

                  {item.type === 'mcp' && (
                    <div className="mt-3 space-y-2">
                      <div>
                        <p className="text-xs text-gray-500 font-medium">Server URL:</p>
                        <p className="text-sm font-mono bg-gray-50 px-2 py-1 rounded mt-1">
                          {item.config?.server_url}
                        </p>
                      </div>
                      {item.auth_headers && Object.keys(JSON.parse(item.auth_headers || '{}')).length > 0 && (
                        <div>
                          <p className="text-xs text-gray-500 font-medium">Auth Headers:</p>
                          <p className="text-sm font-mono bg-gray-50 px-2 py-1 rounded mt-1">
                            {item.auth_headers}
                          </p>
                        </div>
                      )}
                      {item.discovered_tools && item.discovered_tools.length > 0 && (
                        <div>
                          <p className="text-xs text-gray-500 font-medium">Discovered Tools:</p>
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
                  )}

                  {item.type === 'skill' && (
                    <div className="mt-3 space-y-2">
                      <div>
                        <p className="text-xs text-gray-500 font-medium">Function Name:</p>
                        <p className="text-sm font-mono bg-gray-50 px-2 py-1 rounded mt-1">
                          {item.config?.function_name}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 font-medium">File:</p>
                        <p className="text-sm font-mono bg-gray-50 px-2 py-1 rounded mt-1">
                          {item.file_path}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => {
                      if (confirm(`Approve "${item.name}"?`)) {
                        approve.mutate(item.id);
                      }
                    }}
                    disabled={approve.isPending || reject.isPending}
                    className="bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 text-sm disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Reject "${item.name}"?`)) {
                        reject.mutate(item.id);
                      }
                    }}
                    disabled={approve.isPending || reject.isPending}
                    className="bg-red-600 text-white px-3 py-1.5 rounded hover:bg-red-700 text-sm disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
