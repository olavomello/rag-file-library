import { useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { DocumentStatusBadge } from '../../components/DocumentStatusBadge';
import { ApiError } from '../../services/apiClient';
import {
  deleteDocument,
  documentDownloadUrl,
  getDocumentContent,
  listDocuments,
  reindexDocument,
  uploadDocument,
} from '../../services/documents';
import { listIndexingJobs } from '../../services/indexing';
import { formatBytes, formatDate } from '../../lib/format';
import type { DocumentView, IndexingJobView } from '../../types';

const ACTIVE = new Set(['pending', 'processing', 'deleting']);

/** Map each document to the progress (0..1) of its most recent indexing job. */
function latestProgressByDocument(jobs: IndexingJobView[]): Map<string, number> {
  const latest = new Map<string, IndexingJobView>();
  for (const job of jobs) {
    const current = latest.get(job.document_id);
    if (!current || (job.started_at ?? '') >= (current.started_at ?? '')) {
      latest.set(job.document_id, job);
    }
  }
  const progress = new Map<string, number>();
  for (const [documentId, job] of latest) progress.set(documentId, job.progress);
  return progress;
}

export function DocumentsPage(): JSX.Element {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ name: string; content: string } | null>(null);
  const [uploads, setUploads] = useState<Record<string, number>>({});

  const documents = useQuery({
    queryKey: ['documents'],
    queryFn: () => listDocuments(),
    refetchInterval: (query) =>
      query.state.data?.items.some((d) => ACTIVE.has(d.status)) ? 1500 : false,
  });

  const hasActive = documents.data?.items.some((d) => ACTIVE.has(d.status)) ?? false;

  const jobs = useQuery({
    queryKey: ['indexing', 'jobs'],
    queryFn: () => listIndexingJobs(),
    refetchInterval: () => (hasActive ? 1500 : false),
    enabled: hasActive,
  });

  const progressByDoc = latestProgressByDocument(jobs.data?.items ?? []);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['documents'] });

  const upload = useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (percent: number) => void }) =>
      uploadDocument(file, onProgress),
    onSuccess: (result) => {
      setNotice(
        result.is_duplicate
          ? `"${result.document.original_name}" is already in the library (duplicate).`
          : `Uploaded "${result.document.original_name}".`
      );
      invalidate();
    },
    onError: (error) => {
      setNotice(error instanceof ApiError ? error.detail ?? error.message : 'Upload failed.');
    },
  });

  const remove = useMutation({ mutationFn: deleteDocument, onSuccess: invalidate });
  const reindex = useMutation({ mutationFn: reindexDocument, onSuccess: invalidate });

  function clearUpload(name: string): void {
    setUploads((prev) => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
  }

  async function handleFiles(files: FileList | null): Promise<void> {
    if (!files) return;
    for (const file of Array.from(files)) {
      setUploads((prev) => ({ ...prev, [file.name]: 0 }));
      await upload
        .mutateAsync({
          file,
          onProgress: (percent) => setUploads((prev) => ({ ...prev, [file.name]: percent })),
        })
        .catch(() => undefined);
      clearUpload(file.name);
    }
  }

  async function openPreview(doc: DocumentView): Promise<void> {
    const content = await getDocumentContent(doc.id);
    setPreview({ name: doc.original_name, content: content.content });
  }

  function onDelete(doc: DocumentView): void {
    if (window.confirm(`Delete "${doc.original_name}"? This removes it and its index.`)) {
      remove.mutate(doc.id);
    }
  }

  return (
    <div>
      <header className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Documents</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Upload, preview, reindex, and manage your documents.
        </p>
      </header>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          void handleFiles(e.dataTransfer.files);
        }}
        className={`mb-4 flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
          dragging
            ? 'border-brand-500 bg-brand-50 dark:bg-brand-600/10'
            : 'border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900'
        }`}
      >
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Drag &amp; drop files here, or{' '}
          <button
            type="button"
            className="font-medium text-brand-600 hover:underline dark:text-brand-300"
            onClick={() => inputRef.current?.click()}
          >
            browse
          </button>
        </p>
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
          PDF, DOCX, TXT, Markdown — plus images (PNG, JPG, TIFF, BMP, WEBP) when OCR is enabled
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
          className="hidden"
          onChange={(e) => void handleFiles(e.target.files)}
        />
      </div>

      {Object.keys(uploads).length > 0 && (
        <div className="mb-4 space-y-2 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
          {Object.entries(uploads).map(([name, percent]) => (
            <div key={name}>
              <div className="mb-1 flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                <span className="truncate pr-2">{name}</span>
                <span className="tabular-nums text-slate-400 dark:text-slate-500">{percent}%</span>
              </div>
              <div
                className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
                role="progressbar"
                aria-label={`Uploading ${name}`}
                aria-valuenow={percent}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <div
                  className="h-full rounded-full bg-brand-500 transition-all"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {notice && (
        <div className="mb-4 flex items-center justify-between rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          <span>{notice}</span>
          <button
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            onClick={() => setNotice(null)}
          >
            ✕
          </button>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-400 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Size</th>
              <th className="px-4 py-3">Uploaded</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Chunks</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-400 dark:text-slate-500">
                  No documents yet. Upload one above to get started.
                </td>
              </tr>
            )}
            {documents.data?.items.map((doc) => (
              <tr key={doc.id} className="border-b border-slate-100 last:border-0 dark:border-slate-800">
                <td className="px-4 py-3">
                  <span className="font-medium text-slate-800 dark:text-slate-200">{doc.original_name}</span>
                  {doc.error_message && <p className="text-xs text-rose-500">{doc.error_message}</p>}
                </td>
                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{formatBytes(doc.size_bytes)}</td>
                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{formatDate(doc.created_at)}</td>
                <td className="px-4 py-3">
                  <DocumentStatusBadge status={doc.status} />
                  {(doc.status === 'processing' || doc.status === 'pending') && (
                    <IndexingProgress progress={progressByDoc.get(doc.id)} />
                  )}
                </td>
                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{doc.chunk_count}</td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-3 text-xs">
                    <button
                      className="text-slate-600 hover:text-brand-600 dark:text-slate-300 dark:hover:text-brand-300"
                      onClick={() => void openPreview(doc)}
                    >
                      Preview
                    </button>
                    <a
                      className="text-slate-600 hover:text-brand-600 dark:text-slate-300 dark:hover:text-brand-300"
                      href={documentDownloadUrl(doc.id)}
                    >
                      Download
                    </a>
                    <button
                      className="text-slate-600 hover:text-brand-600 dark:text-slate-300 dark:hover:text-brand-300"
                      onClick={() => reindex.mutate(doc.id)}
                    >
                      Reindex
                    </button>
                    <button
                      className="text-rose-500 hover:text-rose-700 dark:hover:text-rose-400"
                      onClick={() => onDelete(doc)}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {preview && (
        <div
          className="fixed inset-0 z-30 flex items-center justify-center bg-black/40 p-4"
          onClick={() => setPreview(null)}
        >
          <div
            className="flex max-h-[80vh] w-full max-w-2xl flex-col rounded-xl bg-white shadow-xl dark:bg-slate-900"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3 dark:border-slate-800">
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{preview.name}</h3>
              <button
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                onClick={() => setPreview(null)}
              >
                ✕
              </button>
            </div>
            <pre className="overflow-auto whitespace-pre-wrap px-5 py-4 text-sm text-slate-700 dark:text-slate-300">
              {preview.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function IndexingProgress({ progress }: { progress: number | undefined }): JSX.Element {
  const hasProgress = typeof progress === 'number' && progress > 0;
  const percent = hasProgress ? Math.round(Math.min(Math.max(progress, 0), 1) * 100) : 0;
  return (
    <div
      className="mt-1.5 h-1 w-24 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
      role="progressbar"
      aria-label="Indexing progress"
      aria-valuenow={hasProgress ? percent : undefined}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      {hasProgress ? (
        <div className="h-full rounded-full bg-brand-500 transition-all" style={{ width: `${percent}%` }} />
      ) : (
        <div className="h-full w-full animate-pulse rounded-full bg-brand-400/60" />
      )}
    </div>
  );
}
