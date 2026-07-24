import { ArrowRight, Bot, CalendarCheck, Database, MessageCircle, MonitorCheck, UserRoundCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import CTASection from '../components/marketing/CTASection';
import SiteHeader from '../components/marketing/SiteHeader';

const steps = [
  { icon: MessageCircle, title: 'WhatsApp', desc: 'Lead manda mensagem no canal oficial da empresa.' },
  { icon: Bot, title: 'Agente IA', desc: 'Entende intenção, responde e conduz uma pergunta por vez.' },
  { icon: MonitorCheck, title: 'CRM', desc: 'Dados, score, estado e histórico aparecem para o time humano.' },
];

const productionBlocks = [
  { icon: Database, title: 'Base RAG', desc: 'Preços, FAQ, políticas e documentos da empresa entram como fonte autorizada.' },
  { icon: CalendarCheck, title: 'Agenda', desc: 'Quando o fluxo pede horário, o agente consulta ou registra em agenda real.' },
  { icon: UserRoundCheck, title: 'Handoff', desc: 'Quando precisa de humano, o vendedor recebe contexto completo da conversa.' },
];

const comparisons = [
  ['Chat web da demo', 'WhatsApp oficial via Meta Cloud API'],
  ['CRM visual ao lado', 'CRM real como Kommo, HubSpot, Chatwoot ou planilha'],
  ['Dados fictícios', 'Base da sua empresa com PDFs, planilhas e regras'],
  ['Slots simulados', 'Agenda real como Google Calendar ou Cal.com'],
  ['Fluxo SDR', 'SDR, suporte, agendamento, RAG, governo ou reativação'],
];

const faqs = [
  {
    q: 'A IA inventa coisas?',
    a: 'A regra é responder com base autorizada. Preços, políticas e condições vêm de dados versionados. Quando a informação não existe, o agente encaminha para humano.',
  },
  {
    q: 'Qual a diferença para chatbot comum?',
    a: 'O agente entende intenção, usa ferramentas, consulta base de conhecimento, atualiza CRM e sabe quando parar para chamar uma pessoa.',
  },
  {
    q: 'Quanto tempo para colocar no ar?',
    a: 'Um piloto simples costuma caber em 7 a 10 dias. Integrações com CRM, agenda e templates Meta entram em uma segunda fase.',
  },
  {
    q: 'Funciona com WhatsApp oficial?',
    a: 'Sim. O modelo de produção usa WhatsApp Cloud API da Meta quando o cliente quer operação oficial e menor risco de bloqueio.',
  },
];

export default function ComoFunciona() {
  return (
    <div className="min-h-screen bg-dark-bg text-white">
      <SiteHeader />
      <main>
        <section className="px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-4xl text-center">
            <p className="text-sm font-bold uppercase tracking-[0.25em] text-brand-cyan">Como funciona</p>
            <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
              Do WhatsApp ao CRM, sem perder contexto no caminho.
            </h1>
            <p className="mx-auto mt-6 max-w-3xl text-lg leading-8 text-gray-300">
              A demo mostra o fluxo em uma interface web. Em produção, o mesmo motor atende pelo WhatsApp oficial, consulta sistemas reais e entrega contexto para a equipe.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Link
                to="/demo"
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold text-dark-bg hover:bg-gray-100"
              >
                Testar demo
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <Link
                to="/agentes"
                className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/15 px-6 py-3 text-sm font-bold text-white hover:bg-white/10"
              >
                Ver agentes
              </Link>
            </div>
          </div>
        </section>

        <section className="px-4 pb-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-4 md:grid-cols-3">
              {steps.map((step, index) => {
                const Icon = step.icon;
                return (
                  <article key={step.title} className="relative rounded-3xl border border-white/10 bg-white/[0.04] p-6">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-violet/25 to-brand-cyan/25 text-brand-cyan">
                      <Icon className="h-6 w-6" aria-hidden="true" />
                    </div>
                    <p className="mt-5 text-xs font-bold uppercase tracking-[0.2em] text-gray-500">Passo {index + 1}</p>
                    <h2 className="mt-2 text-xl font-bold text-white">{step.title}</h2>
                    <p className="mt-3 text-sm leading-6 text-gray-300">{step.desc}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-7xl gap-5 md:grid-cols-3">
            {productionBlocks.map((block) => {
              const Icon = block.icon;
              return (
                <article key={block.title} className="rounded-3xl border border-white/10 bg-dark-surface p-6">
                  <Icon className="h-7 w-7 text-brand-cyan" aria-hidden="true" />
                  <h2 className="mt-5 text-lg font-bold text-white">{block.title}</h2>
                  <p className="mt-3 text-sm leading-6 text-gray-300">{block.desc}</p>
                </article>
              );
            })}
          </div>
        </section>

        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 sm:p-10">
            <h2 className="text-2xl font-bold text-white">Demo versus produção</h2>
            <div className="mt-6 space-y-3">
              {comparisons.map(([demo, prod]) => (
                <div key={demo} className="grid gap-2 rounded-2xl border border-white/10 bg-dark-bg/50 p-4 text-sm sm:grid-cols-[1fr_auto_1fr] sm:items-center">
                  <span className="text-gray-400">{demo}</span>
                  <ArrowRight className="hidden h-4 w-4 text-brand-cyan sm:block" aria-hidden="true" />
                  <span className="font-medium text-white">{prod}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl">
            <h2 className="text-2xl font-bold text-white">Perguntas frequentes</h2>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {faqs.map((faq) => (
                <article key={faq.q} className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
                  <h3 className="text-base font-bold text-white">{faq.q}</h3>
                  <p className="mt-3 text-sm leading-6 text-gray-300">{faq.a}</p>
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
