import React,{useRef} from 'react';
import {ArrowUpRight} from 'lucide-react';
import useHeroVideo from './useHeroVideo.js';
import useLang,{LangSwitch} from './useLang.jsx';
import CopyEmail from './CopyEmail.jsx';

function OceanMark(){return <svg viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15"/><path d="M4 17c5-6 9 6 14 0s9 6 14 0M5 23c5-6 8 6 13 0s8 6 13 0"/><path d="M18 3v5M3 18h5M28 18h5"/></svg>;}

export const heroMedia={
  video:'https://videos.pexels.com/video-files/1409899/1409899-uhd_2560_1440_25fps.mp4'
};

export function HeroNavigation(){
  const [lang,t]=useLang();
  return <nav className="nav shell" aria-label="Primary navigation">
    <a className="brand" href="#top"><OceanMark/><span>OCEAN CARBON<span className="brand-subtitle">{lang==='zh'?'一个采样实验':'A sampling experiment'}</span></span></a>
    <div className="nav-links">{t.nav.map(([href,label])=><a key={href} href={href}>{label}</a>)}</div>
    <CopyEmail lang={lang} label={t.contact}/>
    <LangSwitch lang={lang}/>
    <details className="mobile-navigation" id="mobile-navigation" onClick={event=>{if(event.target.closest('a'))event.currentTarget.open=false;}} onKeyDown={event=>{if(event.key==='Escape'){event.currentTarget.open=false;event.currentTarget.querySelector('summary').focus();}}}>
      <summary>{t.menu} <span aria-hidden="true">+</span></summary>
      <div className="mobile-nav-links">{[...t.nav,...t.more].map(([href,label])=><a key={href} href={href}>{label}<ArrowUpRight className="ui-arrow" aria-hidden="true" /></a>)}</div>
    </details>
  </nav>;
}

// Public fallback when the licensed Hero 9 block is absent.
export default function Hero(){
  const heroRef=useRef(null),videoRef=useRef(null);
  const [,t]=useLang();
  useHeroVideo(videoRef,heroRef);
  return <header id="top" className="cinematic-hero" ref={heroRef}>
    <video ref={videoRef} id="hero-video" className="hero-video" muted loop playsInline preload="none" data-src={heroMedia.video} aria-hidden="true" tabIndex={-1}/>
    <a className="skip-link" href="#evidence-story">{t.skip}</a>
    <HeroNavigation/>
    <div className="hero shell">
      <div className="hero-copy">
        <p className="eyebrow">{t.eyebrow}</p>
        <h1><span className="hero-reveal-line">{t.line1}</span><br/><span className="hero-reveal-line hero-line-soft">{t.line2}</span></h1>
        <div className="hero-intro">
          <p className="lede">{t.description}</p>
          <div className="hero-actions"><a className="button primary" href="#intro">{t.explore} <ArrowUpRight aria-hidden="true" size={20}/></a><a className="hero-code" href="https://github.com/BokaiHe/ocean-carbon-sampling">{t.code} <ArrowUpRight aria-hidden="true" size={20}/></a></div>
        </div>
      </div>
    </div>
    <div className="hero-footer shell">
      <p className="byline"><strong>Bokai He</strong><span>Columbia EEE</span><a href="#sources">{t.credits} <ArrowUpRight className="ui-arrow" aria-hidden="true"/></a></p>
    </div>
  </header>;
}
