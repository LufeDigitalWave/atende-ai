export interface Package {
  name: string;
  highlight?: boolean;
  implMin: number;
  implMax: number;
  mensMin: number;
  mensMax: number;
  prazo: string;
  features: string[];
}

export const PACKAGES: Package[] = [
  {
    name: 'Starter',
    implMin: 1500,
    implMax: 3000,
    mensMin: 300,
    mensMax: 800,
    prazo: '7–10 dias',
    features: ['1 agente WhatsApp', '1 fluxo principal', 'Handoff humano', 'Base de conhecimento simples'],
  },
  {
    name: 'Pro',
    highlight: true,
    implMin: 3500,
    implMax: 8000,
    mensMin: 800,
    mensMax: 2000,
    prazo: '10–20 dias',
    features: ['RAG / FAQ com documentos', 'CRM ou agenda conectada', 'Métricas básicas', 'Templates Meta aprovados'],
  },
  {
    name: 'Business',
    implMin: 8000,
    implMax: 20000,
    mensMin: 2000,
    mensMax: 5000,
    prazo: '20–40 dias',
    features: ['Multiagente / departamentos', 'Integrações n8n ou FastAPI', 'Operação assistida 1º mês', 'Relatórios e auditoria'],
  },
];

export const LLM_COST_PER_CONVERSATION = 0.04;
export const INFRA_MONTHLY_BASE = 150;
