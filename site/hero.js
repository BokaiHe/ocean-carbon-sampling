/* Real video playback, with a static poster when motion or autoplay is unavailable. */
(() => {
  const hero = document.querySelector('.cinematic-hero');
  const button = document.querySelector('#hero-motion');
  const video = document.querySelector('#hero-video');
  if (!hero || !button || !video) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let userPaused = Boolean(navigator.connection?.saveData);
  let inView = hero.getBoundingClientRect().bottom > 0;
  let blocked = false;
  let failed = false;
  let pendingPlay = false;
  video.muted = true;
  video.defaultMuted = true;
  const wanted = () => !reduced.matches && !userPaused && inView && !document.hidden;
  const render = () => {
    button.hidden = reduced.matches;
    button.setAttribute('aria-pressed', String(userPaused || blocked || failed));
    button.textContent = failed ? 'Retry background video' :
      userPaused || blocked ? 'Play background video' : 'Pause background video';
  };
  const update = () => {
    if (reduced.matches) hero.classList.remove('hero-enter');
    if (!wanted()) {
      video.pause();
    } else if (!blocked && !failed && !pendingPlay && video.paused) {
      if (!video.getAttribute('src')) video.src = video.dataset.src;
      pendingPlay = true;
      video.play().then(() => {
        if (!wanted()) video.pause();
      }).catch(error => {
        // Scrolling away during loading intentionally interrupts play().
        if (error.name !== 'AbortError') blocked = true;
      }).finally(() => {
        pendingPlay = false;
        render();
        if (wanted() && !blocked && !failed && video.paused) update();
      });
    }
    render();
  };
  button.addEventListener('click', () => {
    if (failed) { failed = false; video.load(); }
    userPaused = blocked ? false : !userPaused;
    blocked = false;
    update();
  });
  video.addEventListener('error', () => { failed = true; userPaused = true; render(); });
  // A mobile browser may suspend playback; expose a manual-play control.
  video.addEventListener('pause', () => {
    if (wanted() && !pendingPlay) { blocked = true; render(); }
  });
  reduced.addEventListener('change', update);
  document.addEventListener('visibilitychange', update);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; update(); }).observe(hero);
  }
  update();
  if (!reduced.matches && inView && !location.hash.replace('#top', '')) {
    hero.classList.add('hero-enter');
    // Release filters after the entrance rather than retaining compositor layers.
    setTimeout(() => hero.classList.remove('hero-enter'), 1800);
  }
})();
