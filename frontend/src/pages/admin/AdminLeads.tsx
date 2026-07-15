import type { AdminKanban } from '../../lib/admin-api';

const COLUMNS = [
  { key: 'novo', label: 'Novo', color: 'bg-gray-50 border-gray-200' },
  { key: 'em_qualificacao', label: 'Qualificando', color: 'bg-blue-50 border-blue-200' },
  { key: 'qualificado', label: 'Qualificado', color: 'bg-green-50 border-green-200' },
  { key: 'agendamento_proposto', label: 'Agendamento', color: 'bg-amber-50 border-amber-200' },
  { key: 'handoff', label: 'Handoff', color: 'bg-purple-50 border-purple-200' },
] as const;

interface AdminLeadsProps {
  kanban: AdminKanban;
}

/**
 * Kanban de leads (somente leitura — estado muda via conversa).
 */
export default function AdminLeads({ kanban }: AdminLeadsProps) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-4">
        Leads · Kanban
      </h2>
      <p className="text-xs text-gray-500 mb-4">
        Somente leitura — os estados mudam automaticamente conforme a conversa.
      </p>

      <div className="flex gap-3 overflow-x-auto pb-3">
        {COLUMNS.map((col) => {
          const leads = kanban[col.key] as unknown[] || [];
          return (
            <div
              key={col.key}
              className={`flex-shrink-0 w-52 rounded-lg border p-3 ${col.color}`}
            >
              <h3 className="font-semibold text-sm mb-2">
                {col.label}
                <span className="ml-2 text-xs font-normal text-gray-500">
                  ({leads.length})
                </span>
              </h3>
              <div className="space-y-2">
                {leads.length === 0 && (
                  <p className="text-xs text-gray-400 text-center py-4">
                    Vazio
                  </p>
                )}
                {leads.map((lead: unknown) => (
                  <LeadMiniCard
                    key={(lead as { id: string }).id}
                    lead={lead as Record<string, unknown>}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LeadMiniCard({ lead }: { lead: Record<string, unknown> }) {
  return (
    <div className="bg-white rounded border border-gray-200 p-2 text-xs shadow-sm">
      <p className="font-medium text-gray-900 truncate">
        {(lead.name as string) || 'Sem nome'}
      </p>
      {lead.service_interest && (
        <p className="text-gray-500 truncate">{lead.service_interest as string}</p>
      )}
      <div className="flex items-center justify-between mt-1">
        <span className="text-sofia-600 font-semibold">
          {(lead.score as number) || 0}/100
        </span>
      </div>
    </div>
  );
}