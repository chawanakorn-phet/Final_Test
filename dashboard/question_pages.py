"""The three research-question pages, each with a filter bar on top. Charts first; prose only behind the 'show notes' switch.

Filters change the charts and headline numbers. The statistical findings (cards, change-point, decomposition, lag test)
are computed on the full period on purpose: re-running a significance test on whatever window someone drags to would
give numbers that look precise but are not comparable.
"""
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

import config
from analytics import comparisons as cp
from analytics import filters as ft
from analytics import insights as ix
from analytics import metrics as mx
from analytics import qfindings as qf
from dashboard import charts as ch
from dashboard import charts_q as cq
from dashboard import components as ui
from dashboard.pages import _d
from data_processing import store

C = config.COLORS
Tables = dict[str, pd.DataFrame]

QUESTIONS = {
    "q1": "รูปแบบ เนื้อหา และประเภทของข้อมูลบิดเบือนต่างกันอย่างไรระหว่างระดับนานาชาติกับไทย และอะไรเปลี่ยนไปตามเวลา",
    "q2": "ข่าวปลอมและภัยหลอกลวงออนไลน์ในไทยมีแนวโน้มและความเสียหายเปลี่ยนไปอย่างไร และตรวจจับช่วงผิดปกติได้หรือไม่",
    "q3": "เสรีภาพอินเทอร์เน็ตสัมพันธ์กับภัยจาก AI และข้อมูลบิดเบือนอย่างไร ไทยอยู่ตรงไหน และภัยสากลคล้ายกับที่ไทยเจอหรือไม่",
}
FIXED_NOTE = "ตัวกรองมีผลกับกราฟและตัวเลขหลัก · ข้อค้นพบและการทดสอบทางสถิติใช้ข้อมูลทั้งช่วง ไม่เปลี่ยนตามตัวกรอง"


@st.cache_data(show_spinner="กำลังวิเคราะห์…", max_entries=2)
def analysis(built_at: str) -> qf.QAnalysis:  # built_at only keys the cache
    return qf.run(store.load_tables())


def cards(findings: list[dict], cols: int = 3, start: int = 1) -> None:
    """Short headline cards; long text (detail, caution) only when notes are on."""
    for row in range(0, len(findings), cols):
        cs = st.columns(cols)
        for col, (i, f) in zip(cs, enumerate(findings[row:row + cols], start + row)):
            with col:
                st.markdown(f"<div class='find'><span class='n'>{i}</span>{f['headline']}</div>", unsafe_allow_html=True)
        if ui.notes_on():
            for i, f in enumerate(findings[row:row + cols], start + row):
                st.markdown(f"<div class='read'><b>{i}.</b> {f['detail']}</div>", unsafe_allow_html=True)
                ui.note("ข้อควรระวัง: " + f["caution"])


def _question(key: str) -> None:
    st.markdown(f"<div style='font-size:.95rem;font-weight:600;color:{C['scam']};margin:-.2rem 0 .7rem'>{QUESTIONS[key]}</div>", unsafe_allow_html=True)


def _reset(defaults: dict) -> None:
    for k, v in defaults.items():
        st.session_state[k] = v


# ====================================================================== Q1


def q1(t: Tables, meta: dict) -> None:
    q = analysis(meta["built_at"])
    _question("q1")
    years_all = list(range(2020, int(t["weekly"]["year"].max()) + 1))
    cats_all = list(config.CATEGORY_ORDER)
    verdict_default = ["ข่าวปลอม", "ข่าวบิดเบือน"]
    defaults = {"q1_years": (years_all[0], years_all[-1]), "q1_cats": cats_all, "q1_verdicts": verdict_default}

    with st.container(border=True):
        st.markdown(f"<div class='filterbar'>ตัวกรอง · {FIXED_NOTE}</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2.2, 3.2, 2.6, 1])
        with c1:
            st.select_slider("ช่วงปี", options=years_all, value=defaults["q1_years"], key="q1_years")
        with c2:
            st.multiselect("หมวดข่าวไทย", cats_all, default=defaults["q1_cats"], key="q1_cats")
        with c3:
            st.multiselect("ผลตรวจที่นับในกราฟหมวด", list(ft.VERDICT_EN), default=defaults["q1_verdicts"], key="q1_verdicts")
        with c4:
            st.button("ล้างตัวกรอง", on_click=_reset, args=(defaults,), key="q1_reset")

    lo, hi = st.session_state["q1_years"]
    cats, verdicts = st.session_state["q1_cats"], st.session_state["q1_verdicts"]
    if not cats or not verdicts:
        st.warning("เลือกอย่างน้อย 1 หมวดและ 1 ผลตรวจ")
        return
    m = ft.afnc_filtered(t["afnc_monthly"], lo, hi, cats)
    yearly = ft.verdict_year_table(m)
    share = ft.category_share_selected(m, [ft.VERDICT_EN[v] for v in verdicts])
    eu_y = ft.slice_years(t["eu_yearly"], "year", lo, hi)
    kw = ft.slice_years(t["eu_keywords"], "year", lo, hi)

    c = st.columns(5)
    with c[0]:
        ui.kpi("การหักล้างนานาชาติ (EU)", f"{int(eu_y['debunks'].sum()):,}" if len(eu_y) else "–",
               f'<div class="delta">{"ช่วงที่เลือก" if len(eu_y) else "EU มีข้อมูลถึง " + meta["eu_last_date"][:4]}</div>', C["global"], icon="EU")
    with c[1]:
        ui.kpi("คำตัดสินไทย (AFNC)", f"{int(yearly['afnc_verdicts'].sum()):,}", f'<div class="delta">{lo}–{hi} · {len(cats)} หมวด</div>', C["fake"], icon="TH")
    with c[2]:
        ui.kpi("สัดส่วนข่าวเท็จ", f"{ft.overall_false_share(m):.1f}%", '<div class="delta">ปลอม + บิดเบือน ในช่วง/หมวดที่เลือก</div>', C["fake"], icon="%")
    with c[3]:
        top = share.groupby("category_th")["n"].sum().nlargest(1)
        ui.kpi("หมวดใหญ่สุดของไทย", top.index[0].split("/")[0] if len(top) else "–",
               f'<div class="delta">{int(top.iloc[0]):,} เรื่อง</div>' if len(top) else "", C["scam"], icon="#1")
    with c[4]:
        tk = kw.groupby("keyword")["debunks"].sum().nlargest(1)
        ui.kpi("ประเด็นนำของ EU", tk.index[0] if len(tk) else "–", f'<div class="delta">{int(tk.iloc[0]):,} การหักล้าง</div>' if len(tk) else "", C["global"], icon="#1")

    st.markdown("### ลักษณะของข้อมูลบิดเบือน")
    a, b = st.columns(2)
    with a:
        if len(kw):
            ui.chart(ch.eu_keywords(kw, top=12), "q1_eukw")
        else:
            st.info("ช่วงปีที่เลือกไม่มีข้อมูล EUvsDisinfo (มีถึง ส.ค. 2023)")
    with b:
        label = "+".join(v.replace("ข่าว", "") for v in verdicts)
        ui.chart(cq.category_share_year(share, f"ข่าวไทยที่นับ ({label}) ตามหมวด (% ต่อปี) — ปี 2026 เพิ่มหมวดอาชญากรรมออนไลน์"), "q1_cat")
    ui.read_hint("EU: ประเด็น/เรื่องเล่าที่ถูกหักล้าง (นับต่อเรื่อง) · ไทย: หมวดของข่าว ทั้งสองฝั่งใช้การจัดหมวดคนละระบบ จึงเทียบเชิงเนื้อหา ไม่ใช่จับคู่รายหมวด")

    st.markdown("### สัดส่วนข่าวจริง/ปลอม/บิดเบือน")
    a, b = st.columns(2)
    with a:
        ui.chart(ch.verdict_mix(yearly), "q1_verdict")
    with b:
        if len(eu_y):
            ui.chart(cq.eu_class_mix(eu_y), "q1_euclass")
        else:
            st.info("ช่วงปีที่เลือกไม่มีข้อมูล EUvsDisinfo")
    ui.note("EUvsDisinfo ไม่มีป้ายข่าวจริง/ปลอม/บิดเบือน จึงไม่ควรเทียบสัดส่วนสองกราฟนี้ตรง ๆ", "info")

    st.markdown("### เปลี่ยนแปลงตามเวลา")
    a, b = st.columns(2)
    with a:
        ui.chart(cq.covid_compare(ft.slice_years(q.covid, "year", lo, hi)), "q1_covid")
    with b:
        ui.chart(ch.scam_tag_share(ft.slice_years(q.base.scam_share, "year", lo, hi)), "q1_scamshare")
    a, b = st.columns(2)
    y0, y1 = q.thai_years
    with a:
        ui.chart(cq.topic_change(q.thai_rising, f"หัวข้อข่าวเท็จไทย เพิ่ม/ลดมากสุด ({y0}→{y1}) · ช่วงคงที่", color_up=C["fake"]), "q1_thai_rise")
    with b:
        ui.chart(cq.topic_change(q.eu_rising, f"ประเด็น EU เพิ่ม/ลดมากสุด ({q.eu_years[0]}→{q.eu_years[1]}) · ช่วงคงที่", color_up=C["global"]), "q1_eu_rise")
    ui.chart(ch.residual_heatmap(q.base.mix), "q1_heat")
    st.markdown("### ข้อค้นพบ")
    cards(q.findings["q1"])


# ====================================================================== Q2


def q2(t: Tables, meta: dict) -> None:
    q = analysis(meta["built_at"])
    a_ = q.base
    w = t["weekly"]
    _question("q2")
    d0 = w.loc[w["acsc_reported"], "week_start"].min().to_pydatetime()
    d1 = w["week_start"].max().to_pydatetime()
    defaults = {"q2_range": (d0, d1), "q2_z": 3.5}

    with st.container(border=True):
        st.markdown(f"<div class='filterbar'>ตัวกรอง · {FIXED_NOTE}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([4, 3, 1])
        with c1:
            st.slider("ช่วงสัปดาห์", min_value=d0, max_value=d1, value=defaults["q2_range"], step=timedelta(days=7), format="D MMM YYYY", key="q2_range")
        with c2:
            st.slider("ความไวตรวจความผิดปกติ (robust z)", 2.5, 6.0, value=defaults["q2_z"], step=0.5, key="q2_z", help="ต่ำ = จับง่าย (ผิดปกติเยอะ) · สูง = จับเฉพาะที่รุนแรง")
        with c3:
            st.button("ล้างตัวกรอง", on_click=_reset, args=(defaults,), key="q2_reset")

    lo, hi = st.session_state["q2_range"]
    z_cut = st.session_state["q2_z"]
    w2 = ft.slice_weeks(w, lo, hi)
    u2 = mx.usable_weeks(w2)
    u_full = mx.usable_weeks(w)

    lw = mx.latest_week(w)
    recent, last_year = mx.recent_false_share(w)
    c = st.columns(4)
    with c[0]:
        ui.kpi(f"คดีล่าสุด {_d(lw.week_start)}", ui.fmt_int(lw.cases), ui.delta_html(lw.cases_vs_base, "เทียบ 4 สัปดาห์ก่อน"), icon="#")
    with c[1]:
        ui.kpi("ความเสียหาย", ui.fmt_million(lw.loss_baht) + (" *" if lw.rounded else ""), ui.delta_html(lw.loss_vs_base, "เทียบ 4 สัปดาห์ก่อน"), icon="฿")
    with c[2]:
        if len(u2):
            ui.kpi("ความเสียหายต่อคดี (ช่วงที่เลือก)", f"{u2['acsc_loss_baht'].sum() / u2['acsc_cases'].sum():,.0f} บาท",
                   f'<div class="delta">เฉลี่ย {u2["acsc_cases"].mean():,.0f} คดี/สัปดาห์ · {len(u2)} สัปดาห์</div>', icon="฿/#")
        else:
            ui.kpi("ความเสียหายต่อคดี (ช่วงที่เลือก)", "–", '<div class="delta">ไม่มีสัปดาห์ที่ใช้ได้</div>', icon="฿/#")
    with c[3]:
        ui.kpi("สัดส่วนข่าวเท็จ 4 สัปดาห์ล่าสุด", f"{recent:.1f}%", f'<div class="delta">ปีก่อน {last_year:.1f}%</div>', C["fake"], icon="%")

    st.markdown("### แนวโน้ม")
    if w2["acsc_reported"].sum() >= 2:
        ui.chart(ch.scam_vs_fake(w2), "q2_main")
    else:
        st.info("ช่วงที่เลือกสั้นเกินไป — เลือกอย่างน้อย 2 สัปดาห์ที่มีการแถลง")
    ui.read_hint("แถบเทา = สัปดาห์ที่ไม่มีการแถลง (ไม่ใช่ 0) · แถบเหลือง = ตัวเลขน่าสงสัย ตัดออก · จุดโปร่ง = ความเสียหายที่ปัดเป็นล้านบาท")

    st.markdown("### ความเสียหายเปลี่ยนเพราะอะไร")
    a, b = st.columns([2, 3])
    with a:
        if a_.decomp:
            ui.chart(ch.loss_waterfall(a_.decomp), "q2_wf")
    with b:
        ui.chart(ch.change_point_chart(u_full, a_.cp_cases, a_.cp_lpc), "q2_cp")
    a, b = st.columns(2)
    with a:
        if len(u2) >= 5:
            ui.chart(cq.cases_loss_scatter(u2, cp.cases_loss_relation(w2)), "q2_scatter")
        else:
            st.info("ช่วงที่เลือกมีสัปดาห์ที่ใช้ได้น้อยกว่า 5 สัปดาห์ จึงไม่แสดงความสัมพันธ์")
    with b:
        ui.chart(cq.block_changes(q.blocks), "q2_blocks")
    ui.caption("กราฟแยกส่วน จุดเปลี่ยน และบล็อก 4 สัปดาห์ใช้ข้อมูลทั้งช่วง ไม่ตามตัวกรอง")

    st.markdown("### ความผิดปกติ")
    an_all = cp.weekly_anomalies(w, z_cut=z_cut)
    an = an_all[(an_all["week_start"] >= pd.Timestamp(lo)) & (an_all["week_start"] <= pd.Timestamp(hi))] if len(an_all) else an_all
    a, b = st.columns(2)
    with a:
        ui.chart(cq.anomaly_chart(w2 if len(w2) else w, an, "afnc_false_share_pct", "สัดส่วนข่าวเท็จ (%)", "สัดส่วนข่าวเท็จ (%)"), "q2_an_share")
    with b:
        if len(an):
            tbl = an.assign(สัปดาห์=an["week_start"].dt.strftime("%Y-%m-%d"), ค่า=an["value"].round(1), คาดไว้=an["expected"].round(1), z=an["z"].round(1))
            st.dataframe(tbl[["series", "สัปดาห์", "ค่า", "คาดไว้", "z"]].rename(columns={"series": "ชุดข้อมูล"}), hide_index=True, width="stretch", height=320)
        else:
            st.info(f"ไม่พบสัปดาห์ผิดปกติที่ z > {z_cut} ในช่วงที่เลือก")
    ui.read_hint("เทียบแต่ละสัปดาห์กับมัธยฐานของ 13 สัปดาห์รอบข้าง · สัปดาห์ 16 ส.ค. 2026 ของคดี (79,311) ถูกตัดไว้ก่อนแล้ว จึงไม่อยู่ในตารางนี้")

    st.markdown("### ประเภทภัยและความสัมพันธ์กับข่าวปลอม")
    a, b = st.columns(2)
    with a:
        ui.chart(ch.scam_types(t["acsc_types"]), "q2_types")
    with b:
        ui.chart(ch.lag_chart(a_.lag), "q2_lag")
    st.markdown("### ข้อค้นพบ")
    cards(q.findings["q2"])


# ====================================================================== Q3


def q3(t: Tables, meta: dict) -> None:
    q = analysis(meta["built_at"])
    f = t["fotn"]
    _question("q3")
    years = sorted(int(y) for y in f["data_year"].unique())
    opts = ft.country_options(f)
    asean_names = [n for n, i in opts.items() if i in config.ASEAN]
    yearly = t["aiid_yearly"]
    ai_last = int(yearly["year"].max())
    defaults = {"q3_year": years[-1], "q3_countries": asean_names, "q3_ai": (2015, ai_last)}

    with st.container(border=True):
        st.markdown(f"<div class='filterbar'>ตัวกรอง · {FIXED_NOTE}</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2.2, 3.6, 2.4, 1])
        with c1:
            st.select_slider("ปีข้อมูลเสรีภาพ (แผนที่ คะแนน เพื่อนบ้าน)", options=years, value=defaults["q3_year"], key="q3_year")
        with c2:
            st.multiselect("เปรียบเทียบประเทศ (ไทยแสดงเสมอ)", list(opts), default=defaults["q3_countries"], key="q3_countries")
        with c3:
            st.select_slider("ช่วงปีเหตุการณ์ AI", options=list(range(2010, ai_last + 1)), value=defaults["q3_ai"], key="q3_ai")
        with c4:
            st.button("ล้างตัวกรอง", on_click=_reset, args=(defaults,), key="q3_reset")

    year = int(st.session_state["q3_year"])
    chosen = [opts[n] for n in st.session_state["q3_countries"] if n in opts]
    a_lo, a_hi = st.session_state["q3_ai"]

    th = f[(f["iso3"] == "THA") & (f["data_year"] == year)].iloc[0]
    rank, n = mx.fotn_rank(f, "THA", year)
    asn = ix.asean_standing(f, year)
    yf = ft.slice_years(yearly, "year", a_lo, a_hi)
    s = mx.aiid_summary(yf if len(yf) else yearly, t["aiid_risk"], ai_last)
    c = st.columns(4)
    with c[0]:
        ui.kpi(f"คะแนนไทย ({year})", f"{int(th['total_score'])}/100", f'<div class="delta">{th["status_th"]}</div>', C["freedom"], icon="TH")
    with c[1]:
        ui.kpi("อันดับอาเซียน", f"{asn['rank']} จาก {asn['n']}", f'<div class="delta">โลก {rank} จาก {n}</div>', C["freedom"], icon="#")
    with c[2]:
        ui.kpi(f"เหตุการณ์ AI {a_lo}–{a_hi}", f"{int(yf['incidents'].sum()):,}", f'<div class="delta">deepfake {int(yf["deepfake"].sum()):,} · scam {int(yf["scam"].sum()):,}</div>', C["ai"], icon="AI")
    with c[3]:
        ui.kpi("ซ้อนทับกับไทย", f"{int((q.overlap['status'] == 'ซ้อนทับ').sum())} ธีม", f'<div class="delta">เฝ้าระวัง {int((q.overlap["status"] == "เฝ้าระวัง").sum())} ธีม</div>', C["scam"], icon="∩")

    st.markdown("### ไทยอยู่ตรงไหน")
    a, b = st.columns([3, 2])
    with a:
        ui.chart(cq.fotn_lines(f, chosen), "q3_lines")
    with b:
        ui.chart(ch.fotn_components(th), "q3_comp")
    a, b = st.columns(2)
    with a:
        ui.chart(cq.peers_chart(cp.nearest_peers(f, year)), "q3_peers")
    with b:
        if year - 5 in years:
            ui.chart(ch.fotn_change(mx.fotn_change(f, year - 5, year)), "q3_change")
        else:
            st.info("ไม่มีข้อมูลย้อนหลัง 5 ปีก่อนปีที่เลือก")
    ui.chart(ch.fotn_map(f, year), "q3_map")

    st.markdown("### ภัยจาก AI ระดับสากลกับที่ไทยเจอ")
    a, b = st.columns(2)
    with a:
        if len(yf):
            ui.chart(ch.aiid_yearly(yf, ai_last), "q3_aiid")
    with b:
        ui.chart(cq.theme_overlap_chart(q.overlap), "q3_theme")
    ov = q.overlap.copy()
    ov["AIID %"] = ov["share_pct_AIID"].round(1)
    ov["AFNC %"] = ov["share_pct_AFNC"].round(1)
    ov["เรื่องใน AFNC"] = ov["n_AFNC"].astype(int)
    order = {"ซ้อนทับ": 0, "เฝ้าระวัง": 1, "เด่นในไทย": 2, "น้อยทั้งสองฝั่ง": 3}
    ov = ov.sort_values(["status", "AIID %"], key=lambda s_: s_.map(order) if s_.name == "status" else -s_)
    st.dataframe(ov[["theme", "status", "AIID %", "AFNC %", "เรื่องใน AFNC"]].rename(columns={"theme": "ธีม", "status": "สถานะ"}), hide_index=True, width="stretch")
    ui.read_hint("ซ้อนทับ = พบทั้งสองฝั่ง · เฝ้าระวัง = พบมากใน AIID แต่แทบไม่พบในข้อมูล AFNC (ไม่ได้แปลว่าไม่เกิดในไทย) · ธีมจับจากคำในข้อความ หนึ่งเรื่องมีได้หลายธีม")

    st.markdown("### เสรีภาพกับเหตุการณ์ AI รายประเทศ (สำรวจ)")
    a, b = st.columns([3, 2])
    with a:
        ui.chart(cq.country_scatter(t["aiid_country"], q.country["rho"]), "q3_country")
    with b:
        nf = q.country["not_free"].head(8).copy()
        nf["country"] = nf["country"].str.replace(r" \(.*\)", "", regex=True)
        st.dataframe(nf.rename(columns={"country": "ประเทศ (กลุ่มไม่เสรี)", "mentions": "ถูกกล่าวถึง", "total_score": "คะแนน"}), hide_index=True, width="stretch", height=340)
    ui.caption("กราฟ/ตารางนี้ใช้คะแนนเสรีภาพของปีล่าสุดเสมอ ไม่ตามตัวกรองปี")
    ui.note("ช่องประเทศของ AIID มีเพียง ~8% จึงนับจากชื่อประเทศในข้อความ นี่คือ 'การถูกกล่าวถึง' ไม่ใช่ที่เกิดเหตุ และฐานข้อมูลเน้นข่าวภาษาอังกฤษ ผลนี้จึงใช้เป็นภาพสำรวจเท่านั้น")
    st.markdown("### ข้อค้นพบ")
    cards(q.findings["q3"])


# ====================================================================== details


def details(t: Tables, meta: dict) -> None:
    from dashboard import pages
    names = ["ข่าวปลอมไทย", "คดีหลอกลวง", "AI & Deepfake", "เสรีภาพอินเทอร์เน็ต", "ข้อมูลเท็จระดับโลก"]
    fns = [pages.afnc, pages.scams, pages.ai, pages.freedom, pages.global_disinfo]
    for tab, fn in zip(st.tabs(names), fns):
        with tab:
            fn(t, meta)
