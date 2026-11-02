/* Tabs 1-3: Overview, Disinformation & Fake News, Internet Freedom & Country Comparison. */
(function () {
  'use strict';
  const { D, L, C, esc, card, kpi, table, mount, empty, scope, periodText } = APP;
  const A = D.afnc, E = D.eu, VI = A.itypes.indexOf('Verdict');
  const ST = { fake: 0, dist: 1, real: 2, other: 3 };
  const STC = [C.fake, C.fakeL, C.real, C.other];
  const GRAN = { month: 'รายเดือน', quarter: 'รายไตรมาส', year: 'รายปี' };
  const F = () => APP.state.f;
  const ctx = (f = F()) => ({ f, ai: L.afncIdx(D, f), wk: L.weeklyRows(D, f), eu: L.euIdx(D, f), ac: L.aiidRows(D, f), fo: L.fotnRows(D, f) });
  APP.ctx = ctx;

  // ------------------------------------------------------------------ shared aggregations
  const verdictIdx = (ai) => ai.filter((i) => A.it[i] === VI);
  const statusCounts = (ai) => { const c = [0, 0, 0, 0]; for (const i of ai) c[A.st[i]]++; return c; };
  const byPeriod = (ai, gran) => {
    const m = new Map();
    for (const i of ai) { const k = L.periodKey(A.d[i], gran); if (!m.has(k)) m.set(k, [0, 0, 0, 0]); m.get(k)[A.st[i]]++; }
    return [...m.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1));
  };
  const usableLoss = (wk) => L.sum(L.usable(wk).map((w) => w.loss));
  const latestFotn = (rows) => { const y = rows.length ? Math.max(...rows.map((r) => r.y)) : null; return { y, rows: rows.filter((r) => r.y === y) }; };
  const median = (a) => { const s = [...a].sort((x, y) => x - y), n = s.length; return n ? (n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2) : null; };
  APP.helpers = { verdictIdx, statusCounts, byPeriod, usableLoss, latestFotn, median, GRAN, STC, ST };

  const granSwitch = () => `<div class="seg">${Object.entries(GRAN).map(([k, v]) => `<button data-gran="${k}" class="${APP.state.gran === k ? 'on' : ''}">${v}</button>`).join('')}</div>`;
  const colorOf = (i) => STC[i];

  // ================================================================== 1. Overview
  function overview() {
    const x = ctx(), after = [], w = D.weekly;
    const usable = L.usable(w), latest = usable[usable.length - 1];
    const lastDate = D.weekly[D.weekly.length - 1]?.ws;
    const recent = D.weekly.filter((r) => r.ws > L.addDays(lastDate, -28));
    const recentVd = L.sum(recent.map((r) => r.vd));
    const falsePct = recentVd ? 100 * L.sum(recent.map((r) => r.fake + r.dist)) / recentVd : null;
    const cards = [
      kpi({ key: 'cases', label: `คดีออนไลน์ สัปดาห์ ${latest?.ws || '–'}`, value: latest ? L.fmtInt(latest.cases) : '–', sub: 'คดีที่มีการแถลงและผ่านการตรวจข้อมูล' }),
      kpi({ key: 'loss', label: 'ความเสียหายสัปดาห์นั้น', value: latest ? L.fmtMB(latest.loss) : '–', sub: latest?.rnd ? 'ยอดที่แถลงปัดเป็นล้านบาท' : 'ACSC' }),
      kpi({ key: 'lpc', label: 'ความเสียหายต่อคดี', value: latest?.cases ? `${L.fmtInt(latest.loss / latest.cases)} บาท` : '–', sub: 'คำนวณจากยอดรวม ÷ จำนวนคดี' }),
      kpi({ key: 'fake', label: 'สัดส่วนข่าวเท็จ 4 สัปดาห์ล่าสุด', value: falsePct === null ? '–' : `${L.fmtNum(falsePct, 1)}%`, sub: 'ข่าวปลอม + ข่าวบิดเบือน ในคำตัดสิน AFNC' }),
      kpi({ key: 'aiid', label: 'เหตุการณ์ AI ในฐานข้อมูลโลก', value: L.fmtInt(D.meta.n_aiid_incidents), sub: `AI Incident Database · ฉบับ ${D.meta.aiid_snapshot}`, color: C.purple }),
    ].join('');
    const plotStart = w.find((r) => r.rep || r.sus)?.ws;
    const plot = plotStart ? w.filter((r) => r.ws >= plotStart) : [];
    const findings = D.analysis.findings;
    const picks = [findings.q1[0], findings.q2[0], findings.q3[0], findings.q1[1], findings.q2[1], findings.q3[1]].filter(Boolean);
    const html = `<h2 class="sec">ภาพรวม</h2><div class="kpis">${cards}</div>
      <h2 class="sec">ข้อค้นพบสำคัญ</h2><div class="findings">${picks.map((r) => `<div class="find">${esc(r.headline)}<small class="desc">${esc(r.detail)}<br><i>ข้อควรระวัง: ${esc(r.caution)}</i></small></div>`).join('')}</div>
      <h2 class="sec">คดีหลอกลวง vs ข่าวเท็จ</h2>
      ${APP.card({ id: 'ov_main', title: 'แนวโน้มรายสัปดาห์: คดี ความเสียหาย และสัดส่วนข่าวเท็จ', unit: 'คดี · ล้านบาท · %', period: APP.periodText(plot.map((r) => r.ws)), src: 'ACSC + AFNC', span: true,
        desc: 'สัปดาห์ที่ไม่มีการแถลงเป็นช่องว่าง ไม่ใช่ศูนย์ · สัปดาห์ตัวเลขน่าสงสัยถูกตัดออกจากเส้นคดี/ความเสียหาย · ข่าวปลอมและข่าวบิดเบือนเป็นสัดส่วนของคำตัดสิน AFNC' })}
      <p class="hint">จำนวนคำตัดสิน AFNC สะท้อนเรื่องที่ศูนย์ฯ เลือกตรวจ ไม่ใช่จำนวนข่าวปลอมทั้งหมดในสังคม</p>`;
    after.push(() => {
      if (!plot.length) return;
      const dates = plot.map((r) => r.ws);
      mount('ov_main', { legend: { top: 0, data: ['คดี', 'ความเสียหาย (ล้านบาท)', 'สัดส่วนข่าวเท็จ (%)'] }, tooltip: { trigger: 'axis' },
        grid: [{ left: 62, right: 20, top: 38, height: '25%' }, { left: 62, right: 20, top: '37%', height: '25%' }, { left: 62, right: 20, top: '69%', height: '23%' }],
        xAxis: [0, 1, 2].map((i) => ({ type: 'category', gridIndex: i, data: dates, axisLabel: { show: i === 2 } })),
        yAxis: [{ type: 'value', gridIndex: 0, name: 'คดี' }, { type: 'value', gridIndex: 1, name: 'ล้านบาท' }, { type: 'value', gridIndex: 2, name: '%', min: 0, max: 100 }],
        series: [
          { name: 'คดี', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: plot.map((r) => r.use ? r.cases : null), color: C.fake, connectNulls: false, showSymbol: true },
          { name: 'ความเสียหาย (ล้านบาท)', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: plot.map((r) => r.use ? r.loss / 1e6 : null), color: C.orange, connectNulls: false, showSymbol: true },
          { name: 'สัดส่วนข่าวเท็จ (%)', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: plot.map((r) => r.vd ? (r.fake + r.dist) / r.vd * 100 : null), color: C.blue, connectNulls: false, showSymbol: true },
        ] });
    });
    return { html, after };
  }

  function lossChart(id, wk) {
    // Background bars mark weeks that are NOT plotted: grey = no briefing (not zero), light red = suspect figure removed.
    const ymax = Math.ceil(Math.max(...wk.map((w) => (w.loss || 0) / 1e6), 1) * 1.08 / 50) * 50;
    const shade = wk.map((w) => (w.sus ? { value: ymax, itemStyle: { color: 'rgba(231,163,171,.55)' } } : !w.rep ? { value: ymax, itemStyle: { color: 'rgba(150,150,155,.22)' } } : null));
    mount(id, { xAxis: { type: 'category', data: wk.map((w) => w.ws) }, yAxis: { type: 'value', name: 'ล้านบาท', min: 0, max: ymax }, dataZoom: [{ type: 'inside' }],
      tooltip: { trigger: 'axis', formatter: (q) => { const w = wk[q[0].dataIndex]; return `${w.ws}<br>${w.sus ? 'ตัวเลขน่าสงสัย (ตัดออก)' : !w.rep ? 'ไม่มีการแถลง (ไม่ใช่ 0)' : L.fmtNum(w.loss / 1e6, 0) + ' ล้านบาท' + (w.rnd ? ' (ปัด)' : '')}`; } },
      series: [{ type: 'bar', silent: true, barWidth: '100%', z: 0, data: shade }, { type: 'line', z: 3, color: C.fake, connectNulls: false, data: wk.map((w) => (w.use ? { value: w.loss / 1e6, symbol: 'circle', symbolSize: 7, itemStyle: w.rnd ? { color: '#fff', borderColor: C.fake, borderWidth: 2 } : { color: C.fake } } : null)) }] });
  }
  APP.lossChart = lossChart;

  // ================================================================== 2. Disinformation & Fake News
  function disinfo() {
    const x = ctx(), f = x.f, gran = APP.state.gran, v = verdictIdx(x.ai), after = [], p = [];
    const per = byPeriod(x.ai, gran).map(([k, c]) => ({ k, fake: c[0], dist: c[1], real: c[2], other: c[3], vd: c[0] + c[1] + c[2] }));
    const verdPer = per.filter((r) => r.vd > 0);
    const periodA = APP.periodText(x.ai.map((i) => A.d[i]));
    const noA = L.whyNot('afnc', f);
    p.push(`<h2 class="sec">1.1 วิเคราะห์ตามเวลา</h2><p class="sec-sub">จำนวนข่าวปลอม (คำตัดสิน "ข่าวปลอม") และข่าวบิดเบือน แยกตามช่วงเวลา</p>${noA ? scope('afnc') : ''}
      <div class="row-tools">ความละเอียด: ${granSwitch()}</div>`);
    p.push('<div class="grid">');
    p.push(APP.card({ id: 'd1', title: `จำนวนข่าวปลอม${GRAN[gran]}`, unit: `เรื่อง/${{ month: 'เดือน', quarter: 'ไตรมาส', year: 'ปี' }[gran]}`, period: periodA, src: 'AFNC', span: true, msg: verdPer.length ? '' : (noA || 'ไม่มีข้อมูลในช่วงที่เลือก'),
      desc: 'แท่งซ้อน: ข่าวปลอม (แดงเข้ม) + ข่าวบิดเบือน (แดงอ่อน) ของศูนย์ต่อต้านข่าวปลอม',
      insight: verdPer.length ? (() => { const pk = verdPer.reduce((a, b) => (b.fake > a.fake ? b : a)); return `${GRAN[gran]}ที่ข่าวปลอมสูงสุด: ${pk.k} (${L.fmtInt(pk.fake)} เรื่อง)`; })() : '' }));
    after.push(() => verdPer.length && mount('d1', { legend: { top: 0 }, xAxis: { type: 'category', data: verdPer.map((r) => r.k) }, yAxis: { type: 'value', name: 'เรื่อง' }, dataZoom: [{ type: 'inside' }],
      series: [{ name: 'ข่าวปลอม', type: 'bar', stack: 's', color: C.fake, data: verdPer.map((r) => r.fake) }, { name: 'ข่าวบิดเบือน', type: 'bar', stack: 's', color: C.fakeL, data: verdPer.map((r) => r.dist) }] }));
    p.push('</div>');
    // top periods + change table
    const topOf = (g) => { const m = byPeriod(v, g).map(([k, c]) => ({ k, fake: c[0] })).sort((a, b) => b.fake - a.fake).slice(0, 5); return m; };
    const tm = topOf('month'), tq = topOf('quarter');
    const chg = verdPer.map((r, i) => ({ ...r, pct: i ? L.pctChange(r.fake, verdPer[i - 1].fake) : null, share: r.vd ? ((r.fake + r.dist) / r.vd) * 100 : null }));
    p.push(`<div class="grid"><section class="card"><h3>เดือนและไตรมาสที่มีข่าวปลอมสูงสุด (อันดับ 1–5)</h3><div class="grid" style="grid-template-columns:1fr 1fr;gap:10px">
      <div>${table([{ h: 'เดือน', f: (r) => r.k }, { h: 'ข่าวปลอม', n: 1, f: (r) => L.fmtInt(r.fake) }], tm, { hl: (r) => r === tm[0] })}</div>
      <div>${table([{ h: 'ไตรมาส', f: (r) => r.k }, { h: 'ข่าวปลอม', n: 1, f: (r) => L.fmtInt(r.fake) }], tq, { hl: (r) => r === tq[0] })}</div></div>
      <div class="cap">หน่วย: เรื่อง · ช่วงเวลา: ${esc(periodA)} · แหล่ง: AFNC</div></section>
      <section class="card"><h3>ตารางเปรียบเทียบและอัตราการเปลี่ยนแปลงระหว่างช่วง (${GRAN[gran]})</h3>
      ${table([{ h: 'ช่วง', f: (r) => r.k }, { h: 'ข่าวปลอม', n: 1, f: (r) => L.fmtInt(r.fake) }, { h: 'บิดเบือน', n: 1, f: (r) => L.fmtInt(r.dist) }, { h: 'ข่าวจริง', n: 1, f: (r) => L.fmtInt(r.real) }, { h: 'คำตัดสิน', n: 1, f: (r) => L.fmtInt(r.vd) },
        { h: '% เท็จ', n: 1, f: (r) => (r.share === null ? '–' : L.fmtNum(r.share, 1)) }, { h: 'ข่าวปลอม เทียบช่วงก่อน', n: 1, f: (r) => (r.pct === null ? '–' : (r.pct > 0 ? '+' : '') + L.fmtNum(r.pct, 1) + '%') }], chg.slice().reverse(), { max: 120 })}
      <div class="cap">หน่วย: เรื่อง/ร้อยละ · อัตราเปลี่ยนแปลง = (ช่วงนี้ − ช่วงก่อน) ÷ ช่วงก่อน · ช่วงที่ไม่มีคำตัดสินไม่แสดง</div></section></div>`);
    // EU monthly comparison
    const euPer = new Map(); for (const i of x.eu) { const k = L.periodKey(E.d[i], gran); euPer.set(k, (euPer.get(k) || 0) + 1); }
    const eus = [...euPer.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1));
    p.push('<div class="grid" style="margin-top:14px">' + APP.card({ id: 'd2', title: `ระดับนานาชาติ: จำนวนการหักล้างข้อมูลบิดเบือน${GRAN[gran]} (EUvsDisinfo)`, unit: 'การหักล้าง (debunk_id ไม่ซ้ำ)', period: APP.periodText(x.eu.map((i) => E.d[i])), src: 'EUvsDisinfo', span: true,
      msg: eus.length ? '' : (L.whyNot('eu', f) || 'ไม่มีข้อมูลในช่วงที่เลือก (EUvsDisinfo มีข้อมูลถึง 1 ส.ค. 2023)'), desc: 'ชุดข้อมูลของ EU เก็บเฉพาะข้อมูลเท็จฝั่งสนับสนุนรัสเซีย จำนวนที่ลดลงหลังปี 2021 ไม่ได้แปลว่าข้อมูลเท็จลดลง',
      insight: eus.length ? (() => { const pk = eus.reduce((a, b) => (b[1] > a[1] ? b : a)); return `ช่วงที่มีการหักล้างสูงสุด: ${pk[0]} (${L.fmtInt(pk[1])} เรื่อง)`; })() : '' }) + '</div>');
    after.push(() => eus.length && mount('d2', { xAxis: { type: 'category', data: eus.map((e) => e[0]) }, yAxis: { type: 'value', name: 'เรื่อง' }, dataZoom: [{ type: 'inside' }], series: [{ type: 'bar', color: C.teal, data: eus.map((e) => e[1]) }] }));

    // ---- 1.2 categories
    p.push('<h2 class="sec">1.2 วิเคราะห์ประเภทข่าว</h2><p class="sec-sub">ใช้หมวดหมู่ที่ปรากฏในข้อมูลของศูนย์ต่อต้านข่าวปลอม (หมวด Economy, Drugs, Other news รวมเป็น "อื่น ๆ"; แปลเป็นไทย)</p>');
    const cm = new Map(); for (const i of v) if (A.c[i] >= 0) { const k = A.cats[A.c[i]]; if (!cm.has(k)) cm.set(k, [0, 0, 0]); const s = A.st[i]; cm.get(k)[s === 0 ? 0 : s === 1 ? 1 : 2]++; }
    const cr = [...cm.entries()].map(([k, c]) => ({ k, n: L.sum(c), fake: c[0], dist: c[1], real: c[2] })).sort((a, b) => b.n - a.n);
    const tot = L.sum(cr.map((r) => r.n));
    p.push('<div class="grid">');
    p.push(APP.card({ id: 'd3', title: 'จำนวนข่าวแยกตามประเภท', unit: 'เรื่อง (คำตัดสิน)', period: periodA, src: 'AFNC', msg: cr.length ? '' : (noA || 'ไม่มีข้อมูล'), desc: 'แท่งซ้อนตามผลตรวจ: ปลอม / บิดเบือน / จริง',
      insight: cr.length ? `อันดับ 1: ${cr[0].k} ${L.fmtInt(cr[0].n)} เรื่อง (${L.fmtNum((cr[0].n / tot) * 100, 1)}%) · อันดับ 2: ${cr[1] ? cr[1].k + ' ' + L.fmtNum((cr[1].n / tot) * 100, 1) + '%' : '–'}` : '' }));
    after.push(() => cr.length && mount('d3', { legend: { top: 0 }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, grid: { left: 10, right: 20, top: 34, bottom: 10, containLabel: true }, xAxis: { type: 'value' },
      yAxis: { type: 'category', inverse: true, data: cr.map((r) => r.k.replace(/\s*\(.*\)/, '')) }, series: [['ข่าวปลอม', 'fake', C.fake], ['ข่าวบิดเบือน', 'dist', C.fakeL], ['ข่าวจริง', 'real', C.real]].map(([n, k, c]) => ({ name: n, type: 'bar', stack: 's', color: c, data: cr.map((r) => r[k]) })) }));
    p.push(APP.card({ id: 'd4', title: 'สัดส่วนประเภทข่าว (Treemap)', unit: '% ของคำตัดสิน', period: periodA, src: 'AFNC', msg: cr.length ? '' : (noA || 'ไม่มีข้อมูล'), desc: 'พื้นที่ของแต่ละกล่องแปรตามจำนวนเรื่อง'}));
    after.push(() => cr.length && mount('d4', { tooltip: { trigger: 'item', formatter: (q) => `${q.name}<br>${L.fmtInt(q.value)} เรื่อง (${L.fmtNum((q.value / tot) * 100, 1)}%)` }, series: [{ type: 'treemap', roam: false, breadcrumb: { show: false }, label: { formatter: (q) => `${q.name}\n${L.fmtNum((q.value / tot) * 100, 1)}%` },
      data: cr.map((r, i) => ({ name: r.k.replace(/\s*\(.*\)/, ''), value: r.n, itemStyle: { color: ['#7B1E3A', '#C0506E', '#E08A3C', '#F2C078', '#3E5C8A', '#2F7F79', '#B9B3AE'][i % 7] } })) }] }));
    p.push('</div>');
    p.push(`<section class="card" style="margin-top:14px"><h3>ตารางรายละเอียดของแต่ละประเภท</h3>${table([{ h: 'อันดับ', n: 1, f: (r) => cr.indexOf(r) + 1 }, { h: 'ประเภทข่าว', f: (r) => r.k }, { h: 'รวม (เรื่อง)', n: 1, f: (r) => L.fmtInt(r.n) }, { h: '% ของคำตัดสิน', n: 1, f: (r) => L.fmtNum((r.n / tot) * 100, 1) },
      { h: 'ปลอม', n: 1, f: (r) => L.fmtInt(r.fake) }, { h: 'บิดเบือน', n: 1, f: (r) => L.fmtInt(r.dist) }, { h: 'จริง', n: 1, f: (r) => L.fmtInt(r.real) }, { h: '% เท็จในหมวด', n: 1, f: (r) => L.fmtNum(((r.fake + r.dist) / r.n) * 100, 1) }], cr)}
      <div class="cap">หน่วย: เรื่อง/ร้อยละ · ตัวหาร = คำตัดสินทั้งหมด ${L.fmtInt(tot)} เรื่องในช่วงที่เลือก · ช่วงเวลา: ${esc(periodA)}</div></section>`);
    // EU issues + trends (static, full period)
    const kwc = new Map(); for (const i of x.eu) for (const k of E.k[i]) kwc.set(k, (kwc.get(k) || 0) + 1);
    const kws = [...kwc.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12).reverse();
    const cv = D.analysis.covid.filter((r) => r.year >= 2018);
    p.push('<div class="grid" style="margin-top:14px">');
    p.push(APP.card({ id: 'd5', title: 'ประเด็นข้อมูลบิดเบือนระดับนานาชาติ (EUvsDisinfo) 12 อันดับแรก', unit: 'การหักล้าง (นับต่อเรื่อง ไม่ใช่ต่อบทความ)', period: APP.periodText(x.eu.map((i) => E.d[i])), src: 'EUvsDisinfo', msg: kws.length ? '' : (L.whyNot('eu', f) || 'ไม่มีข้อมูลในช่วงที่เลือก'),
      desc: 'ประเด็น (keywords) ที่ถูกหักล้าง · 1 การหักล้างอาจมีหลายประเด็น', insight: kws.length ? `ประเด็นอันดับ 1: ${kws[kws.length - 1][0]} (${L.fmtInt(kws[kws.length - 1][1])} เรื่อง)` : '' }));
    after.push(() => kws.length && mount('d5', { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, grid: { left: 10, right: 40, top: 20, bottom: 10, containLabel: true }, xAxis: { type: 'value' }, yAxis: { type: 'category', data: kws.map((k) => k[0]) }, series: [{ type: 'bar', color: C.teal, data: kws.map((k) => k[1]), label: { show: true, position: 'right' } }] }));
    p.push(APP.card({ id: 'd6', title: 'โควิด: ประเด็นที่ปรากฏซ้ำทั้งไทยและนานาชาติ', unit: '% ของข่าวเท็จไทย / การหักล้าง EU ในปีนั้น', period: '2018–2026 (ทั้งช่วงข้อมูล ไม่เปลี่ยนตามตัวกรอง)', src: 'AFNC + EUvsDisinfo', desc: 'นิยามโควิดของสองฝั่งต่างกัน (แท็กของไทย vs keywords ของ EU) เทียบแนวโน้มได้ ไม่ใช่ค่าที่เทียบกันตรง ๆ',
      insight: 'ทั้งสองฝั่งพุ่งสูงปี 2020 แล้วลดลงเกือบหมดหลังปี 2022' }));
    after.push(() => mount('d6', { legend: { top: 0 }, xAxis: { type: 'category', data: [...new Set(cv.map((r) => r.year))] }, yAxis: { type: 'value', name: '%' }, tooltip: { trigger: 'axis', valueFormatter: (q) => (q === null || q === undefined ? '–' : q.toFixed(1) + '%') },
      series: [['AFNC (ไทย)', C.fake], ['EUvsDisinfo', C.teal]].map(([s, c]) => ({ name: s, type: 'line', color: c, connectNulls: false, data: [...new Set(cv.map((r) => r.year))].map((y) => cv.find((r) => r.year === y && r.source === s)?.share_pct ?? null) })) }));
    p.push('</div>');
    const tr = D.analysis.thai_rising, er = D.analysis.eu_rising;
    p.push(`<section class="card" style="margin-top:14px"><h3>ประเด็นที่ปรากฏซ้ำและมีแนวโน้มเพิ่มขึ้น/ลดลง (ทั้งช่วงข้อมูล)</h3><div class="grid">
      <div><b>ไทย (${D.analysis.thai_years[0]}→${D.analysis.thai_years[1]})</b>${table([{ h: 'หัวข้อ', f: (r) => r.topic }, { h: '% ต้น', n: 1, f: (r) => L.fmtNum(r.share_start, 1) }, { h: '% ปลาย', n: 1, f: (r) => L.fmtNum(r.share_end, 1) }, { h: 'เปลี่ยน (จุด)', n: 1, f: (r) => (r.change_pp > 0 ? '+' : '') + L.fmtNum(r.change_pp, 1) }], [...tr.slice(0, 5), ...tr.slice(-3)])}</div>
      <div><b>EU (${D.analysis.eu_years[0]}→${D.analysis.eu_years[1]})</b>${table([{ h: 'ประเด็น', f: (r) => r.topic }, { h: '% ต้น', n: 1, f: (r) => L.fmtNum(r.share_start, 1) }, { h: '% ปลาย', n: 1, f: (r) => L.fmtNum(r.share_end, 1) }, { h: 'เปลี่ยน (จุด)', n: 1, f: (r) => (r.change_pp > 0 ? '+' : '') + L.fmtNum(r.change_pp, 1) }], [...er.slice(0, 5), ...er.slice(-3)])}</div></div>
      <div class="cap">หน่วย: % ของเรื่องทั้งหมดในปีนั้น · เฉพาะหัวข้อที่มีอย่างน้อย 40 เรื่อง · คำนวณจากข้อมูลทั้งช่วง ไม่เปลี่ยนตามตัวกรอง</div></section>`);

    // ---- 1.3 verdict share
    p.push('<h2 class="sec">1.3 สัดส่วนข่าวจริงและข่าวปลอม</h2><p class="sec-sub">สัดส่วนของ "ข่าวที่ศูนย์ต่อต้านข่าวปลอมเลือกตรวจ" ไม่ใช่สัดส่วนข่าวปลอมทั้งหมดในสังคม — ศูนย์ฯ ไม่ได้สุ่มตรวจ</p>');
    const sc = statusCounts(x.ai), unl = x.ai.filter((i) => A.itypes[A.it[i]] === 'Unlabelled').length, totA = L.sum(sc), vd = sc[0] + sc[1] + sc[2];
    p.push('<div class="grid">');
    p.push(APP.card({ id: 'd7', title: 'สัดส่วนผลตรวจ (Donut)', unit: '% ของโพสต์ทั้งหมดที่ผ่านตัวกรอง', period: periodA, src: 'AFNC', msg: totA ? '' : (noA || 'ไม่มีข้อมูล'), desc: 'ข่าวปลอม / ข่าวบิดเบือน / ข่าวจริง / อื่น ๆ (บทความความรู้ ประกาศเตือนภัย ข่าวอื่น ฯลฯ ที่ไม่ใช่คำตัดสิน)',
      insight: totA ? `จากคำตัดสิน ${L.fmtInt(vd)} เรื่อง: ปลอม ${L.fmtNum((sc[0] / vd) * 100, 1)}% · บิดเบือน ${L.fmtNum((sc[1] / vd) * 100, 1)}% · จริง ${L.fmtNum((sc[2] / vd) * 100, 1)}%` : '' }));
    after.push(() => totA && mount('d7', { tooltip: { trigger: 'item', formatter: (q) => `${q.name}<br>${L.fmtInt(q.value)} โพสต์ (${q.percent}%)` }, legend: { bottom: 0 }, series: [{ type: 'pie', radius: ['42%', '68%'], label: { formatter: '{b}\n{d}%' }, data: ['ข่าวปลอม', 'ข่าวบิดเบือน', 'ข่าวจริง', 'อื่น ๆ'].map((n, k) => ({ name: n, value: sc[k], itemStyle: { color: STC[k] } })) }] }));
    p.push(`<section class="card"><h3>จำนวนและตัวหารของร้อยละ</h3>${table([{ h: 'ประเภท', f: (r) => r[0] }, { h: 'จำนวน', n: 1, f: (r) => L.fmtInt(r[1]) }, { h: '% ของโพสต์ทั้งหมด', n: 1, f: (r) => L.fmtNum((r[1] / totA) * 100, 1) }, { h: '% ของคำตัดสิน', n: 1, f: (r) => (r[2] ? L.fmtNum((r[1] / vd) * 100, 1) : '–') }],
      [['ข่าวปลอม', sc[0], 1], ['ข่าวบิดเบือน', sc[1], 1], ['ข่าวจริง', sc[2], 1], ['อื่น ๆ (ไม่ใช่คำตัดสิน)', sc[3], 0], ['— ในนั้น: ยังไม่ระบุประเภท (Unlabelled)', unl, 0]])}
      <div class="cap">ตัวหาร: โพสต์ทั้งหมดที่ผ่านตัวกรอง ${L.fmtInt(totA)} · คำตัดสินทั้งหมด ${L.fmtInt(vd)} · ช่วงเวลา: ${esc(periodA)} · แหล่ง: AFNC</div>
      <div class="warn">ห้ามนำสัดส่วนนี้ไปสรุปว่า "ข่าวในสังคม ${L.fmtNum((sc[0] / Math.max(vd, 1)) * 100, 0)}% เป็นข่าวปลอม" — ข้อมูลไม่ใช่ตัวแทนของข่าวทั้งหมด</div></section>`);
    p.push('</div>');
    // stacked by year
    const yr = new Map(); for (const i of x.ai) { const k = L.yearOf(A.d[i]); if (!yr.has(k)) yr.set(k, [0, 0, 0, 0]); yr.get(k)[A.st[i]]++; }
    const yrs = [...yr.entries()].sort((a, b) => a[0] - b[0]);
    p.push('<div class="grid" style="margin-top:14px">' + APP.card({ id: 'd8', title: 'สัดส่วนผลตรวจรายปี (100% Stacked)', unit: '% ของโพสต์ในปีนั้น', period: periodA, src: 'AFNC', span: true, msg: yrs.length ? '' : (noA || 'ไม่มีข้อมูล'), desc: 'ปี 2019 มีน้อยเพราะศูนย์ฯ เปิดเดือน พ.ย. 2019 และปีล่าสุดยังไม่ครบปี' }) + '</div>');
    after.push(() => yrs.length && mount('d8', { legend: { top: 0 }, tooltip: { trigger: 'axis', valueFormatter: (q) => q.toFixed(1) + '%' }, xAxis: { type: 'category', data: yrs.map((y) => y[0]) }, yAxis: { type: 'value', max: 100, name: '%' },
      series: ['ข่าวปลอม', 'ข่าวบิดเบือน', 'ข่าวจริง', 'อื่น ๆ'].map((n, k) => ({ name: n, type: 'bar', stack: 's', color: STC[k], data: yrs.map((y) => (y[1][k] / L.sum(y[1])) * 100) })) }));
    return { html: p.join(''), after };
  }

  // ================================================================== 3. Internet Freedom & Country Comparison
  function freedom() {
    const x = ctx(), f = x.f, after = [], p = [], fo = x.fo, lastY = Math.max(...D.fotn.map((r) => r.y));
    const noF = L.whyNot('fotn', f);
    const thAll = L.fotnRows(D, { ...f, region: 'th' }).sort((a, b) => a.y - b.y);
    p.push(`<h2 class="sec">3.1 คะแนนเสรีภาพทางอินเทอร์เน็ต</h2><p class="sec-sub">คะแนน 0–100 สูง = เสรีมาก · ปีข้อมูลต่างจากปีรายงาน 1 ปี (ข้อมูลปี 2024 = รายงานฉบับ 2025) · ${esc(noF)}</p>`);
    const th = thAll[thAll.length - 1];
    if (th) {
      const rk = L.fotnRank(D.fotn, 'THA', th.y), first = thAll[0];
      p.push(`<div class="kpis">${kpi({ key: 'f_score', label: `คะแนนไทย (ปีข้อมูล ${th.y})`, value: `${th.total}<small>/100</small>`, sub: ['', 'เสรี', 'เสรีบางส่วน', 'ไม่เสรี'][th.st], color: C.blue })}
        ${kpi({ key: 'f_rank', label: 'อันดับเทียบทุกประเทศในปีเดียวกัน', value: `${rk.rank}<small>/${rk.n}</small>`, sub: '1 = เสรีที่สุด · คะแนนเท่ากันได้อันดับเดียวกัน', color: C.blue })}
        ${kpi({ key: 'f_chg', label: `เปลี่ยนแปลง ${first.y}→${th.y}`, value: `${th.total - first.total > 0 ? '+' : ''}${th.total - first.total}<small> คะแนน</small>`, sub: `จาก ${first.total} เป็น ${th.total}`, color: C.blue })}
        ${kpi({ key: 'f_weak', label: 'ส่วนที่อ่อนที่สุด (% ของคะแนนเต็ม)', value: (() => { const o = [['สิทธิผู้ใช้', th.rig / 40], ['จำกัดเนื้อหา', th.con / 35], ['การเข้าถึง', th.acc / 25]].sort((a, b) => a[1] - b[1])[0]; return `${o[0]} <small>${L.fmtNum(o[1] * 100, 0)}%</small>`; })(), sub: `ปีข้อมูล ${th.y}`, color: C.blue })}</div>`);
    }
    p.push('<div class="grid" style="margin-top:12px">');
    p.push(APP.card({ id: 'f1', title: 'คะแนนเสรีภาพของประเทศไทยตามปี และคะแนนย่อย 3 ส่วน', unit: 'คะแนน (รวม 0–100; ส่วนย่อยเต็ม 25 / 35 / 40)', period: thAll.length ? `ปีข้อมูล ${thAll[0].y}–${thAll[thAll.length - 1].y}` : '–', src: 'Freedom on the Net', msg: thAll.length ? '' : (noF || 'ไม่มีข้อมูลไทยในช่วงที่เลือก'),
      desc: 'แท่งซ้อน = 3 องค์ประกอบ (อุปสรรคการเข้าถึง + การจำกัดเนื้อหา + การละเมิดสิทธิผู้ใช้) รวมเป็นคะแนนรวม', insight: th ? `ไทย ${th.total} คะแนน (ปีข้อมูล ${th.y}) · ส่วนที่ต่ำที่สุดคือสิทธิผู้ใช้ ${th.rig}/40` : '' }));
    after.push(() => thAll.length && mount('f1', { legend: { top: 0 }, xAxis: { type: 'category', data: thAll.map((r) => r.y) }, yAxis: { type: 'value', max: 100 }, tooltip: { trigger: 'axis' },
      series: [['อุปสรรคการเข้าถึง (เต็ม 25)', 'acc', '#E7A3AB'], ['การจำกัดเนื้อหา (เต็ม 35)', 'con', '#B5485A'], ['สิทธิผู้ใช้ (เต็ม 40)', 'rig', '#8E1B2E']].map(([n, k, c]) => ({ name: n, type: 'bar', stack: 's', color: c, data: thAll.map((r) => r[k]) })) }));
    p.push(APP.card({ id: 'f2', title: 'อันดับของไทยตามปี (เทียบทุกประเทศที่มีข้อมูลในปีนั้น)', unit: 'อันดับ (1 = เสรีที่สุด)', period: thAll.length ? `ปีข้อมูล ${thAll[0].y}–${thAll[thAll.length - 1].y}` : '–', src: 'Freedom on the Net', msg: thAll.length ? '' : (noF || 'ไม่มีข้อมูล'),
      desc: 'จำนวนประเทศต่อปีเพิ่มจาก 37 เป็น 71 อันดับข้ามปีจึงเทียบกันตรง ๆ ไม่ได้ ควรดูร่วมกับจำนวนประเทศ (แสดงใน tooltip)' }));
    after.push(() => thAll.length && mount('f2', { xAxis: { type: 'category', data: thAll.map((r) => r.y) }, yAxis: { type: 'value', inverse: true, name: 'อันดับ' }, tooltip: { trigger: 'axis', formatter: (q) => { const r = L.fotnRank(D.fotn, 'THA', +q[0].axisValue); return `ปี ${q[0].axisValue}<br>อันดับ ${r.rank} จาก ${r.n} ประเทศ`; } },
      series: [{ type: 'line', color: C.blue, symbolSize: 8, data: thAll.map((r) => L.fotnRank(D.fotn, 'THA', r.y).rank) }] }));
    p.push('</div>');

    // ---- 3.2 compare
    p.push('<h2 class="sec">3.2 เปรียบเทียบประเทศ</h2><p class="sec-sub">เลือกประเทศหรือกลุ่มประเทศได้ที่ตัวกรองด้านซ้าย (ไทยแสดงเสมอเป็นจุดอ้างอิง ยกเว้นเลือก "ต่างประเทศ")</p>');
    const lf = latestFotn(fo), bars = lf.rows.sort((a, b) => b.total - a.total);
    const names = [...new Map(fo.map((r) => [r.iso3, r.country])).entries()];
    const yearsSet = [...new Set(fo.map((r) => r.y))].sort((a, b) => a - b);
    p.push('<div class="grid">');
    p.push(APP.card({ id: 'f3', title: 'เปรียบเทียบคะแนนรวมระหว่างประเทศ', unit: 'คะแนน 0–100', period: lf.y ? `ปีข้อมูล ${lf.y}` : '–', src: 'Freedom on the Net', msg: bars.length ? '' : (noF || 'ไม่มีข้อมูล'), h: Math.max(300, Math.min(bars.length, 40) * 18 + 60),
      desc: 'ไทยเป็นสีแดงเข้ม', insight: bars.length ? `สูงสุด ${bars[0].country} ${bars[0].total} · ต่ำสุด ${bars[bars.length - 1].country} ${bars[bars.length - 1].total}` : '' }));
    after.push(() => bars.length && mount('f3', { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, grid: { left: 10, right: 30, top: 10, bottom: 10, containLabel: true }, xAxis: { type: 'value', max: 100 }, yAxis: { type: 'category', inverse: true, data: bars.slice(0, 40).map((r) => r.country), axisLabel: { fontSize: 10 } },
      series: [{ type: 'bar', data: bars.slice(0, 40).map((r) => ({ value: r.total, itemStyle: { color: r.iso3 === 'THA' ? C.fake : '#c9c3c5' } })), label: { show: true, position: 'right', fontSize: 10 } }] }));
    const pick = names.length > 12 ? names.filter(([i]) => i === 'THA' || f.countries.includes(i) || Object.keys(D.meta.asean).includes(i)).slice(0, 12) : names;
    p.push(APP.card({ id: 'f4', title: 'แนวโน้มคะแนนรายปีของประเทศที่เลือก', unit: 'คะแนน 0–100', period: yearsSet.length ? `ปีข้อมูล ${yearsSet[0]}–${yearsSet[yearsSet.length - 1]}` : '–', src: 'Freedom on the Net', msg: pick.length ? '' : (noF || 'ไม่มีข้อมูล'), h: 360,
      desc: names.length > 12 ? 'ประเทศมากกว่า 12 ประเทศ: แสดงไทย ประเทศที่เลือก และอาเซียน (สูงสุด 12 เส้น)' : 'ไทยเป็นเส้นหนาสีแดงเข้ม' }));
    after.push(() => pick.length && mount('f4', { legend: { type: 'scroll', top: 0 }, xAxis: { type: 'category', data: yearsSet }, yAxis: { type: 'value', min: 0, max: 100 }, tooltip: { trigger: 'axis' },
      series: pick.map(([iso, nm]) => ({ name: nm, type: 'line', connectNulls: false, symbolSize: iso === 'THA' ? 7 : 3, lineStyle: { width: iso === 'THA' ? 4 : 1.6 }, color: iso === 'THA' ? C.fake : undefined, data: yearsSet.map((y) => fo.find((r) => r.iso3 === iso && r.y === y)?.total ?? null) })) }));
    const hm = names.length > 30 ? names.slice().sort((a, b) => (fo.find((r) => r.iso3 === b[0] && r.y === lf.y)?.total ?? -1) - (fo.find((r) => r.iso3 === a[0] && r.y === lf.y)?.total ?? -1)).slice(0, 30) : names;
    p.push(APP.card({ id: 'f5', title: 'Heatmap: ประเทศ × ปี', unit: 'คะแนน 0–100 (เทา = ไม่มีข้อมูล ไม่ใช่ 0)', period: yearsSet.length ? `ปีข้อมูล ${yearsSet[0]}–${yearsSet[yearsSet.length - 1]}` : '–', src: 'Freedom on the Net', span: true, h: Math.max(300, hm.length * 20 + 80), msg: hm.length ? '' : (noF || 'ไม่มีข้อมูล'),
      desc: names.length > 30 ? 'ประเทศมากกว่า 30 ประเทศ: แสดง 30 ประเทศที่คะแนนสูงสุดในปีล่าสุด' : ''}));
    after.push(() => hm.length && mount('f5', { tooltip: { trigger: 'item', formatter: (q) => `${hm[q.value[1]][1]} · ปี ${yearsSet[q.value[0]]}<br>${q.value[2]} คะแนน` }, grid: { left: 10, right: 30, top: 10, bottom: 50, containLabel: true }, xAxis: { type: 'category', data: yearsSet }, yAxis: { type: 'category', data: hm.map((h) => h[1]), inverse: true, axisLabel: { fontSize: 10 } },
      visualMap: { min: 0, max: 100, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#C0392B', '#F6D5D7', '#ffffff', '#cfe6d7', '#2E8B57'] } },
      series: [{ type: 'heatmap', data: hm.flatMap((h, yi) => yearsSet.map((y, xi) => { const r = fo.find((q) => q.iso3 === h[0] && q.y === y); return r ? [xi, yi, r.total] : null; }).filter(Boolean)) }] }));
    p.push('</div>');
    p.push(`<section class="card" style="margin-top:14px"><h3>ตารางรายละเอียดคะแนนและปีที่ประเมิน</h3><div class="row-tools"><button class="btn-ghost" id="dlF">⬇ ดาวน์โหลด CSV</button></div>${table([{ h: 'ประเทศ', f: (r) => r.country }, { h: 'ปีข้อมูล', n: 1, f: (r) => r.y }, { h: 'คะแนนรวม', n: 1, f: (r) => r.total }, { h: 'เข้าถึง /25', n: 1, f: (r) => r.acc }, { h: 'เนื้อหา /35', n: 1, f: (r) => r.con }, { h: 'สิทธิผู้ใช้ /40', n: 1, f: (r) => r.rig },
      { h: 'สถานะ', f: (r) => ['', 'เสรี', 'เสรีบางส่วน', 'ไม่เสรี'][r.st] }], fo.slice().sort((a, b) => b.y - a.y || b.total - a.total), { max: 200, hl: (r) => r.iso3 === 'THA' })}
      <div class="cap">หน่วย: คะแนน · ช่วงเวลา: ${yearsSet.length ? `ปีข้อมูล ${yearsSet[0]}–${yearsSet[yearsSet.length - 1]}` : '–'} · แหล่ง: Freedom on the Net (Freedom House ผ่าน QoG)</div></section>`);
    after.push(() => { const b = document.getElementById('dlF'); if (b) b.onclick = () => APP.csv('freedom_on_the_net_filtered.csv', [{ h: 'country', f: (r) => r.country }, { h: 'iso3', f: (r) => r.iso3 }, { h: 'data_year', f: (r) => r.y }, { h: 'total_score', f: (r) => r.total }, { h: 'obstacles_to_access', f: (r) => r.acc }, { h: 'limits_on_content', f: (r) => r.con }, { h: 'violations_of_user_rights', f: (r) => r.rig }], fo); });

    // ---- 3.3 vs disinformation
    p.push('<h2 class="sec">3.3 เปรียบเทียบกับสถานการณ์ข่าวปลอมและความเสียหาย</h2>');
    const ai = L.afncIdx(D, { ...f, from: D.meta.date_min, to: D.meta.date_max, years: [], quarters: [], months: [] });
    const fy = new Map(); for (const i of verdictIdx(ai)) { if (A.st[i] <= 1) { const y = L.yearOf(A.d[i]); fy.set(y, (fy.get(y) || 0) + 1); } }
    const full = [...fy.keys()].filter((y) => y >= 2020 && y < lastY + 1).sort(), thY = new Map(D.fotn.filter((r) => r.iso3 === 'THA').map((r) => [r.y, r.total]));
    const overlap = full.filter((y) => thY.has(y));
    p.push('<div class="grid">');
    p.push(APP.card({ id: 'f6', title: 'ประเทศไทย: คะแนนเสรีภาพ เทียบกับจำนวนข่าวเท็จรายปี', unit: 'คะแนน (เส้น) / เรื่อง (แท่ง)', period: overlap.length ? `${overlap[0]}–${overlap[overlap.length - 1]} (ปีที่ข้อมูลทั้งสองชุดซ้อนกัน)` : 'ไม่มีปีที่ซ้อนกัน', src: 'Freedom on the Net + AFNC', msg: overlap.length ? '' : 'ไม่มีข้อมูลเพียงพอสำหรับการวิเคราะห์นี้: ไม่มีปีที่ข้อมูลทั้งสองชุดซ้อนกัน',
      desc: 'แสดงเฉพาะประเทศไทย เพราะ AFNC เป็นข้อมูลของไทยเท่านั้น ไม่มีจำนวนข่าวปลอมรายประเทศที่เทียบกันได้' }));
    after.push(() => overlap.length && mount('f6', { legend: { top: 0 }, xAxis: { type: 'category', data: overlap }, yAxis: [{ type: 'value', name: 'เรื่อง' }, { type: 'value', name: 'คะแนน', min: 0, max: 100 }],
      series: [{ name: 'ข่าวเท็จ (ปลอม+บิดเบือน)', type: 'bar', color: C.fake, data: overlap.map((y) => fy.get(y)) }, { name: 'คะแนนเสรีภาพไทย', type: 'line', yAxisIndex: 1, color: C.blue, data: overlap.map((y) => thY.get(y)) }] }));
    const rc = L.correlate(overlap.map((y) => thY.get(y)), overlap.map((y) => fy.get(y)), 'spearman', 10);
    p.push(`<section class="card"><h3>สหสัมพันธ์: เสรีภาพ ↔ จำนวนข่าวเท็จ (ไทย, รายปี)</h3>
      <div class="${rc.ok ? 'note' : 'warn'}">${esc(L.interpret(rc))}</div>
      ${table([{ h: 'ปี', n: 1, f: (r) => r }, { h: 'คะแนนเสรีภาพ', n: 1, f: (r) => thY.get(r) }, { h: 'ข่าวเท็จ (เรื่อง)', n: 1, f: (r) => L.fmtInt(fy.get(r)) }], overlap)}
      <div class="cap">หน่วย: คะแนน/เรื่อง · ช่วงเวลา: ${overlap.length ? overlap[0] + '–' + overlap[overlap.length - 1] : '–'} · เกณฑ์ขั้นต่ำ 10 คู่ข้อมูล</div></section>`);
    p.push(`<section class="card"><h3>เสรีภาพ ↔ ความเสียหายจากมิจฉาชีพ</h3><div class="warn">ไม่มีข้อมูลเพียงพอสำหรับการวิเคราะห์นี้: ข้อมูลความเสียหาย (ACSC) เริ่ม พ.ย. 2025 แต่คะแนนเสรีภาพล่าสุดคือปีข้อมูล ${lastY} จึงไม่มีช่วงเวลาที่ซ้อนกันเลย — ระบบไม่คำนวณ</div></section>`);
    // AI incidents mentions
    const cn = D.analysis.country.rows.filter((r) => r.mentions >= 5 && fo.some((q) => q.iso3 === r.iso3));
    const rcn = L.correlate(cn.map((r) => r.total_score), cn.map((r) => r.mentions), 'spearman', 10);
    p.push(APP.card({ id: 'f7', title: 'เสรีภาพ vs จำนวนเหตุการณ์ AI ที่กล่าวถึงแต่ละประเทศ (เชิงสำรวจ)', unit: 'เหตุการณ์ที่กล่าวถึงประเทศ (แกนล็อก)', period: `AIID ฉบับ ${D.meta.aiid_snapshot} · คะแนนเสรีภาพปีข้อมูล ${lastY}`, src: 'AIID + Freedom on the Net', msg: cn.length ? '' : 'ไม่มีประเทศที่ผ่านตัวกรอง (ต้องถูกกล่าวถึงอย่างน้อย 5 ครั้ง)', h: 340,
      desc: 'AIID มีช่องประเทศเพียง ~8% จึงนับจากชื่อประเทศในข้อความ นี่คือ "การถูกกล่าวถึง" ไม่ใช่ที่เกิดเหตุ และฐานข้อมูลเน้นข่าวภาษาอังกฤษ', insight: rcn.ok ? L.interpret(rcn) : '' }));
    after.push(() => cn.length && mount('f7', { tooltip: { trigger: 'item', formatter: (q) => `${q.data[2]}<br>คะแนน ${q.data[0]} · ${q.data[1]} เหตุการณ์` }, xAxis: { type: 'value', name: 'คะแนนเสรีภาพ', min: 0, max: 100 }, yAxis: { type: 'log', name: 'เหตุการณ์' },
      series: [{ type: 'scatter', symbolSize: 11, data: cn.map((r) => ({ value: [r.total_score, r.mentions, r.country.replace(/\s*\(.*\)/, '')], itemStyle: { color: r.iso3 === 'THA' ? C.fake : ({ 1: C.real, 2: C.orange, 3: C.fake }[r.status_code]) } })) }] }));
    p.push(`<section class="card"><h3>สหสัมพันธ์ (เชิงสำรวจ)</h3><div class="${rcn.ok ? 'note' : 'warn'}">${esc(L.interpret(rcn))}</div></section>`);
    p.push('</div>');
    p.push(`<div class="warn"><b>ข้อจำกัด:</b> (1) ข่าวปลอม/คดีหลอกลวงเป็นข้อมูลของไทยเท่านั้น จึงเปรียบเทียบข้ามประเทศไม่ได้ (2) คะแนนเสรีภาพเป็นรายปี ฝั่งคดีเป็นรายสัปดาห์ (3) ไม่สรุปว่าประเทศที่มีข่าวปลอมมากกว่ามีเสรีภาพมากกว่าหรือน้อยกว่า และไม่สรุปเหตุและผลจากสหสัมพันธ์</div>`);
    return { html: p.join(''), after };
  }

  APP.addTab('overview', 'ภาพรวม', overview);
  APP.q1 = disinfo;
  APP.q3 = freedom;
})();
