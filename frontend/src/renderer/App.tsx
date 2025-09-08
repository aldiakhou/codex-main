import React, { useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import DiffModal from './components/DiffModal';

// Workspace Components
import DashboardWorkspace from './components/workspaces/DashboardWorkspace';
import AgentsWorkspace from './components/workspaces/AgentsWorkspace';
import CodeWorkspace from './components/workspaces/CodeWorkspace';
import FilesWorkspace from './components/workspaces/FilesWorkspace';
import PlannerWorkspace from './components/workspaces/PlannerWorkspace';
import TerminalWorkspace from './components/workspaces/TerminalWorkspace';
import ToolsWorkspace from './components/workspaces/ToolsWorkspace';

const AppContent: React.FC = () => {
  const [activeWorkspace, setActiveWorkspace] = useState('dashboard');
  const [isDiffModalOpen, setIsDiffModalOpen] = useState(false);

  const renderWorkspace = () => {
    switch (activeWorkspace) {
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
      />
      
      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Workspace */}
        <main className="flex-1 overflow-auto main-content">
          {renderWorkspace()}
        </main>
      </div>
      
      {/* Chat Interface */}
      <ChatInterface />
      
      {/* Diff Modal */}
      <DiffModal 
        isOpen={isDiffModalOpen} 
        onClose={() => setIsDiffModalOpen(false)} 
      />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
};

export default App;
