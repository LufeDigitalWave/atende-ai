import { useSessionStore, type LeadProfile } from '../../lib/store';

/**
 * Lead card with fields, highlighting new data.
 */
export default function LeadCard() {
  const lead = useSessionStore((s) => s.lead);

  if (!lead) return null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <span>👤 Lead Profile</span>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
          {lead.state.replace(/_/g, ' ')}
        </span>
      </h3>

      <div className="space-y-2">
        <FieldRow label="Nome" value={lead.name} />
        <FieldRow label="Serviço" value={lead.serviceInterest} />
        <FieldRow label="Queixa" value={lead.complaint} />
        <FieldRow label="Orçamento" value={formatBudget(lead.budgetRange)} />
        <FieldRow label="Urgência" value={formatUrgency(lead.urgency)} />
        {lead.scheduledSlot && (
          <FieldRow label="Agendamento" value={lead.scheduledSlot} />
        )}
      </div>
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value: string | null }) {
  const filled = value && value !== 'nao_informado' && value !== 'nao_informada';
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-gray-500">{label}</span>
      <span
        className={`text-xs font-medium transition-all duration-300 ${
          filled
            ? 'text-gray-900 bg-sofia-50 px-2 py-0.5 rounded animate-pulse'
            : 'text-gray-300 italic'
        }`}
      >
        {filled ? value : '—'}
      </span>
    </div>
  );
}

function formatBudget(range: string): string | null {
  const map: Record<string, string> = {
    nao_informado: '',
    ate_1k: 'Até R$ 1.000',
    ate_3k: 'Até R$ 3.000',
    ate_6k: 'Até R$ 6.000',
    acima_6k: 'Acima de R$ 6.000',
  };
  return map[range] || null;
}

function formatUrgency(urgency: string): string | null {
  const map: Record<string, string> = {
    nao_informada: '',
    baixa: 'Baixa',
    media: 'Média',
    alta: 'Alta 🔥',
  };
  return map[urgency] || null;
}
