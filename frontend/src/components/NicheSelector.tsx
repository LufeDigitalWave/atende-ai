import { useState } from 'react';
import { Sparkles, PawPrint, Home, Scale, UtensilsCrossed, Dumbbell, Monitor, Globe } from 'lucide-react';

const NICHES = [
  { id: 'clinica_estetica', label: 'Clínica de Estética', icon: Sparkles },
  { id: 'pet_shop', label: 'Pet Shop / Veterinária', icon: PawPrint },
  { id: 'imobiliaria', label: 'Imobiliária', icon: Home },
  { id: 'advocacia', label: 'Advocacia', icon: Scale },
  { id: 'restaurante', label: 'Restaurante', icon: UtensilsCrossed },
  { id: 'academia', label: 'Academia', icon: Dumbbell },
  { id: 'saas', label: 'SaaS / Tecnologia', icon: Monitor },
  { id: 'escola_idiomas', label: 'Escola de Idiomas', icon: Globe },
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
      <div className="min-h-screen flex items-center justify-center bg-dark-bg relative overflow-hidden">
        {/* Gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-violet rounded-full opacity-20 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-cyan rounded-full opacity-20 blur-3xl" />

        <div className="text-center relative z-10">
          <div className="w-16 h-16 mx-auto mb-6 relative">
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-brand-violet to-brand-cyan animate-pulse" />
            <div className="absolute inset-2 rounded-full bg-dark-bg" />
          </div>
          <p className="text-xl font-semibold text-white mb-2">
            Gerando sua agente personalizada
          </p>
          <p className="text-sm text-gray-400">
            Analisando nicho → construindo perfil → preparando base de conhecimento
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg relative overflow-hidden p-4">
      {/* Gradient orbs for depth */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-violet rounded-full opacity-20 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-cyan rounded-full opacity-20 blur-3xl" />

      <div className="max-w-2xl w-full relative z-10">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-brand-violet_light to-brand-cyan_light bg-clip-text text-transparent mb-4">
            Atende AI
          </h1>
          <p className="text-gray-300 text-base max-w-md mx-auto">
            Escolha o ramo da sua empresa e veja um agente SDR de IA personalizado
            qualificando leads em tempo real.
          </p>
        </div>

        {/* Niche grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
          {NICHES.map((niche) => (
            <button
              key={niche.id}
              onClick={() => onSelect(niche.label)}
              className="flex flex-col items-center gap-3 p-5 rounded-xl bg-dark-surface border border-dark-border hover:border-brand-violet hover:shadow-lg hover:shadow-brand-violet/20 hover:-translate-y-0.5 transition-all cursor-pointer group"
            >
              <niche.icon className="w-7 h-7 text-brand-violet group-hover:text-brand-cyan group-hover:scale-110 transition-all" />
              <span className="text-xs font-medium text-gray-200 text-center">
                {niche.label}
              </span>
            </button>
          ))}
        </div>

        {/* Custom input */}
        <div className="text-center mb-8">
          <p className="text-xs text-gray-500 mb-3">Ou digite seu ramo:</p>
          <form onSubmit={handleCustomSubmit} className="flex gap-2 max-w-sm mx-auto">
            <input
              type="text"
              value={customNiche}
              onChange={(e) => setCustomNiche(e.target.value)}
              placeholder="Ex: consultório odontológico"
              className="flex-1 px-4 py-2.5 text-sm bg-dark-surface border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-brand-violet transition-colors"
            />
            <button
              type="submit"
              disabled={!customNiche.trim()}
              className="px-5 py-2.5 text-sm font-medium bg-gradient-to-r from-brand-violet to-brand-cyan text-white rounded-lg hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              Testar →
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-500">
          <p>A IA gera um agente SDR sob medida pro seu nicho em 2-3 segundos.</p>
          <p className="mt-1">Empresa e dados são 100% fictícios. A IA é real.</p>
        </div>
      </div>
    </div>
  );
}
