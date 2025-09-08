import React from 'react';

const DashboardWorkspace: React.FC = () => {
  return (
    <div className="flex-1 p-12 overflow-y-auto bg-animated-gradient">
      <h1 className="text-3xl font-bold mb-2">Welcome back, John!</h1>
      <p className="text-[var(--text-secondary)] mb-10">
        Here's a look at your day. Let's make it productive.
      </p>
      
      {/* Dashboard Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="workspace-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Active Agents</h3>
            <div className="w-10 h-10 bg-accent-gradient rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <p className="text-2xl font-bold text-[var(--accent)]">3</p>
          <p className="text-sm text-[var(--text-secondary)]">Currently running</p>
        </div>

        <div className="workspace-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Tasks Completed</h3>
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <p className="text-2xl font-bold text-[var(--success)]">47</p>
          <p className="text-sm text-[var(--text-secondary)]">This week</p>
        </div>

        <div className="workspace-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Processing Time</h3>
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-2xl font-bold text-blue-400">2.3s</p>
          <p className="text-sm text-[var(--text-secondary)]">Average response</p>
        </div>

        <div className="workspace-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Efficiency</h3>
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <p className="text-2xl font-bold text-purple-400">94%</p>
          <p className="text-sm text-[var(--text-secondary)]">Success rate</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="workspace-card">
        <h3 className="text-xl font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-3">
          <div className="flex items-center p-3 bg-[var(--bg-tertiary)] rounded-lg">
            <div className="w-2 h-2 bg-[var(--success)] rounded-full mr-3"></div>
            <div className="flex-1">
              <p className="font-medium">Search Agent completed market analysis</p>
              <p className="text-sm text-[var(--text-secondary)]">2 minutes ago</p>
            </div>
          </div>
          <div className="flex items-center p-3 bg-[var(--bg-tertiary)] rounded-lg">
            <div className="w-2 h-2 bg-[var(--accent)] rounded-full mr-3"></div>
            <div className="flex-1">
              <p className="font-medium">Developer Agent updated repository</p>
              <p className="text-sm text-[var(--text-secondary)]">5 minutes ago</p>
            </div>
          </div>
          <div className="flex items-center p-3 bg-[var(--bg-tertiary)] rounded-lg">
            <div className="w-2 h-2 bg-[var(--warning)] rounded-full mr-3"></div>
            <div className="flex-1">
              <p className="font-medium">Document Agent processing reports</p>
              <p className="text-sm text-[var(--text-secondary)]">8 minutes ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardWorkspace;
