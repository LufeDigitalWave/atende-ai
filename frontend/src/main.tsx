import React, { Suspense, lazy } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import './index.css';

const Admin = lazy(() => import('./pages/Admin'));
const Agentes = lazy(() => import('./pages/Agentes'));
const ComoFunciona = lazy(() => import('./pages/ComoFunciona'));
const Demo = lazy(() => import('./pages/Demo'));
const Pricing = lazy(() => import('./pages/Pricing'));

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Suspense fallback={
        <div className="min-h-screen flex items-center justify-center bg-dark-bg">
          <p className="text-gray-400">Carregando...</p>
        </div>
      }>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/demo" element={<Demo />} />
          <Route path="/agentes" element={<Agentes />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/como-funciona" element={<ComoFunciona />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  </React.StrictMode>,
);
