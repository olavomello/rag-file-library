import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DocumentStatusBadge } from '../src/components/DocumentStatusBadge';
import { SearchPage } from '../src/features/search/SearchPage';

function renderWithClient(ui: JSX.Element): void {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('DocumentStatusBadge', () => {
  it('renders the status label', () => {
    render(<DocumentStatusBadge status="indexed" />);
    expect(screen.getByText('indexed')).toBeInTheDocument();
  });
});

describe('SearchPage', () => {
  it('renders the search form', () => {
    renderWithClient(<SearchPage />);
    expect(screen.getByRole('heading', { name: 'Search' })).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText('e.g. What is our vacation policy?')
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument();
  });
});
