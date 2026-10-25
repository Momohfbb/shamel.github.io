(function () {
  var body = document.body;

  // remember the chosen language for the next visit to the site root
  document.querySelectorAll("[data-lang]").forEach(function (a) {
    a.addEventListener("click", function () {
      try { localStorage.setItem("lang", a.dataset.lang); } catch (e) {}
    });
  });

  // mobile menu
  var btn = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open);
    });
  }

  // close the language menu when clicking elsewhere
  var langs = document.querySelector(".langs");
  document.addEventListener("click", function (e) {
    if (langs && langs.open && !langs.contains(e.target)) langs.open = false;
  });

  // localized dates
  var locale = body.dataset.locale;
  if (locale && window.Intl) {
    document.querySelectorAll("time[datetime]").forEach(function (t) {
      try {
        t.textContent = new Intl.DateTimeFormat(locale, { year: "numeric", month: "long", day: "numeric" })
          .format(new Date(t.getAttribute("datetime") + "T12:00:00"));
      } catch (e) {}
    });
  }
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  // listing filters
  var list = document.querySelector("[data-list]");
  if (list) {
    var field = "all", q = document.getElementById("q"), empty = document.querySelector("[data-empty]");
    var chips = document.querySelectorAll(".fchip[data-filter]");
    var run = function () {
      var term = (q && q.value || "").trim().toLowerCase(), shown = 0;
      list.querySelectorAll(".card").forEach(function (c) {
        var ok = (field === "all" || c.dataset.field === field) && (!term || c.dataset.search.indexOf(term) > -1);
        c.hidden = !ok; if (ok) shown++;
      });
      if (empty) empty.hidden = shown > 0;
    };
    chips.forEach(function (ch) {
      ch.addEventListener("click", function () {
        field = ch.dataset.filter;
        chips.forEach(function (o) { o.setAttribute("aria-pressed", o === ch); });
        run();
      });
    });
    if (q) q.addEventListener("input", run);
  }

  // copy citation
  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var text = b.parentNode.querySelector("[data-cite]");
      var done = function () { var o = b.textContent; b.textContent = b.dataset.done; setTimeout(function () { b.textContent = o; }, 1600); };
      var select = function () { var r = document.createRange(); r.selectNodeContents(text); var s = getSelection(); s.removeAllRanges(); s.addRange(r); };
      if (navigator.clipboard) navigator.clipboard.writeText(text.textContent).then(done, select);
      else select();
    });
  });

  // contact form: Formspree if configured, otherwise hand the message to WhatsApp
  var form = document.getElementById("contact-form");
  if (form) {
    var status = document.getElementById("form-status"), d = form.dataset;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var f = new FormData(form), name = (f.get("name") || "").trim(), contact = (f.get("contact") || "").trim(), msg = (f.get("message") || "").trim();
      if (!name || !contact || !msg) { status.textContent = d.stMissing; return; }
      if (d.endpoint) {
        status.textContent = d.stSending;
        fetch(d.endpoint, { method: "POST", headers: { Accept: "application/json" }, body: f })
          .then(function (r) { if (!r.ok) throw 0; status.textContent = d.stOk; form.reset(); })
          .catch(function () { status.textContent = d.stErr; });
        return;
      }
      var a = document.createElement("a");
      a.href = "https://wa.me/" + body.dataset.wa + "?text=" + encodeURIComponent(name + "\n" + contact + "\n\n" + msg);
      a.target = "_blank"; a.rel = "noopener"; a.textContent = d.stWaLink;
      status.textContent = d.stWa + " ";
      status.appendChild(a);
    });
  }
})();
