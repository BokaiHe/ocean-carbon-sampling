/* Recorded navigation example. Independent of all OSSE data and scores. */
(() => {
  'use strict';
  const root = document.querySelector('#voyage-explorer');
  if (!root) return;
  const canvas = document.querySelector('#voyage-globe');
  const slider = document.querySelector('#voyage-time');
  const readout = document.querySelector('#voyage-readout');
  const controls = root.querySelectorAll('button,input');
  async function initialize() {
    try {
      if (!window.d3) throw new Error('Projection library unavailable');
      const [data, land] = await Promise.all(['data/voyage-track.json', 'data/globe-land.json'].map(async url => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Unable to load ${url}`);
        return response.json();
      }));
      const d3 = window.d3, ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('Canvas unavailable');
      const points = data.points, breaks = new Set(data.break_before);
      const coordinates = points.map(p => [p[1], p[2]]);
      const projection = d3.geoOrthographic().clipAngle(90).precision(.3);
      const path = d3.geoPath(projection, ctx);
      const grid = d3.geoGraticule().step([30, 15])();
      let rotation = [25, 53, 0], index = Math.floor(points.length / 2);
      let width = 0, frame = 0, pointer = null;
      const track = end => {
        const lines = [[]];
        for (let i = 0; i <= end; i++) {
          if (breaks.has(i)) lines.push([]);
          lines[lines.length - 1].push(coordinates[i]);
        }
        return {type: 'MultiLineString', coordinates: lines.filter(line => line.length > 1)};
      };
      const fullTrack = track(points.length - 1);
      function stroke(geometry, colour, thickness) {
        ctx.beginPath(); path(geometry); ctx.strokeStyle = colour;
        ctx.lineWidth = thickness; ctx.lineJoin = 'round'; ctx.stroke();
      }
      function draw() {
        frame = 0;
        const size = Math.min(660, canvas.getBoundingClientRect().width);
        if (!size) return;
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        if (width !== size || canvas.width !== Math.round(size * ratio)) {
          width = size; canvas.width = Math.round(size * ratio); canvas.height = Math.round(size * ratio);
        }
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        ctx.clearRect(0, 0, size, size);
        projection.translate([size / 2, size / 2]).scale(size * .45).rotate(rotation);
        const ocean = ctx.createRadialGradient(size * .35, size * .3, 5, size / 2, size / 2, size * .48);
        ocean.addColorStop(0, '#497887'); ocean.addColorStop(1, '#173e4d');
        ctx.beginPath(); path({type:'Sphere'}); ctx.fillStyle = ocean; ctx.fill();
        stroke(grid, '#9abac030', .7);
        stroke(fullTrack, '#aec5cb', 1.5);
        stroke(track(index), '#f2b879', 2.7);
        ctx.beginPath(); path(land); ctx.fillStyle = '#ffffff'; ctx.fill();
        ctx.strokeStyle = '#101c23'; ctx.lineWidth = 1.1; ctx.stroke();
        const visible = d3.geoDistance(coordinates[index], [-rotation[0], -rotation[1]]) < Math.PI / 2;
        if (visible) {
          const [x, y] = projection(coordinates[index]);
          ctx.save(); ctx.translate(x, y);
          ctx.beginPath(); ctx.arc(0, 0, 16, 0, Math.PI * 2); ctx.fillStyle = '#f2b879'; ctx.fill();
          // Illustrative boat, not measured heading. Position is a source record.
          ctx.beginPath(); ctx.moveTo(-11, 2); ctx.lineTo(11, 2); ctx.lineTo(7, 8); ctx.lineTo(-7, 8); ctx.closePath();
          ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.strokeStyle = '#163642'; ctx.lineWidth = 1.4; ctx.stroke();
          ctx.fillRect(-5, -5, 10, 7); ctx.strokeRect(-5, -5, 10, 7);
          ctx.beginPath(); ctx.moveTo(0, -5); ctx.lineTo(0, -11); ctx.stroke(); ctx.restore();
        }
        canvas.dataset.rotation = rotation.join(','); canvas.dataset.index = String(index);
        canvas.dataset.shipVisible = String(visible);
      }
      function requestDraw() { if (!frame) frame = requestAnimationFrame(draw); }
      function select(value) {
        index = Math.max(0, Math.min(points.length - 1, value)); slider.value = String(index);
        const [stamp, lon, lat] = points[index];
        const text = `${stamp.replace('T', ' · ')} · ${Math.abs(lat).toFixed(2)}°${lat < 0 ? 'S' : 'N'}, ${Math.abs(lon).toFixed(2)}°${lon < 0 ? 'W' : 'E'}`;
        readout.textContent = text; slider.setAttribute('aria-valuetext', text); requestDraw();
      }
      function turn(dx, dy = 0) {
        rotation[0] = ((rotation[0] + dx + 180) % 360 + 360) % 360 - 180;
        rotation[1] = Math.max(-85, Math.min(85, rotation[1] + dy)); requestDraw();
      }
      function reset() { rotation = [25, 53, 0]; requestDraw(); }
      slider.max = String(points.length - 1);
      slider.addEventListener('input', () => select(Number(slider.value)));
      document.querySelector('#voyage-start').onclick = () => select(0);
      document.querySelector('#voyage-middle').onclick = () => select(Math.floor(points.length / 2));
      document.querySelector('#voyage-end').onclick = () => select(points.length - 1);
      document.querySelector('#voyage-left').onclick = () => turn(-20);
      document.querySelector('#voyage-right').onclick = () => turn(20);
      document.querySelector('#voyage-reset').onclick = reset;
      document.querySelector('#voyage-locate').onclick = () => { rotation = [-points[index][1], -points[index][2], 0]; requestDraw(); };
      canvas.addEventListener('keydown', event => {
        const keys = {ArrowLeft: () => turn(-10), ArrowRight: () => turn(10), ArrowUp: () => turn(0, -10), ArrowDown: () => turn(0, 10), Home: reset};
        if (keys[event.key]) { event.preventDefault(); keys[event.key](); }
      });
      canvas.addEventListener('pointerdown', event => {
        if (pointer || event.button !== 0) return;
        pointer = {id: event.pointerId, x: event.clientX, y: event.clientY}; canvas.setPointerCapture(event.pointerId);
      });
      canvas.addEventListener('pointermove', event => {
        if (!pointer || pointer.id !== event.pointerId) return;
        turn((event.clientX - pointer.x) * .35, -(event.clientY - pointer.y) * .35);
        pointer.x = event.clientX; pointer.y = event.clientY;
      });
      function release(event) {
        if (!pointer || pointer.id !== event.pointerId) return;
        if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
        pointer = null;
      }
      canvas.addEventListener('pointerup', release); canvas.addEventListener('pointercancel', release);
      new ResizeObserver(requestDraw).observe(canvas);
      controls.forEach(control => control.disabled = false);
      select(index); root.dataset.ready = 'true';
    } catch (error) {
      root.dataset.ready = 'error';
      readout.textContent = 'The voyage globe could not load. The original navigation table and source link below remain available.';
      controls.forEach(control => control.disabled = true);
      console.warn(error.message);
    }
  }
  const loader = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting)) { loader.disconnect(); initialize(); }
  }, {rootMargin: '500px'});
  loader.observe(root);
})();
