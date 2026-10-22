// Render README media (screenshots + GIFs) from the built site in dist/.
//
// Serves dist/ locally, drives headless Chrome over the DevTools protocol (Node >= 22
// for the built-in WebSocket; no extra npm packages) and encodes GIFs with ffmpeg.
// For GIFs, requestAnimationFrame is swapped for a manual clock after load, so each
// frame advances the animation by exactly 1/FPS second however long a capture takes.
//
// Usage:  npm run build && node scripts/readme_media.mjs
// Env:    CHROME=path/to/chrome   FFMPEG=path/to/ffmpeg
import {spawn, execFileSync} from 'node:child_process';
import {createServer} from 'node:http';
import {mkdirSync, rmSync, writeFileSync, existsSync, readFileSync, statSync} from 'node:fs';
import {join, resolve, extname} from 'node:path';
import {tmpdir} from 'node:os';

const ROOT = resolve(import.meta.dirname, '..');
const DIST = join(ROOT, 'dist');
const OUT = join(ROOT, 'assets', 'readme');
const FRAMES = join(tmpdir(), 'ocs-readme-frames');
const CHROME = process.env.CHROME || [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
].find(p => existsSync(p));
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const PORT = 9334, HTTP = 8790, WIDTH = 1240;
const sleep = ms => new Promise(r => setTimeout(r, ms));
if (!existsSync(join(DIST, 'index.html'))) throw new Error('Run `npm run build` first');

const types = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.mp4': 'video/mp4', '.svg': 'image/svg+xml'};
const server = createServer((req, res) => {
  let path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (path.endsWith('/')) path += 'index.html';
  const file = join(DIST, path);
  if (!file.startsWith(DIST) || !existsSync(file) || statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, {'content-type': types[extname(file)] || 'application/octet-stream'});
  res.end(readFileSync(file));
}).listen(HTTP);

async function chrome() {
  const dir = join(tmpdir(), 'ocs-readme-chrome'); rmSync(dir, {recursive: true, force: true});
  const proc = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--autoplay-policy=no-user-gesture-required',
    `--remote-debugging-port=${PORT}`, `--user-data-dir=${dir}`, 'about:blank'], {stdio: 'ignore'});
  for (let i = 0; i < 50; i++) {
    try { const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const pg = list.find(t => t.type === 'page'); if (pg) return {proc, ws: pg.webSocketDebuggerUrl}; } catch {}
    await sleep(200);
  }
  throw new Error('Chrome did not start');
}

function cdp(url) {
  const ws = new WebSocket(url); let id = 0; const pending = new Map(), waiters = [];
  ws.onmessage = ev => { const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { const {res, rej} = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); }
    else if (m.method) waiters.filter(w => w.method === m.method).forEach(w => { waiters.splice(waiters.indexOf(w), 1); w.res(m.params); }); };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, {res, rej}); ws.send(JSON.stringify({id: i, method, params})); });
  const once = method => new Promise(res => waiters.push({method, res}));
  return new Promise(r => { ws.onopen = () => r({send, once, close: () => ws.close()}); });
}

async function evaluate(c, expression) {
  const r = await c.send('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true});
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || 'evaluate failed');
  return r.result.value;
}

// Scroll an element into view, let lazy charts draw, and return its page rectangle.
async function frame(c, selector, pad = 0) {
  return evaluate(c, `(async () => {
    const el = document.querySelector(${JSON.stringify(selector)});
    el.scrollIntoView({block: 'center'}); await new Promise(r => setTimeout(r, 2200));
    document.querySelectorAll('.reveal').forEach(n => n.classList.add('in'));
    await new Promise(r => setTimeout(r, 400));
    const b = el.getBoundingClientRect();
    return {x: Math.max(0, b.left - ${pad}), y: b.top + scrollY - ${pad}, width: b.width + 2 * ${pad}, height: b.height + 2 * ${pad}};
  })()`);
}

async function shot(c, selector, name, {pad = 12, scale = 1} = {}) {
  const clip = await frame(c, selector, pad);
  const {data} = await c.send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true, clip: {...clip, scale}});
  writeFileSync(join(OUT, name), Buffer.from(data, 'base64'));
  console.log(`${name}: ${Math.round(clip.width)}×${Math.round(clip.height)}`);
  return clip;
}

function gif(name, fps, width, colors = 128, dither = 'sierra2_4a') {
  execFileSync(FFMPEG, ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', join(FRAMES, 'f%04d.png'),
    '-vf', `scale=${width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=${colors}:stats_mode=diff[p];[b][p]paletteuse=dither=${dither}:diff_mode=rectangle`,
    '-loop', '0', join(OUT, name)]);
  console.log(`${name}: ${(statSync(join(OUT, name)).size / 1e6).toFixed(1)} MB`);
}

mkdirSync(OUT, {recursive: true});
const {proc, ws} = await chrome();
const c = await cdp(ws);
try {
  await c.send('Page.enable'); await c.send('Runtime.enable');
  await c.send('Emulation.setDeviceMetricsOverride', {width: WIDTH, height: 820, deviceScaleFactor: 1.5, mobile: false});
  await c.send('Page.addScriptToEvaluateOnNewDocument', {source: "try { localStorage.setItem('ocs-lang', 'en'); } catch (e) {}"});
  const loaded = c.once('Page.loadEventFired');
  await c.send('Page.navigate', {url: `http://127.0.0.1:${HTTP}/`});
  await loaded;
  // Give the hero video a chance to start (external URL); the dark fallback is fine otherwise.
  await evaluate(c, `new Promise(r => { const v = document.getElementById('hero-video'); if (!v) return r();
    const done = () => setTimeout(r, 1500); v.addEventListener('playing', done, {once: true}); setTimeout(r, 9000); })`);
  const {data} = await c.send('Page.captureScreenshot', {format: 'jpeg', quality: 82, clip: {x: 0, y: 0, width: WIDTH, height: 820, scale: 1}});
  writeFileSync(join(OUT, 'hero.jpg'), Buffer.from(data, 'base64'));
  console.log('hero.jpg');

  // Keep chrome out of the section shots.
  await evaluate(c, `(() => { const s = document.createElement('style');
    s.textContent = '.topbar,.depth-rail,.tip{display:none!important}'; document.head.append(s); })()`);
  await shot(c, '.rule-grid', 'rules.png', {pad: 2});
  await shot(c, '#f-history', 'finding1.png', {pad: 0});
  await shot(c, '#f-coverage', 'finding2.png', {pad: 0});
  await shot(c, '#f-augment', 'finding3.png', {pad: 0});
  await shot(c, '#checks', 'robustness.png', {pad: 0});
  await shot(c, '#conclusion', 'conclusion.png', {pad: 0});

  // Augmentation map: alternate the two addition rules.
  rmSync(FRAMES, {recursive: true, force: true}); mkdirSync(FRAMES, {recursive: true});
  const card = await frame(c, '.aug-map-card', 0);
  let n = 0;
  for (const arm of ['random_addition', 'gap_addition']) {
    await evaluate(c, `document.querySelector('[data-aug-arm="${arm}"]').click()`); await sleep(500);
    const {data: img} = await c.send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true, clip: {...card, scale: 1}});
    for (let k = 0; k < 3; k++) writeFileSync(join(FRAMES, `f${String(n++).padStart(4, '0')}.png`), Buffer.from(img, 'base64'));
  }
  gif('augment.gif', 2, 900);

  // SOCAT globe: manual clock so the idle spin advances one fixed step per frame.
  rmSync(FRAMES, {recursive: true, force: true}); mkdirSync(FRAMES, {recursive: true});
  const globe = await frame(c, '#observation-globe', 4);
  await evaluate(c, `(() => { let id = 0, t = performance.now(); const q = new Map();
    window.requestAnimationFrame = cb => { q.set(++id, cb); return id; };
    window.cancelAnimationFrame = i => q.delete(i);
    window.__step = dt => { t += dt; const cbs = [...q.values()]; q.clear(); cbs.forEach(cb => cb(t)); }; })()`);
  const FPS = 15;
  for (let i = 0; i < 60; i++) {
    await evaluate(c, `__step(${1000 / FPS}); __step(0)`);
    const {data: img} = await c.send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true, clip: {...globe, scale: 0.7}});
    writeFileSync(join(FRAMES, `f${String(i).padStart(4, '0')}.png`), Buffer.from(img, 'base64'));
  }
  gif('globe.gif', FPS, 460, 64, 'bayer:bayer_scale=3');
} finally {
  c.close(); proc.kill(); server.close();
  rmSync(FRAMES, {recursive: true, force: true});
}
