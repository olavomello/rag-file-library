import { Route, Routes } from 'react-router-dom';

import { Sidebar } from '../components/Sidebar';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { DocumentsPage } from '../features/documents/DocumentsPage';
import { SearchPage } from '../features/search/SearchPage';
import { ChatPage } from '../features/chat/ChatPage';
import { SettingsPage } from '../features/settings/SettingsPage';

export default function App(): JSX.Element {
  return (
    <div className="flex h-full">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-8 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
