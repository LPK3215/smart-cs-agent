/* ============================================================
   Smart CS Agent — Project Overview Interactive Logic
   Tab switching, accordion, scroll animations, counters
   ============================================================ */

(function() {
  'use strict';

  // ----- Tab Navigation -----
  function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    const sections = document.querySelectorAll('[data-section]');

    function activateTab(targetId) {
      tabs.forEach(t => t.classList.remove('active'));
      const activeTab = document.querySelector(`.nav-tab[data-target="${targetId}"]`);
      if (activeTab) activeTab.classList.add('active');

      sections.forEach(s => {
        if (s.getAttribute('data-section') === targetId) {
          s.style.display = 'block';
        } else {
          s.style.display = 'none';
        }
      });
    }

    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.getAttribute('data-target');
        if (target) activateTab(target);
      });
    });

    // Activate first tab by default
    if (tabs.length > 0) {
      activateTab(tabs[0].getAttribute('data-target'));
    }

    // Handle hash-based navigation
    function handleHash() {
      const hash = window.location.hash.slice(1);
      if (hash) {
        const matchingTab = document.querySelector(`.nav-tab[data-target="${hash}"]`);
        if (matchingTab) activateTab(hash);
      }
    }
    window.addEventListener('hashchange', handleHash);
    handleHash();
  }

  // ----- Accordion -----
  function initAccordions() {
    document.querySelectorAll('.accordion-trigger').forEach(trigger => {
      trigger.addEventListener('click', () => {
        const accordion = trigger.closest('.accordion');
        if (accordion) {
          accordion.classList.toggle('open');
        }
      });
    });

    // Open first accordion by default
    const firstAccordion = document.querySelector('.accordion');
    if (firstAccordion) {
      firstAccordion.classList.add('open');
    }
  }

  // ----- Scroll Animation (Intersection Observer) -----
  function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });

    document.querySelectorAll('.fade-up').forEach(el => {
      observer.observe(el);
    });
  }

  // ----- Stat Counter Animation -----
  function initCounters() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseInt(el.getAttribute('data-count'), 10);
          if (!target || el.dataset.animated === 'true') return;

          el.dataset.animated = 'true';
          const duration = 1500;
          const start = performance.now();

          function update(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(eased * target);
            el.textContent = current;

            if (progress < 1) {
              requestAnimationFrame(update);
            } else {
              el.textContent = target;
            }
          }

          requestAnimationFrame(update);
        }
      });
    }, { threshold: 0.3 });

    document.querySelectorAll('[data-count]').forEach(el => {
      observer.observe(el);
    });
  }

  // ----- Smooth scroll for anchor links -----
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href').slice(1);
        const target = document.querySelector(`[data-section="${targetId}"]`) ||
                       document.getElementById(targetId);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  // ----- Copy to clipboard -----
  function initCopyButtons() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const code = btn.closest('.code-block')?.querySelector('pre')?.textContent;
        if (code) {
          navigator.clipboard.writeText(code).then(() => {
            const original = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(() => { btn.textContent = original; }, 2000);
          });
        }
      });
    });
  }

  // ----- Initialize all -----
  function initAll() {
    initTabs();
    initAccordions();
    initScrollAnimations();
    initCounters();
    initSmoothScroll();
    initCopyButtons();
  }

  // Initialize after content is loaded (via fetch in parent page)
  document.addEventListener('content-loaded', initAll);

  // Also initialize on DOMContentLoaded in case content is already present
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      // Check if content already exists (direct open scenario)
      if (document.querySelector('.hero')) {
        initAll();
      }
    });
  } else {
    if (document.querySelector('.hero')) {
      initAll();
    }
  }

})();
