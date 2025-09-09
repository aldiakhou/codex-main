import React, { useEffect, useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { BackendProvider } from './contexts/BackendContext';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import DiffModal from './components/DiffModal';
import SettingsModal from './components/SettingsModal';
import ExecApprovalModal from './components/ExecApprovalModal';
import PatchApprovalModal from './components/PatchApprovalModal';
import ChatMessages from './components/ChatMessages';

// Workspace Components
import DashboardWorkspace from './components/workspaces/DashboardWorkspace';
import AgentsWorkspace from './components/workspaces/AgentsWorkspace';
import CodeWorkspace from './components/workspaces/CodeWorkspace';
import FilesWorkspace from './components/workspaces/FilesWorkspace';
import PlannerWorkspace from './components/workspaces/PlannerWorkspace';
import TerminalWorkspace from './components/workspaces/TerminalWorkspace';
import ToolsWorkspace from './components/workspaces/ToolsWorkspace';
import ChatWorkspace from './components/workspaces/ChatWorkspace';
import SettingsWorkspace from './components/workspaces/SettingsWorkspace';
import GraphWorkspace from './components/workspaces/GraphWorkspace';

const AppContent: React.FC = () => {
  const [activeWorkspace, setActiveWorkspace] = useState('dashboard');
  const [isDiffModalOpen, setIsDiffModalOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    const last = window.localStorage.getItem('lastWorkspace');
    if (last) setActiveWorkspace(last);
  }, []);
  useEffect(() => {
    window.localStorage.setItem('lastWorkspace', activeWorkspace);
  }, [activeWorkspace]);
  useEffect(() => {
    const handler = () => setActiveWorkspace('files');
    window.addEventListener('open-file-in-files', handler);
    return () => window.removeEventListener('open-file-in-files', handler);
  }, []);

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
      <Header
        activeWorkspace={activeWorkspace}
        onWorkspaceChange={setActiveWorkspace}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />
      <div className="flex-1 flex overflow-hidden">
        <main className="flex-1 overflow-hidden main-content">
          {renderWorkspace()}
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

