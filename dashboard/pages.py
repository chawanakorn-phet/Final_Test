"""One render function per tab. Numbers are computed from the processed tables, never typed in."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

import config
from analytics import filters as ft
from analytics import findings as fd
from analytics import metrics as mx
from dashboard import charts as ch
from dashboard import components as ui

C = config.COLORS
Tables = dict[str, pd.DataFrame]


TH_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def _d(ts: pd.Timestamp) -> str:
    """Thai month, Gregorian year (the data files use ค.ศ.)."""
    return f"{ts.day} {TH_MONTHS[ts.month - 1]} {ts.year}"


# ------------------------------------------------------------------ overview


def overview(t: Tables, meta: dict) -> None:
    w = t["weekly"]
    lw = mx.latest_week(w)
    recent, last_year = mx.recent_false_share(w)
    last_afnc_week = w["week_start"].max()
    cols = st.columns(5)
    with cols[0]:
        ui.kpi(f"คดีออนไลน์ สัปดาห์ {_d(lw.week_start)}–{_d(lw.week_end)}", ui.fmt_int(lw.cases),
               ui.delta_html(lw.cases_vs_base, f"เทียบเฉลี่ย {lw.base_weeks} สัปดาห์ก่อน"), icon="#")
    with cols[1]:
        ui.kpi("ความเสียหายสัปดาห์นั้น", ui.fmt_million(lw.loss_baht) + (" *" if lw.rounded else ""),
               ui.delta_html(lw.loss_vs_base, f"เทียบเฉลี่ย {lw.base_weeks} สัปดาห์ก่อน"), icon="฿")
    with cols[2]:
        ui.kpi("ความเสียหายต่อคดี", f"{lw.loss_per_case:,.0f} บาท", ui.delta_html(lw.lpc_vs_base, "เทียบ 4 สัปดาห์ก่อน"), icon="฿/#")
    with cols[3]:
        ui.kpi("สัดส่วนข่าวเท็จ 4 สัปดาห์ล่าสุด", f"{recent:.1f}%", ui.delta_html(
            None if last_year != last_year else recent - last_year, "จุด เทียบช่วงเดียวกันปีก่อน", higher_is_worse=True)
            .replace("%", ""), accent=C["fake"], icon="%")
    with cols[4]:
        ui.kpi("เหตุการณ์ AI ในฐานข้อมูลโลก", ui.fmt_int(meta["n_aiid_incidents"]),
               f'<div class="delta">ฉบับ {meta["aiid_snapshot"]}</div>', accent=C["ai"], icon="AI")
    if lw.rounded:
        ui.caption("* ตั้งแต่ 9 ส.ค. 2026 ตำรวจแถลงความเสียหายเป็นตัวเลขปัดล้านบาท")
    ui.caption(f"สัปดาห์คดีล่าสุดที่แถลงคือ {_d(lw.week_start)}–{_d(lw.week_end)} ส่วนข้อมูลข่าวปลอมถึง {_d(last_afnc_week + pd.Timedelta(days=6))} "
               "สัปดาห์ที่ไม่มีการแถลงแสดงเป็นช่องว่าง")

    from dashboard import question_pages as qp
    qa = qp.analysis(meta["built_at"])
    st.markdown("### ข้อค้นพบสำคัญ")
    top = [f for k in ("q1", "q2", "q3") for f in qa.findings[k][:2]]
    order = [0, 2, 4, 1, 3, 5]
    qp.cards([top[i] for i in order], cols=3)
    d0 = w.loc[w["acsc_reported"], "week_start"].min().to_pydatetime()
    d1 = w["week_start"].max().to_pydatetime()
    with st.container(border=True):
        st.markdown("<div class='filterbar'>ตัวกรอง · มีผลกับกราฟด้านล่าง ไม่เปลี่ยนตัวเลขหลักและข้อค้นพบ</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([6, 1])
        with c1:
            st.slider("ช่วงสัปดาห์", min_value=d0, max_value=d1, value=(d0, d1), step=timedelta(days=7), format="D MMM YYYY", key="ov_range")
        with c2:
            st.button("ล้างตัวกรอง", on_click=lambda: st.session_state.update(ov_range=(d0, d1)), key="ov_reset")
    lo, hi = st.session_state["ov_range"]
    w_view = ft.slice_weeks(w, lo, hi)
    st.markdown("### คดีหลอกลวง vs ข่าวเท็จ")
    if w_view["acsc_reported"].sum() >= 2:
        ui.chart(ch.scam_vs_fake(w_view), "ov_main")
    else:
        st.info("ช่วงที่เลือกสั้นเกินไป — เลือกอย่างน้อย 2 สัปดาห์ที่มีการแถลง")
    ui.read_hint("แถบเทา = สัปดาห์ที่ไม่มีการแถลง (ไม่ใช่ 0) · แถบเหลือง = ตัวเลขน่าสงสัย ถูกตัดออกจากสถิติ · จุดโปร่ง = ตัวเลขความเสียหายที่ปัดเป็นล้านบาท")
    r = mx.correlation_note(w)
    ui.note(f"<b>ห้ามตีความว่าสองเส้นเป็นเหตุและผลของกันและกัน</b> ความสัมพันธ์ระหว่างสัดส่วนข่าวเท็จกับจำนวนคดีเป็น r = {r['cases']:+.2f} "
            f"และกับความเสียหายเป็น r = {r['loss']:+.2f} จากเพียง {r['n']} สัปดาห์ ซึ่งอ่อนและปนกับแนวโน้มตามเวลา · "
            "จำนวนคำตัดสินของ AFNC คงที่ราว 49 เรื่อง/สัปดาห์ จึงสะท้อนโควตางาน ไม่ใช่ปริมาณข่าวปลอมจริง")

    if ui.notes_on():
        st.markdown("### ภาพรวม 5 ชุดข้อมูล")
        s = mx.cases_loss_stats(w)
        ai = mx.aiid_summary(t["aiid_yearly"], t["aiid_risk"], int(t["aiid_yearly"]["year"].max()))
        th = mx.thailand_fotn(t["fotn"]).iloc[-1]
        rank, n = mx.fotn_rank(t["fotn"], "THA", int(th["data_year"]))
        eu = t["eu_yearly"]
        rows = [
            ("ศูนย์ต่อต้านข่าวปลอม (AFNC)", f"{meta['n_afnc_posts']:,} โพสต์ ถึง {meta['afnc_last_date']}", "ข่าวเท็จในไทยเปลี่ยนประเด็นและสัดส่วนอย่างไร"),
            ("สถิติคดีหลอกลวง (ACSC)", f"{s['weeks']} สัปดาห์ที่ใช้ได้ เฉลี่ย {s['cases_mean']:,.0f} คดี และ {s['loss_mean'] / 1e6:,.0f} ล้านบาท/สัปดาห์",
             "ภัยออนไลน์ในไทยรุนแรงแค่ไหน"),
            ("AI Incident Database", f"{ai['total']:,} เหตุการณ์ · deepfake {ai['deepfake']:,} · scam/fraud {ai['scam']:,}", "AI ถูกใช้ก่อปัญหาและหลอกลวงมากขึ้นหรือไม่"),
            ("Freedom on the Net", f"ไทย {int(th['total_score'])}/100 ({th['status_th']}) อันดับ {rank} จาก {n} ประเทศ ปี {int(th['data_year'])}",
             "ไทยอยู่ตรงไหนในเสรีภาพอินเทอร์เน็ต"),
            ("EUvsDisinfo", f"{int(eu['debunks'].sum()):,} การหักล้างที่ไม่ซ้ำ (2015–2023)", "กรณีศึกษาข้อมูลเท็จระดับภูมิรัฐศาสตร์ เพื่อเทียบวิธีวิเคราะห์"),
        ]
        st.dataframe(pd.DataFrame(rows, columns=["ชุดข้อมูล", "ขนาด / ค่าสำคัญ", "ตอบคำถามอะไร"]), hide_index=True, width="stretch")


# ------------------------------------------------------------------ AFNC


def afnc(t: Tables, meta: dict) -> None:
    w = t["weekly"]
    st.subheader("ข่าวปลอมในไทย — ศูนย์ต่อต้านข่าวปลอม (AFNC)")
    yearly = mx.afnc_yearly(w)
    c1, c2 = st.columns([3, 2])
    with c1:
        year_from = st.select_slider("แสดงตั้งแต่ปี", options=list(range(2020, 2027)), value=2022, key="afnc_from")
        mode = st.radio("แสดงเป็น", ["จำนวนเรื่อง", "สัดส่วน %"], horizontal=True, key="afnc_mode")
        ui.chart(ch.category_monthly(t["afnc_monthly"], year_from, mode == "สัดส่วน %"), "afnc_cat")
    with c2:
        ui.chart(ch.verdict_mix(yearly), "afnc_mix")
    ui.note("<b>หมวดข่าวเปลี่ยนนิยามในปี 2026</b> ศูนย์ฯ เพิ่มหมวด 'อาชญากรรมออนไลน์' จึงทำให้สัดส่วนหมวดการเงินปี 2026 ต่ำลงเทียบกับปีก่อน ๆ "
            "ซึ่งเป็นผลของการจัดหมวด ไม่ใช่การเปลี่ยนของโลกจริง · ปี 2019 มีน้อยมากเพราะศูนย์ฯ เปิดเดือน พ.ย. 2019 จึงไม่แสดง")
    ui.read_hint("จำนวนคำตัดสินเป็นสิ่งที่ศูนย์ฯ เลือกตรวจ ไม่ใช่ปริมาณข่าวปลอมที่มีอยู่จริง ให้ดูสัดส่วนและการเปลี่ยนของหมวดมากกว่าตัวเลขดิบ "
                  "สัดส่วนข่าวเท็จคำนวณจากผลรวมของแต่ละปี")
    lo, hi = st.select_slider("ช่วงปีสำหรับอันดับ", options=list(range(2019, 2027)), value=(2024, 2026), key="afnc_range")
    c3, c4 = st.columns(2)
    with c3:
        a = mx.top_agencies(t["afnc_agencies"], lo, hi)
        ui.chart(ch.hbar(a, "n", "checked_by_agency", C["fake"], f"หน่วยงานที่ตรวจข้อเท็จจริงบ่อยที่สุด ({lo}–{hi})", height=430), "afnc_ag")
    with c4:
        tg = mx.top_tags(t["afnc_tags"], lo, hi)
        ui.chart(ch.hbar(tg, "n", "tag", C["fake"], f"หัวข้อที่พบบ่อยที่สุด ({lo}–{hi})", height=430), "afnc_tag")
    ui.read_hint("แท็กที่สะกดต่างกันแต่หมายถึงเรื่องเดียวกัน (เช่น โควิด-19 / COVID19) ถูกรวมแล้ว และตัดแท็กทั่วไปของศูนย์ฯ ออก · "
                 "ว่างข้อมูลหน่วยงานราว 15% ของคำตัดสิน")
    ui.source("ศูนย์ต่อต้านข่าวปลอม (opendata.antifakenewscenter.com) ดาวน์โหลด 1 พ.ย. 2026 · ระบบไม่ได้ระบุสัญญาอนุญาต")


# ------------------------------------------------------------------ scams


def scams(t: Tables, meta: dict) -> None:
    w = t["weekly"]
    st.subheader("คดีหลอกลวงออนไลน์ — ศูนย์ต่อต้านการฉ้อโกงออนไลน์ (ACSC)")
    ui.note(f"ตัวเลขนี้ <b>รวบรวมจากข่าวแถลงรายสัปดาห์</b> ไม่ใช่ข้อมูลเปิดของตำรวจ · มีเพียง {meta['acsc_weeks_usable']} สัปดาห์ที่ใช้ได้ "
            f"({meta['acsc_first_week']} ถึง {meta['acsc_last_week']}) · เป็นเฉพาะคดีที่มีผู้แจ้งความ ความเสียหายจริงน่าจะสูงกว่า", "info")
    m = mx.monthly_scam(w)
    ui.chart(ch.scam_monthly(m), "sc_month")
    ui.read_hint("เดือนที่มีสัปดาห์ใช้ได้น้อย (ดูตารางด้านล่าง) ค่าเฉลี่ยจะไม่แน่นอนกว่า · สัปดาห์ 16–22 ส.ค. ถูกตัดออกเพราะตัวเลขสูงกว่าปกติราว 13 เท่า")
    c1, c2 = st.columns(2)
    with c1:
        ui.chart(ch.scam_types(t["acsc_types"]), "sc_types")
        ui.read_hint("ป้ายประเภทคดีในไฟล์สะกดต่างกันหลายแบบ ถูกจัดเป็นกลุ่มแล้ว · ข้อมูลประเภทมีไม่ครบทุกสัปดาห์ จึงนับเป็นจำนวนสัปดาห์ ไม่ใช่ยอดรวม")
    with c2:
        mm = m[["month", "weeks", "cases", "loss", "loss_per_case"]].copy()
        mm["month"] = mm["month"].dt.strftime("%Y-%m")
        mm["cases"] = mm["cases"].round(0)
        mm["loss"] = (mm["loss"] / 1e6).round(0)
        mm["loss_per_case"] = mm["loss_per_case"].round(0)
        st.dataframe(mm.rename(columns={"month": "เดือน", "weeks": "สัปดาห์ที่ใช้ได้", "cases": "คดี/สัปดาห์ (เฉลี่ย)",
                                        "loss": "ล้านบาท/สัปดาห์ (เฉลี่ย)", "loss_per_case": "บาท/คดี"}),
                     hide_index=True, width="stretch", height=360)
    ui.source("ข่าวแถลงรายสัปดาห์ของ ศตฉอ.ตร./ACSC ผ่านสำนักข่าวต่าง ๆ — ลิงก์ต้นทางอยู่ในคอลัมน์ source_url ของ acsc_weekly.csv")


# ------------------------------------------------------------------ AI


def ai(t: Tables, meta: dict) -> None:
    y, risk = t["aiid_yearly"], t["aiid_risk"]
    latest_year = int(y["year"].max())
    s = mx.aiid_summary(y, risk, latest_year)
    st.subheader("AI Incident Database — AI ก่อปัญหา/ถูกใช้หลอกลวง")
    c = st.columns(4)
    with c[0]:
        ui.kpi("เหตุการณ์ทั้งหมด", f"{s['total']:,}", f'<div class="delta">ฉบับ {meta["aiid_snapshot"]}</div>', C["ai"])
    with c[1]:
        ui.kpi("เกี่ยวกับ deepfake", f"{s['deepfake']:,}", f'<div class="delta">{s["deepfake"] / s["total"]:.0%} ของทั้งหมด</div>', C["ai"])
    with c[2]:
        ui.kpi("เกี่ยวกับ scam/fraud", f"{s['scam']:,}", f'<div class="delta">{s["scam"] / s["total"]:.0%} ของทั้งหมด</div>', C["ai"])
    with c[3]:
        ui.kpi("จัดหมวดความเสี่ยงแล้ว", f"{s['classified_pct']:.0f}%", f'<div class="delta">ปีสูงสุด {s["peak_year"]}: {s["peak_n"]} เหตุการณ์</div>', C["ai"])
    ui.chart(ch.aiid_yearly(y, latest_year), "ai_year")
    ui.read_hint("นับตามวันเกิดเหตุ · deepfake / scam คือเหตุการณ์ที่ชื่อ คำอธิบาย หรือระบบที่เกี่ยวข้องมีคำนั้น (ไม่แยกตัวพิมพ์) จึงกว้างกว่าการนับเฉพาะคอลัมน์ระบบ")
    c1, c2 = st.columns(2)
    with c1:
        ui.chart(ch.aiid_risk(risk), "ai_risk")
        ui.note("แท่งสีเทา 'ยังไม่จัดหมวด' คือเหตุการณ์ที่ยังไม่ถูกกลุ่มวิจัยจัดหมวด ไม่ใช่ความเสี่ยงประเภทหนึ่ง", "info")
    with c2:
        ui.chart(ch.aiid_growth(t["aiid_growth"]), "ai_growth")
        ui.read_hint("เหตุการณ์ที่เพิ่มเข้าฐานข้อมูลในแต่ละสัปดาห์จำนวนมากเป็นเหตุเก่าที่เพิ่งถูกบันทึก "
                     "จึงต้องแยก 'ปีที่เกิดเหตุ' ออกจาก 'สัปดาห์ที่บันทึก' · ไม่มีเหตุการณ์ใดถูกลบระหว่างฉบับ")
    st.markdown("#### เหตุการณ์ที่เกี่ยวข้องกับประเทศไทย")
    th = t["aiid_thai"].copy()
    th["ประเภท"] = th.apply(lambda r: ", ".join(x for x, f in (("deepfake", r["is_deepfake"]), ("scam/fraud", r["is_scam"])) if f) or "-", axis=1)
    th["date"] = th["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(th[["Incident ID", "date", "title", "ประเภท", "report_count", "url"]].rename(columns={
        "Incident ID": "ID", "date": "วันที่", "title": "หัวข้อ", "report_count": "จำนวนข่าว", "url": "ลิงก์"}),
        hide_index=True, width="stretch", column_config={"ลิงก์": st.column_config.LinkColumn("ลิงก์", display_text="เปิด")})
    ui.note("ค้นจากคำว่า Thai/Thailand ในชื่อและคำอธิบาย เป็นรายการตัวอย่าง ไม่ใช่สัดส่วนจริง — ฐานข้อมูลเน้นข่าวภาษาอังกฤษและเหตุการณ์ในสหรัฐฯ "
            "และแทบไม่มีรหัสประเทศ/ภูมิภาค จึงไม่ทำแผนที่หรือกราฟแยกภูมิภาค")
    ui.source("AI Incident Database โดย Responsible AI Collaborative (incidentdatabase.ai) · ไม่ระบุสัญญาอนุญาต ให้อ้างอิงแหล่งที่มา")


# ------------------------------------------------------------------ freedom


def freedom(t: Tables, meta: dict) -> None:
    f = t["fotn"]
    st.subheader("Freedom on the Net — เสรีภาพอินเทอร์เน็ต")
    th_all = mx.thailand_fotn(f)
    th = th_all.iloc[-1]
    rank, n = mx.fotn_rank(f, "THA", int(th["data_year"]))
    c = st.columns(3)
    with c[0]:
        ui.kpi(f"คะแนนไทย ปีข้อมูล {int(th['data_year'])}", f"{int(th['total_score'])}/100",
               f'<div class="delta">{th["status_th"]} · เกณฑ์ "เสรีบางส่วน" เริ่มที่ 40</div>', C["freedom"])
    with c[1]:
        ui.kpi("อันดับ", f"{rank} จาก {n}", '<div class="delta">1 = เสรีที่สุด · ประเทศที่คะแนนเท่ากันได้อันดับเดียวกัน</div>', C["freedom"])
    with c[2]:
        prev = th_all[th_all["data_year"] == int(th["data_year"]) - 5]["total_score"]
        d = int(th["total_score"] - prev.iloc[0]) if len(prev) else None
        ui.kpi("เปลี่ยนใน 5 ปี", "–" if d is None else f"{d:+d} คะแนน", '<div class="delta">คะแนนสูง = เสรีมาก</div>', C["freedom"])
    c1, c2 = st.columns([3, 2])
    with c1:
        ui.chart(ch.fotn_asean(f), "fo_asean")
    with c2:
        ui.chart(ch.fotn_components(th), "fo_comp")
        ui.read_hint("ทั้ง 3 ส่วนมีคะแนนเต็มไม่เท่ากัน (25/35/40) จึงแสดงเป็น % ของคะแนนเต็ม")
    years = sorted(f["data_year"].unique())
    c3, c4 = st.columns([3, 2])
    with c3:
        yr = st.select_slider("ปีข้อมูลในแผนที่", options=years, value=years[-1], key="fo_year")
        ui.chart(ch.fotn_map(f, int(yr)), "fo_map")
    with c4:
        y0, y1 = st.select_slider("เปลี่ยนแปลงระหว่างปี", options=years, value=(2019, years[-1]), key="fo_chg")
        if y0 < y1:
            ui.chart(ch.fotn_change(mx.fotn_change(f, y0, y1)), "fo_change")
    ui.note("จำนวนประเทศเพิ่มจาก 37 (ปี 2010) เป็น 71 (ปี 2023–2024) <b>ค่าเฉลี่ยทุกประเทศจึงเทียบข้ามปีไม่ได้</b> จึงแสดงเป็นรายประเทศเท่านั้น · "
            "ปีข้อมูลต่างจากปีรายงาน 1 ปี (ข้อมูล 2024 = รายงานฉบับ 2025) · เป็นการประเมินของผู้เชี่ยวชาญ ไม่ใช่การนับเหตุการณ์", "info")
    ui.source("Freedom House ผ่าน QoG Standard Dataset (Jan 2026) มหาวิทยาลัยโกเธนเบิร์ก")


# ------------------------------------------------------------------ global disinfo


def global_disinfo(t: Tables, meta: dict) -> None:
    eu = t["eu_yearly"]
    st.subheader("EUvsDisinfo — ข้อมูลเท็จฝั่งสนับสนุนรัสเซีย (กรณีศึกษาเปรียบเทียบ)")
    ui.note("ฐานข้อมูลนี้ตั้งใจเก็บเฉพาะข้อมูลเท็จฝั่งสนับสนุนรัสเซีย จึง <b>ใช้สรุปว่าฝ่ายใดปล่อยข่าวเท็จมากกว่าไม่ได้</b> "
            "และไม่ผูกกับสถานการณ์ในไทย ใช้เพื่อดูวิธีวิเคราะห์ข้อมูลเท็จเท่านั้น", "info")
    c = st.columns(3)
    with c[0]:
        ui.kpi("การหักล้างที่ไม่ซ้ำ", f"{int(eu['debunks'].sum()):,}", f'<div class="delta">{int(eu["articles"].sum()):,} บทความ</div>', C["global"])
    with c[1]:
        peak = eu.loc[eu["debunks"].idxmax()]
        ui.kpi("ปีที่มีการหักล้างมากที่สุด", f"{int(peak['year'])}", f'<div class="delta">{int(peak["debunks"]):,} เรื่อง</div>', C["global"])
    with c[2]:
        ui.kpi("ข้อมูลล่าสุด", meta["eu_last_date"], '<div class="delta">ปีสุดท้ายไม่ครบปี</div>', C["global"])
    c1, c2 = st.columns(2)
    with c1:
        ui.chart(ch.eu_yearly(eu), "eu_year")
        ui.read_hint("ตัวเลขที่ลดลงหลังปี 2021 ไม่ได้แปลว่าข้อมูลเท็จลดลง — เป็นจำนวนที่โครงการเลือกหักล้างและเก็บเข้าชุดข้อมูล")
    with c2:
        ui.chart(ch.eu_keywords(t["eu_keywords"]), "eu_kw")
        ui.read_hint("นับ 1 ครั้งต่อการหักล้าง 1 เรื่อง (ไม่ใช่ต่อบทความ) เพราะบางเรื่องมีบทความผูกอยู่ถึง 125 ชิ้น")
    c3, c4 = st.columns(2)
    with c3:
        dm = t["eu_domains"]
        for cls, label, col in (("disinformation", "โดเมนที่พบบ่อยในกลุ่มข้อมูลเท็จ", C["global"]),):
            d = dm[dm["class"] == cls]
            ui.chart(ch.hbar(d, "articles", "domain", col, label, height=380), "eu_dom")
    with c4:
        lang = t["eu_languages"]
        ui.chart(ch.hbar(lang, "articles", "language", C["global"], "ภาษาของบทความ", height=380), "eu_lang")
    ui.source("EUvsDisinfo (EEAS) · Leite et al., CIKM 2024 ผ่าน Zenodo · CC BY 4.0")


# ------------------------------------------------------------------ analysis


def insights(t: Tables, meta: dict) -> None:
    a = fd.run_all(t)
    w = t["weekly"]
    u = mx.usable_weeks(w)
    st.subheader("วิเคราะห์เชิงลึก")
    ui.note("ทุกข้อด้านล่างคำนวณจากข้อมูลด้วย Python (analytics/insights.py) และมี unit test · แต่ละข้อระบุ <b>วิธี</b> <b>ผล</b> และ <b>ข้อควรระวัง</b> "
            "ซึ่งสำคัญพอ ๆ กับตัวเลข เพราะข้อมูลคดีมีเพียงไม่กี่สิบสัปดาห์", "info")
    findings = fd.key_findings(a)

    def block(idx: int, method: str) -> None:
        f = findings[idx]
        st.markdown(f"**{f['headline']}**")
        if ui.notes_on():
            st.markdown(f"<div class='read'>{f['title']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='read'>วิธี: {method}</div>", unsafe_allow_html=True)
            st.markdown(f["detail"])
            ui.note("ข้อควรระวัง: " + f["caution"])

    # 1 decomposition
    st.markdown("### 1) ความเสียหายลดเพราะอะไร")
    c1, c2 = st.columns([2, 3])
    with c1:
        if a.decomp:
            ui.chart(ch.loss_waterfall(a.decomp), "ix_wf")
    with c2:
        block(0, "ความเสียหาย = จำนวนคดี × ความเสียหายต่อคดี แยกส่วนต่างระหว่างช่วงที่สูงที่สุดกับต่ำที่สุด (ค่าเฉลี่ยเคลื่อนที่ 8 สัปดาห์) ให้ผลรวมตรงกันพอดี")

    # 2 change point
    st.markdown("### 2) จุดเปลี่ยน")
    c1, c2 = st.columns([3, 2])
    with c1:
        ui.chart(ch.change_point_chart(u, a.cp_cases, a.cp_lpc), "ix_cp")
    with c2:
        block(1, "หาจุดแบ่งเดียวที่ทำให้ความผันแปรภายในสองช่วงต่ำสุด (binary split) แล้วทดสอบด้วยการสลับลำดับสัปดาห์ 1,000 ครั้ง")

    # 3 outliers
    st.markdown("### 3) สัปดาห์ผิดปกติ")
    o = a.outliers
    out = o[o["flagged"]]
    c1, c2, c3 = st.columns(3)
    with c1:
        ui.kpi("สัปดาห์ผิดปกติ", str(len(out)), '<div class="delta">เกณฑ์ robust |z| &gt; 3.5</div>', C["warn"])
    with c2:
        wk = _d(out["week_start"].iloc[0]) if len(out) else "-"
        ui.kpi("z-score สูงสุด", f"{o['robust_z'].abs().max():.0f}", f'<div class="delta">สัปดาห์ {wk}</div>', C["scam"])
    with c3:
        ui.kpi("สัปดาห์ปกติ: |z| สูงสุด", f"{o.loc[~o['flagged'], 'robust_z'].abs().max():.1f}", f'<div class="delta">จาก {len(o) - len(out)} สัปดาห์</div>', C["global"])
    ui.read_hint("ใช้ robust z-score (มัธยฐานและ MAD) กับจำนวนคดีรายสัปดาห์ · ตัดเฉพาะค่าที่ผิดปกติจริง ไม่ใช่เลือกตัดเพื่อให้ได้ผลที่ต้องการ")

    # 4 lag
    st.markdown("### 4) ข่าวปลอม ↔ คดี")
    c1, c2 = st.columns([3, 2])
    with c1:
        ui.chart(ch.lag_chart(a.lag), "ix_lag")
    with c2:
        block(4, "ใช้การเปลี่ยนแปลงสัปดาห์ต่อสัปดาห์ (ตัดแนวโน้มร่วม) แล้วหาสหสัมพันธ์ที่ lag −4 ถึง +4 · แถบเทา = เกณฑ์ ±1.96/√n")

    # 5 mix shift + scam share
    st.markdown("### 5) ข่าวเท็จเปลี่ยนไปอย่างไร")
    c1, c2 = st.columns(2)
    with c1:
        ui.chart(ch.residual_heatmap(a.mix), "ix_mix")
    with c2:
        ui.chart(ch.scam_tag_share(a.scam_share), "ix_scamshare")
    block(3, "ทดสอบสัดส่วนสองกลุ่ม (ปีแรกกับปีล่าสุดที่ครบ) + χ² / Cramér's V ของตารางปี × หมวด (เฉพาะ 2020–2025 เพราะหมวดเปลี่ยนในปี 2026)")
    block(2, "นับสัดส่วนข่าวเท็จที่มีแท็กเกี่ยวกับการแอบอ้าง/หลอกลวงต่อปี")

    # 6 global
    st.markdown("### 6) ไทยเทียบอาเซียน/โลก")
    c1, c2 = st.columns(2)
    with c1:
        block(5, "อัตราส่วนปีฐานต่อปีล่าสุด และสัดส่วนของ deepfake/scam ในเหตุการณ์ทั้งหมดของปีนั้น")
    with c2:
        ui.chart(ch.asean_bars(a.asean["table"], a.asean["median_others"]), "ix_asean")
    block(6, "จัดอันดับในกลุ่มอาเซียนที่มีข้อมูล เทียบกับมัธยฐานของประเทศอื่น และส่วนประกอบที่ได้ % ต่ำสุด")

    if ui.notes_on():
        st.markdown("### สรุป: เชื่อได้แค่ไหน")
        st.dataframe(pd.DataFrame([
            ["แยกส่วนจำนวนคดี/ความเสียหายต่อคดี", "แน่น (เป็นการคำนวณตรง)", "บอก 'ส่วนใด' ไม่บอก 'ทำไม'"],
            ["จุดเปลี่ยนเมษายน 2026", "ค่อนข้างแน่น", "p-value มองต่ำเกินจริง; ไม่ทราบสาเหตุ"],
            ["การตัดสัปดาห์ผิดปกติ", "แน่น", "—"],
            ["ข่าวเท็จ ↔ คดี", "ไม่พบความสัมพันธ์", "n น้อย ไม่ใช่การพิสูจน์ว่าไม่มี"],
            ["ข่าวเท็จเปลี่ยนประเด็น", "แน่นทางสถิติ", "ศูนย์ฯ เลือกเรื่องเอง และเกณฑ์/หมวดเปลี่ยน"],
            ["deepfake/scam ใน AIID", "ปานกลาง", "ฐานปีแรกเล็ก; อคติของแหล่งข่าว"],
            ["ไทยเทียบอาเซียน", "ปานกลาง", "การประเมินผู้เชี่ยวชาญ"],
        ], columns=["ข้อค้นพบ", "ความมั่นใจ", "เหตุผล / ข้อจำกัด"]), hide_index=True, width="stretch")


# ------------------------------------------------------------------ data quality


def quality(t: Tables, meta: dict) -> None:
    st.subheader("คุณภาพข้อมูล")
    v = t["validation"].copy()
    counts = v["status"].value_counts()
    c = st.columns(3)
    with c[0]:
        ui.kpi("ผ่านการตรวจ", str(int(counts.get("ok", 0))), "", C["global"])
    with c[1]:
        ui.kpi("ข้อควรระวัง", str(int(counts.get("warn", 0))), "", C["warn"])
    with c[2]:
        ui.kpi("ไม่ผ่าน", str(int(counts.get("fail", 0))), "", C["scam"])
    v["สถานะ"] = v["status"].map({"ok": "✅ ผ่าน", "warn": "⚠️ ระวัง", "fail": "❌ ไม่ผ่าน"})
    st.dataframe(v[["สถานะ", "check", "detail"]].rename(columns={"check": "รายการตรวจ", "detail": "รายละเอียด"}),
                 hide_index=True, width="stretch")
    st.markdown("#### การทำความสะอาดข้อมูล (ก่อน → หลัง)")
    cl = t["cleaning_log"].fillna("")
    st.dataframe(cl.rename(columns={"dataset": "ชุดข้อมูล", "action": "สิ่งที่ทำ", "before": "ก่อน", "after": "หลัง", "detail": "หมายเหตุ"}),
                 hide_index=True, width="stretch")
    st.markdown("#### สัปดาห์คดีที่ไม่ได้ใช้ในสถิติ")
    w = t["weekly"]
    start = w.loc[w["acsc_reported"], "week_start"].min()
    bad = w[(w["week_start"] >= start) & ~w["acsc_usable"]].copy()
    bad["เหตุผล"] = bad.apply(lambda r: "ติดป้ายน่าสงสัย" if r["acsc_suspect"] else "ไม่มีการแถลง", axis=1)
    bad["week"] = bad["week_start"].dt.strftime("%Y-%m-%d")
    bad["acsc_cases"] = bad["acsc_cases"].map(lambda x: "–" if pd.isna(x) else f"{x:,.0f}")
    st.dataframe(bad[["week", "เหตุผล", "acsc_cases", "acsc_flag"]].rename(columns={"week": "สัปดาห์ (เริ่มวันอาทิตย์)", "acsc_cases": "คดีตามที่ระบุ", "acsc_flag": "หมายเหตุจากผู้รวบรวม"}),
                 hide_index=True, width="stretch")
    if ui.notes_on():
        st.markdown("#### กติกาการคำนวณ")
        st.markdown(
            "- **ไม่เติม 0 ให้สัปดาห์ที่ไม่มีข้อมูลคดี** — แสดงเป็นช่องว่าง\n"
            "- **สัดส่วนข่าวเท็จ** = (ปลอม + บิดเบือน) ÷ คำตัดสินทั้งหมด คำนวณจากผลรวม ไม่ใช่ค่าเฉลี่ยของเปอร์เซ็นต์รายสัปดาห์\n"
            "- **ความเสียหายต่อคดี** คำนวณใหม่จากความเสียหายรวม ÷ จำนวนคดี และไม่ใช้ค่า 'เพิ่ม/ลดจากสัปดาห์ก่อน' ที่ตำรวจแถลง เพราะเทียบกับตัวเลขที่ปรับปรุงแล้ว\n"
            "- **การหักล้าง EUvsDisinfo** นับ `debunk_id` ที่ไม่ซ้ำ · วันที่แปลงจากรูปแบบ DD-MM-YYYY\n"
            "- **deepfake / scam (AIID)** ค้นคำในชื่อ คำอธิบาย และระบบที่เกี่ยวข้อง จึงกว้างกว่าการนับเฉพาะคอลัมน์ระบบ\n"
            "- **FOTN** แสดงรายประเทศ ไม่เฉลี่ยข้ามปี เพราะจำนวนประเทศต่อปีไม่คงที่")
        st.markdown("#### แหล่งข้อมูลและสัญญาอนุญาต")
        st.markdown(
            "| ชุดข้อมูล | ผู้จัดทำ | ช่วงเวลา | สัญญาอนุญาต |\n|---|---|---|---|\n"
            f"| AI Incident Database | Responsible AI Collaborative | ถึง {meta['aiid_snapshot']} | ไม่ระบุ |\n"
            "| Freedom on the Net | Freedom House ผ่าน QoG | 2010–2024 | ดูเงื่อนไข QoG |\n"
            f"| EUvsDisinfo | EEAS / Leite et al. 2024 | 2015–{meta['eu_last_date'][:4]} | CC BY 4.0 |\n"
            f"| ศูนย์ต่อต้านข่าวปลอม | กระทรวงดิจิทัลฯ | 2019–{meta['afnc_last_date'][:4]} | ไม่ระบุ |\n"
            f"| สถิติคดี ACSC | รวบรวมจากข่าวแถลงของตำรวจ | {meta['acsc_first_week']} ถึง {meta['acsc_last_week']} | ไม่ใช่ข้อมูลเปิด |")
        st.caption(f"สร้างตารางประมวลผลเมื่อ {meta['built_at']} (UTC)")
