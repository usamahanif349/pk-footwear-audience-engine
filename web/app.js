/* Joota Pulse web app. All numbers come from data.json, exported by src/web/export.py
   from real public YouTube comments. The browser only filters, formats and displays. */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = n => Number(n).toLocaleString("en-US");
  const pct = (x, d = 0) => (x * 100).toFixed(d) + "%";
  const store = {
    get(k, d) { try { const v = localStorage.getItem("jp_" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("jp_" + k, JSON.stringify(v)); } catch (e) { /* storage off */ } },
  };
  const charts = [];

  const ICON = {
    today: '<path d="M3 12l9-8 9 8M5 10v10h5v-6h4v6h5V10"/>',
    inbox: '<path d="M3 13l3-8h12l3 8v6H3zM3 13h5l1 3h6l1-3h5"/>',
    customers: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.3-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><circle cx="17.5" cy="9" r="2.6"/><path d="M16 14.6c2.7.1 4.6 1.8 5.4 4.9"/>',
    content: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9.5v5l4.5-2.5z"/>',
    competitors: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    campaigns: '<path d="M4 14c4-1 6-3 8-9 2 6 4 8 8 9-4 1-6 3-8 9-2-6-4-8-8-9z"/>',
    report: '<path d="M6 3h9l4 4v14H6zM14 3v5h5M9 13h7M9 17h5"/>',
    how: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
  };
  const svg = p => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[p]}</svg>`;
  const PAGES = [
    { grp: "Workspace" },
    { id: "today", label: "Today" }, { id: "inbox", label: "Leads inbox", count: true }, { id: "customers", label: "Your customers" },
    { id: "content", label: "Post this, not that" }, { id: "competitors", label: "Competitors" }, { id: "campaigns", label: "Campaign ideas" },
    { grp: "Share" }, { id: "report", label: "Client report" },
    { grp: "About" }, { id: "how", label: "How it works" },
  ];
  const PALETTE = ["#7B6CFF", "#FF7A59", "#2BB98A", "#3D8BFF", "#E05BA8", "#C9922E", "#14A3A3"];
  const avatar = name => `<div class="av" style="background:${PALETTE[[...String(name)].reduce((a, c) => a + c.charCodeAt(0), 0) % PALETTE.length]}">${esc(String(name).trim()[0] || "?").toUpperCase()}</div>`;

  let D, S = {
    ws: store.get("ws", "all"), price: store.get("price", 4500), conv: store.get("conv", 10),
    kind: "All", src: "Everywhere", q: "", sel: null, lang: store.get("lang", "ru"), link: store.get("link", "[shop link]"),
    seg: null,
  };

  const W = () => D.spaces[S.ws];
  const money = n => {
    const x = n * (S.conv / 100) * S.price;
    return x >= 100000 ? `Rs ${(x / 100000).toFixed(1)} lakh` : `Rs ${fmt(Math.round(x))}`;
  };
  const inboxItems = () => D.inbox.filter(m => W().brands.includes(m.brand));
  const fillMoney = s => s.replace("{MONEY}", money(W().waiting));
  const reply = (need, brand) => {
    const t = (D.replies[need] || D.replies.contact)[S.lang] || "";
    return t.replace(/\{(\w+)\}/g, (_, k) => ({ brand, link: S.link, price: "____", end_date: "____" }[k] ?? ""));
  };
  const toast = msg => { const t = $("#toast"); t.textContent = msg; t.classList.add("on"); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("on"), 1600); };
  const copy = text => {
    const done = () => toast("Copied. Paste it on YouTube.");
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, () => fallback());
    else fallback();
    function fallback() { const a = document.createElement("textarea"); a.value = text; document.body.appendChild(a); a.select(); try { document.execCommand("copy"); done(); } catch (e) { toast("Select the text and copy it"); } a.remove(); }
  };
  const header = (title, sub, right = "") => `<div class="page-h"><div><h1>${title}</h1><p>${sub}</p></div>${right}</div>`;
  const hbars = (rows) => {
    const mx = Math.max(...rows.map(r => r.n), 1);
    return rows.map(r => `<div class="hbar"><div class="row">${esc(r.label)}<span>${fmt(r.n)}</span></div><div class="track"><div class="fill ${r.hot ? "hot" : ""}" style="width:${(r.n / mx * 100).toFixed(0)}%"></div></div></div>`).join("");
  };
  const tagFor = ask => ask === "Complaint" ? "bad" : "hot";

  /* ---------------- nav + shell ---------------- */
  function nav(active) {
    $("#nav").innerHTML = PAGES.map(p => p.grp ? `<div class="grp">${p.grp}</div>` :
      `<a href="#${p.id}" class="${p.id === active ? "on" : ""}" ${p.id === active ? 'aria-current="page"' : ""}>${svg(p.id)}<span>${p.label}</span>${p.count ? `<span class="cnt">${fmt(W().waiting)}</span>` : ""}</a>`).join("");
    $("#ws-av").textContent = S.ws === "all" ? "A" : S.ws === "core" ? "C" : S.ws[0];
  }

  /* ---------------- TODAY ---------------- */
  function today() {
    const w = W();
    const rate = w.own_q ? w.own_answered / w.own_q : null;
    const city = w.cities[0];
    const seen = new Set();
    const tick = inboxItems().filter(m => m.ask !== "Complaint" && m.text.length <= 60 && m.text.length >= 12 && !seen.has(m.text.toLowerCase()) && seen.add(m.text.toLowerCase())).slice(0, 24);
    const bubbles = tick.map(m => `<span class="bubble"><i>${esc(m.ask)}</i>${esc(m.text)}</span>`).join("");
    const preview = inboxItems().filter(m => m.ask !== "Complaint" && m.text.length > 8 && m.text.length < 140).slice(0, 4);
    const ready = w.segments.filter(s => s.tone === "hot").sort((a, b) => b.people - a.people).slice(0, 6);
    const ring = rate === null ? "" : `<svg class="ring" viewBox="0 0 36 36"><circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="4"/><circle cx="18" cy="18" r="15" fill="none" stroke="#FF5C7A" stroke-width="4" stroke-linecap="round" stroke-dasharray="${Math.max(rate * 94.2, 2)} 94.2" transform="rotate(-90 18 18)"/></svg>`;
    return `<div class="fade">
    <div class="grid">
      <section class="hero s8">
        <span class="kicker">● Sales slipping away right now</span>
        <div class="money" id="money" data-target="${w.waiting}">${money(w.waiting)}</div>
        <div class="line"><b>${fmt(w.waiting)} buyers</b> asked about price, stock or delivery. Nobody answered.</div>
        <div class="sub">${esc(w.label)} · ${fmt(w.comments)} real YouTube comments · estimate at Rs ${fmt(S.price)} a pair, ${S.conv}% buying</div>
        <div class="cta"><a class="btn coral" href="#inbox">Answer them now</a><a class="btn ghost" href="#report">Get the client report</a></div>
        <div class="ticker" aria-label="Recent unanswered buyer comments"><div class="track">${bubbles}${bubbles}</div></div>
        <svg class="pulse" viewBox="0 0 1000 120" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="#8B7BFF" stop-opacity="0"/><stop offset=".5" stop-color="#8B7BFF"/><stop offset="1" stop-color="#FF7A59"/></linearGradient></defs><path d="M0 80 H260 L290 80 L310 40 L335 110 L360 20 L385 95 L405 80 H640 L665 80 L685 55 L705 100 L725 70 H1000"/></svg>
      </section>
      <div class="side-stats s4">
        <div class="stat bad">${ring}<div class="l">Your reply rate</div><div class="v">${rate === null ? "–" : pct(rate)}</div><div class="n">${w.own_q ? `${w.own_answered} of ${w.own_q} buying questions answered on your own videos` : "No buying questions on your own videos"}</div></div>
        <div class="stat"><div class="l">Buying questions</div><div class="v">${fmt(w.buying)}</div><div class="n">${pct(w.buying / Math.max(w.top_level, 1))} of all comments · ${fmt(w.creator_q)} on creator videos</div></div>
        <div class="stat good"><div class="l">Hottest city</div><div class="v">${city ? esc(city.city) : "–"}</div><div class="n">${city ? `${city.n} shoppers asked about ${esc(city.city)}` : ""}</div></div>
      </div>

      <section class="panel s7">
        <div class="panel-h"><h2>Buyers waiting for you</h2><a class="more" href="#inbox">Open inbox (${fmt(w.waiting)})</a></div>
        ${preview.map(m => `<div class="msg">${avatar(m.brand)}<div><div class="meta"><b style="color:var(--text)">${esc(m.brand)}</b><span class="tag ${tagFor(m.ask)}">${esc(m.ask)}</span><span>${esc(m.where)}</span></div>
          <div class="txt">${esc(m.text)}</div><div class="rep"><b>Suggested reply:</b> ${esc(reply(m.need, m.brand)).slice(0, 120)}…</div></div><span class="note">${esc(m.date.slice(5))}</span></div>`).join("") || '<p class="note">No waiting buyers here.</p>'}
      </section>
      <section class="panel s5">
        <div class="panel-h"><h2>Ready-to-buy customers</h2><a class="more" href="#customers">All groups</a></div>
        ${hbars(ready.map(s => ({ label: `${s.emoji}  ${s.name}`, n: s.people, hot: true })))}
        <p class="note" style="margin-top:12px">People who asked about price, stock, size, delivery or deals.</p>
      </section>

      <section class="panel s7">
        <div class="panel-h"><h2>Do these 3 things today</h2><a class="more" href="#campaigns">All campaign ideas</a></div>
        ${w.campaigns.slice(0, 3).map(c => `<div class="camp"><div class="tags"><span class="tag ${c.impact.startsWith("High") ? "hot" : "warm"}">${c.impact}</span><span class="tag ok">${c.effort}</span><span class="tag cool">${esc(c.channel)}</span></div><h3>${esc(c.title)}</h3><p>${esc(c.do)}</p><div class="why">${esc(fillMoney(c.why))}</div></div>`).join("")}
      </section>
      <div class="s5" style="display:grid;gap:18px;align-content:start">
        <section class="panel">
          <div class="panel-h"><h2>Creators to partner with</h2><a class="more" href="#content">See all</a></div>
          ${w.leads.slice(0, 4).map((l, i) => `<div class="lead"><span class="rk ${i === 0 ? "top" : ""}">${i + 1}</span>${avatar(l.channel)}<div><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.channel)}</a><div class="sub">${esc(l.brands)}</div></div><div class="n">${l.buyers}<small>buyers asked</small></div></div>`).join("") || '<p class="note">No creator videos for this brand.</p>'}
        </section>
        <section class="panel">
          <div class="panel-h"><h2>Trending</h2><span>last 6 months vs before</span></div>
          ${w.trend.map(t => `<div class="kv"><span>${esc(t.label)}</span><b style="color:${t.pts > 0 ? "var(--mint)" : "var(--rose)"}">${t.pts > 0 ? "▲" : "▼"} ${Math.abs(t.pts).toFixed(1)} pts</b></div>`).join("")}
        </section>
      </div>
    </div></div>`;
  }

  function countUp() {
    const el = $("#money"); if (!el || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const target = Number(el.dataset.target), t0 = performance.now(), dur = 1100;
    const step = now => { const k = Math.min((now - t0) / dur, 1), e = 1 - Math.pow(1 - k, 3); el.textContent = money(target * e); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }

  /* ---------------- INBOX ---------------- */
  function inbox() {
    const all = inboxItems();
    const kinds = ["All", "Where to buy", "Price", "Order & delivery", "Size", "Contact", "Complaint"];
    const count = k => k === "All" ? all.length : all.filter(m => m.ask === k).length;
    let items = all.filter(m => (S.kind === "All" || m.ask === S.kind) && (S.src === "Everywhere" || (S.src === "Your videos") === m.own)
      && (!S.q || m.text.toLowerCase().includes(S.q.toLowerCase())));
    if (!items.find(m => m.id === S.sel)) S.sel = items.length ? items[0].id : null;
    const m = items.find(x => x.id === S.sel);
    const rows = items.slice(0, 300).map(x => `<button class="irow ${x.id === S.sel ? "on" : ""}" data-id="${x.id}" type="button">${avatar(x.brand)}<div><div class="top"><b>${esc(x.brand)}</b><span>${esc(x.date)}</span></div><div class="t">${esc(x.text)}</div><div class="tags"><span class="tag ${tagFor(x.ask)}">${esc(x.ask)}</span><span class="tag grey">${esc(x.where)}</span></div></div></button>`).join("");
    return `<div class="fade">${header("Leads inbox", `${fmt(W().waiting)} buyers asked and are still waiting. Pick one, copy the reply, paste it on YouTube.`,
      `<div class="seg" role="group" aria-label="Source">${["Everywhere", "Your videos", "Creator videos"].map(s => `<button type="button" data-src="${s}" class="${S.src === s ? "on" : ""}">${s}</button>`).join("")}</div>`)}
      <div class="chips" role="group" aria-label="Type">${kinds.map(k => `<button type="button" class="chip ${S.kind === k ? "on" : ""}" data-kind="${k}">${k}<em>${count(k)}</em></button>`).join("")}</div>
      <div class="inbox">
        <section class="panel"><input class="search" id="q" type="search" placeholder="Search comments" value="${esc(S.q)}" aria-label="Search comments">
          <div class="ilist" id="ilist">${rows || '<p class="note">Nothing here. 🎉</p>'}</div>
          <div class="row-btns"><button class="btn ghost sm" id="export" type="button">Export leads (CSV)</button><span class="note" style="align-self:center">${fmt(items.length)} shown</span></div>
        </section>
        <section class="panel reply-pane">${m ? `
          <div class="panel-h"><h2>Reply</h2><div class="seg" role="group" aria-label="Language"><button type="button" data-lang="ru" class="${S.lang === "ru" ? "on" : ""}">Roman Urdu</button><button type="button" data-lang="en" class="${S.lang === "en" ? "on" : ""}">English</button></div></div>
          <div class="cmt"><small>${esc(m.brand)} · ${esc(m.where)} · ${esc(m.date)}</small>${esc(m.text)}</div>
          <div class="suggest"><small>SUGGESTED REPLY</small><span id="rtext">${esc(reply(m.need, m.brand))}</span></div>
          <label class="field">Your shop link<input id="link" value="${esc(S.link)}"></label>
          <div class="row-btns"><button class="btn primary" id="copy" type="button">Copy reply</button>${m.url ? `<a class="btn ghost" href="${esc(m.url)}" target="_blank" rel="noopener">Open the video</a>` : ""}</div>
          <p class="note" style="margin-top:12px">Fill in any ____ before posting. Sample wording for a class project.</p>` : '<p class="note">No message selected.</p>'}
        </section>
      </div></div>`;
  }

  function wireInbox() {
    document.querySelectorAll("[data-kind]").forEach(b => b.onclick = () => { S.kind = b.dataset.kind; S.sel = null; render(); });
    document.querySelectorAll("[data-src]").forEach(b => b.onclick = () => { S.src = b.dataset.src; S.sel = null; render(); });
    document.querySelectorAll("[data-lang]").forEach(b => b.onclick = () => { S.lang = b.dataset.lang; store.set("lang", S.lang); render(); });
    document.querySelectorAll(".irow").forEach(b => b.onclick = () => { S.sel = Number(b.dataset.id); const y = $("#ilist").scrollTop; render(); $("#ilist").scrollTop = y; });
    const q = $("#q"); if (q) q.oninput = () => { S.q = q.value; clearTimeout(q.t); q.t = setTimeout(() => { render(); const nq = $("#q"); nq.focus(); nq.setSelectionRange(nq.value.length, nq.value.length); }, 250); };
    const link = $("#link"); if (link) link.oninput = () => { S.link = link.value; store.set("link", S.link); const m = D.inbox.find(x => x.id === S.sel); if (m) $("#rtext").textContent = reply(m.need, m.brand); };
    const c = $("#copy"); if (c) c.onclick = () => copy($("#rtext").textContent);
    const ex = $("#export"); if (ex) ex.onclick = () => {
      const rows = [["date", "brand", "asking_about", "comment", "posted_on", "video"]].concat(inboxItems().map(m => [m.date, m.brand, m.ask, m.text, m.where, m.url]));
      const csv = rows.map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); a.download = "joota_pulse_leads.csv"; a.click();
    };
  }

  /* ---------------- CUSTOMERS ---------------- */
  function customers() {
    const w = W();
    if (!w.segments.find(s => s.name === S.seg)) S.seg = w.segments[0]?.name;
    const sel = w.segments.find(s => s.name === S.seg);
    const ready = w.segments.filter(s => s.tone === "hot").reduce((a, s) => a + s.people, 0);
    return `<div class="fade">${header("Your customers", `${fmt(w.people)} people commented. Here's who they are and what each group needs.`)}
      <div class="grid" style="margin-bottom:18px">
        <div class="stat s3"><div class="l">People</div><div class="v">${fmt(w.people)}</div><div class="n">${fmt(w.comments)} comments</div></div>
        <div class="stat s3" style="border-color:rgba(255,122,89,.4)"><div class="l">Ready to buy</div><div class="v" style="color:var(--coral)">${fmt(ready)}</div><div class="n">asked about price, stock, size, delivery, deals</div></div>
        <div class="stat s3 bad"><div class="l">Need care</div><div class="v">${fmt((w.segments.find(s => s.name === "Unhappy customers") || {}).people || 0)}</div><div class="n">complaints to fix</div></div>
        <div class="stat s3 good"><div class="l">Fans</div><div class="v">${fmt(w.segments.filter(s => s.badge === "Fans").reduce((a, s) => a + s.people, 0))}</div><div class="n">praise and love</div></div>
      </div>
      <div class="tiles">${w.segments.map(s => `<button type="button" class="tile ${s.name === S.seg ? "on" : ""}" data-seg="${esc(s.name)}"><div class="h"><span class="e">${s.emoji}</span><span class="tag ${s.tone}">${s.badge}</span></div><div class="nm">${esc(s.name)}</div><div class="big">${fmt(s.people)} <small>people</small></div><div class="q">${s.quote ? `“${esc(s.quote)}”` : ""}</div><div class="do"><b>Do:</b> ${esc(s.todo)}</div></button>`).join("")}</div>
      ${sel ? `<section class="panel" style="margin-top:18px" id="hear"><div class="panel-h"><h2>${sel.emoji} ${esc(sel.name)}: in their words</h2><span>${fmt(sel.comments)} comments</span></div>
        <div class="grid">${sel.examples.map(e => `<div class="s6 cmt" style="font-size:.93rem"><small>${esc(e.brand)} · ${esc(e.date)}</small>${esc(e.text)}</div>`).join("")}</div></section>` : ""}
    </div>`;
  }

  /* ---------------- CONTENT ---------------- */
  function content() {
    const w = W(), st = w.stats;
    const card = (c, tone) => `<div class="pc"><div class="t">${esc(c.type)} <span class="tag ${tone}">${c.format}</span></div><div class="m"><div><b>${c.cm.toFixed(2)}</b>comments / 1k views</div><div><b>${pct(c.hi)}</b>buying questions</div><div><b>${fmt(c.views)}</b>median views</div><div><b>${c.n}</b>videos</div></div></div>`;
    return `<div class="fade">${header("Post this, not that", "What gets shoppers talking and asking to buy, and the creators who already bring them in.")}
      ${st ? `<div class="big3">
        <div class="stat"><div class="v">${Math.round(st.cm_ratio)}×</div><div class="n">more comments per view on creator videos than on brand videos</div></div>
        <div class="stat"><div class="v">${pct(st.hi_creator)} vs ${pct(st.hi_brand)}</div><div class="n">of comments are buying questions on creator vs brand videos</div></div>
        <div class="stat"><div class="v">${Math.round(st.views_ratio)}×</div><div class="n">more views on brand videos, mostly paid reach with little conversation</div></div></div>` : ""}
      <div class="grid">
        <section class="panel s6"><div class="panel-h"><h2>✅ Post more of this</h2><span>most conversation per view</span></div>${w.post_more.map(c => card(c, "ok")).join("") || '<p class="note">Not enough videos.</p>'}</section>
        <section class="panel s6"><div class="panel-h"><h2>✋ Less of this</h2><span>views without conversation</span></div>${w.post_less.map(c => card(c, "grey")).join("") || '<p class="note">Not enough videos.</p>'}</section>
        <section class="panel s6"><div class="panel-h"><h2>Creator leaderboard</h2><span>buyers asking on their videos</span></div>
          ${w.leads.slice(0, 8).map((l, i) => `<div class="lead"><span class="rk ${i < 3 ? "top" : ""}">${i + 1}</span>${avatar(l.channel)}<div><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.channel)}</a><div class="sub">${esc(l.brands)} · creator replies to ${pct(l.answered)}</div></div><div class="n">${l.buyers}<small>buyers asked</small></div></div>`).join("") || '<p class="note">No creator videos for this brand.</p>'}</section>
        <section class="panel s6"><div class="panel-h"><h2>Standout posts</h2><span>far ahead of similar posts</span></div>
          ${w.standouts.map(s => `<div class="pc"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title.slice(0, 80))}</a><div class="s">${esc(s.brand)} · ${esc(s.channel)} · ${fmt(s.views)} views</div><div class="w">▲ ${esc(s.why)}</div></div>`).join("") || '<p class="note">No standout posts here.</p>'}</section>
      </div></div>`;
  }

  /* ---------------- COMPETITORS ---------------- */
  function competitors() {
    const mine = new Set(S.ws === "all" ? [] : W().brands);
    const mx = Math.max(...D.competitors.map(c => c.buying));
    return `<div class="fade">${header("Competitors", "Every brand's audience side by side. Your workspace is highlighted.")}
      <section class="panel"><div class="panel-h"><h2>Brand scorecard</h2><span>${fmt(D.how.customer_comments)} customer comments</span></div>
      <div class="scroll-x"><table class="tbl"><thead><tr><th>Brand</th><th>Comments</th><th>Buying questions</th><th>Top ask</th><th>Replies on own videos</th><th>Fans</th><th>Complaints</th><th>Ad buzz</th></tr></thead><tbody>
      ${D.competitors.map(c => `<tr class="${mine.has(c.brand) ? "me" : ""}"><td>${esc(c.brand)}</td><td>${fmt(c.comments)}</td><td>${pct(c.buying)}<span class="meter"><i style="width:${(c.buying / mx * 100).toFixed(0)}%"></i></span></td><td><span class="tag hot">${esc(c.top)}</span></td><td>${c.own_q ? `${c.own_answered} of ${c.own_q}` : "–"}</td><td>${pct(c.fans)}</td><td>${pct(c.complaints, 1)}</td><td>${pct(c.buzz)}</td></tr>`).join("")}
      </tbody></table></div></section>
      <section class="panel" style="margin-top:18px"><div class="panel-h"><h2>What each brand's customers ask about</h2><span>% of the brand's comments</span></div><div class="chart-box"><canvas id="cmp"></canvas></div></section></div>`;
  }
  function drawCompetitors() {
    if (!window.Chart) return;
    const keys = ["Where to buy", "Price", "Sale", "Order & delivery", "Quality", "Complaints"];
    const cols = ["#8B7BFF", "#FF7A59", "#E05BA8", "#3D8BFF", "#3DD9A4", "#FF5C7A"];
    charts.push(new Chart($("#cmp"), {
      type: "bar",
      data: { labels: D.competitors.map(c => c.brand), datasets: keys.map((k, i) => ({ label: k, data: D.competitors.map(c => c.mix[k]), backgroundColor: cols[i], borderRadius: 4, maxBarThickness: 16 })) },
      options: { maintainAspectRatio: false, plugins: { legend: { labels: { color: "#A6A1CC", boxWidth: 10, boxHeight: 10, usePointStyle: true } }, tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.raw}%` } } },
        scales: { x: { ticks: { color: "#A6A1CC" }, grid: { display: false } }, y: { ticks: { color: "#77729F", callback: v => v + "%" }, grid: { color: "rgba(255,255,255,.06)" } } } },
    }));
  }

  /* ---------------- CAMPAIGNS ---------------- */
  function campaigns() {
    const cs = W().campaigns;
    return `<div class="fade">${header("Campaign ideas", "Smart suggestions built from your comments. Every idea shows the number behind it and comes with ready ad copy.")}
      <div class="grid">${cs.map((c, i) => `<section class="panel s6"><div class="camp" style="border:0;padding:0;background:none"><div class="tags"><span class="tag ${c.impact.startsWith("High") ? "hot" : c.impact.startsWith("Medium") ? "warm" : "grey"}">${c.impact}</span><span class="tag ok">${c.effort}</span><span class="tag cool">${esc(c.channel)}</span></div>
        <h3>${esc(c.title)}</h3><p>${esc(c.do)}</p><div class="why">Why: ${esc(fillMoney(c.why))}</div>
        <div class="copy"><div class="c"><div><small>ENGLISH</small><span id="en${i}">${esc(c.en)}</span></div><button class="btn ghost sm" data-copy="en${i}" type="button">Copy</button></div>
        <div class="c"><div><small>ROMAN URDU</small><span id="ru${i}">${esc(c.ru)}</span></div><button class="btn ghost sm" data-copy="ru${i}" type="button">Copy</button></div></div></div></section>`).join("")}</div>
      <section class="panel" style="margin-top:18px"><div class="panel-h"><h2>Plan the budget</h2></div><p class="note" style="font-size:.92rem">Project 2 splits the ad budget across Facebook, TikTok, Instagram, Google and YouTube for the same brands and writes ads around the same angles.</p><div class="row-btns"><a class="btn ghost" href="${D.links.p2app}" target="_blank" rel="noopener">Open the ad budget optimizer</a></div></section></div>`;
  }

  /* ---------------- REPORT ---------------- */
  function report() {
    const w = W();
    const rate = w.own_q ? pct(w.own_answered / w.own_q) : "–";
    const segs = w.segments.filter(s => s.tone === "hot" || s.tone === "bad").sort((a, b) => b.people - a.people).slice(0, 5);
    return `<div class="fade">${header("Client report", "A one-page snapshot to send to the brand. Switch the workspace to make one for a single brand.",
      `<button class="btn primary no-print" id="print" type="button">Download PDF</button>`)}
      <article class="sheet"><div class="hd"><small>JOOTA PULSE · AUDIENCE INTELLIGENCE</small><h2>Client snapshot: ${esc(w.label)}</h2><p>Based on ${fmt(w.comments)} real public YouTube comments · data collected ${esc(D.date)}</p></div>
      <div class="bd"><div class="k4">
        <div class="k"><div class="l">Missed sales (estimate)</div><div class="v">${money(w.waiting)}</div><div class="n">${fmt(w.waiting)} buyers waiting</div></div>
        <div class="k"><div class="l">Buying questions</div><div class="v">${fmt(w.buying)}</div><div class="n">price, stock, order, size</div></div>
        <div class="k"><div class="l">Reply rate, own videos</div><div class="v">${rate}</div><div class="n">${w.own_answered} of ${w.own_q} answered</div></div>
        <div class="k"><div class="l">Hottest city</div><div class="v">${w.cities[0] ? esc(w.cities[0].city) : "–"}</div><div class="n">${w.cities[0] ? w.cities[0].n + " mentions" : ""}</div></div></div>
        <h3>Do these first</h3>${w.campaigns.slice(0, 3).map((c, i) => `<div class="act"><i>${i + 1}</i><div><b>${esc(c.title)}: ${esc(c.do)}</b><span>${esc(fillMoney(c.why))}</span></div></div>`).join("")}
        <div class="two"><div><h3>Who your customers are</h3>${segs.map(s => `<div class="li"><span>${s.emoji} ${esc(s.name)}</span><b>${fmt(s.people)}</b></div>`).join("")}</div>
        <div><h3>Where they are</h3>${w.cities.slice(0, 4).map(c => `<div class="li"><span>${esc(c.city)}</span><b>${c.n}</b></div>`).join("") || '<p class="note">No cities named.</p>'}
        <h3>Creators to partner with</h3>${w.leads.slice(0, 3).map(l => `<div class="li"><span>${esc(l.channel)}</span><b>${l.buyers} buyers</b></div>`).join("") || '<p class="note">None.</p>'}</div></div>
        <div class="ft">Missed sales = unanswered buying questions × ${S.conv}% who would buy × Rs ${fmt(S.price)} per pair; an estimate, not a measured figure. Source: public YouTube comments via the official YouTube Data API; commenter names removed. ${esc(D.links.repo)}</div>
      </div></article></div>`;
  }

  /* ---------------- HOW ---------------- */
  function how() {
    const h = D.how, m = h.metrics;
    return `<div class="fade">${header("How it works", "The engine behind the app: real data, a multilingual AI model and checks on every step.")}
      <div class="grid">
        <section class="panel s6"><div class="panel-h"><h2>The pipeline</h2></div><div class="steps">
          <div class="step"><div><b>Collect</b><span>Official YouTube Data API: 853 videos about 8 Pakistani footwear brands (their channels plus creators' sale vlogs and reviews), 8,508 comments.</span></div></div>
          <div class="step"><div><b>Clean</b><span>Keep videos that name the brand; drop Indian and foreign videos (Bata's channel is Bata India, so Bata is out), foreign-language and empty comments. ${fmt(h.comments)} comments remain.</span></div></div>
          <div class="step"><div><b>Protect</b><span>Commenter names never stored; phone numbers, e-mails, @handles and order numbers removed.</span></div></div>
          <div class="step"><div><b>Understand</b><span>Word lists in English, Roman Urdu and Urdu tag clear needs; a multilingual AI embedding model tags similar comments the lists miss.</span></div></div>
          <div class="step"><div><b>Group</b><span>K-Means finds topic clusters; every person is placed in one customer group.</span></div></div>
          <div class="step"><div><b>Compare and flag</b><span>Attention per video; unusual posts by peer z-scores and an Isolation Forest.</span></div></div>
          <div class="step"><div><b>Act</b><span>Rules turn the numbers into leads, campaign ideas, replies and the client report.</span></div></div></div></section>
        <section class="panel s6"><div class="panel-h"><h2>Accuracy checks</h2></div>
          <div class="kv"><span>Comments tagged by word lists</span><b>${fmt(m.labelled_by_word_list)}</b></div>
          <div class="kv"><span>Tagged by the AI model (nearest neighbours)</span><b>${fmt(m.labelled_by_neighbours)}</b></div>
          <div class="kv"><span>AI tagging check (5-fold accuracy)</span><b>${pct(m.knn_cv_accuracy)}</b></div>
          <div class="kv"><span>Topic clusters (best silhouette)</span><b>${m.k}</b></div>
          <div class="kv"><span>Cluster–need match: AI embeddings (NMI)</span><b>${m.nmi_embeddings_vs_needs.toFixed(2)}</b></div>
          <div class="kv"><span>Cluster–need match: word-count baseline</span><b>${m.nmi_tfidf_vs_needs.toFixed(2)}</b></div>
          <p class="note" style="margin-top:10px">The AI embeddings group comments by need better than plain word counts. Silhouette is low (about 0.14) because short comments overlap.</p></section>
        <section class="panel s7"><div class="panel-h"><h2>Comments mapped by meaning</h2><span>1,500 sample comments</span></div><div class="chart-box"><canvas id="map"></canvas></div></section>
        <section class="panel s5"><div class="panel-h"><h2>Big Data benchmark</h2><span>pandas vs Apache Spark</span></div>${h.benchmark ? `<div class="chart-box" style="height:260px"><canvas id="bench"></canvas></div><p class="note" style="margin-top:10px">${benchNote(h.benchmark)}</p>` : '<p class="note">Spark benchmark results will appear here after the Colab run.</p>'}</section>
        <section class="panel s12"><div class="panel-h"><h2>Limitations</h2></div><ul class="bul">
          <li><b>YouTube only.</b> Instagram, TikTok and Facebook comments can't be collected within their terms.</li>
          <li><b>Missed sales is an estimate</b> from the assumptions (top bar), not a measured figure.</li>
          <li><b>Most comments are on creator videos,</b> so they show what shoppers ask, not how a brand's own page performs.</li>
          <li><b>Brand videos with huge views and few comments are likely paid promotion.</b> No share counts from the API.</li>
          <li><b>Roman Urdu spelling varies,</b> so some comments are missed or mis-tagged; about a third stay unlabelled.</li>
          <li><b>Patterns, not proof:</b> "prices shown → fewer price questions" is a correlation worth A/B testing.</li>
          <li><b>Small groups:</b> size questions (38) and complaints (73) are small samples.</li></ul>
          <div class="row-btns"><a class="btn ghost" href="${D.links.repo}" target="_blank" rel="noopener">Code on GitHub</a><a class="btn ghost" href="${D.links.streamlit}" target="_blank" rel="noopener">Analyst version (Streamlit)</a><a class="btn ghost" href="${D.links.p1}" target="_blank" rel="noopener">Project 1</a><a class="btn ghost" href="${D.links.p2}" target="_blank" rel="noopener">Project 2</a></div></section>
      </div></div>`;
  }
  function benchNote(b) {
    const big = Math.max(...b.map(r => r.rows));
    const pd = b.find(r => r.engine === "Pandas" && r.rows === big), sp = b.find(r => r.engine === "Spark" && r.rows === big);
    const agree = b.filter(r => r.engine === "Spark").every(r => Number(r.labels_agree_with_pandas) >= 0.9999);
    return `At ${fmt(big)} comments: pandas ${Math.round(pd.seconds)} s, Spark ${Math.round(sp.seconds)} s on a free 2-core Colab machine. `
      + `Both grow in a straight line with the data${agree ? " and give identical labels" : ""}. On one small machine Spark's start-up and coordination cost makes it slower; `
      + `it pays off on a cluster or once the data no longer fits in one computer's memory.`;
  }
  function drawHow() {
    if (!window.Chart) return;
    const groups = [...new Set(D.how.points.map(p => p.g))];
    const cols = ["#8B7BFF", "#FF7A59", "#3DD9A4", "#3D8BFF", "#E05BA8", "#FFC75A", "#14A3A3", "#C3BAFF", "#FF9DB0", "#87F0CA"];
    charts.push(new Chart($("#map"), {
      type: "scatter",
      data: { datasets: groups.map((g, i) => ({ label: g, data: D.how.points.filter(p => p.g === g).map(p => ({ x: p.x, y: p.y, t: p.t })), backgroundColor: cols[i % cols.length] + "B0", pointRadius: 2.6 })) },
      options: { maintainAspectRatio: false, plugins: { legend: { position: "right", labels: { color: "#A6A1CC", boxWidth: 8, boxHeight: 8, usePointStyle: true, font: { size: 11 } } }, tooltip: { callbacks: { label: c => c.raw.t } } },
        scales: { x: { display: false }, y: { display: false } } },
    }));
    if (D.how.benchmark && $("#bench")) {
      const b = D.how.benchmark, eng = [...new Set(b.map(r => r.engine))];
      charts.push(new Chart($("#bench"), {
        type: "line",
        data: { labels: [...new Set(b.map(r => r.rows))].map(fmt), datasets: eng.map((e, i) => ({ label: e, data: b.filter(r => r.engine === e).map(r => r.seconds), borderColor: ["#3D8BFF", "#FF7A59"][i], backgroundColor: ["#3D8BFF", "#FF7A59"][i], tension: .25 })) },
        options: { maintainAspectRatio: false, plugins: { legend: { labels: { color: "#A6A1CC" } } },
          scales: { x: { title: { display: true, text: "comments", color: "#77729F" }, ticks: { color: "#A6A1CC" }, grid: { display: false } }, y: { type: "logarithmic", title: { display: true, text: "seconds", color: "#77729F" }, ticks: { color: "#77729F" }, grid: { color: "rgba(255,255,255,.06)" } } } },
      }));
    }
  }

  /* ---------------- router ---------------- */
  const VIEWS = { today, inbox, customers, content, competitors, campaigns, report, how };
  function render() {
    const page = (location.hash.slice(1) || "today");
    const id = VIEWS[page] ? page : "today";
    charts.splice(0).forEach(c => c.destroy());
    nav(id);
    $("#view").innerHTML = VIEWS[id]();
    if (id === "today") countUp();
    if (id === "inbox") wireInbox();
    if (id === "customers") document.querySelectorAll("[data-seg]").forEach(b => b.onclick = () => { S.seg = b.dataset.seg; render(); $("#hear")?.scrollIntoView({ behavior: "smooth", block: "nearest" }); });
    if (id === "campaigns") document.querySelectorAll("[data-copy]").forEach(b => b.onclick = () => copy($("#" + b.dataset.copy).textContent));
    if (id === "competitors") drawCompetitors();
    if (id === "how") drawHow();
    if (id === "report") $("#print").onclick = () => window.print();
    document.title = `${PAGES.find(p => p.id === id).label} · Joota Pulse`;
  }

  function init(data) {
    D = data;
    if (!D.spaces[S.ws]) S.ws = "all";
    const sel = $("#ws-select");
    sel.innerHTML = `<option value="all">All brands (agency view)</option><option value="core">Core brands: Borjan, Servis, Ndure</option>` + D.brands.map(b => `<option value="${esc(b)}">${esc(b)}</option>`).join("");
    sel.value = S.ws;
    sel.onchange = () => { S.ws = sel.value; S.sel = null; S.seg = null; store.set("ws", S.ws); render(); };
    $("#src-sub").textContent = `${fmt(D.how.comments)} comments · ${D.date}`;
    const box = $("#assume"), btn = $("#assume-btn");
    btn.onclick = () => { box.hidden = !box.hidden; btn.setAttribute("aria-expanded", String(!box.hidden)); };
    $("#price").value = S.price; $("#conv").value = S.conv;
    $("#price").oninput = e => { S.price = Math.max(0, Number(e.target.value) || 0); store.set("price", S.price); render(); };
    $("#conv").oninput = e => { S.conv = Math.min(100, Math.max(0, Number(e.target.value) || 0)); store.set("conv", S.conv); render(); };
    window.addEventListener("hashchange", () => { render(); window.scrollTo(0, 0); });
    render();
  }

  fetch("data.json", { cache: "no-cache" }).then(r => r.json()).then(data => {
    try { init(data); } catch (e) { console.error(e); $("#view").innerHTML = `<div class="panel"><h2>Something went wrong</h2><p class="note">${esc(e.message)}</p></div>`; }
  }).catch(() => {
    $("#view").innerHTML = '<div class="panel"><h2>Couldn\'t load the data</h2><p class="note">Refresh the page. If you opened the file directly, open it through GitHub Pages instead.</p></div>';
  });
})();
