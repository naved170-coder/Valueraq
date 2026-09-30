/* Progressive enhancement for valuation tools and calculators.
   Without JavaScript the form posts normally and the server renders a (noindex) result page. */
(function () {
  "use strict";
  var forms = document.querySelectorAll("form[data-calc]");
  Array.prototype.forEach.call(forms, function (form) {
    var out = document.getElementById(form.getAttribute("data-out"));
    var btn = form.querySelector("button[type=submit]");
    var started = false;
    form.addEventListener("input", function () {
      if (!started && window.vqTrack) { started = true; window.vqTrack("tool_started", { tool: form.getAttribute("data-calc") }); }
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearErrors(form);
      btn.disabled = true; var label = btn.textContent; btn.textContent = "Calculating…";
      fetch(form.action, { method: "POST", body: new FormData(form), headers: { "Accept": "application/json" }, credentials: "same-origin" })
        .then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); })
        .then(function (res) {
          var j = res.body;
          if (j.ok) {
            out.innerHTML = j.html; out.hidden = false;
            out.setAttribute("tabindex", "-1"); out.focus({ preventScroll: true });
            out.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
          } else {
            showErrors(form, j.fields || {}, j.error || "Please check your inputs.");
          }
        })
        .catch(function () { form.submit(); })
        .then(function () { btn.disabled = false; btn.textContent = label; });
    });
  });
  function clearErrors(form) {
    Array.prototype.forEach.call(form.querySelectorAll(".field.error"), function (f) { f.classList.remove("error"); });
    Array.prototype.forEach.call(form.querySelectorAll(".err.js"), function (e) { e.remove(); });
    var g = form.querySelector(".form-error"); if (g) g.hidden = true;
  }
  function showErrors(form, fields, msg) {
    var g = form.querySelector(".form-error"); if (g) { g.textContent = msg; g.hidden = false; }
    Object.keys(fields).forEach(function (k) {
      var input = form.querySelector("[name='" + k + "']"); if (!input) return;
      var field = input.closest(".field"); field.classList.add("error");
      var p = document.createElement("p"); p.className = "err js"; p.textContent = fields[k]; field.appendChild(p);
    });
  }
})();
