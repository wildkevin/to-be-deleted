import { Link } from 'react-router-dom';

interface ItemCardProps {
  type: 'agent' | 'team' | 'mcp' | 'skill';
  id: string;
  name: string;
  description: string;
  model?: string;
  mode?: string;
  status?: string;
  onEdit?: () => void;
}

export default function ItemCard({ type, id, name, description, model, mode, status, onEdit }: ItemCardProps) {
  const typeColors = {
    agent: 'bg-blue-100 text-blue-700 border-blue-300',
    team: 'bg-purple-100 text-purple-700 border-purple-300',
    mcp: 'bg-green-100 text-green-700 border-green-300',
    skill: 'bg-orange-100 text-orange-700 border-orange-300',
  };

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  };

  const getLink = () => {
    if (type === 'agent' || type === 'team') {
      return `/playground/${type}/${id}`;
    }
    return '#';
  };

  const getEditLink = () => {
    if (type === 'agent') {
      return `/builder/agent?id=${id}`;
    }
    if (type === 'team') {
      return `/builder/team?id=${id}`;
    }
    return '#';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <span className={`px-2 py-1 text-xs font-medium rounded border ${typeColors[type]}`}>
          {type}
        </span>
        {status && (
          <span className={`px-2 py-1 text-xs font-medium rounded ${statusColors[status as keyof typeof statusColors]}`}>
            {status}
          </span>
        )}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-1">{name}</h3>
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{description}</p>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex gap-2">
          {model && <span>{model}</span>}
          {mode && <span>• {mode}</span>}
        </div>
        <div className="flex gap-3">
          {(type === 'agent' || type === 'team') && (
            <Link to={getEditLink()} className="text-gray-600 hover:text-gray-800 font-medium">
              Edit
            </Link>
          )}
          {type !== 'mcp' && type !== 'skill' && (
            <Link to={getLink()} className="text-blue-600 hover:text-blue-700 font-medium">
              Open →
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
