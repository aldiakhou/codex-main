import { useEffect, useState } from 'react';

export type WorkspaceId =
  | 'chat'
  | 'dashboard'
  | 'agents'
  | 'code'
  | 'files'
  | 'planner'
  | 'terminal'
  | 'tools'
  | 'graph'
  | 'settings';

export function useWorkspaceManager(initial: WorkspaceId = 'dashboard') {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>(() => {
    const last = window.localStorage.getItem('lastWorkspace') as WorkspaceId | null;
    return (last as WorkspaceId) || initial;
  });

  useEffect(() => {
    window.localStorage.setItem('lastWorkspace', activeWorkspace);
  }, [activeWorkspace]);

  useEffect(() => {
    const handler = () => setActiveWorkspace('files');
    window.addEventListener('open-file-in-files', handler);
    return () => window.removeEventListener('open-file-in-files', handler);
  }, []);

  return { activeWorkspace, setActiveWorkspace } as const;
}
