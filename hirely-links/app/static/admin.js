(function () {
  // range bar: auto-submit + show custom dates
  document.querySelectorAll('form[data-range]').forEach(function (f) {
    var sel = f.querySelector('[name=r]'), custom = f.querySelectorAll('[data-custom]');
    function sync() { custom.forEach(function (c) { c.hidden = sel.value !== 'custom'; }); }
    sel.addEventListener('change', function () { sync(); if (sel.value !== 'custom') f.submit(); });
    f.querySelectorAll('select:not([name=r])').forEach(function (s) { s.addEventListener('change', function () { f.submit(); }); });
    sync();
  });
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var t = b.getAttribute('data-copy');
      (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(function () { b.textContent = 'Nusxalandi'; }, function () {
        var i = document.createElement('input'); i.value = t; document.body.appendChild(i); i.select(); try { document.execCommand('copy'); b.textContent = 'Nusxalandi'; } catch (e) {} i.remove();
      });
    });
  });
  document.querySelectorAll('[data-confirm]').forEach(function (f) {
    f.addEventListener('submit', function (e) { if (!confirm(f.getAttribute('data-confirm'))) e.preventDefault(); });
  });

  // time-series chart (plain SVG, no library)
  var NS = 'http://www.w3.org/2000/svg';
  var SERIES = [
    { k: 'page_views', name: "Sahifa ko'rishlar", color: '#163A26', dash: '' },
    { k: 'unique_visitors', name: 'Noyob tashrif', color: '#A9B6A7', dash: '6 5' },
    { k: 'contact_clicks', name: 'Aloqa kliklari', color: '#8CF56E', dash: '' }
  ];
  function el(n, a) { var e = document.createElementNS(NS, n); for (var k in a) e.setAttribute(k, a[k]); return e; }
  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function label(b, gran) {
    var d = new Date(b);
    var dd = ('0' + d.getDate()).slice(-2) + '.' + ('0' + (d.getMonth() + 1)).slice(-2);
    if (gran === 'hour') return ('0' + d.getHours()).slice(-2) + ':00';
    if (gran === 'month') return ('0' + (d.getMonth() + 1)).slice(-2) + '.' + d.getFullYear();
    return dd;
  }
  document.querySelectorAll('[data-chart]').forEach(function (box) {
    fetch(box.getAttribute('data-chart'), { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (data) {
      var pts = data.points || [];
      if (!pts.length || !pts.some(function (p) { return SERIES.some(function (s) { return p[s.k] > 0; }); })) {
        box.innerHTML = '<div class="empty">Tanlangan davr uchun ma\'lumot yo\'q</div>'; return;
      }
      var W = 800, H = 280, L = 44, R = 12, T = 12, B = 30;
      var max = Math.max.apply(null, pts.map(function (p) { return Math.max(p.page_views, p.unique_visitors, p.contact_clicks); })) || 1;
      var step = Math.pow(10, Math.floor(Math.log10(max))); max = Math.ceil(max / step) * step;
      var x = function (i) { return L + (pts.length === 1 ? (W - L - R) / 2 : i * (W - L - R) / (pts.length - 1)); };
      var y = function (v) { return T + (H - T - B) * (1 - v / max); };
      var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Vaqt bo\'yicha grafik' });
      for (var g = 0; g <= 4; g++) {
        var gv = max * g / 4, gy = y(gv);
        svg.appendChild(el('line', { x1: L, x2: W - R, y1: gy, y2: gy, stroke: '#DCE6D9' }));
        var t = el('text', { x: L - 8, y: gy + 4, 'text-anchor': 'end', 'font-size': 11, fill: '#5F6F5C', 'font-family': 'Manrope' }); t.textContent = fmt(Math.round(gv)); svg.appendChild(t);
      }
      var every = Math.ceil(pts.length / 8);
      pts.forEach(function (p, i) {
        if (i % every) return;
        var t = el('text', { x: x(i), y: H - 8, 'text-anchor': 'middle', 'font-size': 11, fill: '#5F6F5C', 'font-family': 'Manrope' }); t.textContent = label(p.b, data.gran); svg.appendChild(t);
      });
      SERIES.forEach(function (s) {
        var d = pts.map(function (p, i) { return (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(p[s.k]).toFixed(1); }).join('');
        var a = { d: d, fill: 'none', stroke: s.color, 'stroke-width': s.k === 'contact_clicks' ? 4 : 3, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' };
        if (s.dash) a['stroke-dasharray'] = s.dash;
        svg.appendChild(el('path', a));
        if (pts.length === 1) svg.appendChild(el('circle', { cx: x(0), cy: y(pts[0][s.k]), r: 5, fill: s.color }));
      });
      var cursor = el('line', { y1: T, y2: H - B, stroke: '#163A26', 'stroke-width': 1, opacity: 0 }); svg.appendChild(cursor);
      box.innerHTML = ''; box.appendChild(svg);
      var tip = document.createElement('div'); tip.className = 'tip'; tip.hidden = true; box.appendChild(tip);
      function move(ev) {
        var r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) * W / r.width;
        var i = Math.max(0, Math.min(pts.length - 1, Math.round((px - L) / ((W - L - R) / Math.max(pts.length - 1, 1)))));
        var p = pts[i]; cursor.setAttribute('x1', x(i)); cursor.setAttribute('x2', x(i)); cursor.setAttribute('opacity', 1);
        tip.innerHTML = '<b>' + label(p.b, data.gran) + '</b><br>' + SERIES.map(function (s) { return s.name + ': ' + fmt(p[s.k]); }).join('<br>');
        tip.hidden = false;
        var left = (ev.clientX - box.getBoundingClientRect().left) + 14;
        tip.style.left = Math.min(left, box.clientWidth - tip.offsetWidth - 4) + 'px'; tip.style.top = '8px';
      }
      svg.addEventListener('pointermove', move);
      svg.addEventListener('pointerdown', move);
      svg.addEventListener('pointerleave', function () { tip.hidden = true; cursor.setAttribute('opacity', 0); });
      var lg = document.createElement('div'); lg.className = 'legend';
      SERIES.forEach(function (s) {
        var sp = document.createElement('span'), i = document.createElement('i');
        i.style.borderTopColor = s.color; if (s.dash) i.style.borderTopStyle = 'dashed';  // CSSOM, allowed by the CSP
        sp.appendChild(i); sp.appendChild(document.createTextNode(s.name)); lg.appendChild(sp);
      });
      box.appendChild(lg);
    }).catch(function () { box.innerHTML = '<div class="empty">Grafikni yuklab bo\'lmadi</div>'; });
  });
})();
