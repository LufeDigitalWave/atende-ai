import { useState } from 'react';
import { useSessionStore } from './lib/store';
import ChatWindow from './components/chat/ChatWindow';
import CRMView from './components/crm/CRMView';
import NicheSelector from './components/NicheSelector';
import { createSession } from './lib/api';

interface AgentMeta {
  agentName: string;
  companyName: string;
  niche: string;
  suggestions: string[];
}

function App() {
  const { sessionId, setSessionId } = useSessionStore();
  const [agentMeta, setAgentMeta] = useState<AgentMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleNicheSelect = async (niche: string) => {
    setLoading(true);
    setError(null);

    try {
      const data = await createSession(niche);
      setSessionId(data.session_id);
      setAgentMeta({
        agentName: data.agent_name || 'Sofia',
        companyName: data.company_name || 'Empresa Demo',
        niche: data.niche || niche,
        suggestions: data.suggestions || [
          'Quero saber mais sobre seus serviços',
          'Quanto custa?',
          'Vocês atendem hoje?',
        ],
      });
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar sessão');
      setLoading(false);
    }
  };

  // Show niche selector if no session yet
  if (!sessionId || !agentMeta) {
    return (
      <>
        {error && (
          <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-red-50 text-red-700 px-4 py-2 rounded-lg text-sm shadow-md z-50">
            {error}
          </div>
        )}
        <NicheSelector onSelect={handleNicheSelect} loading={loading} />
      </>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header — dynamic */}
      <div className="bg-gradient-to-r from-sofia-500 to-sofia-600 text-white px-6 py-4 shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">{agentMeta.companyName} — {agentMeta.agentName} (SDR IA)</h1>
            <p className="text-sm opacity-90">Converse com {agentMeta.agentName} e veja seu lead sendo qualificado em tempo real</p>
          </div>
          <button
            onClick={() => {
              setSessionId(null as unknown as string);
              setAgentMeta(null);
              useSessionStore.getState().reset();
            }}
            className="text-xs bg-white/20 px-3 py-1 rounded-full hover:bg-white/30 transition-colors"
          >
            Trocar nicho
          </button>
        </div>
      </div>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden gap-4 p-4">
        {/* Chat (left) */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatWindow
            sessionId={sessionId!}
            agentName={agentMeta.agentName}
            companyName={agentMeta.companyName}
            suggestions={agentMeta.suggestions}
          />
        </div>

        {/* CRM ao vivo (right) */}
        <CRMView />
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 bg-gray-50 px-6 py-3 text-xs text-gray-600">
        <p>Simulação de atendimento ({agentMeta.niche}). Em produção, este agente opera no WhatsApp oficial via Meta Cloud API.</p>
      </div>
    </div>
  );
}

export default App;
