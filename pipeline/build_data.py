"""Python side of the dashboard: reads the processed tables, runs the statistics and forecasts, and writes docs/data.js.

    python -m data_processing.pipeline     # (optional) raw files -> data/processed/
    python -m pipeline.build_data          # processed tables + analyses -> docs/data.js

The browser (docs/index.html + docs/app.js) only filters, aggregates and draws. Everything that needs a model or a
significance test (forecasts, change-point, lag test, anomaly detection, theme overlap) is computed here, once, on the full data.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from analytics import forecast as fc  # noqa: E402
from analytics import gfilters as gf  # noqa: E402
from analytics import qfindings as qf  # noqa: E402
from analytics import stats  # noqa: E402
from dashboard import summary as sm  # noqa: E402
from data_processing import store  # noqa: E402
from pipeline import catalog  # noqa: E402

OUT = ROOT / "docs" / "data.js"


def clean(o):
    """JSON-safe copy: numpy -> python, NaN/inf -> None, Timestamp -> ISO date."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, pd.DataFrame):
        return clean(o.to_dict("records"))
    if isinstance(o, pd.Series):
        return clean(o.tolist())
    if isinstance(o, (pd.Timestamp, np.datetime64)):
        return None if pd.isna(o) else pd.Timestamp(o).strftime("%Y-%m-%d")
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if (math.isnan(o) or math.isinf(o)) else float(o)
    if o is pd.NaT:
        return None
    return o


def _idx(values: pd.Series, vocab: list) -> list[int]:
    m = {v: i for i, v in enumerate(vocab)}
    return [m.get(v, -1) for v in values]


def afnc_block(t) -> dict:
    a = t["afnc_clean"]
    status = gf.status_of(a)
    itypes = sorted(a["item_type"].unique())
    agencies = sorted(a["checked_by_agency"].dropna().unique())
    return {
        "itypes": itypes, "statuses": gf.STATUS_LABELS, "cats": list(config.CATEGORY_ORDER), "agencies": agencies,
        "d": a["date"].dt.strftime("%Y-%m-%d").tolist(), "it": _idx(a["item_type"], itypes), "st": _idx(status, gf.STATUS_LABELS),
        "c": _idx(a["category_th"], list(config.CATEGORY_ORDER)), "ag": _idx(a["checked_by_agency"], agencies),
        "tg": a["tags_clean"].fillna("").tolist(), "id": a["post_id"].astype(int).tolist(),
    }


def weekly_block(t) -> list[dict]:
    w = t["weekly"]
    cols = {
        "ws": w["week_start"].dt.strftime("%Y-%m-%d"), "cases": w["acsc_cases"], "loss": w["acsc_loss_baht"], "rep": w["acsc_reported"],
        "use": w["acsc_usable"], "sus": w["acsc_suspect"], "rnd": w["acsc_rounded"], "tt": w["top_type_group"], "hl": w["highest_loss_group"],
        "hla": w["acsc_highest_loss_type_loss_baht"], "fake": w["afnc_fake"], "dist": w["afnc_distorted"], "true": w["afnc_true"],
        "vd": w["afnc_verdicts"], "url": w["acsc_source_url"], "flag": w["acsc_flag"],
    }
    return clean(pd.DataFrame(cols).to_dict("records"))


def eu_block(t, top_kw: int = 60) -> dict:
    d = t["eu_debunks"].dropna(subset=["debunk_date"]).copy()
    kws = d["keywords"].fillna("").map(lambda s: [k.strip() for k in s.split(",") if k.strip()])
    vocab = pd.Series([k for ks in kws for k in set(ks)]).value_counts().head(top_kw).index.tolist()
    m = {k: i for i, k in enumerate(vocab)}
    return {"kw": vocab, "d": d["debunk_date"].dt.strftime("%Y-%m-%d").tolist(), "k": [[m[k] for k in ks if k in m] for ks in kws],
            "n": d["articles"].astype(int).tolist(), "nd": d["disinformation_articles"].astype(int).tolist(), "nt": d["trustworthy_articles"].astype(int).tolist()}


def aiid_block(t) -> dict:
    a = t["aiid_clean"]
    risk = sorted(a["Risk Domain"].dropna().unique())
    intent = sorted(a["Intent"].dropna().unique())
    return {"risk": risk, "intent": intent,
            "rows": [[int(r["Incident ID"]), r["date"].strftime("%Y-%m-%d") if pd.notna(r["date"]) else None, str(r["title"])[:150],
                      risk.index(r["Risk Domain"]) if pd.notna(r["Risk Domain"]) else -1, intent.index(r["Intent"]) if pd.notna(r["Intent"]) else -1,
                      int(r["is_deepfake"]), int(r["is_scam"]), int(r["is_thai"]), int(r["report_count"])] for _, r in a.iterrows()]}


def fotn_block(t) -> list[dict]:
    f = t["fotn"]
    out = pd.DataFrame({"country": f["country"].str.replace(r" \(.*\)", "", regex=True), "iso3": f["iso3"], "y": f["data_year"], "total": f["total_score"],
                        "acc": f["obstacles_to_access"], "con": f["limits_on_content"], "rig": f["violations_of_user_rights"], "st": f["status_code"],
                        "asean": f["iso3"].isin(config.ASEAN)})
    return clean(out.to_dict("records"))


def forecasts(t) -> dict:
    a = t["afnc_clean"]
    v = a[(a["item_type"] == "Verdict") & (a["date"] >= "2020-01-01")]
    m = v.groupby(v["date"].dt.to_period("M").dt.to_timestamp())["is_false"].sum().astype(float)
    m.index.freq = "MS"
    out = {}
    r1 = fc.forecast_series(m, horizon=6, min_obs=36, freq="MS")
    out["fake_monthly"] = pack(r1, "จำนวนข่าวเท็จ (ปลอม + บิดเบือน) รายเดือน", "เรื่อง/เดือน", "รายเดือน",
                               "จำนวนคำตัดสินของศูนย์ฯ เป็นโควตาการทำงาน (~49/สัปดาห์) จึงสะท้อนการทำงานของศูนย์ฯ ไม่ใช่ปริมาณข่าวปลอมในสังคม")
    w = t["weekly"]
    u = w[w["acsc_usable"]].set_index("week_start")["acsc_loss_baht"] / 1e6
    full = u.reindex(pd.date_range(u.index.min(), u.index.max(), freq="7D"))
    gaps = int(full.isna().sum())
    r2 = fc.forecast_series(full.interpolate(), horizon=4, min_obs=40, freq="7D")
    out["scam_weekly"] = pack(r2, "ความเสียหายจากมิจฉาชีพรายสัปดาห์", "ล้านบาท/สัปดาห์", "รายสัปดาห์",
                              f"ข้อมูล {len(u)} สัปดาห์ที่ใช้ได้ มี {gaps} สัปดาห์ที่ไม่มีตัวเลข/ถูกตัดออก จึงเติมด้วยการประมาณเชิงเส้นเพื่อใช้ฟิตแบบจำลองเท่านั้น (ไม่แสดงเป็นข้อมูลจริง) "
                              "และข้อมูลมีจุดเปลี่ยนช่วง เม.ย. 2026 จึงไม่เหมาะกับการพยากรณ์ไกล")
    out["scam_weekly"]["interpolated"] = [d.strftime("%Y-%m-%d") for d in full.index[full.isna()]]
    return out


def pack(r: fc.ForecastResult, title: str, unit: str, freq_th: str, caveat: str) -> dict:
    d = {"ok": r.ok, "reason": r.reason, "title": title, "unit": unit, "freq": freq_th, "caveat": caveat, "n_obs": int(len(r.history))}
    if r.history is not None and len(r.history):
        d["history"] = {"d": [x.strftime("%Y-%m-%d") for x in r.history.index], "v": [round(float(x), 3) for x in r.history.values]}
    if r.ok:
        d.update(model=r.model, horizon=r.horizon, metrics=clean(r.metrics), backtest=clean(r.backtest), forecast=clean(r.forecast))
    return d


def correlation_checks(t, qa: qf.QAnalysis) -> dict:
    """Reference values (scipy) so the JavaScript implementation can be tested against them."""
    w = t["weekly"]
    u = w[w["acsc_usable"]]
    ref = {}
    for name, x, y, method in [("cases_loss_pearson", "acsc_cases", "acsc_loss_baht", "pearson"), ("cases_loss_spearman", "acsc_cases", "acsc_loss_baht", "spearman"),
                               ("false_share_cases_spearman", "afnc_false_share_pct", "acsc_cases", "spearman")]:
        r = stats.correlate(u[x], u[y], method)
        ref[name] = {"n": r["n"], "r": r["r"], "p": r["p"], "x": x, "y": y, "method": method}
    c = t["aiid_country"]
    d = c[c["mentions"] >= 5]
    r = stats.correlate(d["total_score"], d["mentions"], "spearman")
    ref["freedom_mentions_spearman"] = {"n": r["n"], "r": r["r"], "p": r["p"]}
    return ref


def inventory(t, meta) -> list[dict]:
    """One row per source dataset: size, period, missing share and what could be checked."""
    a, w, f = t["afnc_clean"], t["weekly"], t["fotn"]
    eu, ai = t["eu_debunks"], t["aiid_clean"]
    v = t["validation"].set_index("check")["detail"].to_dict()
    def miss(df, cols):
        return float(df[cols].isna().mean().mean() * 100)
    return [
        {"dataset": "AFNC (ข่าวปลอมไทย)", "files": "afnc_items.csv", "rows": len(a), "cols": 15, "from": a["date"].min(), "to": a["date"].max(),
         "grain": "โพสต์", "missing_pct": miss(a, ["checked_by_agency", "verdict_en"]), "note": "ซ้ำ 0 แถว (post_id) · ว่างหน่วยงาน 20.5% · ไม่ใช่คำตัดสิน 3,268 โพสต์"},
        {"dataset": "ACSC (คดีหลอกลวง)", "files": "acsc_weekly.csv, weekly_panel.csv", "rows": int(w["acsc_reported"].sum()), "cols": 18, "from": w.loc[w["acsc_reported"], "week_start"].min(),
         "to": w.loc[w["acsc_reported"], "week_start"].max(), "grain": "สัปดาห์", "missing_pct": miss(w[w["acsc_reported"]], ["acsc_highest_loss_type_loss_baht", "acsc_top_type_case_share_pct"]),
         "note": "สัปดาห์ไม่มีตัวเลข 3 · ตัวเลขน่าสงสัย 1 · ปัดล้านบาท 11"},
        {"dataset": "EUvsDisinfo", "files": "euvsdisinfo_base.csv", "rows": meta["n_eu_debunks"], "cols": 9, "from": eu["debunk_date"].min(), "to": eu["debunk_date"].max(),
         "grain": "การหักล้าง (ยุบจาก 18,249 บทความ)", "missing_pct": miss(eu, ["keywords"]), "note": "ปี 2023 มีข้อมูลถึง ส.ค. · ไม่มีเนื้อหาบทความ"},
        {"dataset": "AI Incident Database", "files": "AIID_Excel_Export-20261026.xlsx (+12 ฉบับรายสัปดาห์)", "rows": len(ai), "cols": 59, "from": ai["date"].min(), "to": ai["date"].max(),
         "grain": "เหตุการณ์", "missing_pct": miss(ai, ["Risk Domain", "Intent"]), "note": "ไม่จัดหมวดความเสี่ยง 15.7% · ช่องประเทศมี ~8%"},
        {"dataset": "Freedom on the Net", "files": "freedom_on_the_net_scores.csv", "rows": len(f), "cols": 12, "from": f"{int(f['data_year'].min())}-01-01", "to": f"{int(f['data_year'].max())}-12-31",
         "grain": "ประเทศ-ปี", "missing_pct": miss(f, ["total_score"]), "note": "จำนวนประเทศต่อปี 37 → 71 · ปีข้อมูลต่างจากปีรายงาน 1 ปี"},
    ]


def linkage() -> list[dict]:
    return [
        {"pair": "AFNC ↔ ACSC", "ok": True, "how": "สัปดาห์ (อาทิตย์–เสาร์) ตรงกัน 48 สัปดาห์ (9 พ.ย. 2025 – 24 ต.ค. 2026)", "limit": "ฝั่งคดีมีเพียง 47 สัปดาห์ที่ใช้ได้"},
        {"pair": "AFNC ↔ Freedom on the Net", "ok": False, "how": "ซ้อนกันเป็นรายปี 2019–2024 (ข้อมูลเสรีภาพเฉพาะประเทศไทยคือ 1 จุดต่อปี)", "limit": "มีไม่เกิน 6 คู่ต่อปี และ AFNC มีเฉพาะประเทศไทย จึงเทียบรายประเทศไม่ได้ — ระบบไม่คำนวณสหสัมพันธ์ (ต้องการ ≥ 10 คู่)"},
        {"pair": "ACSC ↔ Freedom on the Net", "ok": False, "how": "ไม่มีปีที่ซ้อนกัน (ACSC เริ่ม พ.ย. 2025, Freedom on the Net สิ้นสุดปีข้อมูล 2024)", "limit": "ไม่มีข้อมูลเพียงพอสำหรับการวิเคราะห์นี้"},
        {"pair": "EUvsDisinfo ↔ AFNC", "ok": True, "how": "เทียบแนวโน้มรายปีปี 2019–2023 (เช่น โควิด)", "limit": "จัดหมวดคนละระบบ EU ไม่มีป้ายปลอม/จริง และเก็บเฉพาะฝั่งสนับสนุนรัสเซีย"},
        {"pair": "AIID ↔ Freedom on the Net", "ok": True, "how": "จับคู่ด้วยชื่อประเทศในข้อความ (24 ประเทศที่ถูกกล่าวถึง ≥ 5 ครั้ง)", "limit": "เป็นการ 'ถูกกล่าวถึง' ไม่ใช่ที่เกิดเหตุ — ใช้เชิงสำรวจเท่านั้น"},
    ]


def date_min(t) -> str:
    """Earliest date in any dataset, so the default 'all' window silently drops nothing."""
    cands = [t["afnc_clean"]["date"].min(), t["eu_debunks"]["debunk_date"].min(), t["aiid_clean"]["date"].min(), pd.Timestamp(int(t["fotn"]["data_year"].min()), 1, 1)]
    return min(c for c in cands if pd.notna(c)).strftime("%Y-%m-%d")


def build() -> dict:
    t = store.load_tables()
    meta = store.load_meta()
    qa = qf.run(t)
    b = qa.base
    rows = lambda df: clean(df)  # noqa: E731
    country = qa.country
    d = t["aiid_country"]
    dd = d[d["mentions"] >= 5]
    cl = stats.correlate(dd["total_score"], dd["mentions"], "spearman")
    analysis = {
        "findings": qa.findings,
        "decomp": clean(b.decomp.__dict__) if b.decomp else None,
        "cp_cases": clean(b.cp_cases.__dict__) if b.cp_cases else None, "cp_lpc": clean(b.cp_lpc.__dict__) if b.cp_lpc else None,
        "lag": rows(b.lag), "detrended": clean(b.detrended), "outliers": rows(b.outliers[b.outliers["flagged"]]),
        "anomalies": rows(qa.anomalies), "spikes": rows(qa.spikes), "blocks": rows(qa.blocks), "relation": clean(qa.relation),
        "loss_types": rows(qa.loss_types), "overlap": rows(qa.overlap), "peers": rows(qa.peers),
        "thai_rising": rows(qa.thai_rising), "eu_rising": rows(qa.eu_rising), "thai_years": list(qa.thai_years), "eu_years": list(qa.eu_years),
        "covid": rows(qa.covid), "scam_share": rows(b.scam_share), "false_trend": clean(b.false_trend), "mix": {"chi2": b.mix.chi2, "dof": b.mix.dof, "v": b.mix.cramers_v,
                                                                                                         "residuals": clean(b.mix.residuals.reset_index().to_dict("records"))},
        "country": {"rho": cl["r"], "p": cl["p"], "n": cl["n"], "rows": rows(t["aiid_country"]), "not_free": rows(country["not_free"].head(10))},
        "theme_year": rows(t["theme_year"]), "aiid_growth": rows(t["aiid_growth"]), "eu_languages": rows(t["eu_languages"]), "eu_domains": rows(t["eu_domains"]),
        "asean": {"rank": b.asean["rank"], "n": b.asean["n"], "median_others": b.asean["median_others"], "weakest": list(b.asean["weakest_component"])},
    }
    data = {
        "meta": {**meta, "asean": config.ASEAN, "date_min": date_min(t), "date_max": meta["afnc_last_date"], "groups": gf.GROUPS, "status_labels": gf.STATUS_LABELS,
                 "damage_groups": sorted(t["weekly"]["highest_loss_group"].dropna().unique().tolist()), "sources": gf.SOURCES},
        "afnc": afnc_block(t), "weekly": weekly_block(t), "eu": eu_block(t), "aiid": aiid_block(t), "fotn": fotn_block(t),
        "analysis": analysis, "forecast": forecasts(t), "corr_ref": correlation_checks(t, qa),
        "summary_md": "",
        "validation": rows(t["validation"]), "cleaning": rows(t["cleaning_log"].fillna("")),
        "dictionary": catalog.DICTIONARY, "source_map": catalog.SOURCE_MAP, "inventory": rows(pd.DataFrame(inventory(t, meta))), "linkage": linkage(),
    }
    data["summary_md"] = sm.build_summary_markdown(t, meta, qa, data["forecast"], data["linkage"])
    return clean(data)


def main() -> None:
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = "window.DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + ";\n"
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  {len(text) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
