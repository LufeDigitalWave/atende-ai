import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import AgentCard from '../components/marketing/AgentCard';
import CTASection from '../components/marketing/CTASection';
import SiteHeader from '../components/marketing/SiteHeader';
import { WHATSAPP_AGENTS } from '../data/agents';
import { CONTACT_URL } from '../lib/constants';

const PACKAGES = [
  {
    name: 'Starter',
    price: 'R$ 1.500–3.000',
    points: ['1 agente', '1 fluxo principal', 'Handoff humano'],
  },
  {
    name: 'Pro',
    price: 'R$ 3.500–8.000',
    points: ['RAG/FAQ', 'CRM ou agenda', 'Métricas básicas'],
  },
  {
    name: 'Business',
    price: 'R$ 8.000+',
    points: ['Multiagente', 'Integrações', 'Operação assistida'],
  },
];

export default function Agentes() {
  return (
    <div className="min-h-screen bg-dark-bg text-white">
      <SiteHeader />
      <main>
        <section className="px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-4xl text-center">
            <p className="text-sm font-bold uppercase tracking-[0.25em] text-brand-cyan">WhatsApp Agents</p>
            <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Agentes especializados para cada gargalo do WhatsApp.
            </h1>
            <p className="mx-auto mt-6 max-w-3xl text-lg leading-8 text-gray-300">
              Comece com um agente simples e evolua para uma operação conectada a CRM, agenda, base de conhecimento, atendimento humano e métricas.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Link
                to="/demo"
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold text-dark-bg hover:bg-gray-100"
              >
                Testar SDR Agent
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <a
                href={CONTACT_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/15 px-6 py-3 text-sm font-bold text-white hover:bg-white/10"
              >
                Pedir piloto
              </a>
            </div>
          </div>
        </section>

        <section className="px-4 pb-16 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-2">
            {WHATSAPP_AGENTS.map((agent) => (
              <AgentCard key={agent.slug} agent={agent} />
            ))}
          </div>
        </section>

        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 sm:p-10">
            <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr]">
              <div>
                <p className="text-sm font-bold uppercase tracking-[0.25em] text-brand-cyan">Como empacotar</p>
                <h2 className="mt-3 text-3xl font-bold text-white">Três pacotes para vender sem escopo infinito.</h2>
                <p className="mt-4 text-sm leading-7 text-gray-300">
                  Cada agente pode começar pequeno e ganhar integrações conforme o cliente prova valor.
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                {PACKAGES.map((plan) => (
                  <article key={plan.name} className="rounded-3xl border border-white/10 bg-dark-bg/60 p-5">
                    <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                    <p className="mt-2 text-sm font-semibold text-brand-cyan">{plan.price}</p>
                    <ul className="mt-5 space-y-3 text-sm text-gray-300">
                      {plan.points.map((point) => (
                        <li key={point} className="flex gap-2">
                          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-cyan" aria-hidden="true" />
                          {point}
                        </li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
            </div>
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
