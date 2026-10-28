import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { StatusBadge } from '../../components/StatusBadge';
import { useTheme, type ThemePreference } from '../../app/theme';
import { ApiError } from '../../services/apiClient';
import {
  fetchModelsStatus,
  fetchSettings,
  pullModel,
  updateSettings,
} from '../../services/dashboard';
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
  const [ocrEnabled, setOcrEnabled] = useState(false);
  const [result, setResult] = useState<{ reindex: boolean; restart: boolean; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (settings.data && !form) {
      setForm(toForm(settings.data));
      setOcrEnabled(settings.data.ocr_enabled);
    }
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
      setOcrEnabled(response.settings.ocr_enabled);
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
    const patch: SettingsUpdate = { ...toPatch(form), ocr_enabled: ocrEnabled };
    if (Object.values(patch).some((v) => typeof v === 'number' && Number.isNaN(v))) {
      setError('All numeric fields must be valid numbers.');
      return;
    }
    save.mutate(patch);
  }

  function set(key: string, value: string): void {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  function refreshModels(): void {
    queryClient.invalidateQueries({ queryKey: ['models'] });
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

            <label className="mt-4 flex items-start gap-3">
              <input
                type="checkbox"
                checked={ocrEnabled}
                onChange={(e) => setOcrEnabled(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-950"
              />
              <span className="flex flex-col">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                  Enable OCR (scanned PDFs &amp; images)
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Uses local OCR; indexing scanned files is slower.
                </span>
              </span>
            </label>

            <div className="mt-5 space-y-3 rounded-lg border border-slate-200 p-4 dark:border-slate-800">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-200">Models</h4>
              <div className="grid gap-4 sm:grid-cols-2">
                <TextField label="Generation model" value={form.generation_model ?? ''} onChange={(v) => set('generation_model', v)} />
                <TextField label="Embedding model" value={form.embedding_model ?? ''} onChange={(v) => set('embedding_model', v)} />
              </div>
              <div className="space-y-2 border-t border-slate-200 pt-3 dark:border-slate-800">
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Download / activate models
                </p>
                <p className="text-xs text-slate-400 dark:text-slate-500">
                  Downloads the model into Ollama (local, free). After it finishes, Save settings and
                  restart to use it. Changing the embedding model also requires re-indexing.
                </p>
                <PullControl label="Generation" model={form.generation_model ?? ''} onDone={refreshModels} />
                <PullControl label="Embedding" model={form.embedding_model ?? ''} onDone={refreshModels} />
              </div>
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

function PullControl({
  label,
  model,
  onDone,
}: {
  label: string;
  model: string;
  onDone: () => void;
}): JSX.Element {
  const [state, setState] = useState<'idle' | 'pulling' | 'done' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [percent, setPercent] = useState<number | null>(null);

  async function run(): Promise<void> {
    const name = model.trim();
    if (!name || state === 'pulling') return;
    setState('pulling');
    setMessage('starting…');
    setPercent(null);
    try {
      for await (const event of pullModel(name)) {
        if (event.type === 'progress') {
          setMessage(event.status || 'downloading…');
          setPercent(
            event.total && event.completed != null
              ? Math.round((event.completed / event.total) * 100)
              : null
          );
        } else if (event.type === 'error') {
          setState('error');
          setMessage(event.detail || 'download failed');
          return;
        } else {
          setState('done');
          setMessage('ready — save & restart to use');
          setPercent(100);
          onDone();
          return;
        }
      }
    } catch (error) {
      setState('error');
      setMessage(error instanceof ApiError ? error.detail ?? error.message : 'download failed');
    }
  }

  const tone =
    state === 'error'
      ? 'text-rose-600 dark:text-rose-400'
      : state === 'done'
        ? 'text-emerald-600 dark:text-emerald-400'
        : 'text-slate-500 dark:text-slate-400';

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => void run()}
          disabled={state === 'pulling' || !model.trim()}
          className="shrink-0 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-brand-400 hover:text-brand-600 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200 dark:hover:text-brand-300"
        >
          {state === 'pulling' ? 'Downloading…' : `Download ${label.toLowerCase()} model`}
        </button>
        <span className={`truncate text-xs ${tone}`}>
          {model.trim() || '—'}
          {message && ` · ${message}`}
          {percent != null && state === 'pulling' && ` ${percent}%`}
        </span>
      </div>
      {state === 'pulling' && (
        <div className="h-1 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
          {percent != null ? (
            <div
              className="h-full rounded-full bg-brand-500 transition-all"
              style={{ width: `${percent}%` }}
            />
          ) : (
            <div className="h-full w-full animate-pulse rounded-full bg-brand-400/60" />
          )}
        </div>
      )}
    </div>
  );
}
