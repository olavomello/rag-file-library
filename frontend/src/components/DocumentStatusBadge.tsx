import type { DocumentStatus } from '../types';

const STYLES: Record<DocumentStatus, string> = {
  uploaded: 'bg-slate-100 text-slate-600',
  pending: 'bg-amber-100 text-amber-700',
  processing: 'bg-blue-100 text-blue-700',
  indexed: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-rose-100 text-rose-700',
  deleting: 'bg-slate-200 text-slate-500',
};

export function DocumentStatusBadge({ status }: { status: DocumentStatus }): JSX.Element {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STYLES[status]}`}
    >
      {status}
    </span>
  );
}
