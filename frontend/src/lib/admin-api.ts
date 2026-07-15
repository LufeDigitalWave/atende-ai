/**
 * Admin API client.
 */

const API_URL = import.meta.env.VITE_API_URL || '';

interface AdminLoginResponse {
  token: string;
  expires_at: string;
}

interface AdminSession {
  session_id: string;
  created_at: string;
  last_activity_at: string;
  message_count: number;
  status: string;
  lead_name: string | null;
  lead_state: string | null;
  lead_score: number | null;
}

interface AdminSessionsList {
  total: number;
  items: AdminSession[];
}

interface AdminCostsToday {
  calls: number;
  input_tokens: number;
  output_tokens: number;
  cached_tokens: number;
  cost_usd: number;
  cost_brl: number;
}

interface AdminCostsBudget {
  daily_tokens: number;
  used_today: number;
  percent_used: number;
}

interface AdminCostsResponse {
  today: AdminCostsToday;
  history: Array<{ date: string; calls: number; cost_brl: number }>;
  budget: AdminCostsBudget;
}

interface AdminAgentInfo {
  provider: string;
  model: string;
  prompt_version: string;
  prompt_sha256: string;
  temperature: number;
  embedding_provider: string;
  embedding_model: string | null;
}

interface AdminKanban {
  novo: unknown[];
  em_qualificacao: unknown[];
  qualificado: unknown[];
  agendamento_proposto: unknown[];
  handoff: unknown[];
}

function authHeaders(token: string | null): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || response.statusText);
  }
  return response.json();
}

export async function adminLogin(username: string, password: string): Promise<AdminLoginResponse> {
  const response = await fetch(`${API_URL}/api/admin/login`, {
    method: 'POST',
    headers: authHeaders(null),
    body: JSON.stringify({ username, password }),
  });
  return handleResponse<AdminLoginResponse>(response);
}

export async function listSessions(token: string): Promise<AdminSessionsList> {
  const response = await fetch(`${API_URL}/api/admin/conversas?limit=50`, {
    headers: authHeaders(token),
  });
  return handleResponse<AdminSessionsList>(response);
}

export async function getKanban(token: string): Promise<AdminKanban> {
  const response = await fetch(`${API_URL}/api/admin/leads`, {
    headers: authHeaders(token),
  });
  return handleResponse<AdminKanban>(response);
}

export async function getCosts(token: string): Promise<AdminCostsResponse> {
  const response = await fetch(`${API_URL}/api/admin/custos?days=14`, {
    headers: authHeaders(token),
  });
  return handleResponse<AdminCostsResponse>(response);
}

export async function getAgentInfo(token: string): Promise<AdminAgentInfo> {
  const response = await fetch(`${API_URL}/api/admin/agente`, {
    headers: authHeaders(token),
  });
  return handleResponse<AdminAgentInfo>(response);
}