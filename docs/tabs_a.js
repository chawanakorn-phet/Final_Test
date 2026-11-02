/* Tabs 1-3: Overview, Disinformation & Fake News, Internet Freedom & Country Comparison. */
(function () {
  'use strict';
  const { D, L, C, esc, card, kpi, table, mount, empty, scope, periodText } = APP;
  const A = D.afnc, E = D.eu, VI = A.itypes.indexOf('Verdict');
  const ST = { fake: 0, dist: 1, real: 2, other: 3 };
  const STC = [C.blue, C.orange, C.real, C.other];
  const CATEGORY_COLORS = ['#3565A8', '#D9902B', '#2C8A68', '#7663A8', '#C95F4B', '#12324A', '#8494A1'];
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
    const x = ctx(), after = [], w = x.wk, showAfNC = x.f.sources.includes('afnc'), showAIID = x.f.sources.includes('aiid');
    const usable = L.usable(w), latest = usable[usable.length - 1];
    const lastDate = w[w.length - 1]?.ws;
    const recent = lastDate ? w.filter((r) => r.ws > L.addDays(lastDate, -28)) : [];
    const recentVd = L.sum(recent.map((r) => r.vd));
    const falsePct = showAfNC && recentVd ? 100 * L.sum(recent.map((r) => r.fake + r.dist)) / recentVd : null;
    const cards = [
      kpi({ key: 'cases', label: `คดีออนไลน์ สัปดาห์ ${latest?.ws || '–'}`, value: latest ? L.fmtInt(latest.cases) : '–', sub: 'คดีที่มีการแถลงและผ่านการตรวจข้อมูล' }),
      kpi({ key: 'loss', label: 'ความเสียหายสัปดาห์นั้น', value: latest ? L.fmtMB(latest.loss) : '–', sub: latest?.rnd ? 'ยอดที่แถลงปัดเป็นล้านบาท' : 'ACSC' }),
      kpi({ key: 'lpc', label: 'ความเสียหายต่อคดี', value: latest?.cases ? `${L.fmtInt(latest.loss / latest.cases)} บาท` : '–', sub: 'คำนวณจากยอดรวม ÷ จำนวนคดี' }),
      kpi({ key: 'fake', label: 'สัดส่วนข่าวเท็จ 4 สัปดาห์ล่าสุด', value: falsePct === null ? '–' : `${L.fmtNum(falsePct, 1)}%`, sub: 'ข่าวปลอม + ข่าวบิดเบือน ในคำตัดสิน AFNC' }),
      kpi({ key: 'aiid', label: 'เหตุการณ์ AI ในฐานข้อมูลโลก', value: showAIID ? L.fmtInt(D.meta.n_aiid_incidents) : '–', sub: `AI Incident Database · ฉบับ ${D.meta.aiid_snapshot}`, color: C.purple }),
    ].join('');
    const plotStart = w.find((r) => r.rep || r.sus)?.ws;
    const plot = plotStart ? w.filter((r) => r.ws >= plotStart) : [];
    const findings = D.analysis.findings;
    const picks = [findings.q1[0], findings.q2[0], findings.q3[0], findings.q1[1], findings.q2[1], findings.q3[1]].filter(Boolean);
    const html = `<h2 class="sec">ภาพรวม</h2><div class="kpis">${cards}</div>
      <h2 class="sec">คดีหลอกลวง vs ข่าวเท็จ</h2>
      ${APP.card({ id: 'ov_main', title: 'แนวโน้มรายสัปดาห์: คดี ความเสียหาย และสัดส่วนข่าวเท็จ', unit: 'คดี · ล้านบาท · %', period: APP.periodText(plot.map((r) => r.ws)), src: 'ACSC + AFNC', span: true,
        desc: 'สัปดาห์ที่ไม่มีการแถลงเป็นช่องว่าง ไม่ใช่ศูนย์ · สัปดาห์ตัวเลขน่าสงสัยถูกตัดออกจากเส้นคดี/ความเสียหาย · ข่าวปลอมและข่าวบิดเบือนเป็นสัดส่วนของคำตัดสิน AFNC' })}
      <p class="hint">จำนวนคำตัดสิน AFNC สะท้อนเรื่องที่ศูนย์ฯ เลือกตรวจ ไม่ใช่จำนวนข่าวปลอมทั้งหมดในสังคม</p>
      <h2 class="sec">ข้อค้นพบสำคัญ</h2><div class="findings">${picks.map((r) => `<div class="find">${esc(r.headline)}<small class="desc">${esc(r.detail)}<br><i>ข้อควรระวัง: ${esc(r.caution)}</i></small></div>`).join('')}</div>`;
    after.push(() => {
      if (!plot.length) return;
      const dates = plot.map((r) => r.ws);
      mount('ov_main', { legend: { top: 0, data: ['คดี', 'ความเสียหาย (ล้านบาท)', 'สัดส่วนข่าวเท็จ (%)'] }, tooltip: { trigger: 'axis' },
        grid: [{ left: 62, right: 20, top: 38, height: '25%' }, { left: 62, right: 20, top: '37%', height: '25%' }, { left: 62, right: 20, top: '69%', height: '23%' }],
        xAxis: [0, 1, 2].map((i) => ({ type: 'category', gridIndex: i, data: dates, axisLabel: { show: i === 2 } })),
        yAxis: [{ type: 'value', gridIndex: 0, name: 'คดี' }, { type: 'value', gridIndex: 1, name: 'ล้านบาท' }, { type: 'value', gridIndex: 2, name: '%', min: 0, max: 100 }],
        series: [
          { name: 'คดี', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: plot.map((r) => r.use ? r.cases : null), color: C.scam, connectNulls: false, showSymbol: true },
          { name: 'ความเสียหาย (ล้านบาท)', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: plot.map((r) => r.use ? r.loss / 1e6 : null), color: C.orange, connectNulls: false, showSymbol: true },
          { name: 'สัดส่วนข่าวเท็จ (%)', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: plot.map((r) => showAfNC && r.vd ? (r.fake + r.dist) / r.vd * 100 : null), color: C.fake, connectNulls: false, showSymbol: true },
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
    const x=ctx(), after=[], p=[], f=x.f, maxYear=L.yearOf(f.to), minYear=Math.min(maxYear,Math.max(2020,L.yearOf(f.from)));
    const q1Start=Math.max(minYear,Math.min(maxYear,APP.state.q1Start??minYear)), q1End=Math.max(q1Start,Math.max(minYear,Math.min(maxYear,APP.state.q1End??maxYear))), q1Cats=APP.state.q1Cats??A.cats.slice(), q1Verdicts=APP.state.q1Verdicts||['ข่าวปลอม','ข่าวบิดเบือน'];
    const yearsFrom=Math.max(minYear,q1Start), yearsTo=Math.min(maxYear,q1End), baseAi=x.ai.filter(i=>L.yearOf(A.d[i])>=yearsFrom&&L.yearOf(A.d[i])<=yearsTo);
    const catBaseAi=baseAi.filter(i=>q1Cats.includes(A.cats[A.c[i]])), selectedAi=catBaseAi.filter(i=>q1Verdicts.includes(A.statuses[A.st[i]]));
    const verdicts=verdictIdx(catBaseAi), falseIdx=verdicts.filter(i=>A.st[i]===0||A.st[i]===1), cats=A.cats;
    const eu=x.eu.filter(i=>L.yearOf(E.d[i])>=yearsFrom&&L.yearOf(E.d[i])<=yearsTo), kwCount=new Map(); for(const i of eu) for(const k of E.k[i]) kwCount.set(E.kw[k],(kwCount.get(E.kw[k])||0)+1);
    const topKw=[...kwCount.entries()].sort((a,b)=>b[1]-a[1]).slice(0,12).reverse();
    const catYear=new Map(), verdictYear=new Map();
    for(const i of selectedAi){const y=L.yearOf(A.d[i]);if(!verdictYear.has(y))verdictYear.set(y,[0,0,0,0]);verdictYear.get(y)[A.st[i]]++;}
    for(const i of selectedAi){const y=L.yearOf(A.d[i]);if(A.c[i]>=0){const k=`${y}|${cats[A.c[i]]}`;catYear.set(k,(catYear.get(k)||0)+1);}}
    const ys=[...verdictYear.keys()].sort((a,b)=>a-b), catNames=[...new Set([...catYear.keys()].map(k=>k.split('|').slice(1).join('|')))],
      topCat=catNames.map(c=>[c,L.sum([...catYear.entries()].filter(([k])=>k.endsWith(`|${c}`)).map(([,v])=>v))]).sort((a,b)=>b[1]-a[1])[0];
    const totalVerd=L.sum(verdicts.map(i=>1)), falsePct=totalVerd?falseIdx.length/totalVerd*100:null;
    const status=[0,0,0,0]; for(const i of verdicts) status[A.st[i]]++;
    const euDebunks=eu.length;
    const kpis=`${kpi({key:'eu',label:'การหักล้างนานาชาติ (EU)',value:L.fmtInt(euDebunks),sub:`${eu.length.toLocaleString()} เรื่องที่ไม่ซ้ำ · ${eu.length?APP.periodText(eu.map(i=>E.d[i])):'ไม่มีข้อมูล'}`,color:C.global})}${kpi({key:'verdict',label:'คำตัดสินไทย (AFNC)',value:L.fmtInt(totalVerd),sub:`ข่าวปลอม/บิดเบือน/จริง · ${APP.periodText(catBaseAi.map(i=>A.d[i]))}`})}${kpi({key:'fake',label:'สัดส่วนข่าวเท็จ',value:falsePct===null?'–':`${L.fmtNum(falsePct,1)}%`,sub:'ปลอม + บิดเบือน จากคำตัดสิน'})}${kpi({key:'fake',label:'หมวดใหญ่สุดของไทย',value:topCat?.[0]||'–',sub:topCat?`${L.fmtInt(topCat[1])} เรื่อง`:'ไม่มีข้อมูล'})}${kpi({key:'eu',label:'ประเด็นนำของ EU',value:topKw.at(-1)?.[0]||'–',sub:topKw.length?`${L.fmtInt(topKw.at(-1)[1])} การหักล้าง`:'ไม่มีข้อมูล',color:C.global})}`;
    p.push(`<h2 class="sec">Q1 ข้อมูลบิดเบือน: สากล vs ไทย</h2><p class="sec-sub">${esc('รูปแบบ เนื้อหา และประเภทของข้อมูลบิดเบือนต่างกันอย่างไรระหว่างระดับนานาชาติกับไทย และอะไรเปลี่ยนไปตามเวลา')}</p>${scope('afnc')}<div class="filterbar local-filter"><label>ปีเริ่ม <select data-state="q1Start" data-state-type="number">${Array.from({length:Math.max(0,maxYear-minYear+1)},(_,i)=>minYear+i).map(y=>`<option value="${y}"${y===q1Start?' selected':''}>${y}</option>`).join('')}</select></label><label>ปีสิ้นสุด <select data-state="q1End" data-state-type="number">${Array.from({length:Math.max(0,maxYear-minYear+1)},(_,i)=>minYear+i).map(y=>`<option value="${y}"${y===q1End?' selected':''}>${y}</option>`).join('')}</select></label><button class="btn-ghost" data-local-reset="q1">ล้างตัวกรอง Q1</button><div class="chips">${A.cats.map(c=>`<button class="chip${q1Cats.includes(c)?' on':''}" data-local-toggle="q1Cats" data-value="${esc(c)}">${esc(c.replace(/\s*\(.*\)/,''))}</button>`).join('')}</div><div class="chips">${A.statuses.slice(0,3).map(s=>`<button class="chip${q1Verdicts.includes(s)?' on':''}" data-local-toggle="q1Verdicts" data-value="${esc(s)}">${esc(s)}</button>`).join('')}</div></div><div class="kpis">${kpis}</div>`);
    p.push('<h2 class="sec">ลักษณะของข้อมูลบิดเบือน</h2><div class="grid">');
    p.push(APP.card({id:'q1_eu_kw',title:'ประเด็นข้อมูลบิดเบือนระดับนานาชาติ (EUvsDisinfo)',unit:'การหักล้างต่อประเด็น',period:APP.periodText(eu.map(i=>E.d[i])),src:'EUvsDisinfo',msg:topKw.length?'':(L.whyNot('eu',f)||'ไม่มีข้อมูลในช่วงที่เลือก'),desc:'นับต่อเรื่องที่ถูกหักล้าง หนึ่งเรื่องอาจมีหลายประเด็น'}));
    after.push(()=>topKw.length&&mount('q1_eu_kw',{grid:{left:15,right:35,top:12,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',data:topKw.map(r=>r[0])},series:[{type:'bar',data:topKw.map(r=>r[1]),color:C.global,label:{show:true,position:'right'}}]}));
    p.push(APP.card({id:'q1_cat',title:'ข่าวเท็จไทยตามหมวด (% ต่อปี)',unit:'% ของข่าวปลอม + บิดเบือนในปีนั้น',period:`${yearsFrom}–${yearsTo}`,src:'AFNC',desc:'สัดส่วนตามหมวดข่าว · ปี 2026 เพิ่มหมวดอาชญากรรมออนไลน์',msg:selectedAi.length?'':'เลือกอย่างน้อยหนึ่งหมวดและผลตรวจ'}));
    after.push(()=>catNames.length&&mount('q1_cat',{legend:{type:'scroll',top:0},xAxis:{type:'category',data:ys.map(String)},yAxis:{type:'value',min:0,max:100,name:'%'},series:catNames.map((c,j)=>({name:c,type:'bar',stack:'s',color:CATEGORY_COLORS[j%CATEGORY_COLORS.length],data:ys.map(y=>{const sum=L.sum(catNames.map(n=>catYear.get(`${y}|${n}`)||0));return sum?(catYear.get(`${y}|${c}`)||0)/sum*100:0;})}))}));
    p.push('</div><h2 class="sec">สัดส่วนข่าวจริง/ปลอม/บิดเบือน</h2><div class="grid">');
    p.push(APP.card({id:'q1_verdict',title:'ผลคำตัดสินไทยรายปี (% ของคำตัดสินที่เลือก)',unit:'%',period:`${yearsFrom}–${yearsTo}`,src:'AFNC',desc:'ผลตรวจในข้อมูลที่ศูนย์ฯ เลือกตรวจ ไม่ใช่สัดส่วนข่าวทั้งหมดในสังคม',msg:selectedAi.length?'':'เลือกอย่างน้อยหนึ่งหมวดและผลตรวจ'}));
    after.push(()=>ys.length&&mount('q1_verdict',{legend:{top:0},xAxis:{type:'category',data:ys.map(String)},yAxis:{type:'value',min:0,max:100,name:'%'},series:q1Verdicts.map(n=>{const k=A.statuses.indexOf(n), c=[C.blue,C.orange,C.real,C.other][k];return{name:n,type:'bar',stack:'s',color:c,data:ys.map(y=>{const r=verdictYear.get(y);return L.sum(r)?r[k]/L.sum(r)*100:0;})};})}));
    const euYear=new Map(); for(const i of eu){const y=L.yearOf(E.d[i]);if(!euYear.has(y))euYear.set(y,[0,0]);euYear.get(y)[0]+=E.nd[i];euYear.get(y)[1]+=E.nt[i];}
    const ey=[...euYear.keys()].filter(y=>y>=2017).sort((a,b)=>a-b);
    p.push(APP.card({id:'q1_eu_mix',title:'EUvsDisinfo: ประเภทบทความที่ผูกกับการหักล้าง (%)',unit:'%',period:APP.periodText(eu.map(i=>E.d[i])),src:'EUvsDisinfo',desc:'EU ไม่มีป้ายข่าวจริง/ปลอม/บิดเบือนโดยตรง จึงไม่ควรเทียบกับสัดส่วน AFNC ตรง ๆ'}));
    after.push(()=>ey.length&&mount('q1_eu_mix',{legend:{top:0},xAxis:{type:'category',data:ey.map(String)},yAxis:{type:'value',min:0,max:100,name:'%'},series:[{name:'disinformation',type:'bar',stack:'s',color:C.purple,data:ey.map(y=>{const r=euYear.get(y);return L.sum(r)?r[0]/L.sum(r)*100:0;})},{name:'trustworthy',type:'bar',stack:'s',color:C.orange,data:ey.map(y=>{const r=euYear.get(y);return L.sum(r)?r[1]/L.sum(r)*100:0;})}]}));
    p.push('</div><h2 class="sec">เปลี่ยนแปลงตามเวลา</h2><div class="grid">');
    const covid=D.analysis.covid.filter(r=>r.year>=yearsFrom&&r.year<=yearsTo), covidYears=[...new Set(covid.map(r=>r.year))];
    p.push(APP.card({id:'q1_covid',title:'สัดส่วนเรื่องเกี่ยวกับโควิดในไทยและระดับนานาชาติ',unit:'% ของข่าวเท็จ/การหักล้างในปีนั้น',period:'2018–2026',src:'AFNC + EUvsDisinfo',desc:'นิยามแท็กของไทยกับ keywords ของ EU ต่างกัน เปรียบเทียบแนวโน้ม ไม่ใช่จำนวนตรงกัน'}));
    after.push(()=>mount('q1_covid',{legend:{top:0},xAxis:{type:'category',data:covidYears.map(String)},yAxis:{type:'value',name:'%'},series:['AFNC (ไทย)','EUvsDisinfo'].map((src,j)=>({name:src,type:'line',connectNulls:false,showSymbol:true,color:j?C.purple:C.fake,data:covidYears.map(y=>covid.find(r=>r.year===y&&r.source===src)?.share_pct??null)}))}));
    const scam=D.analysis.scam_share.filter(r=>r.year>=yearsFrom&&r.year<=yearsTo);
    p.push(APP.card({id:'q1_scam_share',title:'ข่าวเท็จที่เกี่ยวกับการแอบอ้าง/หลอกลวง',unit:'% ของข่าวเท็จที่มีแท็ก',period:scam.length?`${scam[0].year}–${scam.at(-1).year}`:'–',src:'AFNC',desc:'วัดสัดส่วนในข่าวเท็จที่มีแท็ก ไม่ใช่สัดส่วนของข่าวทั้งหมด'}));
    after.push(()=>scam.length&&mount('q1_scam_share',{xAxis:{type:'category',data:scam.map(r=>String(r.year))},yAxis:{type:'value',name:'%',min:0,max:50},series:[{type:'line',data:scam.map(r=>r.scam_share_of_tagged_pct),color:C.scam,symbolSize:7}]}));
    const addChange=(id,title,rows,color)=>{p.push(APP.card({id,title,unit:'เปลี่ยนแปลง (จุดเปอร์เซ็นต์)',period:'ช่วงคงที่จากข้อมูลทั้งช่วง',src:id.includes('thai')?'AFNC':'EUvsDisinfo',h:380}));const d=[...rows.slice(0,6),...rows.slice(-6)].filter((r,i,a)=>a.findIndex(z=>z.topic===r.topic)===i).sort((a,b)=>a.change_pp-b.change_pp);after.push(()=>mount(id,{grid:{left:15,right:35,top:15,bottom:15,containLabel:true},xAxis:{type:'value',name:'จุดเปอร์เซ็นต์'},yAxis:{type:'category',data:d.map(r=>r.topic)},series:[{type:'bar',data:d.map(r=>({value:r.change_pp,itemStyle:{color:r.change_pp>0?color:C.grey}})),label:{show:true,position:'right',formatter:q=>`${q.value>0?'+':''}${q.value.toFixed(1)}`}}]}));};
    addChange('q1_th_change',`หัวข้อข่าวเท็จไทย เพิ่ม/ลดมากสุด (${D.analysis.thai_years[0]}→${D.analysis.thai_years[1]})`,D.analysis.thai_rising,C.scam);
    addChange('q1_eu_change',`ประเด็น EU เพิ่ม/ลดมากสุด (${D.analysis.eu_years[0]}→${D.analysis.eu_years[1]})`,D.analysis.eu_rising,C.global);
    const mix=D.analysis.mix, residuals=mix.residuals, mxYears=residuals.map(r=>r.year), mixCats=Object.keys(residuals[0]||{}).filter(k=>k!=='year');
    p.push(APP.card({id:'q1_heat',title:'หมวดข่าวเท็จที่เกิน/ขาดจากสัดส่วนที่คาด',unit:'Pearson residual',period:`2020–${mxYears.at(-1)||'–'}`,src:'AFNC',desc:`χ²=${L.fmtNum(mix.chi2,0)} · V=${L.fmtNum(mix.v,2)} · น้ำเงิน = ต่ำกว่าที่คาด · เขียวอมฟ้า = สูงกว่าที่คาด`}));
    after.push(()=>residuals.length&&mount('q1_heat',{grid:{left:25,right:65,top:10,bottom:30,containLabel:true},xAxis:{type:'category',data:mixCats},yAxis:{type:'category',data:mxYears.map(String),inverse:true},visualMap:{min:-12,max:12,calculable:false,orient:'vertical',right:0,top:'center',inRange:{color:['#3565A8','#fff','#0F766E']}},series:[{type:'heatmap',data:residuals.flatMap((r,yi)=>mixCats.map((c,xi)=>[xi,yi,r[c]])),label:{show:true,formatter:q=>q.data[2].toFixed(1)}}]}));
    p.push('</div><h2 class="sec">ข้อค้นพบ</h2>');
    const fs=D.analysis.findings.q1||[]; p.push(`<div class="findings">${fs.map((r,i)=>`<div class="find"><b>${i+1}.</b> ${esc(r.headline)}<small class="desc">${esc(r.detail)}<br><i>ข้อควรระวัง: ${esc(r.caution)}</i></small></div>`).join('')}</div>`);
    return {html:p.join(''),after};
  }

  function filteredThemeOverlap(f, aiFrom, aiTo) {
    const useAI=f.sources.includes('aiid'), useAFNC=f.sources.includes('afnc')&&f.region!=='foreign';
    const rows=D.analysis.theme_year.filter(r=>r.source==='AIID'?useAI&&r.year>=aiFrom&&r.year<=aiTo:useAFNC&&r.source==='AFNC'&&r.year>=L.yearOf(f.from)&&r.year<=L.yearOf(f.to)&&(!f.years.length||f.years.includes(r.year)));
    const counts=new Map(), totals={AIID:0,AFNC:0}, seen=new Set();
    for(const r of rows){const key=`${r.source}|${r.theme_th}`;if(!counts.has(key))counts.set(key,0);counts.set(key,counts.get(key)+r.n);const yearKey=`${r.source}|${r.year}`;if(!seen.has(yearKey)){totals[r.source]+=r.total;seen.add(yearKey);}}
    const themes=[...new Set(rows.map(r=>r.theme_th))];
    return themes.map(theme=>{const nAIID=counts.get(`AIID|${theme}`)||0,nAFNC=counts.get(`AFNC|${theme}`)||0,sAIID=totals.AIID?nAIID/totals.AIID*100:0,sAFNC=totals.AFNC?nAFNC/totals.AFNC*100:0;let status='น้อยทั้งสองฝั่ง';if(sAIID>=2&&nAFNC>=30&&sAFNC>=2)status='ซ้อนทับ';else if(sAIID>=2&&nAFNC<30)status='เฝ้าระวัง';else if(sAIID<2&&sAFNC>=2)status='เด่นในไทย';return{theme,n_AFNC:nAFNC,n_AIID:nAIID,share_pct_AFNC:sAFNC,share_pct_AIID:sAIID,status};});
  }

  // ================================================================== 3. Internet Freedom & Country Comparison
  function freedom() {
    const x=ctx(), after=[], p=[], fo=x.fo, availableYears=[...new Set(fo.map(r=>r.y))].sort((a,b)=>a-b), yearOptions=availableYears.length?availableYears:[...new Set(D.fotn.map(r=>r.y))].sort((a,b)=>a-b);
    const year=yearOptions.includes(Number(APP.state.q3Year))?Number(APP.state.q3Year):yearOptions.at(-1), th=fo.find(r=>r.iso3==='THA'&&r.y===year), thRows=fo.filter(r=>r.iso3==='THA').sort((a,b)=>a.y-b.y);
    const asean=Object.keys(D.meta.asean), foCountries=[...new Map(D.fotn.map(r=>[r.iso3,r.country])).entries()].sort((a,b)=>a[1].localeCompare(b[1])), yearRows=fo.filter(r=>r.y===year), aRows=yearRows.filter(r=>asean.includes(r.iso3)), ordered=aRows.slice().sort((a,b)=>b.total-a.total), rank=ordered.findIndex(r=>r.iso3==='THA')+1;
    const allAIYears=D.aiid.rows.map(r=>+r[1].slice(0,4)), minAI=Math.max(2010,Math.min(...allAIYears)), maxAI=Math.max(...allAIYears), aiFrom=Number(APP.state.q3AiFrom??2015), aiTo=Number(APP.state.q3AiTo??maxAI);
    const aiRows=x.ac.filter(r=>+r[1].slice(0,4)>=aiFrom&&+r[1].slice(0,4)<=aiTo), defaultCountries=APP.state.q3Countries||asean, chosen=defaultCountries.filter(i=>fo.some(r=>r.iso3===i));
    const peerRows=th?yearRows.slice().sort((a,b)=>Math.abs(a.total-th.total)-Math.abs(b.total-th.total)).slice(0,11).sort((a,b)=>a.total-b.total):[];
    const previousByCountry=new Map(D.fotn.filter(r=>r.y===year-5).map(r=>[r.iso3,r.total]));
    const changeRows=fo.filter(r=>r.y===year&&previousByCountry.has(r.iso3)).map(r=>({country:r.country,iso3:r.iso3,change:r.total-previousByCountry.get(r.iso3)})).sort((a,b)=>a.change-b.change);
    const counts=[aiRows.length,aiRows.filter(r=>r[5]).length,aiRows.filter(r=>r[6]).length];
    const overlap=x.f.sources.includes('aiid')&&x.f.sources.includes('afnc')&&x.f.region!=='foreign'?filteredThemeOverlap(x.f,aiFrom,aiTo):[];
    const kp=`${kpi({key:'f_score',label:`คะแนนไทย (${year})`,value:th?`${th.total}<small>/100</small>`:'–',sub:th?['','เสรี','เสรีบางส่วน','ไม่เสรี'][th.st]:'ไม่มีข้อมูล',color:C.freedom})}${kpi({key:'f_rank',label:'อันดับอาเซียน',value:`${rank||'–'}<small>/${aRows.length}</small>`,sub:'ไทยเทียบกับประเทศอาเซียนที่มีข้อมูล',color:C.freedom})}${kpi({key:'aiid',label:'เหตุการณ์ AI ในฐานข้อมูลโลก',value:L.fmtInt(counts[0]),sub:`deepfake ${L.fmtInt(counts[1])} · scam/fraud ${L.fmtInt(counts[2])}`,color:C.ai})}${kpi({key:'fake',label:'ธีมที่ซ้อนทับ',value:`${overlap.filter(r=>r.status==='ซ้อนทับ').length}`,sub:`เฝ้าระวัง ${overlap.filter(r=>r.status==='เฝ้าระวัง').length} ธีม`,color:C.scam})}`;
    p.push(`<h2 class="sec">Q3 เสรีภาพอินเทอร์เน็ตและภัย AI</h2><p class="sec-sub">เปรียบเทียบคะแนน Freedom on the Net กับรูปแบบเหตุการณ์ AI และประเด็นที่พบในไทย</p><div class="filterbar local-filter"><label>ปีข้อมูล Freedom <select data-state="q3Year" data-state-type="number">${yearOptions.map(y=>`<option value="${y}"${y===year?' selected':''}>${y}</option>`).join('')}</select></label><label>ช่วงปี AI เริ่ม <select data-state="q3AiFrom" data-state-type="number">${Array.from({length:maxAI-minAI+1},(_,i)=>minAI+i).map(y=>`<option value="${y}"${y===aiFrom?' selected':''}>${y}</option>`).join('')}</select></label><label>ถึง <select data-state="q3AiTo" data-state-type="number">${Array.from({length:maxAI-minAI+1},(_,i)=>minAI+i).map(y=>`<option value="${y}"${y===aiTo?' selected':''}>${y}</option>`).join('')}</select></label><label>ประเทศที่เปรียบเทียบ <select multiple size="5" data-state="q3Countries">${foCountries.map(([iso,name])=>`<option value="${iso}"${defaultCountries.includes(iso)?' selected':''}>${esc(name)}</option>`).join('')}</select></label><button class="btn-ghost" data-local-reset="q3">ล้างตัวกรอง Q3</button></div><div class="kpis">${kp}</div>`);
    p.push('<h2 class="sec">ไทยอยู่ตรงไหน</h2><div class="grid">');
    p.push(APP.card({id:'q3_lines',title:'คะแนนเสรีภาพทางอินเทอร์เน็ตรายปี: ไทยและประเทศที่เลือก',unit:'คะแนน 0–100',period:`${thRows[0]?.y||'–'}–${year}`,src:'Freedom on the Net'}));
    after.push(()=>{const years=[...new Set(fo.map(r=>r.y))].sort((a,b)=>a-b),ids=[...new Set(['THA',...chosen])],countryColors=['#0072B2','#E69F00','#009E73','#CC79A7','#D55E00','#56B4E9','#737373','#332288','#88CCEE','#AA4499'];mount('q3_lines',{legend:{type:'scroll',top:0},xAxis:{type:'category',data:years.map(String)},yAxis:{type:'value',min:0,max:100,name:'คะแนน'},series:ids.map((iso,j)=>({name:fo.find(r=>r.iso3===iso)?.country||iso,type:'line',connectNulls:false,symbolSize:iso==='THA'?7:4,lineStyle:{width:iso==='THA'?3:1.5},color:countryColors[j%countryColors.length],data:years.map(y=>fo.find(r=>r.iso3===iso&&r.y===y)?.total??null)}))});});
    p.push(APP.card({id:'q3_comp',title:'คะแนนไทยและคะแนนย่อย 3 ส่วน',unit:'คะแนน (เต็ม 25 / 35 / 40)',period:`ปีข้อมูล ${year}`,src:'Freedom on the Net',desc:th?`ไทย ${th.total}/100 · การเข้าถึง ${th.acc}/25 · เนื้อหา ${th.con}/35 · สิทธิผู้ใช้ ${th.rig}/40`:''}));
    after.push(()=>th&&mount('q3_comp',{legend:{top:0},xAxis:{type:'category',data:['คะแนนไทย']},yAxis:{type:'value',max:100},series:[['การเข้าถึง',th.acc,C.blue],['การจำกัดเนื้อหา',th.con,C.orange],['สิทธิผู้ใช้',th.rig,C.purple]].map(([name,value,color])=>({name,type:'bar',stack:'s',color,data:[value]}))}));
    p.push(APP.card({id:'q3_peers',title:'ประเทศที่มีคะแนนเสรีภาพใกล้เคียงไทย',unit:'คะแนนรวม 0–100',period:`ปีข้อมูล ${year}`,src:'Freedom on the Net'}));
    after.push(()=>peerRows.length&&mount('q3_peers',{grid:{left:15,right:35,top:12,bottom:10,containLabel:true},xAxis:{type:'value',min:0,max:100},yAxis:{type:'category',inverse:true,data:peerRows.map(r=>r.country)},series:[{type:'bar',data:peerRows.map(r=>({value:r.total,itemStyle:{color:r.iso3==='THA'?C.scam:'#B9B6AE'}})),label:{show:true,position:'right'}}]}));
    p.push(APP.card({id:'q3_change',title:'การเปลี่ยนแปลงคะแนนในช่วง 5 ปี',unit:'คะแนน',period:`${year-5}–${year}`,src:'Freedom on the Net',msg:changeRows.length?'':'ไม่มีข้อมูลย้อนหลัง 5 ปีก่อนปีที่เลือก'}));
    after.push(()=>{const d=changeRows.length>16?[...changeRows.slice(0,8),...changeRows.slice(-8)]:changeRows;d.length&&mount('q3_change',{grid:{left:15,right:35,top:12,bottom:10,containLabel:true},xAxis:{type:'value',name:'เปลี่ยน (คะแนน)'},yAxis:{type:'category',inverse:true,data:d.map(r=>r.country)},series:[{type:'bar',data:d.map(r=>({value:r.change,itemStyle:{color:r.iso3==='THA'?C.scam:r.change>0?C.real:C.orange}})),label:{show:true,position:'right',formatter:q=>`${q.value>0?'+':''}${q.value}`}}]});});
    p.push('</div>');
    const mapRows=fo.filter(r=>r.y===year).map(r=>({name:r.country,value:r.st,score:r.total,iso3:r.iso3}));
    p.push(APP.card({id:'q3_map',title:`สถานะเสรีภาพอินเทอร์เน็ต ปี ${year}`,unit:'สถานะ · คะแนน 0–100 แสดงเมื่อชี้ประเทศ',period:`ปีข้อมูล ${year}`,src:'Freedom on the Net',span:true,desc:'เทาอ่อน = ไม่มีข้อมูล ไม่ใช่ 0 คะแนน'}));
    after.push(()=>{if(!mapRows.length||!window.echarts.getMap('world'))return;const labels={1:'เสรี',2:'เสรีบางส่วน',3:'ไม่เสรี'},aliases={'Russian Federation':'Russia','United States':'United States of America','Korea, Republic of':'South Korea',"Korea, Democratic People's Republic of":'North Korea','Iran, Islamic Republic of':'Iran','Venezuela, Bolivarian Republic of':'Venezuela','Tanzania, United Republic of':'Tanzania','Moldova, Republic of':'Moldova','Bolivia, Plurinational State of':'Bolivia','Czechia':'Czech Republic'},geo=window.echarts.getMap('world'),features=geo.geoJson?.features||geo.geoJSON?.features||[],geoNames=new Map(features.map(f=>{const p=f.properties||{};return[p['iso-a3']||p.ISO_A3||p.iso3||p.ISO3||p.adm0_a3,p.name||p.NAME];}).filter(([iso,name])=>iso&&name));mount('q3_map',{tooltip:{trigger:'item',formatter:q=>{const r=q.data;if(!r||q.value===undefined||q.value===null)return `${q.name}<br>ไม่มีข้อมูล`;const score=Number.isFinite(Number(r.score))?`${r.score} คะแนน`:'ไม่มีคะแนน';return `${q.name}<br>${labels[r.value]||'ไม่มีข้อมูล'} · ${score}`;}},visualMap:{type:'piecewise',left:'center',bottom:4,orient:'horizontal',pieces:[{value:1,label:'เสรี',color:'#2B8C7E'},{value:2,label:'เสรีบางส่วน',color:'#E0A212'},{value:3,label:'ไม่เสรี',color:'#861F41'}]},series:[{type:'map',map:'world',roam:true,emphasis:{label:{show:false}},itemStyle:{areaColor:'#E8E6E1',borderColor:'#fff',borderWidth:.6},data:mapRows.map(r=>({...r,name:geoNames.get(r.iso3)||aliases[r.name]||r.name}))}]});});
    p.push('<h2 class="sec">ภัยจาก AI ระดับสากลกับที่ไทยเจอ</h2><div class="grid">');
    const aiYears=[...new Set(aiRows.map(r=>+r[1].slice(0,4)))].sort((a,b)=>a-b), aiByYear=aiYears.map(y=>{const r=aiRows.filter(q=>+q[1].slice(0,4)===y);return{y,n:r.length,deep:r.filter(q=>q[5]).length,scam:r.filter(q=>q[6]).length};});
    p.push(APP.card({id:'q3_aiid',title:'เหตุการณ์ AI รายปี',unit:'เหตุการณ์ (วันเกิดเหตุ)',period:aiYears.length?`${aiYears[0]}–${aiYears.at(-1)}`:'–',src:'AI Incident Database',desc:'deepfake และ scam/fraud ใช้การค้นคำในชื่อ/คำอธิบาย/ระบบที่เกี่ยวข้อง'}));
    after.push(()=>aiByYear.length&&mount('q3_aiid',{legend:{top:0},xAxis:{type:'category',data:aiByYear.map(r=>String(r.y))},yAxis:{type:'value',name:'เหตุการณ์'},dataZoom:[{type:'inside'}],series:[{name:'ทั้งหมด',type:'line',data:aiByYear.map(r=>r.n),color:C.ai},{name:'deepfake',type:'line',data:aiByYear.map(r=>r.deep),color:C.fake},{name:'scam/fraud',type:'line',data:aiByYear.map(r=>r.scam),color:C.orange}]}));
    const ovs=overlap.slice().sort((a,b)=>a.share_pct_AIID-b.share_pct_AIID);
    p.push(APP.card({id:'q3_theme',title:'ธีมความเสียหายจาก AI เทียบกับข่าวปลอมไทย',unit:'% ของเหตุการณ์/เรื่องในแต่ละชุด',period:`AIID ${aiFrom}–${aiTo} · AFNC ${x.f.from}–${x.f.to}`,src:'AIID + AFNC',desc:'ซ้อนทับ = พบทั้งสองฝั่ง · เฝ้าระวัง = พบมากใน AIID แต่พบต่ำในข้อมูล AFNC',msg:overlap.length?'':'ต้องเลือก AIID และ AFNC และมีข้อมูลในช่วงที่เลือก'}));
    after.push(()=>mount('q3_theme',{legend:{top:0},grid:{left:15,right:20,top:25,bottom:10,containLabel:true},xAxis:{type:'value',name:'%'},yAxis:{type:'category',inverse:true,data:ovs.map(r=>r.theme)},series:[{name:'AIID',type:'bar',data:ovs.map(r=>r.share_pct_AIID),color:C.ai},{name:'AFNC',type:'bar',data:ovs.map(r=>r.share_pct_AFNC),color:C.fake}]}));
    p.push('</div>');
    p.push(`<section class="card"><h3>ตารางธีมซ้อนทับ</h3>${table([{h:'ธีม',f:r=>r.theme},{h:'สถานะ',f:r=>r.status},{h:'AIID %',n:1,f:r=>L.fmtNum(r.share_pct_AIID,1)},{h:'AFNC %',n:1,f:r=>L.fmtNum(r.share_pct_AFNC,1)},{h:'เรื่องใน AFNC',n:1,f:r=>L.fmtInt(r.n_AFNC)}],ovs)}<div class="cap">หนึ่งเรื่องอาจมีได้หลายธีม · เฝ้าระวังไม่ได้แปลว่าไม่เกิดในไทย</div></section>`);
    p.push('<h2 class="sec">เสรีภาพกับเหตุการณ์ AI รายประเทศ (สำรวจ)</h2><div class="grid">');
    const country=x.f.sources.includes('aiid')?D.analysis.country.rows.filter(r=>r.mentions>=5&&fo.some(q=>q.iso3===r.iso3)):[];
    const countryGroups=[['ไทย',country.filter(r=>r.iso3==='THA'),C.scam],['เสรี',country.filter(r=>r.iso3!=='THA'&&r.status_code===1),C.real],['เสรีบางส่วน',country.filter(r=>r.iso3!=='THA'&&r.status_code===2),C.orange],['ไม่เสรี',country.filter(r=>r.iso3!=='THA'&&r.status_code!==1&&r.status_code!==2),C.blue]];
    p.push(APP.card({id:'q3_country',title:'คะแนนเสรีภาพ vs เหตุการณ์ AI ที่กล่าวถึงประเทศ',unit:'คะแนน / จำนวนครั้งที่กล่าวถึง',period:`AIID ฉบับ ${D.meta.aiid_snapshot} · Freedom on the Net ปี ${year}`,src:'AIID + Freedom on the Net',desc:'เป็นการถูกกล่าวถึงในข้อความ ไม่ใช่ตำแหน่งที่เกิดเหตุ และ AIID มีช่องประเทศไม่ครบทุกเหตุการณ์'}));
    after.push(()=>country.length&&mount('q3_country',{legend:{top:0},tooltip:{trigger:'item',formatter:q=>`${q.data[2]}<br>คะแนน ${q.data[0]} · กล่าวถึง ${q.data[1]} เหตุการณ์`},xAxis:{type:'value',min:0,max:100,name:'คะแนนเสรีภาพ'},yAxis:{type:'log',name:'จำนวนเหตุการณ์ที่กล่าวถึง'},series:countryGroups.map(([name,rows,color])=>({name,type:'scatter',symbolSize:name==='ไทย'?12:9,data:rows.map(r=>({value:[r.total_score,r.mentions,r.country],itemStyle:{color}}))}))}));
    const notFree=x.f.sources.includes('aiid')&&fo.length?D.analysis.country.not_free.slice(0,8):[];
    p.push(`<section class="card"><h3>ประเทศกลุ่มไม่เสรีที่ถูกกล่าวถึงบ่อย</h3>${table([{h:'ประเทศ',f:r=>r.country.replace(/\s*\(.*\)/,'')},{h:'ถูกกล่าวถึง',n:1,f:r=>L.fmtInt(r.mentions)},{h:'คะแนน',n:1,f:r=>L.fmtInt(r.total_score)}],notFree)}</section></div>`);
    p.push('<h2 class="sec">ข้อค้นพบ</h2>');
    const fs=D.analysis.findings.q3||[];p.push(`<div class="findings">${fs.map((r,i)=>`<div class="find"><b>${i+1}.</b> ${esc(r.headline)}<small class="desc">${esc(r.detail)}<br><i>ข้อควรระวัง: ${esc(r.caution)}</i></small></div>`).join('')}</div>`);
    return {html:p.join(''),after};
  }

  APP.addTab('overview', 'ภาพรวม', overview);
  APP.q1 = disinfo;
  APP.q3 = freedom;
})();
