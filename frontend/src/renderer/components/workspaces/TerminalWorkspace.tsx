import React, { useMemo } from 'react';
import { useBackend } from '../../contexts/BackendContext';

const TerminalWorkspace: React.FC = () => {
  const { status, logs } = useBackend();
  const color = useMemo(() => {
    switch (status) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  }, [status]);

  return (
    <div className="flex-1 flex flex-col p-12 overflow-hidden">
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-2xl font-bold">Terminal</h1>
        <div className="flex items-center gap-2 text-sm">
          <span className={`inline-block w-2.5 h-2.5 rounded-full ${color}`} />
          <span className="text-[var(--text-secondary)]">{status}</span>
        </div>
      </div>
      <div className="bg-black rounded-lg flex-1 p-4 font-mono text-sm text-green-400 overflow-y-auto border border-[var(--border)]">
        {(logs.length ? logs : [
          'Nexus AI Terminal [Version 1.0.0]',
          '(c) 2025 Nexus Corp. All rights reserved.',
          '',
        ]).slice(-500).map((l, i) => (
          <div key={i} className="whitespace-pre-wrap">{l}</div>
        ))}
      </div>
    </div>
  );
};

export default TerminalWorkspace;
