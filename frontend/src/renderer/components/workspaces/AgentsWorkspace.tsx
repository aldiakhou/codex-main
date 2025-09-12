import React, { useRef, useState, useEffect, useMemo } from 'react';
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
  const { listAgents, agentsReload, startAgent, agentRuns, agents: liveAgents, agentCancel, agentStatus, plan, plansByTask, toolCalls, messages } = useBackend();
  const workforceContainerRef = useRef<HTMLDivElement>(null);
  const [scrollState, setScrollState] = useState({ isAtStart: true, isAtEnd: true });
  const [isCreatingAgent, setIsCreatingAgent] = useState(false);
  const [agentId, setAgentId] = useState('demo_exec_patch');
  const [goal, setGoal] = useState('Demo exec + patch');
  const [params, setParams] = useState('{ "demo_exec_patch": true }');
  const [status, setStatus] = useState('');
  const [cardGoals, setCardGoals] = useState<Record<string, string>>({
    search: 'Research: "AI agents frontend architecture best practices"',
    developer: 'Draft implementation plan for feature X',
    document: 'Summarize project docs into a brief',
  });

  // Drawer state for run details
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsAgentId, setDetailsAgentId] = useState<string | null>(null);
  const [detailsTaskId, setDetailsTaskId] = useState<string | null>(null);
  const [compactMode, setCompactMode] = useState(true);

  const lastAssistant = useMemo(() => {
    try {
      const arr = (messages || []).slice().reverse();
      if (detailsTaskId) {
        const byTask = arr.find((m: any) => m.role === 'assistant' && m.taskId === detailsTaskId);
        if (byTask) return byTask;
      }
      return arr.find((m: any) => m.role === 'assistant') || null;
    } catch {
      return null as any;
    }
  }, [messages, detailsTaskId]);

  // Periodically refresh status for running tasks
  useEffect(() => {
    const t = setInterval(() => {
      Object.values(agentRuns || {}).forEach((run) => {
        if (run.status === 'running') {
          try { agentStatus(run.task_id); } catch {}
        }
      });
    }, 3000);
    return () => clearInterval(t);
  }, [agentRuns, agentStatus]);

  // Fetch agents on mount
  useEffect(() => {
    try { listAgents(); } catch {}
  }, [listAgents]);

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

  const doListAgents = async () => {
    setStatus('Listing agents...');
    await listAgents();
    setStatus('Received agents list.');
  };

  const doReloadAgents = async () => {
    setStatus('Reloading agents...');
    await agentsReload();
    setStatus('Agents reloaded.');
  };

  const doStartTask = async () => {
    let ctx: any = undefined;
    try { ctx = params ? JSON.parse(params) : undefined; } catch { ctx = undefined; }
    setStatus('Starting agent...');
    const ok = await startAgent(agentId, goal, ctx);
    setStatus(ok ? 'Agent started.' : 'Failed to start agent.');
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
      {/* Minimal manager removed from top; integrated below. */}
      {/* Enhanced Grid Layout with Golden Ratio */}
      <div className="grid-asymmetric-sidebar gap-xl">
        {/* Left Panel: Task Overview - Using Golden Ratio Proportion */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="workspace-card glass-card hover-lift card-premium max-h-[560px] overflow-auto"
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
            <div className="glass-card p-md hover-lift-sm interactive-card">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <button className="px-3 py-1 rounded glass-button border border-[var(--border)] flex items-center gap-2" onClick={doListAgents}>
                  <IconList size={16} /> List Agents
                </button>
                <button className="px-3 py-1 rounded glass-button border border-[var(--border)] flex items-center gap-2" onClick={doReloadAgents}>
                  <IconRefresh size={16} /> Reload Agents
                </button>
                <button className="px-3 py-1 rounded glass-button border border-[var(--border)] flex items-center gap-2" onClick={()=>window.aiw.listMcpTools()}>
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
                  <label className="text-2xs text-[var(--text-tertiary)]">Context (JSON)</label>
                  <textarea className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] min-h-[80px]" value={params} onChange={(e)=>setParams(e.target.value)} />
                </div>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <button className="px-3 py-1 rounded btn-gradient btn-haptic flex items-center gap-2" onClick={doStartTask}>
                  <IconPlayerPlay size={16} /> Start Task
                </button>
                <div className="text-2xs text-[var(--text-tertiary)]">Approvals will appear in Chat; monitor progress there.</div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                <div className="p-2 rounded border border-[var(--border)] bg-[var(--bg-tertiary)]">
                  <div className="font-semibold mb-2 text-sm">Available Agents</div>
                  <div className="space-y-1 max-h-40 overflow-auto">
                    {liveAgents.length === 0 ? (
                      <div className="text-2xs text-[var(--text-tertiary)]">No agents yet. Use Reload Agents.</div>
                    ) : (
                      liveAgents.map(a => (
                        <div key={a.id} className="flex items-center justify-between text-sm">
                          <div className="truncate"><span className="font-medium">{a.id}</span> <span className="text-2xs text-[var(--text-tertiary)]">{a.name}</span></div>
                          <button className="px-2 py-0.5 rounded bg-[var(--bg-secondary)] border border-[var(--border)] text-2xs" onClick={()=>{ setAgentId(a.id); setGoal(a.description || goal); }}>Select</button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
                <div className="p-2 rounded border border-[var(--border)] bg-[var(--bg-tertiary)]">
                  <div className="font-semibold mb-2 text-sm">Active Runs</div>
                  <div className="space-y-1 max-h-40 overflow-auto">
                    {Object.keys(agentRuns).length === 0 ? (
                      <div className="text-2xs text-[var(--text-tertiary)]">No active runs.</div>
                    ) : (
                      Object.values(agentRuns).sort((a,b)=>b.updated_at-a.updated_at).map(run => (
                        <div key={run.task_id} className="flex items-center justify-between text-sm">
                          <div className="truncate"><span className="font-medium">{run.agent_id || 'agent'}</span> <span className="text-2xs text-[var(--text-tertiary)]">{run.status}</span></div>
                          <button className="px-2 py-0.5 rounded bg-[var(--bg-secondary)] border border-[var(--border)] text-2xs" onClick={()=>agentCancel(run.task_id)}>Cancel</button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
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
                <label className="text-2xs text-[var(--text-tertiary)] mr-2">Compact</label>
                <input type="checkbox" checked={compactMode} onChange={(e)=>setCompactMode(e.target.checked)} />
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
              className="agent-grid-enhanced gap-xl max-h-[calc(100vh-220px)] overflow-auto pr-2"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {(liveAgents.length ? liveAgents : []).map((a, index) => {
                // Map static cards to real agent ids
                const realId = a.id;
                // Find latest run for this agent
                const latestRun = Object.values(agentRuns || {})
                  .filter(r => (r.agent_id || '') === realId)
                  .sort((a,b)=>b.updated_at - a.updated_at)[0];
                const cardStatusClass = latestRun ? (latestRun.status === 'running' ? 'processing' : latestRun.status === 'complete' ? 'active' : 'idle') : 'idle';
                const statusText = latestRun ? latestRun.status : 'idle';
                const goalValue = cardGoals[realId] ?? '';
                const onStart = async () => { await startAgent(realId, goalValue || 'Start an agent task.'); };
                const onCancel = async () => { if (latestRun) await agentCancel(latestRun.task_id); };
                const onView = () => {
                  setDetailsAgentId(realId);
                  setDetailsTaskId(latestRun?.task_id || null);
                  setDetailsOpen(true);
                };
                const name = a.name || realId;
                const avatar = (name || realId).trim().charAt(0).toUpperCase();
                return (
                <motion.div
                  key={realId}
                  variants={cardVariants}
                  whileHover={{ scale: 1.02, y: -5 }}
                  whileTap={{ scale: 0.98 }}
                  className={`card-premium glass-card ${compactMode ? 'p-md' : 'p-lg'} interactive-card hover-lift stagger-item shadow-multi ${
                    cardStatusClass === 'processing' ? 'loading-pulse shimmer' : ''
                  }`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="content-flow">
                    <div className="flex items-center justify-between">
                      <motion.div 
                        className="agent-avatar hover-spin interactive-icon bg-gradient-sunset shadow-glow-accent"
                        whileHover={{ scale: 1.1, rotate: 10 }}
                      >
                        {avatar}
                      </motion.div>
                      <motion.div 
                        className={`status-indicator status-${cardStatusClass} neon-border glass`}
                        whileHover={{ scale: 1.05 }}
                      >
                        <div className={`w-2 h-2 rounded-full bg-current ${
                          cardStatusClass === 'processing' ? 'animate-pulse loading-bounce neon-blue' : 
                          cardStatusClass === 'active' ? 'neon-green' : 'neon-orange'
                        }`} />
                        {statusText}
                      </motion.div>
                    </div>

                    <div>
                      <motion.h3 
                        className="text-hierarchy-4 font-semibold text-gradient-primary hierarchy-subtitle hover-accent"
                        whileHover={{ x: 4 }}
                      >
                        {name}
                      </motion.h3>
                      {!compactMode && (
                        <div className="flex items-center gap-sm text-hierarchy-5 text-[var(--text-secondary)] hierarchy-paragraph">
                          <span>Agent id: {realId}</span>
                        </div>
                      )}
                    </div>

                    {!compactMode && (
                      <div className="content-flow-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-hierarchy-5 text-[var(--text-secondary)]">Progress</span>
                          <motion.span className="text-hierarchy-5 font-medium neon-blue" whileHover={{ scale: 1.1 }}>
                            {latestRun ? (latestRun.status === 'running' ? '...' : '100%') : '0%'}
                          </motion.span>
                        </div>
                        <div className="agent-progress hover-brighten border-gradient-primary">
                          <motion.div className="agent-progress-bar bg-gradient-ocean" initial={{ width: 0 }} animate={{ width: latestRun ? (latestRun.status === 'running' ? '60%' : '100%') : '0%' }} transition={{ duration: 0.6 }} />
                        </div>
                      </div>
                    )}

                    {!compactMode && (
                      <div className="content-flow-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-hierarchy-5 text-[var(--text-secondary)]">Description</span>
                        </div>
                        <div className="text-2xs text-[var(--text-tertiary)] break-words">{a.description || '—'}</div>
                      </div>
                    )}

                    {/* Per-card goal input */}
                    <div className="content-flow-sm mt-sm">
                      <label className="text-2xs text-[var(--text-tertiary)]">Goal</label>
                      <input
                        className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)] w-full"
                        value={goalValue}
                        onChange={(e)=> setCardGoals((prev)=>({ ...prev, [realId]: e.target.value }))}
                        placeholder="What should this agent do?"
                      />
                    </div>

                    {/* Agent Actions */}
                    <div className="flex gap-sm mt-md">
                      <motion.button
                        className="glass-button btn-elastic flex-1 interactive-icon border-gradient-primary"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={onStart}
                      >
                        <IconSettings size={14} />
                        Run
                      </motion.button>
                      <motion.button
                        className="btn-gradient btn-haptic flex-1"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={onView}
                      >
                        View Details
                      </motion.button>
                      {latestRun && latestRun.status === 'running' && (
                        <motion.button
                          className="glass-button btn-elastic flex-1 interactive-icon border-gradient-aurora"
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={onCancel}
                        >
                          Cancel
                        </motion.button>
                      )}
                    </div>

                    {/* Inline error banner if last run errored */}
                    {latestRun && latestRun.error && (
                      <div className="mt-sm p-xs rounded border border-red-500/40 bg-red-500/10 text-red-300 text-2xs">
                        Error: {latestRun.error}
                      </div>
                    )}
                  </div>
                </motion.div>
              );})}

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
      {/* Run Details Drawer */}
      {detailsOpen && (
        <div className="fixed inset-0 z-50 flex">
          <div className="flex-1 bg-black/40" onClick={()=>setDetailsOpen(false)} />
          <div className="w-full sm:w-[480px] max-w-[90vw] h-full bg-[var(--bg-secondary)] border-l border-[var(--border)] shadow-xl overflow-auto p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-lg font-semibold">Agent Details</div>
              <button className="px-2 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={()=>setDetailsOpen(false)}>Close</button>
            </div>
            <div className="space-y-4">
              <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-tertiary)]">
                <div className="text-sm"><span className="text-[var(--text-tertiary)]">Agent:</span> {detailsAgentId || '-'}</div>
                <div className="text-sm"><span className="text-[var(--text-tertiary)]">Task ID:</span> {detailsTaskId || '-'}</div>
                {detailsTaskId && agentRuns[detailsTaskId] && (
                  <div className="text-sm"><span className="text-[var(--text-tertiary)]">Status:</span> {agentRuns[detailsTaskId].status} {agentRuns[detailsTaskId].error ? (<span className="text-red-400">• {agentRuns[detailsTaskId].error}</span>) : null}</div>
                )}
              </div>

              {/* Live Plan */}
              <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-tertiary)]">
                <div className="font-semibold mb-2 text-sm">Live Plan</div>
                {(() => { const p = detailsTaskId && plansByTask[detailsTaskId] ? plansByTask[detailsTaskId] : plan; return p && p.plan && p.plan.length ? (
                  <ul className="space-y-1">
                    {p.plan.map((it, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm">
                        <span className={`w-2 h-2 rounded-full ${it.status === 'completed' ? 'bg-green-400' : it.status === 'in_progress' ? 'bg-blue-400 animate-pulse' : 'bg-zinc-500'}`} />
                        <span className="font-medium">{it.step}</span>
                        <span className="text-2xs text-[var(--text-tertiary)]">{it.status.replace('_', ' ')}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-2xs text-[var(--text-tertiary)]">No plan yet.</div>
                ); })()}
                {(() => { const p = detailsTaskId && plansByTask[detailsTaskId] ? plansByTask[detailsTaskId] : plan; return p?.explanation ? <div className="mt-2 text-2xs text-[var(--text-tertiary)]">{p.explanation}</div> : null; })()}
              </div>

              {/* Tool Calls (recent) */}
              <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-tertiary)]">
                <div className="font-semibold mb-2 text-sm">Recent Tool Calls</div>
                {toolCalls && toolCalls.length ? (
                  <div className="space-y-2">
                    {toolCalls.filter(tc => !detailsTaskId || tc.task_id === detailsTaskId).slice(0, 10).map((tc) => (
                      <div key={tc.call_id} className="text-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="text-2xs text-[var(--text-tertiary)] mr-2">{tc.kind}</span>
                            {tc.kind === 'mcp' ? <span className="font-medium">{tc.name}</span> : <span className="font-medium">{(tc.command||[]).join(' ')}</span>}
                          </div>
                          <div className="text-2xs text-[var(--text-tertiary)]">{tc.status}</div>
                        </div>
                        {tc.formatted_output && (
                          <pre className="mt-1 whitespace-pre-wrap text-xs bg-black/20 p-2 rounded border border-[var(--border)]">{tc.formatted_output}</pre>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-2xs text-[var(--text-tertiary)]">No tool calls yet.</div>
                )}
              </div>

              {/* Final Output (best-effort) */}
              <div className="p-3 rounded border border-[var(--border)] bg-[var(--bg-tertiary)]">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-semibold text-sm">Final Output (latest assistant)</div>
                  <button className="text-2xs underline" onClick={()=>{
                    try { const text = (lastAssistant as any)?.text || ''; if (text) navigator.clipboard?.writeText(text); } catch {}
                  }}>Copy</button>
                </div>
                {lastAssistant ? (
                  <pre className="whitespace-pre-wrap text-xs bg-black/20 p-2 rounded border border-[var(--border)]">{(lastAssistant as any).text}</pre>
                ) : (
                  <div className="text-2xs text-[var(--text-tertiary)]">No assistant output captured.</div>
                )}
                <div className="mt-2 text-2xs text-[var(--text-tertiary)]">Note: Plan and tool calls are filtered by the run when available.</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentsWorkspace;
