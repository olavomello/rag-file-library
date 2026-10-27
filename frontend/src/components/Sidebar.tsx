import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/documents', label: 'Documents', end: false },
  { to: '/search', label: 'Search', end: false },
  { to: '/chat', label: 'AI Chat', end: false },
  { to: '/settings', label: 'Settings', end: false },
];

export function Sidebar(): JSX.Element {
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="px-6 py-5">
        <h1 className="text-lg font-semibold text-slate-900">Private RAG</h1>
        <p className="text-xs text-slate-400">Local document intelligence</p>
      </div>
      <nav className="flex flex-col gap-1 px-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
