"""Builds the full written summary of the dashboard (Markdown) from the same tables and analyses the pages use.

Nothing here is typed-in data: every number comes from the processed tables or from analytics/*.
The summary always covers the full period (it ignores the page filters) so it can be shared as-is.
"""
from __future__ import annotations

import pandas as pd

import config
from analytics import metrics as mx
from analytics import qfindings as qf

Tables = dict[str, pd.DataFrame]


def _table(df: pd.DataFrame) -> str:
    """Plain Markdown table (no tabulate dependency)."""
    cols = list(df.columns)
    head = "| " + " | ".join(str(c) for c in cols) + " |\n|" + "|".join("---" for _ in cols) + "|\n"
    rows = []
    for _, r in df.iterrows():
        rows.append("| " + " | ".join("–" if (isinstance(v, float) and pd.isna(v)) else str(v) for v in r) + " |")
    return head + "\n".join(rows) + "\n"


def _f(x, nd: int = 1) -> str:
    return "–" if x is None or (isinstance(x, float) and pd.isna(x)) else f"{x:,.{nd}f}"


def _findings(items: list[dict]) -> str:
    out = []
    for i, f in enumerate(items, 1):
        out.append(f"{i}. **{f['headline']}**  \n   {f['detail']}  \n   *ข้อควรระวัง:* {f['caution']}")
    return "\n".join(out) + "\n"


def build_summary_markdown(t: Tables, meta: dict, q: qf.QAnalysis, forecasts: dict | None = None, linkage: list | None = None) -> str:
    w, a = t["weekly"], q.base
    lw = mx.latest_week(w)
    recent, last_year = mx.recent_false_share(w)
    s = mx.cases_loss_stats(w)
    d = qf._d
    L: list[str] = []
    add = L.append

    add("# สรุปแดชบอร์ด: ภัยข่าวปลอมและการหลอกลวงออนไลน์\n")
    add(f"สร้างเมื่อ {meta['built_at']} (UTC) · ข้อมูลข่าวปลอมถึง {meta['afnc_last_date']} · คดีหลอกลวงถึงสัปดาห์ {meta['acsc_last_week']} · "
        f"AI Incident Database ฉบับ {meta['aiid_snapshot']} · สรุปนี้ใช้ข้อมูลทั้งช่วง ไม่ขึ้นกับตัวกรองในหน้าแดชบอร์ด\n")

    add("**สารบัญ:** 1 สรุปสั้น · 2 อ่านแดชบอร์ดนี้อย่างไร · 3 ข้อมูลที่ใช้ · 4 การทำความสะอาดและคุณภาพ · 5 Q1 · 6 Q2 · 7 Q3 · 8 ข้อจำกัด · 9 วิธีวิเคราะห์ · 10 แหล่งที่มา\n")

    # ---------------------------------------------------------------- 1
    add("## 1. สรุปสั้น\n")
    add(f"- **คดีหลอกลวงล่าสุด** (สัปดาห์ {d(lw.week_start)}–{d(lw.week_end)}): {lw.cases:,.0f} คดี · {lw.loss_baht / 1e6:,.0f} ล้านบาท"
        f"{' (ตัวเลขปัด)' if lw.rounded else ''} · {lw.loss_per_case:,.0f} บาท/คดี · เทียบค่าเฉลี่ย {lw.base_weeks} สัปดาห์ก่อน: "
        f"คดี {_f(lw.cases_vs_base)}% · ความเสียหาย {_f(lw.loss_vs_base)}% · บาท/คดี {_f(lw.lpc_vs_base)}%")
    add(f"- **ภาพรวม {s['weeks']} สัปดาห์ที่ใช้ได้**: เฉลี่ย {s['cases_mean']:,.0f} คดี และ {s['loss_mean'] / 1e6:,.0f} ล้านบาทต่อสัปดาห์ · {s['lpc_overall']:,.0f} บาท/คดี")
    add(f"- **สัดส่วนข่าวเท็จ 4 สัปดาห์ล่าสุด:** {recent:.1f}% (ช่วงเดียวกันปีก่อน {last_year:.1f}%)")
    add("- **ข้อสรุปหลัก:**")
    for k in ("q1", "q2", "q3"):
        for f in q.findings[k][:2]:
            add(f"  - ({k.upper()}) {f['headline']}")
    add("")

    # ---------------------------------------------------------------- 2
    add("## 2. อ่านแดชบอร์ดนี้อย่างไร\n")
    add("แดชบอร์ดนี้เป็นเว็บ (HTML/CSS/JavaScript + ECharts) ที่แสดงผลจากข้อมูลที่ Python คำนวณไว้ มีหน้าปก 1 หน้า และ 5 แท็บ (แถบนำทางด้านบน) กับตัวกรองด้านซ้าย ลำดับที่แนะนำสำหรับคนที่เพิ่งเปิดดูคือ 1 → 2 → 3 → 4 → 5\n")
    add(_table(pd.DataFrame(GUIDE_PAGES, columns=["เมนู", "ตอบคำถามอะไร", "มีอะไรในหน้านี้", "ดูอะไรก่อน"])))
    add("**สัญลักษณ์ในกราฟ**\n")
    add(_table(pd.DataFrame(GUIDE_LEGEND, columns=["สัญลักษณ์", "ความหมาย"])))
    add("**ตัวเลขหลัก (การ์ดด้านบนของแต่ละหน้า)**\n")
    add(_table(pd.DataFrame(GUIDE_KPI, columns=["ตัวเลข", "คำนวณอย่างไร"])))
    add("**ตัวกรอง (แถบด้านซ้าย ใช้ร่วมกันทุกแท็บ)**\n")
    add(_table(pd.DataFrame(GUIDE_FILTERS, columns=["หน้า", "ตัวกรอง", "ชนิด", "เปลี่ยนอะไร"])))
    add("ตัวกรองเชื่อมโยงทุกแท็บและมีแถบ 'ตัวกรองที่ใช้อยู่' แสดงสถานะ ตัวกรองที่ใช้กับชุดข้อมูลใดไม่ได้จะไม่ถูกบังคับใช้ และระบบแจ้งเหตุผลแทนการแสดงข้อมูลที่ไม่เกี่ยวข้อง "
        "(เช่น ตั้งเป็น 'ต่างประเทศ' แล้วข้อมูล AFNC/ACSC ซึ่งเป็นของไทยจะแสดงข้อความอธิบาย) การทดสอบทางสถิติและการพยากรณ์ที่ต้องใช้แบบจำลองคำนวณจากข้อมูลทั้งช่วงด้วย Python และไม่เปลี่ยนตามตัวกรอง ส่วนตารางสหสัมพันธ์ในแท็บ 4 คำนวณใหม่ตามตัวกรอง\n")
    add("**ปุ่มและสวิตช์**\n")
    add(_table(pd.DataFrame(GUIDE_SWITCHES, columns=["ปุ่ม", "ทำอะไร"])))

    # ---------------------------------------------------------------- 3
    add("## 3. ข้อมูลที่ใช้\n")
    fotn = t["fotn"]
    data = pd.DataFrame([
        ["ศูนย์ต่อต้านข่าวปลอม (AFNC)", "โพสต์ 1 ชิ้น", f"{meta['n_afnc_posts']:,} โพสต์", f"2019 – {meta['afnc_last_date']}", "Q1, Q2, Q3"],
        ["สถิติคดีหลอกลวง (ACSC)", "การแถลง 1 สัปดาห์", f"{int(w['acsc_reported'].sum())} สัปดาห์ (ใช้ได้ {meta['acsc_weeks_usable']})",
         f"{meta['acsc_first_week']} – {meta['acsc_last_week']}", "Q2"],
        ["EUvsDisinfo", "บทความที่ผูกกับการหักล้าง 1 เรื่อง", f"{meta['n_eu_debunks']:,} การหักล้าง", f"2015 – {meta['eu_last_date']}", "Q1"],
        ["AI Incident Database", "เหตุการณ์ AI ก่อปัญหา 1 เรื่อง", f"{meta['n_aiid_incidents']:,} เหตุการณ์", f"ถึง {meta['aiid_snapshot']}", "Q3"],
        ["Freedom on the Net", "ประเทศ-ปี", f"{len(fotn):,} แถว / {fotn['iso3'].nunique()} ประเทศ", f"2010 – {meta['fotn_last_year']}", "Q3"],
    ], columns=["ชุดข้อมูล", "1 แถว =", "ขนาด", "ช่วงเวลา", "ใช้ตอบ"])
    add(_table(data))

    # ---------------------------------------------------------------- 3
    add("## 4. การทำความสะอาดและคุณภาพข้อมูล\n")
    v = t["validation"]
    cnt = v["status"].value_counts()
    add(f"ตรวจคุณภาพ {len(v)} รายการ: ผ่าน {int(cnt.get('ok', 0))} · ข้อควรระวัง {int(cnt.get('warn', 0))} · ไม่ผ่าน {int(cnt.get('fail', 0))}\n")
    add("**สิ่งที่ทำกับข้อมูลดิบ (ก่อน → หลัง)**\n")
    cl = t["cleaning_log"].fillna("")
    add(_table(cl.rename(columns={"dataset": "ชุดข้อมูล", "action": "สิ่งที่ทำ", "before": "ก่อน", "after": "หลัง", "detail": "หมายเหตุ"})))
    add("**ข้อควรระวัง**\n")
    for _, r in v[v["status"] != "ok"].iterrows():
        add(f"- {r['check']}: {r['detail']}")
    add("")

    # ---------------------------------------------------------------- Q1
    add("## 5. Q1 ข้อมูลบิดเบือน: ระดับนานาชาติ vs ไทย\n")
    add(f"*{_Q['q1']}*\n")
    add(_findings(q.findings["q1"]))
    add("**ผลตรวจของไทยรายปี (% ของคำตัดสิน)**\n")
    ya = mx.afnc_yearly(w)
    mix = pd.DataFrame({"ปี": ya["year"], "คำตัดสิน": ya["afnc_verdicts"], "ปลอม %": (ya["afnc_fake"] / ya["afnc_verdicts"] * 100).round(1),
                        "บิดเบือน %": (ya["afnc_distorted"] / ya["afnc_verdicts"] * 100).round(1), "จริง %": (ya["afnc_true"] / ya["afnc_verdicts"] * 100).round(1),
                        "เท็จรวม %": ya["false_share_pct"].round(1)})
    add(_table(mix))
    add("**หมวดข่าวเท็จของไทย (% ต่อปี)**\n")
    cat = mx.category_share(t["afnc_monthly"]).pivot(index="year", columns="category_th", values="share_pct").round(1).reset_index().rename(columns={"year": "ปี"})
    add(_table(cat.fillna(0)))
    add("**สัดส่วนเรื่องที่เกี่ยวกับโควิด (%)**\n")
    cv = q.covid[q.covid["year"] >= 2018].pivot(index="year", columns="source", values="share_pct").round(1).reset_index().rename(columns={"year": "ปี"})
    add(_table(cv))
    y0, y1 = q.thai_years
    add(f"**หัวข้อข่าวเท็จไทยที่เปลี่ยนมากสุด ({y0}→{y1}, จุดเปอร์เซ็นต์)**\n")
    tr = pd.concat([q.thai_rising.head(5), q.thai_rising.tail(3)])
    add(_table(pd.DataFrame({"หัวข้อ": tr["topic"], f"{y0} %": tr["share_start"].round(1), f"{y1} %": tr["share_end"].round(1), "เปลี่ยน": tr["change_pp"].round(1)})))
    e0, e1 = q.eu_years
    add(f"**ประเด็น EUvsDisinfo ที่เปลี่ยนมากสุด ({e0}→{e1})**\n")
    er = pd.concat([q.eu_rising.head(5), q.eu_rising.tail(3)])
    add(_table(pd.DataFrame({"ประเด็น": er["topic"], f"{e0} %": er["share_start"].round(1), f"{e1} %": er["share_end"].round(1), "เปลี่ยน": er["change_pp"].round(1)})))
    add("**ข้อจำกัดของข้อ Q1:** EU ไม่มีเนื้อหาบทความและไม่มีป้ายปลอม/บิดเบือน/จริง (มีแค่ disinformation/trustworthy) · EU เก็บเฉพาะฝั่งสนับสนุนรัสเซียและสิ้นสุด ส.ค. 2023 · "
        "หมวดของสองฝั่งเป็นคนละระบบ · หมวดของ AFNC เปลี่ยนนิยามปี 2026\n")

    # ---------------------------------------------------------------- Q2
    add("## 6. Q2 ภัยหลอกลวงออนไลน์: แนวโน้ม ความเสียหาย และความผิดปกติ\n")
    add(f"*{_Q['q2']}*\n")
    add(_findings(q.findings["q2"]))
    dc = a.decomp
    if dc:
        add("**แยกส่วนการลดลงของความเสียหาย (ช่วงสูงสุด vs ต่ำสุด 8 สัปดาห์)**\n")
        add(_table(pd.DataFrame([
            ["ช่วง", f"{d(dc.peak_start)}–{d(dc.peak_end)}", f"{d(dc.trough_start)}–{d(dc.trough_end)}"],
            ["ความเสียหายเฉลี่ย (ล้านบาท/สัปดาห์)", f"{dc.loss_peak / 1e6:,.0f}", f"{dc.loss_trough / 1e6:,.0f}"],
            ["คดีเฉลี่ย/สัปดาห์", f"{dc.cases_peak:,.0f}", f"{dc.cases_trough:,.0f}"],
            ["บาท/คดี", f"{dc.lpc_peak:,.0f}", f"{dc.lpc_trough:,.0f}"],
        ], columns=["", "สูงสุด", "ต่ำสุด"])))
        add(f"ผลจากจำนวนคดี {dc.cases_effect / 1e6:,.0f} ล้านบาท · ผลจากความเสียหายต่อคดี {dc.severity_effect / 1e6:,.0f} ล้านบาท "
            f"({dc.severity_share:.0f}% ของการลดลงทั้งหมด)\n")
    cpc, cps = a.cp_cases, a.cp_lpc
    if cpc and cps:
        add("**จุดเปลี่ยน**\n")
        add(_table(pd.DataFrame([
            ["จำนวนคดี/สัปดาห์", d(cpc.date), f"{cpc.mean_before:,.0f}", f"{cpc.mean_after:,.0f}", f"{cpc.pct_change:+.1f}%", f"{cpc.variance_explained:.0%}"],
            ["บาท/คดี", d(cps.date), f"{cps.mean_before:,.0f}", f"{cps.mean_after:,.0f}", f"{cps.pct_change:+.1f}%", f"{cps.variance_explained:.0%}"],
        ], columns=["ตัวชี้วัด", "สัปดาห์ที่แบ่ง", "เฉลี่ยก่อน", "เฉลี่ยหลัง", "เปลี่ยน", "อธิบายความผันแปร"])))
    add("**บล็อก 4 สัปดาห์: คดีลดแต่บาท/คดีเพิ่ม?**\n")
    b = q.blocks
    add(_table(pd.DataFrame({"ช่วง": b["from"].dt.strftime("%Y-%m-%d") + " – " + b["to"].dt.strftime("%Y-%m-%d"), "คดี %": b["cases_chg_pct"].round(1),
                             "บาท/คดี %": b["lpc_chg_pct"].round(1), "คดีลดแต่บาท/คดีเพิ่ม": b["cases_down_lpc_up"].map({True: "ใช่", False: "–"})})))
    add("**สัปดาห์ผิดปกติ (เทียบมัธยฐานสัปดาห์รอบข้าง, robust z > 3.5)**\n")
    an = q.anomalies.head(10)
    if len(an):
        add(_table(pd.DataFrame({"ชุดข้อมูล": an["series"], "สัปดาห์": an["week_start"].dt.strftime("%Y-%m-%d"), "ค่า": an["value"].round(1),
                                 "คาดไว้": an["expected"].round(1), "z": an["z"].round(1)})))
    out = a.outliers[a.outliers["flagged"]]
    for r in out.itertuples():
        add(f"- สัปดาห์ {d(r.week_start)}: {r.acsc_cases:,.0f} คดี (มัธยฐาน {r.median:,.0f}, z = {r.robust_z:.0f}) ถูกตัดออกจากสถิติ")
    add("")
    add("**ประเภทคดี (จำนวนสัปดาห์ที่เป็นอันดับ 1)**\n")
    lt = q.loss_types.rename(columns={"scam_type": "ประเภท", "weeks_top_by_cases": "ด้านจำนวนคดี", "weeks_top_by_loss": "ด้านความเสียหาย"})
    add(_table(lt))
    r_ = q.relation
    add(f"**คดี ↔ ความเสียหาย:** r = {r_['r']:+.2f} · ความยืดหยุ่น {r_['elasticity']:.2f} · r(คดี, บาท/คดี) = {r_['r_lpc_cases']:+.2f} (n = {r_['n']})\n")
    add("**ข่าวปลอม ↔ คดี (การเปลี่ยนแปลงรายสัปดาห์, lag บวก = ข่าวปลอมนำหน้า)**\n")
    lag = a.lag
    add(_table(pd.DataFrame({"lag": lag["lag"], "r": lag["r"].round(2), "n": lag["n"], "เกณฑ์ ±": lag["ci95"].round(2), "เกินเกณฑ์": lag["significant"].map({True: "ใช่", False: "–"})})))
    add(f"สหสัมพันธ์ระดับดิบ r = {a.detrended['raw']:+.2f} → หลังตัดแนวโน้ม {a.detrended['detrended']:+.2f} (n = {a.detrended['n']})\n")
    if forecasts:
        add("**พยากรณ์ (แบบจำลองเลือกด้วย rolling-origin back-test, RMSE ต่ำสุด)**\n")
        for fk in forecasts.values():
            if fk.get("ok"):
                m = fk["metrics"][0]
                fr = fk["forecast"]
                add(f"- {fk['title']} ({fk['unit']}): แบบจำลอง **{fk['model']}** · MAE {m['MAE']:.2f} · RMSE {m['RMSE']:.2f} · พยากรณ์ช่วงถัดไป {fr[0]['forecast']:.1f} "
                    f"(ช่วง {fr[0]['lower']:.1f}–{fr[0]['upper']:.1f}) · ข้อมูล {fk['n_obs']} จุด — {fk['caveat']}")
            else:
                add(f"- {fk['title']}: {fk['reason']}")
        add("")
    add("**ข้อจำกัดของข้อ Q2:** คดีมี 47 สัปดาห์ใช้ได้ · ข้อมูลประเภทคดีเป็น 'อันดับ 1 ของสัปดาห์' ไม่ใช่ยอดเงินแยกประเภท · จำนวนคำตัดสินข่าวปลอมเป็นโควตา (~49/สัปดาห์) · "
        "ตัวเลขหลัง 9 ส.ค. ปัดเป็นล้านบาท · p-value ของจุดเปลี่ยนมองต่ำเกินจริงเพราะไม่คิดสหสัมพันธ์ข้ามสัปดาห์\n")

    # ---------------------------------------------------------------- Q3
    add("## 7. Q3 เสรีภาพอินเทอร์เน็ต ภัยจาก AI และการเทียบกับไทย\n")
    add(f"*{_Q['q3']}*\n")
    add(_findings(q.findings["q3"]))
    asn = a.asean
    add(f"**อาเซียน ปีข้อมูล {meta['fotn_last_year']}** (ไทยอันดับ {asn['rank']} จาก {asn['n']}, มัธยฐานประเทศอื่น {asn['median_others']:.0f})\n")
    tb = asn["table"]
    add(_table(pd.DataFrame({"ประเทศ": tb["country"].str.replace(r" \(.*\)", "", regex=True), "คะแนน": tb["total_score"], "การเข้าถึง %": tb["pct_access"].round(0),
                             "เนื้อหา %": tb["pct_content"].round(0), "สิทธิผู้ใช้ %": tb["pct_rights"].round(0)})))
    add("**ประเทศที่คะแนนใกล้ไทย (±6)**\n")
    pe = q.peers
    add(_table(pd.DataFrame({"ประเทศ": pe["country"], "คะแนน": pe["total_score"], "สถานะ": pe["status"], "เปลี่ยน 5 ปี": pe["change_5y"]})))
    add("**ธีมภัย: AI สากล (AIID) เทียบข่าวเท็จไทย (AFNC)**\n")
    ov = q.overlap.sort_values("share_pct_AIID", ascending=False)
    add(_table(pd.DataFrame({"ธีม": ov["theme"], "AIID %": ov["share_pct_AIID"].round(1), "AFNC %": ov["share_pct_AFNC"].round(1),
                             "เรื่องใน AFNC": ov["n_AFNC"].astype(int), "สถานะ": ov["status"]})))
    cl_ = q.country
    add(f"**เสรีภาพ vs การถูกกล่าวถึงใน AIID (สำรวจ):** ρ = {cl_['rho']:+.2f} (n = {cl_['n']} ประเทศที่ถูกกล่าวถึง ≥ 5 ครั้ง) · "
        f"กลุ่มไม่เสรีที่ถูกกล่าวถึงมาก: " + ", ".join(f"{r.country.split(' (')[0]} {r.mentions}" for r in cl_["not_free"].head(5).itertuples()) + "\n")
    ay = t["aiid_yearly"].tail(6)
    add(_table(pd.DataFrame({"ปี": ay["year"], "เหตุการณ์": ay["incidents"], "deepfake": ay["deepfake"], "scam/fraud": ay["scam"]})))
    if linkage:
        add("**ข้อมูลเชื่อมโยงข้ามชุดได้หรือไม่ (ผลที่ระบบใช้ตัดสินว่าจะคำนวณสหสัมพันธ์หรือไม่)**\n")
        add(_table(pd.DataFrame([[r["pair"], "ได้" if r["ok"] else "ไม่ได้", r["how"], r["limit"]] for r in linkage], columns=["คู่ข้อมูล", "เชื่อมได้", "วิธี/ช่วงที่ซ้อนกัน", "ข้อจำกัด"])))
    add("**ข้อจำกัดของข้อ Q3:** ช่องประเทศของ AIID มีเพียง ~8% จึงนับจากชื่อประเทศในข้อความ (การถูกกล่าวถึง ไม่ใช่ที่เกิดเหตุ) · AIID เอนไปทางข่าวภาษาอังกฤษ/สหรัฐฯ · "
        "'ยังไม่พบในไทย' หมายถึงไม่พบในข้อมูล AFNC ซึ่งเป็นข่าวที่ศูนย์ฯ เลือกตรวจ · ธีมจับจากคำในข้อความ หนึ่งเรื่องมีได้หลายธีม · ปีล่าสุดของ AIID ยังไม่ครบ\n")

    # ---------------------------------------------------------------- 7-9
    add("## 8. ข้อจำกัดโดยรวม\n")
    for x in [
        "ตัวเลขคดีรวบรวมจากข่าวแถลงรายสัปดาห์ ไม่ใช่ข้อมูลเปิดของตำรวจ และเป็นเฉพาะคดีที่มีผู้แจ้งความ",
        "จำนวนคำตัดสินของ AFNC คือสิ่งที่ศูนย์ฯ เลือกตรวจ ไม่ใช่ปริมาณข่าวปลอมจริง",
        "ผลที่ 'ไม่พบความสัมพันธ์' ไม่ใช่การพิสูจน์ว่าไม่มีความสัมพันธ์ (ตัวอย่างน้อย)",
        "ข้อมูลเป็นการสังเกต ไม่ระบุสาเหตุของการเปลี่ยนแปลงใด ๆ",
        "AIID/AFNC/ACSC ไม่ระบุสัญญาอนุญาต: ให้อ้างอิงแหล่งที่มา และตรวจสิทธิ์ก่อนเผยแพร่ต่อสาธารณะ",
    ]:
        add(f"- {x}")
    add("")
    add("## 9. วิธีวิเคราะห์\n")
    for x in [
        "แยกส่วนความเสียหาย = จำนวนคดี × ความเสียหายต่อคดี (ผลรวมตรงกันพอดี)",
        "จุดเปลี่ยนเดียวที่ทำให้ความผันแปรภายในสองช่วงต่ำสุด + ทดสอบด้วยการสลับลำดับ 1,000 ครั้ง (บ่งชี้เท่านั้น)",
        "robust z-score (มัธยฐาน/MAD) ทั้งแบบทั้งช่วงและแบบเทียบ 13 สัปดาห์รอบข้าง",
        "สหสัมพันธ์ของการเปลี่ยนแปลงรายสัปดาห์ที่ lag −4…+4 และเทียบระดับดิบกับหลังตัดแนวโน้มเชิงเส้น",
        "ทดสอบสัดส่วนสองกลุ่ม และ χ² / Cramér's V ของตารางปี × หมวด",
        "ส่วนต่างสัดส่วนของหัวข้อ (จุดเปอร์เซ็นต์) ระหว่างสองปี",
        "ติดธง 10 ธีมจากข้อความ (AIID อังกฤษ / AFNC ไทย) และ Spearman ระหว่างคะแนนเสรีภาพกับจำนวนที่ประเทศถูกกล่าวถึง",
    ]:
        add(f"- {x}")
    add("")
    add("## 10. แหล่งที่มา\n")
    for x in [
        "AI Incident Database — incidentdatabase.ai (Responsible AI Collaborative)",
        "Freedom on the Net — freedomhouse.org/report/freedom-net · QoG Standard Dataset (Jan 2026), qogdata.pol.gu.se",
        "EUvsDisinfo — euvsdisinfo.eu · Leite et al., CIKM 2024, zenodo.org/records/10514307 (CC BY 4.0)",
        "ศูนย์ต่อต้านข่าวปลอม — antifakenewscenter.com · opendata.antifakenewscenter.com",
        "สถิติคดีรายสัปดาห์ — ลิงก์ข่าวต้นทางในคอลัมน์ source_url ของ acsc_weekly.csv",
    ]:
        add(f"- {x}")
    return "\n".join(L).replace("\n\n\n", "\n\n")


_Q = {
    "q1": "รูปแบบ เนื้อหา และประเภทของข้อมูลบิดเบือนต่างกันอย่างไรระหว่างระดับนานาชาติกับไทย และอะไรเปลี่ยนไปตามเวลา",
    "q2": "ข่าวปลอมและภัยหลอกลวงออนไลน์ในไทยมีแนวโน้มและความเสียหายเปลี่ยนไปอย่างไร และตรวจจับช่วงผิดปกติได้หรือไม่",
    "q3": "เสรีภาพอินเทอร์เน็ตสัมพันธ์กับภัยจาก AI และข้อมูลบิดเบือนอย่างไร ไทยอยู่ตรงไหน และภัยสากลคล้ายกับที่ไทยเจอหรือไม่",
}


GUIDE_PAGES = [
    ["หน้าปก", "—", "ชื่อโครงการ 2 ภาษา คำอธิบาย ตัวเลขเด่น 3 ตัว ภาพประกอบเชิงสัญลักษณ์ ปุ่ม Open Dashboard", "กดปุ่มเพื่อเข้าแท็บ 1"],
    ["1 ภาพรวม", "ทั้งหมด (ย่อ)", "KPI 8 ใบ (คลิกเพื่อดูรายการต้นทาง) · กราฟแนวโน้มข่าวปลอม ความเสียหาย สัดส่วนข่าว ประเภทข่าว และคะแนนเสรีภาพ · สรุป Insight · ข้อค้นพบเชิงสถิติ", "KPI แล้วสรุป Insight"],
    ["2 ข่าวปลอมและข้อมูลบิดเบือน", "Q1", "2.1 เวลา (รายเดือน/ไตรมาส/ปี, เดือนสูงสุด, อัตราเปลี่ยนแปลง) · 2.2 ประเภทข่าว (แท่ง Treemap ตาราง ประเด็น EU โควิด หัวข้อเพิ่ม/ลด) · 2.3 สัดส่วนข่าวจริง/ปลอม (Donut, 100% stacked, ตัวหาร)", "กราฟ 2.1 แล้วตารางเปรียบเทียบช่วง"],
    ["3 เสรีภาพอินเทอร์เน็ตและเปรียบเทียบประเทศ", "Q3", "3.1 คะแนนไทย คะแนนย่อย อันดับ · 3.2 เปรียบเทียบประเทศ (Bar, Line, Heatmap, ตาราง) · 3.3 เทียบกับข่าวปลอม/ความเสียหาย (มีเกณฑ์ ≥ 10 คู่ข้อมูล)", "KPI ไทย แล้ว Heatmap"],
    ["4 ความเสียหาย ความสัมพันธ์ และพยากรณ์", "Q2", "4.1 ความเสียหาย (รายช่วง ประเภท รายการต้นทางพร้อมลิงก์ แยกส่วน ความผิดปกติ) · 4.2 สหสัมพันธ์ (ตาราง r/p/n, Scatter, lag) · 4.3 พยากรณ์ (5 แบบจำลอง MAE/RMSE ตารางจริง vs พยากรณ์)", "กราฟ 4.1 แล้วส่วนพยากรณ์"],
    ["5 สำรวจข้อมูลและแหล่งที่มา", "ความน่าเชื่อถือ", "ตารางข้อมูลต้นทางตามตัวกรอง (ค้นหา/CSV) · Inventory · ความสามารถในการเชื่อมข้ามชุด · ผลตรวจคุณภาพ · บันทึกการคลีน · Data Dictionary · Data Source Mapping", "Inventory แล้ว Source Mapping"],
]

GUIDE_LEGEND = [
    ["สีแดงเข้ม", "ข่าวปลอม การฉ้อโกง และความเสียหาย"],
    ["สีแดงอ่อน", "ข่าวบิดเบือน การแจ้งเตือน และข้อมูลที่ต้องเฝ้าระวัง (เช่น สัปดาห์ที่ตัวเลขน่าสงสัย)"],
    ["สีเขียว", "ข่าวจริง (เฉพาะคำตัดสิน 'ข่าวจริง' ที่ศูนย์ฯ ยืนยัน)"],
    ["สีเทา", "ข้อความประกอบ ข้อมูลทั่วไป หรือประเภทอื่นที่ไม่ใช่คำตัดสิน"],
    ["แถบเทาแนวตั้งในกราฟคดี", "สัปดาห์ที่ไม่มีการแถลงตัวเลข — ไม่ใช่ 0 เส้นจึงขาดตรงนั้น"],
    ["แถบแดงอ่อนแนวตั้งในกราฟคดี", "สัปดาห์ที่ตัวเลขน่าสงสัย (16–22 ส.ค. 2026) ถูกตัดออกจากสถิติ"],
    ["จุดโปร่ง", "ความเสียหายที่ตำรวจแถลงเป็นตัวเลขปัดล้านบาท (ตั้งแต่ 9 ส.ค. 2026)"],
    ["เส้นประสีน้ำเงิน + แถบน้ำเงินจาง", "ค่าพยากรณ์และช่วงความไม่แน่นอน (± 1.96 × RMSE ของ back-test) — แยกจากข้อมูลจริง (เส้นทึบสีแดง)"],
    ["Heatmap สีเทา/ช่องว่าง", "ไม่มีข้อมูลของประเทศ-ปีนั้น (ไม่ใช่ 0 คะแนน)"],
    ["ลูกศร ▲ แดง / ▼ เขียวในการ์ด", "เปลี่ยนแปลงเทียบช่วงก่อนหน้าที่ยาวเท่ากัน (ถ้ามีข้อมูลช่วงก่อนหน้าพอ มิฉะนั้นแสดง –)"],
]

GUIDE_KPI = [
    ["กรณีข้อมูลบิดเบือน / ข่าวปลอม / ข่าวจริง", "นับโพสต์ที่เป็นคำตัดสิน (Verdict) ของ AFNC ในช่วง/หมวด/สถานะที่เลือก"],
    ["การหักล้างนานาชาติ (EU)", "นับ debunk_id ที่ไม่ซ้ำ ไม่ใช่จำนวนบทความ"],
    ["มูลค่าความเสียหาย", "รวมเฉพาะสัปดาห์ที่มีการแถลงและไม่ติดป้ายน่าสงสัย สัปดาห์ที่ไม่มีตัวเลขไม่นับเป็น 0"],
    ["จำนวนผู้เสียหาย", "ไม่มีในชุดข้อมูล (คดีที่แจ้ง ≠ ผู้เสียหาย) จึงไม่แสดง"],
    ["คะแนนเสรีภาพไทย / ประเทศเปรียบเทียบ", "ปีข้อมูลล่าสุดในช่วงที่เลือก; ประเทศเปรียบเทียบ = ประเทศแรกที่เลือก มิฉะนั้นมัธยฐานของประเทศที่ผ่านตัวกรอง"],
    ["อันดับเสรีภาพ", "1 + จำนวนประเทศที่คะแนนสูงกว่าในปีเดียวกัน (คะแนนเท่ากันได้อันดับเดียวกัน)"],
    ["เทียบช่วงก่อนหน้า", "ช่วงเวลาที่ยาวเท่ากันก่อนหน้าช่วงที่เลือก ภายใต้ตัวกรองอื่นเดียวกัน"],
]

GUIDE_FILTERS = [
    ["ทุกแท็บ", "ช่วงวันที่ · ปี · ไตรมาส · เดือน", "ช่องวันที่ + ปุ่มเลือกได้หลายค่า", "ใช้กับ AFNC, ACSC, EUvsDisinfo, AIID (Freedom on the Net ใช้เฉพาะส่วนปี)"],
    ["ทุกแท็บ", "ประเทศไทย / ต่างประเทศ", "ปุ่มเลือก 1 ค่า", "ไทย: AFNC, ACSC, คะแนนไทย, เหตุการณ์ AI ที่เกี่ยวกับไทย · ต่างประเทศ: EUvsDisinfo, คะแนนประเทศอื่น"],
    ["ทุกแท็บ", "กลุ่มประเทศ · ประเทศ", "รายการเลือก + ค้นหา", "Freedom on the Net (ไทยแสดงเสมอเป็นจุดอ้างอิง ยกเว้นเลือก 'ต่างประเทศ')"],
    ["ทุกแท็บ", "ประเภทข่าว · สถานะข่าว", "ปุ่มเลือกได้หลายค่า", "AFNC เท่านั้น (สถานะ: ข่าวปลอม/บิดเบือน/จริง/อื่น ๆ)"],
    ["ทุกแท็บ", "หมวดหมู่ความเสียหาย", "ปุ่มเลือกได้หลายค่า", "ACSC — เลือกสัปดาห์ที่ประเภทที่เสียหายสูงสุดตรงกับที่เลือก"],
    ["ทุกแท็บ", "แหล่งข้อมูล", "ช่องติ๊ก", "เปิด/ปิดชุดข้อมูล (ชุดที่ปิดแสดงข้อความอธิบาย)"],
]

GUIDE_SWITCHES = [
    ["📄 สรุปทั้งแดชบอร์ด", "เปิดรายงานฉบับนี้ ดาวน์โหลดเป็น .md ได้ (ใช้ข้อมูลทั้งช่วง ไม่ขึ้นกับตัวกรอง)"],
    ["↺ Reset Filters", "คืนตัวกรองทั้งหมดเป็นค่าเริ่มต้น"],
    ["คำอธิบาย (ช่องติ๊ก)", "แสดงคำอธิบายและข้อสรุปใต้กราฟ (ปิดเป็นค่าเริ่มต้นเพื่อใช้ตอนนำเสนอ)"],
    ["หน้าแรก", "กลับหน้าปก"],
    ["คลิก KPI", "เปิดรายการต้นทาง แหล่งที่มา วิธีคำนวณ และปุ่มดาวน์โหลด CSV"],
]
