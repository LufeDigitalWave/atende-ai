import LeadCard from './LeadCard';
import ScoreBar from './ScoreBar';
import Funnel from './Funnel';
import Timeline from './Timeline';

/**
 * Mini-CRM ao vivo — updates in real-time via SSE events.
 */
export default function CRMView() {
  return (
    <div className="hidden lg:flex lg:w-80 flex-col gap-3 overflow-y-auto">
      <LeadCard />
      <ScoreBar />
      <Funnel />
      <Timeline />
    </div>
  );
}