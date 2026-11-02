"""Global filters: each filter changes exactly what it should, and out-of-scope datasets stay out."""
import pandas as pd

from analytics import gfilters as gf


def _sel(**kw):
    return gf.update(gf.default_selection("2020-01-01", "2026-12-31"), **kw)


def _afnc():
    return pd.DataFrame({
        "date": pd.to_datetime(["2020-02-10", "2021-05-03", "2021-08-20", "2022-11-30", "2022-12-01"]),
        "item_type": ["Verdict", "Verdict", "Knowledge article", "Verdict", "Verdict"],
        "verdict_en": ["Fake", "True", None, "Distorted", "Fake"],
        "category_th": ["สุขภาพ", "การเงิน", "สุขภาพ", "การเงิน", "สุขภาพ"],
    })


def test_time_filters_combine():
    a = _afnc()
    assert len(gf.afnc(a, _sel())) == 5
    assert len(gf.afnc(a, _sel(years=(2021,)))) == 2
    assert len(gf.afnc(a, _sel(quarters=(4,)))) == 2                 # Nov 30 and Dec 1
    assert len(gf.afnc(a, _sel(months=(12,)))) == 1
    assert len(gf.afnc(a, _sel(date_from=pd.Timestamp("2021-06-01"), date_to=pd.Timestamp("2022-11-30")))) == 2


def test_status_filter_counts_non_verdicts_as_other():
    a = _afnc()
    assert list(gf.status_of(a)) == ["ข่าวปลอม", "ข่าวจริง", "อื่น ๆ (ไม่ใช่คำตัดสิน)", "ข่าวบิดเบือน", "ข่าวปลอม"]
    assert len(gf.afnc(a, _sel(statuses=("อื่น ๆ (ไม่ใช่คำตัดสิน)",)))) == 1
    assert len(gf.afnc(a, _sel(statuses=("ข่าวปลอม", "ข่าวบิดเบือน"), cats=("การเงิน",)))) == 1


def test_region_scopes_datasets():
    a = _afnc()
    assert gf.afnc(a, _sel(region="foreign")).empty and "ประเทศไทยเท่านั้น" in gf.why_not("afnc", _sel(region="foreign"))
    deb = pd.DataFrame({"debunk_date": pd.to_datetime(["2021-01-01"]), "keywords": ["x"]})
    assert gf.eu(deb, _sel(region="th")).empty and "ต่างประเทศ" in gf.why_not("eu", _sel(region="th"))
    assert len(gf.eu(deb, _sel(region="foreign"))) == 1
    inc = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-02-01"]), "is_thai": [True, False]})
    assert len(gf.aiid(inc, _sel(region="th"))) == 1 and len(gf.aiid(inc, _sel(region="foreign"))) == 1 and len(gf.aiid(inc, _sel())) == 2


def test_sources_switch_datasets_off_with_reason():
    s = _sel(sources=("EUvsDisinfo",))
    assert gf.afnc(_afnc(), s).empty and "ไม่ได้เลือกแหล่งข้อมูล" in gf.why_not("afnc", s) and gf.why_not("eu", s) == ""


def _fotn():
    rows = []
    for iso, st in [("THA", 3), ("SGP", 2), ("ISL", 1), ("MMR", 3)]:
        for y in (2023, 2024):
            rows.append({"iso3": iso, "data_year": y, "status_code": st, "total_score": 50})
    return pd.DataFrame(rows)


def test_fotn_region_group_countries_and_month_not_applied():
    f = _fotn()
    assert set(gf.fotn(f, _sel(region="th"))["iso3"]) == {"THA"}
    assert "THA" not in set(gf.fotn(f, _sel(region="foreign"))["iso3"])
    assert set(gf.fotn(f, _sel(group="ไม่เสรี"))["iso3"]) == {"THA", "MMR"}
    assert set(gf.fotn(f, _sel(countries=("ISL",)))["iso3"]) == {"ISL", "THA"}           # Thailand stays as the reference
    assert set(gf.fotn(f, _sel(region="foreign", group="อาเซียน"), asean={"SGP", "THA"})["iso3"]) == {"SGP"}
    assert len(gf.fotn(f, _sel(months=(3,)))) == len(f)                                   # months do not apply to annual data
    assert gf.fotn(f, _sel(date_from=pd.Timestamp("2024-01-01")))["data_year"].unique().tolist() == [2024]


def test_weekly_damage_filter_and_chips_reset():
    w = pd.DataFrame({"week_start": pd.to_datetime(["2026-01-04", "2026-01-11", "2026-01-18"]), "highest_loss_group": ["หลอกลงทุน", "แอบอ้างบุคคลอื่น", None]})
    assert len(gf.weekly(w, _sel(damage=("หลอกลงทุน",)))) == 1
    s = _sel(years=(2026,), region="th", cats=("การเงิน",))
    c = gf.chips(s)
    assert any("ปี 2026" in x for x in c) and "ประเทศไทย" in c and gf.chips(gf.reset(s)) == []
    assert any("AFNC เท่านั้น" in n for n in gf.notes(s))
