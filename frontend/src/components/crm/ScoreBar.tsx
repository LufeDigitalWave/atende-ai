import { useState } from 'react';
import { useSessionStore } from '../../lib/store';

/**
 * Score bar with breakdown (expandible).
 */
export default function ScoreBar() {
  const lead = useSessionStore((s) => s.lead);
  const [expanded, setExpanded] = useState(false);

  if (!lead) return null;

  const score = lead.score;
  const breakdown = lead.scoreBreakdown || {};

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-2">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <h3 className="text-sm font-semibold text-gray-700">Score</h3>
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold text-sofia-600">{score}</span>
          <span className="text-xs text-gray-400">/100</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className="bg-gradient-to-r from-sofia-500 to-sofia-600 h-full transition-all duration-500"
          style={{ width: `${score}%` }}
        />
      </div>

      {/* Breakdown (expandible) */}
      {expanded && Object.keys(breakdown).length > 0 && (
        <div className="space-y-1 text-xs text-gray-600 mt-2 pt-2 border-t border-gray-100">
          {Object.entries(breakdown)
            .filter(([key]) => key !== 'total')
            .map(([key, val]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-500">{formatKey(key)}</span>
                <span className="font-medium text-sofia-600">+{val}</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

function formatKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
