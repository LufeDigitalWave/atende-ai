import { useEffect, useState } from 'react';
import { useSessionStore } from '../lib/store';
import ChatWindow from '../components/chat/ChatWindow';
import CRMView from '../components/crm/CRMView';
import NicheSelector from '../components/NicheSelector';
import { createSession } from '../lib/api';

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

export default function Demo() {
  const { sessionId, setSessionId } = useSessionStore();
  const [agentMeta, setAgentMeta] = useState<AgentMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  useEffect(() => {
    if (sessionId && !agentMeta && !isCreatingSession) {
      setSessionId(null as unknown as string);
      useSessionStore.getState().reset();
    }
  }, [agentMeta, isCreatingSession, sessionId, setSessionId]);

  const handleNicheSelect = async (niche: string) => {
    setLoading(true);
    setIsCreatingSession(true);
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
      setIsCreatingSession(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar sessão');
      setLoading(false);
      setIsCreatingSession(false);
    }
  };

  if (!sessionId || !agentMeta) {
    return (
      <>
        {error && (
          <div className="fixed left-1/2 top-4 z-50 -translate-x-1/2 rounded-lg border border-red-700 bg-red-900/50 px-4 py-2 text-sm text-red-200 shadow-md">
            {error}
          </div>
        )}
        <NicheSelector onSelect={handleNicheSelect} loading={loading} />
      </>
    );
  }

  return (
    <div className="relative flex h-screen flex-col overflow-hidden bg-dark-bg">
      <div className="fixed left-1/4 top-1/4 -z-10 h-96 w-96 rounded-full bg-brand-violet opacity-10 blur-3xl" />
      <div className="fixed bottom-1/4 right-1/4 -z-10 h-96 w-96 rounded-full bg-brand-cyan opacity-10 blur-3xl" />

      <div className="z-20 bg-gradient-to-r from-brand-violet to-brand-cyan px-6 py-4 text-white shadow-lg">
        <div className="flex items-center justify-between gap-4">
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
            className="min-h-11 rounded-full bg-white/20 px-4 py-2 text-xs font-semibold transition-colors hover:bg-white/30"
          >
            Trocar nicho
          </button>
        </div>
      </div>

      <main className="flex flex-1 items-center justify-center overflow-hidden p-2 lg:p-6">
        <div
          className="flex h-full w-full max-w-5xl flex-col overflow-hidden rounded-2xl border-4 border-gray-300 bg-white p-2 shadow-2xl lg:flex-row lg:gap-4 lg:border-8 lg:p-4"
          style={{ boxShadow: '0 20px 60px rgba(168, 85, 247, 0.15), 0 0 100px rgba(6, 182, 212, 0.1)' }}
        >
          <div className="flex min-h-0 min-w-0 flex-1 flex-col">
            <ChatWindow
              sessionId={sessionId!}
              agentName={agentMeta.agentName}
              companyName={agentMeta.companyName}
              suggestions={agentMeta.suggestions}
              contactUrl={agentMeta.contactUrl}
            />
          </div>

          <aside className="flex max-h-60 w-full flex-col overflow-auto border-t border-gray-200 pt-3 lg:max-h-none lg:w-80 lg:border-l lg:border-t-0 lg:pl-4 lg:pt-0">
            <div className="mb-4 text-xs font-semibold uppercase tracking-wider text-gray-700">
              CRM ao vivo
            </div>
            <div className="flex-1 overflow-auto">
              <CRMView crmFields={agentMeta.crmFields} />
            </div>
          </aside>
        </div>
      </main>

      <footer className="z-10 border-t border-gray-700 bg-dark-surface/50 px-6 py-3 text-xs text-gray-500">
        <p>Simulação de atendimento ({agentMeta.niche}). Em produção, este agente opera no WhatsApp oficial via Meta Cloud API.</p>
      </footer>
    </div>
  );
}
