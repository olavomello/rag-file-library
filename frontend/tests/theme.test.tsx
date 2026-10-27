import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { ThemeProvider, useTheme } from '../src/app/theme';

function Probe(): JSX.Element {
  const { preference, setPreference } = useTheme();
  return (
    <div>
      <span data-testid="pref">{preference}</span>
      <button onClick={() => setPreference('dark')}>dark</button>
      <button onClick={() => setPreference('light')}>light</button>
    </div>
  );
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove('dark');
});

describe('theme', () => {
  it('defaults to system and applies/persists an explicit choice', () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );
    expect(screen.getByTestId('pref').textContent).toBe('system');

    act(() => screen.getByText('dark').click());
    expect(screen.getByTestId('pref').textContent).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(localStorage.getItem('privaterag.theme')).toBe('dark');

    act(() => screen.getByText('light').click());
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(localStorage.getItem('privaterag.theme')).toBe('light');
  });
});
