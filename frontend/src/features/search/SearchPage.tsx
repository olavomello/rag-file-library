import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { ApiError } from '../../services/apiClient';
import { documentDownloadUrl } from '../../services/documents';
import { semanticSearch } from '../../services/search';
import type { SemanticSearchResponse } from '../../types';

export function SearchPage(): JSX.Element {
  const [query, setQuery] = useState('');

  const search = useMutation<SemanticSearchResponse, unknown, string>({
    mutationFn: (q: string) => semanticSearch(q),
  });

  function onSubmit(event: React.FormEvent): void {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed) search.mutate(trimmed);
  }

  const results = search.data?.results ?? [];

  return (
    <div>
      <header className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">Search</h2>
        <p className="text-sm text-slate-500">
          Semantic search across your indexed documents. No answer is generated — this finds
          the most relevant passages.
        </p>
      </header>

      <form onSubmit={onSubmit} className="mb-6 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What is our vacation policy?"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={search.isPending || !query.trim()}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {search.isPending ? 'Searching…' : 'Search'}
        </button>
      </form>

      {search.isError && (
        <p className="mb-4 text-sm text-rose-600">
          {search.error instanceof ApiError
            ? search.error.detail ?? search.error.message
            : 'Search failed.'}
        </p>
      )}

      {search.isSuccess && results.length === 0 && (
        <p className="text-sm text-slate-500">
          No matches. Make sure documents are uploaded and indexed.
        </p>
      )}

      <ul className="space-y-3">
        {results.map((result) => (
          <li
            key={result.chunk_id}
            className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-800">
                {result.document_name}
                {result.page_number != null && (
                  <span className="ml-2 text-xs font-normal text-slate-400">
                    page {result.page_number}
                  </span>
                )}
              </span>
              <a
                className="text-xs text-brand-600 hover:underline"
                href={documentDownloadUrl(result.document_id)}
              >
                Download
              </a>
            </div>
            <p className="text-sm text-slate-600">{result.excerpt}</p>
            <p className="mt-1 text-[11px] text-slate-400">distance {result.distance.toFixed(4)}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
