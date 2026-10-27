import { useQuery } from '@tanstack/react-query';

import { StatCard } from '../../components/StatCard';
import { StatusBadge } from '../../components/StatusBadge';
import { fetchChromaHealth, fetchOllamaHealth } from '../../services/health';
import { fetchDashboardStats, fetchModelsStatus } from '../../services/dashboard';
import type { ComponentHealthResponse, HealthStatusValue } from '../../types';

function toStatus(query: {
  data?: ComponentHealthResponse;
  isLoading: boolean;
  isError: boolean;
}): HealthStatusValue | 'loading' {
  if (query.isError) return 'error';
  if (query.data) return query.data.status;
  if (query.isLoading) return 'loading';
  return 'unavailable';
}

export function DashboardPage(): JSX.Element {
  const stats = useQuery({ queryKey: ['dashboard', 'stats'], queryFn: () => fetchDashboardStats() });
  const ollama = useQuery({ queryKey: ['health', 'ollama'], queryFn: () => fetchOllamaHealth() });
  const chroma = useQuery({ queryKey: ['health', 'chroma'], queryFn: () => fetchChromaHealth() });
  const models = useQuery({ queryKey: ['models', 'status'], queryFn: () => fetchModelsStatus() });

  const s = stats.data;

  return (
    <div>
      <header className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">Dashboard</h2>
        <p className="text-sm text-slate-500">Knowledge base overview and infrastructure status.</p>
      </header>

      <section className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <StatCard label="Documents" value={s?.total_documents ?? '—'} />
        <StatCard label="Indexed" value={s?.indexed ?? '—'} tone="good" />
        <StatCard label="Pending" value={s ? s.pending + s.processing + s.uploaded : '—'} tone="warn" />
        <StatCard label="Failed" value={s?.failed ?? '—'} tone={s && s.failed > 0 ? 'bad' : 'default'} />
        <StatCard label="Chunks" value={s?.total_chunks ?? '—'} />
        <StatCard label="Active jobs" value={s?.active_jobs ?? '—'} tone={s && s.active_jobs > 0 ? 'warn' : 'default'} />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Infrastructure</h3>
          <Row label="Embedded ChromaDB" status={toStatus(chroma)} detail={chroma.data?.detail} />
          <Row label="Ollama" status={toStatus(ollama)} detail={ollama.data?.detail} />
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Models</h3>
          <Row
            label={`Generation · ${s?.generation_model ?? models.data?.generation_model ?? '—'}`}
            status={models.isLoading ? 'loading' : models.data?.generation_available ? 'ok' : 'unavailable'}
          />
          <Row
            label={`Embedding · ${s?.embedding_model ?? models.data?.embedding_model ?? '—'}`}
            status={models.isLoading ? 'loading' : models.data?.embedding_available ? 'ok' : 'unavailable'}
          />
          {models.data && !models.data.ollama_available && (
            <p className="mt-3 text-xs text-slate-400">
              Ollama is not reachable. Install it and run{' '}
              <code className="rounded bg-slate-100 px-1">ollama pull {models.data.generation_model}</code>{' '}
              and <code className="rounded bg-slate-100 px-1">ollama pull {models.data.embedding_model}</code>.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}

function Row({
  label,
  status,
  detail,
}: {
  label: string;
  status: HealthStatusValue | 'loading';
  detail?: string | null;
}): JSX.Element {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-2.5 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-800">{label}</p>
        {detail && <p className="text-xs text-slate-400">{detail}</p>}
      </div>
      <StatusBadge status={status} />
    </div>
  );
}
