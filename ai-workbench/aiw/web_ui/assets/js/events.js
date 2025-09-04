window.App = window.App || {};
(function () {
  function decodeChunk(chunk) {
    if (Array.isArray(chunk)) {
      try { return new TextDecoder('utf-8', { fatal: false }).decode(new Uint8Array(chunk)); } catch { return ''; }
    }
    return typeof chunk === 'string' ? chunk : '';
  }

  App.onEvent = function (e) {
    switch (e.type) {
      case 'session_configured':
        App.status('connected');
        App.log(`Session configured. model=${e.model}`);
        break;
      case 'agent_message_delta':
        App.ui.addMsg('assistant', e.delta || '');
        break;
      case 'agent_message':
        App.ui.addMsg('assistant', e.message || '');
        App.ui.endAssistantLive();
        break;
      case 'token_count': {
        const total = e.total_tokens ?? 0;
        const input = (e.input_tokens ?? 0) - (e.cached_input_tokens ?? 0);
        const output = e.output_tokens ?? 0;
        const reasoning = e.reasoning_output_tokens ?? 0;
        const el = App.qs('#tokenInfo');
        if (el) el.textContent = `Tokens: total=${total} input=${input} output=${output}${reasoning ? ` (reasoning ${reasoning})` : ''}`;
        break;
      }
      case 'turn_diff':
        App.ui.setDiff(e.unified_diff || '');
        break;
      case 'exec_command_begin':
        App.state.termByCall[e.call_id] = true; break;
      case 'exec_command_output_delta':
        App.ui.appendTerminal(decodeChunk(e.chunk));
        break;
      case 'exec_approval_request':
        App.qs('#execPreview').textContent = `$ cd ${e.cwd}\n$ ` + (e.command || []).join(' ');
        App._execEventId = e.id; App.ui.show('#execModal');
        break;
      case 'apply_patch_approval_request': {
        let preview = '';
        if (e.changes) {
          Object.entries(e.changes).forEach(([path, change]) => {
            if (change.type === 'add') preview += `=== ${path} (add) ===\n` + (change.content || '') + '\n\n';
            else if (change.type === 'delete') preview += `=== ${path} (delete) ===\n`;
            else if (change.type === 'update') preview += `=== ${path} (update) ===\n` + (change.unified_diff || '') + '\n\n';
          });
        }
        App.qs('#patchPreview').textContent = preview || '(no changes)';
        App._patchEventId = e.id; App.ui.show('#patchModal');
        break; }
      case 'patch_apply_begin':
        App.log('Patch apply started'); break;
      case 'patch_apply_end':
        App.log(`Patch apply ${e.success ? 'succeeded' : 'failed'}`);
        if (e.stdout) App.ui.appendTerminal(e.stdout);
        if (e.stderr) App.ui.appendTerminal(e.stderr);
        break;
      case 'plan_update': {
        const el = App.qs('#plan'); if (el) el.textContent = JSON.stringify(e, null, 2); break; }
      case 'mcp_list_tools_response': {
        const list = App.qs('#mcpTools'); if (!list) break;
        list.innerHTML = '';
        const tools = e.tools ? Object.keys(e.tools) : [];
        tools.sort().forEach(name => {
          const item = document.createElement('div');
          item.className = 'flex items-center justify-between text-sm py-1 border-b last:border-0';
          item.innerHTML = `<div class="truncate pr-2" title="${name}">${name}</div>`+
            `<button class="px-2 py-0.5 bg-gray-100 rounded hover:bg-gray-200" data-tool="${name}">Prompt</button>`;
          item.querySelector('button').onclick = () => {
            const prompt = `Please use the MCP tool \`${name}\` with appropriate parameters to accomplish the task.`;
            App.ui.addMsg('user', prompt);
            App.backend.send_user_turn_json(JSON.stringify({ text: prompt }));
          };
          list.appendChild(item);
        });
        break; }
      case 'conversation_history': {
        const panel = App.qs('#historyPanel'); if (!panel) break;
        panel.textContent = JSON.stringify(e, null, 2);
        break; }
      case 'stream_error': App.log(`Stream error: ${e.message}`); break;
      case 'turn_aborted': App.log('Turn aborted'); break;
      default: break;
    }
  };
})();
