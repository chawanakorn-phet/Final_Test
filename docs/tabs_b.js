/* Tabs 4-5: Scam analysis and source details. Also KPI drill-down and the summary report modal. */
(function () {
  'use strict';
  const { D, L, C, esc, card, kpi, table, mount, scope } = APP;
  const A = D.afnc, E = D.eu, H = APP.helpers;
  const F = () => APP.state.f;
  const GRAN = H.GRAN;
  const link = (u, t = 'เปิดต้นทาง') => (u ? `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>` : '–');
  const share = (w) => (w.vd ? ((w.fake + w.dist) / w.vd) * 100 : null);

  // ================================================================== 4. Scam analysis
  function damage() {
    const x = APP.ctx(), f = x.f, wk = x.wk, u = L.usable(wk), after = [], p = [], no = L.whyNot('acsc', f), gran = APP.state.gran;
    const period = APP.periodText(u.map((w) => w.ws)), periodAll = APP.periodText(wk.filter((w) => w.rep).map((w) => w.ws));
    const loss = L.sum(u.map((w) => w.loss)), cases = L.sum(u.map((w) => w.cases));
    const types = new Map(); for (const w of u) if (w.hl) { if (!types.has(w.hl)) types.set(w.hl, { weeks: 0, amt: 0, amtWeeks: 0 }); const t = types.get(w.hl); t.weeks++; if (w.hla) { t.amt += w.hla; t.amtWeeks++; } }
    const tt = [...types.entries()].sort((a, b) => b[1].weeks - a[1].weeks);
    p.push(`<h2 class="sec">2.1 ความเสียหายจากมิจฉาชีพ</h2><p class="sec-sub">ตัวเลขรวบรวมจากข่าวแถลงรายสัปดาห์ของ ศตฉอ.ตร. (ไม่ใช่ข้อมูลเปิดของตำรวจ) · เฉพาะคดีที่มีผู้แจ้งความ · ความเสียหายจริงน่าจะสูงกว่านี้</p>${no ? scope('acsc') : ''}
      <div class="kpis">${kpi({ key: 'loss', label: 'มูลค่าความเสียหายรวม', value: u.length ? `${L.fmtNum(loss / 1e6, 0)} <small>ล้านบาท</small>` : '–', sub: u.length ? `${u.length} สัปดาห์ที่ใช้ได้ · ${period}` : 'ไม่มีข้อมูลคดีในช่วงที่เลือก — ไม่ใช่ความเสียหาย 0' })}
      ${kpi({ key: 'cases', label: 'จำนวนเหตุการณ์ (คดีที่แจ้ง)', value: u.length ? L.fmtInt(cases) : '–', sub: u.length ? `คดี · ${period}` : 'ไม่มีข้อมูลคดีในช่วงที่เลือก' })}
      ${kpi({ key: 'lpc', label: 'ความเสียหายต่อคดี', value: cases ? `${L.fmtInt(loss / cases)} <small>บาท</small>` : '–', sub: 'รวมความเสียหาย ÷ รวมคดี' })}
      <div class="kpi" style="--c:#8B8588;cursor:default"><div class="k-label">จำนวนผู้เสียหาย</div><div class="k-value" style="font-size:1.05rem;white-space:normal">ไม่มีในชุดข้อมูล</div><div class="k-sub">จึงไม่แสดง (คดี ≠ ผู้เสียหาย)</div></div>
      ${kpi({ key: 'loss', label: 'ประเภทที่เสียหายสูงสุดบ่อยที่สุด', value: tt.length ? `<span style="font-size:1.05rem;white-space:normal">${esc(tt.slice().sort((a, b) => b[1].weeks - a[1].weeks)[0][0])}</span>` : '–', sub: tt.length ? `เป็นอันดับ 1 ${tt[0][1].weeks} สัปดาห์` : 'ไม่มีข้อมูลประเภท' })}</div>`);
    const per = new Map(); for (const w of u) { const k = L.periodKey(w.ws, gran); if (!per.has(k)) per.set(k, { loss: 0, cases: 0, weeks: 0 }); const q = per.get(k); q.loss += w.loss; q.cases += w.cases; q.weeks++; }
    const pr = [...per.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1));
    p.push(`<div class="row-tools">ความละเอียด: <div class="seg">${Object.entries(GRAN).map(([k, v]) => `<button data-gran="${k}" class="${gran === k ? 'on' : ''}">${v}</button>`).join('')}</div></div><div class="grid">`);
    p.push(APP.card({ id: 'm1', title: `มูลค่าความเสียหาย${GRAN[gran]} และจำนวนคดี`, unit: 'ล้านบาท (แท่ง) / คดี (เส้น)', period, src: 'ACSC', span: true, msg: pr.length ? '' : (no || 'ไม่มีข้อมูลคดีในช่วงที่เลือก (ACSC มีเฉพาะ 9 พ.ย. 2025 – 24 ต.ค. 2026)'),
      desc: 'รวมเฉพาะสัปดาห์ที่มีการแถลงและไม่ติดป้ายน่าสงสัย · ช่วงที่มีสัปดาห์ไม่ครบจะต่ำกว่าความเป็นจริง (ดูจำนวนสัปดาห์ใน tooltip) · สัปดาห์ที่ไม่มีตัวเลขไม่ถูกนับเป็นศูนย์',
      insight: pr.length ? (() => { const pk = pr.reduce((a, b) => (b[1].loss > a[1].loss ? b : a)); return `ช่วงที่เสียหายสูงสุด: ${pk[0]} (${L.fmtNum(pk[1].loss / 1e6, 0)} ล้านบาท จาก ${pk[1].weeks} สัปดาห์)`; })() : '' }));
    after.push(() => pr.length && mount('m1', { legend: { top: 0 }, tooltip: { trigger: 'axis', formatter: (q) => { const r = per.get(q[0].axisValue); return `${q[0].axisValue} (${r.weeks} สัปดาห์)<br>ความเสียหาย ${L.fmtNum(r.loss / 1e6, 0)} ล้านบาท<br>คดี ${L.fmtInt(r.cases)}`; } },
      xAxis: { type: 'category', data: pr.map((r) => r[0]) }, yAxis: [{ type: 'value', name: 'ล้านบาท' }, { type: 'value', name: 'คดี', splitLine: { show: false } }],
      series: [{ name: 'ความเสียหาย', type: 'bar', color: C.fake, data: pr.map((r) => r[1].loss / 1e6) }, { name: 'จำนวนคดี', type: 'line', yAxisIndex: 1, color: C.grey, data: pr.map((r) => r[1].cases) }] }));
    p.push(APP.card({ id: 'm2', title: 'ประเภทการหลอกลวงที่เสียหายสูงสุดของสัปดาห์', unit: 'จำนวนสัปดาห์ที่เป็นอันดับ 1', period, src: 'ACSC', msg: tt.length ? '' : (no || 'ไม่มีข้อมูลประเภท'), desc: 'ป้ายประเภทในไฟล์สะกดต่างกันหลายแบบ จัดกลุ่มเป็น 6 กลุ่ม · ข้อมูลระบุเฉพาะ "ประเภทอันดับ 1" ของแต่ละสัปดาห์',
      insight: tt.length ? `อันดับ 1: ${tt[0][0]} (${tt[0][1].weeks} สัปดาห์)` : '' }));
    after.push(() => tt.length && mount('m2', { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, grid: { left: 10, right: 40, top: 20, bottom: 10, containLabel: true }, xAxis: { type: 'value' }, yAxis: { type: 'category', inverse: true, data: tt.map((t) => t[0]) }, series: [{ type: 'bar', color: C.fake, data: tt.map((t) => t[1].weeks), label: { show: true, position: 'right' } }] }));
    const amt = tt.filter((t) => t[1].amtWeeks).sort((a, b) => b[1].amt - a[1].amt);
    p.push(APP.card({ id: 'm3', title: 'มูลค่าความเสียหายของประเภทที่สูงสุด (เฉพาะสัปดาห์ที่แถลงยอด)', unit: 'ล้านบาท (ผลรวมเท่าที่มีข้อมูล)', period, src: 'ACSC', msg: amt.length ? '' : (no || 'ไม่มีข้อมูลยอดเงินแยกประเภท'), desc: `ยอดเงินแยกประเภทมีเฉพาะ ${L.sum(amt.map((t) => t[1].amtWeeks))} สัปดาห์ และส่วนใหญ่ปัดเป็นล้านบาท จึงเป็นผลรวมบางส่วน ไม่ใช่ความเสียหายรวมของประเภทนั้น` }));
    after.push(() => amt.length && mount('m3', { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, grid: { left: 10, right: 40, top: 20, bottom: 10, containLabel: true }, xAxis: { type: 'value' }, yAxis: { type: 'category', inverse: true, data: amt.map((t) => `${t[0]} (${t[1].amtWeeks} สัปดาห์)`) }, series: [{ type: 'bar', color: C.fakeL, data: amt.map((t) => t[1].amt / 1e6), label: { show: true, position: 'right', formatter: (q) => L.fmtNum(q.value, 0) } }] }));
    p.push('</div>');
    // weekly trend with cp
    const cp = D.analysis.cp_lpc, dc = D.analysis.decomp;
    p.push('<div class="grid" style="margin-top:14px">');
    p.push(APP.card({ id: 'm4', title: 'ความเสียหายรายสัปดาห์ (สัปดาห์ที่ไม่มีข้อมูล = ช่องว่าง)', unit: 'ล้านบาท/สัปดาห์', period: periodAll, src: 'ACSC', span: true, msg: wk.some((w) => w.rep) ? '' : (no || 'ไม่มีข้อมูล'), desc: 'แถบเทา = ไม่มีการแถลง · แถบแดงอ่อน = ตัวเลขน่าสงสัย (16–22 ส.ค. 2026 รายงาน 79,311 คดี ≈ 13 เท่าของปกติ) ตัดออก · จุดโปร่ง = ตัวเลขปัด' }));
    after.push(() => { const r = wk.filter((w) => w.rep || w.sus); if (r.length) APP.lossChart('m4', wk.filter((w) => w.ws >= r[0].ws && w.ws <= r[r.length - 1].ws)); });
    if (dc && cp) {
      p.push(APP.card({ id: 'm5', title: 'ความเสียหายลดลงเพราะอะไร: จำนวนคดี หรือความเสียหายต่อคดี', unit: 'ล้านบาท/สัปดาห์ (เฉลี่ย 8 สัปดาห์)', period: `ช่วงสูงสุด ${dc.peak_start}→${dc.peak_end} vs ต่ำสุด ${dc.trough_start}→${dc.trough_end} (ทั้งช่วงข้อมูล ไม่เปลี่ยนตามตัวกรอง)`, src: 'ACSC', h: 300,
        desc: 'ความเสียหาย = จำนวนคดี × ความเสียหายต่อคดี แยกส่วนเปลี่ยนแปลงแบบผลรวมตรงกันพอดี บอกว่า "ส่วนใดเปลี่ยน" ไม่ได้บอกว่า "ทำไม"',
        insight: `ความเสียหายลด ${L.fmtNum((Math.abs(dc.loss_trough - dc.loss_peak) / dc.loss_peak) * 100, 0)}% — ${L.fmtNum((dc.severity_effect / (dc.loss_trough - dc.loss_peak)) * 100, 0)}% มาจากความเสียหายต่อคดีที่ลดลง` }));
      after.push(() => mount('m5', { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (q) => L.fmtNum(q, 0) + ' ล้านบาท' }, xAxis: { type: 'category', data: ['ช่วงสูงสุด', 'ผลจากจำนวนคดี', 'ผลจากบาท/คดี', 'ช่วงต่ำสุด'] }, yAxis: { type: 'value', name: 'ล้านบาท' },
        series: [{ type: 'bar', stack: 'w', itemStyle: { color: 'transparent' }, data: [0, dc.loss_peak / 1e6 + dc.cases_effect / 1e6, dc.loss_trough / 1e6, 0] }, { type: 'bar', stack: 'w', label: { show: true, formatter: (q) => L.fmtNum(q.value, 0) }, data: [{ value: dc.loss_peak / 1e6, itemStyle: { color: C.grey } }, { value: -dc.cases_effect / 1e6, itemStyle: { color: C.fakeL } }, { value: -dc.severity_effect / 1e6, itemStyle: { color: C.fake } }, { value: dc.loss_trough / 1e6, itemStyle: { color: C.grey } }] }] }));
    }
    p.push('</div>');
    // anomalies
    const an = D.analysis.anomalies.filter((r) => L.timeOK(r.week_start, f) || true);
    p.push(`<section class="card" style="margin-top:14px"><h3>ช่วงที่ผิดปกติ (ตรวจจากข้อมูลทั้งช่วง)</h3>${table([{ h: 'ชุดข้อมูล', f: (r) => r.series }, { h: 'สัปดาห์', f: (r) => r.week_start }, { h: 'ค่า', n: 1, f: (r) => L.fmtNum(r.value, 1) }, { h: 'ค่าคาดจากสัปดาห์รอบข้าง', n: 1, f: (r) => L.fmtNum(r.expected, 1) }, { h: 'robust z', n: 1, f: (r) => L.fmtNum(r.z, 1) }], an)}
      <div class="cap">เกณฑ์ |z| > 3.5 เทียบมัธยฐานของ 13 สัปดาห์รอบข้าง · สัปดาห์ 16–22 ส.ค. 2026 (คดี z ≈ ${L.fmtNum((D.analysis.outliers[0] || {}).robust_z, 0)}) ถูกตัดออกก่อนแล้ว · ความผิดปกติทางสถิติไม่ใช่เหตุการณ์จริงเสมอไป · ข่าวเท็จนิ่งเพราะจำนวนคำตัดสินเป็นโควตาของศูนย์ฯ</div></section>`);
    // detail rows
    const cols = [{ h: 'สัปดาห์ (อาทิตย์)', f: (w) => w.ws }, { h: 'คดี', n: 1, f: (w) => L.fmtInt(w.cases) }, { h: 'ความเสียหาย (บาท)', n: 1, f: (w) => L.fmtInt(w.loss) }, { h: 'ประเภทอันดับ 1 (คดี)', f: (w) => w.tt || '–' }, { h: 'ประเภทเสียหายสูงสุด', f: (w) => w.hl || '–' },
      { h: 'สถานะ', f: (w) => (w.sus ? 'น่าสงสัย (ตัดออก)' : !w.rep ? 'ไม่มีการแถลง' : w.rnd ? 'ใช้ได้ (ยอดปัด)' : 'ใช้ได้') }, { h: 'แหล่งที่มา', raw: 1, f: (w) => link(w.url) }];
    p.push(`<section class="card" style="margin-top:14px"><h3>รายการต้นทาง (ตรวจสอบแหล่งที่มารายสัปดาห์)</h3><div class="row-tools"><button class="btn-ghost" id="dlW">⬇ ดาวน์โหลด CSV</button></div>${table(cols, wk.filter((w) => w.rep).slice().reverse(), { max: 200 })}<div class="cap">หน่วย: คดี/บาท · ช่วงเวลา: ${esc(periodAll)} · แต่ละแถวมีลิงก์ข่าวต้นทาง</div></section>`);
    after.push(() => { const b = document.getElementById('dlW'); if (b) b.onclick = () => APP.csv('acsc_weekly_filtered.csv', cols.filter((c) => !c.raw).concat([{ h: 'source_url', f: (w) => w.url || '' }]), wk.filter((w) => w.rep)); });

    // ---- 2.2 lag analysis (same analysis as the Streamlit dashboard)
    p.push('<h2 class="sec">2.2 ประเภทภัยและความสัมพันธ์กับข่าวปลอม</h2>');
    const lag = D.analysis.lag;
    p.push(APP.card({ id: 'c2', title: 'ข่าวปลอมนำหน้าหรือตามหลังคดีหลอกลวงหรือไม่ (lag −4…+4 สัปดาห์)', unit: 'สหสัมพันธ์ r ของการเปลี่ยนแปลงรายสัปดาห์', period: 'ทั้งช่วงข้อมูล ACSC (ไม่เปลี่ยนตามตัวกรอง)', src: 'AFNC + ACSC', desc: 'ใช้การเปลี่ยนแปลงสัปดาห์ต่อสัปดาห์เพื่อตัดแนวโน้มร่วม · lag บวก = ข่าวปลอมนำหน้า · แถบเทา = เกณฑ์ ±1.96/√n · ระดับดิบ r = ' + L.fmtNum(D.analysis.detrended.raw, 2) + ' หายไปหลังตัดแนวโน้ม (r = ' + L.fmtNum(D.analysis.detrended.detrended, 2) + ')',
      insight: `มี ${lag.filter((l) => l.significant).length} จาก ${lag.length} lag ที่เกินเกณฑ์ — ไม่พบหลักฐานว่าข่าวปลอมนำหรือตามหลังคดี (ผลที่ไม่พบ ไม่ใช่การพิสูจน์ว่าไม่มี)` }));
    after.push(() => mount('c2', { xAxis: { type: 'category', data: lag.map((l) => l.lag), name: 'lag (สัปดาห์)' }, yAxis: { type: 'value', min: -0.6, max: 0.6, name: 'r' }, tooltip: { trigger: 'axis', formatter: (q) => { const l = lag[q[0].dataIndex]; return `lag ${l.lag}<br>r = ${L.fmtNum(l.r, 2)} (n=${l.n}, เกณฑ์ ±${L.fmtNum(l.ci95, 2)})`; } },
      series: [{ type: 'bar', data: lag.map((l) => ({ value: l.r, itemStyle: { color: l.significant ? C.fake : '#c9c3c5' } })), markArea: { silent: true, itemStyle: { color: 'rgba(150,150,155,.14)' }, data: [[{ yAxis: -lag[0].ci95 }, { yAxis: lag[0].ci95 }]] } }] }));
    p.push('</div>');

    return { html: p.join(''), after };
  }

  // ================================================================== 5. Data Explorer & Sources
  const DS = {
    afnc: { name: 'AFNC — โพสต์ศูนย์ต่อต้านข่าวปลอม', key: 'afnc', map: 'จำนวนข่าวปลอม' },
    acsc: { name: 'ACSC — คดีหลอกลวงรายสัปดาห์', key: 'acsc', map: 'มูลค่าความเสียหายจากมิจฉาชีพ' },
    eu: { name: 'EUvsDisinfo — การหักล้าง', key: 'eu', map: 'จำนวนการหักล้างนานาชาติ' },
    aiid: { name: 'AI Incident Database — เหตุการณ์', key: 'aiid', map: 'เหตุการณ์ AI / deepfake / scam' },
    fotn: { name: 'Freedom on the Net — คะแนน', key: 'fotn', map: 'คะแนนเสรีภาพอินเทอร์เน็ต' },
  };
  function datasetRows(id, x) {
    if (id === 'afnc') return { rows: x.ai, cols: [{ h: 'post_id', raw: 1, f: (i) => link(`https://www.antifakenewscenter.com/?p=${A.id[i]}`, A.id[i]) }, { h: 'วันที่', f: (i) => A.d[i] }, { h: 'ประเภทโพสต์', f: (i) => A.itypes[A.it[i]] }, { h: 'สถานะ', f: (i) => A.statuses[A.st[i]] }, { h: 'ประเภทข่าว', f: (i) => (A.c[i] >= 0 ? A.cats[A.c[i]] : '–') }, { h: 'หน่วยงานที่ตรวจ', f: (i) => (A.ag[i] >= 0 ? A.agencies[A.ag[i]] : '–') }, { h: 'แท็ก', f: (i) => A.tg[i] }], text: (i) => `${A.d[i]} ${A.statuses[A.st[i]]} ${A.cats[A.c[i]] || ''} ${A.tg[i]} ${A.id[i]}`,
      csv: [{ h: 'post_id', f: (i) => A.id[i] }, { h: 'date', f: (i) => A.d[i] }, { h: 'item_type', f: (i) => A.itypes[A.it[i]] }, { h: 'status', f: (i) => A.statuses[A.st[i]] }, { h: 'category', f: (i) => A.cats[A.c[i]] || '' }, { h: 'agency', f: (i) => A.agencies[A.ag[i]] || '' }, { h: 'tags', f: (i) => A.tg[i] }] };
    if (id === 'acsc') { const cols = [{ h: 'สัปดาห์', f: (w) => w.ws }, { h: 'คดี', n: 1, f: (w) => L.fmtInt(w.cases) }, { h: 'ความเสียหาย (บาท)', n: 1, f: (w) => L.fmtInt(w.loss) }, { h: 'ประเภทอันดับ 1', f: (w) => w.tt || '–' }, { h: 'ประเภทเสียหายสูงสุด', f: (w) => w.hl || '–' }, { h: 'ปัด', f: (w) => (w.rnd ? 'ใช่' : '') }, { h: 'ป้ายเตือน', f: (w) => w.flag || '' }, { h: 'แหล่งที่มา', raw: 1, f: (w) => link(w.url) }];
      return { rows: x.wk.filter((w) => w.rep), cols, text: (w) => `${w.ws} ${w.tt} ${w.hl} ${w.flag}`, csv: cols.filter((c) => !c.raw).concat([{ h: 'source_url', f: (w) => w.url || '' }]) }; }
    if (id === 'eu') { const cols = [{ h: 'วันที่', f: (i) => E.d[i] }, { h: 'ประเด็น (keywords)', f: (i) => E.k[i].map((k) => E.kw[k]).join(', ') || '–' }, { h: 'บทความ', n: 1, f: (i) => E.n[i] }, { h: 'disinformation', n: 1, f: (i) => E.nd[i] }, { h: 'trustworthy', n: 1, f: (i) => E.nt[i] }]; return { rows: x.eu, cols, text: (i) => `${E.d[i]} ${E.k[i].map((k) => E.kw[k]).join(' ')}`, csv: cols }; }
    if (id === 'aiid') { const R = D.aiid; const cols = [{ h: 'ID', raw: 1, f: (r) => link(`https://incidentdatabase.ai/cite/${r[0]}`, r[0]) }, { h: 'วันที่เกิดเหตุ', f: (r) => r[1] }, { h: 'ชื่อเหตุการณ์', f: (r) => r[2] }, { h: 'Risk Domain', f: (r) => (r[3] >= 0 ? R.risk[r[3]] : 'ยังไม่จัดหมวด') }, { h: 'Intent', f: (r) => (r[4] >= 0 ? R.intent[r[4]] : '–') }, { h: 'deepfake', f: (r) => (r[5] ? '✓' : '') }, { h: 'scam/fraud', f: (r) => (r[6] ? '✓' : '') }, { h: 'ไทย', f: (r) => (r[7] ? '✓' : '') }, { h: 'ข่าว', n: 1, f: (r) => r[8] }];
      return { rows: x.ac, cols, text: (r) => `${r[1]} ${r[2]}`, csv: cols.filter((c) => !c.raw).concat([{ h: 'id', f: (r) => r[0] }]) }; }
    const cols = [{ h: 'ประเทศ', f: (r) => r.country }, { h: 'ปีข้อมูล', n: 1, f: (r) => r.y }, { h: 'คะแนนรวม', n: 1, f: (r) => r.total }, { h: 'เข้าถึง /25', n: 1, f: (r) => r.acc }, { h: 'เนื้อหา /35', n: 1, f: (r) => r.con }, { h: 'สิทธิผู้ใช้ /40', n: 1, f: (r) => r.rig }, { h: 'สถานะ', f: (r) => ['', 'เสรี', 'เสรีบางส่วน', 'ไม่เสรี'][r.st] }];
    return { rows: x.fo, cols, text: (r) => `${r.country} ${r.y}`, csv: cols };
  }

  function explorer() {
    const x = APP.ctx(), f = x.f, id = APP.state.ds || 'afnc', q = (APP.state.q || '').trim().toLowerCase(), after = [], p = [];
    const ds = datasetRows(id, x), why = L.whyNot(DS[id].key, f);
    let rows = ds.rows; if (q) rows = rows.filter((r) => ds.text(r).toLowerCase().includes(q));
    p.push(`<h2 class="sec">4.1 สำรวจข้อมูลต้นทาง</h2><p class="sec-sub">ตารางตามตัวกรองที่เลือก · ค้นหา ดาวน์โหลด CSV และตรวจสอบแหล่งที่มา</p>${why ? scope(DS[id].key) : ''}
      <div class="row-tools"><select class="sel" data-state="ds">${Object.entries(DS).map(([k, v]) => `<option value="${k}"${k === id ? ' selected' : ''}>${esc(v.name)}</option>`).join('')}</select>
      <input class="sel" id="exQ" type="search" placeholder="ค้นหา แล้วกด Enter" value="${esc(APP.state.q || '')}" style="min-width:220px"><button class="btn-ghost" id="exDl">⬇ ดาวน์โหลด CSV (${L.fmtInt(rows.length)} แถว)</button></div>
      ${table(ds.cols, rows, { max: 300 })}`);
    after.push(() => { const b = document.getElementById('exDl'); if (b) b.onclick = () => APP.csv(`${id}_filtered.csv`, ds.csv, rows); const s = document.getElementById('exQ'); if (s) s.onkeydown = (e) => { if (e.key === 'Enter') { APP.state.q = s.value; APP.refresh(); } }; });
    const m = D.source_map.find((r) => r[0] === DS[id].map);
    if (m) p.push(`<div class="note"><b>แหล่งที่มา:</b> ${esc(m[1])} · <code>${esc(m[2])}</code> · ${esc(m[3])}<br><b>วิธีคำนวณ:</b> ${esc(m[4])}</div>`);

    return { html: p.join(''), after };
  }

  function quality() {
    const html = `<h2 class="sec">ตรวจสอบคุณภาพข้อมูล</h2><p class="sec-sub">ผลตรวจคุณภาพและบันทึกการทำความสะอาดข้อมูลก่อนนำไปวิเคราะห์</p>
      <div class="grid"><section class="card"><h3>ผลตรวจคุณภาพข้อมูล (${D.validation.length} รายการ)</h3>${table([{ h: 'สถานะ', f: (r) => ({ ok: '✅ ผ่าน', warn: '⚠ ระวัง', fail: '❌ ไม่ผ่าน' })[r.status] }, { h: 'รายการตรวจ', f: (r) => r.check }, { h: 'รายละเอียด', f: (r) => r.detail }], D.validation)}</section>
      <section class="card"><h3>บันทึกการทำความสะอาด (ก่อน → หลัง)</h3>${table([{ h: 'ชุดข้อมูล', f: (r) => r.dataset }, { h: 'สิ่งที่ทำ', f: (r) => r.action }, { h: 'ก่อน', n: 1, f: (r) => r.before }, { h: 'หลัง', n: 1, f: (r) => r.after }], D.cleaning)}</section></div>`;
    return { html };
  }

  APP.addTab('q1', 'Q1 ข้อมูลบิดเบือน: สากล vs ไทย', APP.q1);
  APP.addTab('q2', 'Q2 ภัยหลอกลวงและความผิดปกติ', damage);
  APP.addTab('q3', 'Q3 เสรีภาพอินเทอร์เน็ตและภัย AI', APP.q3);
  APP.addTab('details', 'รายละเอียดแต่ละชุดข้อมูล', explorer);
  APP.addTab('quality', 'คุณภาพข้อมูล', quality);

  // ================================================================== KPI drill-down
  APP.onKpi = (key) => {
    const x = APP.ctx(), f = x.f, vi = A.itypes.indexOf('Verdict');
    const afncRows = (pred) => x.ai.filter((i) => A.it[i] === vi && pred(A.st[i]));
    const cols = datasetRows('afnc', x).csv, afncCols = [{ h: 'post_id', raw: 1, f: (i) => link(`https://www.antifakenewscenter.com/?p=${A.id[i]}`, A.id[i]) }, ...datasetRows('afnc', x).cols.slice(1)];
    const go = { verdict: ['กรณีข้อมูลบิดเบือนที่ตรวจแล้ว (คำตัดสิน AFNC)', 'จำนวนข่าวปลอม', afncCols, afncRows(() => true), 'afnc_verdicts.csv'], fake: ['ข่าวปลอม (คำตัดสิน)', 'จำนวนข่าวปลอม', afncCols, afncRows((s) => s === 0), 'afnc_fake.csv'], real: ['ข่าวจริง (คำตัดสิน)', 'จำนวนข่าวจริง', afncCols, afncRows((s) => s === 2), 'afnc_true.csv'] };
    if (go[key]) { const g = go[key]; return APP.detail({ title: g[0], map: g[1], cols: g[2], rows: g[3], file: g[4] }); }
    if (key === 'eu') { const d = datasetRows('eu', x); return APP.detail({ title: 'การหักล้างระดับนานาชาติ (EUvsDisinfo)', map: 'จำนวนการหักล้างนานาชาติ', cols: d.cols, rows: d.rows, file: 'eu_debunks.csv' }); }
    if (key === 'loss' || key === 'cases' || key === 'lpc') { const d = datasetRows('acsc', x); return APP.detail({ title: 'รายสัปดาห์ของคดีหลอกลวง (ACSC) พร้อมลิงก์ข่าวต้นทาง', map: 'มูลค่าความเสียหายจากมิจฉาชีพ', cols: d.cols, rows: d.rows, file: 'acsc_weekly.csv' }); }
    if (key === 'aiid') { const d = datasetRows('aiid', x); return APP.detail({ title: 'เหตุการณ์ AI ก่อปัญหา (AIID)', map: 'เหตุการณ์ AI / deepfake / scam', cols: d.cols, rows: d.rows, file: 'aiid_incidents.csv' }); }
    if (key.startsWith('f')) { const d = datasetRows('fotn', x); return APP.detail({ title: 'คะแนนเสรีภาพอินเทอร์เน็ต (Freedom on the Net)', map: 'คะแนนเสรีภาพอินเทอร์เน็ต', cols: d.cols, rows: d.rows.slice().sort((a, b) => b.y - a.y || b.total - a.total), file: 'freedom_scores.csv' }); }
  };
})();
