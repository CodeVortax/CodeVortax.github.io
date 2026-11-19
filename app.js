// CodeVortax site: scroll reveal slides, filter chips, nav state.
(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- scroll reveal: slide elements in once ---- */
  var revealables = Array.prototype.slice.call(document.querySelectorAll('.reveal'));

  if (!('IntersectionObserver' in window) || reduce) {
    revealables.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var siblings = Array.prototype.slice.call(el.parentElement.children);
        var index = siblings.indexOf(el);
        // stagger cards so they slide in one after another
        el.style.transitionDelay = Math.min(index, 6) * 70 + 'ms';
        el.classList.add('in');
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });

    revealables.forEach(function (el) { io.observe(el); });
  }

  /* ---- pointer glow on cards ---- */
  document.querySelectorAll('.card').forEach(function (card) {
    card.addEventListener('pointermove', function (e) {
      var r = card.getBoundingClientRect();
      card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      card.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
    // drop the fill-forwards animation so hover transforms keep working
    card.addEventListener('animationend', function () {
      card.classList.remove('pop');
      card.style.animationDelay = '';
    });
  });

  /* ---- project filters ---- */
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var empty = document.getElementById('empty');

  function applyFilter(cat) {
    var shown = 0;
    cards.forEach(function (card) {
      var match = cat === 'all' || card.dataset.cat === cat;
      card.classList.toggle('is-hidden', !match);
      if (match) {
        shown++;
        if (!reduce) {
          card.classList.remove('pop');
          void card.offsetWidth; // restart the animation
          card.style.animationDelay = Math.min(shown - 1, 8) * 45 + 'ms';
          card.classList.add('pop');
        }
      }
    });
    if (empty) empty.hidden = shown !== 0;
  }

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) {
        var active = c === chip;
        c.classList.toggle('is-active', active);
        c.setAttribute('aria-pressed', String(active));
      });
      applyFilter(chip.dataset.filter);
    });
  });

  /* ---- nav shadow + scroll progress ---- */
  var nav = document.querySelector('.nav');
  var bar = document.getElementById('bar');
  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      var y = window.scrollY;
      var h = document.documentElement.scrollHeight - window.innerHeight;
      if (nav) nav.classList.toggle('scrolled', y > 8);
      if (bar) bar.style.width = (h > 0 ? Math.min(y / h, 1) * 100 : 0) + '%';
      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- footer year ---- */
  var year = document.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());
})();
