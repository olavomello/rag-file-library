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
import { formatBytes, formatDate } from '../../lib/format';
import type { DocumentView } from '../../types';

const ACTIVE = new Set(['pending', 'processing', 'deleting']);

export function DocumentsPage(): JSX.Element {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ name: string; content: string } | null>(null);

  const documents = useQuery({
    queryKey: ['documents'],
    queryFn: () => listDocuments(),
    refetchInterval: (query) =>
      query.state.data?.items.some((d) => ACTIVE.has(d.status)) ? 1500 : false,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['documents'] });

  const upload = useMutation({
    mutationFn: uploadDocument,
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

  const remove = useMutation({
    mutationFn: deleteDocument,
    onSuccess: invalidate,
  });

  const reindex = useMutation({
    mutationFn: reindexDocument,
    onSuccess: invalidate,
  });

  async function handleFiles(files: FileList | null): Promise<void> {
    if (!files) return;
    for (const file of Array.from(files)) {
      await upload.mutateAsync(file).catch(() => undefined);
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
        <h2 className="text-2xl font-semibold text-slate-900">Documents</h2>
        <p className="text-sm text-slate-500">Upload, preview, reindex, and manage your documents.</p>
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
          dragging ? 'border-brand-500 bg-brand-50' : 'border-slate-300 bg-white'
        }`}
      >
        <p className="text-sm text-slate-600">
          Drag &amp; drop files here, or{' '}
          <button
            type="button"
            className="font-medium text-brand-600 hover:underline"
            onClick={() => inputRef.current?.click()}
          >
            browse
          </button>
        </p>
        <p className="mt-1 text-xs text-slate-400">PDF, DOCX, TXT, Markdown</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={(e) => void handleFiles(e.target.files)}
        />
      </div>

      {notice && (
        <div className="mb-4 flex items-center justify-between rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">
          <span>{notice}</span>
          <button className="text-slate-400 hover:text-slate-600" onClick={() => setNotice(null)}>
            ✕
          </button>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-400">
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
                <td colSpan={6} className="px-4 py-10 text-center text-slate-400">
                  No documents yet. Upload one above to get started.
                </td>
              </tr>
            )}
            {documents.data?.items.map((doc) => (
              <tr key={doc.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-3">
                  <span className="font-medium text-slate-800">{doc.original_name}</span>
                  {doc.error_message && (
                    <p className="text-xs text-rose-500">{doc.error_message}</p>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-500">{formatBytes(doc.size_bytes)}</td>
                <td className="px-4 py-3 text-slate-500">{formatDate(doc.created_at)}</td>
                <td className="px-4 py-3">
                  <DocumentStatusBadge status={doc.status} />
                </td>
                <td className="px-4 py-3 text-slate-500">{doc.chunk_count}</td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-3 text-xs">
                    <button className="text-slate-600 hover:text-brand-600" onClick={() => void openPreview(doc)}>
                      Preview
                    </button>
                    <a className="text-slate-600 hover:text-brand-600" href={documentDownloadUrl(doc.id)}>
                      Download
                    </a>
                    <button className="text-slate-600 hover:text-brand-600" onClick={() => reindex.mutate(doc.id)}>
                      Reindex
                    </button>
                    <button className="text-rose-500 hover:text-rose-700" onClick={() => onDelete(doc)}>
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
          className="fixed inset-0 z-10 flex items-center justify-center bg-black/30 p-4"
          onClick={() => setPreview(null)}
        >
          <div
            className="flex max-h-[80vh] w-full max-w-2xl flex-col rounded-xl bg-white shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
              <h3 className="text-sm font-semibold text-slate-800">{preview.name}</h3>
              <button className="text-slate-400 hover:text-slate-600" onClick={() => setPreview(null)}>
                ✕
              </button>
            </div>
            <pre className="overflow-auto whitespace-pre-wrap px-5 py-4 text-sm text-slate-700">
              {preview.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
