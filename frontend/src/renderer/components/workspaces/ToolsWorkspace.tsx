import React from 'react';
import { useBackend } from '../../contexts/BackendContext';

const ToolsWorkspace: React.FC = () => {
  const { status, logs } = useBackend();
  return (
    <div className="flex-1 p-12 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Tools & MCP Servers</h1>
        <div className="text-sm text-[var(--text-secondary)]">Backend: {status}</div>
      </div>
      <p className="text-[var(--text-secondary)] mb-8">
        Connect and manage your AI tools and Model Context Protocol servers.
      </p>
      <button className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white font-bold py-2 px-4 rounded-lg mb-8 transition-colors">
        + Connect New MCP Server
      </button>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div className="bg-[var(--bg-secondary)] p-6 rounded-lg border border-[var(--border)]">
          <h3 className="text-lg font-bold">Local Filesystem</h3>
          <p className="text-sm text-[var(--text-secondary)] mb-3">mcp://localhost:8000</p>
          <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-[var(--success)] bg-green-200">
            Connected
          </span>
        </div>
        <div className="bg-[var(--bg-secondary)] p-6 rounded-lg border border-[var(--border)]">
          <h3 className="text-lg font-bold">GitHub Repository</h3>
          <p className="text-sm text-[var(--text-secondary)] mb-3">mcp://github-server/project-x</p>
          <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-[var(--success)] bg-green-200">
            Connected
          </span>
        </div>
        <div className="bg-[var(--bg-secondary)] p-6 rounded-lg border border-[var(--border)]">
          <h3 className="text-lg font-bold">Corporate Wiki</h3>
          <p className="text-sm text-[var(--text-secondary)] mb-3">mcp://internal.wiki.nexus</p>
          <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-[var(--warning)] bg-yellow-200">
            Pending
          </span>
        </div>
      </div>
      <div className="mt-8">
        <h2 className="text-lg font-semibold mb-2">Recent Backend Activity</h2>
        <div className="border border-[var(--border)] rounded bg-[var(--bg-secondary)] p-2 max-h-48 overflow-auto font-mono text-xs">
          {logs.slice(-100).map((l, i) => (
            <div key={i} className="whitespace-pre-wrap">{l}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ToolsWorkspace;
