import React from 'react';

interface CodeWorkspaceProps {
  onShowDiffModal: () => void;
}

const CodeWorkspace: React.FC<CodeWorkspaceProps> = ({ onShowDiffModal }) => {
  return (
    <div className="flex-1 flex flex-col p-12 overflow-hidden">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Code Editor</h1>
        <div>
          <button aria-label="Save file" className="bg-[var(--bg-tertiary)] hover:bg-[var(--border)] text-[var(--text-primary)] font-bold py-2 px-4 rounded-lg transition-colors">
            Save
          </button>
          <button 
            onClick={onShowDiffModal}
            aria-label="Open patch review"
            className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white font-bold py-2 px-4 rounded-lg ml-2 transition-colors"
          >
            Apply Patch
          </button>
        </div>
      </div>
      <div className="bg-[var(--bg-secondary)] rounded-lg flex-1 border border-[var(--border)]">
        <textarea 
          className="w-full h-full bg-transparent text-[var(--text-primary)] p-4 font-mono text-sm resize-none focus:outline-none" 
          placeholder="Write your code here..."
        />
        <div className="p-4 text-[var(--text-tertiary)] text-sm border-t border-[var(--border)]">
          No file open. Open a file from the Files workspace to start editing.
        </div>
      </div>
    </div>
  );
};

export default CodeWorkspace;
