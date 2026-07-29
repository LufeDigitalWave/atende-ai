import { ArrowRight, Bot, CheckCircle2, Database, Gauge, MessageCircle, ShieldCheck, Workflow } from 'lucide-react';
import { Link } from 'react-router-dom';
import AgentCard from './components/marketing/AgentCard';
import CTASection from './components/marketing/CTASection';
import SiteHeader from './components/marketing/SiteHeader';
import { WHATSAPP_AGENTS } from './data/agents';
import { CONTACT_URL } from './lib/constants';
import { trackFunnel } from './lib/funnel';
import { useEffect } from 'react';

const proofItems = [
  'WhatsApp Cloud API oficial',
  'CRM ao vivo',
  'FastAPI + React + pgvector',
  'Guardrails de custo',
];

const differentiators = [
  {
    title: 'Entende intenção, não só palavras-chave',
    description: 'O agente identifica se o cliente quer comprar, agendar, tirar dúvida, reclamar ou falar com humano.',
    icon: Bot,
  },
  {
    title: 'Atualiza sistemas reais',
    description: 'Cada conversa pode criar lead, preencher CRM, abrir ticket, consultar agenda ou acionar um workflow n8n.',
    icon: Workflow,
  },
  {
    title: 'Responde com base autorizada',
    description: 'Preços, regras e políticas vêm de base de conhecimento versionada. Se não souber, encaminha com segurança.',
    icon: Database,
  },
  {
    title: 'Nasce com limites operacionais',
    description: 'Rate limit, budget diário, kill switch e logs reduzem risco de custo surpresa e comportamento fora do esperado.',
    icon: Gauge,
  },
];

export default function App() {
  useEffect(() => { trackFunnel('view_landing'); }, []);

  return (
    <div className="min-h-screen bg-dark-bg text-white">
      <SiteHeader />
      <main>
        <section className="relative overflow-hidden px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
          <div className="absolute left-1/2 top-12 h-96 w-96 -translate-x-1/2 rounded-full bg-brand-violet/20 blur-3xl" aria-hidden="true" />
          <div className="absolute right-0 top-1/3 h-80 w-80 rounded-full bg-brand-cyan/10 blur-3xl" aria-hidden="true" />

          <div className="relative mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
            <div>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-gray-200">
                <ShieldCheck className="h-4 w-4 text-brand-cyan" aria-hidden="true" />
                Agentes IA para WhatsApp, CRM e atendimento humano
              </div>

              <h1 className="max-w-4xl text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
                Agentes de IA para WhatsApp que respondem, qualificam e encaminham leads 24/7.
              </h1>

              <p className="mt-6 max-w-2xl text-lg leading-8 text-gray-300">
                Transforme o WhatsApp da sua empresa em um agente operacional conectado a CRM, agenda, base de conhecimento e equipe humana.
              </p>

              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <Link
                  to="/demo"
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold text-dark-bg transition-transform hover:-translate-y-0.5 hover:bg-gray-100"
                >
                  Testar demo SDR
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </Link>
                <a
                  href={CONTACT_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-white/15 px-6 py-3 text-sm font-bold text-white transition-colors hover:bg-white/10"
                >
                  Pedir piloto no WhatsApp
                  <MessageCircle className="h-4 w-4" aria-hidden="true" />
                </a>
              </div>

              <dl className="mt-10 grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
                {proofItems.map((item) => (
                  <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
                    <dt className="sr-only">Prova técnica</dt>
                    <dd className="flex items-start gap-2 text-xs font-medium leading-5 text-gray-300">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-cyan" aria-hidden="true" />
                      {item}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-4 shadow-2xl shadow-brand-violet/10 lg:p-6">
              <div className="rounded-[1.5rem] border border-white/10 bg-dark-bg p-4">
                <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-4">
                  <div>
                    <p className="text-sm font-bold text-white">Lead no WhatsApp</p>
                    <p className="text-xs text-gray-400">Simulação SDR Agent</p>
                  </div>
                  <span className="rounded-full bg-sofia-500/15 px-3 py-1 text-xs font-bold text-sofia-300">ao vivo</span>
                </div>
                <div className="space-y-3">
                  <div className="max-w-[80%] rounded-2xl rounded-bl-sm bg-white/10 p-3 text-sm text-gray-200">
                    Oi, queria entender se vocês atendem empresas B2B.
                  </div>
                  <div className="ml-auto max-w-[84%] rounded-2xl rounded-br-sm bg-gradient-to-r from-brand-violet to-brand-cyan p-3 text-sm text-white">
                    Atendemos sim. Hoje vocês querem captar novos leads, responder quem já chega no WhatsApp ou automatizar follow-up?
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-cyan">CRM ao vivo</p>
                    <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-xs text-gray-500">Intenção</p>
                        <p className="font-semibold text-white">Captar leads</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Score</p>
                        <p className="font-semibold text-white">72 / 100</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Estado</p>
                        <p className="font-semibold text-white">Qualificando</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Próxima ação</p>
                        <p className="font-semibold text-white">Handoff</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="px-4 py-16 sm:px-6 lg:px-8" id="agentes">
          <div className="mx-auto max-w-7xl">
            <div className="mb-10 max-w-3xl">
              <p className="text-sm font-bold uppercase tracking-[0.25em] text-brand-cyan">Catálogo WhatsApp Agents</p>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Uma base técnica, vários agentes vendáveis.
              </h2>
              <p className="mt-4 text-base leading-7 text-gray-300">
                O Atende AI demonstra o SDR Agent. A mesma arquitetura vira atendimento, agendamento, suporte, governo, RAG e reativação.
              </p>
            </div>
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {WHATSAPP_AGENTS.map((agent) => (
                <AgentCard key={agent.slug} agent={agent} compact />
              ))}
            </div>
            <div className="mt-8">
              <Link to="/agentes" className="inline-flex min-h-11 items-center gap-2 rounded-full border border-white/15 px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-white/10">
                Ver catálogo completo
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </section>

        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-7xl gap-5 lg:grid-cols-4">
            {differentiators.map((item) => {
              const Icon = item.icon;
              return (
                <article key={item.title} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
                  <Icon className="h-7 w-7 text-brand-cyan" aria-hidden="true" />
                  <h3 className="mt-5 text-lg font-bold text-white">{item.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-gray-300">{item.description}</p>
                </article>
              );
            })}
          </div>
        </section>

        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <CTASection />
          </div>
        </section>
      </main>
    </div>
  );
}
