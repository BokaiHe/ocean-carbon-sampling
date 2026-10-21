/* Page behaviour and result charts, drawn from frozen JSON only. */
(() => {
  'use strict';
  const tr = (en, zh) => (window.OCS ? window.OCS.tr(en, zh) : en);
  const zh = () => window.OCS && window.OCS.lang === 'zh';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const C = () => ({random: css('--random'), hist: css('--hist'), cov: css('--cov'), base: css('--base'), gap: css('--gap'), teal: css('--teal'), ink: css('--ink'), ink2: css('--ink-2'), muted: css('--muted'), hair: css('--hair'), land: css('--land'), edge: css('--land-edge')});
  const signed = (v, d = 2) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d);
  const json = url => fetch(url).then(r => { if (!r.ok) throw Error(url); return r.json(); });

  /* Chrome: top bar, section highlight, depth gauge, reveals. */
  function chrome() {
    const bar = $('#topbar'), rail = $('.depth-rail'), fill = $('#depth-fill'), depth = $('#depth-value');
    const hero = $('#top');
    const onScroll = () => {
      const past = hero ? hero.getBoundingClientRect().bottom < 60 : true;
      bar.classList.toggle('on', past); rail.classList.toggle('on', past);
      const max = document.documentElement.scrollHeight - innerHeight;
      const t = max > 0 ? Math.min(1, Math.max(0, scrollY / max)) : 0;
      fill.style.height = (t * 100).toFixed(1) + '%';
      depth.textContent = Math.round(t * 4000).toLocaleString('en-US') + ' m';
    };
    addEventListener('scroll', onScroll, {passive: true}); onScroll();
    const links = $$('.topbar-links a');
    const io = new IntersectionObserver(entries => {
      for (const e of entries) if (e.isIntersecting) links.forEach(a => a.toggleAttribute('aria-current', a.hash === '#' + e.target.id || (a.hash === '#findings' && e.target.id.startsWith('f-'))));
    }, {rootMargin: '-40% 0px -55% 0px'});
    $$('main > section[id]').forEach(s => io.observe(s));
    const reveal = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); reveal.unobserve(e.target); } }), {rootMargin: '0px 0px -8% 0px'});
    $$('.chapter-head, .stat, .photo-plate, .flow li, .rule-card, .finding-head, .check, .answer, .limit-grid li').forEach(n => { n.classList.add('reveal'); reveal.observe(n); });
    // Count-up for intro statistics.
    const counter = new IntersectionObserver(entries => entries.forEach(e => {
      if (!e.isIntersecting) return; counter.unobserve(e.target);
      const node = e.target, end = Number(node.dataset.count), suffix = node.dataset.suffix || '';
      if (node.dataset.format === 'quarter' || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      const digits = end % 1 ? 1 : 0, start = performance.now();
      const step = now => { const k = Math.min(1, (now - start) / 1200), v = end * (1 - Math.pow(1 - k, 3));
        node.textContent = v.toLocaleString('en-US', {minimumFractionDigits: digits, maximumFractionDigits: digits}) + suffix; if (k < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    }), {threshold: .6});
    $$('.stat-num[data-count]').forEach(n => counter.observe(n));
  }

  /* Tooltip shared by charts. */
  const tip = document.createElement('div'); tip.className = 'tip'; document.body.append(tip);
  const showTip = (e, html) => { tip.innerHTML = html; tip.classList.add('on'); const x = Math.min(innerWidth - 300, e.clientX + 14); tip.style.left = x + 'px'; tip.style.top = (e.clientY + 14) + 'px'; };
  const hideTip = () => tip.classList.remove('on');
  function hover(sel, html) { sel.on('pointermove', (e, d) => showTip(e, html(d))).on('pointerleave', hideTip); }

  function svgIn(node, height) {
    const width = Math.max(120, node.clientWidth || 280);
    node.innerHTML = '';
    return {svg: d3.select(node).append('svg').attr('viewBox', `0 0 ${width} ${height}`).attr('height', height), width};
  }

  /* Equirectangular map helper for canvases. */
  function flatMap(canvas, land, height) {
    const width = canvas.clientWidth, h = height || width / 2, ratio = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(h * ratio);
    const ctx = canvas.getContext('2d'); ctx.setTransform(ratio, 0, 0, ratio, 0, 0); ctx.clearRect(0, 0, width, h);
    const projection = d3.geoEquirectangular().fitExtent([[2, 2], [width - 2, h - 2]], {type: 'Sphere'});
    const path = d3.geoPath(projection, ctx);
    const c = C();
    return {ctx, projection, width, height: h, sea: () => { ctx.beginPath(); path({type: 'Sphere'}); ctx.fillStyle = css('--sphere'); ctx.fill(); }, land: () => { ctx.beginPath(); path(land); ctx.fillStyle = c.land; ctx.fill(); ctx.strokeStyle = c.edge; ctx.lineWidth = .6; ctx.stroke(); },
      line60: () => { ctx.beginPath(); path({type: 'LineString', coordinates: d3.range(-180, 181, 5).map(x => [x, 60])}); ctx.setLineDash([3, 4]); ctx.strokeStyle = 'rgba(170,220,245,.35)'; ctx.lineWidth = 1; ctx.stroke(); ctx.setLineDash([]); }};
  }

  /* Method: per-block heatmap and samples-per-block histogram for each rule. */
  function miniMaps(globe, land) {
    const c = C(), hue = {random: c.random, historical: c.hist, coverage: c.cov};
    const key = (lon, lat) => `${Math.floor((lon + 180) / 10)}|${Math.floor((lat + 90) / 5)}`;
    const ocean = new Map();
    for (const [lon, lat] of globe.fields) { const k = key(lon, lat); if (!ocean.has(k)) ocean.set(k, [Math.floor((lon + 180) / 10) * 10 - 180, Math.floor((lat + 90) / 5) * 5 - 90]); }
    const bins = [[0, 0, '0'], [1, 2, '1–2'], [3, 4, '3–4'], [5, 6, '5–6'], [7, 8, '7–8'], [9, 12, '9–12'], [13, 20, '13–20'], [21, Infinity, '21+']];
    const stats = {};
    for (const strategy of Object.keys(hue)) {
      const counts = new Map(globe.sampling[strategy].map(([lon, lat, n]) => [key(lon, lat), n]));
      const values = [...ocean.keys()].map(k => counts.get(k) || 0);
      stats[strategy] = {counts, share: bins.map(([lo, hi]) => values.filter(v => v >= lo && v <= hi).length / values.length),
        reached: values.filter(v => v > 0).length, missed: values.filter(v => v === 0).length, max: Math.max(...values)};
    }
    const top = Math.max(...Object.values(stats).flatMap(s => s.share));
    $$('.rule-card').forEach(card => {
      const strategy = card.dataset.rule, s = stats[strategy], canvas = $('.mini-map', card);
      const m = flatMap(canvas, land), {ctx, projection} = m;
      m.sea();
      for (const [k, [x0, y0]] of ocean) {
        const [ax, ay] = projection([x0, y0 + 5]), [bx, by] = projection([x0 + 10, y0]);
        const n = s.counts.get(k) || 0, w = bx - ax - .6, h = by - ay - .6;
        if (n) { ctx.globalAlpha = .18 + .82 * Math.min(1, n / 12); ctx.fillStyle = hue[strategy]; ctx.fillRect(ax, ay, w, h); }
        else { ctx.globalAlpha = .72; ctx.fillStyle = '#d6e2ea'; ctx.fillRect(ax, ay, w, h); }
      }
      // Opaque land is drawn last so coastal sampling blocks cannot show through it.
      ctx.globalAlpha = 1; m.land();
      // Histogram of samples per block, on one shared scale across the three cards.
      const node = $('.rule-hist', card), {svg, width} = svgIn(node, 78);
      const x = d3.scaleBand().domain(bins.map(b => b[2])).range([0, width]).padding(.18), y = d3.scaleLinear().domain([0, top]).range([52, 4]);
      svg.selectAll('rect').data(s.share).join('rect').attr('x', (d, i) => x(bins[i][2])).attr('width', x.bandwidth()).attr('y', d => y(d)).attr('height', d => 52 - y(d)).attr('rx', 2)
        .attr('fill', (d, i) => i === 0 ? '#d6e2ea' : hue[strategy]).attr('opacity', (d, i) => i === 0 ? .7 : .85);
      svg.selectAll('text').data(bins).join('text').attr('class', 'small').attr('x', b => x(b[2]) + x.bandwidth() / 2).attr('y', 70).attr('text-anchor', 'middle').text(b => b[2]);
      hover(svg.selectAll('rect'), d => `${(d * 100).toFixed(1)}% ${tr('of ocean blocks', '的海洋区块')}`);
      $('.rule-meta', card).innerHTML = tr(
        `<span>Samples per 10°×5° block</span><div><b>${s.reached.toLocaleString('en-US')}</b> reached · <b class="miss">${s.missed}</b> missed · max <b>${s.max}</b></div>`,
        `<span>每个 10°×5° 区块的样本数</span><div>覆盖 <b>${s.reached.toLocaleString('en-US')}</b> 个 · 漏掉 <b class="miss">${s.missed}</b> 个 · 最多 <b>${s.max}</b></div>`);
    });
  }

  /* Finding 1: paired dumbbells. */
  let f1Protocol = 'hidden';
  function f1(charts) {
    const node = $('#f1-chart'), rows = charts.pairs[f1Protocol], c = C();
    const rowH = f1Protocol === 'hidden' ? 64 : 28, top = 10, bottom = 40;
    const {svg, width} = svgIn(node, top + rows.length * rowH + bottom);
    const left = f1Protocol === 'hidden' ? 60 : 92, right = 24;
    const all = rows.flatMap(r => [r.random, r.historical]);
    const x = d3.scaleLinear().domain([Math.floor(d3.min(all) - .5), Math.ceil(d3.max(all) + .5)]).range([left, width - right]);
    const h = top + rows.length * rowH;
    svg.append('g').attr('class', 'grid').selectAll('line').data(x.ticks(6)).join('line').attr('x1', x).attr('x2', x).attr('y1', top).attr('y2', h);
    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${h})`).call(d3.axisBottom(x).ticks(6).tickSize(0).tickPadding(10));
    svg.append('text').attr('x', width - right).attr('y', h + 36).attr('text-anchor', 'end').text(tr('MAE · µatm · lower is better', 'MAE · µatm · 越低越好'));
    const g = svg.append('g').selectAll('g').data(rows).join('g').attr('transform', (d, i) => `translate(0,${top + i * rowH + rowH / 2})`);
    g.append('text').attr('x', left - 12).attr('dy', '.35em').attr('text-anchor', 'end').attr('class', f1Protocol === 'hidden' ? null : 'small')
      .text(d => f1Protocol === 'hidden' ? d.year : `${d.year} · F${d.fold}`);
    g.append('line').attr('x1', d => x(d.random)).attr('x2', d => x(d.random)).attr('stroke', 'rgba(170,220,245,.35)').attr('stroke-width', f1Protocol === 'hidden' ? 4 : 2.5)
      .transition().duration(900).delay((d, i) => i * 40).attr('x2', d => x(d.historical));
    const r = f1Protocol === 'hidden' ? 8 : 5;
    g.append('circle').attr('cx', d => x(d.random)).attr('r', r).attr('fill', c.random);
    g.append('circle').attr('cx', d => x(d.random)).attr('r', r).attr('fill', c.hist).transition().duration(900).delay((d, i) => i * 40).attr('cx', d => x(d.historical));
    if (f1Protocol === 'hidden') {
      g.append('text').attr('x', d => x(d.random)).attr('y', -16).attr('text-anchor', 'middle').style('fill', c.random).text(d => d.random.toFixed(2));
      g.append('text').attr('x', d => x(d.historical)).attr('y', -16).attr('text-anchor', 'middle').style('fill', c.hist).text(d => d.historical.toFixed(2));
    }
    hover(g.append('rect').attr('x', left).attr('y', -rowH / 2).attr('width', width - left - right).attr('height', rowH).attr('fill', 'transparent'),
      d => `<b>${d.year}${f1Protocol === 'block' ? ' · F' + d.fold : ''}</b><br>${tr('Random', '随机')} ${d.random.toFixed(3)} · ${tr('Historical', '历史密度')} ${d.historical.toFixed(3)}<br>Δ ${signed(d.historical - d.random, 3)} µatm`);
    const row = charts.mask_audit.rows.find(r => r.mask === 'm1' && r.protocol === f1Protocol && r.comparison === 'historical_density');
    $('#f1-number').textContent = '+' + row.relative_mae_pct.toFixed(1) + '%';
    $$('[data-f1]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.f1 === f1Protocol)));
  }

  /* Finding 2: coverage − random across the three ocean masks. */
  function f2(charts) {
    const node = $('#f2-chart'), c = C();
    const masks = ['m0', 'm1', 'm2'];
    const labels = {m0: tr('Original model domain', '原模式海域'), m1: tr('Connected ocean', '连通海洋'), m2: tr('Open ocean', '开阔大洋')};
    const rows = masks.map(m => charts.mask_audit.rows.find(r => r.mask === m && r.protocol === 'hidden' && r.comparison === 'spatial_coverage'));
    const {svg, width} = svgIn(node, 300);
    const left = 44, right = 10, top = 20, h = 240;
    const x0 = d3.scaleBand().domain(masks).range([left, width - right]).paddingInner(.28).paddingOuter(.1);
    const x1 = d3.scaleBand().domain(['mae', 'rmse']).range([0, x0.bandwidth()]).padding(.12);
    const y = d3.scaleLinear().domain([-2, 1]).range([h, top]);
    svg.append('g').attr('class', 'grid').selectAll('line').data(y.ticks(6)).join('line').attr('x1', left).attr('x2', width - right).attr('y1', y).attr('y2', y);
    svg.append('g').attr('class', 'axis').attr('transform', `translate(${left},0)`).call(d3.axisLeft(y).ticks(6).tickSize(0).tickPadding(8).tickFormat(v => signed(v, 1)));
    svg.append('line').attr('class', 'zero').attr('x1', left).attr('x2', width - right).attr('y1', y(0)).attr('y2', y(0));
    const g = svg.append('g').selectAll('g').data(rows).join('g').attr('transform', d => `translate(${x0(d.mask)},0)`);
    const bars = g.selectAll('rect').data(d => [{k: 'mae', v: d.difference_mae ?? d.comparator_mae - d.random_mae, d}, {k: 'rmse', v: d.difference_rmse, d}]).join('rect')
      .attr('x', d => x1(d.k)).attr('width', x1.bandwidth()).attr('rx', 4).attr('fill', d => d.k === 'mae' ? c.ink2 : c.cov).attr('y', y(0)).attr('height', 0);
    bars.transition().duration(900).attr('y', d => y(Math.max(0, d.v))).attr('height', d => Math.abs(y(d.v) - y(0)));
    g.selectAll('text.v').data(d => [{k: 'mae', v: d.comparator_mae - d.random_mae}, {k: 'rmse', v: d.difference_rmse}]).join('text').attr('class', 'v')
      .attr('x', d => x1(d.k) + x1.bandwidth() / 2).attr('y', d => d.v >= 0 ? y(d.v) - 6 : y(d.v) + 16).attr('text-anchor', 'middle').style('fill', c.ink).style('font-weight', 600).text(d => signed(d.v, 2));
    svg.append('g').selectAll('text').data(masks).join('text').attr('x', m => x0(m) + x0.bandwidth() / 2).attr('y', h + 30).attr('text-anchor', 'middle').style('fill', c.ink).text(m => labels[m]);
    svg.append('g').selectAll('text').data(rows).join('text').attr('x', d => x0(d.mask) + x0.bandwidth() / 2).attr('y', h + 50).attr('text-anchor', 'middle').attr('class', 'small')
      .text(d => tr(`${charts.mask_audit.locations_below_60n[d.mask].toLocaleString('en-US')} locations`, `${charts.mask_audit.locations_below_60n[d.mask].toLocaleString('en-US')} 个位置`));
    hover(bars, d => `<b>${labels[d.d.mask]}</b><br>${d.k === 'mae' ? 'MAE' : 'RMSE'} ${signed(d.v, 3)} µatm`);
  }

  function maskSpark(charts) {
    const node = $('#mask-spark'), c = C();
    const rows = ['m0', 'm1', 'm2'].map(m => charts.mask_audit.rows.find(r => r.mask === m && r.protocol === 'hidden' && r.comparison === 'historical_density'));
    const {svg, width} = svgIn(node, 54);
    const x = d3.scaleBand().domain(rows.map(r => r.mask)).range([0, width]).padding(.25), y = d3.scaleLinear().domain([0, 30]).range([40, 4]);
    svg.selectAll('rect').data(rows).join('rect').attr('x', d => x(d.mask)).attr('width', x.bandwidth()).attr('y', d => y(d.relative_mae_pct)).attr('height', d => 40 - y(d.relative_mae_pct)).attr('rx', 3).attr('fill', c.hist).attr('opacity', (d, i) => .55 + i * .2);
    svg.selectAll('text').data(rows).join('text').attr('x', d => x(d.mask) + x.bandwidth() / 2).attr('y', 53).attr('text-anchor', 'middle').attr('class', 'small').style('fill', c.ink).text(d => '+' + d.relative_mae_pct.toFixed(1) + '%');
  }

  /* Finding 3: network augmentation in the open ocean (M2). */
  const aug = {arm: 'gap_addition', seed: '0'};
  function f3Map(data, land) {
    const canvas = $('#aug-map'), c = C();
    const m = flatMap(canvas, land, canvas.clientWidth / 2.05);
    const {ctx, projection, width} = m;
    m.sea();
    const cell = Math.max(1.5, width / 360);
    ctx.fillStyle = 'rgba(255,194,94,.07)';
    for (const [lon, lat] of data.map.gap_locations) { const [x, y] = projection([lon, lat]); ctx.fillRect(x - cell / 2, y - cell / 2, cell, cell); }
    m.land();
    ctx.fillStyle = c.base; ctx.globalAlpha = .7;
    for (const [lon, lat, n] of data.map.baseline) { const [x, y] = projection([lon, lat]); ctx.beginPath(); ctx.arc(x, y, .6 + Math.sqrt(n) * .35 * width / 900, 0, Math.PI * 2); ctx.fill(); }
    ctx.globalAlpha = 1;
    const colour = aug.arm === 'gap_addition' ? c.gap : c.random;
    ctx.fillStyle = colour; ctx.strokeStyle = 'rgba(2,12,20,.8)'; ctx.lineWidth = .6;
    for (const [lon, lat] of data.map.additions[aug.arm][aug.seed]) { const [x, y] = projection([lon, lat]); ctx.beginPath(); ctx.arc(x, y, Math.max(1.8, width / 380), 0, Math.PI * 2); ctx.fill(); ctx.stroke(); }
    m.line60();
    $('.dot.added').style.background = colour;
    $('#aug-added-label').textContent = aug.arm === 'gap_addition' ? tr('+1,000 in historical gaps', '+1,000 个空白区新点') : tr('+1,000 random', '+1,000 个随机新点');
    $$('[data-aug-arm]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.augArm === aug.arm)));
    $$('#aug-seeds button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.seed === aug.seed)));
  }
  const domains = ['global_unobserved', 'historical_gap', 'previously_observed_locations'];
  const domainLabel = d => ({global_unobserved: tr('All unobserved', '全部未观测'), historical_gap: tr('Historical gaps', '历史空白区'), previously_observed_locations: tr('Previously observed', '原先有观测处')}[d]);
  function f3Bars(data) {
    const node = $('#f3-bars'), c = C();
    const arms = ['baseline', 'random_addition', 'gap_addition'], colours = {baseline: c.base, random_addition: c.random, gap_addition: c.gap};
    const mean = (arm, dom) => d3.mean(data.scores.filter(s => s.arm === arm && s.domain === dom), s => s.rmse);
    const rows = domains.flatMap(dom => arms.map(arm => ({dom, arm, v: mean(arm, dom)})));
    const {svg, width} = svgIn(node, 210);
    const left = 112, right = 46, y0 = d3.scaleBand().domain(domains).range([4, 200]).paddingInner(.3), y1 = d3.scaleBand().domain(arms).range([0, y0.bandwidth()]).padding(.12);
    const x = d3.scaleLinear().domain([0, d3.max(rows, r => r.v) * 1.05]).range([left, width - right]);
    svg.append('g').selectAll('text').data(domains).join('text').attr('x', left - 10).attr('y', d => y0(d) + y0.bandwidth() / 2).attr('dy', '.35em').attr('text-anchor', 'end').style('fill', c.ink).text(domainLabel);
    const bars = svg.append('g').selectAll('rect').data(rows).join('rect').attr('x', left).attr('y', d => y0(d.dom) + y1(d.arm)).attr('height', y1.bandwidth()).attr('rx', 3).attr('fill', d => colours[d.arm]).attr('width', 0);
    bars.transition().duration(800).attr('width', d => x(d.v) - left);
    svg.append('g').selectAll('text').data(rows).join('text').attr('x', d => x(d.v) + 5).attr('y', d => y0(d.dom) + y1(d.arm) + y1.bandwidth() / 2).attr('dy', '.35em').attr('class', 'small').text(d => d.v.toFixed(1));
    hover(bars, d => `<b>${domainLabel(d.dom)}</b><br>${{baseline: tr('Existing network', '现有网络'), random_addition: tr('+ random', '+ 随机'), gap_addition: tr('+ gaps', '+ 空白区')}[d.arm]}: RMSE ${d.v.toFixed(3)} µatm`);
  }
  function f3Dots(data) {
    const node = $('#f3-dots'), c = C();
    const rows = data.paired.filter(p => p.metric === 'rmse' && p.contrast === 'random_minus_gap');
    const {svg, width} = svgIn(node, 190);
    const left = 112, right = 16, axisY = 132, y = d3.scaleBand().domain(domains).range([6, axisY - 4]).padding(.3);
    const ext = d3.max(rows, r => Math.abs(r.improvement)) * 1.15;
    const x = d3.scaleLinear().domain([-ext, ext]).range([left, width - right]);
    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${axisY})`).call(d3.axisBottom(x).ticks(5).tickSize(0).tickPadding(8).tickFormat(v => signed(v, 1)));
    svg.append('line').attr('class', 'zero').attr('x1', x(0)).attr('x2', x(0)).attr('y1', 0).attr('y2', axisY);
    svg.append('g').selectAll('text').data(domains).join('text').attr('x', left - 10).attr('y', d => y(d) + y.bandwidth() / 2).attr('dy', '.35em').attr('text-anchor', 'end').style('fill', c.ink).text(domainLabel);
    // Small vertical offset per seed so overlapping seeds stay visible.
    const dots = svg.append('g').selectAll('circle').data(rows).join('circle').attr('cx', x(0)).attr('cy', d => y(d.domain) + y.bandwidth() / 2 + (d.seed - 2) * 3.2).attr('r', 5.5)
      .attr('fill', d => d.improvement > 0 ? c.gap : c.random).attr('stroke', 'rgba(2,12,20,.8)');
    dots.transition().duration(800).delay((d, i) => i * 30).attr('cx', d => x(d.improvement));
    const means = domains.map(dom => ({dom, v: d3.mean(rows.filter(r => r.domain === dom), r => r.improvement)}));
    svg.append('g').selectAll('line').data(means).join('line').attr('x1', d => x(d.v)).attr('x2', d => x(d.v)).attr('y1', d => y(d.dom) - 4).attr('y2', d => y(d.dom) + y.bandwidth() + 4).attr('stroke', c.ink).attr('stroke-width', 2);
    svg.append('text').attr('x', width - right).attr('y', 184).attr('text-anchor', 'end').attr('class', 'small').text(tr('RMSE · µatm · white tick = mean of 5 seeds', 'RMSE · µatm · 白线为 5 个种子的均值'));
    hover(dots, d => `<b>${domainLabel(d.domain)}</b> · ${tr('seed', '种子')} ${d.seed}<br>${signed(d.improvement, 3)} µatm`);
  }

  async function start() {
    chrome();
    if (!window.d3) return;
    const land = await json('data/globe-land.json').catch(() => null);
    const charts = await json('data/chart-data.json');
    const draw = {};
    draw.f1 = () => f1(charts); draw.f2 = () => f2(charts); draw.spark = () => maskSpark(charts);
    $$('[data-f1]').forEach(b => b.addEventListener('click', () => { f1Protocol = b.dataset.f1; draw.f1(); }));
    let globeData = null, augData = null;
    const lazy = (node, fn) => { const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); Promise.resolve().then(fn).catch(error => console.error('chart failed', error)); } }, {rootMargin: '400px'}); io.observe(node); };
    lazy($('.rule-grid'), async () => { globeData = await json('data/globe-data.json'); draw.mini = () => miniMaps(globeData, land); draw.mini(); });
    lazy($('#f-augment'), async () => {
      augData = await json('data/augmentation.json');
      $('#aug-seeds').replaceChildren(...augData.metadata.seeds.map(s => { const b = document.createElement('button'); b.type = 'button'; b.dataset.seed = String(s); b.textContent = (zh() ? '种子 ' : 'Seed ') + s; b.onclick = () => { aug.seed = String(s); f3Map(augData, land); }; return b; }));
      $$('[data-aug-arm]').forEach(b => b.onclick = () => { aug.arm = b.dataset.augArm; f3Map(augData, land); });
      draw.aug = () => { f3Map(augData, land); f3Bars(augData); f3Dots(augData); }; draw.aug();
    });
    draw.f1(); draw.f2(); draw.spark();
    const all = () => Object.values(draw).forEach(fn => fn());
    // Redraw when a chart's own box changes width, not only the window.
    let frame = 0; const widths = new WeakMap();
    const resize = new ResizeObserver(entries => {
      if (!entries.some(e => { const w = Math.round(e.contentRect.width), old = widths.get(e.target); widths.set(e.target, w); return old !== undefined && old !== w; })) return;
      cancelAnimationFrame(frame); frame = requestAnimationFrame(all);
    });
    $$('.chart, .mask-spark, .mini-map, #aug-map').forEach(n => resize.observe(n));
    document.addEventListener('ocs:lang', () => { all(); if (augData) $$('#aug-seeds button').forEach(b => b.textContent = (zh() ? '种子 ' : 'Seed ') + b.dataset.seed); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
