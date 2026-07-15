import type { AdminAgentInfo } from '../../lib/admin-api';

interface AdminAgenteProps {
  info: AdminAgentInfo;
}

/**
 * Info do agente (versão de prompt, modelo, configurações).
 */
export default function AdminAgente({ info }: AdminAgenteProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-bold">Agente · Configuração</h2>
      <p className="text-xs text-gray-500">
        Somente leitura. Para alterar, edite o .env e reinicie o container.
      </p>

      <div className="bg-white border border-gray-200 rounded-lg divide-y divide-gray-100">
        <ConfigRow label="Provider" value={info.provider} highlight />
        <ConfigRow label="Modelo" value={info.model} />
        <ConfigRow label="Versão do Prompt" value={info.prompt_version} />
        <ConfigRow label="SHA-256 do Prompt" value={info.prompt_sha256 || '—'} mono />
        <ConfigRow label="Temperatura" value={String(info.temperature)} />
        <ConfigRow label="Embeddings" value={info.embedding_provider} />
        <ConfigRow label="Modelo de Embedding" value={info.embedding_model || '—'} />
      </div>

      {/* Instructions */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Como versionar o prompt</h3>
        <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
          <li>Edite backend/app/agent/prompts/sofia_v1.md (ou crie sofia_v2.md)</li>
          <li>Atualize AGENT_PROMPT_VERSION no .env</li>
          <li>Reinicie: docker compose restart api</li>
          <li>Adicione entrada no docs/AGENT_PROMPT.md (changelog)</li>
          <li>Rode pytest para validar carregamento</li>
        </ol>
      </div>
    </div>
  );
}

function ConfigRow({
  label,
  value,
  highlight,
  mono,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <span className="text-sm text-gray-600">{label}</span>
      <span
        className={`text-sm font-medium ${
          highlight ? 'text-sofia-600 bg-sofia-50 px-2 py-0.5 rounded' :
          mono ? 'font-mono text-xs text-gray-400' :
          'text-gray-900'
        }`}
      >
        {value}
      </span>
    </div>
  );
}