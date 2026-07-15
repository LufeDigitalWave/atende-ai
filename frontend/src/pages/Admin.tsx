import { useState, useEffect } from 'react';
import {
  adminLogin,
  listSessions,
  getKanban,
  getCosts,
  getAgentInfo,
  type AdminSession,
  type AdminCostsResponse,
  type AdminAgentInfo,
  type AdminKanban,
} from '../lib/admin-api';
import AdminConversas from './admin/AdminConversas';
import AdminLeads from './admin/AdminLeads';
import AdminCustos from './admin/AdminCustos';
import AdminAgente from './admin/AdminAgente';

type Tab = 'conversas' | 'leads' | 'custos' | 'agente';

export default function Admin() {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('admin_token');
  });
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('conversas');

  // Cache data per tab
  const [sessions, setSessions] = useState<AdminSession[]>([]);
  const [kanban, setKanban] = useState<AdminKanban | null>(null);
  const [costs, setCosts] = useState<AdminCostsResponse | null>(null);
  const [agentInfo, setAgentInfo] = useState<AdminAgentInfo | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const { token } = await adminLogin(username, password);
      localStorage.setItem('admin_token', token);
      setToken(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setToken(null);
    setSessions([]);
    setKanban(null);
    setCosts(null);
    setAgentInfo(null);
  };

  // Load tab data
  useEffect(() => {
    if (!token) return;

    const loadData = async () => {
      try {
        if (activeTab === 'conversas' && sessions.length === 0) {
          const data = await listSessions(token);
          setSessions(data.items);
        }
        if (activeTab === 'leads' && !kanban) {
          const data = await getKanban(token);
          setKanban(data);
        }
        if (activeTab === 'custos' && !costs) {
          const data = await getCosts(token);
          setCosts(data);
        }
        if (activeTab === 'agente' && !agentInfo) {
          const data = await getAgentInfo(token);
          setAgentInfo(data);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load');
      }
    };

    loadData();
  }, [token, activeTab, sessions.length, kanban, costs, agentInfo]);

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-sm w-full">
          <h1 className="text-2xl font-bold mb-6 text-center">🔐 Admin Login</h1>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-sofia-500"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-sofia-500"
            />
            {error && <p className="text-red-600 text-xs">{error}</p>}
            <button
              type="submit"
              className="w-full px-4 py-2 bg-sofia-500 text-white rounded font-medium hover:bg-sofia-600 transition-colors"
            >
              Entrar
            </button>
          </form>
          <p className="text-xs text-gray-500 mt-4 text-center">
            Demo: admin / admin
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Admin · Atende AI</h1>
          <p className="text-xs text-gray-500">Clínica Renova</p>
        </div>
        <button
          onClick={handleLogout}
          className="text-xs text-gray-600 hover:text-gray-900"
        >
          Sair →
        </button>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-6">
          {(['conversas', 'leads', 'custos', 'agente'] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 text-sm font-medium border-b-2 ${
                activeTab === tab
                  ? 'border-sofia-500 text-sofia-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab === 'conversas' && '💬 Conversas'}
              {tab === 'leads' && '👤 Leads (Kanban)'}
              {tab === 'custos' && '💰 Custos'}
              {tab === 'agente' && '🤖 Agente'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-6">
        {activeTab === 'conversas' && <AdminConversas sessions={sessions} />}
        {activeTab === 'leads' && kanban && <AdminLeads kanban={kanban} />}
        {activeTab === 'custos' && costs && <AdminCustos costs={costs} />}
        {activeTab === 'agente' && agentInfo && <AdminAgente info={agentInfo} />}
      </div>
    </div>
  );
}