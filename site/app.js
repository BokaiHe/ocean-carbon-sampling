"use strict";
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const NS = "http://www.w3.org/2000/svg";
const colors = {random:"#456d87",historical:"#a35f4d",hidden:"#456d87",block:"#a35f4d",median:"#a35f4d",p99:"#456d87",rmse:"#687477"};
const state = {data:null, charts:null, strategy:"random", showZero:false, pairedProtocol:"hidden"};
const names = {random:"Random", historical:"Historical-density", coverage:"Coverage"};
const signed = (n,d=3) => (n>0?"+":n<0?"−":"") + Math.abs(n).toFixed(d);
const escapeHTML = text => String(text).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function svgEl(tag, attrs={}, parent) {
  const element=document.createElementNS(NS,tag);
  for(const [k,v] of Object.entries(attrs)) element.setAttribute(k,String(v));
  if(parent) parent.append(element);
  return element;
}
function label(svg,x,y,value,attrs={}) {
  const el=svgEl("text",{x,y,fill:"#465b68","font-size":14,...attrs},svg);
  el.textContent=value;return el;
}
function line(svg,x1,y1,x2,y2,attrs={}) {
  return svgEl("line",{x1,y1,x2,y2,stroke:"#dbe3e7","stroke-width":1,...attrs},svg);
}
function makeChart(id,height,title,description) {
  const host=$("#"+id), width=Math.max(240,Math.floor(host.clientWidth));
  const svg=svgEl("svg",{viewBox:`0 0 ${width} ${height}`,width,height,role:"img","aria-labelledby":id+"-title "+id+"-desc"});
  const t=svgEl("title",{id:id+"-title"},svg);t.textContent=title;
  const d=svgEl("desc",{id:id+"-desc"},svg);d.textContent=description;
  const output=document.createElement("p");output.className="chart-readout";output.setAttribute("aria-live","polite");
  host.replaceChildren(svg,output);return {svg,width,output};
}
function mark(chart,description,draw) {
  const g=svgEl("g",{tabindex:0,role:"img","aria-label":description,class:"chart-mark"},chart.svg);
  const title=svgEl("title",{},g);title.textContent=description;draw(g);
  for(const event of ["mouseenter","focus","click"]) g.addEventListener(event,()=>{chart.output.textContent=description;});
  return g;
}
function table(id,headers,rows) {
  $("#"+id).innerHTML="<table><thead><tr>"+headers.map(v=>"<th scope='col'>"+escapeHTML(v)+"</th>").join("")+"</tr></thead><tbody>"+rows.map(row=>"<tr>"+row.map(v=>"<td>"+escapeHTML(v)+"</td>").join("")+"</tr>").join("")+"</tbody></table>";
}
function pairedChart() {
  const key=state.pairedProtocol, primary=key==="hidden", height=primary?285:600;
  const chart=makeChart("paired-chart",height,primary?"Three primary-year comparisons":"15 whole-block stress-test units","Each row compares random and historical-density mean absolute error on the same evaluation set. Lines pair strategies, not confidence intervals.");
  const {svg,width}=chart,L=primary?53:77,R=22;
  const pairs=Object.values(state.charts.pairs).flat();
  const values=pairs.flatMap(r=>[r.random,r.historical]);
  const min=Math.floor(Math.min(...values)/2)*2, max=Math.ceil(Math.max(...values)/2)*2;
  const x=n=>L+(n-min)/(max-min)*(width-L-R), bottom=height-55;
  for(let tick=min;tick<=max;tick+=2){line(svg,x(tick),15,x(tick),bottom,{stroke:"#e8eef2"});label(svg,x(tick),bottom+22,tick,{"text-anchor":"middle"});}
  label(svg,L+(width-L-R)/2,height-6,"MAE · µatm · lower is better",{"text-anchor":"middle","font-size":width<400?12:14});
  let y=primary?55:27;const rows=[];
  const title=primary?"Hidden cells · primary":"Whole blocks · stress test";
    for(const row of state.charts.pairs[key]){
      const unit=String(row.year)+(key==="block"?" · F"+row.fold:"");
      label(svg,L-10,y+4,unit,{"text-anchor":"end","font-size":primary?14:12});
      const desc=`${title}, ${unit}: random ${row.random.toFixed(3)}, historical-density ${row.historical.toFixed(3)} µatm; difference ${signed(row.historical-row.random)}.`;
      mark(chart,desc,g=>{
        line(g,x(row.random),y,x(row.historical),y,{stroke:"#b5c7d4","stroke-width":primary?4:2.5});
        const r=primary?7:5;
        svgEl("circle",{cx:x(row.random),cy:y,r,fill:colors.random},g);
        svgEl("rect",{x:x(row.historical)-r,y:y-r,width:r*2,height:r*2,rx:2,fill:colors.historical},g);
        if(primary){label(g,x(row.random),y-16,row.random.toFixed(2),{"text-anchor":"middle",fill:colors.random,"font-size":14});label(g,x(row.historical),y+29,row.historical.toFixed(2),{"text-anchor":"middle",fill:colors.historical,"font-size":14});}
        svgEl("rect",{x:L,y:y-15,width:width-L-R,height:30,fill:"transparent"},g);
      });
      rows.push([key==="hidden"?"Primary":"Stress test",unit,row.random.toFixed(3),row.historical.toFixed(3),signed(row.historical-row.random)]);
      y+=primary?70:34;
    }
  $$("[data-paired-protocol]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.pairedProtocol===key)));
  $("#primary-effect").innerHTML="+"+state.data.estimands["area|both60|hidden"].metrics.mae.relative_pct.toFixed(2)+"%<span>higher average error than random · primary test</span>";
  table("paired-table",["Protocol","Unit","Random MAE","Historical-density MAE","ΔMAE (µatm)"],rows);
}
function blockChart() {
  const chart=makeChart("block-chart",236,"Occupied spatial blocks in the illustrative selection","Count of distinct 5 by 10 degree spatial blocks receiving at least one selected observation.");
  const {svg,width}=chart,L=0,R=45,scale=n=>n/1100*(width-L-R);
  const rows=[];
  state.charts.sampling.blocks.forEach((row,i)=>{
    const y=27+i*70, active=state.strategy===row.strategy;
    label(svg,0,y-9,names[row.strategy],{fill:"#243b49","font-weight":active?700:400});
    mark(chart,`${names[row.strategy]}: ${row.blocks} occupied blocks from ${row.sample_count.toLocaleString("en-US")} selected month-cells.`,g=>{
      svgEl("rect",{x:0,y,width:width-R,height:16,rx:2,fill:"#edf2f5"},g);
      svgEl("rect",{x:0,y,width:scale(row.blocks),height:16,rx:2,fill:row.strategy==="historical"?colors.historical:colors.random,opacity:active?1:0.6},g);
    });
    label(svg,width-R+8,y+13,row.blocks,{fill:"#243b49","font-weight":700});
    rows.push([names[row.strategy],row.blocks,row.sample_count]);
  });
  table("block-table",["Rule","Occupied spatial blocks","Selected month-cells"],rows);
}
function robustnessChart() {
  const chart=makeChart("robustness-chart",450,"Historical-density MAE change across 12 evaluation variants","All displayed relative MAE changes are positive; these variants share data and are not independent tests.");
  const {svg,width}=chart,L=width<500?141:205,R=26;
  const x=n=>L+n/60*(width-L-R), rows=[];
  (width<300?[0,30,60]:[0,20,40,60]).forEach(t=>{line(svg,x(t),32,x(t),400,{stroke:t===0?"#617986":"#dbe3e7","stroke-dasharray":t===0?"4 4":"none"});label(svg,x(t),423,(t===0?"0":"+"+t)+"%",{"text-anchor":"middle"});});
  label(svg,width/2,447,"Relative MAE change",{"text-anchor":"middle"});
  let y=20;
  const domains={global:"Full",eval60:"Eval <60°N",both60:"Both <60°N"};
  for(const scheme of ["hidden","block"]){
    label(svg,2,y,scheme==="hidden"?"Hidden cells":"Whole blocks",{fill:"#243b49","font-weight":700});y+=27;
    for(const weight of ["equal","area"])for(const domain of ["global","eval60","both60"]){
      const key=`${weight}|${domain}|${scheme}`,record=state.data.estimands[key],m=record.metrics.mae;
      label(svg,L-10,y+4,(weight==="equal"?"Equal":"Area")+" · "+domains[domain],{"text-anchor":"end","font-size":width<500?12.5:14});
      const desc=`${scheme==="hidden"?"Hidden cells":"Whole blocks"}, ${weight} weighting, ${domains[domain]}: MAE ${signed(m.relative_pct,2)}%; random ${m.random.toFixed(3)}, historical-density ${m.comparator.toFixed(3)} µatm.`;
      mark(chart,desc,g=>{
        if(weight==="area"&&domain==="both60")svgEl("circle",{cx:x(m.relative_pct),cy:y,r:9,fill:"none",stroke:colors[scheme],"stroke-width":1.5},g);
        if(scheme==="hidden")svgEl("circle",{cx:x(m.relative_pct),cy:y,r:5,fill:colors[scheme]},g);
        else svgEl("rect",{x:x(m.relative_pct)-5,y:y-5,width:10,height:10,fill:colors[scheme]},g);
        svgEl("circle",{cx:x(m.relative_pct),cy:y,r:13,fill:"transparent"},g);
      });
      rows.push([scheme,weight,domains[domain],m.random.toFixed(3),m.comparator.toFixed(3),signed(m.relative_pct,2)+"%"]);y+=27;
    }
    y+=21;
  }
  table("robustness-table",["Protocol","Weights","Domain","Random MAE","Historical MAE","Change"],rows);
}
function sweepChart() {
  const narrow=$("#sweep-chart").clientWidth<760;
  const chart=makeChart("sweep-chart",narrow?960:330,"Coverage trade-offs across four sample counts","Separate panels show median, p99 and RMSE differences relative to random. Each vertical scale differs. Below zero means lower error; lines connect tested counts only.");
  const {svg,width}=chart,counts=[500,1000,2500,5000];
  const metrics=[["median_absolute_error","median","Median"],["p99_absolute_error","p99","p99"],["rmse","rmse","RMSE"]];
  const rows=[];
  metrics.forEach(([key,color,name],panel)=>{
    const panelWidth=narrow?width:(width-64)/3,offsetX=narrow?0:panel*(panelWidth+32),offsetY=narrow?panel*320:0;
    const L=offsetX+40,R=offsetX+panelWidth-17,top=offsetY+78,bottom=offsetY+263;
    const differences=counts.map(n=>state.data.sample_sweep[String(n)].metrics[key].difference);
    const low=Math.min(0,Math.floor(Math.min(...differences))),high=Math.max(1,Math.ceil(Math.max(...differences)));
    const x=n=>L+counts.indexOf(n)/3*(R-L),y=n=>top+(high-n)/(high-low)*(bottom-top);
    label(svg,offsetX+3,offsetY+24,name==="Median"?"Typical error":name==="p99"?"Extreme tail":"Large-error-sensitive",{fill:"#203d4d","font-size":18,"font-weight":600});
    label(svg,offsetX+3,offsetY+49,name+" · Δµatm",{fill:colors[color],"font-size":14});
    const ticks=[...new Set([low,0,high])];
    ticks.forEach(t=>{line(svg,L,y(t),R,y(t),{stroke:t===0?"#7593a8":"#e1eaf0","stroke-dasharray":t===0?"4 4":"none"});label(svg,L-9,y(t)+4,signed(t,0),{"text-anchor":"end","font-size":13});});
    counts.forEach((n,i)=>label(svg,x(n),offsetY+290,n===500?"500":n===1000?"1k":n===2500?"2.5k":"5k",{"text-anchor":i===3?"end":"middle","font-size":13}));
    const points=counts.map(n=>[x(n),y(state.data.sample_sweep[String(n)].metrics[key].difference)]);
    svgEl("polyline",{points:points.map(p=>p.join(",")).join(" "),fill:"none",stroke:colors[color],"stroke-width":2.5,"stroke-dasharray":key==="rmse"?"6 4":"none"},svg);
    counts.forEach((n,i)=>{
      const m=state.data.sample_sweep[String(n)].metrics[key],desc=`${n.toLocaleString("en-US")} samples, ${name}: coverage − random ${signed(m.difference)} µatm; random ${m.random.toFixed(3)}, coverage ${m.coverage.toFixed(3)}.`;
      mark(chart,desc,g=>{svgEl("circle",{cx:points[i][0],cy:points[i][1],r:5,fill:colors[color],stroke:"white","stroke-width":1},g);svgEl("circle",{cx:points[i][0],cy:points[i][1],r:12,fill:"transparent"},g);});
      rows.push([n,name,m.random.toFixed(3),m.coverage.toFixed(3),signed(m.difference)]);
    });
    label(svg,(L+R)/2,offsetY+316,"Sample count",{"text-anchor":"middle","font-size":12});
  });
  table("sweep-table",["Count","Metric","Random","Coverage","Δerror (µatm)"],rows);
}
function biasChart() {
  const chart=makeChart("bias-chart",285,"Whole-block signed-bias sensitivity","Four categorical changes to area weighting and domain shrink the original negative signed offset.");
  const {svg,width}=chart,L=44,R=20,top=32,bottom=198;
  const keys=state.data.estimand_journey,values=keys.map(k=>state.data.estimands[k].metrics.bias.difference);
  const x=i=>L+i/3*(width-L-R),y=n=>top+(0-n)/5.5*(bottom-top);
  [0,-2.5,-5].forEach(t=>{line(svg,L,y(t),width-R,y(t),{stroke:t===0?"#617986":"#dbe3e7"});label(svg,L-9,y(t)+5,signed(t,1),{"text-anchor":"end","font-size":13});});
  const captions=[["Equal","Full"],["Area","Full"],["Area","Eval <60°N"],["Area","Both <60°N"]],rows=[];
  values.forEach((v,i)=>{
    mark(chart,`${captions[i].join(" · ")}: historical-density − random signed bias ${signed(v)} µatm, whole-block stress test.`,g=>{svgEl("circle",{cx:x(i),cy:y(v),r:5,fill:colors.random},g);svgEl("circle",{cx:x(i),cy:y(v),r:13,fill:"transparent"},g);});
    const anchor=i===0?"start":i===3?"end":"middle";
    label(svg,x(i),y(v)+(v>-1?24:-12),signed(v),{"text-anchor":anchor,fill:"#243b49","font-size":13});
    label(svg,x(i),231,captions[i][0],{"text-anchor":anchor,"font-size":13});
    label(svg,x(i),251,width<400&&i>1?(i===2?"Eval":"Both"):captions[i][1],{"text-anchor":anchor,"font-size":13});
    if(width<400&&i>1)label(svg,x(i),270,"<60°N",{"text-anchor":anchor,"font-size":13});
    rows.push([captions[i].join(" · "),signed(v)]);
  });
  table("bias-table",["Whole-block setting","Bias difference (µatm)"],rows);
}
function updateMap() {
  const path=state.data.maps.images[state.strategy][state.showZero?"zero":"base"];
  $("#sampling-map").src=path;$("#sampling-map-link").href=path;
  $("#sampling-map").alt=names[state.strategy]+" illustrative sampling map"+(state.showZero?" with historical zero-support overlay":"");
  $("#zero-callout").hidden=!state.showZero;
  $("#map-description").textContent={
    random:"Random: equal selection probability for each candidate month-cell.",
    historical:"Historical-density: SOCAT count weights, not real cruise trajectories.",
    coverage:"Coverage: prioritize underrepresented month-space blocks."
  }[state.strategy];
  $$("[data-strategy]").forEach(b=>{const active=b.dataset.strategy===state.strategy;b.classList.toggle("active",active);b.setAttribute("aria-pressed",String(active));});
  blockChart();
}
function renderAudits() {
  const month=state.data.audits.month_balance;
  $("#month-audit").innerHTML="<p>Supporting whole-block selection audit; all strategies cover 12 months. Mean absolute deviation from equal monthly allocation:</p><ul>"+Object.entries(month).map(([k,v])=>"<li>"+escapeHTML(k.replaceAll("_","-"))+": "+v.mean_abs_equal_deviation_pp.toFixed(3)+" percentage points.</li>").join("")+"</ul>";
  const r=state.data.audits.regridding;
  $("#regrid-audit").innerHTML=`<p>Native-cell-area regridding preserved ${r.direction_checks_passed}/${r.direction_checks} prespecified directions. Correlated metrics are not independent tests. This checks regridding, not evaluation-area weighting.</p><a href="https://github.com/BokaiHe/ocean-carbon-sampling/blob/main/docs/osse_regrid_audit_results.md">Read the full regridding audit ↗</a>`;
}
function renderCharts() {pairedChart();blockChart();robustnessChart();sweepChart();biasChart();}
// The React hero owns mobile navigation (including Escape and focus handling).
async function initialize() {
  try{
    const responses=await Promise.all(["data/site-data.json","data/chart-data.json"].map(path=>fetch(path)));
    for(const r of responses)if(!r.ok)throw Error("Data request failed: "+r.status);
    [state.data,state.charts]=await Promise.all(responses.map(r=>r.json()));
    renderCharts();renderAudits();updateMap();
    $$("[data-paired-protocol]").forEach(b=>b.addEventListener("click",()=>{state.pairedProtocol=b.dataset.pairedProtocol;pairedChart();}));
    $$("[data-strategy]").forEach(b=>b.addEventListener("click",()=>{state.strategy=b.dataset.strategy;updateMap();}));
    $("#zero-toggle").addEventListener("change",e=>{state.showZero=e.target.checked;updateMap();});
    let frame;const widths=new WeakMap();
    const observer=new ResizeObserver(entries=>{
      if(entries.some(e=>{const w=Math.floor(e.contentRect.width),old=widths.get(e.target);widths.set(e.target,w);return old!==w;})){
        cancelAnimationFrame(frame);frame=requestAnimationFrame(renderCharts);
      }
    });
    $$(".chart").forEach(c=>observer.observe(c));
  }catch(error){
    const message=document.createElement("div");message.className="load-error";message.setAttribute("role","alert");
    message.textContent=location.protocol==="file:"?"Open this site over HTTP or use the published GitHub Pages link; local file access cannot load its JSON.":"The frozen chart data could not be loaded. Check your connection and refresh. "+error.message;
    document.body.prepend(message);console.error(error);
  }
}
// Keep image enlargement on this page, including in embedded browsers.
const imageViewer=document.createElement("dialog");
imageViewer.className="image-viewer";
imageViewer.setAttribute("aria-label","Enlarged map");
imageViewer.innerHTML='<div class="image-viewer-toolbar"><span>Enlarged map</span><button type="button" autofocus aria-label="Close enlarged map">Close ×</button></div><div class="image-viewer-body"><img alt="" /></div>';
document.body.append(imageViewer);
let imageOpener=null,imageScroll=0;
$("button",imageViewer).addEventListener("click",()=>imageViewer.close());
imageViewer.addEventListener("click",e=>{if(e.target===imageViewer||e.target.classList.contains("image-viewer-body"))imageViewer.close();});
imageViewer.addEventListener("close",()=>{
  document.documentElement.classList.remove("image-viewer-open");
  imageOpener?.focus({preventScroll:true});
  window.scrollTo({top:imageScroll,behavior:"instant"});
  $("img",imageViewer).removeAttribute("src");
});
document.addEventListener("click",e=>{
  const link=e.target.closest("a[href]");
  if(!link||e.defaultPrevented||e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||link.hasAttribute("download"))return;
  const url=new URL(link.href);
  if(url.origin!==location.origin||!url.pathname.endsWith(".png")||typeof imageViewer.showModal!=="function")return;
  e.preventDefault();
  imageOpener=link;imageScroll=window.scrollY;
  const source=$("img",link)||$("img",link.closest("figure")||link);
  $("img",imageViewer).alt=source?.alt||link.getAttribute("aria-label")||"Enlarged map";
  $("img",imageViewer).src=link.href;
  imageViewer.showModal();
  document.documentElement.classList.add("image-viewer-open");
});
initialize();
