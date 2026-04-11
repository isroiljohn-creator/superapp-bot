/* ══════════════════════════════════════════════
   main.js – NUVI Academy Landing Page
   Handles: theme toggle, scroll reveal, form
══════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ───────────── THEME TOGGLE ─────────────── */
  const html = document.documentElement;
  const toggleBtn = document.getElementById('themeToggle');

  // Persist preference
  const savedTheme = localStorage.getItem('nuvi-theme') || 'light';
  html.setAttribute('data-theme', savedTheme);

  function setTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem('nuvi-theme', theme);
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      setTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  /* ───────── SCROLL REVEAL ────────────────── */
  const revealEls = document.querySelectorAll(
    '.why-card, .learn-item, .speaker-card, .cta-card, .section-header'
  );

  revealEls.forEach((el) => el.classList.add('reveal'));

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry, idx) => {
          if (entry.isIntersecting) {
            // Stagger siblings inside a grid
            const siblings = entry.target.parentElement.querySelectorAll('.reveal');
            siblings.forEach((sib, i) => {
              if (!sib.classList.contains('visible')) {
                setTimeout(() => sib.classList.add('visible'), i * 80);
              }
            });
            entry.target.classList.add('visible');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    revealEls.forEach((el) => io.observe(el));
  } else {
    // Fallback: just show everything
    revealEls.forEach((el) => el.classList.add('visible'));
  }

  /* ───────────── FORM SUBMISSION ─────────── */
  const form = document.getElementById('registerForm');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name  = document.getElementById('nameInput').value.trim();
      const phone = document.getElementById('phoneInput').value.trim();

      if (!name || !phone) {
        shakeForm(form);
        return;
      }
      
      const btn = form.querySelector('[type="submit"]');
      const originalText = btn.innerHTML;
      btn.textContent = "Kuting...";
      btn.disabled = true;

      try {
        // Send to backend
        const urlParams = new URLSearchParams(window.location.search);
        const refId = urlParams.get('ref');
        
        await fetch('/user/landing-lead', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                phone: phone,
                referer_id: refId ? parseInt(refId) : null
            })
        });

        // Show success state
        btn.textContent = '✓ Ro\'yxatdan o\'tdingiz!';
        btn.style.background = 'linear-gradient(90deg, #28C840, #4CD463)';
        btn.style.color = '#fff';
        btn.style.boxShadow = '0 4px 20px rgba(40,200,64,0.35)';
      } catch (err) {
        console.error("Xatolik:", err);
        btn.innerHTML = originalText;
        btn.disabled = false;
        shakeForm(form);
        alert("Xatolik yuz berdi. Iltimos qayta urinib ko'ring.");
      }
    });
  }

  function shakeForm(el) {
    el.style.animation = 'shake 0.4s ease';
    el.addEventListener('animationend', () => {
      el.style.animation = '';
    }, { once: true });
  }

  /* Inject shake keyframe */
  const style = document.createElement('style');
  style.textContent = `
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      20%       { transform: translateX(-6px); }
      40%       { transform: translateX(6px); }
      60%       { transform: translateX(-4px); }
      80%       { transform: translateX(4px); }
    }
  `;
  document.head.appendChild(style);
})();
