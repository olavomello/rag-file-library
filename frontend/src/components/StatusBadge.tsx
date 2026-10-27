import type { HealthStatusValue } from '../types';

const STYLES: Record<HealthStatusValue | 'loading', string> = {
  ok: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300',
  unavailable: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300',
  error: 'bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300',
  loading: 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300',
};

const LABELS: Record<HealthStatusValue | 'loading', string> = {
  ok: 'Online',
  unavailable: 'Unavailable',
  error: 'Error',
  loading: 'Checking…',
};

interface StatusBadgeProps {
  status: HealthStatusValue | 'loading';
}

export function StatusBadge({ status }: StatusBadgeProps): JSX.Element {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
