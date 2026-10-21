/* Bilingual text. English lives in the HTML; this file holds Chinese and the switch. */
(() => {
  'use strict';
  const zh = {
    'nav.intro':'引言','nav.background':'背景','nav.method':'方法','nav.findings':'发现','nav.conclusion':'结论','nav.limits':'局限','nav.sources':'来源',
    'skip':'跳到正文',

    'intro.kicker':'01 · 引言',
    'intro.title':'海洋吸收了大量 CO₂，<br/>但我们只测到<span class="hl-co2">一小部分</span>。',
    'intro.stat1':'人类每年排放的 CO₂，约有这么多被海洋吸收',
    'intro.stat2':'2014 年有船测数据的月度 1° 海洋网格',
    'intro.stat3':'每次实验的样本数——只改变它们放在哪里',
    'intro.lede':'机器学习把稀疏的测量补成完整的海洋 CO₂ 地图。<b>如果测量本身扎堆，地图会变差吗？下一批观测又该放在哪里？</b>',
    'intro.photo':'从太空看凯尔特海的浮游植物水华——海洋表层并不均匀。',
    'intro.source':'来源：Global Carbon Budget',

    'bg.kicker':'02 · 研究背景',
    'bg.title':'船只去过的地方，<br/>和<span class="hl-teal">没去过的</span>地方。',
    'bg.lede':'每个点是一个有真实表层海水 fCO₂ 测量的 1° 网格（SOCAT v2025）。拖动地球，换年份或月份看看空白在哪里。',
    'bg.photo':'把仪器放入海中的科考船。真实测量昂贵、稀疏，而且沿航线分布。',

    'obs.year':'年份','obs.all':'全年','obs.scale':'表层海水 fCO₂ · µatm','obs.land':'陆地','obs.none':'无观测',
    'obs.drag':'拖动旋转 · 双指或 Ctrl + 滚轮缩放',

    'method.kicker':'03 · 研究方法',
    'method.title':'用一个<span class="hl-teal">模拟海洋</span><br/>当标准答案。',
    'method.lede':'真实海洋没有"完整答案"。所以我们用地球系统模式的海洋当真值，隐藏一部分，再看不同采样方式能把它还原得多好。',
    'step1.t':'真值','step1.d':'IPSL-CM6A-LR 模式给出完整的月度表层 pCO₂',
    'step2.t':'隐藏','step2.d':'预留 20% 的月度格点作为所有方案共用的测试集',
    'step3.t':'采样','step3.d':'按某条规则挑出 5,000 个月度格点',
    'step4.t':'学习','step4.d':'同一个梯度提升模型，用 SST、盐度、位置和月份补全地图',
    'step5.t':'打分','step5.d':'与隐藏的真值比较误差，20 组配对随机种子',
    'rules.title':'三种采样规则，同样 5,000 个样本',
    'rules.note':'示意地图及区块计数：2005 年、种子 0、加海洋掩膜之前的原始全域，不是上方主比较的结果。',
    'rule.random':'随机','rule.random.d':'每个格点机会相等',
    'rule.historical':'历史密度','rule.historical.d':'按 1990–2004 年 SOCAT 观测密度加权——不是重放真实航线',
    'rule.coverage':'均匀覆盖','rule.coverage.d':'优先填补观测少的空间与月份',
    'domain.chip':'主比较：60°N 以南 · 连通海洋 · 面积加权 · 2005、2010、2014 年 · 20 组配对种子',
    'aug.title':'第二个实验：在真实网络上增补',
    'aug1.t':'保留真实网络','aug1.d':'2005 年所有与模式海洋对应的 SOCAT 月度格点都留在训练集中',
    'aug2.t':'用两种方式加 1,000 个','aug2.d':'随机加，或只加在 1990–2005 年 SOCAT 从未测过的位置——月份和数量相同',
    'aug3.t':'在同一批隐藏格点上打分','aug3.d':'共用一个测试集、5 组配对种子；新加的格点不参与测试',
    'aug.chip':'开阔大洋（去掉边缘海和近岸格点）· 60°N 以南 · 2005 年 · 5 组种子',
    'globe.title':'亲自看看：采样点和误差在哪里',
    'globe.layer':'显示','globe.sampling':'采样点','globe.mae':'预测误差','globe.delta':'比随机好还是差',
    'globe.plan':'采样规则','globe.note':'2005 年全域辅助视图（加海洋掩膜之前），不是主评估。',

    'find.kicker':'04 · 研究发现',
    'find.title':'三个发现',
    'f1.label':'发现 1','f1.title':'按历史观测密度采样，<br/>重建<span class="hl-hist">误差更高</span>。',
    'f1.unit':'平均绝对误差高于随机采样',
    'f1.hidden':'隐藏格点 · 3 个年份','f1.block':'整块留出 · 15 个单元',
    'f1.caption':'MAE（µatm），越低越好。每一行在同一测试集上比较，20 组配对种子取平均。三个年份、15 个整块单元无一例外。',
    'f2.label':'发现 2','f2.title':'分散采样削减的是<span class="hl-cov">极端误差</span>，<br/>不是典型误差。',
    'f2.caption':'均匀覆盖 − 随机（µatm），越低越好。RMSE 的优势主要来自边缘海和近岸格点：只看开阔大洋时几乎消失。',
    'f2.mae':'MAE（典型误差）','f2.rmse':'RMSE（极端误差）',
    'mask.m0':'原模式海域','mask.m1':'连通海洋','mask.m2':'开阔大洋',
    'f3.label':'发现 3','f3.title':'再加 1,000 个观测：<span class="hl-teal">很有用</span>。<br/>专门加在空白区：<span class="hl-gap">只多一点</span>。',
    'f3.s1':'加 1,000 个观测后 RMSE 下降（µatm）','f3.s2':'专门加在历史空白区，额外再降（µatm）',
    'f3.map':'现有网络和新增的 1,000 个点','f3.seed':'种子','f3.arm':'新增方式',
    'arm.baseline':'现有网络','arm.random':'+ 随机','arm.gap':'+ 空白区',
    'f3.legend.h':'2005 年 SOCAT 现有网络','f3.legend.gap':'1990–2005 从未观测的位置',
    'f3.bars':'各区域的 RMSE（µatm）','f3.dots':'随机 − 空白区的 RMSE：每个种子的差值（µatm，正值有利于补空白）',
    'dom.global':'全部未观测','dom.gap':'历史空白区','dom.observed':'原先有观测处',
    'f3.caption':'2005 年，开阔大洋，60°N 以南。加在空白区对空白区有帮助，但原先有观测的区域略变差。若保留边缘海（连通海洋），优势看起来更大（额外再降 1.32 µatm），但约 80% 来自哈德逊湾；更早的全球版本则被北极和内陆湖放大。这两次限定海域的重跑是在看过全球结果之后决定的。',

    'checks.kicker':'05 · 稳健性',
    'checks.title':'换个问法，<br/>结论还在吗？',
    'c1.t':'每个年份','c1.d':'2005、2010、2014 年，历史密度采样都更差',
    'c2.t':'整块留出','c2.d':'15 个年份×空间折单元全部更差：+18.0%',
    'c3.t':'海洋掩膜','c3.d':'剔除内陆湖、边缘海和近岸后方向不变',
    'c4.t':'有符号偏差','c4.d':'历史密度 − 随机的偏差（µatm，整块留出评估）在按面积加权、对齐评估区域后缩小到这个程度——太敏感，不作为主要结论',

    'concl.kicker':'06 · 结论',
    'concl.title':'在这些测试中，历史密度采样<span class="hl-hist">误差更高</span>。<br/>两种补点方案都<span class="hl-teal">改善了重建</span>。',
    'a1.t':'测在哪里很重要','a1.d':'同样 5,000 个样本，按历史观测密度分配，MAE 高于随机采样——每个测试年份都是如此。',
    'a2.t':'均匀铺开不是万能药','a2.d':'均匀覆盖削减了最大的误差，主要在近岸和边缘海；典型误差几乎不变。',
    'a3.t':'两种增加观测的方式','a3.d':'在 2005 年开阔大洋测试中，两种增加 1,000 个观测的规则都降低了 RMSE；相对现有网络的改善，大于两种补点规则之间的小幅差别。',
    'concl.lede':'采样位置很重要，但这些测试没有找出最优部署方案。所有结果都依赖于一个模拟海洋和一个学习器；对真实观测网络的收益仍未验证。',
    'limits.kicker':'07 · 局限',
    'limits.title':'这项研究<br/><span class="hl-co2">不能</span>说明什么。',
    'l1':'只用了一个地球系统模式的海洋','l2':'只用了一种机器学习模型和有限的特征','l3':'理想化观测：没有测量误差',
    'l4':'样本是网格点，不是真实航线，也不考虑可行性和成本','l5':'只看 60°N 以南','l6':'增补实验只有 2005 一年',

    'src.kicker':'08 · 来源与致谢',
    'src.title':'数据、代码与合作者',
    'src.data':'数据','src.related':'相关研究','src.people':'课程与团队','src.more':'详细内容',
    'src.people.d':'本项目是 2025 年春季 Galen A. McKinley 课程（EESC/STAT 4243）项目的独立延伸。原团队：Azam Khan、Bokai He、Sarah Pariser、Zhi Wang。',
    'src.more.d':'方法细节、所有表格和审计记录都在 notebook 和文档里。',
    'src.notebook':'结果 notebook','src.repo':'代码仓库','src.protocols':'实验协议',
    'foot':'Bokai He · 哥伦比亚大学地球与环境工程系 · 2026',
  };
  const store = {get(){try{return localStorage.getItem('ocs-lang');}catch(e){return null;}}, set(v){try{localStorage.setItem('ocs-lang',v);}catch(e){}}};
  const english = new Map();
  let lang = store.get() === 'zh' ? 'zh' : 'en';

  function apply() {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.querySelectorAll('[data-i18n]').forEach(node => {
      const key = node.dataset.i18n;
      if (!english.has(key + '@' + node.tagName)) english.set(key + '@' + node.tagName, node.innerHTML);
      node.innerHTML = lang === 'zh' && zh[key] ? zh[key] : english.get(key + '@' + node.tagName);
    });
    // React owns the hero's switch; touching it before hydration causes a mismatch.
    document.querySelectorAll('[data-lang-set]').forEach(button => {
      if (!button.closest('#hero-root')) button.setAttribute('aria-pressed', String(button.dataset.langSet === lang));
    });
    document.dispatchEvent(new CustomEvent('ocs:lang', {detail: {lang}}));
  }
  window.OCS = {
    get lang() { return lang; },
    /* Inline pair for strings generated by scripts. */
    tr: (en, cn) => (lang === 'zh' ? cn : en),
    set(next) { if (next === lang) return; lang = next; store.set(lang); apply(); },
  };
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-lang-set]');
    if (button) window.OCS.set(button.dataset.langSet);
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply); else apply();
})();
