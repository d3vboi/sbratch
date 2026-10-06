'use strict';
/*
 * workspace model (see sbblocks/generator.py):
 *   ws = { variables: [name], stacks: [{id, x, y, blocks: [node]}] }
 *   node = { id, type, fields: {}, inputs: {socket: node|null}, slots: {name: [node]}, counts: {} }
 */
(() => {
  const STORE = 'sb-blocks-workspace-v1';
  const $ = (s) => document.querySelector(s);
  const canvas = $('#canvas'), scroller = $('#scroller'), palette = $('#palette'), rail = $('#rail');
  const sidebar = $('#sidebar'), codeEl = $('#code'), diagsEl = $('#diags'), statusEl = $('#status'), ctxEl = $('#ctx');

  let defs = {}, cats = {}, reserved = new Set();
  let ws = null;
  let containers = {}; // container id -> array of nodes (rebuilt every render)
  let history = [], hpos = -1;
  let lastDiags = [], lastCode = '';
  let genTimer = null, genSeq = 0;
  let drag = null;

  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  const uid = () => 'b' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-3);
  const IDENT = /^[A-Za-z][A-Za-z0-9_]*$/;

  /* model */

  function makeNode(type, preset) {
    const d = defs[type];
    const n = { id: uid(), type, fields: {}, inputs: {}, slots: {}, counts: {} };
    for (const p of d.parts) {
      if (p.t === 'text' || p.t === 'number' || p.t === 'dropdown') n.fields[p.name] = p.default;
      else if (p.t === 'input') { if (p.inline !== null) n.fields[p.name] = p.default; }
      else if (p.t === 'slot') n.slots[p.name] = [];
      else if (p.t === 'variadic') {
        n.counts[p.name] = p.count;
        if (p.inline !== null) for (let i = 0; i < p.count; i++) n.fields[p.name + '_' + i] = p.default;
      } else if (p.t === 'variable') n.fields[p.name] = (ws && ws.variables[0]) || '';
    }
    Object.assign(n.fields, preset || {});
    return n;
  }

  function cleanNode(n) {
    if (!n || typeof n !== 'object' || !defs[n.type]) return null;
    const d = defs[n.type];
    const out = { id: typeof n.id === 'string' ? n.id : uid(), type: n.type, fields: {}, inputs: {}, slots: {}, counts: {} };
    if (n.fields && typeof n.fields === 'object') for (const k in n.fields) out.fields[k] = String(n.fields[k]);
    if (n.inputs && typeof n.inputs === 'object') for (const k in n.inputs) {
      const c = cleanNode(n.inputs[k]);
      if (c && defs[c.type].kind === 'value') out.inputs[k] = c;
    }
    for (const p of d.parts) {
      if (p.t === 'slot') {
        const arr = n.slots && Array.isArray(n.slots[p.name]) ? n.slots[p.name] : [];
        out.slots[p.name] = arr.map(cleanNode).filter((c) => c && defs[c.type].kind !== 'value');
      } else if (p.t === 'variadic') {
        const c = n.counts && Number.isInteger(n.counts[p.name]) ? n.counts[p.name] : p.count;
        out.counts[p.name] = Math.max(p.min, Math.min(p.max, c));
      }
    }
    return out;
  }

  function cleanWs(w) {
    const out = { version: 1, variables: [], stacks: [] };
    if (!w || typeof w !== 'object') return null;
    if (Array.isArray(w.variables)) for (const v of w.variables) if (typeof v === 'string' && !out.variables.includes(v)) out.variables.push(v);
    if (Array.isArray(w.stacks)) for (const s of w.stacks) {
      if (!s || !Array.isArray(s.blocks)) continue;
      const blocks = s.blocks.map(cleanNode).filter(Boolean);
      if (blocks.length) out.stacks.push({ id: uid(), x: Number(s.x) || 0, y: Number(s.y) || 0, blocks });
    }
    return out;
  }

  function defaultWs() {
    return { version: 1, variables: [], stacks: [{ id: uid(), x: 30, y: 30, blocks: [makeNode('start')] }] };
  }

  function walk(cb) {
    const walkNode = (n) => {
      for (const k in n.inputs) { const c = n.inputs[k]; if (c) { cb(c, { parent: n, key: k }); walkNode(c); } }
      for (const k in n.slots) n.slots[k].forEach((c, i) => { cb(c, { arr: n.slots[k], i }); walkNode(c); });
    };
    for (const st of ws.stacks) st.blocks.forEach((n, i) => { cb(n, { arr: st.blocks, i, stack: st }); walkNode(n); });
  }
  const locate = (id) => { let res = null; walk((n, loc) => { if (n.id === id) res = Object.assign({ node: n }, loc); }); return res; };
  const getNode = (id) => { const l = locate(id); return l ? l.node : null; };

  function cloneNode(n) {
    const c = JSON.parse(JSON.stringify(n));
    const re = (x) => { x.id = uid(); Object.values(x.inputs).forEach((v) => v && re(v)); Object.values(x.slots).forEach((a) => a.forEach(re)); };
    re(c);
    return c;
  }

  const pruneStacks = () => { ws.stacks = ws.stacks.filter((s) => s.blocks.length); };

  /* variables */

  function validateVarName(name) {
    if (!IDENT.test(name)) return 'Use letters, digits and _ only, starting with a letter.';
    if (reserved.has(name.toLowerCase())) return '"' + name + '" is reserved by Small Basic. Pick another name.';
    if (ws.variables.some((v) => v.toLowerCase() === name.toLowerCase())) return 'That variable already exists (names are not case sensitive).';
    return null;
  }

  function askNewVariable() {
    const name = (prompt('New variable name:') || '').trim();
    if (!name) return null;
    const err = validateVarName(name);
    if (err) { alert(err); return null; }
    ws.variables.push(name);
    return name;
  }

  /* rendering */

  const autosize = (i) => { i.style.width = Math.max(2, i.value.length + 1) + 'ch'; };

  function renderBlock(node) {
    const d = defs[node.type];
    const b = el('div', 'block ' + d.kind + (d.kind === 'value' ? ' shape-' + d.shape : ''));
    b.style.setProperty('--c', cats[d.category].color);
    b.dataset.id = node.id;
    if (d.tooltip) b.title = d.tooltip;
    let row = null, hasSlot = false;
    for (const p of d.parts) {
      if (p.t === 'slot') {
        row = null; hasSlot = true;
        const wrap = el('div', 'slot');
        wrap.appendChild(renderList(node.slots[p.name] || (node.slots[p.name] = []), 'slot:' + node.id + ':' + p.name));
        b.appendChild(wrap);
      } else {
        if (!row) { row = el('div', 'row'); b.appendChild(row); }
        row.appendChild(renderPart(node, p));
      }
    }
    if (d.kind !== 'value') {
      if (hasSlot) b.appendChild(el('div', 'foot'));
      else if (b.firstChild) b.firstChild.style.minHeight = '30px';
    }
    if (d.kind === 'value') { // value blocks are inline: flatten the row
      const r = b.querySelector(':scope > .row');
      if (r) { r.style.cssText = 'display:contents'; }
    }
    return b;
  }

  function renderList(arr, cid) {
    const l = el('div', 'blocklist');
    l.dataset.cid = cid;
    containers[cid] = arr;
    arr.forEach((n) => l.appendChild(renderBlock(n)));
    return l;
  }

  function renderSocket(node, p, key) {
    const s = el('span', 'socket');
    s.dataset.owner = node.id; s.dataset.key = key;
    const child = node.inputs[key];
    if (child) { s.classList.add('filled'); s.appendChild(renderBlock(child)); }
    else if (p.inline === null) s.classList.add('empty', 'hex');
    else {
      const i = el('input', 'inline');
      i.type = 'text'; i.spellcheck = false;
      i.value = node.fields[key] != null ? node.fields[key] : (p.default || '');
      autosize(i);
      i.addEventListener('input', () => { node.fields[key] = i.value; autosize(i); fieldInput(); });
      i.addEventListener('change', fieldCommit);
      s.appendChild(i);
    }
    return s;
  }

  function renderPart(node, p) {
    if (p.t === 'label') return el('span', 'lbl', p.text);
    if (p.t === 'input') return renderSocket(node, p, p.name);

    if (p.t === 'text' || p.t === 'number') {
      const i = el('input', 'field');
      i.type = 'text'; i.spellcheck = false;
      i.value = node.fields[p.name] != null ? node.fields[p.name] : p.default;
      autosize(i);
      i.addEventListener('input', () => { node.fields[p.name] = i.value; autosize(i); fieldInput(); });
      i.addEventListener('change', fieldCommit);
      return i;
    }

    if (p.t === 'dropdown') {
      const s = el('select', 'field');
      p.options.forEach((o) => { const op = el('option', null, o.label); op.value = o.value; s.appendChild(op); });
      s.value = node.fields[p.name] != null ? node.fields[p.name] : p.default;
      s.addEventListener('change', () => { node.fields[p.name] = s.value; fieldInput(); fieldCommit(); });
      return s;
    }

    if (p.t === 'variable') {
      const s = el('select', 'field');
      const cur = node.fields[p.name] || '';
      if (!cur) { const o = el('option', null, 'choose…'); o.value = ''; s.appendChild(o); }
      else if (!ws.variables.includes(cur)) { const o = el('option', null, cur + ' (missing)'); o.value = cur; s.appendChild(o); }
      ws.variables.forEach((v) => { const o = el('option', null, v); o.value = v; s.appendChild(o); });
      const nw = el('option', null, '＋ New variable…'); nw.value = '__new__'; s.appendChild(nw);
      s.value = cur;
      s.addEventListener('change', () => {
        if (s.value === '__new__') {
          const name = askNewVariable();
          if (name) { node.fields[p.name] = name; structuralChange(); } else renderWorkspace();
        } else { node.fields[p.name] = s.value; fieldInput(); fieldCommit(); }
      });
      return s;
    }

    if (p.t === 'variadic') {
      const g = el('span', 'group');
      const n = node.counts[p.name] != null ? node.counts[p.name] : p.count;
      for (let i = 0; i < n; i++) g.appendChild(renderSocket(node, p, p.name + '_' + i));
      const minus = el('button', 'mini', '−'), plus = el('button', 'mini', '+');
      minus.title = 'Remove last item'; plus.title = 'Add an item';
      minus.disabled = n <= p.min; plus.disabled = n >= p.max;
      minus.addEventListener('click', () => {
        node.counts[p.name] = n - 1;
        delete node.inputs[p.name + '_' + (n - 1)]; delete node.fields[p.name + '_' + (n - 1)];
        structuralChange();
      });
      plus.addEventListener('click', () => {
        node.counts[p.name] = n + 1;
        if (p.inline !== null) node.fields[p.name + '_' + n] = p.default;
        structuralChange();
      });
      g.append(minus, plus);
      return g;
    }
    return el('span', 'lbl', '?');
  }

  function renderWorkspace() {
    containers = {};
    canvas.textContent = '';
    for (const st of ws.stacks) {
      const box = el('div', 'stack');
      box.style.left = st.x + 'px'; box.style.top = st.y + 'px';
      const first = st.blocks[0];
      box.appendChild(defs[first.type].kind === 'value' ? renderBlock(first) : renderList(st.blocks, 'stack:' + st.id));
      canvas.appendChild(box);
    }
    applyMarks();
  }

  function renderPalette() {
    palette.textContent = ''; rail.textContent = '';
    for (const cat of Object.values(cats)) {
      const head = el('h3', 'pal-head', cat.name);
      head.style.setProperty('--c', cat.color); head.id = 'cat-' + cat.id;
      const rb = el('button', 'rail-btn', cat.name);
      rb.style.setProperty('--c', cat.color);
      rb.addEventListener('click', () => head.scrollIntoView({ behavior: 'smooth', block: 'start' }));
      rail.appendChild(rb);
      palette.appendChild(head);
      const list = Object.values(defs).filter((d) => d.category === cat.id);
      if (list.some((d) => d.palette === 'variables')) {
        const mk = el('button', 'make-var', 'Make a variable');
        mk.addEventListener('click', () => { if (askNewVariable()) structuralChange(); });
        palette.appendChild(mk);
      }
      for (const d of list) {
        if (d.palette === 'variables') {
          const part = d.parts.find((p) => p.t === 'variable');
          for (const v of ws.variables) {
            const row = el('div', 'pal-var');
            row.appendChild(paletteItem(d.type, { [part.name]: v }));
            const del = el('button', 'del', '×');
            del.title = 'Delete variable "' + v + '"';
            del.addEventListener('click', () => {
              if (!confirm('Delete variable "' + v + '"? Blocks that use it will show an error.')) return;
              ws.variables = ws.variables.filter((x) => x !== v);
              structuralChange();
            });
            row.appendChild(del);
            palette.appendChild(row);
          }
        } else palette.appendChild(paletteItem(d.type));
      }
    }
  }

  function paletteItem(type, preset) {
    const wrap = el('div', 'pal-item');
    wrap._spec = { type, preset };
    wrap.appendChild(renderBlock(makeNode(type, preset)));
    return wrap;
  }

  /* change tracking */

  function save() { try { localStorage.setItem(STORE, JSON.stringify(ws)); } catch (e) { /* storage may be unavailable */ } }
  function snapshot() {
    const s = JSON.stringify(ws);
    if (history[hpos] === s) return;
    history = history.slice(0, hpos + 1); history.push(s);
    if (history.length > 100) history.shift();
    hpos = history.length - 1;
    updateUndo();
  }
  function updateUndo() { $('#btn-undo').disabled = hpos <= 0; $('#btn-redo').disabled = hpos >= history.length - 1; }
  function fieldInput() { save(); scheduleGenerate(); }
  function fieldCommit() { snapshot(); }
  function structuralChange() { pruneStacks(); renderPalette(); renderWorkspace(); save(); snapshot(); scheduleGenerate(); }
  function restore(i) { hpos = i; ws = JSON.parse(history[i]); renderPalette(); renderWorkspace(); save(); updateUndo(); scheduleGenerate(); }
  function loadWorkspace(w, resetHistory) {
    ws = w; if (resetHistory) { history = []; hpos = -1; }
    renderPalette(); renderWorkspace(); save(); snapshot(); scheduleGenerate();
  }

  /* code generation */

  function scheduleGenerate() { clearTimeout(genTimer); genTimer = setTimeout(generate, 200); }

  async function generate() {
    const seq = ++genSeq;
    try {
      const r = await fetch('/api/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ workspace: ws }) });
      const data = await r.json();
      if (seq === genSeq) showResult(data);
    } catch (e) {
      if (seq === genSeq) { statusEl.className = 'bad'; statusEl.textContent = 'Could not reach the server.'; }
    }
  }

  const KEYWORDS = /("[^"]*")|('.*$)|\b(If|Then|Else|ElseIf|EndIf|For|To|Step|EndFor|While|EndWhile|And|Or|True|False)\b|\b(TextWindow|Text|Math|Array|Clock|Program|Stack)\b|\b(\d+(?:\.\d+)?)\b/gi;
  function highlight(line) {
    const esc = line.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return esc.replace(KEYWORDS, (m, s, c, k, o, n) =>
      s ? '<span class="s">' + s + '</span>' : c ? '<span class="c">' + c + '</span>' :
      k ? '<span class="k">' + k + '</span>' : o ? '<span class="o">' + o + '</span>' : '<span class="n">' + n + '</span>');
  }

  function showResult(data) {
    lastCode = data.code || ''; lastDiags = data.diagnostics || [];
    codeEl.textContent = '';
    lastCode.split('\n').filter((_, i, a) => i < a.length - 1 || a[i] !== '').forEach((line, i) => {
      const row = el('div', 'cl');
      row.appendChild(el('span', 'no', String(i + 1)));
      const t = el('span'); t.innerHTML = highlight(line) || ' '; row.appendChild(t);
      codeEl.appendChild(row);
    });
    const errs = lastDiags.filter((d) => d.level === 'error').length, warns = lastDiags.filter((d) => d.level === 'warning').length;
    if (!lastCode) { statusEl.className = 'idle'; statusEl.textContent = 'no code, go do something'; }
    else if (errs) { statusEl.className = 'bad'; statusEl.textContent = errs + ' error' + (errs > 1 ? 's' : '') + ', fix them before using this code.'; }
    else { statusEl.className = 'ok'; statusEl.textContent = 'copy/paste this into smallbasic' + (warns ? ' (' + warns + ' warning' + (warns > 1 ? 's' : '') + ')' : ''); }
    $('#btn-copy').disabled = $('#btn-download').disabled = !lastCode;

    diagsEl.textContent = '';
    const order = { error: 0, warning: 1, info: 2 };
    [...lastDiags].sort((a, b) => order[a.level] - order[b.level]).forEach((d) => {
      const li = el('li', d.level, d.message);
      if (d.block) { li.classList.add('clickable'); li.addEventListener('click', () => focusBlock(d.block)); }
      diagsEl.appendChild(li);
    });
    applyMarks();
  }

  function blockEl(id) { return canvas.querySelector('.block[data-id="' + CSS.escape(id) + '"]'); }
  function applyMarks() {
    canvas.querySelectorAll('.has-error,.has-warning').forEach((e) => e.classList.remove('has-error', 'has-warning'));
    for (const d of lastDiags) {
      if (!d.block || d.level === 'info') continue;
      const b = blockEl(d.block);
      if (b) b.classList.add(d.level === 'error' ? 'has-error' : 'has-warning');
    }
  }
  function focusBlock(id) {
    const b = blockEl(id);
    if (!b) return;
    b.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
    b.classList.add('flash'); setTimeout(() => b.classList.remove('flash'), 1900);
  }

  /* drag & drop */

  document.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    if (!e.target.closest('#ctx')) ctxEl.hidden = true;
    if (e.target.closest('input,select,button,textarea,#ctx')) return;
    const palItem = e.target.closest('.pal-item');
    const b = e.target.closest('.block');
    if (!palItem && !(b && canvas.contains(b))) return;
    e.preventDefault();
    drag = { startX: e.clientX, startY: e.clientY, blockEl: b, palItem, started: false };
  });

  document.addEventListener('pointermove', (e) => {
    if (!drag) return;
    if (!drag.started) {
      if (Math.hypot(e.clientX - drag.startX, e.clientY - drag.startY) < 5) return;
      startDrag();
      if (!drag) return;
    }
    moveDrag(e);
  });

  document.addEventListener('pointerup', (e) => { if (drag && drag.started) finishDrag(e); drag = null; });
  document.addEventListener('pointercancel', () => { if (drag && drag.started) cancelDrag(); drag = null; });

  function startDrag() {
    const d = drag;
    let chain, rect;
    const cr = canvas.getBoundingClientRect();
    if (d.palItem) {
      chain = [makeNode(d.palItem._spec.type, d.palItem._spec.preset)];
      rect = d.palItem.firstChild.getBoundingClientRect();
    } else {
      const loc = locate(d.blockEl.dataset.id);
      if (!loc) { drag = null; return; }
      rect = d.blockEl.getBoundingClientRect();
      if (loc.arr) chain = loc.arr.splice(loc.i);       // the block and everything below it
      else { chain = [loc.node]; loc.parent.inputs[loc.key] = null; }
      pruneStacks();
      renderWorkspace();
    }
    d.chain = chain;
    d.fromPalette = !!d.palItem;
    d.offX = d.startX - rect.left; d.offY = d.startY - rect.top;
    d.origin = { x: rect.left - cr.left, y: rect.top - cr.top };
    d.started = true;
    d.ghost = el('div', 'ghost');
    d.ghost.appendChild(defs[chain[0].type].kind === 'value' ? renderBlock(chain[0]) : renderList(chain, 'ghost'));
    document.body.appendChild(d.ghost);
    d.indicator = el('div', 'indicator'); d.indicator.hidden = true;
    document.body.appendChild(d.indicator);
    document.body.classList.add('dragging');
  }

  function inRect(e, r) { return e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom; }

  function computeTarget(e) {
    const d = drag, kind = defs[d.chain[0].type].kind;
    if (inRect(e, sidebar.getBoundingClientRect())) return { type: 'trash' };
    if (!inRect(e, scroller.getBoundingClientRect())) return { type: 'none' };

    if (kind === 'value') {
      let best = null, bestArea = Infinity;
      for (const s of canvas.querySelectorAll('.socket')) {
        const r = s.getBoundingClientRect();
        if (!inRect(e, r)) continue;
        const area = r.width * r.height;
        if (area < bestArea) { best = s; bestArea = area; }
      }
      return best ? { type: 'socket', el: best, owner: best.dataset.owner, key: best.dataset.key } : { type: 'free' };
    }

    if (kind === 'statement') {
      const gx = e.clientX - d.offX, gy = e.clientY - d.offY;
      let best = null, bestDist = 55;
      for (const list of canvas.querySelectorAll('.blocklist')) {
        const cid = list.dataset.cid, arr = containers[cid];
        if (!arr) continue;
        const r = list.getBoundingClientRect();
        const kids = [...list.children].filter((c) => c.classList.contains('block'));
        const tries = [{ idx: 0, y: r.top + 2 }];
        kids.forEach((k, i) => tries.push({ idx: i + 1, y: k.getBoundingClientRect().bottom }));
        for (const t of tries) {
          if (t.idx === 0 && arr.length && defs[arr[0].type].kind === 'hat') continue;   // nothing goes above a start block
          const dist = Math.hypot(gx - r.left, gy - t.y);
          if (dist < bestDist) { bestDist = dist; best = { type: 'slot', cid, idx: t.idx, x: r.left, y: t.y, w: Math.max(r.width, 70) }; }
        }
      }
      return best || { type: 'free' };
    }
    return { type: 'free' };   // hat blocks start a new stack
  }

  function clearHover() { canvas.querySelectorAll('.drop-hover').forEach((x) => x.classList.remove('drop-hover')); }

  function moveDrag(e) {
    const d = drag;
    d.ghost.style.left = (e.clientX - d.offX) + 'px'; d.ghost.style.top = (e.clientY - d.offY) + 'px';
    clearHover();
    const t = computeTarget(e);
    d.target = t;
    sidebar.classList.toggle('trash', t.type === 'trash' && !d.fromPalette);
    if (t.type === 'slot') {
      d.indicator.hidden = false;
      Object.assign(d.indicator.style, { left: t.x + 'px', top: (t.y - 2) + 'px', width: t.w + 'px' });
    } else d.indicator.hidden = true;
    if (t.type === 'socket') t.el.classList.add('drop-hover');
  }

  function clearDragUI() {
    if (!drag) return;
    drag.ghost && drag.ghost.remove(); drag.indicator && drag.indicator.remove();
    clearHover(); sidebar.classList.remove('trash'); document.body.classList.remove('dragging');
  }

  function cancelDrag() {
    const d = drag; clearDragUI();
    if (!d.fromPalette) ws.stacks.push({ id: uid(), x: d.origin.x, y: d.origin.y, blocks: d.chain });
    structuralChange();
  }

  function finishDrag(e) {
    const d = drag, chain = d.chain;
    const t = computeTarget(e);
    clearDragUI();
    const cr = canvas.getBoundingClientRect();
    const place = (x, y, blocks) => ws.stacks.push({ id: uid(), x: Math.max(8, Math.round(x)), y: Math.max(8, Math.round(y)), blocks });
    if (t.type === 'socket') {
      const owner = getNode(t.owner);
      const old = owner.inputs[t.key];
      owner.inputs[t.key] = chain[0];
      if (old) place(e.clientX - cr.left + 24, e.clientY - cr.top + 24, [old]);   // bump the replaced block out
    } else if (t.type === 'slot') {
      containers[t.cid].splice(t.idx, 0, ...chain);
    } else if (t.type === 'free') {
      place(e.clientX - d.offX - cr.left, e.clientY - d.offY - cr.top, chain);
    } else if (t.type === 'none' && !d.fromPalette) {
      place(d.origin.x, d.origin.y, chain);       // dropped on the code pane etc: put it back
    }                                              // 'trash' (palette) just discards
    structuralChange();
  }

  /* context menu */

  canvas.addEventListener('contextmenu', (e) => {
    const b = e.target.closest('.block');
    if (!b) return;
    e.preventDefault();
    ctxEl.textContent = '';
    const add = (label, fn) => { const x = el('button', null, label); x.addEventListener('click', () => { ctxEl.hidden = true; fn(); }); ctxEl.appendChild(x); };
    add('Duplicate block', () => duplicateBlock(b.dataset.id));
    add('Delete block', () => deleteBlock(b.dataset.id));
    ctxEl.hidden = false;
    ctxEl.style.left = Math.min(e.clientX, innerWidth - 170) + 'px'; ctxEl.style.top = Math.min(e.clientY, innerHeight - 90) + 'px';
  });

  function deleteBlock(id) {
    const loc = locate(id);
    if (!loc) return;
    if (loc.arr) loc.arr.splice(loc.i, 1); else loc.parent.inputs[loc.key] = null;
    structuralChange();
  }

  function duplicateBlock(id) {
    const loc = locate(id);
    if (!loc) return;
    const c = cloneNode(loc.node);
    if (loc.arr && defs[c.type].kind === 'statement') loc.arr.splice(loc.i + 1, 0, c);
    else {
      const r = blockEl(id).getBoundingClientRect(), cr = canvas.getBoundingClientRect();
      ws.stacks.push({ id: uid(), x: r.left - cr.left + 30, y: r.top - cr.top + 30, blocks: [c] });
    }
    structuralChange();
  }

  /* toolbar */

  function download(name, text, type) {
    const a = el('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  function wireToolbar() {
    $('#btn-undo').addEventListener('click', () => { if (hpos > 0) restore(hpos - 1); });
    $('#btn-redo').addEventListener('click', () => { if (hpos < history.length - 1) restore(hpos + 1); });
    $('#btn-clear').addEventListener('click', () => { if (confirm('Clear the whole workspace?')) loadWorkspace(defaultWs(), false); });
    $('#btn-export').addEventListener('click', () => download('workspace.sbblocks.json', JSON.stringify(ws, null, 2), 'application/json'));
    $('#btn-import').addEventListener('click', () => $('#file-import').click());
    $('#file-import').addEventListener('change', (e) => {
      const f = e.target.files[0]; e.target.value = '';
      if (!f) return;
      const rd = new FileReader();
      rd.onload = () => {
        try {
          const w = cleanWs(JSON.parse(rd.result));
          if (!w || !w.stacks.length) throw new Error('empty');
          loadWorkspace(w, false);
        } catch (err) { alert('That file is not a valid workspace.'); }
      };
      rd.readAsText(f);
    });
    $('#btn-copy').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(lastCode); }
      catch (e) { const ta = el('textarea'); ta.value = lastCode; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); }
      const b = $('#btn-copy'); b.textContent = 'Copied!'; setTimeout(() => (b.textContent = 'Copy'), 1200);
    });
    $('#btn-download').addEventListener('click', () => download('program.sb', lastCode, 'text/plain'));

    $('#examples').addEventListener('change', async (e) => {
      const id = e.target.value; e.target.value = '';
      if (!id) return;
      const total = ws.stacks.reduce((n, s) => n + s.blocks.length, 0);
      if (total > 1 && !confirm('Replace your current workspace with this example?')) return;
      const w = cleanWs(await (await fetch('/api/examples/' + encodeURIComponent(id))).json());
      if (w) loadWorkspace(w, false);
    });

    document.addEventListener('keydown', (e) => {
      if (e.target.closest('input,select,textarea')) return;
      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key.toLowerCase() === 'z') { e.preventDefault(); if (e.shiftKey) { if (hpos < history.length - 1) restore(hpos + 1); } else if (hpos > 0) restore(hpos - 1); }
      else if (mod && e.key.toLowerCase() === 'y') { e.preventDefault(); if (hpos < history.length - 1) restore(hpos + 1); }
    });
  }

  /* start */

  async function init() {
    const cat = await (await fetch('/api/blocks')).json();
    cat.categories.forEach((c) => (cats[c.id] = c));
    cat.blocks.forEach((b) => (defs[b.type] = b));
    reserved = new Set(cat.reserved);

    let w = null;
    try { w = cleanWs(JSON.parse(localStorage.getItem(STORE))); } catch (e) { /* ignore */ }
    if (!w || !w.stacks.length) w = defaultWs();
    wireToolbar();
    loadWorkspace(w, true);

    try {
      const list = await (await fetch('/api/examples')).json();
      const sel = $('#examples');
      list.forEach((x) => { const o = el('option', null, x.title); o.value = x.id; sel.appendChild(o); });
    } catch (e) { /* examples are optional */ }
  }

  init();
})();
