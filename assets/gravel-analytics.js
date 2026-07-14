(function () {
  "use strict";

  const config = window.GRAVEL_ANALYTICS || {};
  const endpoint = String(config.endpoint || "").replace(/\/$/, "");
  const CONSENT_KEY = "gravel-analytics-consent-v" + (config.consentVersion || "1");
  const VISITOR_KEY = "gravel-anonymous-visitor-v1";
  const MAX_TEXT = 120;
  let startedAt = Date.now();
  let maxScroll = 0;

  function randomId() {
    if (crypto && crypto.randomUUID) return crypto.randomUUID();
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
  }

  function consent() {
    try { return localStorage.getItem(CONSENT_KEY); } catch (_) { return null; }
  }

  function visitorId() {
    try {
      const current = JSON.parse(localStorage.getItem(VISITOR_KEY) || "null");
      const month = 30 * 24 * 60 * 60 * 1000;
      if (current && current.id && Date.now() - current.created < month) return current.id;
      const next = { id: randomId(), created: Date.now() };
      localStorage.setItem(VISITOR_KEY, JSON.stringify(next));
      return next.id;
    } catch (_) { return randomId(); }
  }

  function sessionId() {
    try {
      let id = sessionStorage.getItem("gravel-session-v1");
      if (!id) { id = randomId(); sessionStorage.setItem("gravel-session-v1", id); }
      return id;
    } catch (_) { return randomId(); }
  }

  function clean(value) {
    return String(value || "").replace(/[\r\n\t]+/g, " ").replace(/\s+/g, " ").trim().slice(0, MAX_TEXT);
  }

  function safePath(value) {
    try { return new URL(value, location.origin).pathname.slice(0, 240); }
    catch (_) { return location.pathname.slice(0, 240); }
  }

  function scrub(value) {
    if (typeof value === "number" || typeof value === "boolean") return value;
    return clean(value)
      .replace(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g, "[email]")
      .replace(/(?:\+?98|0)?9\d{9}/g, "[phone]")
      .replace(/(?:sk-|api[_-]?key\s*[:=])\S+/gi, "[secret]");
  }

  function safeProperties(properties) {
    const result = {};
    Object.entries(properties || {}).slice(0, 12).forEach(function (entry) {
      result[clean(entry[0]).slice(0, 40)] = scrub(entry[1]);
    });
    return result;
  }

  function send(name, properties) {
    if (!endpoint || consent() !== "yes") return false;
    const payload = {
      version: 1,
      event: clean(name),
      visitorId: visitorId(),
      sessionId: sessionId(),
      occurredAt: new Date().toISOString(),
      path: safePath(location.href),
      referrerHost: document.referrer ? new URL(document.referrer).hostname.slice(0, 120) : "",
      properties: safeProperties(properties)
    };
    const body = JSON.stringify(payload);
    try {
      if (navigator.sendBeacon) return navigator.sendBeacon(endpoint + "/v1/events", new Blob([body], { type: "application/json" }));
      fetch(endpoint + "/v1/events", { method: "POST", headers: { "content-type": "application/json" }, body, keepalive: true, credentials: "omit" }).catch(function () {});
      return true;
    } catch (_) { return false; }
  }

  function showConsent() {
    if (!endpoint || consent()) return;
    if (!document.getElementById("gravel-consent-style")) {
      const style = document.createElement("style");
      style.id = "gravel-consent-style";
      style.textContent = ".gravel-consent{position:fixed;z-index:1000;inset:auto 1rem 1rem;max-width:720px;margin:auto;background:#fff;color:#17313a;border:1px solid #c9d9dc;border-radius:18px;box-shadow:0 18px 50px #00192338;padding:16px 18px;display:flex;align-items:center;justify-content:space-between;gap:18px;font-family:Vazirmatn,Tahoma,sans-serif}.gravel-consent p{margin:0;line-height:1.8;font-size:14px}.gravel-consent a{color:#087d86}.gravel-consent div{display:flex;gap:8px;flex:none}.gravel-consent button{font:inherit;border:1px solid #087d86;border-radius:10px;padding:8px 14px;cursor:pointer;background:#087d86;color:#fff}.gravel-consent button+button{background:#fff;color:#31545d;border-color:#b6c8cc}@media(max-width:600px){.gravel-consent{align-items:stretch;flex-direction:column}.gravel-consent div{width:100%}.gravel-consent button{flex:1}}";
      document.head.appendChild(style);
    }
    const box = document.createElement("aside");
    box.className = "gravel-consent";
    box.setAttribute("aria-label", "تنظیمات آمار ناشناس");
    box.innerHTML = '<p><strong>کمک به بهترشدن گراول</strong><br>با اجازهٔ شما، رفتار آموزشی به‌صورت ناشناس ثبت می‌شود؛ بدون نام، ایمیل یا IP خام. <a href="/privacy.html">جزئیات</a></p><div><button data-choice="yes">موافقم</button><button data-choice="no">فعلاً نه</button></div>';
    box.addEventListener("click", function (event) {
      const choice = event.target && event.target.dataset.choice;
      if (!choice) return;
      try { localStorage.setItem(CONSENT_KEY, choice); } catch (_) {}
      box.remove();
      if (choice === "yes") {
        send("visitor_arrived", { entry: true });
        if (window.GRAVEL_TUTORIAL_ID) send("tutorial_started", { tutorialId: window.GRAVEL_TUTORIAL_ID });
      }
    });
    document.body.appendChild(box);
  }

  window.GravelAnalytics = Object.freeze({ track: send, consent: consent });
  document.addEventListener("DOMContentLoaded", function () {
    showConsent();
    if (consent() === "yes") {
      send("visitor_arrived", { entry: true });
      if (window.GRAVEL_TUTORIAL_ID) send("tutorial_started", { tutorialId: window.GRAVEL_TUTORIAL_ID });
    }
  });
  addEventListener("scroll", function () {
    const available = document.documentElement.scrollHeight - innerHeight;
    if (available > 0) maxScroll = Math.max(maxScroll, Math.round(scrollY / available * 100));
  }, { passive: true });
  addEventListener("pagehide", function () {
    send("page_engaged", { seconds: Math.min(3600, Math.round((Date.now() - startedAt) / 1000)), maxScroll: Math.min(100, maxScroll) });
  });
})();
