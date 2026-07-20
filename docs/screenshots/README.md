# Screenshots e Demo Assets

Este diretório guarda os assets visuais referenciados no README.md.

## Como gerar o GIF da demo

### Opção 1 — ScreenToGif (Windows)

1. Abra `http://localhost:5173` com o dev server rodando.
2. Abra [ScreenToGif](https://www.screentogif.com/) e selecione a janela do browser.
3. Grave uma conversa de 15-30s: escolha nicho → envie 2-3 msgs → veja CRM preenchendo.
4. Exporte como GIF (≤5MB) e salve em `docs/demo.gif`.

### Opção 2 — Playwright (automático)

```bash
cd frontend
npx playwright install chromium
npx playwright screenshot http://localhost:5173 docs/screenshots/home.png --viewport-size="1280,720"
```

### Opção 3 — OBS Studio

Grave em MP4, converta com `ffmpeg -i demo.mp4 -vf "fps=10,scale=800:-1" docs/demo.gif`.

## Assets esperados

| Arquivo | Uso | Status |
|---|---|---|
| `docs/demo.gif` | Preview no README.md:9 | ⏳ pendente |
| `docs/screenshots/home.png` | NicheSelector desktop | ⏳ pendente |
| `docs/screenshots/chat-crm.png` | Chat + CRM lado a lado | ⏳ pendente |
| `docs/screenshots/admin.png` | Admin dashboard | ⏳ pendente |
| `frontend/public/og.png` | Open Graph preview (1200x630) | ⏳ pendente |
