/* Frozen-data globe. No routes, interpolated fields, predictions or new fits. */
(() => {
  const root=document.querySelector('#globe-explorer');
  const canvas=document.querySelector('#ocean-globe');
  const scope=document.querySelector('#globe-scope');
  const readout=document.querySelector('#globe-readout');
  const pointSelect=document.querySelector('#globe-point');
  const names={random:'Random',historical:'Historical-density',coverage:'Coverage'};
  const model={strategy:'random',rotation:[35,-20,0],zoom:1,spin:false};
  let data,land,ctx,projection,path,width=500,visible=[],selected=null,frame=0;
  let animation=0,last=0,inView=false,pointer=null;
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const coord=(v,pos,neg)=>`${Math.abs(v).toFixed(1)}°${v>=0?pos:neg}`;
  const degree=Math.PI/180;
  const enrich=row=>({row,xyz:[Math.cos(row[1]*degree)*Math.cos(row[0]*degree),Math.cos(row[1]*degree)*Math.sin(row[0]*degree),Math.sin(row[1]*degree)]});
  let samples={};
  const palettes={};
  const noDataColour='#9ca3af';
  const colourStops={sampling:['#63baf0','#276bb5','#163b79']};
  function requestDraw(){if(!frame)frame=requestAnimationFrame(()=>{frame=0;draw();});}
  function updateView(){
    model.rotation[0]=((model.rotation[0]+180)%360+360)%360-180;
    model.rotation[1]=clamp(model.rotation[1],-85,85);
    canvas.dataset.rotation=model.rotation.join(',');canvas.dataset.zoom=model.zoom;
    requestDraw();
  }
  function stopSpin(){model.spin=false;document.querySelector('#globe-spin').setAttribute('aria-pressed','false');document.querySelector('#globe-spin').textContent='Rotate';cancelAnimationFrame(animation);animation=0;last=0;}
  function tick(time){
    animation=0;if(!model.spin||!inView||document.hidden)return;
    if(last)model.rotation[0]+=Math.min(time-last,100)*.004;
    last=time;updateView();animation=requestAnimationFrame(tick);
  }
  function animate(){if(model.spin&&inView&&!document.hidden&&!animation){last=0;animation=requestAnimationFrame(tick);}}
  function draw(){
    if(!data||!ctx)return;
    const height=width,ratio=Math.min(devicePixelRatio||1,2);
    ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,width,height);
    const radius=width*.435*model.zoom;
    projection.rotate(model.rotation).translate([width/2,height/2]).scale(radius);
    // Neutral ocean is a display backdrop, not an interpolated coverage mask.
    ctx.save();ctx.shadowColor='#b8d8f066';ctx.shadowBlur=14;
    ctx.beginPath();path({type:'Sphere'});ctx.fillStyle=noDataColour;ctx.fill();ctx.strokeStyle='#d3e4ef';ctx.lineWidth=1;ctx.stroke();ctx.restore();
    ctx.save();ctx.beginPath();path({type:'Sphere'});ctx.clip();
    ctx.beginPath();path(d3.geoGraticule10());ctx.strokeStyle='#ffffff18';ctx.lineWidth=.65;ctx.stroke();
    const center=projection.invert([width/2,height/2]);
    const front=[Math.cos(center[1]*degree)*Math.cos(center[0]*degree),Math.cos(center[1]*degree)*Math.sin(center[0]*degree),Math.sin(center[1]*degree)];
    visible=[];
    const rows=samples[model.strategy];
    for(const item of rows){
      const dot=item.xyz[0]*front[0]+item.xyz[1]*front[1]+item.xyz[2]*front[2];if(dot<=.015)continue;
      const [x,y]=projection(item.row);if(x<0||y<0||x>width||y>height)continue;
      const count=item.row[2],colour=count===0?noDataColour:palettes.sampling[Math.round(clamp(count/20,0,1)*63)],size=1.4+Math.sqrt(count)*.5;
      ctx.fillStyle=colour;ctx.beginPath();ctx.arc(x,y,size,0,Math.PI*2);ctx.fill();
      visible.push({x,y,item});
    }
    const latitudeLine={type:'LineString',coordinates:d3.range(-180,181,3).map(lon=>[lon,60])};
    ctx.beginPath();path(latitudeLine);ctx.setLineDash([3,4]);ctx.strokeStyle='#203b5277';ctx.lineWidth=1;ctx.stroke();ctx.setLineDash([]);
    if(selected){const hit=visible.find(p=>p.item===selected);if(hit){ctx.beginPath();ctx.arc(hit.x,hit.y,8,0,Math.PI*2);ctx.strokeStyle='white';ctx.lineWidth=2;ctx.stroke();}}
    // Cartographic overlay only: source data and experimental metrics are unchanged.
    // Draw last so neither data symbols nor selection rings paint over land.
    ctx.beginPath();path(land);ctx.fillStyle='#ffffff';ctx.fill();ctx.strokeStyle='#000000';ctx.lineWidth=1.35;ctx.lineJoin='round';ctx.stroke();
    ctx.restore();root.dataset.ready='true';canvas.dataset.visiblePoints=visible.length;
  }
  function inspect(item,move=false){
    selected=item;if(!item)return;
    const row=item.row,where=`${coord(row[1],'N','S')}, ${coord(row[0],'E','W')}`;
    readout.textContent=`${where} · ${names[model.strategy]}: ${row[2]} observations in this 5° × 10° block (all months).`;
    if(d3.geoContains(land,row))readout.textContent+=' Covered by the land overlay; retained in source data. This is not a corrected ocean mask.';
    if(move){model.rotation=[-row[0],-row[1],0];stopSpin();}
    updateView();
  }
  function inspectPixel(x,y){
    const location=projection.invert([x,y]);
    if(!location||!location.every(Number.isFinite)||Math.hypot(x-width/2,y-width/2)>projection.scale()){selected=null;readout.textContent='Outside the globe. Tap a visible ocean point.';requestDraw();return;}
    if(d3.geoContains(land,location)){selected=null;readout.textContent='Land overlay. Underlying values remain in the download and coordinate inspector; the ocean-domain audit is unresolved.';requestDraw();return;}
    let nearest=null,best=196;
    for(const p of visible){const ds=(p.x-x)**2+(p.y-y)**2;if(ds<best&&!d3.geoContains(land,p.item.row)){best=ds;nearest=p.item;}}
    if(nearest)inspect(nearest);else{selected=null;readout.textContent='No displayed point here. Try a coloured point or zoom in.';requestDraw();}
  }
  function controls(){
    selected=null;readout.textContent='Tap a point to inspect its value.';
    document.querySelectorAll('[data-globe-strategy]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.globeStrategy===model.strategy)));
    root.dataset.layer='sampling';root.dataset.strategy=model.strategy;
    document.querySelector('#globe-role').textContent='DESIGN MAP · NOT MODEL ERROR';
    scope.textContent='2005 · seed 0 · 5,000 observations. Points are 5° × 10° block centres, not vessels. Colour saturates at 20; inspected counts are exact. Grey background is not a fine-grid coverage mask.';
    const title='Selected observations per block',gradient=colourStops.sampling.join(','),ticks=['0','10','20+'];
    const legend=document.querySelector('#globe-legend');
    legend.replaceChildren();const text=document.createElement('div');text.textContent=title;
    const bar=document.createElement('div');bar.className='globe-colour-scale';bar.style.background=`linear-gradient(90deg,${gradient})`;
    const scale=document.createElement('div');scale.className='globe-ticks';ticks.forEach(t=>{const span=document.createElement('span');span.textContent=t;scale.append(span);});legend.append(text,bar,scale);
    const direction=document.createElement('p');direction.textContent='Light blue: fewer samples · Deep blue: more samples';legend.append(direction);
    const key=document.createElement('div');key.className='globe-surface-key';key.innerHTML='<span><i class="land-key"></i>Land</span><span><i class="missing-key"></i>No displayed value</span>';legend.append(key);
    pointSelect.replaceChildren(new Option('Select a sampling block…',''));
    // A native selector provides the same exact values without pointer interaction.
    const rows=samples[model.strategy];
    const fragment=document.createDocumentFragment();rows.forEach((p,i)=>fragment.append(new Option(`${coord(p.row[1],'N','S')} / ${coord(p.row[0],'E','W')}`,String(i))));pointSelect.append(fragment);
    requestDraw();
  }
  async function initializeGlobe(){
    try{
      if(!window.d3)throw Error('Globe library unavailable');
      ctx=canvas.getContext('2d');if(!ctx)throw Error('Canvas unavailable');
      const responses=await Promise.all(['data/globe-data.json','data/globe-land.json'].map(p=>fetch(p)));
      if(responses.some(r=>!r.ok))throw Error('Globe data unavailable');
      [data,land]=await Promise.all(responses.map(r=>r.json()));
      Object.entries(data.sampling).forEach(([k,rows])=>samples[k]=rows.map(enrich));
      for(const layer of Object.keys(colourStops)){
        const [low,mid,high]=colourStops[layer];
        palettes[layer]=d3.range(64).map(i=>i<32?d3.interpolateRgb(low,mid)(i/31):d3.interpolateRgb(mid,high)((i-32)/31));
      }
      projection=d3.geoOrthographic().clipAngle(90);path=d3.geoPath(projection,ctx);
      new ResizeObserver(()=>{width=canvas.clientWidth;const ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(width*ratio);requestDraw();}).observe(canvas);
      document.querySelectorAll('[data-globe-strategy]').forEach(button=>button.addEventListener('click',()=>{model.strategy=button.dataset.globeStrategy;controls();}));
      const rotate=(lon,lat=0)=>{stopSpin();model.rotation[0]+=lon;model.rotation[1]+=lat;updateView();};
      const zoom=delta=>{model.zoom=clamp(model.zoom+delta,.8,2.2);updateView();};
      const reset=()=>{stopSpin();model.rotation=[35,-20,0];model.zoom=1;updateView();};
      document.querySelector('#globe-left').onclick=()=>rotate(-20);
      document.querySelector('#globe-right').onclick=()=>rotate(20);
      document.querySelector('#globe-in').onclick=()=>zoom(.2);
      document.querySelector('#globe-out').onclick=()=>zoom(-.2);
      document.querySelector('#globe-reset').onclick=reset;
      document.querySelector('#globe-spin').onclick=()=>{if(model.spin)stopSpin();else{model.spin=true;document.querySelector('#globe-spin').setAttribute('aria-pressed','true');document.querySelector('#globe-spin').textContent='Pause';animate();}};
      canvas.addEventListener('keydown',e=>{const keys={ArrowLeft:()=>rotate(-10),ArrowRight:()=>rotate(10),ArrowUp:()=>rotate(0,-10),ArrowDown:()=>rotate(0,10),'+':()=>zoom(.2),'=':()=>zoom(.2),'-':()=>zoom(-.2),Home:reset};if(keys[e.key]){e.preventDefault();keys[e.key]();}});
      canvas.addEventListener('pointerdown',e=>{if(pointer||e.button!==0)return;stopSpin();pointer={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,moved:false};canvas.setPointerCapture(e.pointerId);});
      canvas.addEventListener('pointermove',e=>{if(!pointer||pointer.id!==e.pointerId)return;const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;pointer.moved ||= Math.hypot(e.clientX-pointer.startX,e.clientY-pointer.startY)>4;model.rotation[0]+=dx*.3/model.zoom;model.rotation[1]-=dy*.3/model.zoom;pointer.x=e.clientX;pointer.y=e.clientY;updateView();});
      canvas.addEventListener('pointerup',e=>{if(!pointer||pointer.id!==e.pointerId)return;const moved=pointer.moved;pointer=null;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);if(!moved){const box=canvas.getBoundingClientRect();inspectPixel(e.clientX-box.left,e.clientY-box.top);}});
      canvas.addEventListener('pointercancel',()=>pointer=null);
      pointSelect.addEventListener('change',()=>{if(pointSelect.value==='')return;const rows=samples[model.strategy];inspect(rows[Number(pointSelect.value)],true);});
      document.querySelector('#globe-coordinate-form').addEventListener('submit',e=>{
        e.preventDefault();const latitude=Number(document.querySelector('#globe-latitude').value),longitude=Number(document.querySelector('#globe-longitude').value);
        const target=enrich([longitude,latitude]).xyz,rows=samples[model.strategy];
        let nearest=null,best=-Infinity;for(const item of rows){const dot=item.xyz.reduce((sum,v,i)=>sum+v*target[i],0);if(dot>best){best=dot;nearest=item;}}
        inspect(nearest,true);root.scrollIntoView({behavior:'instant',block:'start'});
      });
      document.querySelectorAll('[data-ocean]').forEach(b=>b.onclick=()=>{stopSpin();model.rotation={atlantic:[35,-20,0],pacific:[150,-5,0],indian:[-80,10,0],southern:[0,65,0]}[b.dataset.ocean].slice();updateView();});
      new IntersectionObserver(entries=>{inView=entries[0].isIntersecting;if(inView)animate();else{cancelAnimationFrame(animation);animation=0;last=0;}},{threshold:.05}).observe(canvas);
      document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(animation);animation=0;last=0;}else animate();});
      reduced.addEventListener('change',()=>{if(reduced.matches)stopSpin();});
      controls();updateView();
    }catch(error){scope.textContent='The interactive globe could not load. The supporting error map and result charts below are still available.';root.dataset.ready='error';root.querySelectorAll('button,select').forEach(el=>el.disabled=true);console.warn(error.message);}
  }
  // Load geography and point data only as the reader approaches the globe.
  const loader=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){loader.disconnect();initializeGlobe();}},{rootMargin:'600px'});loader.observe(root);
  const chapters=document.querySelectorAll('.chapter-nav a[href^="#"]');
  const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){chapters.forEach(a=>{if(a.hash==='#'+entry.target.id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});}},{rootMargin:'-5% 0px -65% 0px'});
  chapters.forEach(a=>{const section=document.querySelector(a.hash);if(section)observer.observe(section);});
})();
