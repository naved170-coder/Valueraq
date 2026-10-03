/* Google Analytics 4 with Consent Mode.
   Until the visitor taps Accept, Google gets cookie-free, anonymous counts only.
   Advertising storage is always refused. The choice is remembered in this browser. */
(function () {
  var tag = document.currentScript || document.querySelector("script[data-ga-id]");
  var id = tag && tag.getAttribute("data-ga-id");
  if (!id) return;
  var KEY = "vq_cookie_choice";
  function read() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  var choice = read();
  gtag("consent", "default", {
    analytics_storage: choice === "granted" ? "granted" : "denied",
    ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied"
  });
  gtag("js", new Date());
  gtag("config", id);

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
  document.head.appendChild(s);

  var bar = document.getElementById("cookie-bar");
  function show(on) { if (bar) bar.hidden = !on; }
  if (choice !== "granted" && choice !== "denied") show(true);
  document.addEventListener("click", function (e) {
    var t = e.target.closest && e.target.closest("[data-cookie-choice], [data-cookie-settings]");
    if (!t) return;
    if (t.hasAttribute("data-cookie-settings")) { show(true); if (bar) bar.querySelector("button").focus(); return; }
    var v = t.getAttribute("data-cookie-choice");
    save(v);
    gtag("consent", "update", { analytics_storage: v === "granted" ? "granted" : "denied" });
    show(false);
  });
})();
