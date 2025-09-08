import React from 'react';

const TerminalWorkspace: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col p-12 overflow-hidden">
      <h1 className="text-2xl font-bold mb-6">Terminal</h1>
      <div className="bg-black rounded-lg flex-1 p-4 font-mono text-sm text-green-400 overflow-y-auto border border-[var(--border)]">
        <p>Nexus AI Terminal [Version 1.0.0]</p>
        <p>(c) 2025 Nexus Corp. All rights reserved.</p>
        <br />
        <p>
          <span className="text-blue-400">user@nexus</span>:
          <span className="text-purple-400">~</span>$
          <span className="animate-pulse">|</span>
        </p>
      </div>
    </div>
  );
};

export default TerminalWorkspace;
