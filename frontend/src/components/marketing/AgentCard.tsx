import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { WhatsAppAgent } from '../../data/agents';
import { CONTACT_URL } from '../../lib/constants';

interface AgentCardProps {
  agent: WhatsAppAgent;
  compact?: boolean;
}

export default function AgentCard({ agent, compact = false }: AgentCardProps) {
  const Icon = agent.icon;

  return (
    <article className="group flex h-full flex-col rounded-3xl border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/10 transition-all hover:-translate-y-1 hover:border-brand-cyan/50 hover:bg-white/[0.07]">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-violet/25 to-brand-cyan/25 text-brand-cyan ring-1 ring-white/10">
          <Icon className="h-6 w-6" aria-hidden="true" />
        </div>
        <span className="rounded-full border border-white/10 px-3 py-1 text-xs font-medium text-gray-300">
          {agent.label}
        </span>
      </div>

      <h3 className="text-xl font-bold text-white">{agent.name}</h3>
      <p className="mt-3 text-sm leading-6 text-gray-300">{agent.outcome}</p>

      {!compact && (
        <>
          <div className="mt-5 rounded-2xl border border-white/10 bg-dark-bg/50 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-cyan">Fluxo</p>
            <ol className="mt-3 space-y-2 text-sm text-gray-300">
              {agent.flow.map((step, index) => (
                <li key={step} className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/10 text-xs font-bold text-white">
                    {index + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            {agent.integrations.slice(0, 4).map((integration) => (
              <span key={integration} className="rounded-full bg-white/5 px-3 py-1 text-xs text-gray-300 ring-1 ring-white/10">
                {integration}
              </span>
            ))}
          </div>
        </>
      )}

      {agent.slug === 'sdr' ? (
        <Link
          to="/demo"
          className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-full text-sm font-bold text-brand-cyan transition-colors hover:text-white"
        >
          Testar demo SDR
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
        </Link>
      ) : (
        <a
          href={CONTACT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-full text-sm font-bold text-brand-cyan transition-colors hover:text-white"
        >
          Pedir piloto
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
        </a>
      )}
    </article>
  );
}
