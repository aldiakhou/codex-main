import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))

from mcp_agents_orchestrator.__main__ import BRIDGE, TASKS

def run(agent_id: str, goal: str, params: dict, permission_profile=None, cwd=None, timeout=30):
    ok = BRIDGE.load()
    print('BRIDGE_LOAD_OK:', ok, 'ERR:', BRIDGE.error)
    task = TASKS.create(agent_id, goal, params)
    print('TASK_ID:', task['task_id'])
    BRIDGE.start_task(task['task_id'], agent_id, goal, params, cwd, permission_profile)
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = TASKS.get(task['task_id'])
        print('STATUS:', st.get('status'), 'progress:', len(st.get('progress', [])))
        if st.get('status') in ('completed', 'failed', 'canceled'):
            print('DONE:', st.get('status'))
            print('RESULT:', json.dumps(st.get('result') or {}, ensure_ascii=False)[:400])
            return st
        time.sleep(0.5)
    print('TIMEOUT')
    return TASKS.get(task['task_id'])

if __name__ == '__main__':
    run('web_search', 'Find score', {'query':'senegal vs congo score today','max_results':5},
        permission_profile={'tool_allowlist':['mcp','mcp:stdio:npx']}, cwd=None)

