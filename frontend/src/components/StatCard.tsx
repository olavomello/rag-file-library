interface StatCardProps {
  label: string;
  value: number | string;
  tone?: 'default' | 'good' | 'warn' | 'bad';
}

const TONES: Record<NonNullable<StatCardProps['tone']>, string> = {
  default: 'text-slate-900 dark:text-slate-100',
  good: 'text-emerald-600 dark:text-emerald-400',
  warn: 'text-amber-600 dark:text-amber-400',
  bad: 'text-rose-600 dark:text-rose-400',
};

export function StatCard({ label, value, tone = 'default' }: StatCardProps): JSX.Element {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">
        {label}
      </p>
      <p className={`mt-1 text-2xl font-semibold ${TONES[tone]}`}>{value}</p>
    </div>
  );
}
