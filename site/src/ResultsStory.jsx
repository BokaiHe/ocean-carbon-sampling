import React, {useEffect, useRef, useState} from 'react';

// Original implementation informed by the Showcase 7 editorial pattern.
// Scientific panels remain static HTML; React owns only their navigation.
const chapters = [
  {id:'paired-evidence', label:'The cost of past density', hint:'Compare two plans on the same test.'},
  {id:'results', label:'Does the result hold?', hint:'Change the weighting and evaluation domain.'},
  {id:'error-map', label:'Where do errors differ?', hint:'A supporting map, not the primary scope.'},
  {id:'sample-count', label:'The limits of coverage', hint:'Typical and extreme errors need not improve together.'},
];
const hashIndex = () => {
  const id=window.location.hash.slice(1);
  return id==='validation'||id==='evidence-story'?0:chapters.findIndex(c=>c.id===id);
};

export default function ResultsStory(){
  const [active,setActive]=useState(()=>Math.max(0,hashIndex()));
  const buttons=useRef([]);
  const scrollRequested=useRef(false);
  useEffect(()=>{
    const sync=()=>{const index=hashIndex();if(index>=0){scrollRequested.current=true;setActive(index);}};
    window.addEventListener('hashchange',sync);
    window.addEventListener('popstate',sync);
    return ()=>{window.removeEventListener('hashchange',sync);window.removeEventListener('popstate',sync);};
  },[]);
  useEffect(()=>{
    const root=document.getElementById('evidence-story');
    root.dataset.enhanced='true';
    chapters.forEach((chapter,index)=>{
      const panel=document.getElementById(chapter.id);
      panel.hidden=index!==active;
      panel.setAttribute('role','tabpanel');
      panel.setAttribute('aria-labelledby',`finding-tab-${index}`);
      panel.tabIndex=0;
    });
    const frame=requestAnimationFrame(()=>{
      window.dispatchEvent(new Event('research:panelchange'));
      if(scrollRequested.current){document.getElementById(chapters[active].id).scrollIntoView({behavior:'instant',block:'start'});scrollRequested.current=false;}
    });
    return ()=>cancelAnimationFrame(frame);
  },[active]);
  useEffect(()=>()=>{
    document.getElementById('evidence-story')?.removeAttribute('data-enhanced');
    chapters.forEach(chapter=>{
      const panel=document.getElementById(chapter.id);
      panel.hidden=false;panel.removeAttribute('role');panel.removeAttribute('aria-labelledby');panel.removeAttribute('tabindex');
    });
  },[]);
  function choose(index,focus=false){
    scrollRequested.current=true;
    if(index===active){document.getElementById(chapters[index].id).scrollIntoView({behavior:'instant',block:'start'});scrollRequested.current=false;}
    setActive(index);
    history.replaceState(null,'',`#${chapters[index].id}`);
    if(focus)buttons.current[index]?.focus({preventScroll:true});
  }
  function keyboard(event,index){
    const destinations={ArrowDown:(index+1)%4,ArrowUp:(index+3)%4,ArrowRight:(index+1)%4,ArrowLeft:(index+3)%4,Home:0,End:3};
    if(event.key in destinations){event.preventDefault();choose(destinations[event.key],true);}
  }
  return <>
    <p className="story-nav-label">Four questions. Follow the evidence.</p>
    <div className="finding-tabs" role="tablist" aria-label="Research findings" aria-orientation="vertical">
      {chapters.map((chapter,index)=><button key={chapter.id} ref={node=>buttons.current[index]=node} id={`finding-tab-${index}`} role="tab" aria-selected={active===index} aria-controls={chapter.id} tabIndex={active===index?0:-1} onClick={()=>choose(index)} onKeyDown={event=>keyboard(event,index)}>
        <span className="finding-number">0{index+1}</span>
        <span className="finding-label">{chapter.label}<span className="finding-hint">{chapter.hint}</span></span>
        <svg className="finding-arrow ui-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M7 7h10v10"/></svg>
      </button>)}
    </div>
    <div className="story-nav-footer"><span>0{active+1} / 04</span><a href="#technical">Methods &amp; limitations</a></div>
  </>;
}
