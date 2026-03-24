import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getAgents } from '../../api/agents';
import { getTeams } from '../../api/teams';
import { getMarketplaceItems } from '../../api/marketplace';
import ItemCard from '../../components/ItemCard';

export default function Hub() {
  const { data: agents } = useQuery({
    queryKey: ['agents'],
    queryFn: () => getAgents(),
  });

  const { data: teams } = useQuery({
    queryKey: ['teams'],
    queryFn: () => getTeams(),
  });

  const { data: mcps } = useQuery({
    queryKey: ['marketplace', 'mcp'],
    queryFn: () => getMarketplaceItems('mcp'),
  });

  const { data: skills } = useQuery({
    queryKey: ['marketplace', 'skill'],
    queryFn: () => getMarketplaceItems('skill'),
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">CCM Agent Hub</h1>
          <div className="flex gap-4">
            <Link
              to="/builder/agent"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              + New Agent
            </Link>
            <Link
              to="/builder/team"
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 text-sm font-medium"
            >
              + New Team
            </Link>
            <Link
              to="/marketplace"
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium"
            >
              Marketplace
            </Link>
            <Link
              to="/marketplace/admin"
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 text-sm font-medium"
            >
              Admin
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Agents</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents?.items?.map(agent => (
              <ItemCard
                key={agent.id}
                type="agent"
                id={agent.id}
                name={agent.name}
                description={agent.description}
                model={agent.model}
              />
            ))}
            {agents?.items?.length === 0 && (
              <div className="col-span-full text-center py-8 text-gray-500">
                No agents yet. Create your first agent!
              </div>
            )}
          </div>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Teams</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams?.items?.map(team => (
              <ItemCard
                key={team.id}
                type="team"
                id={team.id}
                name={team.name}
                description={team.description}
                mode={team.mode}
              />
            ))}
            {teams?.items?.length === 0 && (
              <div className="col-span-full text-center py-8 text-gray-500">
                No teams yet. Create your first team!
              </div>
            )}
          </div>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">MCP Tools</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mcps?.items?.map(mcp => (
              <ItemCard
                key={mcp.id}
                type="mcp"
                id={mcp.id}
                name={mcp.name}
                description={mcp.description}
                status={mcp.status}
              />
            ))}
            {mcps?.items?.length === 0 && (
              <div className="col-span-full text-center py-8 text-gray-500">
                No MCP tools available yet.
              </div>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Skills</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {skills?.items?.map(skill => (
              <ItemCard
                key={skill.id}
                type="skill"
                id={skill.id}
                name={skill.name}
                description={skill.description}
                status={skill.status}
              />
            ))}
            {skills?.items?.length === 0 && (
              <div className="col-span-full text-center py-8 text-gray-500">
                No skills available yet.
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
