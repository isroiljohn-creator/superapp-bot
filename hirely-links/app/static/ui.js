/* Hirely UI kit: replaces every native browser popup/control with the brand versions.
   Dropdowns, date(-time) pickers, confirm dialogs and form validation messages.
   Progressive enhancement: without JS the native controls still work. No dependencies. */
(function () {
  'use strict';
  var MONTHS = ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr'];
  var WEEK = ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya'];
  var CHEV = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  var CAL = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>';
  var uid = 0;

  function h(tag, cls, attrs) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    for (var k in (attrs || {})) e.setAttribute(k, attrs[k]);
    for (var i = 3; i < arguments.length; i++) {
      var c = arguments[i];
      if (c == null) continue;
      e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return e;
  }
  function svg(markup) { var s = h('span', 'ico'); s.innerHTML = markup; return s; }
  function pad(n) { return (n < 10 ? '0' : '') + n; }

  /* ---------- open-popover stack (a date picker can host dropdowns) ---------- */
  var stack = [], scrim = null;
  function sync() { document.body.classList.toggle('has-sheet', stack.length > 0); }
  function place(root, panel) {
    panel.classList.remove('up', 'right');
    if (window.innerWidth <= 600) return; // phones use a bottom sheet
    var r = panel.getBoundingClientRect(), rr = root.getBoundingClientRect();
    if (r.right > window.innerWidth - 8) panel.classList.add('right');
    var below = window.innerHeight - rr.bottom;
    if (r.height > below - 8 && rr.top > below) panel.classList.add('up');
  }
  function register(api) {
    if (!scrim) {
      scrim = h('div', 'dd-scrim');
      scrim.addEventListener('pointerdown', function (e) { e.preventDefault(); if (stack.length) stack[stack.length - 1].close(true); });
      document.body.appendChild(scrim);
    }
    stack.push(api); sync();
  }
  function unregister(api) { var i = stack.indexOf(api); if (i >= 0) stack.splice(i, 1); sync(); }
  document.addEventListener('pointerdown', function (e) {
    for (var i = stack.length - 1; i >= 0; i--) {
      if (!stack[i].root.contains(e.target)) stack[i].close(false);
    }
  }, true);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && stack.length) { e.preventDefault(); stack[stack.length - 1].close(true); }
  });

  /* ---------- dropdown (replaces <select>) ---------- */
  function enhanceSelect(sel) {
    if (sel.multiple || sel.dataset.native !== undefined || sel.classList.contains('dd-native')) return;
    var id = sel.id, n = ++uid;
    var root = h('div', 'dd');
    sel.parentNode.insertBefore(root, sel);
    root.appendChild(sel);
    sel.classList.add('dd-native'); sel.tabIndex = -1; sel.setAttribute('aria-hidden', 'true');
    var btn = h('button', 'dd-btn', { type: 'button', 'aria-haspopup': 'listbox', 'aria-expanded': 'false' });
    if (id) { sel.id = id + '-native'; btn.id = id; }
    var text = h('span', 'dd-text');
    btn.appendChild(text); btn.appendChild(svg(CHEV));
    var list = h('ul', 'dd-list', { role: 'listbox', tabindex: '-1', hidden: '' });
    var items = [], active = -1, buf = '', bufT = null;
    Array.prototype.forEach.call(sel.options, function (o, i) {
      var li = h('li', '', { role: 'option', id: 'dd' + n + '-' + i }, o.text);
      if (o.disabled) li.setAttribute('aria-disabled', 'true');
      li.addEventListener('pointerdown', function (e) { e.preventDefault(); });
      li.addEventListener('click', function () { if (!o.disabled) choose(i); });
      li.addEventListener('pointermove', function () { setActive(i, false); });
      items.push(li); list.appendChild(li);
    });
    root.appendChild(btn); root.appendChild(list);
    var api = { root: root, close: close };

    function refresh() {
      var i = sel.selectedIndex;
      text.textContent = i >= 0 ? sel.options[i].text : '';
      items.forEach(function (li, j) { li.setAttribute('aria-selected', j === i ? 'true' : 'false'); });
      btn.disabled = sel.disabled;
    }
    function setActive(i, scroll) {
      if (active >= 0 && items[active]) items[active].classList.remove('is-active');
      active = i;
      if (i >= 0) {
        items[i].classList.add('is-active'); list.setAttribute('aria-activedescendant', items[i].id);
        if (scroll !== false) items[i].scrollIntoView({ block: 'nearest' });
      }
    }
    function open() {
      if (btn.disabled || !list.hidden) return;
      list.hidden = false; root.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true');
      place(root, list); register(api);
      setActive(sel.selectedIndex >= 0 ? sel.selectedIndex : 0);
      list.focus({ preventScroll: true });
    }
    function close(refocus) {
      if (list.hidden) return;
      list.hidden = true; root.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false');
      unregister(api);
      if (refocus) btn.focus({ preventScroll: true });
    }
    function choose(i) {
      if (sel.selectedIndex !== i) { sel.selectedIndex = i; sel.dispatchEvent(new Event('change', { bubbles: true })); }
      refresh(); close(true);
    }
    function move(d) {
      var i = active;
      do { i += d; } while (i >= 0 && i < items.length && items[i].getAttribute('aria-disabled') === 'true');
      if (i >= 0 && i < items.length) setActive(i);
    }
    btn.addEventListener('click', function () { list.hidden ? open() : close(true); });
    btn.addEventListener('keydown', function (e) {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].indexOf(e.key) >= 0) { e.preventDefault(); open(); }
    });
    list.addEventListener('keydown', function (e) {
      var k = e.key;
      if (k === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (k === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (k === 'Home') { e.preventDefault(); setActive(0); }
      else if (k === 'End') { e.preventDefault(); setActive(items.length - 1); }
      else if (k === 'Enter' || k === ' ') { e.preventDefault(); if (active >= 0) choose(active); }
      else if (k === 'Tab') { close(false); }
      else if (k.length === 1 && !e.ctrlKey && !e.metaKey) {
        buf += k.toLowerCase(); clearTimeout(bufT); bufT = setTimeout(function () { buf = ''; }, 600);
        for (var j = 0; j < items.length; j++) {
          if (items[j].textContent.toLowerCase().indexOf(buf) === 0) { setActive(j); break; }
        }
      }
    });
    sel.addEventListener('change', refresh);
    refresh();
  }

  /* ---------- date / date-time picker (replaces native pickers) ---------- */
  function parse(v, withTime) {
    var m = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/.exec(v || '');
    return m ? { y: +m[1], m: +m[2] - 1, d: +m[3], hh: withTime ? +(m[4] || 9) : 0, mm: withTime ? +(m[5] || 0) : 0 } : null;
  }
  function enhanceDate(inp) {
    if (inp.dataset.dp) return;
    inp.dataset.dp = '1';
    var withTime = inp.type === 'datetime-local', id = inp.id;
    var st = parse(inp.value, withTime);
    inp.type = 'hidden';
    if (id) inp.id = id + '-value';
    var root = h('div', 'dd dp');
    inp.parentNode.insertBefore(root, inp);
    root.appendChild(inp);
    var btn = h('button', 'dd-btn', { type: 'button', 'aria-haspopup': 'dialog', 'aria-expanded': 'false' });
    if (id) btn.id = id;
    var text = h('span', 'dd-text');
    btn.appendChild(text); btn.appendChild(svg(CAL));
    var panel = h('div', 'dp-panel', { role: 'dialog', 'aria-label': 'Sanani tanlang', hidden: '' });
    root.appendChild(btn); root.appendChild(panel);
    var api = { root: root, close: close };
    var now = new Date();
    var view = { y: st ? st.y : now.getFullYear(), m: st ? st.m : now.getMonth() };

    var title = h('div', 'dp-title', { 'aria-live': 'polite' });
    function nav(label, aria, dy, dm) {
      var b = h('button', 'dp-nav', { type: 'button', 'aria-label': aria }, label);
      b.addEventListener('click', function () {
        var d = new Date(view.y + dy, view.m + dm, 1); view.y = d.getFullYear(); view.m = d.getMonth(); render();
      });
      return b;
    }
    var head = h('div', 'dp-head', null, nav('«', 'Oldingi yil', -1, 0), nav('‹', 'Oldingi oy', 0, -1), title, nav('›', 'Keyingi oy', 0, 1), nav('»', 'Keyingi yil', 1, 0));
    var grid = h('div', 'dp-grid', { role: 'grid' });
    panel.appendChild(head); panel.appendChild(grid);

    var hourSel, minSel;
    if (withTime) {
      hourSel = h('select', '', { 'aria-label': 'Soat' });
      for (var i = 0; i < 24; i++) hourSel.appendChild(h('option', '', { value: i }, pad(i)));
      minSel = h('select', '', { 'aria-label': 'Daqiqa' });
      var mins = []; for (var j = 0; j < 60; j += 5) mins.push(j);
      if (st && mins.indexOf(st.mm) < 0) { mins.push(st.mm); mins.sort(function (a, b) { return a - b; }); }
      mins.forEach(function (mm) { minSel.appendChild(h('option', '', { value: mm }, pad(mm))); });
      var row = h('div', 'dp-time', null, h('span', 'lbl', null, 'Vaqt'), h('div', 'dp-time-pick', null, hourSel), h('span', 'dp-colon', null, ':'), h('div', 'dp-time-pick', null, minSel));
      panel.appendChild(row);
      hourSel.value = st ? st.hh : 9; minSel.value = st ? st.mm : 0;
      [hourSel, minSel].forEach(function (s) {
        s.addEventListener('change', function () {
          if (!st) { st = { y: now.getFullYear(), m: now.getMonth(), d: now.getDate(), hh: 9, mm: 0 }; }
          st.hh = +hourSel.value; st.mm = +minSel.value; write(); render();
        });
        enhanceSelect(s);
      });
    }
    var foot = h('div', 'dp-foot');
    var today = h('button', 'btn btn--line btn--sm', { type: 'button' }, 'Bugun');
    var clear = h('button', 'btn btn--line btn--sm', { type: 'button' }, 'Tozalash');
    foot.appendChild(today); foot.appendChild(clear);
    if (withTime) { var done = h('button', 'btn btn--dark btn--sm', { type: 'button' }, 'Tayyor'); done.addEventListener('click', function () { close(true); }); foot.appendChild(done); }
    panel.appendChild(foot);

    function fmt() {
      if (!st) return '';
      return pad(st.d) + '.' + pad(st.m + 1) + '.' + st.y + (withTime ? ' ' + pad(st.hh) + ':' + pad(st.mm) : '');
    }
    function label() { text.textContent = st ? fmt() : (withTime ? 'Sana va vaqtni tanlang' : 'Sanani tanlang'); text.classList.toggle('ph', !st); }
    function write() {
      inp.value = st ? st.y + '-' + pad(st.m + 1) + '-' + pad(st.d) + (withTime ? 'T' + pad(st.hh) + ':' + pad(st.mm) : '') : '';
      inp.dispatchEvent(new Event('change', { bubbles: true }));
      label();
    }
    function pick(y, m, d) {
      st = { y: y, m: m, d: d, hh: withTime ? +hourSel.value : 0, mm: withTime ? +minSel.value : 0 };
      view.y = y; view.m = m; write(); render();
      if (!withTime) close(true);
    }
    function render() {
      title.textContent = MONTHS[view.m] + ' ' + view.y;
      grid.textContent = '';
      WEEK.forEach(function (w) { grid.appendChild(h('div', 'dp-wd', null, w)); });
      var off = (new Date(view.y, view.m, 1).getDay() + 6) % 7;
      for (var i = 0; i < 42; i++) {
        var d = new Date(view.y, view.m, 1 - off + i);
        var b = h('button', 'dp-day', { type: 'button', 'aria-label': d.getDate() + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear() }, String(d.getDate()));
        if (d.getMonth() !== view.m) b.classList.add('out');
        if (d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()) b.classList.add('today');
        if (st && d.getFullYear() === st.y && d.getMonth() === st.m && d.getDate() === st.d) { b.classList.add('sel'); b.setAttribute('aria-pressed', 'true'); }
        (function (dd) { b.addEventListener('click', function () { pick(dd.getFullYear(), dd.getMonth(), dd.getDate()); }); })(d);
        grid.appendChild(b);
      }
    }
    today.addEventListener('click', function () { pick(now.getFullYear(), now.getMonth(), now.getDate()); if (withTime) close(true); });
    clear.addEventListener('click', function () { st = null; write(); render(); if (!withTime) close(true); });
    function open() {
      if (!panel.hidden) return;
      if (st) { view.y = st.y; view.m = st.m; }
      render(); panel.hidden = false; root.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true');
      place(root, panel); register(api);
      var sel = panel.querySelector('.dp-day.sel') || panel.querySelector('.dp-day.today') || panel.querySelector('.dp-day');
      if (sel) sel.focus({ preventScroll: true });
    }
    function close(refocus) {
      if (panel.hidden) return;
      panel.hidden = true; root.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false');
      unregister(api);
      if (refocus) btn.focus({ preventScroll: true });
    }
    btn.addEventListener('click', function () { panel.hidden ? open() : close(true); });
    label();
  }

  /* ---------- confirm dialog (replaces window.confirm) ---------- */
  function confirmDialog(message, onYes, opener) {
    var idn = 'cf' + (++uid);
    var yes = h('button', 'btn btn--dark', { type: 'button' }, 'Ha, davom etish');
    var no = h('button', 'btn btn--line', { type: 'button' }, 'Bekor qilish');
    var box = h('div', 'modal', { role: 'alertdialog', 'aria-modal': 'true', 'aria-labelledby': idn + 't', 'aria-describedby': idn + 'd' },
      h('h2', '', { id: idn + 't' }, 'Tasdiqlang'), h('p', 'muted', { id: idn + 'd' }, message), h('div', 'modal-actions', null, no, yes));
    var wrap = h('div', 'modal-scrim', null, box);
    function done(ok) {
      document.removeEventListener('keydown', key, true); wrap.remove();
      if (opener && opener.focus) opener.focus({ preventScroll: true });
      if (ok) onYes();
    }
    function key(e) {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); done(false); }
      else if (e.key === 'Tab') {
        var f = [no, yes], i = f.indexOf(document.activeElement);
        e.preventDefault(); f[(i + (e.shiftKey ? -1 : 1) + 2) % 2].focus();
      }
    }
    yes.addEventListener('click', function () { done(true); });
    no.addEventListener('click', function () { done(false); });
    wrap.addEventListener('pointerdown', function (e) { if (e.target === wrap) done(false); });
    document.addEventListener('keydown', key, true);
    document.body.appendChild(wrap);
    no.focus();
  }

  /* ---------- form validation messages (replaces native bubbles) ---------- */
  function message(el) {
    var v = el.validity;
    if (v.valueMissing) return "Bu maydonni to'ldiring";
    if (v.typeMismatch) return el.type === 'email' ? "To'g'ri email kiriting" : "To'g'ri havola kiriting (https://…)";
    if (v.tooShort) return 'Kamida ' + el.minLength + ' belgi kiriting';
    if (v.rangeUnderflow || v.rangeOverflow) return 'Qiymat ' + (el.min || '') + '–' + (el.max || '') + " oralig'ida bo'lsin";
    if (v.patternMismatch) return "Format noto'g'ri";
    return el.validationMessage || "Noto'g'ri qiymat";
  }
  function clearError(field) {
    if (!field) return;
    field.classList.remove('is-invalid');
    var m = field.querySelector('.field-err'); if (m) m.remove();
  }
  function showError(el) {
    var field = el.closest('.field') || el.parentNode;
    clearError(field);
    var p = h('p', 'field-err', { role: 'alert', id: 'err' + (++uid) }, message(el));
    field.classList.add('is-invalid'); field.appendChild(p);
    var ctl = document.getElementById(el.id.replace(/-native$/, '')) || el;
    ctl.setAttribute('aria-invalid', 'true'); ctl.setAttribute('aria-describedby', p.id);
    return ctl;
  }
  function enhanceForm(f) {
    f.noValidate = true;
    f.addEventListener('submit', function (e) {
      var first = null;
      Array.prototype.forEach.call(f.elements, function (el) {
        if (!el.willValidate || el.type === 'hidden' || el.disabled) return;
        if (!el.checkValidity()) { var c = showError(el); if (!first) first = c; }
      });
      if (first) {
        e.preventDefault(); e.stopImmediatePropagation();
        first.scrollIntoView({ block: 'center', behavior: 'smooth' }); first.focus({ preventScroll: true });
      }
    }, true);
    ['input', 'change'].forEach(function (t) {
      f.addEventListener(t, function (e) { clearError(e.target.closest && e.target.closest('.field')); }, true);
    });
    var msg = f.getAttribute('data-confirm');
    if (msg) {
      f.addEventListener('submit', function (e) {
        if (f.__confirmed) return;
        e.preventDefault();
        confirmDialog(msg, function () { f.__confirmed = true; f.requestSubmit ? f.requestSubmit() : f.submit(); }, document.activeElement);
      });
    }
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll('select'), enhanceSelect);
    Array.prototype.forEach.call(document.querySelectorAll('input[type=date], input[type=datetime-local]'), enhanceDate);
    Array.prototype.forEach.call(document.forms, enhanceForm);
    // Keep the browser's own autofill dropdown off the admin's plain text fields (credentials keep theirs).
    Array.prototype.forEach.call(document.querySelectorAll('input:not([type=hidden]):not([type=password]):not([type=email]):not([autocomplete]), textarea:not([autocomplete])'), function (el) { el.setAttribute('autocomplete', 'off'); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
