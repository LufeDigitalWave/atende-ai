# CTA Audit — 1 primário por rota

**Data:** 2026-07-29  
**Regra:** cada rota tem exatamente 1 CTA primário (visualmente dominante) e 0-1 secundários.

| Rota | CTA primário | Destino | Motivo |
| --- | --- | --- | --- |
| `/` | Testar demo SDR | `/demo` | Demo é a entrada do funil; visitante precisa experimentar antes de comprar |
| `/demo` | Quero no meu negócio | WhatsApp (CONTACT_URL) | Aparece após 4 msgs ou qualificação — momento de maior engajamento |
| `/agentes` | Testar SDR Agent | `/demo` | Único agente funcional; demais direcionam para WhatsApp como secundário |
| `/pricing` | Pedir piloto Pro | WhatsApp (CONTACT_URL) | Pro tem destaque visual; é o pacote mais lucrativo para primeiro cliente |
| `/como-funciona` | Testar demo | `/demo` | Sequência natural: entendeu → experimenta |

## Decisões

1. Não há competição de CTAs: cada rota direciona para um único próximo passo.
2. O WhatsApp aparece como primário apenas em `/pricing` (momento de decisão) e `/demo` (momento de engajamento pós-qualificação).
3. Landing (`/`) prioriza demo sobre WhatsApp porque o visitante frio ainda não viu valor.
4. `/agentes` não compete com 6 CTAs diferentes; só SDR tem demo, os demais são "Pedir piloto" como secundário.
5. Nenhuma rota tem mais de 2 ações competindo above-the-fold.
