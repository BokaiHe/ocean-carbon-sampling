/* Two interactive globes from frozen data: SOCAT observations and the 2005 experiment.
   No routes, interpolation, predictions or model fitting happen in the browser. */
(() => {
  'use strict';
  const tr = (en, zh) => (window.OCS ? window.OCS.tr(en, zh) : en);
  const fmt = n => n.toLocaleString(window.OCS && window.OCS.lang === 'zh' ? 'zh-CN' : 'en-US');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const RAD = Math.PI / 180;
  const unit = (lon, lat) => [Math.cos(lat * RAD) * Math.cos(lon * RAD), Math.cos(lat * RAD) * Math.sin(lon * RAD), Math.sin(lat * RAD)];
  const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  let landPromise = null;
  const loadLand = () => (landPromise ||= fetch('data/globe-land.json').then(r => { if (!r.ok) throw Error('land'); return r.json(); }));
  const ramp = (stops, n = 64) => d3.range(n).map(i => {
    const t = i / (n - 1), k = t * (stops.length - 1), j = Math.min(stops.length - 2, Math.floor(k));
    return d3.interpolateRgb(stops[j], stops[j + 1])(k - j);
  });

  /* Shared orthographic globe: drag, wheel/keys zoom, idle spin, resize. */
  function createGlobe(canvas, {rotation = [20, -15, 0], drawPoints, onPick}) {
    const ctx = canvas.getContext('2d');
    const projection = d3.geoOrthographic().clipAngle(90).precision(.4);
    const path = d3.geoPath(projection, ctx);
    const graticule = d3.geoGraticule10();
    const state = {rotation: rotation.slice(), zoom: 1, width: 0, spin: !reduced.matches, inView: false, land: null, visible: []};
    let frame = 0, spinFrame = 0, last = 0, pointer = null;
    const request = () => { if (!frame) frame = requestAnimationFrame(draw); };
    function draw() {
      frame = 0;
      const width = canvas.clientWidth; if (!width) return;
      const ratio = Math.min(devicePixelRatio || 1, 2);
      if (canvas.width !== Math.round(width * ratio)) { canvas.width = canvas.height = Math.round(width * ratio); }
      state.width = width;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0); ctx.clearRect(0, 0, width, width);
      const r = width * .46 * state.zoom;
      projection.translate([width / 2, width / 2]).scale(r).rotate(state.rotation);
      // Atmosphere glow and sphere
      const glow = ctx.createRadialGradient(width / 2, width / 2, r * .9, width / 2, width / 2, r * 1.12);
      glow.addColorStop(0, 'rgba(79,214,200,.18)'); glow.addColorStop(1, 'rgba(79,214,200,0)');
      ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(width / 2, width / 2, r * 1.12, 0, Math.PI * 2); ctx.fill();
      const sea = ctx.createRadialGradient(width * .4, width * .38, r * .1, width / 2, width / 2, r);
      sea.addColorStop(0, '#12405c'); sea.addColorStop(1, css('--sphere') || '#0b2537');
      ctx.beginPath(); path({type: 'Sphere'}); ctx.fillStyle = sea; ctx.fill();
      ctx.save(); ctx.beginPath(); path({type: 'Sphere'}); ctx.clip();
      ctx.beginPath(); path(graticule); ctx.strokeStyle = 'rgba(170,220,245,.08)'; ctx.lineWidth = .6; ctx.stroke();
      const centre = projection.invert([width / 2, width / 2]), front = unit(centre[0], centre[1]);
      state.visible = [];
      drawPoints({ctx, projection, front, radius: r, width, visible: state.visible, zoom: state.zoom});
      if (state.land) { ctx.beginPath(); path(state.land); ctx.fillStyle = css('--land') || '#173247'; ctx.fill(); ctx.strokeStyle = css('--land-edge') || '#2d5672'; ctx.lineWidth = .8; ctx.stroke(); }
      ctx.restore();
      ctx.beginPath(); path({type: 'Sphere'}); ctx.strokeStyle = 'rgba(170,220,245,.35)'; ctx.lineWidth = 1; ctx.stroke();
    }
    function tick(time) {
      spinFrame = 0;
      if (!state.spin || !state.inView || document.hidden) { last = 0; return; }
      if (last) state.rotation[0] += Math.min(time - last, 60) * .006;
      last = time; request(); spinFrame = requestAnimationFrame(tick);
    }
    const spin = () => { if (state.spin && state.inView && !spinFrame) spinFrame = requestAnimationFrame(tick); };
    const stop = () => { state.spin = false; cancelAnimationFrame(spinFrame); spinFrame = 0; last = 0; };
    const turn = (dx, dy = 0) => { stop(); state.rotation[0] += dx; state.rotation[1] = Math.max(-85, Math.min(85, state.rotation[1] + dy)); request(); };
    const zoom = step => { stop(); state.zoom = Math.max(.8, Math.min(3, state.zoom * step)); request(); };
    canvas.addEventListener('pointerdown', e => { if (e.button !== 0) return; stop(); pointer = {id: e.pointerId, x: e.clientX, y: e.clientY, sx: e.clientX, sy: e.clientY}; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', e => { if (!pointer || pointer.id !== e.pointerId) return; turn((e.clientX - pointer.x) * .3 / state.zoom, -(e.clientY - pointer.y) * .3 / state.zoom); pointer.x = e.clientX; pointer.y = e.clientY; });
    canvas.addEventListener('pointerup', e => {
      if (!pointer || pointer.id !== e.pointerId) return;
      const moved = Math.hypot(e.clientX - pointer.sx, e.clientY - pointer.sy) > 4; pointer = null;
      if (!moved) { const box = canvas.getBoundingClientRect(); pick(e.clientX - box.left, e.clientY - box.top); }
    });
    canvas.addEventListener('pointercancel', () => { pointer = null; });
    canvas.addEventListener('wheel', e => { if (!e.ctrlKey && !e.metaKey) return; e.preventDefault(); zoom(e.deltaY < 0 ? 1.12 : 1 / 1.12); }, {passive: false});
    canvas.addEventListener('keydown', e => {
      const keys = {ArrowLeft: () => turn(-10), ArrowRight: () => turn(10), ArrowUp: () => turn(0, 10), ArrowDown: () => turn(0, -10), '+': () => zoom(1.2), '=': () => zoom(1.2), '-': () => zoom(1 / 1.2), Home: () => { stop(); state.rotation = rotation.slice(); state.zoom = 1; request(); }};
      if (keys[e.key]) { e.preventDefault(); keys[e.key](); }
    });
    function pick(x, y) {
      const location = projection.invert([x, y]);
      if (!location || Math.hypot(x - state.width / 2, y - state.width / 2) > projection.scale()) return onPick(null);
      let best = null, distance = 144;
      for (const p of state.visible) { const d = (p.x - x) ** 2 + (p.y - y) ** 2; if (d < distance) { distance = d; best = p; } }
      if (best) { state.selected = best.item; request(); }
      onPick(best ? best.item : null);
    }
    new ResizeObserver(request).observe(canvas);
    new IntersectionObserver(([entry]) => { state.inView = entry.isIntersecting; spin(); }, {threshold: .1}).observe(canvas);
    document.addEventListener('visibilitychange', spin);
    reduced.addEventListener('change', () => { if (reduced.matches) stop(); });
    loadLand().then(land => { state.land = land; request(); }).catch(() => {});
    return {state, request, stop};
  }

  function lazy(node, init) {
    const io = new IntersectionObserver(entries => { if (entries.some(e => e.isIntersecting)) { io.disconnect(); init(); } }, {rootMargin: '600px'});
    io.observe(node);
  }

  /* SOCAT observations */
  function observationGlobe() {
    const root = document.getElementById('observation-explorer'); if (!root) return;
    const canvas = document.getElementById('observation-globe');
    const yearBox = document.getElementById('observation-year');
    const monthBox = document.getElementById('observation-month');
    const count = document.getElementById('observation-count');
    const readout = document.getElementById('observation-readout');
    const monthsEn = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const colour = ramp(['#2f5fbf', '#21a3b0', '#9fd8a0', '#ffb454', '#ff7f5c']);
    const colourOf = v => colour[Math.round(Math.max(0, Math.min(1, (v - 200) / 400)) * (colour.length - 1))];
    document.getElementById('observation-scale').style.background = `linear-gradient(90deg,${colour.filter((_, i) => i % 8 === 0).join(',')},${colour[colour.length - 1]})`;
    lazy(root, async () => {
      try {
        const data = await fetch('data/observed-co2.json').then(r => { if (!r.ok) throw Error('data'); return r.json(); });
        let year = data.metadata.default_year, month = 0, cells = [], selected = null;
        const globe = createGlobe(canvas, {rotation: [30, -20, 0], drawPoints, onPick: item => { selected = item; describe(); }});
        function drawPoints({ctx, projection, front, width, visible, zoom}) {
          const size = Math.max(1.2, width / 330) * Math.sqrt(zoom);
          for (const c of cells) {
            if (c.xyz[0] * front[0] + c.xyz[1] * front[1] + c.xyz[2] * front[2] <= 0) continue;
            const [x, y] = projection([c.lon, c.lat]);
            ctx.fillStyle = c.colour; ctx.fillRect(x - size / 2, y - size / 2, size, size);
            visible.push({x, y, item: c});
          }
          if (selected) { const [x, y] = projection([selected.lon, selected.lat]); ctx.beginPath(); ctx.arc(x, y, 7, 0, Math.PI * 2); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke(); }
        }
        function rebuild() {
          const agg = new Map();
          for (const [m, lon, lat, value, n] of data.years[String(year)]) {
            if (month && m !== month) continue;
            const key = lon + '|' + lat;
            if (!agg.has(key)) agg.set(key, {lon, lat, sum: 0, months: 0, n: 0});
            const c = agg.get(key); c.sum += value; c.months++; c.n += n;
          }
          cells = [...agg.values()].map(c => ({...c, value: c.sum / c.months, xyz: unit(c.lon, c.lat), colour: colourOf(c.sum / c.months)}));
          selected = null;
          yearBox.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(Number(b.dataset.year) === year)));
          monthBox.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(Number(b.dataset.month) === month)));
          root.dataset.cells = String(cells.length);
          describe(); globe.request();
        }
        function describe() {
          const n = cells.reduce((s, c) => s + c.n, 0);
          count.textContent = tr(`${fmt(cells.length)} grid cells · ${fmt(n)} measurements`, `${fmt(cells.length)} 个网格 · ${fmt(n)} 次测量`);
          if (!selected) { readout.textContent = tr('Tap a dot to read its value.', '点击一个点查看数值。'); return; }
          const c = selected;
          readout.textContent = tr(
            `${c.value.toFixed(1)} µatm · ${c.lat}°, ${c.lon}° · ${fmt(c.n)} measurements in ${c.months} month${c.months > 1 ? 's' : ''}`,
            `${c.value.toFixed(1)} µatm · ${c.lat}°, ${c.lon}° · ${c.months} 个月共 ${fmt(c.n)} 次测量`);
        }
        yearBox.replaceChildren(...data.metadata.years.map(y => { const b = document.createElement('button'); b.type = 'button'; b.textContent = y; b.dataset.year = y; b.onclick = () => { year = y; rebuild(); }; return b; }));
        function months() {
          monthBox.replaceChildren(...[0, ...d3.range(1, 13)].map(m => {
            const b = document.createElement('button'); b.type = 'button'; b.dataset.month = m;
            b.textContent = m ? (window.OCS && window.OCS.lang === 'zh' ? `${m}月` : monthsEn[m - 1]) : tr('All', '全年');
            b.setAttribute('aria-pressed', String(m === month)); b.onclick = () => { month = m; rebuild(); }; return b;
          }));
        }
        months(); rebuild(); root.dataset.ready = 'true';
        document.addEventListener('ocs:lang', () => { months(); describe(); });
      } catch (error) { count.textContent = tr('Observations could not load.', '观测数据加载失败。'); root.dataset.ready = 'error'; console.warn(error); }
    });
  }

  /* 2005 experiment: sampling blocks and per-cell errors (pre-mask supporting view). */
  function experimentGlobe() {
    const root = document.getElementById('globe-explorer'); if (!root) return;
    const canvas = document.getElementById('ocean-globe');
    const legend = document.getElementById('globe-legend');
    const readout = document.getElementById('globe-readout');
    const model = {layer: 'sampling', strategy: 'random'};
    const stops = {sampling: ['#1d4f7a', '#77bdfd', '#e8f6ff'], mae: ['#183d57', '#ffb454', '#ff5c5c'], delta: ['#69e3b0', '#183d57', '#ff7f5c']};
    const palettes = {}; for (const [k, s] of Object.entries(stops)) palettes[k] = ramp(s);
    const column = {random: 2, historical: 3, coverage: 4};
    lazy(root, async () => {
      try {
        const data = await fetch('data/globe-data.json').then(r => { if (!r.ok) throw Error('data'); return r.json(); });
        const samples = {}; for (const [k, rows] of Object.entries(data.sampling)) samples[k] = rows.map(r => ({row: r, xyz: unit(r[0], r[1])}));
        const fields = data.fields.map(r => ({row: r, xyz: unit(r[0], r[1])}));
        let selected = null;
        const value = item => { const v = item.row[column[model.strategy]]; if (v === null) return null; return model.layer === 'delta' ? (item.row[2] === null ? null : v - item.row[2]) : v; };
        const globe = createGlobe(canvas, {rotation: [-150, -10, 0], drawPoints, onPick: item => { selected = item; describe(); }});
        function drawPoints({ctx, projection, front, radius, visible}) {
          const rows = model.layer === 'sampling' ? samples[model.strategy] : fields;
          const pal = palettes[model.layer];
          for (const item of rows) {
            if (item.xyz[0] * front[0] + item.xyz[1] * front[1] + item.xyz[2] * front[2] <= .02) continue;
            const [x, y] = projection(item.row);
            if (model.layer === 'sampling') {
              const n = item.row[2]; if (!n) continue;
              ctx.fillStyle = pal[Math.round(Math.min(1, n / 20) * 63)];
              ctx.beginPath(); ctx.arc(x, y, 1.6 + Math.sqrt(n) * .55 * radius / 260, 0, Math.PI * 2); ctx.fill();
            } else {
              const v = value(item); if (v === null) continue;
              const t = model.layer === 'mae' ? v / 60 : (v + 30) / 60;
              const s = Math.max(1, radius * .0105);
              ctx.fillStyle = pal[Math.round(Math.max(0, Math.min(1, t)) * 63)]; ctx.fillRect(x - s / 2, y - s / 2, s, s);
            }
            visible.push({x, y, item});
          }
          if (selected) { const [x, y] = projection(selected.row); ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI * 2); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke(); }
        }
        const names = () => ({random: tr('Random', '随机'), historical: tr('Historical-density', '历史密度'), coverage: tr('Coverage', '均匀覆盖')});
        function describe() {
          if (!selected) { readout.textContent = tr('Tap a point to read its value.', '点击一个点查看数值。'); return; }
          const r = selected.row, where = `${Math.abs(r[1]).toFixed(1)}°${r[1] >= 0 ? 'N' : 'S'}, ${Math.abs(r[0]).toFixed(1)}°${r[0] >= 0 ? 'E' : 'W'}`;
          if (model.layer === 'sampling') readout.textContent = tr(`${where} · ${names()[model.strategy]}: ${r[2]} samples in this 10°×5° block`, `${where} · ${names()[model.strategy]}：此 10°×5° 区块有 ${r[2]} 个样本`);
          else { const v = value(selected); readout.textContent = `${where} · ${names()[model.strategy]}: ${v === null ? '—' : (model.layer === 'delta' && v > 0 ? '+' : '') + v.toFixed(1) + ' µatm'} ${model.layer === 'delta' ? tr('MAE vs random', '相对随机的 MAE') : 'MAE'}`; }
        }
        function legendFor() {
          const s = model.layer === 'sampling';
          const title = s ? tr('Samples per 10°×5° block (all months)', '每个 10°×5° 区块的样本数（全年）') : model.layer === 'mae' ? tr('Mean absolute error · µatm', '平均绝对误差 · µatm') : tr('MAE minus random · µatm', '与随机采样的 MAE 之差 · µatm');
          const ticks = s ? ['1', '10', '20+'] : model.layer === 'mae' ? ['0', '30', '60+'] : ['−30', '0', '+30'];
          legend.innerHTML = `<span>${title}</span><div class="ramp" style="background:linear-gradient(90deg,${stops[model.layer].join(',')})"></div><div class="ramp-ticks">${ticks.map(t => `<span>${t}</span>`).join('')}</div>` +
            (model.layer === 'delta' ? `<div class="key-row"><span>${tr('Green: better than random', '绿色：优于随机')}</span><span>${tr('Coral: worse', '珊瑚色：更差')}</span></div>` : '');
          root.querySelectorAll('[data-globe-layer]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.globeLayer === model.layer)));
          root.querySelectorAll('[data-globe-strategy]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.globeStrategy === model.strategy)));
          root.dataset.layer = model.layer; root.dataset.strategy = model.strategy;
        }
        root.querySelectorAll('[data-globe-layer]').forEach(b => b.addEventListener('click', () => { model.layer = b.dataset.globeLayer; selected = null; legendFor(); describe(); globe.request(); }));
        root.querySelectorAll('[data-globe-strategy]').forEach(b => b.addEventListener('click', () => { model.strategy = b.dataset.globeStrategy; selected = null; legendFor(); describe(); globe.request(); }));
        document.addEventListener('ocs:lang', () => { legendFor(); describe(); });
        legendFor(); describe(); root.dataset.ready = 'true';
      } catch (error) { readout.textContent = tr('The globe could not load.', '地球仪加载失败。'); root.dataset.ready = 'error'; console.warn(error); }
    });
  }

  function start() { if (!window.d3) return console.warn('d3 unavailable'); observationGlobe(); experimentGlobe(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
