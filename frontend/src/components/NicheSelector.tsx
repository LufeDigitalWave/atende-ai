import { useState } from 'react';

const NICHES = [
  { id: 'clinica_estetica', label: 'Clínica de Estética', emoji: '💆' },
  { id: 'pet_shop', label: 'Pet Shop / Veterinária', emoji: '🐾' },
  { id: 'imobiliaria', label: 'Imobiliária', emoji: '🏠' },
  { id: 'advocacia', label: 'Advocacia', emoji: '⚖️' },
  { id: 'restaurante', label: 'Restaurante', emoji: '🍽️' },
  { id: 'academia', label: 'Academia', emoji: '💪' },
  { id: 'saas', label: 'SaaS / Tecnologia', emoji: '💻' },
  { id: 'escola_idiomas', label: 'Escola de Idiomas', emoji: '🌍' },
];

interface NicheSelectorProps {
  onSelect: (niche: string) => void;
  loading: boolean;
}

export default function NicheSelector({ onSelect, loading }: NicheSelectorProps) {
  const [customNiche, setCustomNiche] = useState('');

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customNiche.trim()) {
      onSelect(customNiche.trim());
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sofia-50 to-white">
        <div className="text-center">
          <div className="w-12 h-12 animate-spin mx-auto mb-4 border-4 border-sofia-500 border-t-transparent rounded-full" />
          <p className="text-lg font-medium text-gray-800">Gerando agente personalizado...</p>
          <p className="text-sm text-gray-500 mt-1">Isso leva 2-3 segundos</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sofia-50 to-white p-4">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Atende AI — Demo ao Vivo
          </h1>
          <p className="text-gray-600 text-sm max-w-md mx-auto">
            Escolha o ramo da sua empresa e veja um agente SDR de IA personalizado
            qualificando leads em tempo real — com CRM ao vivo.
          </p>
        </div>

        {/* Niche grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {NICHES.map((niche) => (
            <button
              key={niche.id}
              onClick={() => onSelect(niche.label)}
              className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 bg-white hover:border-sofia-400 hover:shadow-md transition-all cursor-pointer group"
            >
              <span className="text-2xl group-hover:scale-110 transition-transform">
                {niche.emoji}
              </span>
              <span className="text-xs font-medium text-gray-700 text-center">
                {niche.label}
              </span>
            </button>
          ))}
        </div>

        {/* Custom input */}
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-2">Ou digite seu ramo:</p>
          <form onSubmit={handleCustomSubmit} className="flex gap-2 max-w-sm mx-auto">
            <input
              type="text"
              value={customNiche}
              onChange={(e) => setCustomNiche(e.target.value)}
              placeholder="Ex: consultório odontológico"
              className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-sofia-500"
            />
            <button
              type="submit"
              disabled={!customNiche.trim()}
              className="px-4 py-2 text-sm font-medium bg-sofia-500 text-white rounded-lg hover:bg-sofia-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Testar →
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-xs text-gray-400">
          <p>A IA gera um agente SDR sob medida pro seu nicho em 2-3 segundos.</p>
          <p className="mt-1">Empresa e dados são 100% fictícios. A IA é real (OpenAI GPT-4o-mini).</p>
        </div>
      </div>
    </div>
  );
}
