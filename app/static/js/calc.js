/* Progressive enhancement for valuation tools and calculators.
   Without JavaScript the form posts normally and the server renders a (noindex) result page. */
(function () {
  "use strict";
  var forms = document.querySelectorAll("form[data-calc]");
  Array.prototype.forEach.call(forms, function (form) {
    var out = document.getElementById(form.getAttribute("data-out"));
    var btn = form.querySelector("button[type=submit]");
    var started = false, initial = out ? out.innerHTML : "";
    var rows = form.querySelector("[data-src-rows]"), tpl = form.querySelector("template[data-src-template]");
    var startRows = rows ? rows.children.length : 0;
    function total() {
      if (!rows) return;
      var sum = 0;
      Array.prototype.forEach.call(rows.querySelectorAll("input[name=src_amount]"), function (i) {
        var v = parseFloat(String(i.value).replace(/[,$\s]/g, "")); if (!isNaN(v) && v > 0) sum += v;
      });
      form.querySelector("[data-src-total]").textContent = "$" + Math.round(sum).toLocaleString("en-US");
      var n = rows.children.length;
      Array.prototype.forEach.call(rows.querySelectorAll("[data-src-del]"), function (b) { b.hidden = n < 2; });
    }
    if (rows) {
      form.querySelector("[data-src-add]").addEventListener("click", function () {
        rows.appendChild(tpl.content.cloneNode(true));
        var sel = rows.lastElementChild.querySelector("select"); if (sel) sel.focus();
        total();
      });
      rows.addEventListener("click", function (e) {
        var b = e.target.closest("[data-src-del]"); if (!b) return;
        var r = b.closest(".src-row"), next = r.nextElementSibling || r.previousElementSibling;
        r.remove(); total();
        if (next) next.querySelector("select").focus();
      });
      rows.addEventListener("input", total);
      total();
    }
    form.addEventListener("reset", function () {
      clearErrors(form);
      if (rows) { while (rows.children.length > startRows) rows.lastElementChild.remove(); setTimeout(total, 0); }
      if (out) out.innerHTML = initial;
      setTimeout(function () { var f = form.querySelector("input, select"); if (f) f.focus(); }, 0);
    });
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
  /* "Value another business": clear the form and go back to it. */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-new-valuation]"); if (!a) return;
    var form = document.querySelector("form[data-calc]"); if (!form) return;
    e.preventDefault();
    form.reset();
    form.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  });
  function clearErrors(form) {
    Array.prototype.forEach.call(form.querySelectorAll(".field.error"), function (f) { f.classList.remove("error"); });
    Array.prototype.forEach.call(form.querySelectorAll(".err.js"), function (e) { e.remove(); });
    var g = form.querySelector(".form-error"); if (g) g.hidden = true;
  }
  function showErrors(form, fields, msg) {
    var g = form.querySelector(".form-error"); if (g) { g.textContent = msg; g.hidden = false; }
    Object.keys(fields).forEach(function (k) {
      var input = form.querySelector("[name='" + k + "']") || form.querySelector("[data-fields~='" + k + "']");
      if (!input) return;
      var field = input.closest(".field"); field.classList.add("error");
      var p = document.createElement("p"); p.className = "err js"; p.textContent = fields[k]; field.appendChild(p);
    });
  }
})();
