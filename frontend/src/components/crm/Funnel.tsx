import { useSessionStore } from '../../lib/store';

const STATES = [
  { key: 'novo', label: 'Novo' },
  { key: 'em_qualificacao', label: 'Qualificando' },
  { key: 'qualificado', label: 'Qualificado' },
  { key: 'agendamento_proposto', label: 'Agendamento' },
  { key: 'handoff', label: 'Handoff' },
];

/**
 * Funnel: horizontal state indicator.
 */
export default function Funnel() {
  const lead = useSessionStore((s) => s.lead);

  if (!lead) return null;

  const currentIndex = STATES.findIndex((s) => s.key === lead.state);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">🔄 Funil</h3>
      <div className="flex items-center gap-1">
        {STATES.map((state, idx) => {
          const isActive = idx <= currentIndex;
          const isCurrent = idx === currentIndex;
          return (
            <div key={state.key} className="flex-1 flex flex-col items-center">
              {/* Bar */}
              <div
                className={`w-full h-2 rounded-full transition-all duration-500 ${
                  isActive
                    ? 'bg-sofia-500'
                    : 'bg-gray-100'
                } ${isCurrent ? 'ring-2 ring-sofia-300' : ''}`}
              />
              {/* Label */}
              <span
                className={`text-[10px] mt-1 ${
                  isCurrent
                    ? 'text-sofia-600 font-semibold'
                    : isActive
                    ? 'text-gray-600'
                    : 'text-gray-300'
                }`}
              >
                {state.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
