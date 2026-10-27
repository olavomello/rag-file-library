import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { StatusBadge } from '../../components/StatusBadge';
import { useTheme, type ThemePreference } from '../../app/theme';
import { ApiError } from '../../services/apiClient';
import { fetchModelsStatus, fetchSettings, updateSettings } from '../../services/dashboard';
import type { SettingsUpdate, SettingsView } from '../../types';

type FormState = Record<string, string>;

function toForm(settings: SettingsView): FormState {
  return {
    generation_model: settings.generation_model,
    embedding_model: settings.embedding_model,
    temperature: String(settings.temperature),
    max_output_tokens: String(settings.max_output_tokens),
    context_window: String(settings.context_window),
    chunk_size: String(settings.chunk_size),
    chunk_overlap: String(settings.chunk_overlap),
    search_top_k: String(settings.search_top_k),
    rag_max_context_chunks: String(settings.rag_max_context_chunks),
    rag_max_context_chars: String(settings.rag_max_context_chars),
    max_upload_size_mb: String(settings.max_upload_size_mb),
    indexing_concurrency: String(settings.indexing_concurrency),
    generation_concurrency: String(settings.generation_concurrency),
  };
}

function toPatch(form: FormState): SettingsUpdate {
  return {
    generation_model: form.generation_model,
    embedding_model: form.embedding_model,
    temperature: Number(form.temperature),
    max_output_tokens: Number(form.max_output_tokens),
    context_window: Number(form.context_window),
    chunk_size: Number(form.chunk_size),
    chunk_overlap: Number(form.chunk_overlap),
    search_top_k: Number(form.search_top_k),
    rag_max_context_chunks: Number(form.rag_max_context_chunks),
    rag_max_context_chars: Number(form.rag_max_context_chars),
    max_upload_size_mb: Number(form.max_upload_size_mb),
    indexing_concurrency: Number(form.indexing_concurrency),
    generation_concurrency: Number(form.generation_concurrency),
  };
}

const NUMBER_FIELDS: { key: string; label: string; step?: string }[] = [
  { key: 'chunk_size', label: 'Chunk size (tokens)' },
  { key: 'chunk_overlap', label: 'Chunk overlap (tokens)' },
  { key: 'search_top_k', label: 'Search results (top k)' },
  { key: 'rag_max_context_chunks', label: 'RAG context chunks' },
  { key: 'rag_max_context_chars', label: 'RAG context chars' },
  { key: 'max_upload_size_mb', label: 'Max upload size (MB)' },
  { key: 'temperature', label: 'Temperature', step: '0.1' },
  { key: 'max_output_tokens', label: 'Max output tokens' },
  { key: 'context_window', label: 'Context window' },
  { key: 'indexing_concurrency', label: 'Indexing concurrency' },
  { key: 'generation_concurrency', label: 'Generation concurrency' },
];

export function SettingsPage(): JSX.Element {
  const queryClient = useQueryClient();
  const { preference, setPreference } = useTheme();
  const settings = useQuery({ queryKey: ['settings'], queryFn: () => fetchSettings() });
  const models = useQuery({ queryKey: ['models', 'status'], queryFn: () => fetchModelsStatus() });

  const [form, setForm] = useState<FormState | null>(null);
  const [result, setResult] = useState<{ reindex: boolean; restart: boolean; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (settings.data && !form) setForm(toForm(settings.data));
  }, [settings.data, form]);

  const save = useMutation({
    mutationFn: updateSettings,
    onSuccess: (response) => {
      setError(null);
      setResult({
        reindex: response.requires_reindex,
        restart: response.requires_restart,
        message: response.message,
      });
      setForm(toForm(response.settings));
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (err) => {
      setResult(null);
      setError(err instanceof ApiError ? err.detail ?? err.message : 'Update failed.');
    },
  });

  function onSave(event: React.FormEvent): void {
    event.preventDefault();
    if (!form) return;
    const patch = toPatch(form);
    if (Object.values(patch).some((v) => typeof v === 'number' && Number.isNaN(v))) {
      setError('All numeric fields must be valid numbers.');
      return;
    }
    save.mutate(patch);
  }

  function set(key: string, value: string): void {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  return (
    <div>
      <header className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Settings</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Appearance and configuration. Saved changes are applied on the next restart.
        </p>
      </header>

      <section className="mb-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">Appearance</h3>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600 dark:text-slate-300">Theme</span>
          <div className="inline-flex overflow-hidden rounded-md border border-slate-300 dark:border-slate-700">
            {(['light', 'system', 'dark'] as ThemePreference[]).map((option) => (
              <button
                key={option}
                onClick={() => setPreference(option)}
                className={`px-3 py-1.5 text-sm capitalize transition-colors ${
                  preference === option
                    ? 'bg-brand-600 text-white'
                    : 'bg-white text-slate-600 hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="mb-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">Models</h3>
        <ModelRow label="Generation" value={form?.generation_model} available={models.data?.generation_available} loading={models.isLoading} />
        <ModelRow label="Embedding" value={form?.embedding_model} available={models.data?.embedding_available} loading={models.isLoading} />
        <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
          Changing the embedding model requires re-indexing every document, so vectors are not
          mixed across models.
        </p>
      </section>

      <form
        onSubmit={onSave}
        className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
      >
        <h3 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-200">Configuration</h3>

        {!form ? (
          <p className="text-sm text-slate-400 dark:text-slate-500">Loading…</p>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2">
              <TextField label="Generation model" value={form.generation_model ?? ''} onChange={(v) => set('generation_model', v)} />
              <TextField label="Embedding model" value={form.embedding_model ?? ''} onChange={(v) => set('embedding_model', v)} />
              {NUMBER_FIELDS.map((field) => (
                <NumberField
                  key={field.key}
                  label={field.label}
                  step={field.step}
                  value={form[field.key] ?? ''}
                  onChange={(v) => set(field.key, v)}
                />
              ))}
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={save.isPending}
                className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
              >
                {save.isPending ? 'Saving…' : 'Save settings'}
              </button>
              {result && (
                <span className="text-sm text-slate-600 dark:text-slate-300">
                  {result.message}
                </span>
              )}
              {error && <span className="text-sm text-rose-600 dark:text-rose-400">{error}</span>}
            </div>

            {result && (result.restart || result.reindex) && (
              <div className="mt-3 flex flex-wrap gap-2">
                {result.restart && (
                  <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                    Restart required
                  </span>
                )}
                {result.reindex && (
                  <span className="rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-medium text-rose-700 dark:bg-rose-500/15 dark:text-rose-300">
                    Reindex required
                  </span>
                )}
              </div>
            )}
          </>
        )}
      </form>
    </div>
  );
}

function ModelRow({
  label,
  value,
  available,
  loading,
}: {
  label: string;
  value: string | undefined;
  available: boolean | undefined;
  loading: boolean;
}): JSX.Element {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-2 last:border-0 dark:border-slate-800">
      <span className="text-sm text-slate-600 dark:text-slate-300">
        {label} · <span className="font-medium text-slate-900 dark:text-slate-100">{value ?? '—'}</span>
      </span>
      <StatusBadge status={loading ? 'loading' : available ? 'ok' : 'unavailable'} />
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  step,
  onChange,
}: {
  label: string;
  value: string;
  step?: string;
  onChange: (value: string) => void;
}): JSX.Element {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</span>
      <input
        type="number"
        step={step}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
      />
    </label>
  );
}
