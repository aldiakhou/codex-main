import React, { useRef, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { IconBolt, IconCode, IconFileText, IconActivity, IconPlus, IconSettings, IconList, IconRefresh, IconPlayerPlay } from '@tabler/icons-react';
import { useBackend } from '../../contexts/BackendContext';

interface Agent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'processing';
  avatar: string;
  progress: number;
  tasksCompleted: number;
  totalTasks: number;
  lastActivity: string;
  icon: React.ReactNode;
  tags: string[];
}

const agents: Agent[] = [
  {
    id: 'search',
    name: 'Search Agent',
    status: 'active',
    avatar: 'S',
    progress: 75,
    tasksCompleted: 8,
    totalTasks: 12,
    lastActivity: '2 min ago',
    icon: <IconBolt size={20} />,
    tags: ['#eva_search', '#terminal']
  },
  {
    id: 'developer',
    name: 'Developer Agent',
    status: 'processing',
    avatar: 'D',
    progress: 45,
    tasksCompleted: 3,
    totalTasks: 8,
    lastActivity: '1 min ago',
    icon: <IconCode size={20} />,
    tags: ['#terminal']
  },
  {
    id: 'document',
    name: 'Document Agent',
    status: 'idle',
    avatar: 'Doc',
    progress: 90,
    tasksCompleted: 15,
    totalTasks: 16,
    lastActivity: '5 min ago',
    icon: <IconFileText size={20} />,
    tags: ['#google_workspace', '#terminal']
  }
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0
  }
};

const AgentsWorkspace: React.FC = () => {
  const { userTurn } = useBackend();
  const workforceContainerRef = useRef<HTMLDivElement>(null);
  const [scrollState, setScrollState] = useState({ isAtStart: true, isAtEnd: true });
  const [isCreatingAgent, setIsCreatingAgent] = useState(false);
  const [agentId, setAgentId] = useState('demo_exec_patch');
  const [goal, setGoal] = useState('Demo exec + patch');
  const [params, setParams] = useState('{ "demo_exec_patch": true }');
  const [status, setStatus] = useState('');

  const scrollWorkforce = (direction: 'left' | 'right') => {
    if (workforceContainerRef.current) {
      const scrollAmount = 404; // width of card + gap
      const scrollLeft = direction === 'left' ? -scrollAmount : scrollAmount;
      workforceContainerRef.current.scrollBy({ left: scrollLeft, behavior: 'smooth' });
    }
  };

  const updateScrollButtons = () => {
    const container = workforceContainerRef.current;
    if (container && container.scrollWidth > container.clientWidth) {
      const isAtStart = container.scrollLeft <= 0;
      const isAtEnd = container.scrollLeft + container.clientWidth >= container.scrollWidth - 1;
      return { isAtStart, isAtEnd };
    }
    return { isAtStart: true, isAtEnd: true };
  };

  const handleCreateAgent = () => {
    setIsCreatingAgent(true);
    setTimeout(() => setIsCreatingAgent(false), 2000);
  };

  const sendListAgents = async () => {
    setStatus('Listing agents...');
    const text = 'Call the MCP tool `agents.list` with {} and show the JSON result.';
    await userTurn(text);
    setStatus('List request sent. See Chat for results.');
  };

  const sendStartTask = async () => {
    let args: any = {};
    try { args = JSON.parse(params || '{}'); } catch { args = {}; }
    const payload = {
      agent_id: agentId,
      goal,
      params: args,
      permission_profile: { sandbox: 'read-only', approval_policy: 'on-request', tool_allowlist: ['mcp:any'] },
    } as any;
    setStatus('Starting task...');
    const text = [
      'Call the MCP tool `agents.start_task` with the following JSON arguments:',
      '```json',
      JSON.stringify(payload),
      '```',
      'Use the tool directly; do not ask for confirmation. Then acknowledge.'
    ].join('\n');
    await userTurn(text);
    setStatus('Task request sent. Watch Chat for approvals and progress.');
  };

  useEffect(() => {
    const container = workforceContainerRef.current;
    if (container) {
      const updateState = () => setScrollState(updateScrollButtons());
      container.addEventListener('scroll', updateState);
      window.addEventListener('resize', updateState);
      updateState();

      return () => {
        container.removeEventListener('scroll', updateState);
        window.removeEventListener('resize', updateState);
      };
    }
  }, []);

  return (
    <div className="workspace-layout container-full transition-fade-in bg-gradient-aurora">
      {/* Minimal Agents Manager controls */}
      <div className="border border-[var(--border)] rounded-lg p-4 bg-[var(--bg-secondary)] m-6 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Agents Manager (Minimal)</h2>
          <div className="text-sm text-[var(--text-secondary)]">{status}</div>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] flex items-center gap-2" onClick={sendListAgents}>
            <IconList size={16} /> List Agents
          </button>
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] flex items-center gap-2" onClick={()=>window.aiw.listMcpTools()}>
            <IconRefresh size={16} /> Refresh MCP Tools
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-2xs text-[var(--text-tertiary)]">Agent ID</label>
            <input className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" value={agentId} onChange={(e)=>setAgentId(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1 md:col-span-2">
            <label className="text-2xs text-[var(--text-tertiary)]">Goal</label>
            <input className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" value={goal} onChange={(e)=>setGoal(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1 md:col-span-3">
            <label className="text-2xs text-[var(--text-tertiary)]">Params (JSON)</label>
            <textarea className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] min-h-[100px]" value={params} onChange={(e)=>setParams(e.target.value)} />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1 rounded bg-[var(--accent)] text-white flex items-center gap-2" onClick={sendStartTask}>
            <IconPlayerPlay size={16} /> Start Task
          </button>
          <div className="text-2xs text-[var(--text-tertiary)]">Approvals will appear in Chat; monitor progress there.</div>
        </div>
      </div>
      {/* Enhanced Grid Layout with Golden Ratio */}
      <div className="grid-asymmetric-sidebar gap-xl">
        {/* Left Panel: Task Overview - Using Golden Ratio Proportion */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="workspace-card glass-card hover-lift card-premium"
        >
          <div className="content-flow-lg">
            <div>
              <motion.h2 
                className="text-hierarchy-2 font-bold text-aurora hierarchy-title hover-accent"
                whileHover={{ x: 4 }}
              >
                Task Overview
              </motion.h2>
              <p className="text-hierarchy-5 text-[var(--text-secondary)] rhythm-relaxed hierarchy-paragraph">
                Urgently analyze the reasons behind the unusual surge in new energy stocks. Combine internal user behavior database and investment portfolios. Generate personalized analysis reports and send them to relevant clients.
              </p>
            </div>
            
            <div className="glass-card p-lg hover-lift-sm interactive-card">
              <div className="flex items-center gap-md hierarchy-subtitle">
                <motion.div 
                  className="w-10 h-10 bg-gradient-aurora rounded-lg flex items-center justify-center hover-spin interactive-icon shadow-glow-accent"
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.5 }}
                >
                  <IconActivity size={20} className="text-white" />
                </motion.div>
                <div>
                  <motion.h3 
                    className="font-semibold text-[var(--text-primary)] text-hierarchy-4 hover-accent"
                    whileHover={{ x: 4 }}
                  >
                    Active Session
                  </motion.h3>
                  <p className="text-hierarchy-5 text-[var(--text-secondary)]">3 agents working</p>
                </div>
              </div>
              
              <div className="content-flow">
                <div className="flex justify-between items-center">
                  <span className="text-hierarchy-5 text-[var(--text-secondary)]">Overall Progress</span>
                  <motion.span 
                    className="text-hierarchy-5 font-semibold neon-blue"
                    whileHover={{ scale: 1.1 }}
                  >
                    67%
                  </motion.span>
                </div>
                <div className="agent-progress hover-brighten border-gradient-aurora">
                  <motion.div 
                    className="agent-progress-bar bg-gradient-aurora"
                    initial={{ width: 0 }}
                    animate={{ width: "67%" }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-md">
              <motion.div 
                className="text-center p-md glass-card hover-lift-sm interactive-card shadow-colored"
                whileHover={{ scale: 1.05 }}
              >
                <motion.div 
                  className="text-hierarchy-2 font-bold neon-green"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.3, type: "spring" }}
                  whileHover={{ scale: 1.1 }}
                >
                  26
                </motion.div>
                <div className="text-hierarchy-5 text-[var(--text-secondary)]">Tasks Done</div>
              </motion.div>
              <motion.div 
                className="text-center p-md glass-card hover-lift-sm interactive-card shadow-colored"
                whileHover={{ scale: 1.05 }}
              >
                <motion.div 
                  className="text-hierarchy-2 font-bold neon-purple"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.4, type: "spring" }}
                  whileHover={{ scale: 1.1 }}
                >
                  12
                </motion.div>
                <div className="text-hierarchy-5 text-[var(--text-secondary)]">In Progress</div>
              </motion.div>
            </div>

            {/* Add Agent Button */}
            <motion.button
              className="btn-gradient btn-haptic hover-lift w-full shimmer"
              onClick={handleCreateAgent}
              disabled={isCreatingAgent}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <IconPlus size={16} className="interactive-icon" />
              {isCreatingAgent ? 'Creating Agent...' : 'Create New Agent'}
            </motion.button>
          </div>
        </motion.div>

        {/* Right Panel: Agent Grid - Main Content Area */}
        <div className="workspace-content">
          {/* Agent Workforce Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="section-spacing-sm"
          >
            <div className="flex items-center justify-between hierarchy-subtitle">
              <motion.h2 
                className="text-hierarchy-2 font-bold text-gradient-cosmic hover-accent"
                whileHover={{ x: 4 }}
              >
                Agent Workforce
              </motion.h2>
              <div className="flex items-center gap-sm">
                <motion.button 
                  onClick={() => scrollWorkforce('left')}
                  disabled={scrollState.isAtStart}
                  className="glass-button btn-elastic p-xs disabled:opacity-50 disabled:cursor-not-allowed interactive-icon"
                  whileHover={{ scale: 1.1, rotate: -5 }}
                  whileTap={{ scale: 0.9 }}
                >
                  ←
                </motion.button>
                <motion.button 
                  onClick={() => scrollWorkforce('right')}
                  disabled={scrollState.isAtEnd}
                  className="glass-button btn-elastic p-xs disabled:opacity-50 disabled:cursor-not-allowed interactive-icon"
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  whileTap={{ scale: 0.9 }}
                >
                  →
                </motion.button>
              </div>
            </div>

            {/* Enhanced Agent Grid with Container Queries */}
            <motion.div
              ref={workforceContainerRef}
              className="agent-grid-enhanced gap-xl"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {agents.map((agent, index) => (
                <motion.div
                  key={agent.id}
                  variants={cardVariants}
                  whileHover={{ scale: 1.02, y: -5 }}
                  whileTap={{ scale: 0.98 }}
                  className={`card-premium glass-card p-lg interactive-card hover-lift stagger-item shadow-multi ${
                    agent.status === 'processing' ? 'loading-pulse shimmer' : ''
                  }`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="content-flow">
                    <div className="flex items-center justify-between">
                      <motion.div 
                        className="agent-avatar hover-spin interactive-icon bg-gradient-sunset shadow-glow-accent"
                        whileHover={{ scale: 1.1, rotate: 10 }}
                      >
                        {agent.avatar}
                      </motion.div>
                      <motion.div 
                        className={`status-indicator status-${agent.status} neon-border glass`}
                        whileHover={{ scale: 1.05 }}
                      >
                        <div className={`w-2 h-2 rounded-full bg-current ${
                          agent.status === 'processing' ? 'animate-pulse loading-bounce neon-blue' : 
                          agent.status === 'active' ? 'neon-green' : 'neon-orange'
                        }`} />
                        {agent.status}
                      </motion.div>
                    </div>

                    <div>
                      <motion.h3 
                        className="text-hierarchy-4 font-semibold text-gradient-primary hierarchy-subtitle hover-accent"
                        whileHover={{ x: 4 }}
                      >
                        {agent.name}
                      </motion.h3>
                      
                      <div className="flex items-center gap-sm text-hierarchy-5 text-[var(--text-secondary)] hierarchy-paragraph">
                        <motion.div
                          className="interactive-icon text-gradient-aurora"
                          whileHover={{ scale: 1.2, rotate: 15 }}
                        >
                          {agent.icon}
                        </motion.div>
                        <span>Last active: {agent.lastActivity}</span>
                      </div>
                    </div>

                    <div className="content-flow-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-hierarchy-5 text-[var(--text-secondary)]">Progress</span>
                        <motion.span 
                          className="text-hierarchy-5 font-medium neon-blue"
                          whileHover={{ scale: 1.1 }}
                        >
                          {agent.progress}%
                        </motion.span>
                      </div>
                      <div className="agent-progress hover-brighten border-gradient-primary">
                        <motion.div 
                          className="agent-progress-bar bg-gradient-ocean"
                          initial={{ width: 0 }}
                          animate={{ width: `${agent.progress}%` }}
                          transition={{ duration: 1, delay: index * 0.1, ease: "easeOut" }}
                        />
                      </div>
                    </div>

                    <div className="content-flow-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-hierarchy-5 text-[var(--text-secondary)]">Tasks</span>
                        <motion.span 
                          className="text-hierarchy-5 font-medium neon-purple"
                          whileHover={{ scale: 1.1 }}
                        >
                          {agent.tasksCompleted}/{agent.totalTasks}
                        </motion.span>
                      </div>
                      
                      <div className="flex flex-wrap gap-xs">
                        {agent.tags.map((tag, tagIndex) => (
                          <motion.span 
                            key={tagIndex}
                            className="text-hierarchy-5 px-sm py-xs glass border-gradient-aurora rounded-full hover-lift-sm interactive-card shimmer-text"
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ 
                              delay: (index * 0.1) + (tagIndex * 0.05),
                              duration: 0.3 
                            }}
                            whileHover={{ scale: 1.05, y: -2 }}
                          >
                            {tag}
                          </motion.span>
                        ))}
                      </div>
                    </div>

                    {/* Agent Actions */}
                    <div className="flex gap-sm mt-md">
                      <motion.button
                        className="glass-button btn-elastic flex-1 interactive-icon border-gradient-primary"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <IconSettings size={14} />
                        Configure
                      </motion.button>
                      <motion.button
                        className="btn-gradient btn-haptic flex-1"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        View Details
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              ))}

              {/* Loading Skeleton when creating new agent */}
              {isCreatingAgent && (
                <motion.div
                  className="card-premium glass-card p-lg skeleton-card interactive-card bg-animated-gradient"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                >
                  <div className="content-flow">
                    <div className="flex items-center justify-between">
                      <div className="skeleton-avatar bg-gradient-aurora" />
                      <div className="skeleton-text-sm bg-gradient-sunset" />
                    </div>
                    <div className="skeleton-text bg-gradient-ocean" />
                    <div className="skeleton-text-lg bg-gradient-forest" />
                    <div className="skeleton-text-sm bg-gradient-cosmic" />
                    <div className="flex gap-xs">
                      <div className="skeleton-text-sm w-16 bg-gradient-primary" />
                      <div className="skeleton-text-sm w-20 bg-gradient-secondary" />
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default AgentsWorkspace;
