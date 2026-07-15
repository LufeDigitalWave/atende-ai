import type { QuickReply } from '../../lib/store';

interface QuickRepliesProps {
  options: QuickReply[];
  onSelect: (id: string, label: string) => void;
}

/**
 * Quick reply buttons (scheduling slots, confirmation options).
 */
export default function QuickReplies({ options, onSelect }: QuickRepliesProps) {
  return (
    <div className="flex flex-wrap gap-2 px-2 py-1">
      {options.map((opt) => (
        <button
          key={opt.id}
          onClick={() => onSelect(opt.id, opt.label)}
          className="quick-reply-btn"
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
