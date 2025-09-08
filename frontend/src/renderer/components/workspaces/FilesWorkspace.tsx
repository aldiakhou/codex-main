import React from 'react';

const FilesWorkspace: React.FC = () => {
  return (
    <div className="flex-1 flex p-12 gap-8 overflow-hidden">
      <div className="w-1/3 bg-[var(--bg-secondary)] rounded-lg p-6 overflow-y-auto border border-[var(--border)]">
        <h2 className="text-lg font-semibold mb-4">Project Files</h2>
        <ul className="space-y-1">
          <li className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer">- /src</li>
          <li className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer">- /components</li>
          <li className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer">- app.js</li>
        </ul>
      </div>
      <div className="w-2/3 bg-[var(--bg-secondary)] rounded-lg p-6 border border-[var(--border)]">
        <h2 className="text-lg font-semibold mb-4">Preview: app.js</h2>
        <div className="bg-[var(--bg-tertiary)] p-4 rounded h-5/6 font-mono text-sm border border-[var(--border)]">
          <span className="text-[var(--text-primary)]">console.log("Hello, Nexus AI!");</span>
        </div>
      </div>
    </div>
  );
};

export default FilesWorkspace;
