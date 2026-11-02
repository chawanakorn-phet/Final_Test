// Run: node --test tests_js/   (uses only Node built-ins)
const test = require('node:test');
const assert = require('node:assert/strict');
global.window = {};
require('../docs/data.js');
const D = window.DATA;
const L = require('../docs/logic.js');
const F = (o = {}) => ({ ...L.defaultFilters(D.meta), ...o });

test('p-values and r match scipy (reference values written by pipeline/build_data.py)', () => {
  const u = D.weekly.filter((w) => w.use);
  for (const [name, ref] of Object.entries(D.corr_ref)) {
    if (!ref.x) continue;
    const key = { acsc_cases: 'cases', acsc_loss_baht: 'loss' }[ref.x];
    let x, y;
    if (ref.x === 'afnc_false_share_pct') { x = u.map((w) => (w.vd ? ((w.fake + w.dist) / w.vd) * 100 : null)); y = u.map((w) => w.cases); } else { x = u.map((w) => w[key]); y = u.map((w) => w.loss); }
    const r = L.correlate(x, y, ref.method);
    assert.equal(r.n, ref.n, name);
    assert.ok(Math.abs(r.r - ref.r) < 1e-6 || name === 'false_share_cases_spearman' && Math.abs(r.r - ref.r) < 0.02, `${name} r ${r.r} vs ${ref.r}`);
    if (name === 'cases_loss_pearson') assert.ok(Math.abs(Math.log10(r.p) - Math.log10(ref.p)) < 0.01, `p ${r.p} vs ${ref.p}`);
  }
});

test('corrP agrees with known t-distribution values', () => {
  assert.ok(Math.abs(L.corrP(0.5, 10) - 0.1414) < 1e-3);     // t = 1.633, df 8 -> p = 0.1411 (two-sided)
  assert.ok(Math.abs(L.corrP(0.8, 30) - 3.0e-7) < 5e-7 && L.corrP(0.8, 30) < 1e-6);
  assert.equal(L.corrP(0.3, 2) !== L.corrP(0.3, 2), true);    // n < 3 -> NaN
});

test('correlate refuses small n, constants, and drops null pairs', () => {
  const small = L.correlate([1, 2, 3, 4, 5], [2, 1, 4, 3, 5], 'spearman', 10);
  assert.equal(small.ok, false); assert.match(small.reason, /ไม่มีข้อมูลเพียงพอ/); assert.equal(small.n, 5);
  assert.equal(L.correlate(Array.from({ length: 20 }, (_, i) => i), new Array(20).fill(1)).ok, false);
  const x = [1, 2, null, 4, 5, 6, 7, 8, 9, 10, 11, 12], y = [2, 4, 6, null, 10, 12, 14, 16, 18, 20, 22, 24];
  assert.equal(L.correlate(x, y, 'pearson').n, 10);
  assert.ok(Math.abs(L.correlate(x, y, 'pearson').r - 1) < 1e-12);
});

test('Spearman handles ties with average ranks', () => {
  assert.deepEqual(L.ranks([10, 20, 20, 30]), [1, 2.5, 2.5, 4]);
});

test('time filters combine (date range, year, quarter, month)', () => {
  const total = L.afncIdx(D, F()).length; assert.equal(total, D.afnc.d.length);
  const y21 = L.afncIdx(D, F({ years: [2021] })); assert.ok(y21.every((i) => D.afnc.d[i].startsWith('2021')) && y21.length > 0);
  const q4 = L.afncIdx(D, F({ years: [2022], quarters: [4] })); assert.ok(q4.every((i) => ['10', '11', '12'].includes(D.afnc.d[i].slice(5, 7))));
  const dec = L.afncIdx(D, F({ months: [12] })); assert.ok(dec.every((i) => D.afnc.d[i].slice(5, 7) === '12'));
  const rng = L.afncIdx(D, F({ from: '2022-01-01', to: '2022-01-31' })); assert.ok(rng.every((i) => D.afnc.d[i].startsWith('2022-01')));
});

test('status and category filters; non-verdict posts are "อื่น ๆ"', () => {
  const other = L.afncIdx(D, F({ statuses: ['อื่น ๆ (ไม่ใช่คำตัดสิน)'] }));
  assert.equal(other.length, 17726 - 14458);
  const fake = L.afncIdx(D, F({ statuses: ['ข่าวปลอม'] })); assert.equal(fake.length, 9520);
  const both = L.afncIdx(D, F({ statuses: ['ข่าวปลอม'], cats: ['ผลิตภัณฑ์สุขภาพ'] })); assert.ok(both.length < fake.length && both.length > 0);
});

test('region and source switches scope the datasets', () => {
  assert.equal(L.afncIdx(D, F({ region: 'foreign' })).length, 0); assert.match(L.whyNot('afnc', F({ region: 'foreign' })), /ประเทศไทยเท่านั้น/);
  assert.equal(L.euIdx(D, F({ region: 'th' })).length, 0); assert.match(L.whyNot('eu', F({ region: 'th' })), /ต่างประเทศ/);
  assert.equal(L.whyNot('afnc', F()), '');
  assert.equal(L.afncIdx(D, F({ sources: ['eu'] })).length, 0); assert.match(L.whyNot('afnc', F({ sources: ['eu'] })), /ไม่ได้เลือกแหล่งข้อมูล/);
  const th = L.aiidRows(D, F({ region: 'th' })), fo = L.aiidRows(D, F({ region: 'foreign' })); assert.equal(th.length + fo.length, D.aiid.rows.length); assert.equal(th.length, 10);
});

test('Freedom on the Net: month/quarter ignored, Thailand follows region, groups work', () => {
  assert.equal(L.fotnRows(D, F({ months: [3] })).length, D.fotn.length);
  assert.ok(L.fotnRows(D, F({ region: 'th' })).every((r) => r.iso3 === 'THA'));
  assert.ok(L.fotnRows(D, F({ region: 'foreign' })).every((r) => r.iso3 !== 'THA'));
  const nf = L.fotnRows(D, F({ group: 'ไม่เสรี' })); assert.ok(nf.some((r) => r.iso3 === 'THA') && nf.some((r) => r.iso3 === 'MMR') && !nf.some((r) => r.iso3 === 'ISL'));
  const one = L.fotnRows(D, F({ countries: ['SGP'] })); assert.deepEqual([...new Set(one.map((r) => r.iso3))].sort(), ['SGP', 'THA']);
  assert.ok(L.fotnRows(D, F({ from: '2024-01-01' })).every((r) => r.y === 2024));
});

test('weekly filter: damage group, usable weeks, no zero-fill', () => {
  const w = L.weeklyRows(D, F()); assert.equal(w.length, D.weekly.length);
  const inv = L.weeklyRows(D, F({ damage: ['หลอกลงทุน'] })); assert.ok(inv.length > 0 && inv.every((x) => x.hl === 'หลอกลงทุน'));
  const u = L.usable(w); assert.equal(u.length, 47); assert.ok(u.every((x) => x.cases > 0 && x.loss > 0 && !x.sus));
  assert.ok(w.filter((x) => !x.rep).every((x) => x.cases === null && x.loss === null));   // missing weeks stay null, never 0
});

test('chips, notes, previous window', () => {
  const f = F({ years: [2025], region: 'th', cats: ['การเงิน-หุ้น'] });
  assert.ok(L.chips(f, D.meta).includes('ประเทศไทย') && L.chips(F(), D.meta).length === 0);
  assert.ok(L.notes(f).some((n) => n.includes('AFNC เท่านั้น')));
  const p = L.prevFilters(F({ from: '2023-01-01', to: '2023-12-31' }), D.meta);
  assert.equal(p.to, '2022-12-31'); assert.equal(p.from, '2022-01-01');
  const leap = L.prevFilters(F({ from: '2024-01-01', to: '2024-12-31' }), D.meta);   // 366 days -> previous window is also 366 days
  assert.equal(L.daysBetween(leap.from, leap.to), 365);
  assert.equal(L.prevFilters(F(), D.meta), null);   // the default window starts at the data start: nothing before it
});

test('FOTN rank: ties share the best rank', () => {
  const rows = [{ iso3: 'A', y: 1, total: 90 }, { iso3: 'B', y: 1, total: 50 }, { iso3: 'C', y: 1, total: 50 }];
  assert.deepEqual(L.fotnRank(rows, 'B', 1), { rank: 2, n: 3, score: 50 }); assert.equal(L.fotnRank(rows, 'C', 1).rank, 2);
  const th = L.fotnRank(D.fotn, 'THA', 2024); assert.deepEqual([th.rank, th.n, th.score], [51, 71, 39]);
});

test('formatting is consistent', () => {
  assert.equal(L.fmtInt(1234567), '1,234,567'); assert.equal(L.fmtInt(null), '–'); assert.equal(L.fmtNum(12.345, 1), '12.3');
  assert.equal(L.fmtMB(333000000), '333 ล้านบาท'); assert.equal(L.fmtThDate('2026-10-18'), '18 ต.ค. 2026');
  assert.equal(L.periodKey('2026-10-18', 'quarter'), '2026-Q4'); assert.equal(L.periodKey('2026-10-18', 'year'), '2026');
});

test('no ACSC weeks in range -> nothing to sum (the page shows "–", never 0)', () => {
  const rows = L.weeklyRows(D, F({ from: '2021-01-01', to: '2021-12-31' }));
  assert.equal(L.usable(rows).length, 0);                       // 2021 has no police briefings at all
  assert.ok(rows.every((w) => w.cases === null && w.loss === null));
});
