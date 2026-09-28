import React,{Component,Suspense,lazy,useEffect,useRef,useState} from 'react';

// User-supplied licensed component, intentionally excluded from public source.
const MosaicWaves=lazy(()=>import('@licensed/mosaic-waves'));
class BackgroundBoundary extends Component {
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  render(){return this.state.failed?null:this.props.children;}
}

export default function MosaicBackdrop(){
  const root=useRef(null);
  const [visible,setVisible]=useState(false),[calm,setCalm]=useState(true);
  const [paused,setPaused]=useState(false),[hidden,setHidden]=useState(false);
  useEffect(()=>{
    const query=matchMedia('(prefers-reduced-motion: reduce)');
    const sync=()=>setCalm(query.matches||Boolean(navigator.connection?.saveData));
    const visibility=()=>setHidden(document.hidden);
    sync();visibility();query.addEventListener('change',sync);
    document.addEventListener('visibilitychange',visibility);
    const observer=new IntersectionObserver(([entry])=>setVisible(entry.isIntersecting),{rootMargin:'100px'});
    observer.observe(root.current);
    return()=>{observer.disconnect();query.removeEventListener('change',sync);document.removeEventListener('visibilitychange',visibility);};
  },[]);
  return <div className="mosaic-backdrop" ref={root} data-motion={calm?'reduced':paused?'paused':'running'}>
    <div className="mosaic-field" aria-hidden="true">
      {__HAS_LICENSED_MOSAIC__&&!calm&&visible&&!hidden&&<BackgroundBoundary><Suspense fallback={null}>
        <MosaicWaves paused={paused}/>
      </Suspense></BackgroundBoundary>}
    </div>
    {__HAS_LICENSED_MOSAIC__&&!calm&&<button type="button" className="mosaic-pause" onClick={()=>setPaused(p=>!p)} aria-pressed={paused}>{paused?'Play waves':'Pause waves'} <span aria-hidden="true">{paused?'▷':'Ⅱ'}</span></button>}
  </div>;
}
