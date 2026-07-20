import { useState } from 'react';
import { useSessionStore } from './lib/store';
import ChatWindow from './components/chat/ChatWindow';
import CRMView from './components/crm/CRMView';
import NicheSelector from './components/NicheSelector';
import { createSession } from './lib/api';

interface CRMField {
  key: string;
  label: string;
  priority: string;
}

interface AgentMeta {
  agentName: string;
  companyName: string;
  niche: string;
  suggestions: string[];
  openingMessage?: string;
  crmFields: CRMField[];
  businessMode: string;
  contactUrl: string;
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
        openingMessage: data.opening_message,
        crmFields: data.crm_fields || [],
        businessMode: data.business_mode || 'mixed',
        contactUrl: data.contact_url || 'https://wa.me/5511999999999',
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
          <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 rounded-lg text-sm shadow-md z-50">
            {error}
          </div>
        )}
        <NicheSelector onSelect={handleNicheSelect} loading={loading} />
      </>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-dark-bg relative overflow-hidden">
      {/* Gradient orbs (background) */}
      <div className="fixed top-1/4 left-1/4 w-96 h-96 bg-brand-violet rounded-full opacity-10 blur-3xl -z-10" />
      <div className="fixed bottom-1/4 right-1/4 w-96 h-96 bg-brand-cyan rounded-full opacity-10 blur-3xl -z-10" />

      {/* Header with gradient */}
      <div className="bg-gradient-to-r from-brand-violet to-brand-cyan text-white px-6 py-4 shadow-lg z-20">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">
              {agentMeta.companyName} — {agentMeta.agentName} (SDR IA)
            </h1>
            <p className="text-sm opacity-90">
              Converse com {agentMeta.agentName} e veja seu lead sendo qualificado em tempo real
            </p>
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

      {/* Main layout — device frame effect */}
      <div className="flex-1 overflow-hidden flex items-center justify-center p-2 lg:p-6">
        <div className="w-full h-full max-w-5xl rounded-2xl border-4 lg:border-8 border-gray-300 bg-white shadow-2xl overflow-hidden flex flex-col lg:flex-row gap-0 lg:gap-4 p-2 lg:p-4" style={{
          boxShadow: '0 20px 60px rgba(168, 85, 247, 0.15), 0 0 100px rgba(6, 182, 212, 0.1)',
        }}>
          {/* Chat */}
          <div className="flex-1 flex flex-col min-w-0 min-h-0">
            <ChatWindow
              sessionId={sessionId!}
              agentName={agentMeta.agentName}
              companyName={agentMeta.companyName}
              suggestions={agentMeta.suggestions}
              contactUrl={agentMeta.contactUrl}
            />
          </div>

          {/* CRM ao vivo — abaixo em mobile, lateral em desktop */}
          <div className="w-full lg:w-80 border-t lg:border-t-0 lg:border-l border-gray-200 pt-3 lg:pt-0 lg:pl-4 flex flex-col max-h-60 lg:max-h-none overflow-auto">
            <div className="text-xs font-semibold text-gray-700 mb-4 uppercase tracking-wider">
              📊 CRM ao vivo
            </div>
            <div className="flex-1 overflow-auto">
              <CRMView crmFields={agentMeta.crmFields} />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-700 bg-dark-surface/50 px-6 py-3 text-xs text-gray-500 z-10">
        <p>Simulação de atendimento ({agentMeta.niche}). Em produção, este agente opera no WhatsApp oficial via Meta Cloud API.</p>
      </div>
    </div>
  );
}

export default App;
