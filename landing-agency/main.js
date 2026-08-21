// NUVI AI Agency — renders the whole page from I18N (see i18n.js), wires
// up the language switch, nav, FAQ accordion, scroll reveals, and the
// lead form + analytics beacons.

// ── Anonymous funnel tracking ──
function _sessionId() {
  let id = sessionStorage.getItem("agency_session_id");
  if (!id) {
    id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`);
    sessionStorage.setItem("agency_session_id", id);
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
      navigator.sendBeacon("/api/agency/event", new Blob([body], { type: "application/json" }));
    } else {
      fetch("/api/agency/event", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true });
    }
  } catch (e) { /* analytics must never break the page */ }
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

// ── Language state ──
const SUPPORTED_LANGS = ["uz", "ru", "en"];
let currentLang = localStorage.getItem("agency_lang") || "uz";
if (!SUPPORTED_LANGS.includes(currentLang)) currentLang = "uz";

function t() {
  return I18N[currentLang];
}

// ── Static text-node rendering (data-i18n="a.b.c") ──
function applyStaticText() {
  const data = t();
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const path = el.getAttribute("data-i18n").split(".");
    let val = data;
    for (const key of path) val = val && val[key];
    if (typeof val === "string") el.textContent = val;
  });
  document.documentElement.lang = currentLang;
  document.getElementById("pageTitle").textContent = data.meta.title;
  document.getElementById("metaDescription").setAttribute("content", data.meta.desc);
}

// ── Dynamic section renderers ──
function renderHeroFlow() {
  const items = t().hero.flow;
  document.getElementById("heroFlow").innerHTML = items.map((it, i) => (
    `<span class="hero-flow-item">${esc(it)}</span>` + (i < items.length - 1 ? `<span class="hero-flow-arrow">→</span>` : "")
  )).join("");
}

function renderProblem() {
  document.getElementById("problemFragments").innerHTML = t().problem.fragments.map((f) => `<div class="fragment">${esc(f)}</div>`).join("");
}

function renderSystem() {
  const sys = t().system;
  document.getElementById("systemFlow").innerHTML = sys.flow.map((it, i) => (
    `<span class="system-flow-item">${esc(it)}</span>` + (i < sys.flow.length - 1 ? `<span class="system-flow-arrow">→</span>` : "")
  )).join("");
  document.getElementById("systemStages").innerHTML = sys.stages.map((s) => `
    <div class="stage-card reveal">
      <div class="stage-num">${esc(s.num)}</div>
      <div class="stage-title">${esc(s.title)}</div>
      <div class="stage-services">${s.services.map((sv) => `<span class="stage-service-chip">${esc(sv)}</span>`).join("")}</div>
      <p class="stage-result">${esc(s.result)}</p>
    </div>
  `).join("");
}

function renderPricing() {
  const p = t().pricing;
  document.getElementById("pricingGrid").innerHTML = p.tiers.map((tier) => `
    <div class="tier-card ${tier.badge ? "featured" : ""} reveal">
      ${tier.badge ? `<span class="tier-badge">${esc(tier.badge)}</span>` : ""}
      <span class="tier-name">${esc(tier.name)}</span>
      <div class="tier-price">${esc(tier.price)} <span>${esc(tier.period)}</span></div>
      <div class="tier-headline">${esc(tier.headline)}</div>
      <p class="tier-desc">${esc(tier.desc)}</p>
      <ul class="tier-features">${tier.features.map((f) => `<li><span class="dot">✓</span><span>${esc(f)}</span></li>`).join("")}</ul>
      <button class="btn btn-primary tier-cta" data-track="${esc(tier.key)}_selected">${esc(tier.cta)}</button>
    </div>
  `).join("");

  document.getElementById("customModules").innerHTML = p.custom.modules.map((m) => `<span class="custom-module-chip">${esc(m)}</span>`).join("");
}

function renderBonus() {
  const b = t().bonus;
  document.getElementById("bonusCapabilities").innerHTML = b.hero.capabilities.map((c) => `<li><span class="dot">✓</span><span>${esc(c)}</span></li>`).join("");
  document.getElementById("bonusFlow").innerHTML = b.hero.flow.map((f, i) => (
    `<span class="bonus-flow-item">${esc(f)}</span>` + (i < b.hero.flow.length - 1 ? `<span class="bonus-flow-arrow">→</span>` : "")
  )).join("");
  document.getElementById("bonusOthers").innerHTML = b.others.map((o) => `
    <div class="bonus-other-card reveal">
      <div class="bonus-other-title">${esc(o.title)}</div>
      <p class="bonus-other-desc">${esc(o.desc)}</p>
    </div>
  `).join("");
}

function renderStandalone() {
  document.getElementById("standaloneGrid").innerHTML = t().standalone.services.map((s) => `
    <div class="service-card reveal">
      <div class="service-card-title">${esc(s.title)}</div>
      <ul class="service-list">${s.list.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>
      <div class="service-price">${esc(s.price)}</div>
      <button class="btn btn-outline btn-block" data-track="${esc(s.key)}_selected">${esc(s.cta)}</button>
    </div>
  `).join("");
}

function renderAiProduction() {
  const ai = t().aiProduction;
  document.getElementById("aiCategories").innerHTML = ai.categories.map((c) => `<div class="ai-category-chip">${esc(c)}</div>`).join("");
  document.getElementById("aiPricingRange").textContent = ai.pricingRange;
  document.getElementById("aiPricingFactors").innerHTML = ai.factors.map((f) => `<span class="ai-factor-chip">${esc(f)}</span>`).join("");
  document.getElementById("aiTierCompare").innerHTML = ai.tiers.map((tier) => `
    <div class="ai-tier-item">
      <div class="tier-mini-name">${esc(tier.name)}</div>
      <div class="tier-mini-desc">${esc(tier.desc)}</div>
    </div>
  `).join("");
}

function renderAutomation() {
  const a = t().automation;
  document.getElementById("automationExamples").innerHTML = a.examples.map((e) => `<div class="automation-chip">${esc(e)}</div>`).join("");
  document.getElementById("automationWorkflow").innerHTML = a.workflow.map((w, i) => (
    `<div class="workflow-step">${esc(w)}</div>` + (i < a.workflow.length - 1 ? `<div class="workflow-arrow-v">↓</div>` : "")
  )).join("");
}

function renderHow() {
  document.getElementById("howSteps").innerHTML = t().how.steps.map((s) => `
    <div class="reveal">
      <div class="how-step-num">${esc(s.num)}</div>
      <div class="how-step-title">${esc(s.title)}</div>
      <p class="how-step-desc">${esc(s.desc)}</p>
    </div>
  `).join("");
}

function renderKpi() {
  document.getElementById("kpiTags").innerHTML = t().kpi.list.map((k) => `<span class="kpi-tag">${esc(k)}</span>`).join("");
}

function renderResponsibility() {
  const r = t().responsibility;
  document.getElementById("responsibilityNuvi").innerHTML = r.nuviList.map((i) => `<li><span class="dot">✓</span><span>${esc(i)}</span></li>`).join("");
  document.getElementById("responsibilityClient").innerHTML = r.clientList.map((i) => `<li><span class="dot">✓</span><span>${esc(i)}</span></li>`).join("");
}

function renderCases() {
  document.getElementById("casesGrid").innerHTML = t().cases.placeholders.map((c) => `
    <div class="case-card reveal">
      <span class="case-tag">${esc(c.tag)}</span>
      ${c.fields.map(([k, v]) => `<div class="case-row"><span>${esc(k)}</span><span>${esc(v)}</span></div>`).join("")}
    </div>
  `).join("");
}

function renderWhy() {
  document.getElementById("whyPillars").innerHTML = t().why.pillars.map((p) => `
    <div class="pillar-card reveal"><div class="pillar-title">${esc(p)}</div></div>
  `).join("");
}

function renderFaq() {
  document.getElementById("faqList").innerHTML = t().faq.items.map((item) => `
    <div class="faq-item" data-toggle="faq">
      <div class="faq-q"><span>${esc(item.q)}</span><span class="faq-toggle">+</span></div>
      <div class="faq-a">${esc(item.a)}</div>
    </div>
  `).join("");
  wireFaq();
}

function renderFormOptions() {
  const select = document.getElementById("fService");
  const current = select.value;
  select.innerHTML = t().form.serviceOptions.map((o, i) => `<option value="${i}">${esc(o)}</option>`).join("");
  if (current) select.value = current;
}

function wireFaq() {
  document.querySelectorAll('[data-toggle="faq"]').forEach((el) => {
    el.addEventListener("click", () => el.closest(".faq-item").classList.toggle("open"));
  });
}

function wireTrackedCtas() {
  document.querySelectorAll("[data-track]").forEach((el) => {
    el.addEventListener("click", () => trackEvent(el.getAttribute("data-track")));
  });
  // Tier/service buttons also jump to the lead form for a quick path to conversion.
  document.querySelectorAll(".tier-cta, .standalone-grid .btn, .ai-pricing .btn, .automation-section .btn, .custom-card .btn").forEach((el) => {
    el.addEventListener("click", () => document.getElementById("lead").scrollIntoView({ behavior: "smooth" }));
  });
}

function renderAll() {
  applyStaticText();
  renderHeroFlow();
  renderProblem();
  renderSystem();
  renderPricing();
  renderBonus();
  renderStandalone();
  renderAiProduction();
  renderAutomation();
  renderHow();
  renderKpi();
  renderResponsibility();
  renderCases();
  renderWhy();
  renderFaq();
  renderFormOptions();
  wireTrackedCtas();
  observeReveals();
}

// ── Language switch ──
function setLang(lang) {
  if (!SUPPORTED_LANGS.includes(lang)) return;
  currentLang = lang;
  localStorage.setItem("agency_lang", lang);
  document.querySelectorAll(".lang-btn").forEach((b) => b.classList.toggle("active", b.getAttribute("data-lang") === lang));
  renderAll();
  trackEvent(`language_changed:${lang}`);
}

document.querySelectorAll(".lang-btn").forEach((btn) => {
  btn.addEventListener("click", () => setLang(btn.getAttribute("data-lang")));
});

// ── Nav: sticky burger + smooth-scroll close ──
const navEl = document.getElementById("nav");
document.getElementById("navBurger").addEventListener("click", () => navEl.classList.toggle("mobile-open"));
document.querySelectorAll(".nav-mobile a").forEach((a) => a.addEventListener("click", () => navEl.classList.remove("mobile-open")));

// ── Scroll reveal ──
function observeReveals() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in-view");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  document.querySelectorAll(".reveal:not(.in-view)").forEach((el) => observer.observe(el));
}

// ── Section-view analytics (fires once each) ──
(function trackSectionViews() {
  const seen = new Set();
  const sectionEvents = { pricing: "pricing_viewed", "ai-production": "ai_production_viewed", lead: "lead_form_started" };
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const ev = sectionEvents[entry.target.id];
      if (ev && !seen.has(ev)) {
        seen.add(ev);
        trackEvent(ev);
      }
    });
  }, { threshold: 0.3 });
  Object.keys(sectionEvents).forEach((id) => {
    const el = document.getElementById(id);
    if (el) observer.observe(el);
  });
})();

// ── Lead form ──
const leadForm = document.getElementById("leadForm");
const leadSubmitBtn = document.getElementById("leadSubmitBtn");
const leadError = document.getElementById("leadError");

leadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("fName").value.trim();
  const phone = document.getElementById("fPhone").value.trim();
  const company = document.getElementById("fCompany").value.trim();
  const serviceIdx = document.getElementById("fService").value;
  const serviceLabel = t().form.serviceOptions[serviceIdx] || "";
  const message = document.getElementById("fMessage").value.trim();

  if (name.length < 2 || phone.replace(/\D/g, "").length < 9) {
    leadError.style.display = "block";
    leadError.textContent = currentLang === "ru" ? "Пожалуйста, укажите корректное имя и телефон." : currentLang === "en" ? "Please enter a valid name and phone number." : "Iltimos, ism va telefon raqamingizni to'g'ri kiriting.";
    return;
  }
  leadError.style.display = "none";
  leadSubmitBtn.classList.add("loading");
  leadSubmitBtn.disabled = true;

  const params = new URLSearchParams(window.location.search);
  try {
    const res = await fetch("/api/agency/lead", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name, phone, company, service: serviceLabel, message,
        lang: currentLang,
        session_id: _sessionId(),
        utm_source: params.get("utm_source") || "",
        utm_campaign: params.get("utm_campaign") || "",
      }),
    });
    if (!res.ok) throw new Error("bad response");
    trackEvent("lead_form_submitted");
    leadForm.style.display = "none";
    document.getElementById("leadSuccess").classList.add("show");
  } catch (err) {
    leadError.style.display = "block";
    leadError.textContent = currentLang === "ru" ? "Произошла ошибка. Попробуйте ещё раз." : currentLang === "en" ? "Something went wrong. Please try again." : "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.";
  } finally {
    leadSubmitBtn.classList.remove("loading");
    leadSubmitBtn.disabled = false;
  }
});

// ── Init ──
document.querySelectorAll(".lang-btn").forEach((b) => b.classList.toggle("active", b.getAttribute("data-lang") === currentLang));
renderAll();
trackEvent("page_view");
