import type { AdminCostsResponse } from '../../lib/admin-api';

interface AdminCustosProps {
  costs: AdminCostsResponse;
}

/**
 * Dashboard de custos (tokens, R$, budget).
 */
export default function AdminCustos({ costs }: AdminCustosProps) {
  const { today, budget, history } = costs;

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-bold">Custos · Hoje</h2>

      {/* Cards de hoje */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <CostCard
          label="Chamadas"
          value={String(today.calls)}
          unit="calls"
        />
        <CostCard
          label="Tokens In"
          value={today.input_tokens.toLocaleString()}
          unit="tokens"
        />
        <CostCard
          label="Tokens Out"
          value={today.output_tokens.toLocaleString()}
          unit="tokens"
        />
        <CostCard
          label="Cache Hit"
          value={today.cached_tokens.toLocaleString()}
          unit="tokens"
        />
      </div>

      {/* Custo real */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-xs text-gray-500 mb-1">Custo USD (hoje)</p>
          <p className="text-2xl font-bold text-gray-900">
            ${today.cost_usd.toFixed(4)}
          </p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-xs text-gray-500 mb-1">Custo BRL (hoje)</p>
          <p className="text-2xl font-bold text-sofia-600">
            R$ {today.cost_brl.toFixed(3)}
          </p>
        </div>
      </div>

      {/* Budget */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Budget Diário</h3>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500">
            {budget.used_today.toLocaleString()} / {budget.daily_tokens.toLocaleString()} tokens
          </span>
          <span className={`text-xs font-bold ${
            budget.percent_used > 80 ? 'text-red-600' :
            budget.percent_used > 50 ? 'text-amber-600' :
            'text-green-600'
          }`}>
            {budget.percent_used.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              budget.percent_used > 80 ? 'bg-red-500' :
              budget.percent_used > 50 ? 'bg-amber-500' :
              'bg-sofia-500'
            }`}
            style={{ width: `${Math.min(budget.percent_used, 100)}%` }}
          />
        </div>
      </div>

      {/* History */}
      {history.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Últimos 14 dias</h3>
          <div className="space-y-1">
            {history.map((item) => (
              <div key={item.date} className="flex items-center justify-between text-xs">
                <span className="text-gray-600">{item.date}</span>
                <span className="text-gray-600">{item.calls} calls</span>
                <span className="font-medium text-gray-900">
                  R$ {item.cost_brl.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function CostCard({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-900">{value}</p>
      <p className="text-[10px] text-gray-400">{unit}</p>
    </div>
  );
}