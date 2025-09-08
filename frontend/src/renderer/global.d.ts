export { };

declare global {
  interface Window {
    aiw: {
      start: (opts?: { codexPath?: string; profile?: string }) => Promise<void>;
      stop: () => Promise<void>;
      login: (apiKey?: string) => Promise<boolean>;
      userTurn: (params: {
        text: string;
        cwd?: string;
        approval_policy?: 'untrusted' | 'on-failure' | 'on-request' | 'never';
        sandbox_mode?: 'read-only' | 'workspace-write' | 'danger-full-access';
        model?: string;
        effort?: 'minimal' | 'low' | 'medium' | 'high';
        summary?: 'auto' | 'concise' | 'detailed' | 'none';
      }) => Promise<boolean>;
      interrupt: () => Promise<boolean>;
      execApproval: (id: string, decision: string) => Promise<boolean>;
      patchApproval: (id: string, decision: string) => Promise<boolean>;
      setCodexPath: (codexPath: string) => Promise<boolean>;
      getHistory: () => Promise<boolean>;
      listMcpTools: () => Promise<boolean>;
      upsertMcpServer: (server: { name: string; command: string; args?: string[]; env?: Record<string,string>}) => Promise<boolean>;
      removeMcpServer: (name: string) => Promise<boolean>;
      restart: () => Promise<void>;
      getMcpServers: () => Promise<Record<string, { name: string; command: string; args?: string[]; env?: Record<string,string> }>>;
      onEvent: (cb: (e: any) => void) => () => void;
      onStatus: (cb: (s: string) => void) => () => void;
      onLog: (cb: (m: string) => void) => () => void;
      onError: (cb: (m: string) => void) => () => void;
    };
  }
}
