import React,{useEffect,useRef,useState} from 'react';
import {ArrowUpRight,Check} from 'lucide-react';

const EMAIL='bh2954@columbia.edu';

export default function CopyEmail({lang,label}){
  const [status,setStatus]=useState('');
  const timer=useRef(null);
  const busy=useRef(false);
  useEffect(()=>()=>clearTimeout(timer.current),[]);

  async function copy(){
    if(busy.current)return;
    busy.current=true;
    clearTimeout(timer.current);
    let copied=false;
    try{
      await navigator.clipboard.writeText(EMAIL);
      copied=true;
    }catch{
      // Older browsers may still allow copying during the click gesture.
      const focused=document.activeElement;
      const field=document.createElement('textarea');
      field.value=EMAIL;
      field.readOnly=true;
      field.style.cssText='position:fixed;left:-9999px;top:0;';
      document.body.append(field);
      try{field.select();copied=document.execCommand('copy');}catch{/* Show manual-copy fallback. */}
      finally{field.remove();focused?.focus({preventScroll:true});}
    }
    busy.current=false;
    setStatus(copied?'copied':'failed');
    if(copied)timer.current=setTimeout(()=>setStatus(''),5000);
  }

  const copied=status==='copied';
  return <>
    <button type="button" className="hero-contact" onClick={copy}
      title={`${lang==='zh'?'复制邮箱':'Copy email'}: ${EMAIL}`}>
      {copied?(lang==='zh'?'邮箱已复制':'Email copied'):label}
      {copied?<Check className="ui-arrow" aria-hidden="true"/>:<ArrowUpRight className="ui-arrow" aria-hidden="true"/>}
    </button>
    <div className={`contact-copy-status${status?' is-visible':''}`} role="status" aria-live="polite" aria-atomic="true">
      {status&&<>{copied?(lang==='zh'?'邮箱复制成功':'Email copied to clipboard'):(lang==='zh'?'无法自动复制，请手动复制':'Could not copy automatically. Please copy manually')}
        <span className="contact-copy-address">{EMAIL}</span></>}
    </div>
  </>;
}
