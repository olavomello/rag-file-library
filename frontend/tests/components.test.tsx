import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { Sidebar } from '../src/components/Sidebar';
import { StatusBadge } from '../src/components/StatusBadge';

describe('Sidebar', () => {
  it('renders all primary navigation items', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    for (const label of ['Dashboard', 'Documents', 'Search', 'AI Chat', 'Settings']) {
      expect(screen.getByRole('link', { name: label })).toBeInTheDocument();
    }
  });
});

describe('StatusBadge', () => {
  it('shows the correct label for each status', () => {
    const { rerender } = render(<StatusBadge status="ok" />);
    expect(screen.getByText('Online')).toBeInTheDocument();

    rerender(<StatusBadge status="unavailable" />);
    expect(screen.getByText('Unavailable')).toBeInTheDocument();

    rerender(<StatusBadge status="loading" />);
    expect(screen.getByText('Checking…')).toBeInTheDocument();
  });
});
