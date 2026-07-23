import { useSessionStore } from '../../lib/store';

interface CRMField {
  key: string;
  label: string;
  priority: string;
}

interface LeadCardProps {
  crmFields?: CRMField[];
}

/**
 * Lead card with DYNAMIC fields per niche.
 * v3: renders fields from ConversationProfile.qualification_fields.
 * Falls back to legacy 5 fields if no crmFields provided.
 */
export default function LeadCard({ crmFields = [] }: LeadCardProps) {
  const lead = useSessionStore((s) => s.lead);

  if (!lead) return null;

  // Use dynamic fields if available, otherwise fallback to legacy
  const hasDynamicFields = crmFields.length > 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <span>Lead Profile</span>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
          {lead.state.replace(/_/g, ' ')}
        </span>
      </h3>

      <div className="space-y-2">
        {hasDynamicFields ? (
          // v3: Dynamic fields from ConversationProfile
          crmFields.map((field) => {
            const value = getDynamicFieldValue(field.key, lead.dynamicFields);
            return (
              <FieldRow
                key={field.key}
                label={field.label}
                value={value}
                priority={field.priority}
              />
            );
          })
        ) : (
          // Legacy fallback: 5 universal fields
          <>
            <FieldRow label="Nome" value={lead.name} />
            <FieldRow label="Serviço" value={lead.serviceInterest} />
            <FieldRow label="Queixa" value={lead.complaint} />
            <FieldRow label="Orçamento" value={formatBudget(lead.budgetRange)} />
            <FieldRow label="Urgência" value={formatUrgency(lead.urgency)} />
          </>
        )}
        {lead.scheduledSlot && (
          <FieldRow label="Agendamento" value={lead.scheduledSlot} />
        )}
      </div>
    </div>
  );
}

function getDynamicFieldValue(
  key: string,
  dynamicFields: Record<string, string | number | boolean | null>
): string | null {
  const val = dynamicFields[key];
  if (val === null || val === undefined) return null;
  if (typeof val === 'boolean') return val ? 'Sim' : 'Não';
  return String(val);
}

function FieldRow({ label, value, priority }: { label: string; value: string | null; priority?: string }) {
  const filled = value && value !== 'nao_informado' && value !== 'nao_informada' && value.trim() !== '';
  const isHigh = priority === 'high';

  if (!filled) {
    // Hide empty fields to reduce visual noise
    return null;
  }

  return (
    <div className="flex items-start justify-between gap-2 py-1.5 border-b border-gray-50 last:border-0">
      <span className={`text-xs shrink-0 ${isHigh ? 'text-gray-700 font-semibold' : 'text-gray-500'}`}>
        {label}
      </span>
      <span className="text-xs text-gray-900 font-medium text-right bg-sofia-50 px-2 py-0.5 rounded">
        {value}
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
