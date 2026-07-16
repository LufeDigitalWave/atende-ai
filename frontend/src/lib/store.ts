import { create } from 'zustand';

export interface Message {
  id: string;
  role: 'user' | 'agent' | 'system_event';
  content: string;
  createdAt: string;
  isStreaming?: boolean;
}

export interface CRMField {
  key: string;
  label: string;
  priority: string;
}

export interface LeadProfile {
  name: string | null;
  serviceInterest: string | null;
  complaint: string | null;
  budgetRange: string;
  urgency: string;
  score: number;
  state: string;
  scoreBreakdown: Record<string, number>;
  scheduledSlot: string | null;
  // v3: dynamic fields per niche
  dynamicFields: Record<string, string | number | boolean | null>;
}

export interface LeadEvent {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  createdAt: string;
}

export interface QuickReply {
  id: string;
  label: string;
}

interface SessionState {
  sessionId: string | null;
  messages: Message[];
  lead: LeadProfile | null;
  events: LeadEvent[];
  isTyping: boolean;
  quickReplies: QuickReply[];
  isCapped: boolean;
  bannerMessage: string | null;

  setSessionId: (id: string) => void;
  addMessage: (msg: Message) => void;
  appendToLastAgent: (delta: string) => void;
  setTyping: (val: boolean) => void;
  updateLead: (fields: Partial<LeadProfile>) => void;
  setScore: (total: number, breakdown: Record<string, number>) => void;
  setState: (state: string) => void;
  addEvent: (event: LeadEvent) => void;
  setQuickReplies: (replies: QuickReply[]) => void;
  clearQuickReplies: () => void;
  setCapped: () => void;
  setBanner: (msg: string | null) => void;
  reset: () => void;
}

const initialLead: LeadProfile = {
  name: null,
  serviceInterest: null,
  complaint: null,
  budgetRange: 'nao_informado',
  urgency: 'nao_informada',
  score: 0,
  state: 'novo',
  scoreBreakdown: {},
  scheduledSlot: null,
  dynamicFields: {},
};

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null,
  messages: [],
  lead: { ...initialLead },
  events: [],
  isTyping: false,
  quickReplies: [],
  isCapped: false,
  bannerMessage: null,

  setSessionId: (id) => set({ sessionId: id }),

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  appendToLastAgent: (delta) =>
    set((state) => {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'agent') {
        msgs[msgs.length - 1] = { ...last, content: last.content + delta };
      }
      return { messages: msgs };
    }),

  setTyping: (val) => set({ isTyping: val }),

  updateLead: (fields) =>
    set((state) => ({
      lead: state.lead ? { ...state.lead, ...fields } : { ...initialLead, ...fields },
    })),

  setScore: (total, breakdown) =>
    set((state) => ({
      lead: state.lead ? { ...state.lead, score: total, scoreBreakdown: breakdown } : null,
    })),

  setState: (newState) =>
    set((state) => ({
      lead: state.lead ? { ...state.lead, state: newState } : null,
    })),

  addEvent: (event) =>
    set((state) => ({ events: [...state.events, event] })),

  setQuickReplies: (replies) => set({ quickReplies: replies }),
  clearQuickReplies: () => set({ quickReplies: [] }),

  setCapped: () => set({ isCapped: true }),
  setBanner: (msg) => set({ bannerMessage: msg }),

  reset: () =>
    set({
      messages: [],
      lead: { ...initialLead },
      events: [],
      isTyping: false,
      quickReplies: [],
      isCapped: false,
      bannerMessage: null,
    }),
}));
