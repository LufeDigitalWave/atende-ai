import { ArrowRight, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CONTACT_URL } from '../../lib/constants';

export default function CTASection() {
  return (
    <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-brand-violet/25 via-dark-surface to-brand-cyan/20 px-6 py-12 text-center shadow-2xl shadow-brand-violet/10 sm:px-10 lg:px-16">
      <div className="absolute left-1/2 top-0 h-64 w-64 -translate-x-1/2 rounded-full bg-brand-cyan/20 blur-3xl" aria-hidden="true" />
      <div className="relative mx-auto max-w-3xl">
        <div className="mx-auto mb-5 flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-gray-200">
          <ShieldCheck className="h-4 w-4 text-brand-cyan" aria-hidden="true" />
          API oficial Meta no modelo de produção, sem depender de gambiarras de sessão
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Quer ver isso no WhatsApp da sua empresa?
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-gray-300">
          Eu monto um piloto rápido com seu nicho, suas perguntas frequentes e o fluxo comercial que você usa hoje.
        </p>
        <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <a
            href={CONTACT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold text-dark-bg transition-transform hover:-translate-y-0.5 hover:bg-gray-100"
          >
            Pedir piloto no WhatsApp
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </a>
          <Link
            to="/demo"
            className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/15 px-6 py-3 text-sm font-bold text-white transition-colors hover:bg-white/10"
          >
            Testar a demo SDR
          </Link>
        </div>
      </div>
    </section>
  );
}
