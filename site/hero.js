/* Progressive enhancement: content stays visible if this script fails to load. */
(() => {
  const hero = document.querySelector('.cinematic-hero');
  const button = document.querySelector('#hero-motion');
  if (!hero || !button) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let userPaused = false;
  let inView = true;
  const update = () => {
    const enabled = !reduced.matches;
    hero.classList.toggle('hero-motion-enabled', enabled);
    hero.classList.toggle('hero-motion-paused', userPaused || !inView || document.hidden);
    button.hidden = !enabled;
    button.setAttribute('aria-pressed', String(userPaused));
    button.textContent = userPaused ? 'Resume background motion' : 'Pause background motion';
    if (!enabled) hero.classList.remove('hero-enter');
  };
  button.addEventListener('click', () => { userPaused = !userPaused; update(); });
  reduced.addEventListener('change', update);
  document.addEventListener('visibilitychange', update);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; update(); }).observe(hero);
  }
  update();
  if (!reduced.matches && hero.getBoundingClientRect().bottom > 0 && !location.hash.replace('#top', '')) {
    hero.classList.add('hero-enter');
    // Release filters after the entrance rather than retaining compositor layers.
    setTimeout(() => hero.classList.remove('hero-enter'), 1800);
  }
})();
