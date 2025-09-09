import React, { useEffect, useRef, useState } from 'react';
import cytoscape, { ElementsDefinition } from 'cytoscape';

const GraphWorkspace: React.FC = () => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [status, setStatus] = useState<string>('');

  const loadGraph = async () => {
    setStatus('Loading graph...');
    const res = await window.idx.graph();
    if (!res.ok) { setStatus(res.error || 'Graph load failed'); return; }
    const el: ElementsDefinition = {
      nodes: (res.nodes || []).map((n) => ({ data: { id: n.path, label: n.name } })),
      edges: (res.edges || []).map((e, i) => ({ data: { id: 'e'+i, source: e.from, target: e.to } })),
    };
    if (!containerRef.current) return;
    if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; }
    const cy = cytoscape({
      container: containerRef.current,
      elements: el,
      style: [
        { selector: 'node', style: { 'background-color': '#7aa2f7', 'label': 'data(label)', 'font-size': 8, 'text-wrap': 'wrap', 'text-max-width': 120, 'color': '#e0e0e0' } },
        { selector: 'edge', style: { 'line-color': '#565f89', 'width': 1, 'target-arrow-color': '#565f89', 'target-arrow-shape': 'triangle' } },
        { selector: ':selected', style: { 'background-color': '#9ece6a', 'line-color': '#9ece6a', 'target-arrow-color': '#9ece6a' } },
      ],
      layout: { name: 'cose', animate: true, fit: true },
    });
    cy.on('tap', 'node', async (evt) => {
      const p = evt.target.id();
      // Highlight neighbors
      cy.elements().removeClass('faded');
      const neighborhood = evt.target.closedNeighborhood();
      cy.elements().difference(neighborhood).addClass('faded');
      setStatus(p);
      try {
        localStorage.setItem('files:openPath', p);
        window.dispatchEvent(new Event('open-file-in-files'));
      } catch {}
    });
    cy.style().selector('.faded').style({ opacity: 0.2 }).update();
    cyRef.current = cy;
    setStatus(`Nodes: ${(res.nodes||[]).length}, edges: ${(res.edges||[]).length}`);
  };

  useEffect(() => { loadGraph(); }, []);

  return (
    <div className="flex-1 flex flex-col p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold">Graph</h1>
        <div className="flex gap-2 text-sm">
          <button className="px-3 py-1 rounded bg-[var(--bg-tertiary)] border border-[var(--border)]" onClick={loadGraph}>Refresh</button>
          <div className="text-[var(--text-tertiary)]">{status}</div>
        </div>
      </div>
      <div ref={containerRef} className="flex-1 border border-[var(--border)] rounded bg-[var(--bg-secondary)]" />
    </div>
  );
};

export default GraphWorkspace;
