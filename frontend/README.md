# Atende AI Frontend

> React 18 + TypeScript + Vite + TailwindCSS — chat UI estilo WhatsApp (não oficial).

## Features

- ✓ Streaming de mensagens em tempo real (SSE)
- ✓ Indicador "digitando..."
- ✓ Quick replies (botões)
- ✓ Responsive (mobile & desktop)
- ✓ TypeScript strict mode
- ✓ TailwindCSS design
- ✓ Zustand state management
- ✓ TanStack Query (HTTP caching)

## Setup

```bash
cd frontend
npm install
npm run dev      # Vite dev server (port 5173)
npm run build    # Production build
```

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `src/App.tsx` | Layout principal (2 colunas: chat \| CRM) |
| `src/lib/store.ts` | Zustand state (messages, lead, events, quick replies) |
| `src/lib/api.ts` | API client com SSE parsing |
| `src/components/chat/ChatWindow.tsx` | Orquestra chat + agent turn |
| `src/components/chat/MessageBubble.tsx` | Renderiza uma mensagem |
| `src/components/chat/TypingIndicator.tsx` | Animação "digitando..." |
| `src/components/chat/QuickReplies.tsx` | Botões de quick reply |
| `src/components/chat/ChatInput.tsx` | Input + send button |

## SSE Client

O hook em `ChatWindow` chama `sendMessage()` que:

1. Faz `POST /api/sessions/{id}/messages`
2. Backend responde com `text/event-stream`
3. Parser lê events: `token`, `lead_update`, `score_update`, `state_update`, `quick_replies`, `done`
4. Cada event atualiza o Zustand store
5. Components re-render automaticamente

## Design

- **Cores:** Sofia verde (#22c55e) em vez de verde WhatsApp (#25D366)
- **Chat bubbles:** user=verde, agent=cinza claro
- **Check duplo:** ✓✓ em user messages
- **Timestamps:** HH:MM em PT-BR
- **Mobile:** abas [Chat | CRM] (passo 6)

## Próximas etapas (Passo 6)

- CRM ao vivo (direita, desktop apenas)
  - Card do lead com nome + score + state
  - Barra de score com breakdown
  - Funil (5 estados)
  - Timeline de eventos
- Página `/como-funciona` com FAQ
