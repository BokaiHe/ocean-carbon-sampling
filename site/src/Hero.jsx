import React,{useRef} from 'react';
import useHeroVideo from './useHeroVideo.js';

const chapters=[['#background','The question'],['#voyage','Observed ocean'],['#workflow','The method'],['#validation','Findings']];
function OceanMark(){return <svg viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15"/><path d="M4 17c5-6 9 6 14 0s9 6 14 0M5 23c5-6 8 6 13 0s8 6 13 0"/><path d="M18 3v5M3 18h5M28 18h5"/></svg>;}

export default function Hero(){
  const heroRef=useRef(null),videoRef=useRef(null);
  const media=useHeroVideo(videoRef,heroRef);
  const paused=media.mode==='paused'||media.mode==='error';
  return <header id="top" className="cinematic-hero" ref={heroRef}>
    <video ref={videoRef} id="hero-video" className="hero-video" muted loop playsInline preload="none" poster="assets/context/ocean-waves-poster.jpg" data-src="assets/context/ocean-waves.mp4" aria-hidden="true" tabIndex={-1}/>
    <a className="skip-link" href="#background">Skip to the research</a>
    <nav className="nav shell" aria-label="Primary navigation">
      <a className="brand" href="#top"><OceanMark/><span>OCEAN CARBON<span className="brand-subtitle">A sampling experiment</span></span></a>
      <div className="nav-links">{chapters.map(([href,label])=><a key={href} href={href}>{label}</a>)}</div>
      <a className="hero-contact" href="mailto:bh2954@columbia.edu">Let’s talk <span aria-hidden="true">↗</span></a>
      <details className="mobile-navigation" id="mobile-navigation" onClick={event=>{if(event.target.closest('a'))event.currentTarget.open=false;}} onKeyDown={event=>{if(event.key==='Escape'){event.currentTarget.open=false;event.currentTarget.querySelector('summary').focus();}}}>
        <summary>Menu <span aria-hidden="true">＋</span></summary>
        <div className="mobile-nav-links">{[...chapters,['#sampling','Explore the experiment'],['#technical','Boundaries'],['#related-work','Sources & credits']].map(([href,label])=><a key={href} href={href}>{label}<span aria-hidden="true">↗</span></a>)}</div>
      </details>
    </nav>
    <div className="publication-strip shell"><span><i aria-hidden="true"/>Independent research / 01</span><span>Ocean observation &amp; machine learning</span></div>
    <div className="hero shell">
      <div className="hero-copy">
        <p className="eyebrow">How much can a few observations tell us?</p>
        <h1><span className="hero-reveal-line">A vast ocean.</span><br/><span className="hero-reveal-line hero-line-soft">A few paths through it.</span></h1>
        <div className="hero-intro">
          <p className="lede">We cannot measure everywhere.<br/>With the same number of observations, how much does <em>where we look</em> change what we know?</p>
          <div className="hero-actions"><a className="button primary" href="#background">Explore the research <span aria-hidden="true">↘</span></a><a className="hero-code" href="https://github.com/BokaiHe/ocean-carbon-sampling">Code &amp; data <span aria-hidden="true">↗</span></a></div>
        </div>
      </div>
    </div>
    <div className="hero-footer shell">
      <p className="byline"><strong>Bokai He</strong><span>Columbia EEE · Independent course-project extension</span><a href="#related-work">Course foundation &amp; credits ↗</a></p>
      <div className="hero-footer-right"><button id="hero-motion" type="button" aria-controls="hero-video" aria-pressed={paused} hidden={!media.allowed} onClick={media.toggle}><span aria-hidden="true">{paused?'▷':'Ⅱ'}</span>{media.mode==='error'?'Retry background video':paused?'Play background video':'Pause background video'}</button><a className="hero-image-credit" href="https://www.pexels.com/video/aerial-view-of-ocean-waves-4631568/">ArtHouse Studio / Pexels ↗<small>Context imagery, not model output.</small></a></div>
    </div>
    <div className="story-rail shell" aria-label="Explore the study">{[['01','#background','Why location matters'],['02','#workflow','Test with a known answer'],['03','#validation','See what changes']].map(([number,href,label])=><a key={number} href={href}><small>{number}</small><span>{label}</span><b aria-hidden="true">↗</b></a>)}</div>
  </header>;
}
