import LeadCard from './LeadCard';
import ScoreBar from './ScoreBar';
import Funnel from './Funnel';
import Timeline from './Timeline';

interface CRMField {
  key: string;
  label: string;
  priority: string;
}

interface CRMViewProps {
  crmFields?: CRMField[];
}

/**
 * Mini-CRM ao vivo — updates in real-time via SSE events.
 * v3: renders dynamic fields per niche (not hardcoded 5 universals).
 */
export default function CRMView({ crmFields = [] }: CRMViewProps) {
  return (
    <div className="flex flex-col gap-3 overflow-y-auto">
      <LeadCard crmFields={crmFields} />
      <ScoreBar />
      <Funnel />
      <Timeline />
    </div>
  );
}
