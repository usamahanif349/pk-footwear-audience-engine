/* Joota Pulse: the personal audit page a brand opens from the pitch e-mail (audit.html?brand=Borjan).
   Every number comes from data.json, the same weekly data as the app. */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = n => Number(n).toLocaleString("en-US");
  const pct = x => Math.round(x * 100) + "%";
  const store = {
    get(k, d) { try { const v = localStorage.getItem("jp_" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("jp_" + k, JSON.stringify(v)); } catch (e) { /* storage off */ } },
  };
  const PRICE = 4500, CONV = 10;
  const money = n => { const x = n * CONV / 100 * PRICE; return x >= 100000 ? `Rs ${(x / 100000).toFixed(1)} lakh` : `Rs ${fmt(Math.round(x))}`; };
  const scoreColor = s => s >= 70 ? "var(--mint)" : s >= 50 ? "var(--gold)" : "var(--rose)";
  const short = b => b.replace(" Pakistan", "");
  const I = {
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/>',
    chat: '<path d="M21 12a8 8 0 01-11.6 7.1L4 20l1-4.6A8 8 0 1121 12z"/>',
    check: '<path d="M20 6L9 17l-5-5"/>',
    video: '<rect x="2" y="6" width="14" height="12" rx="3"/><path d="M16 10l6-3v10l-6-3"/>',
    pin: '<path d="M12 22s7-6.2 7-12a7 7 0 10-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.6"/>',
  };
  const svg = k => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${I[k]}</svg>`;

  let theme = document.documentElement.getAttribute("data-theme") || "dark";
  const setTheme = t => { document.documentElement.setAttribute("data-theme", t); $("#theme").innerHTML = svg(t === "light" ? "moon" : "sun"); };
  setTheme(theme);
  $("#theme").onclick = () => { theme = theme === "light" ? "dark" : "light"; setTheme(theme); store.set("theme", theme); };
  $("#print").onclick = () => window.print();

  function picker(D) {
    return `<section class="sec-h" style="margin-top:60px"><small>FREE AUDIT</small><h2>Which brand's audit would you like to see?</h2></section>
      <div class="bproof">${D.brands.map(b => `<a class="bp" href="?brand=${encodeURIComponent(b)}"><div class="h"><b>${esc(short(b))}</b></div><div class="go">Open the audit →</div></a>`).join("")}</div>`;
  }

  function audit(D, b) {
    const s = D.spaces[b], h = s.health[b], others = D.brands.length - 1;
    const seen = new Set();
    const asks = D.inbox.filter(m => m.brand === b && m.ask !== "Complaint" && m.text.length >= 10 && m.text.length <= 160 && !/\d:\d\d|co ?-?ord|dress|suit|shirt|kurt|lawn|dupatta|lehenga|frock|trouser|jeans|bag|makeup|jewel/i.test(m.text)
      && !seen.has(m.text.toLowerCase()) && seen.add(m.text.toLowerCase())).slice(0, 6);
    const rows = [...D.competitors].sort((x, y) => y.health - x.health);
    const MIN = 5;  // a finding needs at least 5 comments behind it
    const city = s.cities.filter(c => c.n >= MIN)[0];
    const ownOk = s.own_q >= MIN;
    const topAsk = s.asks[0];
    const fix = s.campaigns.slice(0, 3);
    const leads = s.leads.slice(0, 3);
    const subject = `Joota Pulse audit for ${short(b)}`;
    document.title = `${short(b)} · YouTube audience audit · Joota Pulse`;
    return `
    <section class="au-hero">
      <span class="eyebrow"><span class="live-dot"></span>Prepared for ${esc(short(b))} · data from ${esc(D.date)}</span>
      <h1><span class="grad">${fmt(s.waiting)} shoppers</span> asked ${esc(short(b))} where to buy, what it costs or how to order.<br>They're still waiting for a reply.</h1>
      <p class="lede">We read ${fmt(s.comments)} public YouTube comments about ${esc(short(b))} from your channel and from creators' sale vlogs and reviews. Here is what your customers are asking, how you compare with ${others} other Pakistani footwear brands, and three things to do this week.</p>
      <div class="au-kpis">
        <div class="au-k hot"><small>Missed sales (estimate)</small><b>${money(s.waiting)}</b><span>${fmt(s.waiting)} unanswered buying questions × ${CONV}% × Rs ${fmt(PRICE)} a pair</span></div>
        <div class="au-k"><small>Audience health</small><b style="color:${scoreColor(h.score)}">${h.score}<em>/100</em></b><span>#${h.rank} of ${D.brands.length} brands we track</span></div>
        ${ownOk ? `<div class="au-k"><small>Buying questions answered on your own videos</small><b>${s.own_answered} of ${s.own_q}</b><span>${s.own_answered ? "most still need a reply" : "not one has had a reply"}</span></div>`
          : `<div class="au-k"><small>Buying questions on creators' videos</small><b>${fmt(s.creator_q)}</b><span>where brands rarely reply</span></div>`}
        ${city ? `<div class="au-k"><small>Most-asked city</small><b>${esc(city.city)}</b><span>${city.n} shoppers named it</span></div>`
          : `<div class="au-k"><small>Top question</small><b>${topAsk ? esc(topAsk.label) : "–"}</b><span>${topAsk ? `${fmt(topAsk.n)} comments ask this` : ""}</span></div>`}
      </div>
    </section>

    <section class="sec"><div class="sec-h"><small>IN THEIR OWN WORDS</small><h2>Real questions under videos about ${esc(short(b))}</h2><p>The most recent questions still waiting for a reply. ${topAsk ? `The most common ask is <b>${esc(topAsk.label.toLowerCase())}</b> (${fmt(topAsk.n)} comments).` : ""}</p></div>
      <div class="au-quotes">${asks.map(m => `<figure class="au-q"><blockquote>“${esc(m.text)}”</blockquote><figcaption><span class="tag hot">${esc(m.ask)}</span>${esc(m.where.replace("Creator · ", "on "))} · ${esc(m.date)}</figcaption></figure>`).join("")}</div>
    </section>

    <section class="sec"><div class="au-two">
      <div class="panel"><div class="panel-h"><h2>Where you stand</h2><span>audience health, 0–100</span></div>
        ${rows.map((c, i) => `<div class="au-rank ${c.brand === b ? "me" : ""}"><span class="n">${i + 1}</span><span class="nm">${esc(short(c.brand))}</span><span class="bar"><i style="width:${c.health}%;background:${scoreColor(c.health)}"></i></span><b>${c.health}</b></div>`).join("")}
        <p class="note" style="margin-top:12px">Health combines buying interest (40%), few complaints (35%) and fans (25%), each compared with the other brands.</p></div>
      <div class="panel"><div class="panel-h"><h2>Creators already selling for you</h2><span>buyers asking on their videos</span></div>
        ${leads.length ? leads.map(l => `<div class="au-cr">${svg("video")}<div><b>${esc(l.channel)}</b><span>${l.buyers} viewers asked about price, sizes or where to buy</span></div></div>`).join("") : '<p class="note">No creator videos found for this brand yet.</p>'}
        <p class="note" style="margin-top:12px">${fmt(s.creator_q)} of ${esc(short(b))}'s buying questions sit under creators' videos, where brands rarely reply.</p></div>
    </div></section>

    <section class="sec"><div class="sec-h"><small>DO THIS WEEK</small><h2>Three moves to win these buyers back</h2></div>
      <div class="steps3">${fix.map((c, i) => `<div class="step3"><div class="n">${i + 1}</div><h3>${esc(c.title)}</h3><p>${esc(c.do)}</p><p class="au-why">${esc(c.why.replace("{MONEY}", money(s.waiting)))}</p></div>`).join("")}</div>
    </section>

    <section class="sec"><div class="au-offer">
      <div><small>WHAT JOOTA PULSE DOES FOR ${esc(short(b).toUpperCase())}</small><h2>Every Monday, your team gets the buyers to answer and the replies to send.</h2>
        <ul><li>${svg("chat")}A leads inbox with ready replies in Roman Urdu and English</li><li>${svg("check")}Alerts for new buyers, complaints and creator leads</li><li>${svg("pin")}Your health score and rank against ${others} competitors, every week</li><li>${svg("video")}Campaign ideas with ad copy, plus a client-ready PDF report</li></ul></div>
      <div class="au-cta"><a class="btn coral lg" data-audit href="#">Book a 20-min call</a><a class="btn ghost lg" href="app.html?brand=${encodeURIComponent(b)}#today">Open ${esc(short(b))}'s live workspace</a><span>Free 30-day pilot for the first 3 brands. No payment details needed.</span></div>
    </div></section>
    <p class="au-method">How we got these numbers: public YouTube comments collected through the official YouTube Data API, cleaned (Indian and foreign videos removed, commenter names never stored) and tagged by a multilingual AI model that reads English, Roman Urdu and Urdu. Missed sales is an estimate, not a measured figure.</p>`.replace(/data-audit href="#"/g, `data-audit href="mailto:usamahanif349@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(`Hi Usama,\n\nI saw the Joota Pulse audit for ${short(b)}. Let's talk.\n\nName:\nRole:\nBest time to call:\n`)}"`);
  }

  fetch("data.json", { cache: "no-cache" }).then(r => r.json()).then(D => {
    const b = new URLSearchParams(location.search).get("brand");
    const ok = b && D.spaces[b] && D.brands.includes(b);
    $("#audit").innerHTML = ok ? audit(D, b) : picker(D);
    const mail = "mailto:usamahanif349@gmail.com?subject=" + encodeURIComponent("Joota Pulse: free audit");
    $$('a[data-audit][href="#"]').forEach(a => a.href = ok ? $("#audit a[data-audit]").href : mail);
  }).catch(() => { $("#audit").innerHTML = '<p class="note" style="padding:60px 0;text-align:center">The audit couldn\'t load. Please refresh.</p>'; });
})();
