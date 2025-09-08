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
  messages: { id: string; role: 'assistant' | 'reasoning' | 'system' | 'tool' | 'user'; text: string }[];
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
  getHistory: () => Promise<boolean>;
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
        // Agent message streaming
        if (type === 'agent_message') {
          const text = e.msg?.message ?? '';
          const id = e.id || `msg_${Date.now()}`;
          streamingAssistantRef.current = null;
          if (text) setMessages((prev) => [...prev, { id, role: 'assistant', text }]);
          return;
        }
        if (type === 'agent_message_delta') {
          const delta = e.msg?.delta ?? '';
          if (!delta) return;
          let cur = streamingAssistantRef.current;
          if (!cur) {
            cur = { id: e.id || `delta_${Date.now()}`, text: '' };
            streamingAssistantRef.current = cur;
            setMessages((prev) => [...prev, { id: cur.id, role: 'assistant', text: '' }]);
          }
          cur.text += delta;
          const cid = cur.id;
          setMessages((prev) => prev.map((m) => (m.id === cid ? { ...m, text: cur!.text } : m)));
          return;
        }
        if (type === 'agent_reasoning') {
          const text = e.msg?.text ?? '';
          if (text) setMessages((prev) => [...prev, { id: e.id || `rsn_${Date.now()}`, role: 'reasoning', text }]);
          return;
        }
        if (type === 'agent_reasoning_delta') {
          const delta = e.msg?.delta ?? e.msg?.text ?? '';
          if (!delta) return;
          let cur = streamingReasoningRef.current;
          if (!cur) {
            cur = { id: e.id || `rsn_${Date.now()}`, text: '' };
            streamingReasoningRef.current = cur;
            setMessages((prev) => [...prev, { id: cur.id, role: 'reasoning', text: '' }]);
          }
          cur.text += delta;
          const cid = cur.id;
          setMessages((prev) => prev.map((m) => (m.id === cid ? { ...m, text: cur!.text } : m)));
          return;
        }
        if (type === 'session_configured') {
          const model = e.msg?.model || '';
          setMessages((prev) => [...prev, { id: e.id || `sys_${Date.now()}`, role: 'system', text: `Connected. Model: ${model}` }]);
          return;
        }
        if (type === 'task_started') {
          setMessages((prev) => [...prev, { id: e.id || `sys_${Date.now()}`, role: 'system', text: `Task started` }]);
          return;
        }
        if (type === 'task_complete') {
          const last = e.msg?.last_agent_message ? `: ${e.msg.last_agent_message}` : '';
          setMessages((prev) => [...prev, { id: e.id || `sys_${Date.now()}`, role: 'system', text: `Task complete${last}` }]);
          return;
        }
        if (type === 'mcp_tool_call_begin') {
          const name = e.msg?.tool || e.msg?.name || 'tool';
          setMessages((prev) => [...prev, { id: e.id || `tool_${Date.now()}`, role: 'tool', text: `Tool call begin: ${name}` }]);
          return;
        }
        if (type === 'mcp_tool_call_end') {
          const name = e.msg?.tool || e.msg?.name || 'tool';
          setMessages((prev) => [...prev, { id: e.id || `tool_${Date.now()}`, role: 'tool', text: `Tool call end: ${name}` }]);
          return;
        }
        if (type === 'exec_command_begin') {
          const cmd = (e.msg?.command || []).join(' ');
          const cwd = e.msg?.cwd || '';
          setMessages((prev) => [...prev, { id: e.id || `tool_${Date.now()}`, role: 'tool', text: `exec: ${cmd}\ncwd: ${cwd}` }]);
          return;
        }
        if (type === 'exec_command_end') {
          const code = e.msg?.exit_code;
          const out = e.msg?.formatted_output || e.msg?.stdout || '';
          setMessages((prev) => [...prev, { id: e.id || `tool_${Date.now()}`, role: 'tool', text: `exit ${code}\n${out}` }]);
          return;
        }
        if (type === 'web_search_begin') {
          setMessages((prev) => [...prev, { id: e.id || `sys_${Date.now()}`, role: 'system', text: `web search: ${e.msg?.query || ''}` }]);
          return;
        }
        if (type === 'web_search_end') {
          setMessages((prev) => [...prev, { id: e.id || `sys_${Date.now()}`, role: 'system', text: `web search done` }]);
          return;
        }
        if (type === 'patch_apply_begin') {
          setMessages((prev) => [...prev, { id: e.id || `sys_${Date.now()}`, role: 'system', text: `Applying patch...` }]);
          return;
        }
        if (type === 'patch_apply_end') {
          const ok = e.msg?.success ? 'success' : 'failed';
          setMessages((prev) => [...prev, { id: e.id || `sys_${Date.now()}`, role: 'system', text: `Patch apply ${ok}` }]);
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
    unsub.current.push(window.aiw.onError((m) => { setLastError(m); setLogs((prev) => [...prev.slice(-400), `ERROR: ${m}`]); setMessages((prev)=>[...prev,{id:`err_${Date.now()}`, role:'system', text:`Error: ${m}` }]); }));

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
    chatParams,
    setChatParams,
    start: (opts) => window.aiw.start(opts),
    stop: () => window.aiw.stop(),
    login: (apiKey?: string) => window.aiw.login(apiKey),
    userTurn: async (text: string, params = {}) => {
      setMessages((prev) => [...prev, { id: `user_${Date.now()}`, role: 'user', text }]);
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
  }), [status, logs, lastEvent, execApprovalRequest, patchApprovalRequest, chatParams]);

  return <BackendContext.Provider value={api}>{children}</BackendContext.Provider>;
};
