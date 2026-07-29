import { useEffect, useState } from 'react';
import { trackFunnel } from '../lib/funnel';
import { CheckCircle2, MessageCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import CTASection from '../components/marketing/CTASection';
import SiteHeader from '../components/marketing/SiteHeader';
import { INFRA_MONTHLY_BASE, LLM_COST_PER_CONVERSATION, PACKAGES } from '../data/pricing';
import { CONTACT_URL } from '../lib/constants';

function formatBRL(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
}

function suggestPackage(conversas: number): string {
  if (conversas <= 300) return 'Starter';
  if (conversas <= 1500) return 'Pro';
  return 'Business';
}

export default function Pricing() {
  useEffect(() => { trackFunnel('clicked_pricing'); }, []);
  const [conversas, setConversas] = useState(500);

  const llmCost = Math.round(conversas * LLM_COST_PER_CONVERSATION);
  const totalOperacional = llmCost + INFRA_MONTHLY_BASE;
  const suggested = suggestPackage(conversas);

  return (
    <div className="min-h-screen bg-dark-bg text-white">
      <SiteHeader />
      <main>
        {/* Hero */}
        <section className="px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-4xl text-center">
            <p className="text-sm font-bold uppercase tracking-[0.25em] text-brand-cyan">Pricing</p>
            <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Implante um agente WhatsApp e recupere o custo em semanas.
            </h1>
            <p className="mx-auto mt-6 max-w-3xl text-lg leading-8 text-gray-300">
              Escolha o pacote ideal pelo seu volume e complexidade. Use o simulador para estimar o custo operacional mensal.
            </p>
          </div>
        </section>

        {/* Packages */}
        <section className="px-4 pb-16 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-7xl gap-6 md:grid-cols-3">
            {PACKAGES.map((pkg) => (
              <article
                key={pkg.name}
                className={`flex flex-col rounded-3xl border p-6 ${
                  pkg.highlight
                    ? 'border-brand-cyan/60 bg-gradient-to-br from-brand-violet/20 to-brand-cyan/15 shadow-2xl shadow-brand-cyan/10'
                    : 'border-white/10 bg-white/[0.04]'
                }`}
              >
                {pkg.highlight && (
                  <span className="mb-4 w-fit rounded-full bg-brand-cyan/20 px-3 py-1 text-xs font-bold uppercase tracking-widest text-brand-cyan">Mais popular</span>
                )}
                <h2 className="text-2xl font-bold text-white">{pkg.name}</h2>

                <div className="mt-5 space-y-1">
                  <p className="text-sm text-gray-400">Implantação</p>
                  <p className="text-2xl font-bold text-white">
                    {formatBRL(pkg.implMin)}<span className="text-base font-normal text-gray-400">–{formatBRL(pkg.implMax)}</span>
                  </p>
                </div>

                <div className="mt-3 space-y-1">
                  <p className="text-sm text-gray-400">Mensalidade</p>
                  <p className="text-xl font-bold text-brand-cyan">
                    {formatBRL(pkg.mensMin)}<span className="text-sm font-normal text-gray-400">–{formatBRL(pkg.mensMax)}/mês</span>
                  </p>
                </div>

                <p className="mt-3 text-xs text-gray-500">Prazo: {pkg.prazo}</p>

                <ul className="mt-5 flex-1 space-y-3">
                  {pkg.features.map((feat) => (
                    <li key={feat} className="flex gap-2 text-sm text-gray-300">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-cyan" aria-hidden="true" />
                      {feat}
                    </li>
                  ))}
                </ul>

                <a
                  href={CONTACT_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`mt-6 inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-bold transition-colors ${
                    pkg.highlight
                      ? 'bg-white text-dark-bg hover:bg-gray-100'
                      : 'border border-white/20 text-white hover:bg-white/10'
                  }`}
                >
                  Pedir piloto {pkg.name}
                  <MessageCircle className="h-4 w-4" aria-hidden="true" />
                </a>
              </article>
            ))}
          </div>
        </section>

        {/* Simulator */}
        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 sm:p-10">
            <h2 className="text-2xl font-bold text-white">Simulador de custo operacional</h2>
            <p className="mt-2 text-sm text-gray-400">Estimativa de custo de LLM + infra por mês, baseada em Claude Haiku 4.5 com prompt caching.</p>

            <div className="mt-8">
              <label htmlFor="conversas" className="text-sm font-semibold text-gray-200">
                Conversas / mês: <span className="text-brand-cyan">{conversas.toLocaleString('pt-BR')}</span>
              </label>
              <input
                id="conversas"
                type="range"
                min={100}
                max={5000}
                step={100}
                value={conversas}
                onChange={(e) => setConversas(Number(e.target.value))}
                className="mt-3 h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-brand-cyan"
                aria-label="Número de conversas por mês"
              />
              <div className="mt-1 flex justify-between text-xs text-gray-600">
                <span>100</span>
                <span>5.000</span>
              </div>
            </div>

            <dl className="mt-8 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-dark-bg/60 p-4 text-center">
                <dt className="text-xs text-gray-500">Custo LLM estimado</dt>
                <dd className="mt-2 text-2xl font-bold text-white">{formatBRL(llmCost)}</dd>
                <dd className="mt-1 text-xs text-gray-500">{conversas} conversas × R$ {LLM_COST_PER_CONVERSATION}</dd>
              </div>
              <div className="rounded-2xl border border-white/10 bg-dark-bg/60 p-4 text-center">
                <dt className="text-xs text-gray-500">Infra / mês</dt>
                <dd className="mt-2 text-2xl font-bold text-white">{formatBRL(INFRA_MONTHLY_BASE)}</dd>
                <dd className="mt-1 text-xs text-gray-500">VPS + banco + monitoramento</dd>
              </div>
              <div className="rounded-2xl border border-brand-cyan/40 bg-brand-cyan/10 p-4 text-center">
                <dt className="text-xs text-brand-cyan">Total operacional</dt>
                <dd className="mt-2 text-2xl font-bold text-brand-cyan">{formatBRL(totalOperacional)}</dd>
                <dd className="mt-1 text-xs text-gray-500">por mês</dd>
              </div>
            </dl>

            <div className="mt-6 rounded-2xl border border-white/10 bg-dark-bg/50 p-4">
              <p className="text-sm text-gray-300">
                Com {conversas.toLocaleString('pt-BR')} conversas/mês, o pacote{' '}
                <span className="font-bold text-brand-cyan">{suggested}</span>{' '}
                é a melhor entrada. A mensalidade começa em{' '}
                <span className="font-bold text-white">
                  {formatBRL(PACKAGES.find((p) => p.name === suggested)!.mensMin)}</span>, cobrindo suporte, operação e ajustes.
              </p>
            </div>

            <p className="mt-4 text-xs text-gray-600">
              Estimativas com Claude Haiku 4.5 + prompt caching. Custo real varia conforme modelo, idioma, duração das conversas e provider escolhido.
            </p>
          </div>
        </section>

        {/* FAQ pricing */}
        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl">
            <h2 className="text-2xl font-bold text-white">Perguntas sobre preço</h2>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {[
                { q: '1 mês de suporte incluso?', a: 'Sim. Todo pacote inclui 1 mês de suporte pós-entrega para ajustes, dúvidas e monitoramento.' },
                { q: 'Preciso pagar a API da Meta?', a: 'A API oficial WhatsApp tem custo por conversa pago diretamente à Meta. A mensalidade cobre operação, não o consumo de API.' },
                { q: 'Posso começar com Starter e evoluir?', a: 'Sim. O Starter é a entrada recomendada para validar valor antes de integrar CRM, agenda ou RAG.' },
                { q: 'Tem contrato de fidelidade?', a: 'Não. Mensalidade é recorrente mas sem multa. Você pode pausar ou encerrar com 30 dias de aviso.' },
              ].map((item) => (
                <article key={item.q} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
                  <h3 className="text-base font-bold text-white">{item.q}</h3>
                  <p className="mt-3 text-sm leading-6 text-gray-300">{item.a}</p>
                </article>
              ))}
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
