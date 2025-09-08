import React from 'react';

interface DiffModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const DiffModal: React.FC<DiffModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    console.log('Patch confirmed and applied');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-[var(--bg-secondary)] w-11/12 max-w-4xl h-5/6 rounded-lg shadow-xl flex flex-col border border-[var(--border)]">
        <div className="p-4 border-b border-[var(--border)] flex justify-between items-center">
          <h2 className="text-xl font-bold">Patch Review</h2>
          <button 
            onClick={onClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-2xl font-bold transition-colors"
          >
            ×
          </button>
        </div>
        <div className="p-6 flex-1 overflow-y-auto">
          <div className="diff-view font-mono text-sm">
            <div className="diff-remove bg-[var(--error)] bg-opacity-20 px-2 py-1 rounded mb-1">
              - console.log("Old implementation");
            </div>
            <div className="diff-add bg-[var(--success)] bg-opacity-20 px-2 py-1 rounded mb-1">
              + console.log("New, improved implementation");
            </div>
            <div className="px-2 py-1">  function existingFunction() {'{'}</div>
            <div className="px-2 py-1">    // no changes here</div>
            <div className="px-2 py-1">  {'}'}</div>
          </div>
        </div>
        <div className="p-4 border-t border-[var(--border)] flex justify-end gap-2">
          <button 
            onClick={onClose}
            className="bg-[var(--bg-tertiary)] hover:bg-[var(--border)] text-[var(--text-primary)] font-bold py-2 px-4 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleConfirm}
            className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white font-bold py-2 px-4 rounded-lg transition-colors"
          >
            Confirm & Apply
          </button>
        </div>
      </div>
    </div>
  );
};

export default DiffModal;
