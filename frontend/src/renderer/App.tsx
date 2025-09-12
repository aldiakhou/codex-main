import React, { Suspense, useCallback, useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { BackendProvider } from './contexts/BackendContext';
import Header from './components/Header';
import DiffModal from './components/DiffModal';
import SettingsModal from './components/SettingsModal';
import ExecApprovalModal from './components/ExecApprovalModal';
import PatchApprovalModal from './components/PatchApprovalModal';
import { useWorkspaceManager } from './hooks/useWorkspaceManager';

// Lazy-loaded Workspace Components
const DashboardWorkspace = React.lazy(() => import('./components/workspaces/DashboardWorkspace'));
const AgentsWorkspace = React.lazy(() => import('./components/workspaces/AgentsWorkspace'));
const CodeWorkspace = React.lazy(() => import('./components/workspaces/CodeWorkspace'));
const FilesWorkspace = React.lazy(() => import('./components/workspaces/FilesWorkspace'));
const PlannerWorkspace = React.lazy(() => import('./components/workspaces/PlannerWorkspace'));
const TerminalWorkspace = React.lazy(() => import('./components/workspaces/TerminalWorkspace'));
const ToolsWorkspace = React.lazy(() => import('./components/workspaces/ToolsWorkspace'));
const ChatWorkspace = React.lazy(() => import('./components/workspaces/ChatWorkspace'));
const SettingsWorkspace = React.lazy(() => import('./components/workspaces/SettingsWorkspace'));
const GraphWorkspace = React.lazy(() => import('./components/workspaces/GraphWorkspace'));

const AppContent: React.FC = () => {
  const { activeWorkspace, setActiveWorkspace } = useWorkspaceManager('dashboard');
  const [isDiffModalOpen, setIsDiffModalOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleWorkspaceChange: (id: string) => void = useCallback(
    (id: string) => {
      setActiveWorkspace(id as any);
    },
    [setActiveWorkspace]
  );

  const renderWorkspace = () => {
    switch (activeWorkspace) {
      case 'chat':
        return <ChatWorkspace />;
      case 'dashboard':
        return <DashboardWorkspace />;
      case 'agents':
        return <AgentsWorkspace />;
      case 'code':
        return <CodeWorkspace onShowDiffModal={() => setIsDiffModalOpen(true)} />;
      case 'files':
        return <FilesWorkspace />;
      case 'planner':
        return <PlannerWorkspace />;
      case 'terminal':
        return <TerminalWorkspace />;
      case 'tools':
        return <ToolsWorkspace />;
      case 'graph':
        return <GraphWorkspace />;
      case 'settings':
        return <SettingsWorkspace />;
      default:
        return <DashboardWorkspace />;
    }
  };

  return (
    <div className="h-screen flex flex-col app-container">
  <Header activeWorkspace={activeWorkspace} onWorkspaceChange={handleWorkspaceChange} />
      <div className="flex-1 flex overflow-hidden">
        <main className="flex-1 overflow-hidden main-content">
          <Suspense fallback={<div className="p-6 text-[var(--text-secondary)]">Loading workspace…</div>}>
            {renderWorkspace()}
          </Suspense>
        </main>
      </div>
      <DiffModal isOpen={isDiffModalOpen} onClose={() => setIsDiffModalOpen(false)} />
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <ExecApprovalModal />
      <PatchApprovalModal />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BackendProvider>
        <AppContent />
      </BackendProvider>
    </ThemeProvider>
  );
};

export default App;

