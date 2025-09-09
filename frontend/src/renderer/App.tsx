import React, { useState } from 'react';
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

const AppContent: React.FC = () => {
  const [activeWorkspace, setActiveWorkspace] = useState('dashboard');
  const [isDiffModalOpen, setIsDiffModalOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

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
      case 'settings':
        return <SettingsWorkspace />;
      default:
        return <DashboardWorkspace />;
    }
  };

  return (
    <div className="h-screen flex flex-col app-container">
      {/* Header */}
      <Header 
        activeWorkspace={activeWorkspace} 
        onWorkspaceChange={setActiveWorkspace} 
        onOpenSettings={() => setIsSettingsOpen(true)}
      />
      
      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Workspace */}
        <main className="flex-1 overflow-auto main-content">
          {renderWorkspace()}
        </main>
      </div>
      
      {/* Modals */}
      <DiffModal 
        isOpen={isDiffModalOpen} 
        onClose={() => setIsDiffModalOpen(false)} 
      />
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
