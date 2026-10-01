/* VALUERAQ first-party analytics + Core Web Vitals beacon (~2 KB). No third parties. */
(function () {
  "use strict";
  var d = document, w = window, tpl = d.body.getAttribute("data-template") || "";
  function ck(n) { var m = d.cookie.match("(?:^|; )" + n + "=([^;]*)"); return m ? decodeURIComponent(m[1]) : null; }
  function setck(n, v) { d.cookie = n + "=" + encodeURIComponent(v) + "; path=/; max-age=1800; SameSite=Lax" + (location.protocol === "https:" ? "; Secure" : ""); }
  function send(url, obj) {
    var body = JSON.stringify(obj);
    try { if (navigator.sendBeacon && navigator.sendBeacon(url, new Blob([body], { type: "application/json" }))) return; } catch (e) {}
    try { fetch(url, { method: "POST", body: body, keepalive: true, headers: { "Content-Type": "application/json" } }); } catch (e) {}
  }
  var sid = ck("vq_sid"), first = !sid, path = location.pathname;
  if (first) { sid = Math.random().toString(36).slice(2) + Date.now().toString(36); setck("vq_lp", path); }
  setck("vq_sid", sid);
  var um = (location.search.match(/[?&]utm_medium=([^&]+)/) || [])[1];
  var ev = { n: "page_view", p: path, sid: sid, lp: ck("vq_lp") || path, ch: ck("vq_ch"), t: tpl };
  if (first) {
    ev.first = 1; ev.ref = d.referrer; ev.um = um;
    fetch("/api/events/", { method: "POST", body: JSON.stringify(ev), headers: { "Content-Type": "application/json" }, keepalive: true })
      .then(function (r) { return r.json(); }).then(function (j) { if (j && j.ch) setck("vq_ch", j.ch); }).catch(function () {});
  } else { setck("vq_ch", ck("vq_ch") || "direct"); send("/api/events/", ev); }
  w.vqTrack = function (name, props) { send("/api/events/", { n: name, p: path, sid: sid, lp: ck("vq_lp"), ch: ck("vq_ch"), x: props }); };

  /* Core Web Vitals (field data), sent once when the page is hidden. */
  if (!("PerformanceObserver" in w)) return;
  var v = { LCP: 0, CLS: 0, INP: 0 }, sent = false, sess = 0, sessVal = 0, last = 0;
  function obs(type, cb) { try { new PerformanceObserver(function (l) { l.getEntries().forEach(cb); }).observe({ type: type, buffered: true }); } catch (e) {} }
  obs("largest-contentful-paint", function (e) { v.LCP = e.startTime; });
  obs("layout-shift", function (e) {
    if (e.hadRecentInput) return;
    if (e.startTime - last > 1000 || e.startTime - sess > 5000) { sess = e.startTime; sessVal = 0; }
    last = e.startTime; sessVal += e.value; if (sessVal > v.CLS) v.CLS = sessVal;
  });
  try { new PerformanceObserver(function (l) { l.getEntries().forEach(function (e) { if (e.interactionId && e.duration > v.INP) v.INP = e.duration; }); })
    .observe({ type: "event", buffered: true, durationThreshold: 40 }); } catch (e) {}
  function flush() {
    if (sent) return; sent = true;
    var nav = performance.getEntriesByType && performance.getEntriesByType("navigation")[0];
    if (nav) send("/api/vitals/", { m: "TTFB", v: Math.round(nav.responseStart), t: tpl, p: path });
    if (v.LCP) send("/api/vitals/", { m: "LCP", v: Math.round(v.LCP), t: tpl, p: path });
    send("/api/vitals/", { m: "CLS", v: Math.round(v.CLS * 1000) / 1000, t: tpl, p: path });
    if (v.INP) send("/api/vitals/", { m: "INP", v: Math.round(v.INP), t: tpl, p: path });
  }
  d.addEventListener("visibilitychange", function () { if (d.visibilityState === "hidden") flush(); });
  w.addEventListener("pagehide", flush);
})();
/* Show/hide password buttons */
document.addEventListener("click", function (e) {
  var b = e.target.closest && e.target.closest("[data-pw-toggle]");
  if (!b) return;
  var i = document.getElementById(b.getAttribute("data-pw-toggle"));
  if (!i) return;
  var show = i.type === "password";
  i.type = show ? "text" : "password";
  b.setAttribute("aria-pressed", show ? "true" : "false");
  b.setAttribute("aria-label", show ? "Hide password" : "Show password");
});
/* Monthly / Yearly switch on plan cards */
document.addEventListener("click", function (e) {
  var b = e.target.closest && e.target.closest(".period button[data-period]");
  if (!b) return;
  var card = b.closest("[data-period]:not(button)");
  if (!card) return;
  card.setAttribute("data-period", b.getAttribute("data-period"));
  Array.prototype.forEach.call(b.parentNode.querySelectorAll("button"), function (x) {
    x.setAttribute("aria-pressed", x === b ? "true" : "false");
  });
});
