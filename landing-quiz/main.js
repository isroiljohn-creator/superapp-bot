// AI Bilim Testi — quiz flow. Options order/text must match server QUESTIONS in
// api/routers/quiz.py exactly (server re-scores, this is just the UI).

// ── Anonymous funnel tracking ──
function _sessionId() {
  let id = sessionStorage.getItem("quiz_session_id");
  if (!id) {
    id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`);
    sessionStorage.setItem("quiz_session_id", id);
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
      navigator.sendBeacon("/api/quiz/event", new Blob([body], { type: "application/json" }));
    } else {
      fetch("/api/quiz/event", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true });
    }
  } catch (e) { /* analytics must never break the quiz */ }
}

trackEvent("page_view");

const PROFESSIONS = [
  { emoji: "💼", value: "biznes_egasi", label: "Biznes egasi" },
  { emoji: "🎓", value: "oqituvchi", label: "O'qituvchi" },
  { emoji: "📚", value: "oquvchi", label: "O'quvchi" },
  { emoji: "🛠", value: "mutaxassis", label: "Mutaxassis" },
  { emoji: "🩺", value: "shifokor", label: "Shifokor" },
  { emoji: "🎨", value: "ijodkor", label: "Ijodkor" },
];

// Questions are fetched per-profession from the server (20-question bank per
// profession, 6 served at random each visit) — see api/routers/quiz.py.
const state = { profession: null, current: 0, questions: [], answers: [], name: "", phone: "" };

const stages = {
  intro: document.getElementById("stage-intro"),
  profession: document.getElementById("stage-profession"),
  quiz: document.getElementById("stage-quiz"),
  contact: document.getElementById("stage-contact"),
  result: document.getElementById("stage-result"),
};
const progressFill = document.getElementById("progressFill");

function showStage(name) {
  Object.values(stages).forEach((el) => el.classList.remove("active"));
  stages[name].classList.add("active");
}

// ── Step 0: intro ──
document.getElementById("startBtn").addEventListener("click", () => {
  renderProfessions();
  showStage("profession");
  progressFill.style.width = "10%";
});

// ── Step 1: profession ──
function renderProfessions() {
  const el = document.getElementById("professionOptions");
  el.innerHTML = "";
  PROFESSIONS.forEach((p) => {
    const btn = document.createElement("button");
    btn.className = "option";
    btn.innerHTML = `<span class="option-emoji">${p.emoji}</span><span>${p.label}</span>`;
    btn.addEventListener("click", async () => {
      state.profession = p.value;
      document.querySelectorAll("#professionOptions .option").forEach((o) => o.classList.remove("selected"));
      btn.classList.add("selected");
      trackEvent("profession_selected");

      try {
        const res = await fetch(`/api/quiz/questions?profession=${encodeURIComponent(p.value)}`);
        if (!res.ok) throw new Error("failed to load questions");
        const data = await res.json();
        state.questions = data.questions;
        state.current = 0;
        state.answers = [];
        trackEvent("quiz_started");
        showStage("quiz");
        renderQuestion();
      } catch (e) {
        alert("Savollarni yuklashda xatolik. Iltimos, sahifani yangilab qayta urinib ko'ring.");
      }
    });
    el.appendChild(btn);
  });
}

// ── Step 2: quiz ──
function renderQuestion() {
  const q = state.questions[state.current];
  document.getElementById("qCounter").textContent = `Savol ${state.current + 1} / ${state.questions.length}`;
  document.getElementById("qText").textContent = q.text;
  progressFill.style.width = `${10 + (state.current / state.questions.length) * 70}%`;

  const optsEl = document.getElementById("qOptions");
  optsEl.innerHTML = "";
  q.options.forEach((opt, idx) => {
    const btn = document.createElement("button");
    btn.className = "option";
    btn.innerHTML = `<span class="option-letter">${String.fromCharCode(65 + idx)}</span><span>${opt}</span>`;
    btn.addEventListener("click", () => selectOption(idx));
    optsEl.appendChild(btn);
  });
}

function selectOption(idx) {
  const q = state.questions[state.current];
  state.answers[state.current] = { question_index: q.question_index, selected: idx };
  document.querySelectorAll("#qOptions .option").forEach((el, i) => el.classList.toggle("selected", i === idx));

  setTimeout(() => {
    if (state.current < state.questions.length - 1) {
      state.current += 1;
      renderQuestion();
    } else {
      progressFill.style.width = "85%";
      trackEvent("quiz_completed");
      trackEvent("contact_view");
      showStage("contact");
    }
  }, 280);
}

// ── Step 3: contact form ──
const nameInput = document.getElementById("nameInput");
const phoneInput = document.getElementById("phoneInput");
const submitContactBtn = document.getElementById("submitContactBtn");

submitContactBtn.addEventListener("click", async () => {
  const name = nameInput.value.trim();
  const phone = phoneInput.value.trim();
  const digits = phone.replace(/\D/g, "");

  if (name.length < 2) {
    nameInput.focus();
    return;
  }
  if (digits.length < 9) {
    phoneInput.focus();
    return;
  }

  state.name = name;
  state.phone = phone;
  submitContactBtn.classList.add("loading");
  submitContactBtn.disabled = true;
  await finishQuiz();
});

// ── Step 4: submit + result ──
async function finishQuiz() {
  try {
    const params = new URLSearchParams(window.location.search);
    const res = await fetch("/api/quiz/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profession: state.profession,
        answers: state.answers,
        name: state.name,
        phone: state.phone,
        session_id: _sessionId(),
        utm_source: params.get("utm_source") || "",
        utm_campaign: params.get("utm_campaign") || "",
      }),
    });
    if (!res.ok) throw new Error("submit failed");
    const data = await res.json();
    progressFill.style.width = "100%";
    showStage("result");
    showResult(data);
  } catch (e) {
    submitContactBtn.classList.remove("loading");
    submitContactBtn.disabled = false;
    alert("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.");
  }
}

const LEVEL_META = {
  boshlangich: { emoji: "🌱", title: "Boshlang'ich daraja", desc: "AI olamiga hali endi qadam qo'yyapsiz — biz siz uchun asosdan boshlaydigan bepul darsni tayyorladik." },
  orta: { emoji: "⚡", title: "O'rta daraja", desc: "Asosiy tushunchalarni bilasiz! Endi amaliy ko'nikmalarni chuqurlashtiradigan bepul darsni ko'ring." },
  yuqori: { emoji: "🚀", title: "Yuqori daraja", desc: "Siz allaqachon AI bilan yaxshi tanishsiz — ilg'or, professional darajadagi bepul darsni taklif qilamiz." },
};

function showResult(data) {
  const meta = LEVEL_META[data.level] || LEVEL_META.boshlangich;
  document.getElementById("resultEmoji").textContent = meta.emoji;
  document.getElementById("resultLevel").textContent = meta.title;
  document.getElementById("resultDesc").textContent = meta.desc;
  document.getElementById("resultScore").textContent = `${data.correct_count} / ${state.questions.length} to'g'ri javob`;

  const continueBtn = document.getElementById("continueBtn");
  continueBtn.addEventListener("click", () => {
    window.location.href = data.redirect_url;
  });
}
