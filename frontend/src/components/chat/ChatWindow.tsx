import { useEffect, useRef, useState } from 'react';
import { useSessionStore } from '../../lib/store';
import { sendMessage, ApiError } from '../../lib/api';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import QuickReplies from './QuickReplies';
import ChatInput from './ChatInput';

// Fallback for crypto.randomUUID (not available in insecure contexts)
function uuid(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    try { return crypto.randomUUID(); } catch {}
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

interface ChatWindowProps {
  sessionId: string;
  agentName?: string;
  companyName?: string;
  suggestions?: string[];
}

const DEFAULT_SUGGESTIONS = [
  'Quero saber sobre limpeza de pele',
  'Quanto custa tratar melasma?',
  'Vocês atendem sábado?',
];

export default function ChatWindow({ sessionId, agentName = 'Sofia', companyName = 'Clínica Renova', suggestions = DEFAULT_SUGGESTIONS }: ChatWindowProps) {
  const {
    messages,
    isTyping,
    quickReplies,
    isCapped,
    bannerMessage,
    addMessage,
    appendToLastAgent,
    setTyping,
    updateLead,
    setScore,
    setState,
    addEvent,
    setQuickReplies,
    clearQuickReplies,
    setCapped,
    setBanner,
  } = useSessionStore();

  const [inputDisabled, setInputDisabled] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async (content: string) => {
    if (!content.trim() || inputDisabled || isCapped) return;

    // Add user message
    const userMsg = {
      id: uuid(),
      role: 'user' as const,
      content: content.trim(),
      createdAt: new Date().toISOString(),
    };
    addMessage(userMsg);
    clearQuickReplies();

    // Start typing indicator
    setTyping(true);
    setInputDisabled(true);

    // Create placeholder for agent response
    const agentMsgId = uuid();
    addMessage({
      id: agentMsgId,
      role: 'agent',
      content: '',
      createdAt: new Date().toISOString(),
      isStreaming: true,
    });

    try {
      await sendMessage(
        sessionId,
        content.trim(),
        // onToken
        (delta) => {
          appendToLastAgent(delta);
        },
        // onLeadUpdate
        (fields) => {
          const mapped: Record<string, unknown> = {};
          if (fields.name) mapped.name = fields.name;
          if (fields.service_interest) mapped.serviceInterest = fields.service_interest;
          if (fields.complaint) mapped.complaint = fields.complaint;
          if (fields.budget_range) mapped.budgetRange = fields.budget_range;
          if (fields.urgency) mapped.urgency = fields.urgency;
          updateLead(mapped);
        },
        // onScoreUpdate
        (total, breakdown) => {
          setScore(total, breakdown);
        },
        // onStateUpdate
        (from, to) => {
          setState(to);
          addEvent({
            id: uuid(),
            type: 'state_changed',
            payload: { from, to },
            createdAt: new Date().toISOString(),
          });
        },
        // onTimelineEvent
        (type, payload) => {
          addEvent({
            id: uuid(),
            type,
            payload,
            createdAt: new Date().toISOString(),
          });
        },
        // onQuickReplies
        (options) => {
          setQuickReplies(options);
        },
        // onDone
        () => {
          setTyping(false);
          setInputDisabled(false);
        },
        // onError
        (code, message) => {
          console.error(`SSE error: ${code} — ${message}`);
          setTyping(false);
          setInputDisabled(false);
        },
      );
    } catch (err) {
      setTyping(false);
      setInputDisabled(false);

      if (err instanceof ApiError) {
        if (err.status === 410) {
          setCapped();
        } else if (err.status === 503) {
          setBanner('Demo em alta demanda — volte amanhã ou fale conosco');
        }
      }
    }
  };

  const handleQuickReply = (id: string, label: string) => {
    handleSend(label);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* Chat header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
        <div className="relative">
          <div className="w-10 h-10 rounded-full bg-sofia-500 flex items-center justify-center text-white text-sm font-bold">
            {agentName.charAt(0)}
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-white" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 text-sm">{agentName}</h3>
          <p className="text-xs text-gray-500">SDR · IA · {companyName}</p>
        </div>
        <div className="ml-auto">
          <span className="text-xs bg-sofia-50 text-sofia-700 px-2 py-0.5 rounded-full font-medium">
            🤖 IA
          </span>
        </div>
      </div>

      {/* Banner */}
      {bannerMessage && (
        <div className="bg-amber-50 text-amber-800 text-xs px-4 py-2 border-b border-amber-100">
          {bannerMessage}
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500 text-sm mb-4">
              Comece a conversa com {agentName}!
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestions.map((sug) => (
                <button
                  key={sug}
                  onClick={() => handleSend(sug)}
                  className="quick-reply-btn"
                >
                  {sug}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isTyping && <TypingIndicator />}

        {quickReplies.length > 0 && (
          <QuickReplies options={quickReplies} onSelect={handleQuickReply} />
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={inputDisabled || isCapped}
        placeholder={
          isCapped
            ? 'Sessão encerrada'
            : 'Digite sua mensagem...'
        }
      />
    </div>
  );
}
