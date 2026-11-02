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
    const x = ctx(), f = x.f, pf = L.prevFilters(f, D.meta), px = pf ? ctx(pf) : null;
    const v = verdictIdx(x.ai), sc = statusCounts(v), pv = px ? statusCounts(verdictIdx(px.ai)) : null;
    const delta = (now, prev, ok) => (px && ok && prev ? L.pctChange(now, prev) : null);
    const loss = usableLoss(x.wk), ploss = px ? usableLoss(px.wk) : 0;
    const periodA = APP.periodText(x.ai.map((i) => A.d[i])), periodW = APP.periodText(L.usable(x.wk).map((w) => w.ws)), periodE = APP.periodText(x.eu.map((i) => E.d[i]));
    const th = L.fotnRows(D, { ...f, region: 'th' }), thL = latestFotn(th);
    const thRow = thL.rows[0];
    let cmpLabel = 'ประเทศที่เลือกเปรียบเทียบ', cmpVal = null, cmpSub = 'เลือกประเทศในตัวกรองด้านซ้าย';
    const others = x.fo.filter((r) => r.iso3 !== 'THA');
    if (thRow) {
      const same = others.filter((r) => r.y === thRow.y);
      if (f.countries.length && same.length) { cmpLabel = same[0].country; cmpVal = same.find((r) => r.iso3 === f.countries[0])?.total ?? same[0].total; cmpLabel = (same.find((r) => r.iso3 === f.countries[0]) || same[0]).country; cmpSub = `ปีข้อมูล ${thRow.y}`; }
      else if (same.length) { cmpLabel = `มัธยฐานของ ${same.length} ประเทศที่เลือก`; cmpVal = median(same.map((r) => r.total)); cmpSub = `ปีข้อมูล ${thRow.y}`; }
    }
    const kp = [
      kpi({ key: 'verdict', label: 'กรณีข้อมูลบิดเบือนที่ตรวจแล้ว (AFNC)', value: L.fmtInt(v.length), sub: `คำตัดสิน · ${periodA}`, delta: delta(v.length, pv && L.sum(pv.slice(0, 3)), true) }),
      kpi({ key: 'fake', label: 'ข่าวปลอม', value: L.fmtInt(sc[0]), sub: `ข่าวปลอม (Fake) · ${periodA}`, delta: delta(sc[0], pv && pv[0], true) }),
      kpi({ key: 'real', label: 'ข่าวจริง', value: L.fmtInt(sc[2]), sub: `ข่าวที่ตรวจแล้วเป็นจริง · ${periodA}`, delta: delta(sc[2], pv && pv[2], true), color: C.real }),
      kpi({ key: 'eu', label: 'การหักล้างระดับนานาชาติ (EU)', value: L.fmtInt(x.eu.length), sub: `debunk ไม่ซ้ำ · ${periodE}`, delta: delta(x.eu.length, px && px.eu.length, true), color: C.teal }),
      kpi({ key: 'loss', label: 'มูลค่าความเสียหายจากมิจฉาชีพ', value: L.usable(x.wk).length ? L.fmtNum(loss / 1e6, 0) + ' <small>ล้านบาท</small>' : '–', sub: L.usable(x.wk).length ? `เฉพาะสัปดาห์ที่ใช้ได้ ${L.usable(x.wk).length} สัปดาห์ · ${periodW}` : (L.whyNot('acsc', f) || 'ไม่มีข้อมูลคดีในช่วงที่เลือก (ACSC มีเฉพาะ 9 พ.ย. 2025 – 24 ต.ค. 2026) — ไม่ใช่ความเสียหาย 0'), delta: delta(loss, ploss, ploss > 0) }),
      kpi({ key: 'fotn_th', label: 'คะแนนเสรีภาพอินเทอร์เน็ต ไทย', value: thRow ? `${thRow.total}<small>/100</small>` : '–', sub: thRow ? `ปีข้อมูล ${thRow.y} · ${['', 'เสรี', 'เสรีบางส่วน', 'ไม่เสรี'][thRow.st]}` : 'ไม่มีข้อมูลในช่วงที่เลือก', color: C.blue }),
      kpi({ key: 'fotn_cmp', label: cmpLabel, value: cmpVal === null ? '–' : `${L.fmtNum(cmpVal, cmpVal % 1 ? 1 : 0)}<small>/100</small>`, sub: cmpSub, color: C.blue }),
      kpi({ key: 'aiid', label: 'เหตุการณ์ AI ก่อปัญหา (AIID)', value: L.fmtInt(x.ac.length), sub: `เหตุการณ์ · ${APP.periodText(x.ac.map((r) => r[1]))}`, delta: delta(x.ac.length, px && px.ac.length, true), color: C.purple }),
    ].join('');

    // ---- charts
    const cards = [], after = [];
    const mon = byPeriod(v, 'month');
    cards.push(APP.card({ id: 'o1', title: 'แนวโน้มจำนวนข่าวปลอม', unit: 'เรื่อง/เดือน', period: periodA, src: 'AFNC', msg: mon.length ? '' : (L.whyNot('afnc', f) || 'ไม่มีข้อมูลในช่วงที่เลือก'),
      desc: 'จำนวนคำตัดสินข่าวปลอมและข่าวบิดเบือนรายเดือนของศูนย์ต่อต้านข่าวปลอม จำนวนที่ศูนย์ฯ เลือกตรวจ ไม่ใช่ปริมาณข่าวปลอมจริงในสังคม',
      insight: mon.length ? (() => { const pk = mon.reduce((a, b) => (b[1][0] > a[1][0] ? b : a)); return `เดือนที่ข่าวปลอมสูงสุดคือ ${pk[0]} (${L.fmtInt(pk[1][0])} เรื่อง)`; })() : '' }));
    after.push(() => mon.length && mount('o1', { legend: { top: 0 }, xAxis: { type: 'category', data: mon.map((m) => m[0]) }, yAxis: { type: 'value', name: 'เรื่อง' }, dataZoom: [{ type: 'inside' }],
      series: [{ name: 'ข่าวปลอม', type: 'line', data: mon.map((m) => m[1][0]), color: C.fake, showSymbol: false, areaStyle: { opacity: 0.08 } }, { name: 'ข่าวบิดเบือน', type: 'line', data: mon.map((m) => m[1][1]), color: C.fakeL, showSymbol: false }] }));

    const rep = x.wk.filter((w) => w.rep || w.sus), wkAll = rep.length ? x.wk.filter((w) => w.ws >= rep[0].ws && w.ws <= rep[rep.length - 1].ws) : [];
    const lossMsg = wkAll.length ? '' : (L.whyNot('acsc', f) || 'ไม่มีข้อมูลคดีในช่วงที่เลือก (ข้อมูล ACSC มีเฉพาะ 9 พ.ย. 2025 – 24 ต.ค. 2026)');
    cards.push(APP.card({ id: 'o2', title: 'แนวโน้มมูลค่าความเสียหายจากมิจฉาชีพ', unit: 'ล้านบาท/สัปดาห์', period: periodW, src: 'ACSC', msg: lossMsg,
      desc: 'แถบเทา = สัปดาห์ที่ไม่มีการแถลง (ไม่ใช่ 0) · แถบแดงอ่อน = ตัวเลขน่าสงสัย ตัดออก · จุดโปร่ง = ตัวเลขที่ปัดเป็นล้านบาท',
      insight: (() => { const u = L.usable(x.wk); if (u.length < 8) return ''; const a = L.sum(u.slice(-4).map((w) => w.loss)) / 4, b = L.sum(u.slice(-8, -4).map((w) => w.loss)) / 4; return `4 สัปดาห์ล่าสุดเฉลี่ย ${L.fmtNum(a / 1e6, 0)} ล้านบาท/สัปดาห์ (${L.pctChange(a, b) > 0 ? '+' : ''}${L.fmtNum(L.pctChange(a, b), 1)}% เทียบ 4 สัปดาห์ก่อนหน้า)`; })() }));
    after.push(() => wkAll.length && lossChart('o2', wkAll));

    const yr = new Map(); for (const i of x.ai) { const k = L.yearOf(A.d[i]); if (!yr.has(k)) yr.set(k, [0, 0, 0, 0]); yr.get(k)[A.st[i]]++; }
    const yrs = [...yr.entries()].sort((a, b) => a[0] - b[0]);
    cards.push(APP.card({ id: 'o3', title: 'สัดส่วนข่าวจริง ข่าวปลอม และประเภทอื่น', unit: '% ของโพสต์ที่ศูนย์ฯ เผยแพร่ในปีนั้น', period: periodA, src: 'AFNC', msg: yrs.length ? '' : (L.whyNot('afnc', f) || 'ไม่มีข้อมูล'),
      desc: 'ตัวหารคือโพสต์ทั้งหมดของศูนย์ฯ ในปีนั้น (รวมบทความ ประกาศเตือน ฯลฯ ที่ไม่ใช่คำตัดสิน) ไม่ใช่สัดส่วนข่าวปลอมในสังคม',
      insight: yrs.length ? `ปีล่าสุด ${yrs[yrs.length - 1][0]}: ข่าวปลอม ${L.fmtNum(yrs[yrs.length - 1][1][0] / L.sum(yrs[yrs.length - 1][1]) * 100, 1)}% · ข่าวจริง ${L.fmtNum(yrs[yrs.length - 1][1][2] / L.sum(yrs[yrs.length - 1][1]) * 100, 1)}%` : '' }));
    after.push(() => yrs.length && mount('o3', { legend: { top: 0 }, tooltip: { trigger: 'axis', valueFormatter: (q) => q.toFixed(1) + '%' }, xAxis: { type: 'category', data: yrs.map((y) => y[0]) }, yAxis: { type: 'value', max: 100, name: '%' },
      series: ['ข่าวปลอม', 'ข่าวบิดเบือน', 'ข่าวจริง', 'อื่น ๆ'].map((n, k) => ({ name: n, type: 'bar', stack: 's', color: STC[k], data: yrs.map((y) => (y[1][k] / L.sum(y[1])) * 100) })) }));

    const cat = new Map(); for (const i of v) { if (A.c[i] >= 0) cat.set(A.cats[A.c[i]], (cat.get(A.cats[A.c[i]]) || 0) + 1); }
    const cats = [...cat.entries()].sort((a, b) => a[1] - b[1]);
    cards.push(APP.card({ id: 'o4', title: 'ประเภทข่าวที่พบมากที่สุด', unit: 'เรื่อง (คำตัดสิน)', period: periodA, src: 'AFNC', msg: cats.length ? '' : (L.whyNot('afnc', f) || 'ไม่มีข้อมูล'),
      desc: 'หมวดข่าวตามที่ปรากฏในข้อมูลของศูนย์ฯ (หมวดเล็กรวมเป็น "อื่น ๆ"; หมวด "อาชญากรรมออนไลน์" เพิ่งมีปี 2026)',
      insight: cats.length ? `อันดับ 1 คือ ${cats[cats.length - 1][0]} (${L.fmtInt(cats[cats.length - 1][1])} เรื่อง, ${L.fmtNum((cats[cats.length - 1][1] / v.length) * 100, 1)}%)` : '' }));
    after.push(() => cats.length && mount('o4', { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, grid: { left: 10, right: 40, top: 20, bottom: 10, containLabel: true }, xAxis: { type: 'value' }, yAxis: { type: 'category', data: cats.map((c) => c[0]) },
      series: [{ type: 'bar', data: cats.map((c) => c[1]), color: C.fake, label: { show: true, position: 'right' } }] }));

    const lf = latestFotn(x.fo); let fr = lf.rows.sort((a, b) => b.total - a.total);
    if (fr.length > 22) fr = [...fr.slice(0, 10), ...fr.slice(-6), ...fr.filter((r) => r.iso3 === 'THA' && !fr.slice(0, 10).includes(r) && !fr.slice(-6).includes(r))];
    cards.push(APP.card({ id: 'o5', title: 'เปรียบเทียบคะแนนเสรีภาพอินเทอร์เน็ตระหว่างประเทศ', unit: 'คะแนน 0–100 (สูง = เสรี)', period: lf.y ? `ปีข้อมูล ${lf.y}` : '–', src: 'Freedom on the Net', span: true, msg: fr.length ? '' : (L.whyNot('fotn', f) || 'ไม่มีข้อมูลในช่วงที่เลือก'),
      desc: 'ไทยแสดงเป็นสีแดงเข้ม · ถ้ามีมากกว่า 22 ประเทศ จะแสดง 10 อันดับสูงสุด 6 อันดับต่ำสุด และไทย',
      insight: lf.y ? (() => { const rk = L.fotnRank(D.fotn, 'THA', lf.y); return rk ? `ไทยอยู่อันดับ ${rk.rank} จาก ${rk.n} ประเทศ (ปีข้อมูล ${lf.y}, ${rk.score} คะแนน)` : ''; })() : '' }));
    after.push(() => fr.length && mount('o5', { xAxis: { type: 'category', data: fr.map((r) => r.country), axisLabel: { interval: 0, rotate: 40, fontSize: 10 } }, yAxis: { type: 'value', max: 100 }, grid: { bottom: 90, left: 40, right: 12, top: 30, containLabel: true },
      series: [{ type: 'bar', data: fr.map((r) => ({ value: r.total, itemStyle: { color: r.iso3 === 'THA' ? C.fake : '#c9c3c5' } })) }] }));

    // ---- insights + findings
    const bul = [];
    if (mon.length) { const pk = mon.reduce((a, b) => (b[1][0] > a[1][0] ? b : a)); bul.push(`ช่วงเวลาที่มีข่าวปลอมมากที่สุด: เดือน ${pk[0]} (${L.fmtInt(pk[1][0])} เรื่อง)`); }
    if (cats.length) bul.push(`ประเภทข่าวที่พบมากที่สุด: ${cats[cats.length - 1][0]} (${L.fmtNum((cats[cats.length - 1][1] / v.length) * 100, 1)}% ของคำตัดสินในช่วงที่เลือก)`);
    const u = L.usable(x.wk); if (u.length >= 8) { const a = L.sum(u.slice(-4).map((w) => w.loss)), b = L.sum(u.slice(-8, -4).map((w) => w.loss)); bul.push(`มูลค่าความเสียหาย 4 สัปดาห์ล่าสุด ${L.fmtNum(a / 1e6, 0)} ล้านบาท (${L.pctChange(a, b) > 0 ? '+' : ''}${L.fmtNum(L.pctChange(a, b), 1)}% เทียบ 4 สัปดาห์ก่อนหน้า, ตัวเลขช่วงหลังเป็นค่าปัด)`); }
    const rkT = L.fotnRank(D.fotn, 'THA', D.analysis.asean ? Math.max(...D.fotn.map((r) => r.y)) : 0);
    if (rkT) bul.push(`เสรีภาพอินเทอร์เน็ตของไทย ${rkT.score}/100 อันดับ ${rkT.rank} จาก ${rkT.n} ประเทศ (ปีข้อมูล ${Math.max(...D.fotn.map((r) => r.y))}) · อันดับ ${D.analysis.asean.rank} จาก ${D.analysis.asean.n} ในอาเซียน`);
    const fnd = D.analysis.findings, pick = [fnd.q2[0], fnd.q2[1], fnd.q1[3], fnd.q2[2], fnd.q1[4], fnd.q3[2]].filter(Boolean);
    const html = `
      <h2 class="sec">ภาพรวมสถานการณ์</h2><p class="sec-sub">คลิกที่การ์ดตัวเลขเพื่อดูรายการต้นทาง แหล่งที่มา และวิธีคำนวณ · ตัวเลขทุกตัวระบุช่วงเวลา</p>
      <div class="kpis">${kp}</div>
      <div class="grid" style="margin-top:14px">${cards.join('')}</div>
      <h2 class="sec">สรุป Insight จากข้อมูลที่เลือก</h2>
      <div class="card"><ul style="margin:0;padding-left:18px">${bul.map((b) => `<li>${esc(b)}</li>`).join('') || '<li>ไม่มีข้อมูลในช่วงที่เลือก</li>'}</ul></div>
      <h2 class="sec">ข้อค้นพบที่มีหลักฐานเชิงสถิติรองรับ</h2><p class="sec-sub">คำนวณด้วย Python จากข้อมูลทั้งช่วง (ไม่เปลี่ยนตามตัวกรอง) — เปิดสวิตช์ "คำอธิบาย" เพื่อดูรายละเอียดและข้อควรระวัง</p>
      <div class="findings">${pick.map((p) => `<div class="find">${esc(p.headline)}<small class="desc">${esc(p.detail)}<br><i>ข้อควรระวัง: ${esc(p.caution)}</i></small></div>`).join('')}</div>`;
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
    p.push(`<h2 class="sec">2.1 วิเคราะห์ตามเวลา</h2><p class="sec-sub">จำนวนข่าวปลอม (คำตัดสิน "ข่าวปลอม") และข่าวบิดเบือน แยกตามช่วงเวลา</p>${noA ? scope('afnc') : ''}
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

    // ---- 2.2 categories
    p.push('<h2 class="sec">2.2 วิเคราะห์ประเภทข่าว</h2><p class="sec-sub">ใช้หมวดหมู่ที่ปรากฏในข้อมูลของศูนย์ต่อต้านข่าวปลอม (หมวด Economy, Drugs, Other news รวมเป็น "อื่น ๆ"; แปลเป็นไทย)</p>');
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
      data: cr.map((r, i) => ({ name: r.k.replace(/\s*\(.*\)/, ''), value: r.n, itemStyle: { color: ['#254F6F', '#C35A73', '#C9841D', '#D9A441', '#3565A8', '#0F766E', '#8B9AA5'][i % 7] } })) }] }));
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

    // ---- 2.3 verdict share
    p.push('<h2 class="sec">2.3 สัดส่วนข่าวจริงและข่าวปลอม</h2><p class="sec-sub">สัดส่วนของ "ข่าวที่ศูนย์ต่อต้านข่าวปลอมเลือกตรวจ" ไม่ใช่สัดส่วนข่าวปลอมทั้งหมดในสังคม — ศูนย์ฯ ไม่ได้สุ่มตรวจ</p>');
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
      series: [['อุปสรรคการเข้าถึง (เต็ม 25)', 'acc', '#72BDB5'], ['การจำกัดเนื้อหา (เต็ม 35)', 'con', '#3565A8'], ['สิทธิผู้ใช้ (เต็ม 40)', 'rig', '#12324A']].map(([n, k, c]) => ({ name: n, type: 'bar', stack: 's', color: c, data: thAll.map((r) => r[k]) })) }));
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
      visualMap: { min: 0, max: 100, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#BD5962', '#F3DADC', '#ffffff', '#D3EBE5', '#2C8A68'] } },
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

  APP.addTab('overview', '1 ภาพรวม', overview);
  APP.addTab('disinfo', '2 ข่าวปลอมและข้อมูลบิดเบือน', disinfo);
  APP.addTab('freedom', '3 เสรีภาพอินเทอร์เน็ตและเปรียบเทียบประเทศ', freedom);
})();
