import React,{useEffect,useState} from 'react';

// Hero copy in both languages; the rest of the page is translated by i18n.js.
export const heroText={
  en:{
    eyebrow:'Ocean carbon / A sampling experiment',
    line1:'A vast ocean.',line2:'A few paths through it.',
    description:'We cannot measure everywhere. With the same number of observations, how much does where we look change what we know?',
    explore:'Explore the research',code:'Code & data',how:'How it works',
    credits:'Course foundation & credits',contact:'Let’s talk',menu:'Menu',skip:'Skip to the research',
    nav:[['#intro','Intro'],['#background','Background'],['#method','Method'],['#findings','Findings']],
    more:[['#conclusion','Conclusion'],['#limits','Limits'],['#sources','Sources & credits']],
  },
  zh:{
    eyebrow:'海洋碳汇 / 一个采样实验',
    line1:'浩瀚海洋，',line2:'寥寥航迹。',
    description:'我们无法处处测量。观测数量相同时，测在哪里，会在多大程度上改变我们对海洋的认识？',
    explore:'开始阅读',code:'代码与数据',how:'研究方法',
    credits:'课程基础与致谢',contact:'联系我',menu:'菜单',skip:'跳到正文',
    nav:[['#intro','引言'],['#background','背景'],['#method','方法'],['#findings','发现']],
    more:[['#conclusion','结论'],['#limits','局限'],['#sources','来源与致谢']],
  },
};

export default function useLang(){
  // Server render and first client render are English, so hydration matches.
  const [lang,setLang]=useState('en');
  useEffect(()=>{
    const sync=()=>setLang(window.OCS?.lang==='zh'?'zh':'en');
    sync();
    document.addEventListener('ocs:lang',sync);
    return()=>document.removeEventListener('ocs:lang',sync);
  },[]);
  return [lang,heroText[lang]];
}

export function LangSwitch({lang}){
  // Clicks are handled by i18n.js so the whole page switches together.
  return <div className="lang-switch" role="group" aria-label="Language">
    <button type="button" data-lang-set="en" aria-pressed={lang==='en'}>EN</button>
    <button type="button" data-lang-set="zh" aria-pressed={lang==='zh'}>中文</button>
  </div>;
}
