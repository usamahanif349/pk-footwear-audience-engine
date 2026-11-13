/* Joota Pulse web app. All numbers come from data.json, exported by src/web/export.py
   from real public YouTube comments. The browser only filters, formats and displays. */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = n => Number(n).toLocaleString("en-US");
  const pct = (x, d = 0) => (x * 100).toFixed(d) + "%";
  const store = {
    get(k, d) { try { const v = localStorage.getItem("jp_" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("jp_" + k, JSON.stringify(v)); } catch (e) { /* storage off */ } },
  };
  const charts = [];
  const CONTACT = "usamahanif349@gmail.com";

  const ICON = {
    start: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    today: '<path d="M3 12l9-8 9 8M5 10v10h5v-6h4v6h5V10"/>',
    inbox: '<path d="M3 13l3-8h12l3 8v6H3zM3 13h5l1 3h6l1-3h5"/>',
    customers: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.3-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><circle cx="17.5" cy="9" r="2.6"/><path d="M16 14.6c2.7.1 4.6 1.8 5.4 4.9"/>',
    content: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9.5v5l4.5-2.5z"/>',
    competitors: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    campaigns: '<path d="M4 14c4-1 6-3 8-9 2 6 4 8 8 9-4 1-6 3-8 9-2-6-4-8-8-9z"/>',
    digest: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    report: '<path d="M6 3h9l4 4v14H6zM14 3v5h5M9 13h7M9 17h5"/>',
    how: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 01-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 010-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 014 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 010 4h-.1a1.7 1.7 0 00-1.5 1z"/>',
    bell: '<path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 01-3.4 0"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    flame: '<path d="M12 22c4 0 7-2.7 7-7 0-4-3-6.5-4-10-2 2-2.5 4-2.5 5.5C11 9 10 7.5 10 5c-3 2.5-5 6-5 10 0 4.3 3 7 7 7z"/>',
    pin: '<path d="M12 22s7-6.2 7-12a7 7 0 10-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.6"/>',
    alert: '<path d="M10.3 3.9L2 18a2 2 0 001.7 3h16.6a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0zM12 9v4M12 17h.01"/>',
    video: '<rect x="2" y="6" width="14" height="12" rx="3"/><path d="M16 10l6-3v10l-6-3"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    rupee: '<path d="M6 4h12M6 9h12M9 4c6 0 6 10 0 10H6l8 7"/>',
    tag: '<path d="M20.6 13.4L13.4 20.6a2 2 0 01-2.8 0L3 13V3h10l7.6 7.6a2 2 0 010 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    truck: '<path d="M1 4h14v12H1zM15 9h4l3 3v4h-7"/><circle cx="5.5" cy="18.5" r="2"/><circle cx="18.5" cy="18.5" r="2"/>',
    phone: '<path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3.1 19.5 19.5 0 01-6-6A19.8 19.8 0 012.1 4.2 2 2 0 014.1 2h3a2 2 0 012 1.7c.1 1 .4 1.9.7 2.8a2 2 0 01-.5 2.1L8 9.9a16 16 0 006 6l1.3-1.3a2 2 0 012.1-.5c.9.3 1.8.6 2.8.7a2 2 0 011.7 2z"/>',
    ruler: '<path d="M3 17L17 3l4 4L7 21zM7 13l2 2M10 10l2 2M13 7l2 2"/>',
    lens: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5M8 11h6M11 8v6"/>',
    heart: '<path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 00-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 000-7.8z"/>',
    tv: '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M17 2l-5 5-5-5"/>',
    star: '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    up: '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
    down: '<path d="M3 7l6 6 4-4 8 8M15 17h6v-6"/>',
    share: '<path d="M4 12v8h16v-8M12 3v13M7 8l5-5 5 5"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  };
  const AICON = { "🔥": "flame", "📍": "pin", "⚠️": "alert", "🎬": "video", "💤": "clock" };
  const SICON = { "Where-can-I-buy askers": "pin", "Price checkers": "rupee", "Deal hunters": "tag", "Order & delivery askers": "truck",
    "Contact seekers": "phone", "Size & fit askers": "ruler", "Unhappy customers": "alert", "Quality-conscious shoppers": "lens",
    "Product fans": "heart", "Ad & meme crowd": "tv", "Supporters (general praise)": "star" };
  const segIcon = s => svg(SICON[s.name] || "customers");
  const alertIcon = a => svg(AICON[a.icon] || "bell");
  const svg = p => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[p]}</svg>`;
  const PAGES = [
    { grp: "Workspace" },
    { id: "today", label: "Today" }, { id: "inbox", label: "Leads inbox", count: true }, { id: "customers", label: "Your customers" },
    { id: "content", label: "Post this, not that" }, { id: "competitors", label: "Competitors" }, { id: "campaigns", label: "Campaign ideas" },
    { grp: "Share" }, { id: "digest", label: "Weekly digest" }, { id: "report", label: "Client report" },
    { grp: "About" }, { id: "start", label: "Switch brand" }, { id: "settings", label: "Settings" }, { id: "how", label: "How it works" },
  ];
  const TABS = ["today", "inbox", "customers", "campaigns", "report"];
  const TAB_LABEL = { today: "Today", inbox: "Leads", customers: "Customers", campaigns: "Ideas", report: "Report" };
  const PALETTE = ["#7B6CFF", "#FF7A59", "#2BB98A", "#3D8BFF", "#E05BA8", "#C9922E", "#14A3A3"];
  const colorOf = name => PALETTE[[...String(name)].reduce((a, c) => a + c.charCodeAt(0), 0) % PALETTE.length];
  const initials = name => String(name).replace(/Pakistan|Shoes/g, "").trim().split(/\s+/).map(w => w[0]).join("").slice(0, 2).toUpperCase() || "?";
  const avatar = (name, round) => `<div class="av ${round ? "round" : ""}" style="background:${colorOf(name)}">${esc(initials(name))}</div>`;

  let D, S = {
    ws: store.get("ws", null), price: store.get("price", 4500), conv: store.get("conv", 10), theme: store.get("theme", null),
    kind: "All", src: "Everywhere", q: "", sel: null, lang: store.get("lang", "ru"), link: store.get("link", "[shop link]"), seg: null,
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
  const copy = (text, msg = "Copied. Paste it on YouTube.") => {
    const done = () => toast(msg);
    const fallback = () => { const a = document.createElement("textarea"); a.value = text; document.body.appendChild(a); a.select(); try { document.execCommand("copy"); done(); } catch (e) { toast("Select the text and copy it"); } a.remove(); };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, fallback); else fallback();
  };
  const header = (title, sub, right = "") => `<div class="page-h"><div><h1>${title}</h1><p>${sub}</p></div>${right}</div>`;
  const hbars = rows => {
    const mx = Math.max(...rows.map(r => r.n), 1);
    return rows.map(r => `<div class="hbar"><div class="row">${r.icon ? `<i class="hic">${svg(r.icon)}</i>` : ""}${esc(r.label)}<span>${fmt(r.n)}</span></div><div class="track"><div class="fill ${r.hot ? "hot" : ""}" style="width:${(r.n / mx * 100).toFixed(0)}%"></div></div></div>`).join("");
  };
  const ago = iso => {
    const days = Math.round((Date.now() - new Date(iso + "T00:00:00").getTime()) / 864e5);
    return days <= 0 ? "today" : days === 1 ? "yesterday" : `${days} days ago`;
  };
  const sparkline = pts => {
    if (pts.length < 2) return "";
    const w = 160, h = 40, mx = Math.max(...pts), mn = Math.min(...pts), r = mx - mn || 1;
    const xy = pts.map((v, i) => `${(i / (pts.length - 1) * w).toFixed(1)},${(h - 4 - (v - mn) / r * (h - 8)).toFixed(1)}`).join(" ");
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><polyline points="${xy}" fill="none" stroke="#FF8A5B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  };
  const tagFor = ask => ask === "Complaint" ? "bad" : "hot";
  const scoreColor = s => s >= 70 ? "var(--mint)" : s >= 50 ? "var(--gold)" : "var(--rose)";
  const scoreWord = s => s >= 70 ? "Strong" : s >= 50 ? "Fair" : "Weak";
  const gauge = (score, size = 96) => {
    const r = 40, c = 2 * Math.PI * r, f = Math.max(score, 1) / 100 * c;
    return `<svg viewBox="0 0 100 100" style="width:${size}px;height:${size}px" aria-hidden="true"><circle cx="50" cy="50" r="${r}" fill="none" stroke="var(--s3)" stroke-width="10"/>
      <circle cx="50" cy="50" r="${r}" fill="none" stroke="${scoreColor(score)}" stroke-width="10" stroke-linecap="round" stroke-dasharray="${f.toFixed(1)} ${c.toFixed(1)}" transform="rotate(-90 50 50)"/></svg>`;
  };
  /* workspace health: one brand -> its score; several -> average, with best and worst */
  function health() {
    const h = W().health, list = Object.entries(h).map(([b, v]) => ({ brand: b, ...v }));
    if (list.length === 1) return { single: true, ...list[0] };
    const avg = Math.round(list.reduce((a, x) => a + x.score, 0) / list.length);
    const sorted = list.sort((a, b) => b.score - a.score);
    return { single: false, score: avg, best: sorted[0], worst: sorted[sorted.length - 1], n: list.length };
  }
  const chartTheme = () => {
    const cs = getComputedStyle(document.documentElement);
    return { text: cs.getPropertyValue("--muted").trim(), dim: cs.getPropertyValue("--dim").trim(), grid: cs.getPropertyValue("--line").trim() };
  };

  /* ---------------- shell ---------------- */
  function nav(active) {
    const w = W();
    $("#nav").innerHTML = PAGES.map(p => p.grp ? `<div class="grp">${p.grp}</div>` :
      `<a href="#${p.id}" class="${p.id === active ? "on" : ""}" ${p.id === active ? 'aria-current="page"' : ""}>${svg(p.id)}<span>${p.label}</span>${p.count && w ? `<span class="cnt">${fmt(w.waiting)}</span>` : ""}</a>`).join("");
    $("#tabbar").innerHTML = TABS.map(id => `<a href="#${id}" class="${id === active ? "on" : ""}">${svg(id)}<span>${TAB_LABEL[id]}</span>${id === "inbox" && w ? `<span class="cnt">${fmt(w.waiting)}</span>` : ""}</a>`).join("");
    $("#ws-av").textContent = !S.ws ? "?" : S.ws === "all" ? "A" : S.ws === "core" ? "3" : initials(S.ws);
    $("#ws-av").style.background = S.ws && D.spaces[S.ws] && D.spaces[S.ws].brands.length === 1 ? colorOf(S.ws) : "";
    $("#ws-select").value = S.ws || "all";
  }
  function setTheme(t) {
    S.theme = t;
    document.documentElement.setAttribute("data-theme", t);
    $("#theme").innerHTML = svg(t === "light" ? "moon" : "sun");
    $("#theme").setAttribute("aria-label", t === "light" ? "Switch to dark mode" : "Switch to light mode");
  }

  /* ---------------- START: choose a brand ---------------- */
  function start() {
    const card = b => {
      const s = D.spaces[b], h = s.health[b];
      return `<button type="button" class="bcard" data-ws="${esc(b)}"><div class="h">${avatar(b)}<div><div class="nm">${esc(b)}</div><div class="sub">${fmt(s.comments)} comments · ${fmt(s.videos)} videos</div></div>
        <span class="tag ${h.score >= 70 ? "ok" : h.score >= 50 ? "warm" : "bad"}">Health ${h.score}</span></div>
        <div class="row"><div><b style="color:var(--coral)">${fmt(s.waiting)}</b>buyers waiting</div><div><b>${money(s.waiting)}</b>missed sales</div><div><b>#${h.rank}</b>of ${D.brands.length}</div></div></button>`;
    };
    const a = D.spaces.all;
    return `<div class="choose fade"><h1>Which brand are we looking at?</h1>
      <p>Pick a brand to open its workspace, or use the agency view to see all ${D.brands.length} brands together. You can switch any time.</p>
      <div class="brands">
        <button type="button" class="bcard agency" data-ws="all"><div class="h"><div class="av" style="background:linear-gradient(135deg,var(--violet-2),var(--coral))">All</div><div><div class="nm">Agency view: all ${D.brands.length} brands</div><div class="sub">${fmt(a.comments)} comments · ${fmt(a.videos)} videos</div></div><span class="tag cool">Recommended for agencies</span></div>
          <div class="row"><div><b style="color:var(--coral)">${fmt(a.waiting)}</b>buyers waiting</div><div><b>${money(a.waiting)}</b>missed sales</div><div><b>${fmt(a.people)}</b>people</div></div></button>
        ${D.brands.map(card).join("")}
      </div></div>`;
  }

  /* ---------------- TODAY ---------------- */
  function trendLine(w) {
    const hist = (D.history || []).map(h => h[S.ws]).filter(Boolean);
    if (hist.length < 2) return `<div class="sub" style="margin-top:4px">Live data · updated ${ago(D.updated)} · refreshes every week</div>`;
    return `<div class="trend">${sparkline(hist.map(h => h.waiting))}<span><b>${fmt(w.new_buyers)}</b> new buying question${w.new_buyers === 1 ? "" : "s"} posted since the last update · updated ${ago(D.updated)}</span></div>`;
  }
  function healthCard() {
    const h = health();
    const sub = h.single
      ? `#${h.rank} of ${D.brands.length} brands · ${scoreWord(h.score)} audience`
      : `average of ${h.n} brands · best ${esc(h.best.brand)} (${h.best.score}), weakest ${esc(h.worst.brand)} (${h.worst.score})`;
    return `<div class="stat"><div class="l">Brand health score <a class="info" href="#how" title="How is this calculated?">?</a></div>
      <div class="gauge" style="margin-top:8px">${gauge(h.score, 84)}<div><div class="score" style="color:${scoreColor(h.score)}">${h.score}<small> /100</small></div><div class="n">${sub}</div></div></div></div>`;
  }
  function today() {
    const w = W();
    const rate = w.own_q ? w.own_answered / w.own_q : null;
    const seen = new Set();
    const tick = inboxItems().filter(m => m.ask !== "Complaint" && m.text.length <= 60 && m.text.length >= 12 && !seen.has(m.text.toLowerCase()) && seen.add(m.text.toLowerCase())).slice(0, 24);
    const bubbles = tick.map(m => `<span class="bubble"><i>${esc(m.ask)}</i>${esc(m.text)}</span>`).join("");
    const pseen = new Set(), preview = inboxItems().filter(m => m.ask !== "Complaint" && m.text.length > 8 && m.text.length < 140 && !pseen.has(m.text.toLowerCase()) && pseen.add(m.text.toLowerCase())).slice(0, 3);
    const ready = w.segments.filter(s => s.tone === "hot").sort((a, b) => b.people - a.people).slice(0, 6);
    const city = w.cities[0];
    return `<div class="fade"><div class="grid">
      <section class="hero s8">
        <span class="kicker">● ${w.new_buyers ? `${fmt(w.new_buyers)} new buyer${w.new_buyers === 1 ? "" : "s"} since the last update` : "Sales slipping away right now"}</span>
        <div class="money" id="money" data-target="${w.waiting}">${money(w.waiting)}</div>
        <div class="line"><b>${fmt(w.waiting)} buyers</b> asked about price, stock or delivery. Nobody answered.</div>
        <div class="sub">${esc(w.label)} · ${fmt(w.buying)} buying questions in ${fmt(w.comments)} real YouTube comments · estimate at Rs ${fmt(S.price)} a pair, ${S.conv}% buying</div>
        ${trendLine(w)}
        <div class="cta"><a class="btn coral" href="#inbox">Answer them now</a><a class="btn ghost" href="#report">Get the client report</a></div>
        <div class="ticker" aria-label="Recent unanswered buyer comments"><div class="track">${bubbles}${bubbles}</div></div>
        <svg class="pulse" viewBox="0 0 1000 120" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="#8B7BFF" stop-opacity="0"/><stop offset=".5" stop-color="#8B7BFF"/><stop offset="1" stop-color="#FF7A59"/></linearGradient></defs><path d="M0 80 H260 L290 80 L310 40 L335 110 L360 20 L385 95 L405 80 H640 L665 80 L685 55 L705 100 L725 70 H1000"/></svg>
      </section>
      <div class="side-stats s4">
        ${healthCard()}
        <div class="stat bad"><div class="l">Your reply rate</div><div class="v">${rate === null ? "–" : pct(rate)}</div><div class="n">${w.own_q ? `${w.own_answered} of ${w.own_q} buying questions answered on your own videos` : "No buying questions on your own videos yet"}</div></div>
        <div class="stat good"><div class="l">Hottest city</div><div class="v">${city ? esc(city.city) : "–"}</div><div class="n">${city ? `${city.n} shoppers asked about ${esc(city.city)}` : "No city named yet"}</div></div>
      </div>

      <section class="panel s5"><div class="panel-h"><h2>Alerts</h2><span>${D.history && D.history.length > 1 ? "since the last update" : "last 30 days of data"}</span></div>
        ${w.alerts.map(a => `<a class="alert" href="#${a.go}"><div class="ic ${a.tone}">${alertIcon(a)}</div><p>${esc(a.text)}</p></a>`).join("") || '<p class="note">All quiet.</p>'}</section>
      <section class="panel s7"><div class="panel-h"><h2>Buyers waiting for you</h2><a class="more" href="#inbox">Open inbox (${fmt(w.waiting)})</a></div>
        ${preview.map(m => `<div class="msg">${avatar(m.brand, true)}<div><div class="meta"><b>${esc(m.brand)}</b>${m.new ? '<span class="tag new">New</span>' : ""}<span class="tag ${tagFor(m.ask)}">${esc(m.ask)}</span><span>${esc(m.where)}</span></div>
          <div class="txt">${esc(m.text)}</div><div class="rep"><b>Suggested reply:</b> ${esc(reply(m.need, m.brand)).slice(0, 120)}…</div></div><span class="note">${esc(m.date.slice(5))}</span></div>`).join("") || '<p class="note">No waiting buyers here.</p>'}</section>

      <section class="panel s7"><div class="panel-h"><h2>Do these 3 things today</h2><a class="more" href="#campaigns">All campaign ideas</a></div>
        ${w.campaigns.slice(0, 3).map(c => `<div class="camp"><div class="tags"><span class="tag ${c.impact.startsWith("High") ? "hot" : "warm"}">${c.impact}</span><span class="tag ok">${c.effort}</span><span class="tag cool">${esc(c.channel)}</span></div><h3>${esc(c.title)}</h3><p>${esc(c.do)}</p><div class="why">${esc(fillMoney(c.why))}</div></div>`).join("")}</section>
      <div class="s5" style="display:grid;gap:18px;align-content:start">
        <section class="panel"><div class="panel-h"><h2>Ready-to-buy customers</h2><a class="more" href="#customers">All groups</a></div>${hbars(ready.map(s => ({ label: s.name, icon: SICON[s.name], n: s.people, hot: true })))}</section>
        <section class="panel"><div class="panel-h"><h2>Creators to partner with</h2><a class="more" href="#content">See all</a></div>
          ${w.leads.slice(0, 3).map((l, i) => `<div class="lead"><span class="rk ${i === 0 ? "top" : ""}">${i + 1}</span>${avatar(l.channel, true)}<div><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.channel)}</a><div class="sub">${esc(l.brands)}</div></div><div class="n">${l.buyers}<small>buyers asked</small></div></div>`).join("") || '<p class="note">No creator videos for this brand.</p>'}</section>
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
    const hasNew = all.some(m => m.new);
    const kinds = ["All"].concat(hasNew ? ["New"] : [], ["Where to buy", "Price", "Order & delivery", "Size", "Contact", "Complaint"]);
    const count = k => k === "All" ? all.length : k === "New" ? all.filter(m => m.new).length : all.filter(m => m.ask === k).length;
    const items = all.filter(m => (S.kind === "All" || (S.kind === "New" ? m.new : m.ask === S.kind)) && (S.src === "Everywhere" || (S.src === "Your videos") === m.own)
      && (!S.q || m.text.toLowerCase().includes(S.q.toLowerCase())));
    if (!items.find(m => m.id === S.sel)) S.sel = items.length ? items[0].id : null;
    const m = items.find(x => x.id === S.sel);
    const rows = items.slice(0, 300).map(x => `<button class="irow ${x.id === S.sel ? "on" : ""}" data-id="${x.id}" type="button">${avatar(x.brand, true)}<div><div class="top"><b>${esc(x.brand)}</b><span>${esc(x.date)}</span></div><div class="t">${esc(x.text)}</div><div class="tags">${x.new ? '<span class="tag new">New</span>' : ""}<span class="tag ${tagFor(x.ask)}">${esc(x.ask)}</span><span class="tag grey">${esc(x.where)}</span></div></div></button>`).join("");
    return `<div class="fade">${header("Leads inbox", `${fmt(W().waiting)} buyers asked and are still waiting. Pick one, copy the reply, paste it on YouTube.`,
      `<div class="seg" role="group" aria-label="Source">${["Everywhere", "Your videos", "Creator videos"].map(s => `<button type="button" data-src="${s}" class="${S.src === s ? "on" : ""}">${s}</button>`).join("")}</div>`)}
      <div class="chips" role="group" aria-label="Type">${kinds.map(k => `<button type="button" class="chip ${S.kind === k ? "on" : ""}" data-kind="${k}">${k}<em>${count(k)}</em></button>`).join("")}</div>
      <div class="inbox">
        <section class="panel"><input class="search" id="q" type="search" placeholder="Search comments" value="${esc(S.q)}" aria-label="Search comments">
          <div class="ilist" id="ilist">${rows || '<p class="note">Nothing here. All answered.</p>'}</div>
          <div class="row-btns"><button class="btn ghost sm" id="export" type="button">Export leads (CSV)</button><span class="note" style="align-self:center">${fmt(items.length)} shown</span></div>
        </section>
        <section class="panel reply-pane">${m ? `
          <div class="panel-h"><h2>Reply</h2><div class="seg" role="group" aria-label="Language"><button type="button" data-lang="ru" class="${S.lang === "ru" ? "on" : ""}">Roman Urdu</button><button type="button" data-lang="en" class="${S.lang === "en" ? "on" : ""}">English</button></div></div>
          <div class="cmt"><small>${esc(m.brand)} · ${esc(m.where)} · ${esc(m.date)}</small>${esc(m.text)}</div>
          <div class="suggest"><small>SUGGESTED REPLY</small><span id="rtext">${esc(reply(m.need, m.brand))}</span></div>
          <label class="field">Your shop link<input id="link" value="${esc(S.link)}"></label>
          <div class="row-btns"><button class="btn primary" id="copy" type="button">Copy reply</button>${m.url ? `<a class="btn ghost" href="${esc(m.url)}" target="_blank" rel="noopener">Open the video</a>` : ""}</div>
          <p class="note" style="margin-top:12px">Fill in any ____ before posting. Sample wording written for this project.</p>` : '<p class="note">No message selected.</p>'}
        </section>
      </div></div>`;
  }
  function wireInbox() {
    $$("[data-kind]").forEach(b => b.onclick = () => { S.kind = b.dataset.kind; S.sel = null; render(); });
    $$("[data-src]").forEach(b => b.onclick = () => { S.src = b.dataset.src; S.sel = null; render(); });
    $$("[data-lang]").forEach(b => b.onclick = () => { S.lang = b.dataset.lang; store.set("lang", S.lang); render(); });
    $$(".irow").forEach(b => b.onclick = () => { S.sel = Number(b.dataset.id); const y = $("#ilist").scrollTop; render(); $("#ilist").scrollTop = y; });
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
        <div class="stat s3" style="border-color:var(--coral)"><div class="l">Ready to buy</div><div class="v" style="color:var(--coral)">${fmt(ready)}</div><div class="n">asked about price, stock, size, delivery, deals</div></div>
        <div class="stat s3 bad"><div class="l">Need care</div><div class="v">${fmt((w.segments.find(s => s.name === "Unhappy customers") || {}).people || 0)}</div><div class="n">complaints to fix</div></div>
        <div class="stat s3 good"><div class="l">Fans</div><div class="v">${fmt(w.segments.filter(s => s.badge === "Fans").reduce((a, s) => a + s.people, 0))}</div><div class="n">praise and love</div></div>
      </div>
      <div class="tiles">${w.segments.map(s => `<button type="button" class="tile ${s.name === S.seg ? "on" : ""}" data-seg="${esc(s.name)}"><div class="h"><span class="e">${segIcon(s)}</span><span class="tag ${s.tone}">${s.badge}</span></div><div class="nm">${esc(s.name)}</div><div class="big">${fmt(s.people)} <small>people</small></div><div class="q">${s.quote ? `“${esc(s.quote)}”` : ""}</div><div class="do"><b>Do:</b> ${esc(s.todo)}</div></button>`).join("")}</div>
      ${sel ? `<section class="panel" style="margin-top:18px" id="hear"><div class="panel-h"><h2><i class="hic">${segIcon(sel)}</i>${esc(sel.name)}: in their words</h2><span>${fmt(sel.comments)} comments</span></div>
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
        <section class="panel s6"><div class="panel-h"><h2><i class="hic ok">${svg("up")}</i>Post more of this</h2><span>most conversation per view</span></div>${w.post_more.map(c => card(c, "ok")).join("") || '<p class="note">Not enough videos.</p>'}</section>
        <section class="panel s6"><div class="panel-h"><h2><i class="hic bad">${svg("down")}</i>Less of this</h2><span>views without conversation</span></div>${w.post_less.map(c => card(c, "grey")).join("") || '<p class="note">Not enough videos.</p>'}</section>
        <section class="panel s6"><div class="panel-h"><h2>Creator leaderboard</h2><span>buyers asking on their videos</span></div>
          ${w.leads.slice(0, 8).map((l, i) => `<div class="lead"><span class="rk ${i < 3 ? "top" : ""}">${i + 1}</span>${avatar(l.channel, true)}<div><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.channel)}</a><div class="sub">${esc(l.brands)} · creator replies to ${pct(l.answered)}</div></div><div class="n">${l.buyers}<small>buyers asked</small></div></div>`).join("") || '<p class="note">No creator videos for this brand.</p>'}
          ${w.leads.length ? '<div class="row-btns"><button class="btn ghost sm" id="pitch" type="button">Copy a partnership message</button></div>' : ""}</section>
        <section class="panel s6"><div class="panel-h"><h2>Standout posts</h2><span>far ahead of similar posts</span></div>
          ${w.standouts.map(s => `<div class="pc"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title.slice(0, 80))}</a><div class="s">${esc(s.brand)} · ${esc(s.channel)} · ${fmt(s.views)} views</div><div class="w">${svg("up")}${esc(s.why)}</div></div>`).join("") || '<p class="note">No standout posts here.</p>'}</section>
      </div></div>`;
  }
  function wireContent() {
    const b = $("#pitch"); if (!b) return;
    b.onclick = () => {
      const w = W(), l = w.leads[0];
      copy(`Hi ${l.channel}! Your videos about ${l.brands.split(",")[0]} get lots of buyer questions (${l.buyers} viewers asked about price, sizes or where to buy). `
        + `We'd love to work together: we can send you a price list, size chart and an order link to pin under your next video. Interested?`, "Partnership message copied.");
    };
  }

  /* ---------------- COMPETITORS ---------------- */
  function competitors() {
    const mine = new Set(S.ws === "all" ? [] : W().brands);
    const mx = Math.max(...D.competitors.map(c => c.buying));
    const rows = [...D.competitors].sort((a, b) => b.health - a.health);
    return `<div class="fade">${header("Competitors", "Every brand's audience side by side, ranked by brand health. Your workspace is highlighted.")}
      <section class="panel"><div class="panel-h"><h2>Brand scorecard</h2><a class="more" href="#how">How health is calculated</a></div>
      <div class="scroll-x"><table class="tbl"><thead><tr><th>#</th><th>Brand</th><th>Health</th><th>Comments</th><th>Buying questions</th><th>Top ask</th><th>Replies on own videos</th><th>Fans</th><th>Complaints</th><th>Ad buzz</th></tr></thead><tbody>
      ${rows.map((c, i) => `<tr class="${mine.has(c.brand) ? "me" : ""}"><td>${i + 1}</td><td>${esc(c.brand)}</td><td><span class="score-pill" style="background:color-mix(in srgb, ${scoreColor(c.health)} 16%, transparent);color:${scoreColor(c.health)}">${c.health}</span></td><td>${fmt(c.comments)}</td><td>${pct(c.buying)}<span class="meter"><i style="width:${(c.buying / mx * 100).toFixed(0)}%"></i></span></td><td><span class="tag hot">${esc(c.top)}</span></td><td>${c.own_q ? `${c.own_answered} of ${c.own_q}` : "–"}</td><td>${pct(c.fans)}</td><td>${pct(c.complaints, 1)}</td><td>${pct(c.buzz)}</td></tr>`).join("")}
      </tbody></table></div></section>
      <section class="panel" style="margin-top:18px"><div class="panel-h"><h2>What each brand's customers ask about</h2><span>% of the brand's comments</span></div><div class="chart-box"><canvas id="cmp"></canvas></div></section></div>`;
  }
  function drawCompetitors() {
    if (!window.Chart) return;
    const t = chartTheme();
    const keys = ["Where to buy", "Price", "Sale", "Order & delivery", "Quality", "Complaints"];
    const cols = ["#8B7BFF", "#FF7A59", "#E05BA8", "#3D8BFF", "#2BB98A", "#FF5C7A"];
    charts.push(new Chart($("#cmp"), {
      type: "bar",
      data: { labels: D.competitors.map(c => c.brand), datasets: keys.map((k, i) => ({ label: k, data: D.competitors.map(c => c.mix[k]), backgroundColor: cols[i], borderRadius: 4, maxBarThickness: 16 })) },
      options: { maintainAspectRatio: false, plugins: { legend: { labels: { color: t.text, boxWidth: 10, boxHeight: 10, usePointStyle: true } }, tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.raw}%` } } },
        scales: { x: { ticks: { color: t.text }, grid: { display: false } }, y: { ticks: { color: t.dim, callback: v => v + "%" }, grid: { color: t.grid } } } },
    }));
  }

  /* ---------------- CAMPAIGNS ---------------- */
  function campaigns() {
    const cs = W().campaigns;
    return `<div class="fade">${header("Campaign ideas", "Smart suggestions built from your comments. Every idea shows the number behind it and comes with ready ad copy.")}
      <div class="grid">${cs.map((c, i) => `<section class="camp-card s6"><div class="tags"><span class="tag ${c.impact.startsWith("High") ? "hot" : c.impact.startsWith("Medium") ? "warm" : "grey"}">${c.impact}</span><span class="tag ok">${c.effort}</span><span class="tag cool">${esc(c.channel)}</span></div>
        <h3>${esc(c.title)}</h3><p>${esc(c.do)}</p><div class="why">Why: ${esc(fillMoney(c.why))}</div>
        <div class="copy"><div class="c"><div><small>ENGLISH</small><span id="en${i}">${esc(c.en)}</span></div><button class="btn ghost sm" data-copy="en${i}" type="button">Copy</button></div>
        <div class="c"><div><small>ROMAN URDU</small><span id="ru${i}">${esc(c.ru)}</span></div><button class="btn ghost sm" data-copy="ru${i}" type="button">Copy</button></div></div></section>`).join("")}</div>
      <section class="panel" style="margin-top:18px"><div class="panel-h"><h2>Plan the budget</h2></div><p class="note" style="font-size:.92rem">Project 2 splits the ad budget across Facebook, TikTok, Instagram, Google and YouTube for the same brands and writes ads around the same angles.</p><div class="row-btns"><a class="btn ghost" href="${D.links.p2app}" target="_blank" rel="noopener">Open the ad budget optimizer</a></div></section></div>`;
  }

  /* ---------------- WEEKLY DIGEST (email preview) ---------------- */
  function digestText(w) {
    const lines = [`Joota Pulse weekly digest: ${w.label}`, `Data updated ${D.date}`, "",
      `${w.waiting} buyers are waiting for a reply (about ${money(w.waiting)} in missed sales).`,
      `Brand health: ${health().score}/100. Reply rate on your own videos: ${w.own_q ? pct(w.own_answered / w.own_q) : "no data"}.`, "", "This week:"]
      .concat(w.alerts.map(a => `- ${a.text}`), ["", "Do these first:"], w.campaigns.slice(0, 3).map((c, i) => `${i + 1}. ${c.title}: ${c.do}`), ["", `Open the dashboard: ${location.href.split("#")[0]}`]);
    return lines.join("\n");
  }
  function digest() {
    const w = W(), h = health();
    const seen = new Set(), leads = inboxItems().filter(m => m.ask !== "Complaint" && m.text.length >= 8 && m.text.length < 120 && !seen.has(m.text.toLowerCase()) && seen.add(m.text.toLowerCase())).slice(0, 3);
    return `<div class="fade">${header("Weekly digest", "The email a brand's marketing team gets every Monday. Copy it or send it yourself.",
      `<div class="row-btns no-print" style="margin:0"><button class="btn ghost" id="dcopy" type="button">Copy as text</button><a class="btn primary" id="dmail" href="#">Send by email</a></div>`)}
      <div class="mail"><div class="bar"><i></i><i></i><i></i></div>
        <div class="hd"><div><b>From:</b> Joota Pulse &lt;digest@jootapulse&gt;</div><div><b>To:</b> marketing team, ${esc(w.label)}</div><div><b>Subject:</b> ${fmt(w.waiting)} buyers are waiting for your reply</div></div>
        <div class="bd"><h2>Good morning! Here's your week on YouTube.</h2>
          <div class="kpis"><div class="kpi"><b style="color:var(--coral)">${money(w.waiting)}</b><span>missed sales (estimate)</span></div><div class="kpi"><b>${fmt(w.waiting)}</b><span>buyers waiting</span></div><div class="kpi"><b style="color:${scoreColor(h.score)}">${h.score}/100</b><span>brand health</span></div></div>
          <h3>What happened</h3>${w.alerts.map(a => `<div class="alert"><div class="ic ${a.tone}">${alertIcon(a)}</div><p>${esc(a.text)}</p></div>`).join("")}
          <h3>Answer these first</h3>${leads.map(m => `<div class="msg">${avatar(m.brand, true)}<div><div class="meta"><b>${esc(m.brand)}</b><span class="tag ${tagFor(m.ask)}">${esc(m.ask)}</span></div><div class="txt">${esc(m.text)}</div></div><span></span></div>`).join("")}
          <h3>Your 3 actions</h3>${w.campaigns.slice(0, 3).map((c, i) => `<div class="kv"><span><b>${i + 1}. ${esc(c.title)}</b><br><span class="note">${esc(c.do)}</span></span></div>`).join("")}
          <div class="row-btns"><a class="btn primary" href="#inbox">Open the leads inbox</a></div></div></div></div>`;
  }

  /* ---------------- REPORT ---------------- */
  function report() {
    const w = W(), h = health();
    const rate = w.own_q ? pct(w.own_answered / w.own_q) : "–";
    const segs = w.segments.filter(s => s.tone === "hot" || s.tone === "bad").sort((a, b) => b.people - a.people).slice(0, 5);
    return `<div class="fade">${header("Client report", "A one-page snapshot to send to the brand. Switch the workspace to make one for a single brand.",
      `<div class="row-btns no-print" style="margin:0">${W().brands.length === 1 ? `<a class="btn ghost" href="audit.html?brand=${encodeURIComponent(W().brands[0])}" target="_blank" rel="noopener">${svg("share")}Open the shareable audit</a>` : ""}<button class="btn primary" id="print" type="button">Download PDF</button></div>`)}
      <article class="sheet"><div class="hd"><small>JOOTA PULSE · AUDIENCE INTELLIGENCE</small><h2>Client snapshot: ${esc(w.label)}</h2><p>Based on ${fmt(w.comments)} real public YouTube comments · data updated ${esc(D.date)}</p></div>
      <div class="bd"><div class="k4">
        <div class="k"><div class="l">Missed sales (estimate)</div><div class="v">${money(w.waiting)}</div><div class="n">${fmt(w.waiting)} buyers waiting</div></div>
        <div class="k"><div class="l">Brand health</div><div class="v">${h.score}/100</div><div class="n">${h.single ? `#${h.rank} of ${D.brands.length} brands` : `average of ${h.n} brands`}</div></div>
        <div class="k"><div class="l">Reply rate, own videos</div><div class="v">${rate}</div><div class="n">${w.own_answered} of ${w.own_q} answered</div></div>
        <div class="k"><div class="l">Hottest city</div><div class="v">${w.cities[0] ? esc(w.cities[0].city) : "–"}</div><div class="n">${w.cities[0] ? w.cities[0].n + " mentions" : ""}</div></div></div>
        <h3>Do these first</h3>${w.campaigns.slice(0, 3).map((c, i) => `<div class="act"><i>${i + 1}</i><div><b>${esc(c.title)}: ${esc(c.do)}</b><span>${esc(fillMoney(c.why))}</span></div></div>`).join("")}
        <div class="two"><div><h3>Who your customers are</h3>${segs.map(s => `<div class="li"><span>${esc(s.name)}</span><b>${fmt(s.people)}</b></div>`).join("")}</div>
        <div><h3>Where they are</h3>${w.cities.slice(0, 4).map(c => `<div class="li"><span>${esc(c.city)}</span><b>${c.n}</b></div>`).join("") || '<p class="note">No cities named.</p>'}
        <h3>Creators to partner with</h3>${w.leads.slice(0, 3).map(l => `<div class="li"><span>${esc(l.channel)}</span><b>${l.buyers} buyers</b></div>`).join("") || '<p class="note">None.</p>'}</div></div>
        <div class="ft">Missed sales = unanswered buying questions × ${S.conv}% who would buy × Rs ${fmt(S.price)} per pair; an estimate, not a measured figure. Brand health = buying interest (40%), few complaints (35%) and fans (25%), each relative to the other brands. Source: public YouTube comments via the official YouTube Data API; commenter names removed. ${esc(D.links.repo)}</div>
      </div></article></div>`;
  }

  /* ---------------- HOW ---------------- */
  function how() {
    const h = D.how, m = h.metrics;
    return `<div class="fade">${header("How it works", "The engine behind the app: real data, a multilingual AI model and checks on every step.")}
      <div class="grid">
        <section class="panel s6"><div class="panel-h"><h2>The pipeline</h2></div><div class="steps">
          <div class="step"><div><b>Collect</b><span>Official YouTube Data API, every week: brand channels plus creators' sale vlogs and reviews. Latest run (${esc(D.date)}): ${fmt(D.pipeline.videos_kept)} videos and ${fmt(D.pipeline.comments_raw)} comments collected.</span></div></div>
          <div class="step"><div><b>Clean</b><span>Keep videos that name the brand; drop Indian and foreign videos (Bata's channel is Bata India, so Bata is out), foreign-language and empty comments. ${fmt(h.comments)} comments on ${fmt(h.videos)} videos about ${D.brands.length} brands remain.</span></div></div>
          <div class="step"><div><b>Protect</b><span>Commenter names never stored; phone numbers, e-mails, @handles and order numbers removed.</span></div></div>
          <div class="step"><div><b>Understand</b><span>Word lists in English, Roman Urdu and Urdu tag clear needs; a multilingual AI embedding model tags similar comments the lists miss.</span></div></div>
          <div class="step"><div><b>Group</b><span>K-Means finds topic clusters; every person is placed in one customer group.</span></div></div>
          <div class="step"><div><b>Compare and flag</b><span>Attention per video; unusual posts by peer z-scores and an Isolation Forest.</span></div></div>
          <div class="step"><div><b>Act</b><span>Rules turn the numbers into leads, alerts, campaign ideas, replies, the digest and the client report.</span></div></div></div></section>
        <section class="panel s6"><div class="panel-h"><h2>Brand health score</h2></div>
          <p class="note" style="font-size:.92rem">A 0–100 score for how strong a brand's YouTube audience is, comparable across brands:</p>
          <div class="kv"><span>Buying interest: share of comments that are buying questions, vs the best brand</span><b>40%</b></div>
          <div class="kv"><span>Few complaints: complaint share, vs the brand with the most</span><b>35%</b></div>
          <div class="kv"><span>Fans: share of praise comments, vs the best brand</span><b>25%</b></div>
          <p class="note" style="margin-top:10px">The reply rate is shown next to the score, not inside it: some brands have no buying questions on their own videos, so mixing it in would reward brands for having no channel. 70+ is strong, 50–69 fair, under 50 weak.</p>
          <div class="panel-h" style="margin-top:20px"><h2>Accuracy checks</h2></div>
          <div class="kv"><span>Comments tagged by word lists</span><b>${fmt(m.labelled_by_word_list)}</b></div>
          <div class="kv"><span>Tagged by the AI model (nearest neighbours)</span><b>${fmt(m.labelled_by_neighbours)}</b></div>
          <div class="kv"><span>AI tagging check (5-fold accuracy)</span><b>${pct(m.knn_cv_accuracy)}</b></div>
          <div class="kv"><span>Cluster–need match: AI embeddings vs word counts (NMI)</span><b>${m.nmi_embeddings_vs_needs.toFixed(2)} vs ${m.nmi_tfidf_vs_needs.toFixed(2)}</b></div></section>
        <section class="panel s7"><div class="panel-h"><h2>Comments mapped by meaning</h2><span>1,500 sample comments</span></div><div class="chart-box"><canvas id="map"></canvas></div></section>
        <section class="panel s5"><div class="panel-h"><h2>Big Data benchmark</h2><span>pandas vs Apache Spark</span></div>${h.benchmark ? `<div class="chart-box" style="height:260px"><canvas id="bench"></canvas></div><p class="note" style="margin-top:10px">${benchNote(h.benchmark)}</p>` : '<p class="note">Spark benchmark results will appear here after the Colab run.</p>'}</section>
        <section class="panel s12"><div class="panel-h"><h2>Limitations</h2></div><ul class="bul">
          <li><b>YouTube only.</b> Instagram, TikTok and Facebook comments can't be collected within their terms.</li>
          <li><b>Missed sales is an estimate</b> from the assumptions (top bar), not a measured figure.</li>
          <li><b>Most comments are on creator videos,</b> so they show what shoppers ask, not how a brand's own page performs.</li>
          <li><b>Brand videos with huge views and few comments are likely paid promotion.</b> No share counts from the API.</li>
          <li><b>Roman Urdu spelling varies,</b> so some comments are missed or mis-tagged; ${pct(D.limits.unlabelled)} stay unlabelled.</li>
          <li><b>Patterns, not proof:</b> "prices shown → fewer price questions" is a correlation worth A/B testing.</li>
          <li><b>Small groups:</b> size questions (${fmt(D.limits.size_q)}) and complaints (${fmt(D.limits.complaints)}) are small samples.</li></ul>
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
    const t = chartTheme();
    const groups = [...new Set(D.how.points.map(p => p.g))];
    const cols = ["#8B7BFF", "#FF7A59", "#2BB98A", "#3D8BFF", "#E05BA8", "#E0A030", "#14A3A3", "#A99BFF", "#FF9DB0", "#5CC8A0"];
    charts.push(new Chart($("#map"), {
      type: "scatter",
      data: { datasets: groups.map((g, i) => ({ label: g, data: D.how.points.filter(p => p.g === g).map(p => ({ x: p.x, y: p.y, t: p.t })), backgroundColor: cols[i % cols.length] + "B0", pointRadius: 2.6 })) },
      options: { maintainAspectRatio: false, plugins: { legend: { position: "right", labels: { color: t.text, boxWidth: 8, boxHeight: 8, usePointStyle: true, font: { size: 11 } } }, tooltip: { callbacks: { label: c => c.raw.t } } },
        scales: { x: { display: false }, y: { display: false } } },
    }));
    if (D.how.benchmark && $("#bench")) {
      const b = D.how.benchmark, eng = [...new Set(b.map(r => r.engine))];
      charts.push(new Chart($("#bench"), {
        type: "line",
        data: { labels: [...new Set(b.map(r => r.rows))].map(fmt), datasets: eng.map((e, i) => ({ label: e, data: b.filter(r => r.engine === e).map(r => r.seconds), borderColor: ["#3D8BFF", "#FF7A59"][i], backgroundColor: ["#3D8BFF", "#FF7A59"][i], tension: .25 })) },
        options: { maintainAspectRatio: false, plugins: { legend: { labels: { color: t.text } } },
          scales: { x: { title: { display: true, text: "comments", color: t.dim }, ticks: { color: t.text }, grid: { display: false } }, y: { type: "logarithmic", title: { display: true, text: "seconds", color: t.dim }, ticks: { color: t.dim }, grid: { color: t.grid } } } },
      }));
    }
  }

  /* ---------------- SETTINGS ---------------- */
  function settings() {
    return `<div class="fade">${header("Settings", "Your brand details. Saved in this browser and used across the app.")}
      <div class="grid">
        <section class="panel s7"><div class="panel-h"><h2>Brand</h2></div>
          <label class="field">Workspace<select id="set-ws">${["all", "core"].concat(D.brands).map(k => `<option value="${esc(k)}" ${k === S.ws ? "selected" : ""}>${esc(D.spaces[k].label)}</option>`).join("")}</select></label>
          <label class="field">Shop or order link (goes into every reply)<input id="set-link" value="${esc(S.link)}" placeholder="https://yourbrand.pk"></label>
          <label class="field">Reply language<select id="set-lang"><option value="ru" ${S.lang === "ru" ? "selected" : ""}>Roman Urdu</option><option value="en" ${S.lang === "en" ? "selected" : ""}>English</option></select></label>
        </section>
        <section class="panel s5"><div class="panel-h"><h2>Missed-sales estimate</h2></div>
          <label class="field">Average pair price (Rs)<input id="set-price" type="number" min="500" max="30000" step="500" value="${S.price}"></label>
          <label class="field">Askers who'd buy if answered (%)<input id="set-conv" type="number" min="1" max="50" value="${S.conv}"></label>
          <p class="note">Missed sales = unanswered buying questions × this share × the pair price.</p></section>
        <section class="panel s7"><div class="panel-h"><h2>Appearance</h2></div>
          <div class="seg" role="group" aria-label="Theme"><button type="button" data-th="dark" class="${S.theme !== "light" ? "on" : ""}">Dark</button><button type="button" data-th="light" class="${S.theme === "light" ? "on" : ""}">Light</button></div></section>
        <section class="panel s5"><div class="panel-h"><h2>Data</h2></div>
          <div class="kv"><span>Last update</span><b>${esc(D.date)}</b></div><div class="kv"><span>Next update</span><b>Every Monday</b></div><div class="kv"><span>Source</span><b>YouTube Data API</b></div></section>
      </div></div>`;
  }
  function wireSettings() {
    $("#set-ws").onchange = e => choose(e.target.value, "settings");
    $("#set-link").oninput = e => { S.link = e.target.value; store.set("link", S.link); };
    $("#set-lang").onchange = e => { S.lang = e.target.value; store.set("lang", S.lang); toast("Saved."); };
    $("#set-price").oninput = e => { S.price = Math.max(0, Number(e.target.value) || 0); store.set("price", S.price); $("#price").value = S.price; };
    $("#set-conv").oninput = e => { S.conv = Math.min(100, Math.max(0, Number(e.target.value) || 0)); store.set("conv", S.conv); $("#conv").value = S.conv; };
    $$("[data-th]").forEach(b => b.onclick = () => { setTheme(b.dataset.th); store.set("theme", S.theme); render(); });
  }

  /* ---------------- notifications bell ---------------- */
  function bell() {
    if (!S.ws) { $("#bell").hidden = true; return; }
    $("#bell").hidden = false;
    const w = W(), seen = store.get("seen", {})[S.ws] === D.updated;
    $("#bell-n").textContent = w.alerts.length; $("#bell-n").hidden = seen || !w.alerts.length;
    $("#bell-pop").innerHTML = `<div class="pop-h"><b>Alerts</b><span>${esc(w.label)} · ${esc(D.date)}</span></div>`
      + (w.alerts.map(a => `<a class="alert" href="#${a.go}"><div class="ic ${a.tone}">${alertIcon(a)}</div><p>${esc(a.text)}</p></a>`).join("") || '<p class="note">All quiet this week.</p>')
      + `<a class="pop-f" href="#digest">Open the weekly digest ${svg("arrow")}</a>`;
  }
  function wireBell() {
    const btn = $("#bell"), pop = $("#bell-pop");
    btn.onclick = e => {
      e.stopPropagation(); pop.hidden = !pop.hidden; btn.setAttribute("aria-expanded", String(!pop.hidden));
      if (!pop.hidden) { const sn = store.get("seen", {}); sn[S.ws] = D.updated; store.set("seen", sn); $("#bell-n").hidden = true; }
    };
    pop.onclick = e => { if (e.target.closest("a")) pop.hidden = true; };
    document.addEventListener("click", e => { if (!pop.hidden && !pop.contains(e.target) && e.target !== btn) pop.hidden = true; });
  }

  /* ---------------- Ctrl+K command palette ---------------- */
  let cmdSel = 0;
  function cmdItems(q) {
    const pages = PAGES.filter(p => p.id).map(p => ({ kind: "Page", label: p.label, icon: p.id, run: () => { location.hash = p.id; } }));
    const brands = ["all", "core"].concat(D.brands).map(k => ({ kind: "Workspace", label: D.spaces[k].label, icon: "customers", run: () => choose(k) }));
    const acts = [
      { kind: "Action", label: S.theme === "light" ? "Switch to dark mode" : "Switch to light mode", icon: S.theme === "light" ? "moon" : "sun", run: () => { setTheme(S.theme === "light" ? "dark" : "light"); store.set("theme", S.theme); render(); } },
      { kind: "Action", label: "Copy the weekly digest", icon: "digest", run: () => S.ws && copy(digestText(W()), "Digest copied.") },
      { kind: "Action", label: "Download the client report (PDF)", icon: "report", run: () => { location.hash = "report"; setTimeout(() => window.print(), 400); } },
    ];
    const all = (S.ws ? pages : []).concat(brands, acts), t = q.trim().toLowerCase();
    if (!t) return all;
    const hit = all.filter(i => (i.label + " " + i.kind).toLowerCase().includes(t));
    return hit.filter(i => i.label.toLowerCase().startsWith(t)).concat(hit.filter(i => !i.label.toLowerCase().startsWith(t)));
  }
  function openCmd() {
    const box = $("#cmdk"); box.hidden = false; cmdSel = 0;
    const inp = $("#cmdk-q"); inp.value = ""; drawCmd(); inp.focus();
  }
  function closeCmd() { $("#cmdk").hidden = true; }
  function drawCmd() {
    const items = cmdItems($("#cmdk-q").value); cmdSel = Math.min(cmdSel, Math.max(items.length - 1, 0));
    $("#cmdk-list").innerHTML = items.map((it, i) => `<button type="button" class="ci ${i === cmdSel ? "on" : ""}" data-i="${i}">${svg(it.icon)}<span>${esc(it.label)}</span><em>${it.kind}</em></button>`).join("") || '<p class="note" style="padding:14px">No results.</p>';
    $$("#cmdk-list .ci").forEach(b => { b.onclick = () => { closeCmd(); items[Number(b.dataset.i)].run(); }; b.onmousemove = () => { if (cmdSel !== Number(b.dataset.i)) { cmdSel = Number(b.dataset.i); drawCmd(); } }; });
    $("#cmdk-list .ci.on")?.scrollIntoView({ block: "nearest" });
    return items;
  }
  function wireCmd() {
    $("#cmd-btn").onclick = openCmd;
    $("#cmdk").onclick = e => { if (e.target.id === "cmdk") closeCmd(); };
    $("#cmdk-q").oninput = () => { cmdSel = 0; drawCmd(); };
    $("#cmdk-q").onkeydown = e => {
      const items = cmdItems($("#cmdk-q").value);
      if (e.key === "ArrowDown") { cmdSel = (cmdSel + 1) % Math.max(items.length, 1); drawCmd(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { cmdSel = (cmdSel - 1 + items.length) % Math.max(items.length, 1); drawCmd(); e.preventDefault(); }
      else if (e.key === "Enter" && items[cmdSel]) { closeCmd(); items[cmdSel].run(); }
    };
    document.addEventListener("keydown", e => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); $("#cmdk").hidden ? openCmd() : closeCmd(); }
      else if (e.key === "Escape") { closeCmd(); $("#bell-pop").hidden = true; }
    });
  }

  /* ---------------- router ---------------- */
  const VIEWS = { start, today, inbox, customers, content, competitors, campaigns, digest, report, how, settings };
  function render() {
    let id = location.hash.slice(1) || "today";
    if (!VIEWS[id]) id = "today";
    if (!S.ws && id !== "how" && id !== "settings") id = "start";
    if (!S.ws && id === "settings") id = "start";
    charts.splice(0).forEach(c => c.destroy());
    if (S.ws) nav(id); else { $("#nav").innerHTML = ""; $("#tabbar").innerHTML = ""; }
    $("#view").innerHTML = VIEWS[id]();
    if (id === "start") $$("[data-ws]").forEach(b => b.onclick = () => choose(b.dataset.ws));
    if (id === "today") countUp();
    if (id === "inbox") wireInbox();
    if (id === "customers") $$("[data-seg]").forEach(b => b.onclick = () => { S.seg = b.dataset.seg; render(); $("#hear")?.scrollIntoView({ behavior: "smooth", block: "nearest" }); });
    if (id === "content") wireContent();
    if (id === "campaigns") $$("[data-copy]").forEach(b => b.onclick = () => copy($("#" + b.dataset.copy).textContent, "Ad copy copied."));
    if (id === "competitors") drawCompetitors();
    if (id === "how") drawHow();
    if (id === "report") $("#print").onclick = () => window.print();
    if (id === "settings") wireSettings();
    bell();
    if (id === "digest") {
      const txt = digestText(W());
      $("#dcopy").onclick = () => copy(txt, "Digest copied.");
      $("#dmail").href = `mailto:?subject=${encodeURIComponent(`Joota Pulse: ${W().waiting} buyers are waiting for your reply`)}&body=${encodeURIComponent(txt)}`;
    }
    const page = PAGES.find(p => p.id === id);
    document.title = `${page ? page.label : "Choose a brand"} · Joota Pulse`;
  }
  function choose(ws, stay) {
    S.ws = ws; S.sel = null; S.seg = null; store.set("ws", ws);
    const to = "#" + (stay || "today");
    if (location.hash === to) render(); else location.hash = to;
    window.scrollTo(0, 0);
  }

  function init(data) {
    D = data;
    const qp = new URLSearchParams(location.search).get("brand");
    if (qp && D.spaces[qp]) { S.ws = qp; store.set("ws", qp); history.replaceState(null, "", location.pathname + (location.hash || "#today")); }
    if (S.ws && !D.spaces[S.ws]) S.ws = null;
    setTheme(S.theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"));
    $("#theme").onclick = () => { setTheme(S.theme === "light" ? "dark" : "light"); store.set("theme", S.theme); render(); };
    const sel = $("#ws-select");
    sel.innerHTML = `<option value="all">All brands (agency view)</option><option value="core">Core: Borjan, Servis, Ndure</option>` + D.brands.map(b => `<option value="${esc(b)}">${esc(b)}</option>`).join("");
    sel.onchange = () => choose(sel.value);
    $("#src-sub").textContent = `${fmt(D.how.comments)} comments · updated ${ago(D.updated)}`;
    const box = $("#assume"), btn = $("#assume-btn");
    btn.onclick = () => { box.hidden = !box.hidden; btn.setAttribute("aria-expanded", String(!box.hidden)); };
    $("#price").value = S.price; $("#conv").value = S.conv;
    $("#price").oninput = e => { S.price = Math.max(0, Number(e.target.value) || 0); store.set("price", S.price); render(); };
    $("#conv").oninput = e => { S.conv = Math.min(100, Math.max(0, Number(e.target.value) || 0)); store.set("conv", S.conv); render(); };
    window.addEventListener("hashchange", () => { render(); window.scrollTo(0, 0); });
    wireBell(); wireCmd();
    $("#cmd-btn").querySelector("kbd").textContent = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘K" : "Ctrl K";
    render();
  }

  fetch("data.json", { cache: "no-cache" }).then(r => r.json()).then(data => {
    try { init(data); } catch (e) { console.error(e); $("#view").innerHTML = `<div class="panel"><h2>Something went wrong</h2><p class="note">${esc(e.message)}</p></div>`; }
  }).catch(() => {
    $("#view").innerHTML = '<div class="panel"><h2>Couldn\'t load the data</h2><p class="note">Refresh the page. If you opened the file directly, open it through GitHub Pages instead.</p></div>';
  });
})();
