/* Core UI: state, sidebar filters, cards/KPIs/tables, detail modal. Tabs are in tabs_a.js and tabs_b.js, start-up in boot.js. */
(function () {
  'use strict';
  const D = window.DATA, L = window.L;
  const APP = (window.APP = { D, L, state: null, charts: [], tabs: {}, order: [] });
  APP.C = { scam: '#12324A', fake: '#0F766E', fakeL: '#A8DAD6', ai: '#7663A8', freedom: '#3565A8', global: '#138A8A', warn: '#C9841D', ink: '#172B3A', muted: '#657887', grid: '#DCE7ED', paper: '#F3F7FA', real: '#2C8A68', grey: '#657887', other: '#CBD5DD', blue: '#3565A8', orange: '#C9841D', teal: '#0F766E', purple: '#7663A8', alert: '#EAF5F4' };
  const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  APP.$ = $; APP.esc = esc;

  APP.state = { tab: 'overview', f: L.defaultFilters(D.meta), gran: 'month', notes: false, detail: 'afnc' };

  // ------------------------------------------------------------------ small builders
  APP.periodText = (dates) => { const d = dates.filter(Boolean).sort(); return d.length ? `${L.fmtDate(d[0])} → ${L.fmtDate(d[d.length - 1])}` : 'ไม่มีข้อมูลในช่วงที่เลือก'; };
  APP.empty = (msg) => `<div class="empty">${esc(msg)}</div>`;
  APP.scope = (key) => { const w = L.whyNot(key, APP.state.f); return w ? `<div class="scope">⚠ ${esc(w)}</div>` : ''; };

  APP.card = ({ id, title, unit, period, h = 320, desc = '', insight = '', span = false, src = '', extra = '', msg = '' }) => `
    <section class="card${span ? ' span2' : ''}"><h3>${esc(title)}</h3>
      ${msg ? APP.empty(msg) : `<div id="${id}" class="chart" style="height:${h}px"></div>`}
      <div class="cap">หน่วย: ${esc(unit)} · ช่วงเวลา: ${esc(period)}${src ? ' · แหล่ง: ' + esc(src) : ''}</div>
      ${desc ? `<p class="desc">${esc(desc)}</p>` : ''}${insight ? `<p class="insight">▸ ${esc(insight)}</p>` : ''}${extra}</section>`;

  APP.kpi = ({ key, label, value, sub, delta, color }) => {
    let d = '';
    if (delta !== undefined) d = delta === null ? '<div class="k-delta flat">เทียบช่วงก่อนหน้า: –</div>' : `<div class="k-delta ${delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat'}">${delta > 0 ? '▲' : delta < 0 ? '▼' : '■'} ${L.fmtNum(Math.abs(delta), 1)}% เทียบช่วงก่อนหน้า</div>`;
    return `<button class="kpi" data-kpi="${key}" style="--c:${color || '#7B1E3A'}"><div class="k-label">${esc(label)}</div><div class="k-value">${value}</div><div class="k-sub">${esc(sub)}</div>${d}</button>`;
  };

  APP.table = (cols, rows, opts = {}) => {
    const head = cols.map((c) => `<th class="${c.n ? 'n' : ''}">${esc(c.h)}</th>`).join('');
    const body = rows.slice(0, opts.max || 400).map((r) => `<tr class="${opts.hl && opts.hl(r) ? 'hl' : ''}">${cols.map((c) => `<td class="${c.n ? 'n' : ''}">${c.raw ? c.f(r) : esc(c.f(r))}</td>`).join('')}</tr>`).join('');
    const more = rows.length > (opts.max || 400) ? `<p class="hint">แสดง ${opts.max || 400} จาก ${L.fmtInt(rows.length)} แถว — ดาวน์โหลด CSV เพื่อดูทั้งหมด</p>` : '';
    return `<div class="tbl-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="${cols.length}">ไม่มีข้อมูลในช่วงที่เลือก</td></tr>`}</tbody></table></div>${more}`;
  };

  APP.csv = (name, cols, rows) => {
    const q = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const text = '﻿' + [cols.map((c) => q(c.h)).join(','), ...rows.map((r) => cols.map((c) => q(c.f(r))).join(','))].join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' })); a.download = name; a.click(); URL.revokeObjectURL(a.href);
  };

  // ------------------------------------------------------------------ charts
  APP.dispose = () => { APP.charts.forEach((c) => c.dispose()); APP.charts = []; };
  APP.mount = (id, option) => {
    const el = document.getElementById(id); if (!el || !window.echarts) return null;
    const c = echarts.init(el, null, { renderer: 'canvas' });
  c.setOption({ textStyle: { fontFamily: 'Noto Sans Thai, Sarabun, sans-serif', color: APP.C.ink }, animation: false, grid: { left: 52, right: 18, top: 34, bottom: 44, containLabel: true }, tooltip: { trigger: 'axis', confine: true }, toolbox: { right: 4, feature: { saveAsImage: { title: 'บันทึกรูป', pixelRatio: 2 } } }, ...option });
    APP.charts.push(c); return c;
  };
  window.addEventListener('resize', () => APP.charts.forEach((c) => c.resize()));

  // ------------------------------------------------------------------ modal
  APP.modal = (html) => { $('#modalBody').innerHTML = html; $('#modal').hidden = false; };
  $('#modalX').addEventListener('click', () => ($('#modal').hidden = true));
  $('#modal').addEventListener('click', (e) => { if (e.target.id === 'modal') $('#modal').hidden = true; });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') $('#modal').hidden = true; });

  /** Detail view behind a KPI / table: where the number comes from, how it was computed, and the rows (with CSV export). */
  APP.detail = ({ title, map, cols, rows, file }) => {
    const m = D.source_map.find((r) => r[0] === map);
    const src = m ? `<div class="note"><b>แหล่งที่มา:</b> ${esc(m[1])} · ไฟล์ <code>${esc(m[2])}</code> · คอลัมน์ ${esc(m[3])}<br><b>วิธีคำนวณ:</b> ${esc(m[4])}<br><b>ตัวกรองที่ใช้ได้:</b> ${esc(m[5])}</div>` : '';
    APP.modal(`<h3>${esc(title)}</h3>${src}<div class="row-tools"><button class="btn-ghost" id="dlCsv">⬇ ดาวน์โหลด CSV (${L.fmtInt(rows.length)} แถว)</button></div>${APP.table(cols, rows, { max: 300 })}`);
    $('#dlCsv').onclick = () => APP.csv(file || 'detail.csv', cols, rows);
  };

  // ------------------------------------------------------------------ sidebar
  const FOTN_COUNTRIES = [...new Map(D.fotn.map((r) => [r.iso3, r.country])).entries()].sort((a, b) => a[1].localeCompare(b[1]));
  const YEARS = Array.from({ length: +D.meta.date_max.slice(0, 4) - 2010 + 1 }, (_, i) => 2010 + i);
  const chip = (k, v, label, on) => `<button class="chip${on ? ' on' : ''}" data-k="${k}" data-v="${esc(v)}">${esc(label)}</button>`;

  APP.buildSidebar = () => {
    const f = APP.state.f, A = D.afnc;
    $('#sidebar').innerHTML = `
      <div class="f-group"><h4>ช่วงวันที่</h4>
        <div class="f-row"><label>จาก</label><input type="date" id="fFrom" min="${D.meta.date_min}" max="${D.meta.date_max}" value="${f.from}"></div>
        <div class="f-row"><label>ถึง</label><input type="date" id="fTo" min="${D.meta.date_min}" max="${D.meta.date_max}" value="${f.to}"></div></div>
      <div class="f-group"><h4>ปี</h4><div class="chips">${YEARS.map((y) => chip('years', y, y, f.years.includes(y))).join('')}</div><p class="hint">ไม่เลือก = ทุกปี</p></div>
      <div class="f-group"><h4>ไตรมาส</h4><div class="chips">${[1, 2, 3, 4].map((q) => chip('quarters', q, 'Q' + q, f.quarters.includes(q))).join('')}</div></div>
      <div class="f-group"><h4>เดือน</h4><div class="chips">${L.TH_MONTHS.map((m, i) => chip('months', i + 1, m, f.months.includes(i + 1))).join('')}</div></div>
      <div class="f-group"><h4>ประเทศไทย / ต่างประเทศ</h4><div class="chips">${Object.entries(L.REGIONS).map(([k, v]) => chip('region', k, v, f.region === k)).join('')}</div></div>
      <div class="f-group"><h4>กลุ่มประเทศ (Freedom on the Net)</h4><select id="fGroup">${D.meta.groups.map((g) => `<option${g === f.group ? ' selected' : ''}>${g}</option>`).join('')}</select>
        <input type="search" id="fCsearch" placeholder="ค้นหาประเทศ…" style="margin-top:8px"><div class="list" id="fCountries">${FOTN_COUNTRIES.map(([i, c]) => `<label data-name="${esc(c.toLowerCase())}"><input type="checkbox" data-country="${i}"${f.countries.includes(i) ? ' checked' : ''}>${esc(c)}</label>`).join('')}</div></div>
      <div class="f-group"><h4>ประเภทข่าว (AFNC)</h4><div class="chips">${A.cats.map((c) => chip('cats', c, c.replace(/\s*\(.*\)/, ''), f.cats.includes(c))).join('')}</div></div>
      <div class="f-group"><h4>สถานะข่าว</h4><div class="chips">${A.statuses.map((c) => chip('statuses', c, c, f.statuses.includes(c))).join('')}</div></div>
      <div class="f-group"><h4>หมวดหมู่ความเสียหาย</h4><div class="chips">${D.meta.damage_groups.map((c) => chip('damage', c, c, f.damage.includes(c))).join('')}</div><p class="hint">กรองตามประเภทที่เสียหายสูงสุดของสัปดาห์</p></div>
      <div class="f-group"><h4>แหล่งข้อมูล</h4>${Object.entries(L.SRC).map(([k, v]) => `<label class="f-row"><input type="checkbox" data-src="${k}"${f.sources.includes(k) ? ' checked' : ''}> ${esc(v)}</label>`).join('')}</div>`;
  };

  APP.renderFilterBar = () => {
    const f = APP.state.f, chips = L.chips(f, D.meta), notes = L.notes(f);
    $('#active-filters').innerHTML = (chips.length ? `<b>ตัวกรองที่ใช้อยู่:</b> ${chips.map((c) => `<span class="tag">${esc(c)}</span>`).join('')}` : '<b>ตัวกรอง:</b> <span class="tag">ไม่ได้กรอง (ข้อมูลทั้งหมด)</span>')
      + (notes.length ? `<div style="flex-basis:100%;color:#6b6670">ℹ ${notes.map(esc).join(' · ')}</div>` : '');
  };

  const sidebar = $('#sidebar');
  const toggle = (arr, v) => (arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v].sort((a, b) => (a > b ? 1 : -1)));
  sidebar.addEventListener('click', (e) => {
    const b = e.target.closest('.chip'); if (!b) return; const f = APP.state.f, k = b.dataset.k; let v = b.dataset.v;
    if (k === 'region') f.region = v; else { if (['years', 'quarters', 'months'].includes(k)) v = +v; f[k] = toggle(f[k], v); }
    b.closest('.chips').querySelectorAll('.chip').forEach((c) => c.classList.toggle('on', k === 'region' ? c.dataset.v === f.region : f[k].includes(['years', 'quarters', 'months'].includes(k) ? +c.dataset.v : c.dataset.v)));
    APP.refresh();
  });
  sidebar.addEventListener('change', (e) => {
    const f = APP.state.f, t = e.target;
    if (t.id === 'fFrom') f.from = t.value || D.meta.date_min; else if (t.id === 'fTo') f.to = t.value || D.meta.date_max;
    else if (t.id === 'fGroup') f.group = t.value;
    else if (t.dataset.country) f.countries = toggle(f.countries, t.dataset.country);
    else if (t.dataset.src) f.sources = Object.keys(L.SRC).filter((k) => (k === t.dataset.src ? t.checked : f.sources.includes(k)));
    else return;
    if (f.from > f.to) { const x = f.from; f.from = f.to; f.to = x; $('#fFrom').value = f.from; $('#fTo').value = f.to; }
    APP.refresh();
  });
  sidebar.addEventListener('input', (e) => {
    if (e.target.id !== 'fCsearch') return; const q = e.target.value.trim().toLowerCase();
    sidebar.querySelectorAll('#fCountries label').forEach((l) => (l.style.display = l.dataset.name.includes(q) ? '' : 'none'));
  });

  APP.resetFilters = () => { APP.state.f = L.defaultFilters(D.meta); APP.buildSidebar(); APP.refresh(); };

  // ------------------------------------------------------------------ routing / render
  APP.addTab = (id, label, fn) => { APP.tabs[id] = fn; APP.order.push([id, label]); };
  APP.buildTabs = () => {
    $('#tabs').innerHTML = APP.order.map(([id, label]) => `<button role="tab" data-tab="${id}" class="${id === APP.state.tab ? 'on' : ''}">${esc(label)}</button>`).join('');
  };
  APP.refresh = () => {
    APP.dispose(); APP.renderFilterBar();
    const view = $('#view'); let out;
    try { out = APP.tabs[APP.state.tab](); } catch (err) { console.error(err); out = { html: `<div class="warn">เกิดข้อผิดพลาดในการแสดงผล: ${esc(err.message)}</div>` }; }
    view.innerHTML = out.html;
    (out.after || []).forEach((fn) => { try { fn(); } catch (err) { console.error(err); } });
  };
  $('#tabs').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-tab]'); if (!b) return;
    APP.state.tab = b.dataset.tab; APP.buildTabs(); APP.refresh(); window.scrollTo({ top: 0 });
  });
  $('#view').addEventListener('click', (e) => {
    const k = e.target.closest('[data-kpi]'); if (k && APP.onKpi) return APP.onKpi(k.dataset.kpi);
    const d = e.target.closest('[data-detail]'); if (d) { APP.state.detail = d.dataset.detail; APP.refresh(); return; }
    const g = e.target.closest('[data-gran]'); if (g) { APP.state.gran = g.dataset.gran; APP.refresh(); }
    const s = e.target.closest('[data-set]'); if (s) { const [key, val] = s.dataset.set.split('='); APP.state[key] = val; APP.refresh(); }
  });
  $('#view').addEventListener('change', (e) => { const t = e.target; if (t.dataset && t.dataset.state) { APP.state[t.dataset.state] = t.value; APP.refresh(); } });
  $('#chkNotes').addEventListener('change', (e) => { document.body.classList.toggle('notes-on', e.target.checked); APP.state.notes = e.target.checked; });
  $('#btnReset').addEventListener('click', APP.resetFilters);
  $('#btnDrawer').addEventListener('click', () => document.body.classList.add('drawer'));
  $('#scrim').addEventListener('click', () => document.body.classList.remove('drawer'));
})();
