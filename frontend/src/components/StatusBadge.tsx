import type { HealthStatusValue } from '../types';

const STYLES: Record<HealthStatusValue | 'loading', string> = {
  ok: 'bg-emerald-100 text-emerald-700',
  unavailable: 'bg-amber-100 text-amber-700',
  error: 'bg-rose-100 text-rose-700',
  loading: 'bg-slate-100 text-slate-500',
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
