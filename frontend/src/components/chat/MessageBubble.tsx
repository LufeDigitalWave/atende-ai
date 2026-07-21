import ReactMarkdown from 'react-markdown';
import type { Message } from '../../lib/store';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system_event';

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <span className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  const time = new Date(message.createdAt).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className="flex flex-col max-w-[75%]">
        <div className={isUser ? 'chat-bubble-user' : 'chat-bubble-agent'}>
          {message.content ? (
            <div className="prose prose-sm prose-gray max-w-none [&>p]:mb-2 [&>ul]:mb-2 [&>ul]:pl-4 [&>ol]:pl-4 [&>li]:mb-1">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          ) : (
            <span className="text-gray-400 italic">...</span>
          )}
        </div>
        <div
          className={`flex items-center gap-1 mt-0.5 ${
            isUser ? 'justify-end' : 'justify-start'
          }`}
        >
          <span className="text-[10px] text-gray-400">{time}</span>
          {isUser && (
            <span className="text-[10px] text-sofia-500" title="Entregue">
              ✓✓
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
