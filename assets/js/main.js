(() => {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function setupNavigation() {
    const toggle = document.querySelector('[data-nav-toggle]');
    const nav = document.getElementById('site-nav');
    if (!toggle || !nav) return;
    const close = () => {
      nav.classList.add('hidden');
      toggle.setAttribute('aria-expanded', 'false');
    };
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('hidden') === false;
      toggle.setAttribute('aria-expanded', String(open));
    });
    nav.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener('click', () => { if (window.innerWidth < 1024) close(); });
    });
  }

  function setupReveal() {
    const elements = document.querySelectorAll('.reveal');
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

  function setupLightbox() {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox) return;
    const image = lightbox.querySelector('.lightbox-image');
    const closeButton = lightbox.querySelector('.lightbox-close');
    let lastFocus = null;

    function open(trigger) {
      const source = trigger.querySelector('img');
      if (!source) return;
      lastFocus = trigger;
      image.src = source.dataset.full || source.currentSrc || source.src;
      image.alt = source.alt;
      lightbox.hidden = false;
      document.body.style.overflow = 'hidden';
      closeButton.focus();
    }

    function close() {
      lightbox.hidden = true;
      image.removeAttribute('src');
      document.body.style.overflow = '';
      if (lastFocus) lastFocus.focus();
    }

    document.querySelectorAll('[data-lightbox]').forEach((trigger) => {
      trigger.addEventListener('click', () => open(trigger));
    });
    closeButton.addEventListener('click', close);
    lightbox.addEventListener('click', (event) => { if (event.target === lightbox) close(); });
    document.addEventListener('keydown', (event) => {
      if (lightbox.hidden) return;
      if (event.key === 'Escape') close();
      if (event.key === 'Tab') { event.preventDefault(); closeButton.focus(); }
    });
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
  setupReveal();
  setupLightbox();
  respectDataSaver();
})();
