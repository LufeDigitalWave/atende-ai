import { useState, useRef, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Chat input with send button and Enter-to-send.
 */
export default function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    if (trimmed.length > 500) {
      // Enforce max input chars client-side
      return;
    }
    onSend(trimmed);
    setValue('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-gray-100 px-4 py-3 flex items-center gap-2">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder || 'Digite sua mensagem...'}
        maxLength={500}
        className="flex-1 px-3 py-2 text-sm bg-white text-gray-900 border border-gray-200 rounded-full outline-none focus:border-sofia-500 focus:ring-1 focus:ring-sofia-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
        aria-label="Mensagem"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
        className="w-9 h-9 flex items-center justify-center rounded-full bg-sofia-500 text-white hover:bg-sofia-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        aria-label="Enviar mensagem"
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
          <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" />
        </svg>
      </button>
    </div>
  );
}
