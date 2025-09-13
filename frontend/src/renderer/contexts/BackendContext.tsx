import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';

type Status = 'connecting' | 'connected' | 'disconnected' | 'error' | 'idle';

type ExecApprovalRequest = {
  id: string; // event id
  call_id: string;
  command: string[];
  cwd: string;
  reason?: string;
};

type PatchApprovalRequest = {
  id: string;
  call_id: string;
  changes: Record<string, { type: 'add' | 'delete' | 'update'; unified_diff?: string; move_path?: string | null; content?: string }>;
  reason?: string;
  grant_root?: string;
};

type BackendContextType = {
  status: Status;
  logs: string[];
  lastEvent: any | null;
  messages: { id: string; role: 'assistant' | 'reasoning' | 'system' | 'tool' | 'user'; text: string; ts?: number; taskId?: string }[];
  draftMessage: string;
  setDraftMessage: (v: string) => void;
  chatParams: {
    model: string;
    approval_policy: 'untrusted' | 'on-failure' | 'on-request' | 'never';
    sandbox_mode: 'read-only' | 'workspace-write' | 'danger-full-access';
    effort: 'minimal' | 'low' | 'medium' | 'high';
    summary: 'auto' | 'concise' | 'detailed' | 'none';
    cwd?: string;
    showReasoning: boolean;
  };
  setChatParams: (p: Partial<BackendContextType['chatParams']>) => void;
  start: (opts?: { codexPath?: string; profile?: string }) => Promise<void>;
  stop: () => Promise<void>;
  login: (apiKey?: string) => Promise<boolean>;
  userTurn: (text: string, params?: Partial<{ cwd: string; approval_policy: string; sandbox_mode: string; model: string; effort: string; summary: string }>) => Promise<boolean>;
  interrupt: () => Promise<boolean>;
  execApproval: (submissionId: string, decision: 'approved' | 'approved_for_session' | 'denied' | 'abort') => Promise<boolean>;
  patchApproval: (submissionId: string, decision: 'approved' | 'approved_for_session' | 'denied' | 'abort') => Promise<boolean>;
  setCodexPath: (p: string) => Promise<boolean>;
  execApprovalRequest: ExecApprovalRequest | null;
  patchApprovalRequest: PatchApprovalRequest | null;
  clearApprovals: () => void;
  lastError?: string | null;
  tokenUsage?: { input_tokens: number; cached_input_tokens?: number; output_tokens: number; reasoning_output_tokens?: number; total_tokens: number; context_window?: number };
  toolCalls: Array<{
    call_id: string;
    kind: 'exec' | 'mcp';
    name?: string;
    command?: string[];
    cwd?: string;
    status: 'running' | 'done';
    exit_code?: number;
    started_at: number;
    ended_at?: number;
    stdout: string;
    stderr: string;
    formatted_output?: string;
    task_id?: string;
  }>;
  getHistory: () => Promise<boolean>;
  mcpTools: Record<string, any>;
  refreshMcpTools: () => Promise<boolean>;
  mcpServers: Record<string, { name: string; command: string; args?: string[]; env?: Record<string,string> }>;
  refreshMcpServers: () => Promise<Record<string, any>>;
  serverErrors: Record<string, string>;
  plan: { explanation?: string | null; plan: Array<{ step: string; status: 'pending' | 'in_progress' | 'completed' }> } | null;
  plansByTask: Record<string, { explanation?: string | null; plan: Array<{ step: string; status: 'pending' | 'in_progress' | 'completed' }> }>;
  turnDiff?: string | null;
  customPrompts: Array<{ name: string; path: string; content: string }>;
  refreshCustomPrompts: () => Promise<boolean>;
  // --- Agents proto state/actions ---
  agents: Array<{ id: string; name: string; description: string }>;
  agentRuns: Record<string, { task_id: string; agent_id: string; status: string; error?: string; created_at: number; updated_at: number; allowed_mcp_tools?: string[] }>;
  listAgents: () => Promise<boolean>;
  agentsReload: () => Promise<boolean>;
  startAgent: (id: string, input?: string, context?: any) => Promise<boolean>;
  agentStatus: (taskId: string) => Promise<boolean>;
  agentCancel: (taskId: string) => Promise<boolean>;
};

const BackendContext = createContext<BackendContextType | undefined>(undefined);

export const useBackend = () => {
  const ctx = useContext(BackendContext);
  if (!ctx) throw new Error('useBackend must be used within BackendProvider');
  return ctx;
};

export const BackendProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [status, setStatus] = useState<Status>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [lastEvent, setLastEvent] = useState<any | null>(null);
  const [messages, setMessages] = useState<BackendContextType['messages']>([]);
  const streamingAssistantRef = useRef<{ id: string; text: string } | null>(null);
  const streamingReasoningRef = useRef<{ id: string; text: string } | null>(null);
  const [execApprovalRequest, setExecApprovalRequest] = useState<ExecApprovalRequest | null>(null);
  const [patchApprovalRequest, setPatchApprovalRequest] = useState<PatchApprovalRequest | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);
  const [draftMessage, setDraftMessage] = useState<string>('');
  const [tokenUsage, setTokenUsage] = useState<BackendContextType['tokenUsage']>();
  const [toolCalls, setToolCalls] = useState<BackendContextType['toolCalls']>([]);
  const [mcpTools, setMcpTools] = useState<Record<string, any>>({});
  const [mcpServers, setMcpServers] = useState<Record<string, any>>({});
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});
  const [plan, setPlan] = useState<BackendContextType['plan']>(null);
  const [plansByTask, setPlansByTask] = useState<BackendContextType['plansByTask']>({});
  const [turnDiff, setTurnDiff] = useState<string | null>(null);
  const rawReasoningRef = useRef<{ id: string; text: string } | null>(null);
  const [customPrompts, setCustomPrompts] = useState<BackendContextType['customPrompts']>([]);
  // Agents proto state
  const [agents, setAgents] = useState<BackendContextType['agents']>([]);
  const [agentRuns, setAgentRuns] = useState<BackendContextType['agentRuns']>({});
  const [chatParams, setChatParamsState] = useState<BackendContextType['chatParams']>(() => {
    const saved = localStorage.getItem('chatParams');
    if (saved) {
      try { return JSON.parse(saved); } catch {}
    }
    return {
      model: 'gpt-5',
      approval_policy: 'on-request',
      sandbox_mode: 'read-only',
      effort: 'medium',
      summary: 'auto',
      cwd: undefined,
      showReasoning: true,
    };
  });
  const setChatParams = (p: Partial<BackendContextType['chatParams']>) => {
    setChatParamsState((prev) => {
      const next = { ...prev, ...p };
      localStorage.setItem('chatParams', JSON.stringify(next));
      return next;
    });
  };

  const unsub = useRef<(() => void)[]>([]);

  useEffect(() => {
    // wire listeners
    unsub.current.push(window.aiw.onStatus((s) => setStatus((s as Status) || 'idle')));
    unsub.current.push(window.aiw.onLog((m) => setLogs((prev) => [...prev.slice(-400), m])));
    unsub.current.push(
      window.aiw.onEvent((e) => {
        setLastEvent(e);
        const type = e?.msg?.type || e?.type || '';
        const metaTaskId: string | undefined = (e && e._meta && (e._meta.task_id || e._meta.taskId)) ? String(e._meta.task_id || e._meta.taskId) : undefined;
        // --- Agents proto events ---
        if (type === 'agents_listed') {
          const arr = Array.isArray(e?.msg?.agents) ? e.msg.agents : [];
          const mapped = arr.map((a: any) => ({ id: String(a.id||''), name: String(a.name||''), description: String(a.description||'') }));
          setAgents(mapped);
          return;
        }
        if (type === 'agent_run_started') {
          const agent_id = String(e?.msg?.agent_id || '');
          const task_id = String(e?.msg?.task_id || '');
          // try to extract allowlist if backend provided it
          const allowed: string[] | undefined = (e?.structured_content?.allowed_mcp_tools
            || e?.msg?.structured_content?.allowed_mcp_tools
            || e?.allowed_mcp_tools
            || undefined);
          if (!task_id) return;
          setAgentRuns((prev) => ({
            ...prev,
            [task_id]: { task_id, agent_id, status: 'running', created_at: Date.now(), updated_at: Date.now(), allowed_mcp_tools: Array.isArray(allowed) ? allowed.map(String) : undefined },
          }));
          return;
        }
        if (type === 'agent_status') {
          const task_id = String(e?.msg?.task_id || '');
          const status = String(e?.msg?.status || 'unknown');
          const error = e?.msg?.error ? String(e.msg.error) : undefined;
          if (!task_id) return;
          setAgentRuns((prev) => ({
            ...prev,
            [task_id]: { ...(prev[task_id] || { task_id, agent_id: '', created_at: Date.now() }), task_id, status, error, updated_at: Date.now() },
          }));
          return;
        }
        if (type === 'agent_cancelled') {
          const task_id = String(e?.msg?.task_id || '');
          if (!task_id) return;
          setAgentRuns((prev) => ({
            ...prev,
            [task_id]: { ...(prev[task_id] || { task_id, agent_id: '', created_at: Date.now() }), task_id, status: 'cancelled', updated_at: Date.now() },
          }));
          return;
        }
        // Agent message streaming
        if (type === 'agent_message') {
          const text = e.msg?.message ?? '';
          if (!text) return;
          // If we were streaming deltas, update that message instead of appending a new one
          const cur = streamingAssistantRef.current;
          if (cur) {
            const cid = cur.id;
            setMessages((prev) => prev.map((m) => (m.id === cid ? { ...m, text } : m)));
            streamingAssistantRef.current = null;
          } else {
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.role === 'assistant' && last.text === text) return prev; // de-dupe
              return [...prev, { id: `msg_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'assistant', text, taskId: metaTaskId } as any];
            });
          }
          return;
        }
        if (type === 'agent_message_delta') {
          const delta = e.msg?.delta ?? '';
          if (!delta) return;
          let cur = streamingAssistantRef.current;
          if (!cur) {
            cur = { id: `delta_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, text: '' };
            streamingAssistantRef.current = cur;
            setMessages((prev) => [...prev, { id: cur.id, role: 'assistant', text: '', ts: Date.now(), taskId: metaTaskId } as any]);
          }
          cur.text += delta;
          const cid = cur.id;
            setMessages((prev) => prev.map((m) => (m.id === cid ? { ...m, text: cur!.text } : m)));
          return;
        }
        if (type === 'agent_reasoning') {
          const text = e.msg?.text ?? '';
          if (!text) return;
          const cur = streamingReasoningRef.current;
          if (cur) {
            const cid = cur.id;
            setMessages((prev) => prev.map((m) => (m.id === cid ? { ...m, text } : m)));
            streamingReasoningRef.current = null;
          } else {
            setMessages((prev) => [...prev, { id: `rsn_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'reasoning', text, ts: Date.now(), taskId: metaTaskId } as any]);
          }
          return;
        }
        if (type === 'agent_reasoning_delta') {
          const delta = e.msg?.delta ?? e.msg?.text ?? '';
          if (!delta) return;
          let cur = streamingReasoningRef.current;
          if (!cur) {
            cur = { id: `rsn_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, text: '' };
            streamingReasoningRef.current = cur;
            setMessages((prev) => [...prev, { id: cur.id, role: 'reasoning', text: '', ts: Date.now(), taskId: metaTaskId } as any]);
          }
          cur.text += delta;
          const cid = cur.id;
          setMessages((prev) => prev.map((m) => (m.id === cid ? { ...m, text: cur!.text } : m)));
          return;
        }
        if (type === 'agent_reasoning_raw_content') {
          const text = e.msg?.text ?? '';
          if (!text) return;
          const cur = rawReasoningRef.current;
          if (cur) {
            const cid = cur.id;
            setMessages((prev) => prev.map((m) => (m.id === cid ? { ...m, text } : m)));
            rawReasoningRef.current = null;
          } else {
            setMessages((prev) => [...prev, { id: `raw_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'reasoning', text, ts: Date.now(), taskId: metaTaskId } as any]);
          }
          return;
        }
        if (type === 'agent_reasoning_raw_content_delta') {
          const delta = e.msg?.delta ?? '';
          if (!delta) return;
          let cur = rawReasoningRef.current;
          if (!cur) {
            cur = { id: `raw_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, text: '' };
            rawReasoningRef.current = cur;
            setMessages((prev) => [...prev, { id: cur.id, role: 'reasoning', text: '', ts: Date.now(), taskId: metaTaskId } as any]);
          }
          cur.text += delta;
          const cid = cur.id;
          setMessages((prev) => prev.map((m) => (m.id === cid ? { ...m, text: cur!.text } : m)));
          return;
        }
        if (type === 'agent_reasoning_section_break') {
          // Add a subtle separator system message when a new section starts
          setMessages((prev) => [...prev, { id: `sec_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text: '--- Reasoning section ---', ts: Date.now() } as any]);
          return;
        }
        if (type === 'plan_update') {
          try {
            const payload = e.msg || {};
            const explanation: string | undefined = payload.explanation || undefined;
            const items: Array<{ step: string; status: 'pending' | 'in_progress' | 'completed' }> = Array.isArray(payload.plan)
              ? payload.plan.map((it: any) => ({
                  step: String(it.step || ''),
                  status: (String(it.status || 'pending').toLowerCase().replace('-', '_') as any) || 'pending',
                }))
              : [];
            setPlan({ explanation: explanation ?? undefined, plan: items });
            if (metaTaskId) {
              setPlansByTask((prev) => ({ ...prev, [metaTaskId]: { explanation: explanation ?? undefined, plan: items } }));
            }
          } catch {}
          return;
        }
        if (type === 'token_count') {
          const tu = e.msg || {};
          setTokenUsage((prev) => ({
            input_tokens: tu.input_tokens ?? prev?.input_tokens ?? 0,
            cached_input_tokens: tu.cached_input_tokens ?? prev?.cached_input_tokens,
            output_tokens: tu.output_tokens ?? prev?.output_tokens ?? 0,
            reasoning_output_tokens: tu.reasoning_output_tokens ?? prev?.reasoning_output_tokens,
            total_tokens: tu.total_tokens ?? prev?.total_tokens ?? 0,
            context_window: prev?.context_window,
          }));
          return;
        }
        if (type === 'stream_error') {
          const msg = e.msg?.message || 'model stream error';
          setLogs((prev) => [...prev.slice(-400), `STREAM ERROR: ${msg}`]);
          setMessages((prev) => {
            const text = `Stream error: ${msg}`;
            const last = prev[prev.length - 1];
            if (last && last.role === 'system' && last.text === text) return prev;
            return [...prev, { id: `sys_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any];
          });
          return;
        }
        if (type === 'background_event') {
          const msg = e.msg?.message || '';
          if (!msg) return;
          setMessages((prev) => {
            const text = `Background: ${msg}`;
            return [...prev, { id: `bg_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any];
          });
          return;
        }
        if (type === 'turn_diff') {
          const diff = e.msg?.unified_diff || '';
          setTurnDiff(diff || null);
          return;
        }
        if (type === 'list_custom_prompts_response') {
          const cps = Array.isArray(e.msg?.custom_prompts) ? e.msg.custom_prompts : [];
          setCustomPrompts(cps.map((p: any) => ({ name: String(p.name||''), path: String(p.path||''), content: String(p.content||'') })));
          const names = cps.map((p: any) => p?.name || '').filter(Boolean).join(', ');
          const text = names ? `Custom prompts available: ${names}` : 'Custom prompts list received';
          setMessages((prev) => [...prev, { id: `cp_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any]);
          return;
        }
        if (type === 'session_configured') {
          const model = e.msg?.model || '';
          setMessages((prev) => { const last = prev[prev.length-1]; const text = `Connected. Model: ${model}`; if (last && last.role==='system' && last.text===text) return prev; return [...prev, { id: `sys_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any]; });
          return;
        }
        if (type === 'task_started') {
          const cw = e.msg?.model_context_window;
          if (cw) setTokenUsage((prev) => ({ ...(prev || { input_tokens:0, output_tokens:0, total_tokens:0 }), context_window: cw }));
          setMessages((prev) => { const last = prev[prev.length-1]; const text = 'Task started'; if (last && last.role==='system' && last.text===text) return prev; return [...prev, { id: `sys_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any]; });
          return;
        }
        if (type === 'task_complete') {
          setMessages((prev) => { const last = prev[prev.length-1]; const text = 'Task complete.'; if (last && last.role==='system' && last.text===text) return prev; return [...prev, { id: `sys_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any]; });
          return;
        }
        if (type === 'mcp_tool_call_begin') {
          const name = e.msg?.tool || e.msg?.name || 'tool';
          const call_id = e.msg?.call_id || e.id || `mcp_${Date.now()}`;
          setToolCalls((prev) => [{ call_id, kind: 'mcp', name, status: 'running', started_at: Date.now(), stdout: '', stderr: '', task_id: metaTaskId }, ...prev]);
          return;
        }
        if (type === 'mcp_tool_call_end') {
          const name = e.msg?.tool || e.msg?.name || 'tool';
          const call_id = e.msg?.call_id || e.id || '';
          setToolCalls((prev) => prev.map(tc => tc.call_id === call_id ? { ...tc, status: 'done', ended_at: Date.now() } : tc));
          return;
        }
        if (type === 'exec_command_begin') {
          const cmd = (e.msg?.command || []).join(' ');
          const cwd = e.msg?.cwd || '';
          const call_id = e.msg?.call_id || e.id || `exec_${Date.now()}`;
          setToolCalls((prev) => [{ call_id, kind: 'exec', command: e.msg?.command || [], cwd, status: 'running', started_at: Date.now(), stdout: '', stderr: '', task_id: metaTaskId }, ...prev]);
          return;
        }
        if (type === 'exec_command_output_delta') {
          const call_id = e.msg?.call_id || '';
          const stream = e.msg?.stream || 'stdout';
          const chunk = e.msg?.chunk;
          let text = '';
          try {
            if (typeof chunk === 'string') {
              const bin = atob(chunk);
              const bytes = new Uint8Array(bin.length);
              for (let i=0;i<bin.length;i++) bytes[i] = bin.charCodeAt(i);
              text = new TextDecoder('utf-8', { fatal: false }).decode(bytes);
            }
          } catch { text = ''; }
          if (text) {
            setToolCalls((prev) => prev.map(tc => tc.call_id === call_id ? { ...tc, stdout: stream === 'stdout' ? (tc.stdout + text) : tc.stdout, stderr: stream === 'stderr' ? (tc.stderr + text) : tc.stderr } : tc));
          }
          return;
        }
        if (type === 'exec_command_end') {
          const code = e.msg?.exit_code;
          const out = e.msg?.formatted_output || e.msg?.stdout || '';
          const call_id = e.msg?.call_id || e.id || '';
          setToolCalls((prev) => prev.map(tc => tc.call_id === call_id ? { ...tc, status: 'done', ended_at: Date.now(), exit_code: code, formatted_output: out, stdout: tc.stdout || (e.msg?.stdout || ''), stderr: tc.stderr || (e.msg?.stderr || '') } : tc));
          return;
        }
        if (type === 'web_search_begin') {
          setMessages((prev) => { const text = `web search: ${e.msg?.query || ''}`; const last = prev[prev.length-1]; if (last && last.role==='system' && last.text===text) return prev; return [...prev, { id: `sys_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any]; });
          return;
        }
        if (type === 'web_search_end') {
          setMessages((prev) => { const text = 'web search done'; const last = prev[prev.length-1]; if (last && last.role==='system' && last.text===text) return prev; return [...prev, { id: `sys_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any]; });
          return;
        }
        if (type === 'patch_apply_begin') {
          setMessages((prev) => { const text = 'Applying patch...'; const last = prev[prev.length-1]; if (last && last.role==='system' && last.text===text) return prev; return [...prev, { id: `sys_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any]; });
          return;
        }
        if (type === 'patch_apply_end') {
          const ok = e.msg?.success ? 'success' : 'failed';
          setMessages((prev) => { const text = `Patch apply ${ok}`; const last = prev[prev.length-1]; if (last && last.role==='system' && last.text===text) return prev; return [...prev, { id: `sys_${Date.now()}_${Math.random().toString(36).slice(2,6)}`, role: 'system', text, ts: Date.now() } as any]; });
          return;
        }
        if (type === 'conversation_history') {
          try {
            const entries = e.msg?.entries || [];
            const hist: { id: string; role: 'assistant' | 'reasoning' | 'system' | 'tool' | 'user'; text: string }[] = [];
            for (const it of entries) {
              const t = it?.type || '';
              if (t === 'message') {
                const role = (it.role === 'assistant' ? 'assistant' : it.role === 'user' ? 'user' : 'system');
                const parts = Array.isArray(it.content) ? it.content : [];
                const txt = parts.map((p: any) => p.text || '').join('\n');
                hist.push({ id: `hist_${hist.length}`, role, text: txt });
              } else if (t === 'reasoning') {
                const sum = Array.isArray(it.summary) ? it.summary : [];
                const txt = sum.map((s: any) => s.text || '').join('\n');
                if (txt) hist.push({ id: `hist_${hist.length}`, role: 'reasoning', text: txt });
              }
            }
            setMessages((prev) => [...hist, ...prev]);
            setMessages((prev) => [{ id: `sys_${Date.now()}`, role: 'system', text: `Loaded ${hist.length} history entries` }, ...prev]);
          } catch {}
          return;
        }
        if (type === 'mcp_list_tools_response') {
          const tools = e.msg?.tools || {};
          setMcpTools(tools || {});
          return;
        }
        if (type === 'exec_approval_request' || type === 'execApprovalRequest') {
          setExecApprovalRequest({
            id: e.id || '',
            call_id: e.msg?.call_id || e.call_id || '',
            command: e.msg?.command || e.command || [],
            cwd: (e.msg?.cwd || e.cwd || '').toString(),
            reason: e.msg?.reason || e.reason,
          });
        } else if (type === 'apply_patch_approval_request' || type === 'applyPatchApprovalRequest') {
          const changes = e.msg?.changes || e.changes || {};
          const normalized: PatchApprovalRequest['changes'] = {};
          Object.keys(changes || {}).forEach((k) => {
            const ch = changes[k];
            if (typeof ch === 'string') return; // defensive
            if (ch?.Add) normalized[k] = { type: 'add', content: ch.Add?.content };
            else if (ch?.Delete) normalized[k] = { type: 'delete' };
            else if (ch?.Update) normalized[k] = { type: 'update', unified_diff: ch.Update?.unified_diff, move_path: ch.Update?.move_path };
          });
          setPatchApprovalRequest({
            id: e.id || '',
            call_id: e.msg?.call_id || e.call_id || '',
            changes: normalized,
            reason: e.msg?.reason || e.reason,
            grant_root: e.msg?.grant_root || e.grant_root,
          });
        }
      })
    );
    unsub.current.push(window.aiw.onError((m) => {
      setLastError(m);
      setLogs((prev) => [...prev.slice(-400), `ERROR: ${m}`]);
      try {
        const re1 = /MCP client for `([^`]+)` failed to start: (.*)/i;
        const re2 = /MCP client for '([^']+)' failed to start: (.*)/i;
        const re3 = /failed to start mcp server[:\s]+(\w+).*?:\s+(.*)/i;
        const m1 = re1.exec(m) || re2.exec(m) || re3.exec(m);
        if (m1) {
          const name = m1[1]; const msg = m1[2] || m;
          setServerErrors((prev) => ({ ...prev, [name]: msg }));
        }
      } catch {}
      setMessages((prev)=>[...prev,{id:`err_${Date.now()}`, role:'system', text:`Error: ${m}` }]);
    }));

    // start backend on mount (with stored codexPath if available)
    const saved = localStorage.getItem('codexPath') || undefined;
    window.aiw.start(saved ? { codexPath: saved } : undefined).catch(() => {});

    return () => {
      unsub.current.forEach((off) => off());
      unsub.current = [];
    };
  }, []);

  // Auto-retry start if not connected
  useEffect(() => {
    let timer: any;
    let lastAttempt = 0;
    function maybeStart() {
      const now = Date.now();
      if ((status === 'idle' || status === 'disconnected' || status === 'error') && now - lastAttempt > 15000) {
        lastAttempt = now;
        const saved = localStorage.getItem('codexPath') || undefined;
        window.aiw.start(saved ? { codexPath: saved } : undefined).catch(() => {});
      }
    }
    timer = setInterval(maybeStart, 5000);
    return () => clearInterval(timer);
  }, [status]);

  const api = useMemo<BackendContextType>(() => ({
    status,
    logs,
    lastEvent,
    messages,
    draftMessage,
    setDraftMessage,
    chatParams,
    setChatParams,
    tokenUsage,
    toolCalls,
    mcpServers,
    serverErrors,
    plan,
    plansByTask,
    turnDiff,
    customPrompts,
    refreshCustomPrompts: async () => window.aiw.listCustomPrompts(),
    // Agents proto
    agents,
    agentRuns,
    listAgents: async () => window.aiw.listAgents(),
    agentsReload: async () => window.aiw.agentsReload(),
    startAgent: async (id: string, input?: string, context?: any) => window.aiw.startAgent(id, input, context),
    agentStatus: async (taskId: string) => window.aiw.agentStatus(taskId),
    agentCancel: async (taskId: string) => window.aiw.agentCancel(taskId),
    start: (opts) => window.aiw.start(opts),
    stop: () => window.aiw.stop(),
    login: (apiKey?: string) => window.aiw.login(apiKey),
    userTurn: async (text: string, params = {}) => {
      setMessages((prev) => [...prev, { id: `user_${Date.now()}`, role: 'user', text, ts: Date.now() } as any]);
      const merged = {
        model: chatParams.model,
        approval_policy: chatParams.approval_policy,
        sandbox_mode: chatParams.sandbox_mode,
        effort: chatParams.effort,
        summary: chatParams.summary,
        cwd: chatParams.cwd,
        ...params,
      } as any;
      return window.aiw.userTurn({ text, ...merged });
    },
    interrupt: () => window.aiw.interrupt(),
    execApproval: (id, decision) => window.aiw.execApproval(id, decision),
    patchApproval: (id, decision) => window.aiw.patchApproval(id, decision),
    setCodexPath: async (p: string) => {
      const ok = await window.aiw.setCodexPath(p);
      if (ok) localStorage.setItem('codexPath', p);
      return ok;
    },
    execApprovalRequest,
    patchApprovalRequest,
    clearApprovals: () => {
      setExecApprovalRequest(null);
      setPatchApprovalRequest(null);
    },
    lastError,
    getHistory: async () => window.aiw.getHistory(),
    mcpTools,
    refreshMcpTools: async () => window.aiw.listMcpTools(),
    refreshMcpServers: async () => {
      const cfg = await window.aiw.getMcpServers();
      setMcpServers(cfg || {});
      return cfg;
    },
  }), [status, logs, lastEvent, execApprovalRequest, patchApprovalRequest, chatParams, draftMessage, tokenUsage, toolCalls, mcpTools, mcpServers, serverErrors, plan, plansByTask, turnDiff, customPrompts, agents, agentRuns]);

  return <BackendContext.Provider value={api}>{children}</BackendContext.Provider>;
};

