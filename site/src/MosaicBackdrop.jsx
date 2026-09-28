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
        <MosaicWaves pitch={9} fill={0.54} speed={0.24} warp={0.3} color="#426f91" hotColor="#a6c9df" backgroundColor="#102c40" brightness={3.8} ambient={0.025} vignette={0.45} cursorInteraction={false} dpr={1.25} targetFps={30} paused={paused}/>
      </Suspense></BackgroundBoundary>}
    </div>
    {__HAS_LICENSED_MOSAIC__&&!calm&&<button type="button" className="mosaic-pause" onClick={()=>setPaused(p=>!p)} aria-pressed={paused}>{paused?'Play waves':'Pause waves'} <span aria-hidden="true">{paused?'▷':'Ⅱ'}</span></button>}
  </div>;
}
