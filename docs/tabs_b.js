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
    const x=APP.ctx(), f=x.f, wk=D.weekly.filter(w=>L.timeOK(w.ws,f)), use=wk.filter(w=>w.use), allUse=L.usable(D.weekly), after=[], p=[];
    const latest=allUse[allUse.length-1], last4=D.weekly.slice(-4), v4=L.sum(last4.map(w=>w.vd)), false4=v4?100*L.sum(last4.map(w=>w.fake+w.dist))/v4:null;
    const loss= L.sum(use.map(w=>w.loss)), cases=L.sum(use.map(w=>w.cases));
    const kp=`${kpi({key:'cases',label:`คดีล่าสุด ${latest?.ws||'–'}`,value:latest?L.fmtInt(latest.cases):'–',sub:'เทียบกับค่าเฉลี่ย 4 สัปดาห์ก่อน'})}${kpi({key:'loss',label:'ความเสียหายสัปดาห์ล่าสุด',value:latest?L.fmtMB(latest.loss):'–',sub:latest?.rnd?'ตัวเลขปัดเป็นล้านบาท':'ACSC'})}${kpi({key:'lpc',label:'ความเสียหายต่อคดี (ช่วงที่เลือก)',value:cases?`${L.fmtInt(loss/cases)} บาท`:'–',sub:`${L.fmtInt(cases)} คดี · ${use.length} สัปดาห์ที่ใช้ได้`})}${kpi({key:'fake',label:'สัดส่วนข่าวเท็จ 4 สัปดาห์ล่าสุด',value:false4===null?'–':`${L.fmtNum(false4,1)}%`,sub:'ปลอม + บิดเบือน จากคำตัดสิน AFNC'})}`;
    p.push(`<h2 class="sec">Q2 ภัยหลอกลวงและความผิดปกติ</h2><p class="sec-sub">ตัวเลข ACSC รวบรวมจากข่าวแถลงรายสัปดาห์ ไม่ใช่ข้อมูลเปิดของตำรวจ · นับเฉพาะคดีที่มีผู้แจ้งความ</p><div class="kpis">${kp}</div>`);
    const plot=wk.filter(w=>w.ws>=D.meta.acsc_first_week), xdates=plot.map(w=>w.ws);
    p.push('<h2 class="sec">แนวโน้ม</h2>');
    p.push(APP.card({id:'q2_main',title:'คดีออนไลน์ · ความเสียหาย · สัดส่วนข่าวเท็จรายสัปดาห์',unit:'คดี / ล้านบาท / %',period:APP.periodText(plot.filter(w=>w.rep).map(w=>w.ws)),src:'ACSC + AFNC',span:true,desc:'ช่องว่างสีเทา = ไม่มีการแถลง (ไม่ใช่ 0) · ตัวเลขน่าสงสัยถูกตัดออก · จุดโปร่ง = ยอดความเสียหายที่ปัดเป็นล้านบาท'}));
    after.push(()=>{if(!plot.length)return;const colors={scam:C.scam,fake:C.fake};mount('q2_main',{legend:{top:0,data:['คดี','ความเสียหาย (ล้านบาท)','สัดส่วนข่าวเท็จ (%)']},tooltip:{trigger:'axis'},grid:[{left:58,right:20,top:38,height:'25%'},{left:58,right:20,top:'37%',height:'25%'},{left:58,right:20,top:'69%',height:'23%'}],xAxis:[0,1,2].map(i=>({type:'category',gridIndex:i,data:xdates,axisLabel:{show:i===2}})),yAxis:[{type:'value',gridIndex:0,name:'คดี'},{type:'value',gridIndex:1,name:'ล้านบาท'},{type:'value',gridIndex:2,name:'%',min:0,max:100}],series:[{name:'คดี',type:'line',xAxisIndex:0,yAxisIndex:0,data:plot.map(w=>w.use?w.cases:null),color:colors.scam,connectNulls:false,symbolSize:5},{name:'ความเสียหาย (ล้านบาท)',type:'line',xAxisIndex:1,yAxisIndex:1,data:plot.map(w=>w.use?w.loss/1e6:null),color:colors.scam,connectNulls:false,symbolSize:5},{name:'สัดส่วนข่าวเท็จ (%)',type:'line',xAxisIndex:2,yAxisIndex:2,data:plot.map(w=>w.vd?(w.fake+w.dist)/w.vd*100:null),color:colors.fake,connectNulls:false,symbolSize:5}]});});
    p.push('<h2 class="sec">ความเสียหายเปลี่ยนเพราะอะไร</h2><div class="grid">');
    const dc=D.analysis.decomp, cpCases=D.analysis.cp_cases, cpLpc=D.analysis.cp_lpc;
    p.push(APP.card({id:'q2_wf',title:'แยกส่วนการลดลงของความเสียหาย (ล้านบาท/สัปดาห์)',unit:'ล้านบาท/สัปดาห์',period:`${dc.peak_start}–${dc.peak_end} เทียบ ${dc.trough_start}–${dc.trough_end}`,src:'ACSC',desc:'แยกผลจากจำนวนคดีและความเสียหายต่อคดี เป็นการแยกเชิงบัญชี ไม่ใช่สาเหตุ'}));
    after.push(()=>mount('q2_wf',{tooltip:{trigger:'axis'},xAxis:{type:'category',data:['ช่วงสูงสุด','ผลจากจำนวนคดี','ผลจากบาท/คดี','ช่วงต่ำสุด']},yAxis:{type:'value',name:'ล้านบาท/สัปดาห์'},series:[{type:'bar',data:[{value:dc.loss_peak/1e6,itemStyle:{color:C.grey}},{value:dc.cases_effect/1e6,itemStyle:{color:C.fake}},{value:dc.severity_effect/1e6,itemStyle:{color:C.scam}},{value:dc.loss_trough/1e6,itemStyle:{color:C.grey}}],label:{show:true,position:'top',formatter:q=>L.fmtNum(q.value,0)}}]}));
    p.push(APP.card({id:'q2_cp',title:'จุดเปลี่ยนของจำนวนคดีและความเสียหายต่อคดี',unit:'คดี / บาทต่อคดี',period:APP.periodText(allUse.map(w=>w.ws)),src:'ACSC',span:true}));
    after.push(()=>{const d=allUse.map(w=>w.ws);mount('q2_cp',{legend:{top:0},tooltip:{trigger:'axis'},grid:[{left:58,right:20,top:35,height:'28%'},{left:58,right:20,top:'58%',height:'28%'}],xAxis:[0,1].map(i=>({type:'category',gridIndex:i,data:d,axisLabel:{show:i===1}})),yAxis:[{type:'value',gridIndex:0,name:'คดี'},{type:'value',gridIndex:1,name:'บาท/คดี'}],series:[{name:'คดี',type:'line',xAxisIndex:0,yAxisIndex:0,data:allUse.map(w=>w.cases),color:C.scam,markLine:{symbol:'none',data:[{xAxis:cpCases.date,lineStyle:{color:C.orange,type:'dashed'}}]}},{name:'บาท/คดี',type:'line',xAxisIndex:1,yAxisIndex:1,data:allUse.map(w=>w.loss/w.cases),color:C.fake,markLine:{symbol:'none',data:[{xAxis:cpLpc.date,lineStyle:{color:C.orange,type:'dashed'}}]}}]});});
    const pts=use.filter(w=>w.cases&&w.loss).map(w=>[w.cases,w.loss/1e6,w.ws]);
    p.push(APP.card({id:'q2_scatter',title:'จำนวนคดี vs ความเสียหายต่อสัปดาห์',unit:'คดี / ล้านบาท',period:APP.periodText(use.map(w=>w.ws)),src:'ACSC',msg:pts.length<5?'ช่วงที่เลือกมีสัปดาห์ที่ใช้ได้น้อยกว่า 5 สัปดาห์':''}));
    after.push(()=>pts.length>=5&&mount('q2_scatter',{tooltip:{trigger:'item',formatter:q=>`${q.data[2]}<br>${L.fmtInt(q.data[0])} คดี · ${L.fmtNum(q.data[1],0)} ล้านบาท`},xAxis:{type:'value',name:'คดี'},yAxis:{type:'value',name:'ล้านบาท'},series:[{type:'scatter',data:pts.map(q=>({value:q,symbolSize:9,itemStyle:{color:C.scam,opacity:.75}}))}]}));
    const blocks=D.analysis.blocks;
    p.push(APP.card({id:'q2_blocks',title:'การเปลี่ยนแปลงต่อบล็อก 4 สัปดาห์',unit:'% เทียบช่วงก่อนหน้า',period:'ทั้งช่วงข้อมูล',src:'ACSC',desc:'แถบสีเหลืองคือช่วงที่จำนวนคดีลด แต่ความเสียหายต่อคดีเพิ่ม'}));
    after.push(()=>mount('q2_blocks',{legend:{top:0},tooltip:{trigger:'axis'},xAxis:{type:'category',data:blocks.map(r=>r.from)},yAxis:{type:'value',name:'%'},series:[{name:'คดี',type:'bar',data:blocks.map(r=>r.cases_chg_pct),color:C.scam,markArea:{silent:true,itemStyle:{color:'rgba(201,132,29,.18)'},data:blocks.flatMap(r=>r.cases_down_lpc_up?[[{xAxis:r.from},{xAxis:r.from}]]:[])}},{name:'บาท/คดี',type:'bar',data:blocks.map(r=>r.lpc_chg_pct),color:C.fake}]}));
    p.push('</div><h2 class="sec">ความผิดปกติ</h2>');
    const anomalies=D.analysis.anomalies.filter(r=>r.week_start>=D.meta.acsc_first_week&&r.week_start<=D.meta.acsc_last_week);
    const falseShareSeries='สัดส่วนข่าวเท็จ (%)';
    const falseAnomalies=anomalies.filter(r=>r.series===falseShareSeries);
    const falseWeeks=wk.filter(w=>w.ws>='2020-01-01'&&w.vd>0);
    p.push(APP.card({id:'q2_an_share',title:'สัดส่วนข่าวเท็จรายสัปดาห์ — จุดแดง = ผิดปกติ',unit:'%',period:APP.periodText(falseWeeks.map(w=>w.ws)),src:'AFNC',desc:'สัดส่วนข่าวปลอม + ข่าวบิดเบือนในคำตัดสิน AFNC · จุดผิดปกติเทียบกับมัธยฐานของ 13 สัปดาห์รอบข้าง'}));
    after.push(()=>{const hit=new Map(falseAnomalies.map(r=>[r.week_start,r]));mount('q2_an_share',{tooltip:{trigger:'axis',formatter:q=>{const w=falseWeeks[q[0].dataIndex],a=hit.get(w.ws);return `${w.ws}<br>${L.fmtNum((w.fake+w.dist)/w.vd*100,1)}%${a?`<br>ค่าคาด ${L.fmtNum(a.expected,1)}% · z ${L.fmtNum(a.z,1)}`:''}`}},xAxis:{type:'category',data:falseWeeks.map(w=>w.ws)},yAxis:{type:'value',name:'%',min:0,max:100},dataZoom:[{type:'inside'}],series:[{name:'สัดส่วนข่าวเท็จ',type:'line',data:falseWeeks.map(w=>({value:(w.fake+w.dist)/w.vd*100,symbol:'circle',symbolSize:6})),color:C.fake,connectNulls:false},{name:'ผิดปกติ',type:'scatter',data:falseAnomalies.filter(a=>falseWeeks.some(w=>w.ws===a.week_start)).map(a=>({value:[a.week_start,a.value],symbolSize:12,itemStyle:{color:C.scam,borderColor:'#fff',borderWidth:2}})),color:C.scam}]});});
    p.push(`<section class="card"><h3>สัปดาห์ผิดปกติ (robust z &gt; 3.5)</h3>${table([{h:'ชุดข้อมูล',f:r=>r.series},{h:'สัปดาห์',f:r=>r.week_start},{h:'ค่า',n:1,f:r=>L.fmtNum(r.value,1)},{h:'ค่าคาดจากสัปดาห์รอบข้าง',n:1,f:r=>L.fmtNum(r.expected,1)},{h:'robust z',n:1,f:r=>L.fmtNum(r.z,1)}],anomalies)}<div class="cap">เทียบกับมัธยฐานของ 13 สัปดาห์รอบข้าง · สัปดาห์ 16 ส.ค. 2026 ที่ถูกตัดออกไม่อยู่ในตารางนี้</div></section>`);
    p.push('<h2 class="sec">ประเภทภัยและความสัมพันธ์กับข่าวปลอม</h2><div class="grid">');
    const types=D.analysis.loss_types;
    p.push(APP.card({id:'q2_types',title:'ประเภทคดีที่เป็นอันดับ 1 ของสัปดาห์',unit:'จำนวนสัปดาห์',period:APP.periodText(use.map(w=>w.ws)),src:'ACSC'}));
    after.push(()=>mount('q2_types',{grid:{left:15,right:30,top:12,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',inverse:true,data:types.map(r=>r.scam_type)},series:[{type:'bar',name:'อันดับ 1 ตามคดี',data:types.map(r=>r.weeks_top_by_cases),color:C.fake},{type:'bar',name:'อันดับ 1 ตามความเสียหาย',data:types.map(r=>r.weeks_top_by_loss),color:C.scam}]}));
    const lag=D.analysis.lag;
    p.push(APP.card({id:'q2_lag',title:'สัดส่วนข่าวเท็จนำหน้าหรือตามหลังคดีหลอกลวงหรือไม่ (lag −4…+4)',unit:'สหสัมพันธ์ r ของการเปลี่ยนแปลงรายสัปดาห์',period:'ทั้งช่วงข้อมูล',src:'AFNC + ACSC',desc:'lag บวก = ข่าวเท็จนำหน้า · แถบเทาเป็นช่วงเกณฑ์ ±1.96/√n · ความสัมพันธ์ไม่ใช่เหตุและผล'}));
    after.push(()=>mount('q2_lag',{xAxis:{type:'category',data:lag.map(r=>r.lag),name:'lag (สัปดาห์)'},yAxis:{type:'value',min:-.6,max:.6,name:'r'},series:[{type:'bar',data:lag.map(r=>({value:r.r,itemStyle:{color:r.significant?C.fake:'#CBD5DD'}})),markArea:{silent:true,itemStyle:{color:'rgba(100,120,135,.14)'},data:[[{yAxis:-lag[0].ci95},{yAxis:lag[0].ci95}]]}}]}));
    p.push('</div><h2 class="sec">ข้อค้นพบ</h2>');
    const fs=D.analysis.findings.q2||[];p.push(`<div class="findings">${fs.map((r,i)=>`<div class="find"><b>${i+1}.</b> ${esc(r.headline)}<small class="desc">${esc(r.detail)}<br><i>ข้อควรระวัง: ${esc(r.caution)}</i></small></div>`).join('')}</div>`);
    return {html:p.join(''),after};
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
    const id=APP.state.detail||'afnc', after=[], p=[], options=[['afnc','ข่าวปลอมไทย'],['scam','คดีหลอกลวง'],['ai','AI & Deepfake'],['freedom','เสรีภาพอินเทอร์เน็ต'],['eu','ข้อมูลเท็จระดับโลก']];
    p.push(`<h2 class="sec">รายละเอียดแต่ละชุดข้อมูล</h2><div class="row-tools"><div class="seg">${options.map(([k,n])=>`<button data-detail="${k}" class="${id===k?'on':''}">${n}</button>`).join('')}</div></div>`);
    if(id==='afnc'){
      const months=new Map(), annual=new Map(), agencies=new Map(), tags=new Map();
      for(let i=0;i<A.d.length;i++){
        const y=L.yearOf(A.d[i]), m=A.d[i].slice(0,7), st=A.st[i], cat=A.c[i];
        if(A.itypes[A.it[i]]==='Verdict'){
          if(!annual.has(y))annual.set(y,[0,0,0,0]);annual.get(y)[st]++;
          if(y>=2020&&cat>=0){if(!months.has(m))months.set(m,new Map());const cm=months.get(m);const key=A.cats[cat];if(!cm.has(key))cm.set(key,[0,0]);if(st<2)cm.get(key)[st]++;}
          if(A.ag[i]>=0){const a=A.agencies[A.ag[i]];agencies.set(a,(agencies.get(a)||0)+1);}
          for(const tag of String(A.tg[i]||'').split(/[;,|]/).map(t=>t.trim()).filter(Boolean))tags.set(tag,(tags.get(tag)||0)+1);
        }
      }
      const ys=[...annual.keys()].sort((a,b)=>a-b), ms=[...months.keys()].sort(), cats=[...new Set([...months.values()].flatMap(m=>[...m.keys()]))];
      p.push('<h3>ข่าวปลอมในไทย — ศูนย์ต่อต้านข่าวปลอม (AFNC)</h3><div class="grid">');
      p.push(APP.card({id:'det_afnc_cat',title:'จำนวนเรื่องรายเดือน แยกตามหมวดข่าว',unit:'เรื่อง/เดือน',period:ms.length?`${ms[0]}–${ms.at(-1)}`:'–',src:'AFNC',span:true}));
      after.push(()=>ms.length&&mount('det_afnc_cat',{legend:{type:'scroll',top:0},xAxis:{type:'category',data:ms},yAxis:{type:'value',name:'เรื่อง'},dataZoom:[{type:'inside'}],series:cats.map((c,j)=>({name:c,type:'bar',stack:'s',color:[C.scam,C.fake,C.orange,C.warn,C.blue,C.ink,C.other][j%7],data:ms.map(m=>L.sum(months.get(m).get(c)||[0,0]))}))}));
      p.push(APP.card({id:'det_afnc_mix',title:'สัดส่วนผลคำตัดสินรายปี',unit:'% ของคำตัดสิน',period:ys.length?`${ys[0]}–${ys.at(-1)}`:'–',src:'AFNC'}));
      after.push(()=>ys.length&&mount('det_afnc_mix',{legend:{top:0},xAxis:{type:'category',data:ys.map(String)},yAxis:{type:'value',min:0,max:100,name:'%'},series:[['ข่าวปลอม',0,C.fake],['ข่าวบิดเบือน',1,C.fakeL],['ข่าวจริง',2,C.global]].map(([n,k,c])=>({name:n,type:'bar',stack:'s',color:c,data:ys.map(y=>{const a=annual.get(y);return L.sum(a.slice(0,3))?a[k]/L.sum(a.slice(0,3))*100:0;})}))}));
      const top=(m)=>[...m.entries()].sort((a,b)=>b[1]-a[1]).slice(0,12).reverse();const ag=top(agencies),tg=top(tags);
      p.push(APP.card({id:'det_afnc_ag',title:'หน่วยงานที่ตรวจข้อเท็จจริงบ่อยที่สุด',unit:'จำนวนคำตัดสิน',period:'2019–2026',src:'AFNC'}));
      after.push(()=>mount('det_afnc_ag',{grid:{left:12,right:30,top:10,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',data:ag.map(r=>r[0])},series:[{type:'bar',data:ag.map(r=>r[1]),color:C.fake}]}));
      p.push(APP.card({id:'det_afnc_tag',title:'หัวข้อที่พบบ่อยที่สุด',unit:'จำนวนคำตัดสิน',period:'2019–2026',src:'AFNC'}));
      after.push(()=>mount('det_afnc_tag',{grid:{left:12,right:30,top:10,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',data:tg.map(r=>r[0])},series:[{type:'bar',data:tg.map(r=>r[1]),color:C.fake}]}));
      p.push('</div><div class="note">จำนวนคำตัดสินเป็นเรื่องที่ศูนย์ฯ เลือกตรวจ ไม่ใช่จำนวนข่าวปลอมทั้งหมด · หมวดข่าวเพิ่ม “อาชญากรรมออนไลน์” ในปี 2026</div>');
    } else if(id==='scam'){
      const byMonth=new Map();for(const w of D.weekly){const m=w.ws.slice(0,7);if(!byMonth.has(m))byMonth.set(m,{cases:0,loss:0,weeks:0});if(w.use){const r=byMonth.get(m);r.cases+=w.cases;r.loss+=w.loss;r.weeks++;}}
      const ms=[...byMonth.keys()].sort(), types=D.analysis.loss_types, rows=ms.map(m=>({month:m,...byMonth.get(m)}));
      p.push('<h3>คดีหลอกลวงออนไลน์ — ศูนย์ต่อต้านการฉ้อโกงออนไลน์ (ACSC)</h3><div class="note">ตัวเลขรวบรวมจากข่าวแถลงรายสัปดาห์ · สัปดาห์ที่ไม่มีข้อมูลไม่ถูกนับเป็นศูนย์ · สัปดาห์ 16–22 ส.ค. 2026 ถูกตัดออกเพราะตัวเลขผิดปกติ</div><div class="grid">');
      p.push(APP.card({id:'det_scam_month',title:'คดีและความเสียหายเฉลี่ยรายเดือน',unit:'คดี/สัปดาห์ · ล้านบาท/สัปดาห์',period:ms.length?`${ms[0]}–${ms.at(-1)}`:'–',src:'ACSC'}));
      after.push(()=>mount('det_scam_month',{legend:{top:0},tooltip:{trigger:'axis'},xAxis:{type:'category',data:ms},yAxis:[{type:'value',name:'คดี'},{type:'value',name:'ล้านบาท'}],series:[{name:'คดี/สัปดาห์ (เฉลี่ย)',type:'bar',data:rows.map(r=>r.weeks?r.cases/r.weeks:null),color:C.fake},{name:'ล้านบาท/สัปดาห์ (เฉลี่ย)',type:'line',yAxisIndex:1,data:rows.map(r=>r.weeks?r.loss/r.weeks/1e6:null),color:C.scam}]}));
      p.push(APP.card({id:'det_scam_types',title:'ประเภทการหลอกลวงที่เสียหายสูงสุดของสัปดาห์',unit:'จำนวนสัปดาห์',period:APP.periodText(D.weekly.filter(w=>w.use).map(w=>w.ws)),src:'ACSC'}));
      after.push(()=>mount('det_scam_types',{grid:{left:12,right:30,top:10,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',inverse:true,data:types.map(r=>r.scam_type)},series:[{name:'อันดับ 1 ตามความเสียหาย',type:'bar',data:types.map(r=>r.weeks_top_by_loss),color:C.scam},{name:'อันดับ 1 ตามคดี',type:'bar',data:types.map(r=>r.weeks_top_by_cases),color:C.fake}]}));
      p.push(`</div><section class="card"><h3>ตารางรายเดือน</h3>${table([{h:'เดือน',f:r=>r.month},{h:'สัปดาห์ที่ใช้ได้',n:1,f:r=>r.weeks},{h:'คดี/สัปดาห์ (เฉลี่ย)',n:1,f:r=>r.weeks?L.fmtInt(r.cases/r.weeks):'–'},{h:'ล้านบาท/สัปดาห์ (เฉลี่ย)',n:1,f:r=>r.weeks?L.fmtNum(r.loss/r.weeks/1e6,0):'–'},{h:'บาท/คดี',n:1,f:r=>r.cases?L.fmtInt(r.loss/r.cases):'–'}],rows.slice().reverse())}</section>`);
    } else if(id==='ai'){
      const rows=D.aiid.rows, byYear=new Map(), risks=new Map();for(const r of rows){const y=+r[1].slice(0,4);if(!byYear.has(y))byYear.set(y,[0,0,0]);const q=byYear.get(y);q[0]++;if(r[5])q[1]++;if(r[6])q[2]++;const risk=r[3]>=0?D.aiid.risk[r[3]]:'ยังไม่จัดหมวด';risks.set(risk,(risks.get(risk)||0)+1);}
      const ys=[...byYear.keys()].filter(y=>y>=2010).sort((a,b)=>a-b), rr=[...risks.entries()].sort((a,b)=>b[1]-a[1]);
      p.push('<h3>AI Incident Database — AI ก่อปัญหา/ถูกใช้หลอกลวง</h3><div class="grid">');
      p.push(APP.card({id:'det_ai_year',title:'เหตุการณ์ AI ตามปีเกิดเหตุ',unit:'เหตุการณ์',period:ys.length?`${ys[0]}–${ys.at(-1)}`:'–',src:'AI Incident Database',span:true}));
      after.push(()=>mount('det_ai_year',{legend:{top:0},xAxis:{type:'category',data:ys.map(String)},yAxis:{type:'value',name:'เหตุการณ์'},dataZoom:[{type:'inside'}],series:[{name:'ทั้งหมด',type:'line',data:ys.map(y=>byYear.get(y)[0]),color:C.ai},{name:'deepfake',type:'line',data:ys.map(y=>byYear.get(y)[1]),color:C.fake},{name:'scam/fraud',type:'line',data:ys.map(y=>byYear.get(y)[2]),color:C.scam}]}));
      p.push(APP.card({id:'det_ai_risk',title:'เหตุการณ์แยกตาม Risk Domain',unit:'เหตุการณ์',period:`AIID ฉบับ ${D.meta.aiid_snapshot}`,src:'AI Incident Database'}));
      after.push(()=>mount('det_ai_risk',{grid:{left:12,right:30,top:10,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',inverse:true,data:rr.slice(0,14).map(r=>r[0])},series:[{type:'bar',data:rr.slice(0,14).map(r=>r[1]),color:C.ai}]}));
      const g=D.analysis.aiid_growth;
      p.push(APP.card({id:'det_ai_growth',title:'เหตุการณ์ที่เพิ่มเข้าฐานข้อมูลรายสัปดาห์',unit:'เหตุการณ์ที่บันทึกเพิ่ม',period:g.length?`${g[0].snapshot}–${g.at(-1).snapshot}`:'–',src:'AI Incident Database'}));
      after.push(()=>mount('det_ai_growth',{tooltip:{trigger:'axis'},xAxis:{type:'category',data:g.map(r=>r.snapshot)},yAxis:{type:'value'},series:[{name:'เพิ่มเข้าฐาน',type:'bar',data:g.map(r=>r.new),color:C.ai},{name:'เหตุเก่าที่เพิ่งบันทึก',type:'line',data:g.map(r=>r.new_with_old_event_date),color:C.fake}]}));
      const thai=rows.filter(r=>r[7]).sort((a,b)=>b[1].localeCompare(a[1]));
      p.push(`</div><section class="card"><h3>เหตุการณ์ที่เกี่ยวข้องกับประเทศไทย (รายการตัวอย่าง)</h3>${table([{h:'ID',f:r=>r[0]},{h:'วันที่',f:r=>r[1]},{h:'หัวข้อ',f:r=>r[2]},{h:'Risk Domain',f:r=>r[3]>=0?D.aiid.risk[r[3]]:'ยังไม่จัดหมวด'},{h:'deepfake',f:r=>r[5]?'✓':''},{h:'scam/fraud',f:r=>r[6]?'✓':''},{h:'ข่าว',n:1,f:r=>r[8]}],thai,{max:100})}<div class="cap">ค้นจากคำว่า Thai/Thailand ในชื่อ/คำอธิบาย เป็นรายการตัวอย่าง ไม่ใช่สัดส่วนจริง</div></section>`);
    } else if(id==='freedom'){
      const y=Math.max(...D.fotn.map(r=>r.y)), fr=D.fotn.filter(r=>r.y===y), th=fr.find(r=>r.iso3==='THA'), thAll=D.fotn.filter(r=>r.iso3==='THA').sort((a,b)=>a.y-b.y);
      const asean=D.fotn.filter(r=>r.y===y&&Object.keys(D.meta.asean).includes(r.iso3)).sort((a,b)=>a.total-b.total);
      p.push('<h3>Freedom on the Net — เสรีภาพอินเทอร์เน็ต</h3>');
      if(th)p.push(`<div class="kpis">${kpi({key:'f_score',label:`คะแนนไทย ปีข้อมูล ${y}`,value:`${th.total}/100`,sub:['','เสรี','เสรีบางส่วน','ไม่เสรี'][th.st],color:C.freedom})}${kpi({key:'f_rank',label:'อันดับ',value:`${L.fotnRank(D.fotn,'THA',y).rank} จาก ${L.fotnRank(D.fotn,'THA',y).n}`,sub:'1 = เสรีที่สุด',color:C.freedom})}${kpi({key:'f_chg',label:'เปลี่ยนใน 5 ปี',value:`${thAll.at(-1).total-thAll.find(r=>r.y===y-5)?.total||0} คะแนน`,sub:'คะแนนสูง = เสรีมาก',color:C.freedom})}</div>`);
      p.push('<div class="grid">');
      p.push(APP.card({id:'det_fo_asean',title:'คะแนนเสรีภาพอินเทอร์เน็ต ไทยเทียบอาเซียน',unit:'คะแนน 0–100',period:`ปีข้อมูล ${y}`,src:'Freedom on the Net'}));
      after.push(()=>{const ids=Object.keys(D.meta.asean);const yrs=[...new Set(D.fotn.map(r=>r.y))].sort((a,b)=>a-b);mount('det_fo_asean',{legend:{type:'scroll',top:0},xAxis:{type:'category',data:yrs.map(String)},yAxis:{type:'value',min:0,max:100},series:ids.map((iso,j)=>({name:D.meta.asean[iso],type:'line',connectNulls:false,color:iso==='THA'?C.freedom:'#B9B6AE',lineStyle:{width:iso==='THA'?3:1.2},data:yrs.map(yy=>D.fotn.find(r=>r.iso3===iso&&r.y===yy)?.total??null)}))});});
      p.push(APP.card({id:'det_fo_comp',title:`ไทย ปี ${y}: 3 ส่วนของคะแนน`,unit:'% ของคะแนนเต็ม',period:`ปีข้อมูล ${y}`,src:'Freedom on the Net'}));
      after.push(()=>th&&mount('det_fo_comp',{grid:{left:12,right:40,top:10,bottom:10,containLabel:true},xAxis:{type:'value',max:100},yAxis:{type:'category',data:['สิทธิผู้ใช้','การจำกัดเนื้อหา','อุปสรรคการเข้าถึง']},series:[{type:'bar',data:[{value:th.rig/40*100,label:`${th.rig}/40`},{value:th.con/35*100,label:`${th.con}/35`},{value:th.acc/25*100,label:`${th.acc}/25`}],color:C.freedom,label:{show:true,position:'right',formatter:q=>q.data.label}}]}));
      const y0=y-5, changes=[];
      for(const r of fr){const old=D.fotn.find(q=>q.iso3===r.iso3&&q.y===y0);if(old)changes.push({country:r.country,iso3:r.iso3,change:r.total-old.total});}
      const changeEnds=changes.length>16?[...changes.slice().sort((a,b)=>a.change-b.change).slice(0,8),...changes.slice().sort((a,b)=>b.change-a.change).slice(0,8)].sort((a,b)=>a.change-b.change):changes.sort((a,b)=>a.change-b.change);
      p.push(APP.card({id:'det_fo_change',title:`ประเทศที่คะแนนเปลี่ยนมากที่สุด (${y0}–${y})`,unit:'คะแนน',period:`เปรียบเทียบปีข้อมูล ${y0} กับ ${y}`,src:'Freedom on the Net'}));
      after.push(()=>changeEnds.length&&mount('det_fo_change',{grid:{left:15,right:38,top:12,bottom:10,containLabel:true},xAxis:{type:'value',name:'เปลี่ยน (คะแนน)'},yAxis:{type:'category',inverse:true,data:changeEnds.map(r=>r.country)},series:[{type:'bar',data:changeEnds.map(r=>({value:r.change,itemStyle:{color:r.iso3==='THA'?C.scam:r.change<0?C.scam:C.global}})),label:{show:true,position:'right',formatter:q=>`${q.value>0?'+':''}${q.value}`}}]}));
      p.push(APP.card({id:'det_fo_map',title:`คะแนนอินเทอร์เน็ตรายประเทศ (${y})`,unit:'คะแนน 0–100',period:`ปีข้อมูล ${y}`,src:'Freedom on the Net',span:true}));
      after.push(()=>{if(!window.echarts.getMap('world'))return;mount('det_fo_map',{visualMap:{min:0,max:100,left:'center',bottom:4,orient:'horizontal',inRange:{color:['#D9E8F0','#A8DAD6','#0F766E']}},tooltip:{trigger:'item',formatter:q=>q.value===undefined?`${q.name}<br>ไม่มีข้อมูล`:`${q.name}: ${q.value}`},series:[{type:'map',map:'world',roam:true,data:fr.map(r=>({name:r.country,value:r.total}))}]});});
      p.push('</div><div class="note">ปีข้อมูลต่างจากปีรายงาน 1 ปี · คะแนนเป็นการประเมินของผู้เชี่ยวชาญ ไม่ใช่การนับเหตุการณ์</div>');
    } else {
      const eu=D.eu, years=new Map(), kw=new Map();for(let i=0;i<eu.d.length;i++){const y=L.yearOf(eu.d[i]);years.set(y,(years.get(y)||0)+1);for(const k of eu.k[i])kw.set(eu.kw[k],(kw.get(eu.kw[k])||0)+1);}
      const ys=[...years.keys()].sort((a,b)=>a-b), kws=[...kw.entries()].sort((a,b)=>b[1]-a[1]).slice(0,15).reverse(), dm=D.analysis.eu_domains, lg=D.analysis.eu_languages;
      p.push('<h3>EUvsDisinfo — ข้อมูลเท็จฝั่งสนับสนุนรัสเซีย (กรณีศึกษาเปรียบเทียบ)</h3><div class="note">ชุดข้อมูลนี้เก็บเฉพาะข้อมูลเท็จฝั่งสนับสนุนรัสเซีย จึงใช้สรุปว่าฝ่ายใดปล่อยข่าวเท็จมากกว่าไม่ได้</div><div class="grid">');
      p.push(APP.card({id:'det_eu_year',title:'จำนวนการหักล้างรายปี',unit:'การหักล้างที่ไม่ซ้ำ',period:ys.length?`${ys[0]}–${ys.at(-1)}`:'–',src:'EUvsDisinfo'}));
      after.push(()=>ys.length&&mount('det_eu_year',{xAxis:{type:'category',data:ys.map(String)},yAxis:{type:'value',name:'เรื่อง'},series:[{type:'bar',data:ys.map(y=>years.get(y)),color:C.global}]}));
      p.push(APP.card({id:'det_eu_kw',title:'ประเด็น/เรื่องเล่าที่พบบ่อย',unit:'จำนวนการหักล้าง',period:APP.periodText(eu.d),src:'EUvsDisinfo'}));
      after.push(()=>mount('det_eu_kw',{grid:{left:12,right:30,top:10,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',data:kws.map(r=>r[0])},series:[{type:'bar',data:kws.map(r=>r[1]),color:C.global}]}));
      p.push(APP.card({id:'det_eu_domain',title:'โดเมนบทความที่พบบ่อย',unit:'บทความ',period:APP.periodText(eu.d),src:'EUvsDisinfo'}));
      after.push(()=>mount('det_eu_domain',{grid:{left:12,right:30,top:10,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',data:dm.map(r=>r.domain)},series:[{type:'bar',data:dm.map(r=>r.articles),color:C.global}]}));
      p.push(APP.card({id:'det_eu_lang',title:'ภาษาของบทความ',unit:'บทความ',period:APP.periodText(eu.d),src:'EUvsDisinfo'}));
      after.push(()=>mount('det_eu_lang',{grid:{left:12,right:30,top:10,bottom:10,containLabel:true},xAxis:{type:'value'},yAxis:{type:'category',data:lg.map(r=>r.language)},series:[{type:'bar',data:lg.map(r=>r.articles),color:C.global}]}));
      p.push('</div>');
    }
    return {html:p.join(''),after};
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
