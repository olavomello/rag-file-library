import type { DocumentStatus } from '../types';

const STYLES: Record<DocumentStatus, string> = {
  uploaded: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  pending: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300',
  processing: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300',
  indexed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300',
  failed: 'bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300',
  deleting: 'bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-400',
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
