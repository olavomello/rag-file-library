import { useQuery } from '@tanstack/react-query';

import { StatusBadge } from '../../components/StatusBadge';
import { fetchModelsStatus, fetchSettings } from '../../services/dashboard';

export function SettingsPage(): JSX.Element {
  const settings = useQuery({ queryKey: ['settings'], queryFn: () => fetchSettings() });
  const models = useQuery({ queryKey: ['models', 'status'], queryFn: () => fetchModelsStatus() });

  const s = settings.data;

  return (
    <div>
      <header className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">Settings</h2>
        <p className="text-sm text-slate-500">Effective configuration (read-only in this version).</p>
      </header>

      <section className="mb-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Models</h3>
        <Field label="Generation model" value={s?.generation_model}>
          <StatusBadge
            status={models.isLoading ? 'loading' : models.data?.generation_available ? 'ok' : 'unavailable'}
          />
        </Field>
        <Field label="Embedding model" value={s?.embedding_model}>
          <StatusBadge
            status={models.isLoading ? 'loading' : models.data?.embedding_available ? 'ok' : 'unavailable'}
          />
        </Field>
        <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
          Changing the embedding model requires re-indexing every document, so vectors are not
          mixed across models.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Chunking &amp; search</h3>
          <Field label="Chunk size (tokens)" value={s?.chunk_size} />
          <Field label="Chunk overlap (tokens)" value={s?.chunk_overlap} />
          <Field label="Search results (top k)" value={s?.search_top_k} />
          <Field label="RAG context chunks" value={s?.rag_max_context_chunks} />
          <Field label="RAG context chars" value={s?.rag_max_context_chars} />
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Limits &amp; generation</h3>
          <Field label="Max upload size (MB)" value={s?.max_upload_size_mb} />
          <Field label="Indexing concurrency" value={s?.indexing_concurrency} />
          <Field label="Generation concurrency" value={s?.generation_concurrency} />
          <Field label="Temperature" value={s?.temperature} />
          <Field label="Max output tokens" value={s?.max_output_tokens} />
          <Field label="Context window" value={s?.context_window} />
        </div>
      </section>
    </div>
  );
}

function Field({
  label,
  value,
  children,
}: {
  label: string;
  value: string | number | undefined;
  children?: React.ReactNode;
}): JSX.Element {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-2 last:border-0">
      <span className="text-sm text-slate-600">{label}</span>
      <span className="flex items-center gap-2 text-sm font-medium text-slate-900">
        {value ?? '—'}
        {children}
      </span>
    </div>
  );
}
