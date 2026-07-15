/**
 * "Digitando..." indicator with animated dots.
 */
export default function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="chat-bubble-agent">
        <div className="typing-indicator">
          <div className="typing-dot" style={{ animationDelay: '0ms' }} />
          <div className="typing-dot" style={{ animationDelay: '150ms' }} />
          <div className="typing-dot" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
