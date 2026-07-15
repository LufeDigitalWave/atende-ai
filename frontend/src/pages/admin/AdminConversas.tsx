import type { AdminSession } from '../../lib/admin-api';

interface AdminConversasProps {
  sessions: AdminSession[];
}

/**
 * Lista de conversas (somente leitura).
 */
export default function AdminConversas({ sessions }: AdminConversasProps) {
  if (sessions.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Nenhuma conversa ainda. Aguarde visitantes.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-bold mb-4">
        Conversas ({sessions.length})
      </h2>

      <div className="grid gap-3">
        {sessions.map((session) => (
          <SessionCard key={session.session_id} session={session} />
        ))}
      </div>
    </div>
  );
}

function SessionCard({ session }: { session: AdminSession }) {
  const created = new Date(session.created_at).toLocaleString('pt-BR');
  const lastActivity = new Date(session.last_activity_at).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="font-semibold text-sm text-gray-900">
            {session.lead_name || 'Visitante sem nome'}
          </h3>
          <p className="text-xs text-gray-500">{created}</p>
        </div>
        <StatusBadge status={session.status} />
      </div>

      <div className="flex items-center gap-3 text-xs">
        <span className="text-gray-600">
          💬 {session.message_count} mensagens
        </span>
        {session.lead_state && (
          <span className="text-gray-600">
            🔄 {session.lead_state.replace(/_/g, ' ')}
          </span>
        )}
        {session.lead_score !== null && (
          <span className="text-sofia-600 font-semibold">
            📊 {session.lead_score}/100
          </span>
        )}
        <span className="ml-auto text-gray-400">Ativo às {lastActivity}</span>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; className: string }> = {
    active: { label: '● Ativa', className: 'bg-green-50 text-green-700' },
    capped: { label: '● Cap', className: 'bg-amber-50 text-amber-700' },
    expired: { label: '● Exp', className: 'bg-gray-50 text-gray-600' },
  };
  const info = map[status] || map.active;
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${info.className}`}>
      {info.label}
    </span>
  );
}