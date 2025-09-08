import React from 'react';

const PlannerWorkspace: React.FC = () => {
  return (
    <div className="flex-1 p-12 overflow-y-auto">
      <h1 className="text-2xl font-bold mb-6">Task Planner</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-[var(--bg-secondary)] p-5 rounded-lg border border-[var(--border)]">
          <h3 className="font-bold mb-4">To Do</h3>
          <div className="space-y-3">
            <div className="bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--border)] transition-colors cursor-pointer">
              Implement login feature
            </div>
            <div className="bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--border)] transition-colors cursor-pointer">
              Design database schema
            </div>
          </div>
        </div>
        <div className="bg-[var(--bg-secondary)] p-5 rounded-lg border border-[var(--border)]">
          <h3 className="font-bold mb-4">In Progress</h3>
          <div className="bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--border)] transition-colors cursor-pointer">
            Develop UI components
          </div>
        </div>
        <div className="bg-[var(--bg-secondary)] p-5 rounded-lg border border-[var(--border)]">
          <h3 className="font-bold mb-4">Done</h3>
          <div className="text-[var(--text-secondary)] text-sm text-center py-8">
            No completed tasks yet
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlannerWorkspace;
