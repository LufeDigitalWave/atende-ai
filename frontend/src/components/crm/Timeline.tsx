import { useSessionStore, type LeadEvent } from '../../lib/store';

/**
 * Timeline of lead events.
 */
export default function Timeline() {
  const events = useSessionStore((s) => s.events);

  if (events.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Timeline</h3>
        <p className="text-xs text-gray-400 italic">Eventos aparecerão aqui...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Timeline</h3>
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {events.map((event) => (
          <TimelineItem key={event.id} event={event} />
        ))}
      </div>
    </div>
  );
}

function TimelineItem({ event }: { event: LeadEvent }) {
  const time = new Date(event.createdAt).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="flex items-start gap-2 text-xs">
      <div className="w-2 h-2 rounded-full bg-sofia-500 mt-1 flex-shrink-0" />
      <div className="flex-1">
        <span className="text-gray-700 font-medium">{formatEventType(event.type)}</span>
        {event.payload && Object.keys(event.payload).length > 0 && (
          <span className="text-gray-500 ml-1">
            {formatPayload(event.type, event.payload)}
          </span>
        )}
      </div>
      <span className="text-gray-400 flex-shrink-0">{time}</span>
    </div>
  );
}

function formatEventType(type: string): string {
  const map: Record<string, string> = {
    session_started: 'Sessão iniciada',
    field_extracted: 'Campo extraído',
    score_updated: 'Score atualizado',
    state_changed: 'Estado alterado',
    handoff_triggered: 'Handoff acionado',
    slot_offered: 'Horários oferecidos',
    slot_picked: 'Horário escolhido',
    human_requested: 'Humano solicitado',
    out_of_scope: 'Fora de escopo',
    session_capped: 'Sessão encerrada',
  };
  return map[type] || type;
}

function formatPayload(
  type: string,
  payload: Record<string, unknown>,
): string {
  if (type === 'field_extracted') {
    const fields = payload.extracted_fields as Record<string, unknown>;
    if (fields) {
      return Object.entries(fields)
        .filter(([, v]) => v)
        .map(([k, v]) => `${k}: ${v}`)
        .join(', ');
    }
  }
  if (type === 'state_changed') {
    return `${payload.from} → ${payload.to}`;
  }
  if (type === 'score_updated') {
    return `→ ${payload.score}`;
  }
  return '';
}
