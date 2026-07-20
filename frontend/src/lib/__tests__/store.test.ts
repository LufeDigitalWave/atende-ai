import { describe, it, expect, beforeEach } from 'vitest';
import { useSessionStore } from '../store';

describe('useSessionStore', () => {
  beforeEach(() => {
    useSessionStore.getState().reset();
  });

  it('initial state has null sessionId and empty messages', () => {
    const state = useSessionStore.getState();
    expect(state.sessionId).toBeNull();
    expect(state.messages).toHaveLength(0);
    expect(state.lead).not.toBeNull();
    expect(state.lead?.state).toBe('novo');
  });

  it('setSessionId updates sessionId', () => {
    useSessionStore.getState().setSessionId('test-123');
    expect(useSessionStore.getState().sessionId).toBe('test-123');
  });

  it('addMessage appends to messages array', () => {
    const msg = {
      id: '1',
      role: 'user' as const,
      content: 'Olá',
      createdAt: new Date().toISOString(),
    };
    useSessionStore.getState().addMessage(msg);
    expect(useSessionStore.getState().messages).toHaveLength(1);
    expect(useSessionStore.getState().messages[0].content).toBe('Olá');
  });

  it('appendToLastAgent concatenates delta to last agent message', () => {
    useSessionStore.getState().addMessage({
      id: '1',
      role: 'agent',
      content: 'Olá,',
      createdAt: new Date().toISOString(),
    });
    useSessionStore.getState().appendToLastAgent(' como posso ajudar?');
    expect(useSessionStore.getState().messages[0].content).toBe('Olá, como posso ajudar?');
  });

  it('setState updates lead.state reactively', () => {
    useSessionStore.getState().setState('handoff');
    expect(useSessionStore.getState().lead?.state).toBe('handoff');
  });

  it('setScore updates lead.score and scoreBreakdown', () => {
    useSessionStore.getState().setScore(75, { name: 20, service: 30, intent: 25 });
    const lead = useSessionStore.getState().lead;
    expect(lead?.score).toBe(75);
    expect(lead?.scoreBreakdown).toEqual({ name: 20, service: 30, intent: 25 });
  });

  it('reset clears all state back to initial', () => {
    useSessionStore.getState().setSessionId('x');
    useSessionStore.getState().addMessage({ id: '1', role: 'user', content: 'hi', createdAt: '' });
    useSessionStore.getState().setState('handoff');
    useSessionStore.getState().setCapped();

    useSessionStore.getState().reset();

    const state = useSessionStore.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.lead?.state).toBe('novo');
    expect(state.isCapped).toBe(false);
  });
});
