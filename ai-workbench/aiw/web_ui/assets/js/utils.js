window.App = window.App || {};
(function () {
  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => Array.from(r.querySelectorAll(s));
  const log = (m) => {
    const el = qs('#logs');
    if (!el) return;
    el.textContent += `[${new Date().toLocaleTimeString()}] ${m}\n`;
    el.scrollTop = el.scrollHeight;
  };
  const status = (s) => {
    const dot = qs('#statusDot');
    const txt = qs('#statusText');
    if (txt) txt.textContent = s[0].toUpperCase() + s.slice(1);
    if (dot) {
      dot.className = 'status-dot';
      dot.classList.remove('status-connected','status-connecting','status-disconnected');
      dot.classList.add(s === 'connected' ? 'status-connected' : s === 'connecting' ? 'status-connecting' : 'status-disconnected');
    }
    // Toggle start/stop buttons
    const start = qs('#startBtn'); const stop = qs('#stopBtn');
    // Allow Start unless already connected; Stop only when connected
    if (start) { start.disabled = (s === 'connected'); start.classList.toggle('opacity-50', start.disabled); start.classList.toggle('cursor-not-allowed', start.disabled); }
    if (stop) { stop.disabled = (s !== 'connected'); stop.classList.toggle('opacity-50', stop.disabled); stop.classList.toggle('cursor-not-allowed', stop.disabled); }
  };

  const ui = {
    addMsg(role, text) {
      const wrap = qs('#chat');
      if (!wrap) return;
      if (role === 'assistant' && App._lastAssistant?.isLive) {
        App._lastAssistant.body.textContent += text;
        wrap.scrollTop = wrap.scrollHeight;
        return;
      }
      const row = document.createElement('div');
      row.className = 'flex gap-2';
      const bubble = document.createElement('div');
      bubble.className = 'rounded px-3 py-2 max-w-[90%] whitespace-pre-wrap ' + (role === 'user' ? 'bg-surface-2' : 'bg-surface-2');
      bubble.textContent = text;
      row.appendChild(bubble);
      wrap.appendChild(row);
      wrap.scrollTop = wrap.scrollHeight;
      App._lastAssistant = role === 'assistant' ? { body: bubble, isLive: true } : null;
    },
    endAssistantLive() { if (App._lastAssistant) App._lastAssistant.isLive = false; },
    setDiff(diff) { const el = qs('#diffView'); if (el) el.textContent = diff || ''; },
    appendTerminal(text) {
      const term = qs('#terminal'); if (!term) return;
      term.textContent += text; term.scrollTop = term.scrollHeight;
    },
    show(id) { const el = qs(id); if (!el) return; el.classList.remove('hidden'); el.classList.add('flex'); },
    hide(id) { const el = qs(id); if (!el) return; el.classList.add('hidden'); el.classList.remove('flex'); },
  };

  // Lightweight toast helper using #toasts container
  function toast(message, opts) {
    try {
      const box = qs('#toasts'); if (!box) { log(message); return; }
      const type = (opts && opts.type) || 'info';
      const timeout = (opts && opts.timeout) || 3000;
      const div = document.createElement('div');
      div.className = `text-inverse text-sm rounded shadow px-3 py-2`;
      // Theme-based background from CSS variables
      const root = getComputedStyle(document.documentElement);
      if (type === 'error') div.style.background = root.getPropertyValue('--danger');
      else if (type === 'success') div.style.background = root.getPropertyValue('--success');
      else div.style.background = root.getPropertyValue('--primary');
      div.textContent = String(message);
      box.appendChild(div);
      setTimeout(() => { try { div.remove(); } catch {} }, timeout);
    } catch { /* noop */ }
  }

  // Auto-contrast for text on colored surfaces using WCAG
  function parseRGB(str) {
    try {
      let s = String(str).trim();
      if (s.startsWith('#')) {
        const hex = s.slice(1);
        const v = hex.length === 3 ? hex.split('').map(h=>h+h).join('') : hex;
        const r = parseInt(v.slice(0,2),16), g = parseInt(v.slice(2,4),16), b = parseInt(v.slice(4,6),16);
        return { r, g, b };
      }
      const m = s.match(/rgba?\(([^)]+)\)/);
      if (!m) return null; const parts = m[1].split(',').map(x=>parseFloat(x.trim()));
      return { r: parts[0], g: parts[1], b: parts[2] };
    } catch { return null; }
  }
  function luminance({r,g,b}) {
    const srgb = [r,g,b].map(v=>{
      v/=255; return v<=0.03928? v/12.92 : Math.pow((v+0.055)/1.055,2.4);
    });
    return 0.2126*srgb[0]+0.7152*srgb[1]+0.0722*srgb[2];
  }
  function contrast(bg, fg) {
    const L1 = luminance(bg), L2 = luminance(fg);
    const light = Math.max(L1,L2), dark = Math.min(L1,L2);
    return (light + 0.05)/(dark + 0.05);
  }
  function pickOnColor(bgStr) {
    const bg = parseRGB(bgStr) || { r:80,g:80,b:80 };
    const white = { r:255,g:255,b:255 }, black = { r:0,g:0,b:0 };
    const cw = contrast(bg, white), cb = contrast(bg, black);
    return cw >= cb ? '#ffffff' : '#000000';
  }
  function applyAutoContrast() {
    try {
      const root = getComputedStyle(document.documentElement);
      const setVar = (k,v)=> document.documentElement.style.setProperty(k, v);
      const prim = root.getPropertyValue('--primary');
      const succ = root.getPropertyValue('--success');
      const warn = root.getPropertyValue('--warning');
      const dang = root.getPropertyValue('--danger');
      setVar('--on-primary', pickOnColor(prim));
      setVar('--on-success', pickOnColor(succ));
      setVar('--on-warning', pickOnColor(warn));
      setVar('--on-danger', pickOnColor(dang));
      setVar('--on-accent', pickOnColor(prim));
    } catch { /* noop */ }
  }

  // Expose helpers
  App.applyAutoContrast = applyAutoContrast;

  App.qs = qs; App.qsa = qsa; App.log = log; App.status = status; App.ui = ui; App.toast = toast; App.state = { termByCall: {} };
  // Run once on load
  try { applyAutoContrast(); } catch {}
})();






