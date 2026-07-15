/**
 * API client for Atende AI backend.
 *
 * Uses native fetch (no axios in production bundle — smaller).
 * SSE via EventSource pattern.
 */

const API_URL = import.meta.env.VITE_API_URL || '';

interface CreateSessionResponse {
  session_id: string;
  created_at: string;
  status: string;
  niche: string;
  agent_name: string;
  company_name: string;
  suggestions: string[];
}

interface SendMessageResponse {
  status: string;
}

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(
      body.detail || response.statusText,
      response.status,
      body.code,
    );
  }
  return response.json();
}

export async function createSession(niche?: string): Promise<CreateSessionResponse> {
  const response = await fetch(`${API_URL}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ niche: niche || '' }),
  });
  return handleResponse<CreateSessionResponse>(response);
}

export async function getSession(sessionId: string) {
  const response = await fetch(`${API_URL}/api/sessions/${sessionId}`);
  return handleResponse(response);
}

/**
 * Send message and process SSE stream.
 *
 * The backend returns text/event-stream for real-time updates.
 */
export async function sendMessage(
  sessionId: string,
  content: string,
  onToken: (delta: string) => void,
  onLeadUpdate: (fields: Record<string, unknown>) => void,
  onScoreUpdate: (total: number, breakdown: Record<string, number>) => void,
  onStateUpdate: (from: string, to: string) => void,
  onTimelineEvent: (type: string, payload: Record<string, unknown>) => void,
  onQuickReplies: (options: Array<{ id: string; label: string }>) => void,
  onDone: (latencyMs: number, messageId: string) => void,
  onError: (code: string, message: string) => void,
): Promise<void> {
  const response = await fetch(`${API_URL}/api/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(body.detail, response.status, body.code);
  }

  // Check if response is SSE
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('text/event-stream')) {
    // Fallback: non-streaming response
    const data = await response.json();
    if (data.agent_response) {
      onToken(data.agent_response);
    }
    onDone(0, '');
    return;
  }

  // Parse SSE stream
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body reader');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let currentEvent = '';

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        const dataStr = line.slice(6);
        try {
          const data = JSON.parse(dataStr);
          switch (currentEvent) {
            case 'token':
              onToken(data.delta);
              break;
            case 'lead_update':
              onLeadUpdate(data.fields);
              break;
            case 'score_update':
              onScoreUpdate(data.total, data.breakdown);
              break;
            case 'state_update':
              onStateUpdate(data.from, data.to);
              break;
            case 'timeline_event':
              onTimelineEvent(data.type, data.payload);
              break;
            case 'quick_replies':
              onQuickReplies(data.options);
              break;
            case 'done':
              onDone(data.latency_ms, data.message_id);
              break;
            case 'error':
              onError(data.code, data.message);
              break;
          }
        } catch {
          // Skip malformed JSON
        }
        currentEvent = '';
      }
    }
  }
}

/**
 * Admin login.
 */
export async function adminLogin(username: string, password: string) {
  const response = await fetch(`${API_URL}/api/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  return handleResponse(response);
}
