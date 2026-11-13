/* Joota Pulse landing page: fills the live numbers from data.json. */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = n => Number(n).toLocaleString("en-US");
  const store = {
    get(k, d) { try { const v = localStorage.getItem("jp_" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("jp_" + k, JSON.stringify(v)); } catch (e) { /* storage off */ } },
  };
  const PRICE = 4500, CONV = 10;
  const money = n => { const x = n * CONV / 100 * PRICE; return x >= 100000 ? `Rs ${(x / 100000).toFixed(1)} lakh` : `Rs ${fmt(Math.round(x))}`; };
  const PALETTE = ["#7B6CFF", "#FF7A59", "#2BB98A", "#3D8BFF", "#E05BA8", "#C9922E", "#14A3A3"];
  const colorOf = name => PALETTE[[...String(name)].reduce((a, c) => a + c.charCodeAt(0), 0) % PALETTE.length];
  const initials = name => String(name).replace(/Pakistan|Shoes/g, "").trim().split(/\s+/).map(w => w[0]).join("").slice(0, 2).toUpperCase();
  const scoreColor = s => s >= 70 ? "var(--mint)" : s >= 50 ? "var(--gold)" : "var(--rose)";

  /* theme */
  const SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  const MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/></svg>';
  const setTheme = t => {
    document.documentElement.setAttribute("data-theme", t); $("#theme").innerHTML = t === "light" ? MOON : SUN;
    const dir = t === "light" ? "light" : "dark";
    $$("[data-shot]").forEach(i => i.src = `shots/${dir}/${i.dataset.shot}.jpg`);
    $$("[data-crop]").forEach(i => i.src = `shots/${dir}/crop-${i.dataset.crop}.jpg`);
  };
  let theme = document.documentElement.getAttribute("data-theme") || "dark";
  setTheme(theme);
  $("#theme").onclick = () => { theme = theme === "light" ? "dark" : "light"; setTheme(theme); store.set("theme", theme); };

  /* hero product tour: auto-plays, pauses on hover, tabs jump */
  (function tour() {
    const tabs = $$("#tour [data-v]"), imgs = $$("#tour [data-shot]");
    if (!tabs.length) return;
    let i = 0, timer = null;
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const show = k => {
      i = k;
      tabs.forEach((t, n) => { t.classList.toggle("on", n === k); t.setAttribute("aria-selected", String(n === k)); t.classList.remove("run"); });
      imgs.forEach((im, n) => im.classList.toggle("on", n === k));
      if (!still && !paused) { void tabs[k].offsetWidth; tabs[k].classList.add("run"); }
    };
    let paused = false;
    const play = () => { clearInterval(timer); if (still) return; timer = setInterval(() => { if (!paused) show((i + 1) % tabs.length); }, 5000); };
    tabs.forEach((t, n) => t.onclick = () => { show(n); play(); });
    const box = $("#tour");
    box.onmouseenter = () => { paused = true; tabs[i].classList.remove("run"); };
    box.onmouseleave = () => { paused = false; show(i); play(); };
    show(0); play();
  })();

  /* audit e-mail */
  const audit = "mailto:usamahanif349@gmail.com?subject=" + encodeURIComponent("Joota Pulse: free audit for my brand")
    + "&body=" + encodeURIComponent("Hi Usama,\n\nI'd like a free Joota Pulse audit.\n\nBrand:\nMy role:\nBest time to talk:\n\nThanks!");
  $$("[data-audit]").forEach(a => a.href = audit);

  fetch("data.json", { cache: "no-cache" }).then(r => r.json()).then(D => {
    const a = D.spaces.all, set = (k, v) => $$(`[data-k="${k}"]`).forEach(el => el.textContent = v);
    set("eyebrow", `Live: ${fmt(a.comments)} comments on ${D.brands.length} brands · updated ${D.date}`);
    set("comments", fmt(a.comments));
    set("waiting", fmt(a.waiting));
    set("money", money(a.waiting));
    set("brands", D.brands.length);
    set("ratio", `${a.own_answered} of ${a.own_q}`);
    set("creatorq", fmt(a.creator_q));
    if (a.stats) set("cmratio", `${Math.round(a.stats.cm_ratio)}×`);
    if (a.cities[0]) { set("city", a.cities[0].city); set("citytxt", `is the city shoppers ask about most (${a.cities[0].n} mentions)`); }
    const cards = D.brands.map(b => ({ b, s: D.spaces[b], h: D.spaces[b].health[b] })).sort((x, y) => y.s.waiting - x.s.waiting);
    $("#bproof").innerHTML = cards.map(({ b, s, h }) => `<a class="bp" href="audit.html?brand=${encodeURIComponent(b)}">
      <div class="h"><div class="av" style="background:${colorOf(b)}">${esc(initials(b))}</div><b>${esc(b.replace(" Pakistan", ""))}</b><div class="score" style="color:${scoreColor(h.score)}">${h.score}<small>health · #${h.rank}</small></div></div>
      <div class="rows"><div>Buyers waiting<b style="color:var(--coral)">${fmt(s.waiting)}</b></div><div>Missed sales (est.)<b>${money(s.waiting)}</b></div>
      <div>Reply rate, own videos<b>${s.own_q ? Math.round(s.own_answered / s.own_q * 100) + "%" : "no questions yet"}</b></div></div>
      <div class="go">See ${esc(b.replace(" Pakistan", ""))}'s free audit →</div></a>`).join("")
      + `<a class="bp" href="app.html?brand=all#today" style="background:linear-gradient(135deg,var(--violet-soft),transparent)"><div class="h"><div class="av" style="background:linear-gradient(135deg,var(--violet-2),var(--coral))">All</div><b>Agency view</b></div>
      <div class="rows"><div>Brands<b>${D.brands.length}</b></div><div>Buyers waiting<b style="color:var(--coral)">${fmt(a.waiting)}</b></div><div>People who commented<b>${fmt(a.people)}</b></div></div><div class="go">Open the agency view →</div></a>`;
  }).catch(() => { $("#bproof").innerHTML = '<p class="note" style="text-align:center">Live numbers couldn\'t load. <a href="app.html">Open the app</a>.</p>'; });
})();
