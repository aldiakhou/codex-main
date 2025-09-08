(function(){
  if (window.lucide && typeof window.lucide.createIcons === 'function') return;
  function svg(tag, attrs){ const el = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const k in attrs||{}) el.setAttribute(k, attrs[k]); return el; }
  const paths = {
    play: ['M5 3l14 9-14 9z'],
    square: ['M3 3h18v18H3z'],
    'log-in': ['M15 12H3','M10 7l5 5-5 5','M21 3v18'],
    sun: ['M12 4V2','M12 22v-2','M4.22 4.22l1.42 1.42','M18.36 18.36l1.42 1.42','M2 12h2','M20 12h2','M4.22 19.78l1.42-1.42','M18.36 5.64l1.42-1.42','M12 6a6 6 0 1 0 0 12 6 6 0 0 0 0-12z'],
    settings: ['M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z','M21 12l-2 1','M3 12l2 1','M19.4 7.34l-1.45.84','M5.05 17.66l1.45-.84','M19.4 16.66l-1.45-.84','M5.05 6.34l1.45.84'],
    minus: ['M5 12h14'],
    x: ['M18 6 6 18','M6 6l12 12'],
    folder: ['M3 7h5l2 2h11v10H3z'],
    file: ['M14 2H6a2 2 0 0 0-2 2v16h12V8z','M14 2v6h6'],
    'rotate-cw': ['M23 4v6h-6','M22 10a8 8 0 1 1-2-5.3'],
    bold: ['M6 4h7a4 4 0 0 1 0 8H6z','M6 12h8a4 4 0 0 1 0 8H6z'],
    italic: ['M19 4h-9','M14 20H5','M15 4L9 20'],
    'code-2': ['M18 16l4-4-4-4','M6 8l-4 4 4 4','M14 4l-4 16'],
    list: ['M8 6h13','M8 12h13','M8 18h13','M3 6h.01','M3 12h.01','M3 18h.01'],
    cpu: ['M4 9h16v6H4z','M9 1v3','M15 1v3','M9 24v-3','M15 24v-3','M1 9h3','M1 15h3','M24 9h-3','M24 15h-3'],
    activity: ['M22 12h-4l-3 7L9 5l-3 7H2'],
    'file-text': ['M14 2v6h6','M14 2H6a2 2 0 0 0-2 2v16h12V8z','M9 13h6','M9 17h6','M9 9h2'],
    cog: ['M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z','M2 12h3','M19 12h3','M12 2v3','M12 19v3','M4.9 4.9l2.1 2.1','M16.9 16.9l2.1 2.1','M4.9 19.1l2.1-2.1','M16.9 7.1l2.1-2.1'],
    send: ['M22 2L11 13','M22 2l-7 20-4-9-9-4z']
  };
  function renderIcon(name, size){
    const svgEl = svg('svg', { width: size||'16', height: size||'16', viewBox:'0 0 24 24', fill:'none', stroke:'currentColor', 'stroke-width':'2', 'stroke-linecap':'round', 'stroke-linejoin':'round', 'aria-hidden':'true' });
    const d = paths[name] || paths.square;
    d.forEach(p => svgEl.appendChild(svg(p.startsWith('M')||p.startsWith('m')?'path':'path', { d: p })));
    return svgEl;
  }
  window.lucide = {
    createIcons: function(){
      const nodes = document.querySelectorAll('[data-lucide]');
      nodes.forEach(node => {
        // prevent double-rendering
        if (node.__lucideRendered) return;
        const name = (node.getAttribute('data-lucide')||'').trim();
        const size = (node.getAttribute('data-size')||'16');
        const icon = renderIcon(name, size);
        // inherit classes from <i> to svg for sizing
        icon.setAttribute('class', (node.getAttribute('class')||''));
        node.replaceWith(icon);
        icon.__lucideRendered = true;
      });
    }
  };
  // Auto-run once DOM is ready in case consumers forget
  if (document.readyState === 'complete' || document.readyState === 'interactive') setTimeout(()=>window.lucide.createIcons(), 0);
  else document.addEventListener('DOMContentLoaded', ()=> window.lucide.createIcons());
})();
