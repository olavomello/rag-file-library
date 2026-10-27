import { useQuery } from '@tanstack/react-query';

import { StatusBadge } from '../../components/StatusBadge';
import { fetchChromaHealth, fetchLiveness, fetchOllamaHealth } from '../../services/health';
import type { ComponentHealthResponse, HealthStatusValue } from '../../types';

function InfraRow({
  label,
  query,
}: {
  label: string;
  query: { data?: ComponentHealthResponse; isLoading: boolean; isError: boolean };
}): JSX.Element {
  let status: HealthStatusValue | 'loading' = 'loading';
  if (query.isError) status = 'error';
  else if (query.data) status = query.data.status;
  else if (!query.isLoading) status = 'unavailable';

  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-800">{label}</p>
        {query.data?.detail && <p className="text-xs text-slate-400">{query.data.detail}</p>}
      </div>
      <StatusBadge status={status} />
    </div>
  );
}

export function DashboardPage(): JSX.Element {
  const liveness = useQuery({ queryKey: ['health', 'liveness'], queryFn: () => fetchLiveness() });
  const ollama = useQuery({ queryKey: ['health', 'ollama'], queryFn: () => fetchOllamaHealth() });
  const chroma = useQuery({ queryKey: ['health', 'chroma'], queryFn: () => fetchChromaHealth() });

  return (
    <div>
      <header className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">Dashboard</h2>
        <p className="text-sm text-slate-500">
          Infrastructure status and knowledge base overview.
        </p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-700">Infrastructure</h3>
          <StatusBadge
            status={
              liveness.isLoading ? 'loading' : liveness.isError ? 'error' : 'ok'
            }
          />
        </div>
        <InfraRow label="Embedded ChromaDB" query={chroma} />
        <InfraRow label="Ollama (local models)" query={ollama} />
      </section>

      <p className="mt-6 text-xs text-slate-400">
        Document, indexing, and search statistics will appear here once the ingestion
        backend is available.
      </p>
    </div>
  );
}
