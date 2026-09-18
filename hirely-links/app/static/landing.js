/* Counts an ad impression only when >=50% of it has been visible, in a visible tab, for 1 continuous second. */
(function () {
  var el = document.querySelector('[data-tk]');
  if (!el || !('IntersectionObserver' in window)) return;
  var token = el.getAttribute('data-tk'), sent = false, timer = null, since = 0, ratioOk = false;
  function send(ms) {
    if (sent) return;
    sent = true;
    var body = JSON.stringify({ t: token, ms: Math.max(1000, Math.round(ms)) });
    try {
      if (navigator.sendBeacon && navigator.sendBeacon('/t/i', new Blob([body], { type: 'text/plain' }))) return;
    } catch (e) {}
    try { fetch('/t/i', { method: 'POST', body: body, keepalive: true, headers: { 'Content-Type': 'text/plain' } }); } catch (e) {}
  }
  function check() {
    var on = ratioOk && document.visibilityState === 'visible';
    if (on && !timer && !sent) {
      since = Date.now();
      timer = setTimeout(function () { timer = null; send(Date.now() - since); }, 1000);
    } else if (!on && timer) {
      clearTimeout(timer); timer = null;
    }
  }
  new IntersectionObserver(function (entries) {
    ratioOk = entries[entries.length - 1].intersectionRatio >= 0.5;
    check();
  }, { threshold: [0, 0.5, 1] }).observe(el);
  document.addEventListener('visibilitychange', check);
})();
