import React, { Suspense, useCallback, useState, useEffect } from 'react';
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

  const handleWorkspaceChange = useCallback((id: string) => {
    // Only update if id is one of the known workspace ids
    const allowed = ['chat','dashboard','agents','code','files','planner','terminal','tools','graph','settings'] as const;
    if ((allowed as readonly string[]).includes(id)) {
      setActiveWorkspace(id as typeof allowed[number]);
    }
  }, [setActiveWorkspace]);

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

  // Toggle global mesh background off for Agents workspace to reduce visual noise.
  useEffect(() => {
    const body = document.body;
    if (activeWorkspace === 'agents') {
      body.classList.add('no-mesh-bg');
    } else {
      body.classList.remove('no-mesh-bg');
    }
    return () => body.classList.remove('no-mesh-bg');
  }, [activeWorkspace]);

  // Apply persisted UI variables on app load
  useEffect(() => {
    try {
      const root = document.documentElement;
      const base = parseFloat(localStorage.getItem('ui.fontSizeBase') || '13');
      if (!isNaN(base)) root.style.setProperty('--font-size-base', `${base}px`);
      const p = localStorage.getItem('ui.primaryColor');
      if (p) root.style.setProperty('--primary-color', p);
      const s = localStorage.getItem('ui.secondaryColor');
      if (s) root.style.setProperty('--secondary-color', s);
      const uiFont = localStorage.getItem('ui.fontFamily');
      if (uiFont) {
        if (uiFont === 'inter') root.style.setProperty('--font-ui', "'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif");
        else if (uiFont === 'jetbrains') root.style.setProperty('--font-ui', "'JetBrains Mono', 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif");
        else root.style.setProperty('--font-ui', "'Cascadia Code', 'Cascadia Mono', 'Segoe UI Variable', 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif");
      }
      const monoFont = localStorage.getItem('ui.fontMono');
      if (monoFont) {
        if (monoFont === 'jetbrains') root.style.setProperty('--font-mono', "'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, monospace");
        else root.style.setProperty('--font-mono', "'Cascadia Code', 'Cascadia Mono', 'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, monospace");
      }
      const compact = localStorage.getItem('ui.compact') === 'true';
      if (compact) document.body.classList.add('compact');
    } catch {}
  }, []);

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
