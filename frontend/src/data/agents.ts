import {
  CalendarCheck,
  FileSearch,
  HandCoins,
  Headphones,
  Landmark,
  MessageSquareText,
  type LucideIcon,
} from 'lucide-react';

export interface WhatsAppAgent {
  slug: string;
  name: string;
  label: string;
  icon: LucideIcon;
  audience: string;
  problem: string;
  outcome: string;
  flow: string[];
  integrations: string[];
}

export const WHATSAPP_AGENTS: WhatsAppAgent[] = [
  {
    slug: 'sdr',
    name: 'SDR Agent',
    label: 'Vendas e qualificação',
    icon: MessageSquareText,
    audience: 'Empresas que recebem leads pelo WhatsApp e perdem oportunidades por demora no atendimento.',
    problem: 'Lead esfria antes do vendedor responder, chega sem contexto e não entra no CRM.',
    outcome: 'Responde 24/7, entende intenção, qualifica, calcula score e entrega lead quente para o time comercial.',
    flow: ['Entende o interesse', 'Faz uma pergunta por vez', 'Atualiza CRM ao vivo', 'Aciona vendedor no momento certo'],
    integrations: ['WhatsApp Cloud API', 'Kommo', 'HubSpot', 'Chatwoot', 'Google Sheets'],
  },
  {
    slug: 'support',
    name: 'Support Agent',
    label: 'Atendimento e suporte',
    icon: Headphones,
    audience: 'SaaS, e-commerce e operações com alto volume de dúvidas repetidas.',
    problem: 'Equipe humana gasta tempo respondendo as mesmas perguntas e tickets simples acumulam.',
    outcome: 'Responde FAQ, consulta base de conhecimento, abre ticket e faz handoff com contexto completo.',
    flow: ['Classifica a dúvida', 'Busca na base RAG', 'Responde com segurança', 'Escala quando precisa'],
    integrations: ['Chatwoot', 'Zendesk', 'Freshdesk', 'Notion', 'Base RAG'],
  },
  {
    slug: 'appointment',
    name: 'Appointment Agent',
    label: 'Agendamento automático',
    icon: CalendarCheck,
    audience: 'Clínicas, estética, oficinas, consultórios, aulas e serviços locais.',
    problem: 'Cliente pede horário fora do expediente e o agendamento depende de troca manual de mensagens.',
    outcome: 'Coleta serviço, preferência, disponibilidade e confirma agenda com lembrete automático.',
    flow: ['Identifica serviço', 'Coleta disponibilidade', 'Sugere horários', 'Confirma e registra'],
    integrations: ['Google Calendar', 'Cal.com', 'Agenda interna', 'WhatsApp templates'],
  },
  {
    slug: 'faq-rag',
    name: 'FAQ/RAG Agent',
    label: 'Base de conhecimento',
    icon: FileSearch,
    audience: 'Empresas com documentos, políticas, catálogos, regras ou processos que mudam com frequência.',
    problem: 'Informação fica espalhada em PDFs, planilhas e mensagens antigas, gerando resposta inconsistente.',
    outcome: 'Consulta documentos e responde com base em conteúdo autorizado, sem inventar preço ou regra.',
    flow: ['Recebe pergunta', 'Busca trechos relevantes', 'Responde com limite claro', 'Encaminha exceções'],
    integrations: ['Postgres pgvector', 'Supabase', 'Drive', 'Notion', 'PDFs'],
  },
  {
    slug: 'civic',
    name: 'Civic Agent',
    label: 'Atendimento público',
    icon: Landmark,
    audience: 'Prefeituras, câmaras, secretarias, ouvidorias e projetos civic-tech.',
    problem: 'Cidadão não sabe onde pedir serviço e equipe precisa classificar solicitações manualmente.',
    outcome: 'Orienta cidadão, coleta dados mínimos, classifica demanda e gera protocolo para acompanhamento.',
    flow: ['Entende solicitação', 'Coleta localização', 'Classifica categoria', 'Gera protocolo'],
    integrations: ['Sistema de protocolo', 'Jira-like', 'Sheets', 'Geocoding', 'Chatwoot'],
  },
  {
    slug: 'collections',
    name: 'Collections Agent',
    label: 'Follow-up e reativação',
    icon: HandCoins,
    audience: 'Operações que precisam reativar leads, lembrar pagamentos ou recuperar oportunidades paradas.',
    problem: 'Follow-up manual é inconsistente e oportunidades ficam esquecidas no funil.',
    outcome: 'Executa cadência com linguagem segura, respeita opt-out e encaminha negociações para humano.',
    flow: ['Segmenta pendência', 'Envia lembrete aprovado', 'Responde objeções', 'Atualiza status'],
    integrations: ['CRM', 'Asaas', 'n8n', 'WhatsApp templates', 'Planilhas'],
  },
];
