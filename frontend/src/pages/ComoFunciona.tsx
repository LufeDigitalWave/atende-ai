/**
 * Página /como-funciona — explicação de 1 tela para o cliente leigo.
 */
export default function ComoFunciona() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-sofia-500 to-sofia-600 text-white px-6 py-8 text-center">
        <h1 className="text-3xl font-bold mb-2">Como funciona?</h1>
        <p className="text-sm opacity-90 max-w-2xl mx-auto">
          Entenda como o agente de IA qualifica leads 24/7 no WhatsApp da sua empresa.
        </p>
      </div>

      {/* Diagram */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center text-center mb-12">
          <Step
            emoji="📱"
            title="WhatsApp"
            desc="Lead manda mensagem"
          />
          <Arrow />
          <Step
            emoji="🤖"
            title="Agente IA"
            desc="Qualifica + extrai dados"
          />
          <Arrow />
          <Step
            emoji="📊"
            title="CRM"
            desc="Lead score + funil + agendamento"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center text-center">
          <Step
            emoji="🗂️"
            title="Base RAG"
            desc="Preços, FAQ, serviços da empresa"
          />
          <Step
            emoji="📅"
            title="Agendamento"
            desc="Propõe horários automáticos"
          />
          <Step
            emoji="👤"
            title="Vendedor"
            desc="Recebe lead quente + handoff"
          />
        </div>
      </div>

      {/* Production vs Demo */}
      <div className="bg-gray-50 px-6 py-12">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">
            Em produção, o que muda?
          </h2>
          <div className="space-y-3">
            <CompareRow
              demo="Chat web (esta demo)"
              prod="WhatsApp oficial via Meta Cloud API"
            />
            <CompareRow
              demo="CRM visual ao lado"
              prod="CRM real (HubSpot, Kommo, Chatwoot)"
            />
            <CompareRow
              demo="Slots fictícios"
              prod="Agenda real (Google Calendar, Cal.com)"
            />
            <CompareRow
              demo="Base fictícia (Clínica Renova)"
              prod="Base da SUA empresa (PDFs, docs, planilha de preços)"
            />
            <CompareRow
              demo="Budget diário limitado"
              prod="Sem limite — custo ~R$ 0,03/conversa"
            />
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="max-w-3xl mx-auto px-6 py-12">
        <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">FAQ</h2>
        <div className="space-y-4">
          <FAQ
            q="A IA inventa coisas (alucina)?"
            a="Não. Preços e informações clínicas vêm de uma base RAG com dados da empresa. O prompt tem regra explícita: se não tiver na base, a IA diz 'vou confirmar com a equipe'. Toda resposta é auditável."
          />
          <FAQ
            q="Quanto custa por conversa?"
            a="Em média R$ 0,02 a R$ 0,05 por conversa qualificada (8 turnos) usando Claude Haiku com prompt caching. Para 500 conversas/mês: ~R$ 25 de API + R$ 80 de infra = R$ 105/mês total."
          />
          <FAQ
            q="Quanto tempo pra colocar na minha empresa?"
            a="1 semana pro MVP funcional com a sua base. 2 semanas com integrações completas (CRM, agenda real, Meta Cloud API). O motor é o mesmo — muda só a base de conhecimento e os campos de qualificação."
          />
          <FAQ
            q="E se o cliente xingar a IA?"
            a="Detecção automática de tom hostil e frases-chave ('quero falar com humano', 'atendente'). Handoff imediato pro vendedor. A IA nunca revida ou se irrita."
          />
          <FAQ
            q="Funciona em outros idiomas?"
            a="Sim — troca o prompt e a base RAG. O modelo entende 50+ idiomas nativamente."
          />
          <FAQ
            q="E se a API cair?"
            a="Fallback roteirizado — o sistema responde com mensagens padrão e agenda retorno. Fila de mensagens pendentes pra re-enviar quando volta."
          />
        </div>
      </div>

      {/* CTA */}
      <div className="bg-sofia-500 text-white px-6 py-8 text-center">
        <h2 className="text-xl font-bold mb-2">Quer um agente assim no SEU WhatsApp?</h2>
        <p className="text-sm opacity-90 mb-4">Fale comigo — demonstro em 5 minutos.</p>
        <a
          href={import.meta.env.VITE_CONTACT_URL || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-6 py-3 bg-white text-sofia-600 font-bold rounded-full hover:bg-gray-100 transition-colors"
        >
          Falar agora →
        </a>
      </div>
    </div>
  );
}

function Step({ emoji, title, desc }: { emoji: string; title: string; desc: string }) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-4xl mb-2">{emoji}</span>
      <p className="font-bold text-gray-900 text-sm">{title}</p>
      <p className="text-xs text-gray-600">{desc}</p>
    </div>
  );
}

function Arrow() {
  return (
    <div className="hidden md:flex items-center justify-center text-gray-300 text-2xl">
      →
    </div>
  );
}

function CompareRow({ demo, prod }: { demo: string; prod: string }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="flex-1 text-right text-gray-500">{demo}</span>
      <span className="text-gray-300">→</span>
      <span className="flex-1 font-medium text-gray-900">{prod}</span>
    </div>
  );
}

function FAQ({ q, a }: { q: string; a: string }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <h4 className="font-semibold text-gray-900 text-sm mb-1">"{q}"</h4>
      <p className="text-xs text-gray-600 leading-relaxed">{a}</p>
    </div>
  );
}
