(() => {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function setupNavigation() {
    const toggle = document.querySelector('[data-nav-toggle]');
    const nav = document.getElementById('site-nav');
    if (!toggle || !nav) return;
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('hidden') === false;
      toggle.setAttribute('aria-expanded', String(open));
    });
    nav.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 1024) {
          nav.classList.add('hidden');
          toggle.setAttribute('aria-expanded', 'false');
        }
      });
    });
  }

  function setupRevealOnScroll() {
    const elements = document.querySelectorAll('.fade-in-up');
    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
      elements.forEach((element) => element.classList.add('visible'));
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    elements.forEach((element) => observer.observe(element));
  }

  function setupCarousel(root) {
    const track = root.querySelector('.carousel-track');
    const slides = root.querySelectorAll('.carousel-slide');
    const dotsContainer = root.querySelector('[data-carousel-dots]');
    if (!track || slides.length < 2) return;

    let current = 0;
    let timer = null;
    const dots = Array.from(slides, (_, index) => {
      const dot = document.createElement('button');
      dot.type = 'button';
      dot.setAttribute('aria-label', `${index + 1} / ${slides.length}`);
      dot.addEventListener('click', () => { goTo(index); restart(); });
      dotsContainer.appendChild(dot);
      return dot;
    });

    function goTo(index) {
      current = (index + slides.length) % slides.length;
      track.style.transform = `translateX(-${current * 100}%)`;
      dots.forEach((dot, i) => dot.setAttribute('aria-current', String(i === current)));
    }

    function restart() {
      if (prefersReducedMotion) return;
      clearInterval(timer);
      timer = setInterval(() => goTo(current + 1), 6000);
    }

    root.querySelector('[data-carousel-prev]').addEventListener('click', () => { goTo(current - 1); restart(); });
    root.querySelector('[data-carousel-next]').addEventListener('click', () => { goTo(current + 1); restart(); });
    goTo(0);
    restart();
  }

  function setupLightbox() {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox) return;
    const image = lightbox.querySelector('.lightbox-image');
    const closeButton = lightbox.querySelector('.lightbox-close');
    let lastFocus = null;

    function open(source) {
      lastFocus = document.activeElement;
      image.src = source.dataset.full || source.currentSrc || source.src;
      image.alt = source.alt;
      lightbox.hidden = false;
      closeButton.focus();
    }

    function close() {
      lightbox.hidden = true;
      image.removeAttribute('src');
      if (lastFocus) lastFocus.focus();
    }

    document.querySelectorAll('.js-lightbox').forEach((element) => {
      element.tabIndex = 0;
      element.addEventListener('click', () => open(element));
      element.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(element); }
      });
    });
    closeButton.addEventListener('click', close);
    lightbox.addEventListener('click', (event) => { if (event.target === lightbox) close(); });
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !lightbox.hidden) close(); });
  }

  function respectDataSaver() {
    const video = document.querySelector('.hero-video');
    const connection = navigator.connection;
    if (video && (prefersReducedMotion || (connection && connection.saveData))) {
      video.removeAttribute('autoplay');
      video.pause();
    }
  }

  setupNavigation();
  setupRevealOnScroll();
  document.querySelectorAll('[data-carousel]').forEach(setupCarousel);
  setupLightbox();
  respectDataSaver();
})();
