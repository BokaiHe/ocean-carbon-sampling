import {useEffect,useRef,useState} from 'react';

export default function useHeroVideo(videoRef,heroRef){
  const [media,setMedia]=useState({allowed:false,mode:'loading'});
  const controller=useRef(null);
  useEffect(()=>{
    const video=videoRef.current,hero=heroRef.current;
    const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
    let userPaused=Boolean(navigator.connection?.saveData),blocked=false,failed=false,pending=false,disposed=false;
    let inView=hero.getBoundingClientRect().bottom>0;
    video.muted=true;video.defaultMuted=true;
    const wanted=()=>!disposed&&!reduced.matches&&!userPaused&&inView&&!document.hidden;
    const render=()=>{if(!disposed)setMedia({allowed:!reduced.matches,mode:failed?'error':userPaused||blocked?'paused':'playing'});};
    const update=()=>{
      if(reduced.matches)hero.classList.remove('hero-enter');
      if(!wanted())video.pause();
      else if(!blocked&&!failed&&!pending&&video.paused){
        if(!video.getAttribute('src'))video.src=video.dataset.src;
        pending=true;
        video.play().then(()=>{if(!wanted())video.pause();}).catch(error=>{
          if(error.name!=='AbortError')blocked=true;
        }).finally(()=>{
          pending=false;render();
          if(wanted()&&!blocked&&!failed&&video.paused)update();
        });
      }
      render();
    };
    const error=()=>{failed=true;userPaused=true;render();};
    const paused=()=>{if(wanted()&&!pending){blocked=true;render();}};
    controller.current=()=>{
      if(failed){failed=false;video.load();}
      userPaused=blocked?false:!userPaused;blocked=false;update();
    };
    video.addEventListener('error',error);video.addEventListener('pause',paused);
    reduced.addEventListener('change',update);document.addEventListener('visibilitychange',update);
    const observer=new IntersectionObserver(([entry])=>{inView=entry.isIntersecting;update();});observer.observe(hero);
    update();hero.dataset.reactReady='true';
    if(!reduced.matches&&inView&&(!location.hash||location.hash==='#top'))hero.classList.add('hero-enter');
    const timer=setTimeout(()=>hero.classList.remove('hero-enter'),1700);
    return()=>{
      disposed=true;controller.current=null;clearTimeout(timer);observer.disconnect();
      video.removeEventListener('error',error);video.removeEventListener('pause',paused);
      reduced.removeEventListener('change',update);document.removeEventListener('visibilitychange',update);video.pause();
    };
  },[videoRef,heroRef]);
  return {...media,toggle:()=>controller.current?.()};
}
