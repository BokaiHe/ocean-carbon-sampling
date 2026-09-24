/* SOCAT observation context. No OSSE fields, fitted values or invented routes. */
function aggregateObservedCells(rows, month) {
  const cells = new Map();
  for (const [m, lon, lat, value, count] of rows) {
    if (month && m !== month) continue;
    const key = `${lon}|${lat}`;
    if (!cells.has(key)) cells.set(key, {lon, lat, sum:0, months:0, count:0});
    const cell = cells.get(key);
    cell.sum += value; cell.months++; cell.count += count;
  }
  return [...cells.values()].map(cell => ({...cell, value:cell.sum / cell.months}));
}
(() => {
  'use strict';
  const root = document.querySelector('#observation-explorer');
  if (!root) return;
  const canvas = document.querySelector('#observation-globe');
  const yearSelect = document.querySelector('#observation-year');
  const monthSelect = document.querySelector('#observation-month');
  const pointSelect = document.querySelector('#observation-point');
  const status = document.querySelector('#observation-status');
  const readout = document.querySelector('#observation-readout');
  const months = ['All available months','January','February','March','April','May','June','July','August','September','October','November','December'];
  async function initialize() {
    try {
      if (!window.d3) throw new Error('Projection library unavailable');
      const [data, land] = await Promise.all(['data/observed-co2.json','data/globe-land.json'].map(async url => {
        const response = await fetch(url); if (!response.ok) throw new Error(`Unable to load ${url}`);
        return response.json();
      }));
      const d3 = window.d3, ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('Canvas unavailable');
      const projection = d3.geoOrthographic().clipAngle(90).precision(.3), path = d3.geoPath(projection,ctx);
      const grid = d3.geoGraticule().step([30,15])();
      const colour = value => d3.interpolateViridis(Math.max(0,Math.min(1,(value-200)/400)));
      document.querySelector('#observation-scale').style.background = `linear-gradient(90deg,${Array.from({length:11},(_,i)=>colour(200+i*40)).join(',')})`;
      let year = data.metadata.default_year, month = 0, rotation = [35,-15,0], zoom = 1;
      let cells = [], visible = [], selected = null, frame = 0, pointer = null;
      const radians = Math.PI/180;
      function rebuild() {
        cells = aggregateObservedCells(data.years[String(year)],month).map(cell => ({...cell,
          xyz:[Math.cos(cell.lat*radians)*Math.cos(cell.lon*radians),Math.cos(cell.lat*radians)*Math.sin(cell.lon*radians),Math.sin(cell.lat*radians)],
          colour:colour(cell.value)}));
        selected = null;
        pointSelect.replaceChildren(new Option('Select an observed grid cell…',''));
        const fragment = document.createDocumentFragment();
        cells.forEach((cell,i)=>fragment.append(new Option(`${cell.lat}°, ${cell.lon}° · ${cell.value.toFixed(1)} µatm`,String(i))));
        pointSelect.append(fragment);
        const count = cells.reduce((sum,cell)=>sum+cell.count,0);
        status.textContent = `${year} · ${months[month]} · ${cells.length.toLocaleString('en-US')} observed grid cells · ${count.toLocaleString('en-US')} underlying measurements. ${month?'Monthly grid means.':'Mean of available months only; not a complete annual mean.'}`;
        readout.textContent = 'Tap a dot to see its value, position and observation count.';
        root.dataset.year=String(year);root.dataset.month=String(month);root.dataset.cells=String(cells.length);
        requestDraw();
      }
      function draw() {
        frame=0;
        const width=Math.min(660,canvas.getBoundingClientRect().width);if(!width)return;
        const ratio=Math.min(window.devicePixelRatio||1,2), pixels=Math.round(width*ratio);
        if(canvas.width!==pixels){canvas.width=pixels;canvas.height=pixels;}
        ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,width,width);
        projection.translate([width/2,width/2]).scale(width*.45*zoom).rotate(rotation);
        ctx.beginPath();path({type:'Sphere'});ctx.fillStyle='#234c5c';ctx.fill();
        ctx.beginPath();path(grid);ctx.strokeStyle='#afc7d026';ctx.lineWidth=.6;ctx.stroke();
        const lon=-rotation[0]*radians,lat=-rotation[1]*radians;
        const centre=[Math.cos(lat)*Math.cos(lon),Math.cos(lat)*Math.sin(lon),Math.sin(lat)];
        visible=[];
        for(let i=0;i<cells.length;i++){
          const cell=cells[i];if(cell.xyz.reduce((sum,v,j)=>sum+v*centre[j],0)<=0)continue;
          const [x,y]=projection([cell.lon,cell.lat]);if(x<0||x>width||y<0||y>width)continue;
          const radius=Math.max(1.35,width/290)*Math.sqrt(zoom);
          ctx.beginPath();ctx.arc(x,y,radius,0,Math.PI*2);ctx.fillStyle=cell.colour;ctx.fill();
          visible.push({i,x,y});
        }
        if(selected!==null){const hit=visible.find(p=>p.i===selected);if(hit){ctx.beginPath();ctx.arc(hit.x,hit.y,7,0,Math.PI*2);ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();}}
        // Cartographic overlay, not a data exclusion rule. Keep white land on top.
        ctx.beginPath();path(land);ctx.fillStyle='#ffffff';ctx.fill();ctx.strokeStyle='#000000';ctx.lineWidth=1.2;ctx.stroke();
        canvas.dataset.rotation=rotation.join(',');canvas.dataset.zoom=String(zoom);canvas.dataset.visiblePoints=String(visible.length);
      }
      function requestDraw(){if(!frame)frame=requestAnimationFrame(draw);}
      function inspect(index,centre=false){
        selected=index;pointSelect.value=String(index);const cell=cells[index];
        const covered=d3.geoContains(land,[cell.lon,cell.lat]);
        readout.textContent=`${cell.value.toFixed(2)} µatm · ${cell.lat}°, ${cell.lon}° · ${cell.count.toLocaleString('en-US')} observations · ${cell.months}/12 months represented. ${month?'SOCAT monthly per-cruise-weighted mean.':'Equal-weight mean of available monthly values.'}${covered?' Covered by the land overlay; retained in source data.':''}`;
        if(centre)rotation=[-cell.lon,-cell.lat,0];requestDraw();
      }
      function inspectPixel(x,y){
        const location=projection.invert([x,y]);
        if(!location||Math.hypot(x-projection.translate()[0],y-projection.translate()[1])>projection.scale())return;
        if(d3.geoContains(land,location)){readout.textContent='Land overlay. Covered coastal grid centres remain available in the grid-cell selector and download.';return;}
        let nearest=null,distance=12;
        for(const point of visible){const d=Math.hypot(point.x-x,point.y-y);if(d<distance&&!d3.geoContains(land,[cells[point.i].lon,cells[point.i].lat])){nearest=point;distance=d;}}
        if(nearest)inspect(nearest.i);else readout.textContent='No displayed observed grid cell at this position and date. Empty water does not mean zero CO₂.';
      }
      function turn(dx,dy=0){rotation[0]+=dx;rotation[1]=Math.max(-85,Math.min(85,rotation[1]+dy));requestDraw();}
      function changeZoom(step){zoom=Math.max(.8,Math.min(2.2,Math.round((zoom+step)*10)/10));requestDraw();}
      function reset(){rotation=[35,-15,0];zoom=1;requestDraw();}
      yearSelect.replaceChildren(...data.metadata.years.map(y=>new Option(String(y),String(y))));yearSelect.value=String(year);
      monthSelect.replaceChildren(...months.map((name,i)=>new Option(name,String(i))));
      yearSelect.onchange=()=>{year=Number(yearSelect.value);rebuild();};monthSelect.onchange=()=>{month=Number(monthSelect.value);rebuild();};
      pointSelect.onchange=()=>{if(pointSelect.value!=='')inspect(Number(pointSelect.value),true);};
      document.querySelector('#observation-left').onclick=()=>turn(-20);document.querySelector('#observation-right').onclick=()=>turn(20);
      document.querySelector('#observation-in').onclick=()=>changeZoom(.2);document.querySelector('#observation-out').onclick=()=>changeZoom(-.2);
      document.querySelector('#observation-reset').onclick=reset;
      root.querySelectorAll('[data-observed-ocean]').forEach(button=>button.onclick=()=>{rotation={atlantic:[35,-15,0],pacific:[150,-5,0],indian:[-80,10,0],southern:[0,65,0]}[button.dataset.observedOcean].slice();requestDraw();});
      canvas.addEventListener('keydown',event=>{const keys={ArrowLeft:()=>turn(-10),ArrowRight:()=>turn(10),ArrowUp:()=>turn(0,-10),ArrowDown:()=>turn(0,10),'+':()=>changeZoom(.2),'=':()=>changeZoom(.2),'-':()=>changeZoom(-.2),Home:reset};if(keys[event.key]){event.preventDefault();keys[event.key]();}});
      canvas.addEventListener('pointerdown',event=>{if(pointer||event.button!==0)return;pointer={id:event.pointerId,x:event.clientX,y:event.clientY,startX:event.clientX,startY:event.clientY,moved:false};canvas.setPointerCapture(event.pointerId);});
      canvas.addEventListener('pointermove',event=>{if(!pointer||pointer.id!==event.pointerId)return;pointer.moved ||= Math.hypot(event.clientX-pointer.startX,event.clientY-pointer.startY)>4;turn((event.clientX-pointer.x)*.3/zoom,-(event.clientY-pointer.y)*.3/zoom);pointer.x=event.clientX;pointer.y=event.clientY;});
      canvas.addEventListener('pointerup',event=>{if(!pointer||pointer.id!==event.pointerId)return;const moved=pointer.moved;pointer=null;if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);if(!moved){const box=canvas.getBoundingClientRect();inspectPixel(event.clientX-box.left,event.clientY-box.top);}});
      canvas.addEventListener('pointercancel',()=>pointer=null);
      new ResizeObserver(requestDraw).observe(canvas);
      root.querySelectorAll('button,select').forEach(control=>control.disabled=false);pointSelect.disabled=false;
      rebuild();root.dataset.ready='true';
    }catch(error){status.textContent='Observed CO₂ could not load. The source links and JSON download below remain available.';root.dataset.ready='error';root.querySelectorAll('button,select').forEach(control=>control.disabled=true);pointSelect.disabled=true;console.warn(error.message);}
  }
  const loader=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting)){loader.disconnect();initialize();}},{rootMargin:'500px'});loader.observe(root);
})();
