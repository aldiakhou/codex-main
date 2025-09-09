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
      listCustomPrompts: () => Promise<boolean>;
      upsertMcpServer: (server: { name: string; command: string; args?: string[]; env?: Record<string,string>}) => Promise<boolean>;
      removeMcpServer: (name: string) => Promise<boolean>;
      restart: () => Promise<void>;
      getMcpServers: () => Promise<Record<string, { name: string; command: string; args?: string[]; env?: Record<string,string> }>>;
      readCodexConfig: () => Promise<{ ok: boolean; config?: any; raw?: string; path: string; error?: string }>;
      saveCodexConfig: (cfg: any) => Promise<{ ok: boolean; path: string; error?: string }>;
      onEvent: (cb: (e: any) => void) => () => void;
      onStatus: (cb: (s: string) => void) => () => void;
      onLog: (cb: (m: string) => void) => () => void;
      onError: (cb: (m: string) => void) => () => void;
    };
    fsapi: {
      list: (dir: string) => Promise<{ ok: boolean; entries?: Array<{ name: string; path: string; isDir: boolean }>; error?: string }>;
      read: (filePath: string) => Promise<{ ok: boolean; data?: string; error?: string }>;
      readBase64: (filePath: string) => Promise<{ ok: boolean; base64?: string; error?: string }>;
      stat: (p: string) => Promise<{ ok: boolean; stat?: { size: number; mtimeMs: number; isDir: boolean }; error?: string }>;
      chooseDir: () => Promise<{ ok: boolean; path?: string; canceled?: boolean }>;
      createFile: (filePath: string, content?: string) => Promise<{ ok: boolean; error?: string }>;
      createDir: (dirPath: string) => Promise<{ ok: boolean; error?: string }>;
      renamePath: (oldPath: string, newPath: string) => Promise<{ ok: boolean; error?: string }>;
      deletePath: (p: string, root: string) => Promise<{ ok: boolean; error?: string }>;
      undo: () => Promise<{ ok: boolean; error?: string }>;
    };
    idx: {
      build: (dir: string) => Promise<{ ok: boolean; stats?: { files: number; links: number }; error?: string }>;
      backlinks: (filePath: string) => Promise<{ ok: boolean; backlinks?: Array<{ from: string; anchor?: string }>; error?: string }>;
      graph: () => Promise<{ ok: boolean; nodes?: Array<{ path: string; name: string }>; edges?: Array<{ from: string; to: string; anchor?: string }>; root?: string; error?: string }>;
      watchStart: (dir: string) => Promise<{ ok: boolean }>;
      watchStop: () => Promise<{ ok: boolean }>;
      onUpdate: (cb: (payload: { stats: { files: number; links: number } }) => void) => () => void;
    };
  }
}
