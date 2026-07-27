import { Link, NavLink } from 'react-router-dom';
import { Bot, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { CONTACT_URL } from '../../lib/constants';

const navItems = [
  { to: '/', label: 'Início' },
  { to: '/agentes', label: 'Agentes' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/como-funciona', label: 'Como funciona' },
  { to: '/demo', label: 'Demo' },
];

export default function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-dark-bg/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex min-h-11 items-center gap-3 text-white" aria-label="Atende AI — início">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-violet to-brand-cyan shadow-lg shadow-brand-violet/20">
            <Bot className="h-5 w-5" aria-hidden="true" />
          </span>
          <span>
            <span className="block text-sm font-bold leading-none">Atende AI</span>
            <span className="block text-xs text-gray-400">WhatsApp Agents</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Navegação principal">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  isActive ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <a
            href={CONTACT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="min-h-11 rounded-full bg-white px-5 py-2.5 text-sm font-bold text-dark-bg transition-transform hover:-translate-y-0.5 hover:bg-gray-100"
          >
            Pedir piloto
          </a>
        </div>

        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-xl border border-white/10 text-white md:hidden"
          aria-label={open ? 'Fechar menu' : 'Abrir menu'}
          aria-expanded={open}
        >
          {open ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-white/10 px-4 pb-4 md:hidden">
          <nav className="flex flex-col gap-2" aria-label="Navegação mobile">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `rounded-xl px-4 py-3 text-sm font-medium ${
                    isActive ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
            <a
              href={CONTACT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 rounded-xl bg-white px-4 py-3 text-center text-sm font-bold text-dark-bg"
            >
              Pedir piloto
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
