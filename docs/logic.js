/* Pure logic (no DOM): filters, aggregation, statistics. Loaded by the page and by the Node tests (tests_js/). */
(function (root) {
  'use strict';
  const L = {};

  // ------------------------------------------------------------------ dates
  const ymd = (d) => (d ? d.slice(0, 10) : null);
  const yearOf = (d) => +d.slice(0, 4);
  const monthOf = (d) => +d.slice(5, 7);
  const quarterOf = (d) => Math.ceil(monthOf(d) / 3);
  L.yearOf = yearOf; L.monthOf = monthOf; L.quarterOf = quarterOf;
  L.periodKey = (d, gran) => (gran === 'year' ? String(yearOf(d)) : gran === 'quarter' ? `${yearOf(d)}-Q${quarterOf(d)}` : d.slice(0, 7));
  L.addDays = (d, n) => new Date(new Date(d + 'T00:00:00Z').getTime() + n * 864e5).toISOString().slice(0, 10);
  L.daysBetween = (a, b) => Math.round((new Date(b + 'T00:00:00Z') - new Date(a + 'T00:00:00Z')) / 864e5);

  // ------------------------------------------------------------------ filters
  const SRC = { afnc: 'AFNC (ข่าวปลอมไทย)', acsc: 'ACSC (คดีหลอกลวง)', eu: 'EUvsDisinfo', aiid: 'AI Incident Database', fotn: 'Freedom on the Net' };
  const REGIONS = { all: 'ทั้งหมด', th: 'ประเทศไทย', foreign: 'ต่างประเทศ' };
  const TH_MONTHS = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
  L.SRC = SRC; L.REGIONS = REGIONS; L.TH_MONTHS = TH_MONTHS;

  L.defaultFilters = (meta) => ({
    from: meta.date_min, to: meta.date_max, years: [], quarters: [], months: [], region: 'all', group: 'ทุกประเทศ', countries: [],
    cats: [], statuses: [], damage: [], sources: Object.keys(SRC),
  });
  const has = (f, key) => f.sources.includes(key);
  const timeOK = (d, f) => {
    if (d === null || d === undefined) return false;
    if (d < f.from || d > f.to) return false;
    if (f.years.length && !f.years.includes(yearOf(d))) return false;
    if (f.quarters.length && !f.quarters.includes(quarterOf(d))) return false;
    if (f.months.length && !f.months.includes(monthOf(d))) return false;
    return true;
  };
  L.timeOK = timeOK;

  // Each *Rows function returns the indices (or rows) that pass; [] when the dataset is out of scope.
  L.afncIdx = (D, f) => {
    const A = D.afnc, out = [];
    if (!has(f, 'afnc') || f.region === 'foreign') return out;
    const catIdx = f.cats.map((c) => A.cats.indexOf(c)), stIdx = f.statuses.map((s) => A.statuses.indexOf(s));
    for (let i = 0; i < A.d.length; i++) {
      if (!timeOK(A.d[i], f)) continue;
      if (catIdx.length && !catIdx.includes(A.c[i])) continue;
      if (stIdx.length && !stIdx.includes(A.st[i])) continue;
      out.push(i);
    }
    return out;
  };
  L.weeklyRows = (D, f) => {
    if (!has(f, 'acsc') || f.region === 'foreign') return [];
    return D.weekly.filter((w) => timeOK(w.ws, f) && (!f.damage.length || f.damage.includes(w.hl)));
  };
  L.euIdx = (D, f) => {
    const E = D.eu, out = [];
    if (!has(f, 'eu') || f.region === 'th') return out;
    for (let i = 0; i < E.d.length; i++) if (timeOK(E.d[i], f)) out.push(i);
    return out;
  };
  L.aiidRows = (D, f) => {
    if (!has(f, 'aiid')) return [];
    return D.aiid.rows.filter((r) => timeOK(r[1], f) && (f.region === 'all' || (f.region === 'th') === (r[7] === 1)));
  };
  L.fotnRows = (D, f) => {
    if (!has(f, 'fotn')) return [];
    const y0 = yearOf(f.from), y1 = yearOf(f.to);
    let rows = D.fotn.filter((r) => r.y >= y0 && r.y <= y1 && (!f.years.length || f.years.includes(r.y)));
    if (f.region === 'th') return rows.filter((r) => r.iso3 === 'THA');
    const lastY = Math.max(...D.fotn.map((r) => r.y));
    let keep = new Set(D.fotn.map((r) => r.iso3));
    if (f.group === 'อาเซียน') keep = new Set(Object.keys(D.meta.asean));
    else if (['เสรี', 'เสรีบางส่วน', 'ไม่เสรี'].includes(f.group)) {
      const code = { 'เสรี': 1, 'เสรีบางส่วน': 2, 'ไม่เสรี': 3 }[f.group];
      keep = new Set(D.fotn.filter((r) => r.y === lastY && r.st === code).map((r) => r.iso3));
    }
    if (f.countries.length) keep = new Set(f.countries);
    if (f.region === 'foreign') return rows.filter((r) => keep.has(r.iso3) && r.iso3 !== 'THA');
    return rows.filter((r) => keep.has(r.iso3) || r.iso3 === 'THA');
  };

  L.whyNot = (key, f) => {
    if (!has(f, key)) return `ไม่ได้เลือกแหล่งข้อมูล ${SRC[key]} ในตัวกรอง`;
    if ((key === 'afnc' || key === 'acsc') && f.region === 'foreign') return `${SRC[key]} เป็นข้อมูลของประเทศไทยเท่านั้น — ตัวกรองถูกตั้งเป็น 'ต่างประเทศ'`;
    if (key === 'eu' && f.region === 'th') return "EUvsDisinfo เป็นข้อมูลต่างประเทศ (ไม่มีรายการของไทย) — ตัวกรองถูกตั้งเป็น 'ประเทศไทย'";
    return '';
  };
  L.notes = (f) => {
    const out = [];
    if (f.months.length || f.quarters.length) out.push('เดือน/ไตรมาส ไม่ใช้กับ Freedom on the Net (ข้อมูลรายปี)');
    if (f.cats.length || f.statuses.length) out.push('ประเภทข่าว/สถานะข่าว ใช้กับ AFNC เท่านั้น (EUvsDisinfo ใช้การจัดหมวดคนละระบบ)');
    if (f.damage.length) out.push('หมวดหมู่ความเสียหาย ใช้กับ ACSC โดยเลือกสัปดาห์ที่ประเภทที่เสียหายสูงสุดตรงกับที่เลือก');
    if (f.countries.length || f.group !== 'ทุกประเทศ') out.push('ประเทศ/กลุ่มประเทศ ใช้กับ Freedom on the Net เท่านั้น (AFNC/ACSC เป็นของไทย)');
    return out;
  };
  L.chips = (f, meta) => {
    const out = [];
    if (f.from !== meta.date_min || f.to !== meta.date_max) out.push(`ช่วงวันที่ ${f.from} → ${f.to}`);
    if (f.years.length) out.push('ปี ' + f.years.join(', '));
    if (f.quarters.length) out.push('ไตรมาส ' + f.quarters.map((q) => 'Q' + q).join(', '));
    if (f.months.length) out.push('เดือน ' + f.months.map((m) => TH_MONTHS[m - 1]).join(', '));
    if (f.region !== 'all') out.push(REGIONS[f.region]);
    if (f.group !== 'ทุกประเทศ') out.push('กลุ่ม: ' + f.group);
    if (f.countries.length) out.push(`ประเทศ ${f.countries.length} ประเทศ`);
    if (f.cats.length) out.push(`ประเภทข่าว ${f.cats.length} หมวด`);
    if (f.statuses.length) out.push('สถานะ: ' + f.statuses.join(', '));
    if (f.damage.length) out.push('ความเสียหาย: ' + f.damage.join(', '));
    if (f.sources.length !== Object.keys(SRC).length) out.push(`แหล่งข้อมูล ${f.sources.length}/${Object.keys(SRC).length}`);
    return out;
  };
  /** The window of equal length immediately before [from, to] (for 'vs previous period'); null when it would leave the data. */
  L.prevFilters = (f, meta) => {
    const n = L.daysBetween(f.from, f.to) + 1;
    const to = L.addDays(f.from, -1), from = L.addDays(f.from, -n);
    if (from < meta.date_min) return null;
    return { ...f, from, to };
  };

  // ------------------------------------------------------------------ aggregation
  L.count = (keys) => { const m = new Map(); for (const k of keys) m.set(k, (m.get(k) || 0) + 1); return m; };
  L.sum = (a) => a.reduce((x, y) => x + y, 0);
  L.sortedEntries = (m) => [...m.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1));
  L.pctChange = (now, prev) => (prev === null || prev === undefined || prev === 0 || now === null ? null : ((now - prev) / prev) * 100);
  L.fotnRank = (fotn, iso3, year) => {
    const y = fotn.filter((r) => r.y === year); const me = y.find((r) => r.iso3 === iso3);
    return me ? { rank: y.filter((r) => r.total > me.total).length + 1, n: y.length, score: me.total } : null;
  };
  /** Weekly rows that count in the statistics: reported and not flagged suspect. */
  L.usable = (rows) => rows.filter((w) => w.use);

  // ------------------------------------------------------------------ statistics
  function lgamma(x) {
    const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
    let y = x, t = x + 5.5; t -= (x + 0.5) * Math.log(t); let s = 1.000000000190015;
    for (const cj of c) s += cj / ++y;
    return -t + Math.log((2.5066282746310005 * s) / x);
  }
  function betacf(a, b, x) {
    const MAXIT = 300, EPS = 3e-14, FPMIN = 1e-300;
    const qab = a + b, qap = a + 1, qam = a - 1; let c = 1, d = 1 - (qab * x) / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN; d = 1 / d; let h = d;
    for (let m = 1; m <= MAXIT; m++) {
      const m2 = 2 * m; let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN; d = 1 / d; h *= d * c;
      aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN; d = 1 / d;
      const del = d * c; h *= del; if (Math.abs(del - 1) < EPS) break;
    }
    return h;
  }
  /** Regularised incomplete beta I_x(a, b). */
  L.betai = (a, b, x) => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? (bt * betacf(a, b, x)) / a : 1 - (bt * betacf(b, a, 1 - x)) / b;
  };
  /** Two-sided p-value for a correlation coefficient r from n pairs (t-distribution, df = n - 2). */
  L.corrP = (r, n) => {
    if (n < 3) return NaN; if (Math.abs(r) >= 1) return 0;
    const df = n - 2, t2 = (r * r * df) / (1 - r * r);
    return L.betai(df / 2, 0.5, df / (df + t2));
  };
  L.ranks = (v) => {
    const idx = v.map((x, i) => [x, i]).sort((a, b) => a[0] - b[0]); const r = new Array(v.length);
    for (let i = 0; i < idx.length;) { let j = i; while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++; const avg = (i + j) / 2 + 1; for (let k = i; k <= j; k++) r[idx[k][1]] = avg; i = j + 1; }
    return r;
  };
  const pearsonR = (a, b) => {
    const n = a.length, ma = L.sum(a) / n, mb = L.sum(b) / n; let sab = 0, saa = 0, sbb = 0;
    for (let i = 0; i < n; i++) { sab += (a[i] - ma) * (b[i] - mb); saa += (a[i] - ma) ** 2; sbb += (b[i] - mb) ** 2; }
    return sab / Math.sqrt(saa * sbb);
  };
  const INSUFFICIENT = 'ไม่มีข้อมูลเพียงพอสำหรับการวิเคราะห์นี้';
  L.INSUFFICIENT = INSUFFICIENT;
  /** Pearson/Spearman with a validity gate: below minN complete pairs (or a constant variable) nothing is computed. */
  L.correlate = (x, y, method = 'spearman', minN = 10) => {
    const a = [], b = [];
    for (let i = 0; i < x.length; i++) if (x[i] !== null && y[i] !== null && Number.isFinite(x[i]) && Number.isFinite(y[i])) { a.push(x[i]); b.push(y[i]); }
    const out = { method, n: a.length, r: NaN, p: NaN, ok: false, reason: '', a, b };
    if (a.length < minN) { out.reason = `${INSUFFICIENT}: มีคู่ข้อมูลที่ใช้ได้ ${a.length} คู่ (ต้องการอย่างน้อย ${minN})`; return out; }
    if (Math.max(...a) === Math.min(...a) || Math.max(...b) === Math.min(...b)) { out.reason = `${INSUFFICIENT}: ตัวแปรหนึ่งมีค่าคงที่ทุกแถว`; return out; }
    out.r = method === 'spearman' ? pearsonR(L.ranks(a), L.ranks(b)) : pearsonR(a, b);
    out.p = L.corrP(out.r, a.length); out.ok = true; return out;
  };
  L.strength = (r) => { const a = Math.abs(r); return a < 0.2 ? 'ไม่มี/อ่อนมาก' : a < 0.4 ? 'อ่อน' : a < 0.6 ? 'ปานกลาง' : a < 0.8 ? 'ค่อนข้างแรง' : 'แรง'; };
  L.interpret = (res, alpha = 0.05) => {
    if (!res.ok) return res.reason;
    const dir = res.r > 0 ? 'ไปทางเดียวกัน' : 'สวนทางกัน', sig = res.p < alpha ? 'มีนัยสำคัญทางสถิติ' : 'ไม่มีนัยสำคัญทางสถิติ';
    return `${res.method === 'spearman' ? 'Spearman' : 'Pearson'} r = ${res.r.toFixed(2)} (ความสัมพันธ์${L.strength(res.r)} ${dir}), p = ${res.p < 0.001 ? res.p.toExponential(1) : res.p.toFixed(3)} (${sig} ที่ α = ${alpha}), n = ${res.n} · ไม่ใช่หลักฐานเชิงเหตุและผล`;
  };
  L.linfit = (a, b) => { const n = a.length, ma = L.sum(a) / n, mb = L.sum(b) / n; let sab = 0, saa = 0; for (let i = 0; i < n; i++) { sab += (a[i] - ma) * (b[i] - mb); saa += (a[i] - ma) ** 2; } const k = sab / saa; return { k, c: mb - k * ma }; };

  // ------------------------------------------------------------------ formatting (consistent across the page)
  L.fmtInt = (x) => (x === null || x === undefined || Number.isNaN(x) ? '–' : Math.round(x).toLocaleString('en-US'));
  L.fmtNum = (x, d = 1) => (x === null || x === undefined || Number.isNaN(x) ? '–' : x.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }));
  L.fmtMB = (baht) => (baht === null || baht === undefined ? '–' : L.fmtNum(baht / 1e6, 0) + ' ล้านบาท');
  L.fmtDate = (d) => (d ? d.slice(0, 10) : '–');
  L.fmtThDate = (d) => { if (!d) return '–'; return `${+d.slice(8, 10)} ${TH_MONTHS[monthOf(d) - 1]} ${yearOf(d)}`; };

  if (typeof module !== 'undefined' && module.exports) module.exports = L; else root.L = L;
})(typeof window !== 'undefined' ? window : globalThis);
