from __future__ import annotations

import json
from html import escape

from .analysis import analyze_impact
from .model import EnterpriseGraph


def render_explorer_html(graph: EnterpriseGraph, *, change_id: str | None = None) -> str:
    highlighted: set[str] = set()
    if change_id:
        highlighted = {node.id for node in analyze_impact(graph, change_id=change_id).impacted}
    payload = {
        "nodes": [node.to_dict() for node in sorted(graph.nodes.values(), key=lambda item: item.id)],
        "edges": [edge.to_dict() for edge in sorted(graph.edges, key=lambda item: (item.source, item.target, item.relation))],
        "highlighted": sorted(highlighted),
        "change": change_id,
    }
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    title = "Enterprise Change Graph" + (f" — {change_id}" if change_id else "")
    return f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>{escape(title)}</title><style>
:root{{font-family:Inter,system-ui,sans-serif;color:#151515;background:#f6f4ef}}body{{margin:0}}header{{padding:24px 28px;border-bottom:1px solid #d8d4ca;background:#fff}}h1{{font-size:22px;margin:0 0 6px}}.meta{{color:#666;font-size:13px}}main{{display:grid;grid-template-columns:minmax(0,1fr) 330px;height:calc(100vh - 90px)}}#canvas{{overflow:auto;padding:20px}}aside{{border-left:1px solid #d8d4ca;background:#fff;padding:18px;overflow:auto}}input,select{{width:100%;box-sizing:border-box;margin:0 0 10px;padding:9px;border:1px solid #bbb;border-radius:6px;background:#fff}}svg{{background:#fff;border:1px solid #d8d4ca;border-radius:8px}}.edge{{stroke:#bbb;stroke-width:1}}.node rect{{fill:#f7f7f7;stroke:#777;rx:5}}.node.impacted rect{{stroke:#111;stroke-width:2.5;fill:#fff7d6}}.node.hidden{{display:none}}.node text{{font-size:11px;pointer-events:none}}.node{{cursor:pointer}}code{{font-size:12px}}ul{{padding-left:18px}}.pill{{display:inline-block;padding:2px 7px;border:1px solid #ccc;border-radius:99px;font-size:11px;margin:2px}}
</style></head><body><header><h1>{escape(title)}</h1><div class=\"meta\">Static, dependency-free explorer. Highlighted nodes are in the selected change impact.</div></header>
<main><div id=\"canvas\"></div><aside><input id=\"search\" placeholder=\"Filter nodes…\"><select id=\"type\"><option value=\"\">All types</option></select><div id=\"details\">Select a node.</div></aside></main>
<script id=\"ecg-data\" type=\"application/json\">{data}</script><script>
const data=JSON.parse(document.getElementById('ecg-data').textContent);const byId=Object.fromEntries(data.nodes.map(n=>[n.id,n]));const types=[...new Set(data.nodes.map(n=>n.type))].sort();const sel=document.getElementById('type');types.forEach(t=>{{const o=document.createElement('option');o.value=t;o.textContent=t;sel.appendChild(o)}});const impacted=new Set(data.highlighted);
const groups=Object.fromEntries(types.map(t=>[t,data.nodes.filter(n=>n.type===t).sort((a,b)=>a.id.localeCompare(b.id))]));const maxRows=Math.max(1,...Object.values(groups).map(x=>x.length));const width=Math.max(900,types.length*220+80),height=Math.max(600,maxRows*74+80);const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('width',width);svg.setAttribute('height',height);document.getElementById('canvas').appendChild(svg);const pos={{}};types.forEach((t,xi)=>groups[t].forEach((n,yi)=>pos[n.id]={{x:40+xi*220,y:40+yi*74}}));data.edges.forEach(e=>{{if(!pos[e.source]||!pos[e.target])return;const l=document.createElementNS(ns,'line');l.classList.add('edge');l.setAttribute('x1',pos[e.source].x+160);l.setAttribute('y1',pos[e.source].y+22);l.setAttribute('x2',pos[e.target].x);l.setAttribute('y2',pos[e.target].y+22);l.dataset.source=e.source;l.dataset.target=e.target;svg.appendChild(l)}});
const nodeEls={{}};data.nodes.forEach(n=>{{const g=document.createElementNS(ns,'g');g.classList.add('node');if(impacted.has(n.id))g.classList.add('impacted');g.setAttribute('transform',`translate(${{pos[n.id].x}},${{pos[n.id].y}})`);const r=document.createElementNS(ns,'rect');r.setAttribute('width',160);r.setAttribute('height',44);const a=document.createElementNS(ns,'text');a.setAttribute('x',7);a.setAttribute('y',17);a.textContent=n.name.slice(0,24);const b=document.createElementNS(ns,'text');b.setAttribute('x',7);b.setAttribute('y',34);b.textContent='['+n.type+']';g.append(r,a,b);g.onclick=()=>show(n.id);svg.appendChild(g);nodeEls[n.id]=g}});
function show(id){{const n=byId[id];const links=data.edges.filter(e=>e.source===id||e.target===id);document.getElementById('details').innerHTML=`<h3>${{esc(n.name)}}</h3><div><code>${{esc(n.id)}}</code></div><div class=pill>${{esc(n.type)}}</div><div class=pill>${{esc(n.criticality||'medium')}}</div><h4>Connections</h4><ul>${{links.map(e=>`<li><code>${{esc(e.source)}}</code> — <b>${{esc(e.relation)}}</b> → <code>${{esc(e.target)}}</code></li>`).join('')||'<li>none</li>'}}</ul><h4>Provenance</h4><ul>${{(n.provenance||[]).map(x=>`<li><code>${{esc(x)}}</code></li>`).join('')||'<li>not recorded</li>'}}</ul>`}}function esc(s){{return String(s).replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}}[c]))}}
function filter(){{const q=document.getElementById('search').value.toLowerCase(),t=sel.value;data.nodes.forEach(n=>{{const visible=(!q||(n.id+' '+n.name).toLowerCase().includes(q))&&(!t||n.type===t);nodeEls[n.id].classList.toggle('hidden',!visible)}});svg.querySelectorAll('.edge').forEach(e=>{{e.style.display=(nodeEls[e.dataset.source].classList.contains('hidden')||nodeEls[e.dataset.target].classList.contains('hidden'))?'none':''}})}}document.getElementById('search').oninput=filter;sel.onchange=filter;
</script></body></html>"""
