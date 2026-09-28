/* Fixed-view navigation illustration. Independent of OSSE observations and scores. */
(() => {
  'use strict';
  const root = document.querySelector('#voyage-explorer');
  if (!root) return;
  const canvas = document.querySelector('#voyage-globe');
  const readout = document.querySelector('#voyage-readout');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const LOOP_MS = 32000;
  let inView = false, loaded = false, frame = 0, previous = null, elapsed = 0;
  let data, land, ctx, projection, path, grid, coordinates, stamps, fullTrack;
  let segments, index = 0, lastPaint = 0, width = 0;
  function track(end) {
    const lines = [[]];
    for (let i = 0; i <= end; i++) {
      if (segments.has(i)) lines.push([]);
      lines[lines.length - 1].push(coordinates[i]);
    }
    return {type:'MultiLineString', coordinates:lines.filter(line=>line.length>1)};
  }
  function stroke(geometry, colour, thickness) {
    ctx.beginPath(); path(geometry); ctx.strokeStyle=colour; ctx.lineWidth=thickness;
    ctx.lineJoin='round'; ctx.stroke();
  }
  function draw() {
    if (!loaded) return;
    const size = canvas.getBoundingClientRect().width;
    if (!size) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    if (width !== size || canvas.width !== Math.round(size*ratio)) {
      width=size; canvas.width=Math.round(size*ratio); canvas.height=Math.round(size*ratio);
    }
    ctx.setTransform(ratio,0,0,ratio,0,0); ctx.clearRect(0,0,size,size);
    projection.translate([size/2,size/2]).scale(size*.45);
    const ocean=ctx.createRadialGradient(size*.35,size*.3,5,size/2,size/2,size*.48);
    ocean.addColorStop(0,'#497887'); ocean.addColorStop(1,'#173e4d');
    ctx.beginPath();path({type:'Sphere'});ctx.fillStyle=ocean;ctx.fill();
    stroke(grid,'#9abac030',.7);stroke(fullTrack,'#aec5cb',1.4);
    stroke(track(index),'#f2b879',2.5);
    ctx.beginPath();path(land);ctx.fillStyle='#ffffff';ctx.fill();
    ctx.strokeStyle='#101c23';ctx.lineWidth=1.1;ctx.stroke();
    const visible=d3.geoDistance(coordinates[index],[-25,-53])<Math.PI/2;
    if (visible) {
      const [x,y]=projection(coordinates[index]);ctx.save();ctx.translate(x,y);
      ctx.beginPath();ctx.arc(0,0,14,0,Math.PI*2);ctx.fillStyle='#f2b879';ctx.fill();
      ctx.beginPath();ctx.moveTo(-10,2);ctx.lineTo(10,2);ctx.lineTo(6,8);ctx.lineTo(-6,8);ctx.closePath();
      ctx.fillStyle='#ffffff';ctx.fill();ctx.strokeStyle='#163642';ctx.lineWidth=1.4;ctx.stroke();
      ctx.fillRect(-4,-5,8,7);ctx.strokeRect(-4,-5,8,7);
      ctx.beginPath();ctx.moveTo(0,-5);ctx.lineTo(0,-10);ctx.stroke();ctx.restore();
    }
    canvas.dataset.index=String(index);canvas.dataset.shipVisible=String(visible);
    const label=data.points[index][0].slice(0,10);
    if (readout.textContent!==label) readout.textContent=label;
  }
  function chooseRecord() {
    // Step through real timestamps, never interpolate an invented ship position.
    const target=stamps[0]+(elapsed/LOOP_MS)*(stamps.at(-1)-stamps[0]);
    let lo=0,hi=stamps.length;
    while(lo<hi){const mid=(lo+hi)>>1;if(stamps[mid]<=target)lo=mid+1;else hi=mid;}
    index=Math.max(0,lo-1);
  }
  function stop() {cancelAnimationFrame(frame);frame=0;previous=null;root.dataset.playing='false';}
  function tick(time) {
    frame=0;
    if (!loaded||!inView||document.hidden||reduced.matches) {stop();return;}
    if(previous!==null) elapsed=(elapsed+Math.min(time-previous,100))%LOOP_MS;
    previous=time;
    if(time-lastPaint>=1000/30){chooseRecord();draw();lastPaint=time;}
    frame=requestAnimationFrame(tick);
  }
  function sync() {
    stop();if(!loaded)return;
    if(reduced.matches){index=Math.floor(data.points.length/2);root.dataset.motion='reduced';draw();return;}
    root.dataset.motion='animated';chooseRecord();draw();
    if(inView&&!document.hidden){root.dataset.playing='true';frame=requestAnimationFrame(tick);}
  }
  async function initialize() {
    try {
      if(!window.d3)throw Error('Projection library unavailable');
      [data,land]=await Promise.all(['data/voyage-track.json','data/globe-land.json'].map(async url=>{
        const response=await fetch(url);if(!response.ok)throw Error('Route unavailable');return response.json();
      }));
      ctx=canvas.getContext('2d');if(!ctx)throw Error('Canvas unavailable');
      coordinates=data.points.map(p=>[p[1],p[2]]);
      stamps=data.points.map(p=>Date.parse(p[0]+'Z'));segments=new Set(data.break_before);
      fullTrack=track(coordinates.length-1);
      projection=d3.geoOrthographic().clipAngle(90).precision(.3).rotate([25,53,0]);
      path=d3.geoPath(projection,ctx);grid=d3.geoGraticule().step([30,15])();
      loaded=true;root.dataset.ready='true';
      new ResizeObserver(draw).observe(canvas);sync();
    } catch(error) {
      root.dataset.ready='error';readout.textContent='The original navigation table and source link below remain available.';
      console.warn(error.message);
    }
  }
  new IntersectionObserver(entries=>{inView=entries[0].isIntersecting;sync();},{threshold:.05}).observe(canvas);
  document.addEventListener('visibilitychange',sync);reduced.addEventListener('change',sync);
  const loader=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){loader.disconnect();initialize();}},{rootMargin:'500px'});
  loader.observe(root);
})();
