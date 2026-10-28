import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '../src/app/theme';
import { SettingsPage } from '../src/features/settings/SettingsPage';
import type { ModelsStatus, SettingsView } from '../src/types';

const settings: SettingsView = {
  app_name: 'Private RAG',
  app_env: 'test',
  generation_model: 'qwen3:0.6b',
  embedding_model: 'embeddinggemma',
  temperature: 0.2,
  max_output_tokens: 512,
  context_window: 4096,
  chunk_size: 500,
  chunk_overlap: 75,
  search_top_k: 5,
  rag_max_context_chunks: 6,
  rag_max_context_chars: 8000,
  max_upload_size_mb: 25,
  indexing_concurrency: 1,
  generation_concurrency: 1,
  ocr_enabled: true,
};

const models: ModelsStatus = {
  generation_model: 'qwen3:0.6b',
  embedding_model: 'embeddinggemma',
  ollama_available: true,
  generation_available: true,
  embedding_available: true,
};

vi.mock('../src/services/dashboard', () => ({
  fetchSettings: () => Promise.resolve(settings),
  fetchModelsStatus: () => Promise.resolve(models),
  updateSettings: vi.fn(),
}));

function renderPage(): void {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ThemeProvider>
        <SettingsPage />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

describe('SettingsPage', () => {
  it('renders the OCR toggle reflecting the loaded setting', async () => {
    renderPage();
    const checkbox = await screen.findByRole('checkbox', {
      name: /Enable OCR \(scanned PDFs & images\)/i,
    });
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).toBeChecked();
  });
});
