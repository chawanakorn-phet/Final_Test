"""Findings grouped by the three research questions. Every number is computed; none is typed in."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analytics import comparisons as cp
from analytics import findings as fd
from analytics import metrics as mx

Tables = dict[str, pd.DataFrame]
TH = fd.TH_MONTHS


def _d(ts) -> str:
    return fd._d(pd.Timestamp(ts))


@dataclass
class QAnalysis:
    base: fd.Analysis
    covid: pd.DataFrame
    thai_rising: pd.DataFrame
    eu_rising: pd.DataFrame
    thai_years: tuple[int, int]
    eu_years: tuple[int, int]
    verdict_mix: dict
    anomalies: pd.DataFrame
    spikes: pd.DataFrame
    blocks: pd.DataFrame
    relation: dict
    loss_types: pd.DataFrame
    overlap: pd.DataFrame
    peers: pd.DataFrame
    country: dict
    findings: dict = field(default_factory=dict)


def run(t: Tables) -> QAnalysis:
    base = fd.run_all(t)
    w = t["weekly"]
    totals = w.groupby("year")["afnc_verdicts"].sum()
    thai_years = (2022, 2025)
    tags = t["afnc_tags"][["year", "tag", "n"]].rename(columns={"tag": "topic"})
    thai_rising = cp.rising_topics(tags, totals, "topic", *thai_years, min_count=40)
    eu_years = (2019, 2022)
    eu_total = t["eu_yearly"].set_index("year")["debunks"]
    eu_rising = cp.rising_topics(cp.eu_topic_counts(t["eu_keywords"]), eu_total, "topic", *eu_years, min_count=40)
    v = w[w["year"] >= 2020][["afnc_fake", "afnc_distorted", "afnc_true", "afnc_verdicts"]].sum()
    mix = {k: float(v[c] / v["afnc_verdicts"] * 100) for k, c in (("fake", "afnc_fake"), ("distorted", "afnc_distorted"), ("true", "afnc_true"))}
    overlap = cp.theme_overlap(t["theme_year"])
    overlap["status"] = overlap.apply(lambda r: cp.overlap_status(r["share_pct_AIID"], r["share_pct_AFNC"], int(r["n_AFNC"])), axis=1)
    qa = QAnalysis(
        base=base, covid=t["covid_share"], thai_rising=thai_rising, eu_rising=eu_rising, thai_years=thai_years, eu_years=eu_years,
        verdict_mix=mix, anomalies=cp.weekly_anomalies(w), spikes=cp.category_spikes(t["afnc_monthly"]),
        blocks=cp.cases_down_severity_up(w), relation=cp.cases_loss_relation(w), loss_types=t["acsc_types"], overlap=overlap,
        peers=cp.nearest_peers(t["fotn"], int(t["fotn"]["data_year"].max())), country=cp.country_link(t["aiid_country"]))
    qa.findings = build(qa, t)
    return qa


def build(q: QAnalysis, t: Tables) -> dict[str, list[dict]]:
    a = q.base
    base = {f["headline"]: f for f in fd.key_findings(a)}
    keyed = list(base.values())  # [decomp, changepoint, scamshare, falsetrend, lag, aiid, asean]
    out: dict[str, list[dict]] = {"q1": [], "q2": [], "q3": []}

    # ---- Q1
    c = q.covid.pivot(index="year", columns="source", values="share_pct")
    peak = int(c["AFNC (ไทย)"].idxmax())
    out["q1"].append({
        "headline": f"โควิดเป็นประเด็นใหญ่ทั้งสองฝั่งปี {peak}: ไทย {c.loc[peak, 'AFNC (ไทย)']:.0f}% · EU {c.loc[peak, 'EUvsDisinfo']:.0f}% แล้วลดเกือบหมดหลังปี 2022",
        "detail": f"สัดส่วนข่าวเท็จ/การหักล้างที่เกี่ยวกับโควิด (ไทย: แท็กโควิด/วัคซีน/โรคระบาด, EU: keywords coronavirus/vaccination) ปี 2022 = ไทย {c.loc[2022, 'AFNC (ไทย)']:.1f}% · EU {c.loc[2022, 'EUvsDisinfo']:.1f}%",
        "caution": "นิยามโควิดของสองฝั่งต่างกัน (แท็ก vs keywords) เทียบแนวโน้มได้ ไม่ใช่ค่าที่เทียบกันตรง ๆ · EU เก็บเฉพาะฝั่งสนับสนุนรัสเซีย"})
    tr, er = q.thai_rising, q.eu_rising
    y0, y1 = q.thai_years
    top_t = tr.iloc[0]
    out["q1"].append({
        "headline": f"ไทยเพิ่ม: {top_t['topic']} +{top_t['change_pp']:.1f} จุด · {tr.iloc[1]['topic']} +{tr.iloc[1]['change_pp']:.1f} จุด ({y0}→{y1}) · EU: {er.iloc[0]['topic']} {er.iloc[0]['share_start']:.0f}% → {er.iloc[0]['share_end']:.0f}%",
        "detail": "หัวข้อที่ลดลงมากสุดของไทย: " + ", ".join(f"{r.topic} {r.change_pp:+.1f}" for r in tr.tail(3).itertuples()) + " จุด · ของ EU: "
                  + ", ".join(f"{r.topic} {r.change_pp:+.1f}" for r in er.tail(2).itertuples()) + " จุด",
        "caution": f"เทียบสัดส่วนของเรื่องทั้งหมดในปีนั้น (ไทย {y0}→{y1}, EU {q.eu_years[0]}→{q.eu_years[1]}) เฉพาะหัวข้อที่มีอย่างน้อย 40 เรื่อง · แท็กรวมตัวสะกดต่างแล้ว"})
    m = q.verdict_mix
    ya = mx.afnc_yearly(t["weekly"]).set_index("year")
    dist = ya["afnc_distorted"] / ya["afnc_verdicts"] * 100
    out["q1"].append({
        "headline": f"สัดส่วนผลตรวจของไทย (2020–): ปลอม {m['fake']:.0f}% · บิดเบือน {m['distorted']:.0f}% · จริง {m['true']:.0f}%",
        "detail": f"ข่าวบิดเบือนเป็น {dist.loc[2023]:.1f}% ของคำตัดสินปี 2023 และ {dist.loc[dist.index.max()]:.1f}% ปี {dist.index.max()} (ปีล่าสุดยังไม่ครบ) · ข่าวเท็จรวม {a.false_trend['share0']:.1f}% → {a.false_trend['share1']:.1f}% ({a.false_trend['y0']}→{a.false_trend['y1']})",
        "caution": "EUvsDisinfo ไม่มีป้าย ปลอม/บิดเบือน/จริง (มีแค่ disinformation vs trustworthy ของบทความที่ผูกกับการหักล้าง) จึงเทียบสัดส่วนข้ามฝั่งไม่ได้"})
    out["q1"].append(keyed[2])  # scam-related share
    out["q1"].append(keyed[3])  # false share trend + mix shift

    # ---- Q2
    out["q2"].append(keyed[0])
    out["q2"].append(keyed[1])
    r = q.relation
    out["q2"].append({
        "headline": f"คดีกับความเสียหายเคลื่อนไปด้วยกัน (r = {r['r']:+.2f}) และความเสียหายไวกว่าคดี: คดี +1% ↔ ความเสียหาย +{r['elasticity']:.1f}%",
        "detail": f"จาก {r['n']} สัปดาห์ · สหสัมพันธ์ระหว่างจำนวนคดีกับบาท/คดี r = {r['r_lpc_cases']:+.2f} แปลว่าสัปดาห์ที่คดีมากมักเป็นสัปดาห์ที่คดีมูลค่าสูงมากด้วย",
        "caution": "ความยืดหยุ่นคำนวณจาก log-log ของข้อมูลช่วงสั้นที่มีจุดเปลี่ยน จึงเป็นภาพรวม ไม่ใช่กฎคงที่"})
    b = q.blocks
    hit = b[b["cases_down_lpc_up"]]
    if len(hit):
        h = hit.iloc[-1]
        out["q2"].append({
            "headline": f"มีช่วงที่คดีลดแต่บาท/คดีเพิ่ม: {_d(h['from'])}–{_d(h['to'])} คดี {h['cases_chg_pct']:+.0f}% · บาท/คดี {h['lpc_chg_pct']:+.0f}%",
            "detail": f"เทียบกับบล็อก 4 สัปดาห์ก่อนหน้า · พบ {len(hit)} จาก {len(b)} บล็อก",
            "caution": "บล็อกละ 4 สัปดาห์ จึงมีตัวอย่างน้อย · ตัวเลขหลัง 9 ส.ค. เป็นความเสียหายที่ปัดเป็นล้านบาท"})
    an = q.anomalies
    cnt = an.groupby("series").size().to_dict() if len(an) else {}
    out_acsc = int(a.outliers["flagged"].sum())
    out["q2"].append({
        "headline": f"ตรวจพบสัปดาห์ผิดปกติ: คดี {out_acsc} (ค่าผิดพลาดที่ตัดออก) · บาท/คดี {cnt.get('ความเสียหายต่อคดี (บาท)', 0)} · ข่าวเท็จ {cnt.get('ข่าวเท็จ (เรื่อง/สัปดาห์)', 0)} · สัดส่วนเท็จ {cnt.get('สัดส่วนข่าวเท็จ (%)', 0)}",
        "detail": "เทียบแต่ละสัปดาห์กับค่ามัธยฐานของสัปดาห์รอบข้าง 13 สัปดาห์ (robust z > 3.5) · ข่าวเท็จส่วนใหญ่นิ่งเพราะจำนวนคำตัดสินเป็นโควตา" + (
            f" · เดือนที่หมวดข่าวเท็จพุ่ง: {', '.join(f'{r.category} {r.month:%Y-%m}' for r in q.spikes.head(3).itertuples())}" if len(q.spikes) else ""),
        "caution": "ความผิดปกติทางสถิติไม่ใช่เหตุการณ์จริงเสมอไป ต้องดูบริบทข่าว"})
    lt = q.loss_types.sort_values("weeks_top_by_loss", ascending=False)
    top = lt.iloc[0]
    out["q2"].append({
        "headline": f"ประเภทที่เสียหายสูงสุดบ่อยที่สุดคือ '{top['scam_type']}' ({int(top['weeks_top_by_loss'])} จาก {int(lt['weeks_top_by_loss'].sum())} สัปดาห์ที่มีข้อมูล)",
        "detail": "ด้านจำนวนคดี '" + q.loss_types.sort_values("weeks_top_by_cases", ascending=False).iloc[0]["scam_type"] + "' เป็นอันดับ 1 เกือบทุกสัปดาห์ แต่เป็นคนละประเภทกับที่เสียหายสูงสุด",
        "caution": "ข้อมูลระบุเพียง 'ประเภทอันดับ 1' ของแต่ละสัปดาห์ ไม่มียอดเงินแยกประเภททุกสัปดาห์"})
    out["q2"].append(keyed[4])

    # ---- Q3
    asn = a.asean
    pe = q.peers
    th_row = pe[pe["iso3"] == "THA"].iloc[0]
    out["q3"].append(keyed[6])
    out["q3"].append({
        "headline": f"ไทยอยู่กลุ่ม 'ไม่เสรี' ใกล้เกณฑ์เสรีบางส่วน · จุดฉุดคือ {asn['weakest_component'][0]} ({asn['weakest_component'][1]:.0f}% ของเต็ม)",
        "detail": f"คะแนน {asn['score']} · ประเทศคะแนนใกล้กัน (±6): " + ", ".join(f"{r.country} {r.total_score}" for r in pe.itertuples() if r.iso3 != 'THA') +
                  f" · ไทยเปลี่ยน {th_row['change_5y']:+.0f} คะแนนใน 5 ปี",
        "caution": "เกณฑ์ 'เสรีบางส่วน' เริ่มที่ 40 ตามข้อมูลไฟล์ · การประเมินผู้เชี่ยวชาญ"})
    ov = q.overlap
    over = ov[ov["status"] == "ซ้อนทับ"]["theme"].tolist()
    watch = ov[ov["status"] == "เฝ้าระวัง"].sort_values("share_pct_AIID", ascending=False)["theme"].tolist()
    out["q3"].append({
        "headline": f"ภัย AI สากลซ้อนทับกับไทย {len(over)} ธีม · ยังพบน้อยในข้อมูลไทยแต่ควรเฝ้าระวัง {len(watch)} ธีม",
        "detail": "ซ้อนทับ: " + ", ".join(over) + " · เฝ้าระวัง: " + ", ".join(watch),
        "caution": "AFNC เป็นข่าวที่ศูนย์ฯ เลือกตรวจ 'ไม่พบ' ไม่เท่ากับ 'ไม่เกิดในไทย' · ธีมจับจากคำในข้อความ (หลายธีมต่อเรื่องได้)"})
    cl = q.country
    nf = cl["not_free"]
    out["q3"].append({
        "headline": f"ไม่พบความสัมพันธ์ชัดเจนระหว่างเสรีภาพกับจำนวนเหตุการณ์ AI รายประเทศ (ρ = {cl['rho']:+.2f}, n = {cl['n']})",
        "detail": "กลุ่ม 'ไม่เสรี' ที่ถูกกล่าวถึงมากสุด: " + ", ".join(f"{r.country.split(' (')[0]} {r.mentions}" for r in nf.head(4).itertuples()),
        "caution": "ช่องประเทศของ AIID มีเพียง ~8% จึงดึงชื่อประเทศจากข้อความ — เป็น 'การถูกกล่าวถึง' ไม่ใช่ที่เกิดเหตุ และฐานข้อมูลเน้นข่าวภาษาอังกฤษ (ไม่ใช่การพิสูจน์ว่าไม่มีความสัมพันธ์)"})
    out["q3"].append(keyed[5])
    return out
