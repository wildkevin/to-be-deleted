import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Hub from './pages/Hub';
import AgentBuilder from './pages/Builder/AgentBuilder';
import TeamBuilder from './pages/Builder/TeamBuilder';
import Playground from './pages/Playground';
import Marketplace from './pages/Marketplace';
import SubmitItem from './pages/Marketplace/Submit';
import MarketplaceAdmin from './pages/Marketplace/Admin';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Hub />} />
          <Route path="/builder/agent" element={<AgentBuilder />} />
          <Route path="/builder/team" element={<TeamBuilder />} />
          <Route path="/playground/:type/:id" element={<Playground />} />
          <Route path="/marketplace" element={<Marketplace />} />
          <Route path="/marketplace/submit" element={<SubmitItem />} />
          <Route path="/marketplace/admin" element={<MarketplaceAdmin />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
