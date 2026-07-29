/**
 * Server-side funnel tracking — no external analytics, no cookies.
 * Fires events to POST /api/events.
 */

const API_URL = import.meta.env.VITE_API_URL || '';

export type FunnelStep =
  | 'view_landing'
  | 'start_demo'
  | 'first_message'
  | 'reached_qualified'
  | 'lead_captured'
  | 'clicked_pricing'
  | 'clicked_whatsapp';

export function trackFunnel(step: FunnelStep, metadata: Record<string, unknown> = {}): void {
  const sessionId = sessionStorage.getItem('atende_session_id') || undefined;

  fetch(`${API_URL}/api/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      step,
      session_id: sessionId,
      metadata,
    }),
  }).catch(() => {
    // Fire and forget — tracking failure must never block UX
  });
}
