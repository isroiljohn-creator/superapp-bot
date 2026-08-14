// NUVI AI 2.0 sales page — content is fully server-driven (see
// api/routers/course_landing.py / CourseLandingContent) so every text and
// image block can be edited from the admin panel without a deploy.

// ── Anonymous funnel tracking ──
function _sessionId() {
  let id = sessionStorage.getItem("course_session_id");
  if (!id) {
    id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`);
    sessionStorage.setItem("course_session_id", id);
  }
  return id;
}

function trackEvent(eventType) {
  const params = new URLSearchParams(window.location.search);
  const body = JSON.stringify({
    session_id: _sessionId(),
    event_type: eventType,
    utm_source: params.get("utm_source") || "",
    utm_campaign: params.get("utm_campaign") || "",
  });
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon("/api/course-landing/event", new Blob([body], { type: "application/json" }));
    } else {
      fetch("/api/course-landing/event", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true });
    }
  } catch (e) { /* analytics must never break the page */ }
}

trackEvent("page_view");

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

function renderModuleCard(m) {
  const lessons = (m.lessons || []).map((l, i) => `
    <div class="module-lesson"><span class="n">${i + 1}</span><span>${esc(l)}</span></div>
  `).join("");
  const image = m.image ? `<img class="module-image show" src="${esc(m.image)}" alt="${esc(m.title)}">` : "";
  return `
    <div class="module-card">
      ${image}
      <div class="module-head" data-toggle="module">
        <span class="module-badge">${esc(m.badge)}</span>
        <span class="module-title">${esc(m.title)}</span>
        <span class="module-toggle">+</span>
      </div>
      <div class="module-result">${esc(m.result)}</div>
      <div class="module-lessons">${lessons}</div>
    </div>
  `;
}

function renderTierCard(t) {
  const features = (t.features || []).map((f) => `<li><span class="dot">✓</span><span>${esc(f)}</span></li>`).join("");
  return `
    <div class="tier-card ${t.highlight ? "highlight" : ""}">
      <span class="tier-name">${esc(t.name)}</span>
      <div class="tier-subtitle">${esc(t.subtitle)}</div>
      <div class="tier-price">${esc(t.price)} <span class="currency">so'm</span></div>
      <ul class="tier-features">${features}</ul>
      <button class="btn btn-primary tier-cta" data-tariff="${esc(t.key)}">Tanlash</button>
    </div>
  `;
}

function render(content) {
  const hero = content.hero || {};
  document.getElementById("heroBadge").textContent = hero.badge || "";
  document.getElementById("heroTitle").textContent = hero.title || "";
  document.getElementById("heroSubtitle").textContent = hero.subtitle || "";
  document.querySelectorAll("#topCta, #heroCta").forEach((el) => { el.textContent = hero.cta || "Ariza qoldirish"; });
  document.getElementById("heroMeta").innerHTML = (hero.meta || []).map((m) => `<span>${esc(m)}</span>`).join("");
  const heroImg = document.getElementById("heroImage");
  if (hero.image) { heroImg.src = hero.image; heroImg.classList.add("show"); } else { heroImg.classList.remove("show"); }

  const audience = content.audience || {};
  document.getElementById("audienceEyebrow").textContent = audience.subtitle || "Kimlar uchun";
  document.getElementById("audienceTitle").textContent = audience.title || "";
  document.getElementById("audienceGrid").innerHTML = (audience.items || []).map((it) => `
    <div class="audience-item"><span class="check">✓</span><span>${esc(it)}</span></div>
  `).join("");

  document.getElementById("modulesList").innerHTML = (content.modules || []).map(renderModuleCard).join("");
  document.getElementById("bonusTitle").textContent = content.bonus_title || "";
  document.getElementById("bonusList").innerHTML = (content.bonus_modules || []).map(renderModuleCard).join("");

  const outcomes = content.outcomes || {};
  document.getElementById("outcomesTitle").textContent = outcomes.title || "";
  document.getElementById("outcomesGrid").innerHTML = (outcomes.items || []).map((it, i) => `
    <div class="outcome-item"><div class="outcome-num">${String(i + 1).padStart(2, "0")}</div><div class="outcome-text">${esc(it)}</div></div>
  `).join("");

  const extras = content.extras || {};
  document.getElementById("extrasTitle").textContent = extras.title || "";
  document.getElementById("extrasGrid").innerHTML = (extras.items || []).map((it) => `
    <div class="extra-item"><div class="extra-title">${esc(it.title)}</div><div class="extra-desc">${esc(it.desc)}</div></div>
  `).join("");
  document.getElementById("extrasFooter").textContent = extras.footer || "";

  const pricing = content.pricing || {};
  document.getElementById("pricingTitle").textContent = pricing.title || "";
  document.getElementById("pricingGrid").innerHTML = (pricing.tiers || []).map(renderTierCard).join("");

  document.getElementById("faqList").innerHTML = (content.faq || []).map((f) => `
    <div class="faq-item" data-toggle="faq">
      <div class="faq-q"><span>${esc(f.q)}</span><span class="faq-toggle">+</span></div>
      <div class="faq-a">${esc(f.a)}</div>
    </div>
  `).join("");

  const leadForm = content.lead_form || {};
  document.getElementById("leadTitle").textContent = leadForm.title || "Ariza qoldiring";
  document.getElementById("leadSubtitle").textContent = leadForm.subtitle || "";
  document.getElementById("leadSuccessText").textContent = leadForm.success || "Rahmat! Arizangiz qabul qilindi.";

  document.getElementById("footerText").textContent = (content.footer || {}).text || "";

  wireInteractions();
}

function wireInteractions() {
  document.querySelectorAll('[data-toggle="module"]').forEach((el) => {
    el.addEventListener("click", () => el.closest(".module-card").classList.toggle("open"));
  });
  document.querySelectorAll('[data-toggle="faq"]').forEach((el) => {
    el.addEventListener("click", () => el.closest(".faq-item").classList.toggle("open"));
  });
  document.querySelectorAll(".tier-cta").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tariff = btn.getAttribute("data-tariff");
      trackEvent(`cta_click:${tariff}`);
      const select = document.getElementById("tariffSelect");
      if (select) select.value = tariff;
      document.getElementById("ariza").scrollIntoView({ behavior: "smooth" });
    });
  });
  document.querySelectorAll("#topCta, #heroCta").forEach((el) => {
    el.addEventListener("click", () => trackEvent("cta_click:hero"));
  });

  // Section view tracking (fires once each)
  const seen = new Set();
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const id = entry.target.id;
      const eventMap = { "modules-section": "modules_view", "pricing-section": "pricing_view", "ariza": "lead_form_view" };
      const ev = eventMap[id];
      if (ev && !seen.has(ev)) {
        seen.add(ev);
        trackEvent(ev);
      }
    });
  }, { threshold: 0.3 });
  ["modules-section", "pricing-section", "ariza"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) observer.observe(el);
  });
}

async function init() {
  try {
    const res = await fetch("/api/course-landing/content");
    const content = await res.json();
    render(content);
  } catch (e) {
    console.error("Failed to load content", e);
  }
}

init();

// ── Lead form submit ──
const leadForm = document.getElementById("leadForm");
const submitBtn = document.getElementById("submitBtn");
const leadError = document.getElementById("leadError");

leadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("nameInput").value.trim();
  const phone = document.getElementById("phoneInput").value.trim();
  const tariff = document.getElementById("tariffSelect").value || null;

  if (name.length < 2 || phone.replace(/\D/g, "").length < 9) {
    leadError.style.display = "block";
    leadError.textContent = "Iltimos, ism va telefon raqamingizni to'g'ri kiriting.";
    return;
  }
  leadError.style.display = "none";
  submitBtn.classList.add("loading");
  submitBtn.disabled = true;

  const params = new URLSearchParams(window.location.search);
  try {
    const res = await fetch("/api/course-landing/lead", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name, phone, tariff,
        session_id: _sessionId(),
        utm_source: params.get("utm_source") || "",
        utm_campaign: params.get("utm_campaign") || "",
      }),
    });
    if (!res.ok) throw new Error("bad response");
    leadForm.style.display = "none";
    document.getElementById("leadSuccess").classList.add("show");
  } catch (e) {
    leadError.style.display = "block";
    leadError.textContent = "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.";
  } finally {
    submitBtn.classList.remove("loading");
    submitBtn.disabled = false;
  }
});
