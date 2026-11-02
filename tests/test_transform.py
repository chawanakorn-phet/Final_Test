"""Unit tests on small hand-made frames (never the real data)."""
import numpy as np
import pandas as pd

from analytics import metrics as mx
from data_processing import transform as tf


def _panel():
    return pd.DataFrame({
        "week_start": pd.to_datetime(["2026-01-04", "2026-01-11", "2026-01-18", "2026-01-25"]),
        "week_end": pd.to_datetime(["2026-01-10", "2026-01-17", "2026-01-24", "2026-01-31"]),
        "year": 2026, "afnc_verdicts": [10, 10, 10, 0], "afnc_fake": [5, 6, 4, 0], "afnc_distorted": [2, 1, 1, 0],
        "afnc_true": [3, 3, 5, 0], "acsc_reported": [True, True, True, False],
        "acsc_cases": [100.0, 1300.0, 120.0, np.nan], "acsc_loss_baht": [1e6, 1.3e7, 1.2e6, np.nan],
        "acsc_loss_precision": ["exact", "exact", "rounded", None], "acsc_loss_per_case_baht": [10000, 10000, 10000, np.nan],
        "acsc_top_type_th": ["หลอกซื้อขายสินค้าออนไลน์", None, "การหลอกลวงด้านสินค้าและบริการ", None],
        "acsc_highest_loss_type_th": ["หลอกให้ลงทุน", "การหลอกโอนเงินเพื่อรับรางวัล", "ข่มขู่ทางโทรศัพท์", None],
        "acsc_flag": [None, "Suspect: 13x normal", None, None],
    })


def test_scam_type_grouping_merges_spellings():
    assert tf.group_scam_type("หลอกซื้อขายสินค้าออนไลน์") == tf.group_scam_type("การหลอกลวงด้านสินค้าและบริการ")
    assert tf.group_scam_type("การหลอกให้ลงทุนผ่านระบบคอมพิวเตอร์") == "หลอกลงทุน"
    assert tf.group_scam_type(np.nan) is None


def test_weekly_flags_and_no_zero_fill():
    w = tf.build_weekly(_panel())
    assert list(w["acsc_suspect"]) == [False, True, False, False]
    assert list(w["acsc_usable"]) == [True, False, True, False]
    assert w.loc[3, "acsc_cases"] != 0 and np.isnan(w.loc[3, "acsc_cases"])      # missing week stays NaN
    assert np.isnan(w.loc[1, "acsc_cases_plot"])                                  # suspect week not plotted
    assert w.loc[2, "acsc_rounded"]


def test_latest_week_ignores_suspect_and_unreported():
    w = tf.build_weekly(_panel())
    lw = mx.latest_week(w, base_weeks=4)
    assert lw.week_start == pd.Timestamp("2026-01-18")
    assert lw.cases == 120 and lw.base_weeks == 1
    assert round(lw.cases_vs_base) == 20  # vs 100, the 1,300 outlier is excluded


def test_false_share_uses_summed_counts():
    w = tf.build_weekly(_panel())
    # 2 weeks: false 7 and 5 of 10 each -> 12/20 = 60%, mean of weekly % would also be 60 here; make it uneven
    uneven = w.iloc[[0, 2]].copy()
    uneven.loc[uneven.index[0], "afnc_verdicts"] = 100
    uneven.loc[uneven.index[0], "afnc_false"] = 50
    assert round(mx.false_share(uneven), 2) == round((50 + 5) / (100 + 10) * 100, 2)


def test_normalize_tags_aliases_generic_and_dedupe():
    assert tf.normalize_tags("COVID-19;โควิด19;AntiFakeNewsCenter;ออมสิน; ") == ["โควิด-19", "ธนาคารออมสิน"]
    assert tf.normalize_tags(np.nan) == []


def test_eu_dates_parse_day_first_and_count_unique_debunks():
    eu = pd.DataFrame({
        "debunk_id": ["a", "a", "b"], "keywords": ["x,y", "x,y", "x"], "article_id": [1, 2, 3],
        "debunk_date": ["01-06-2022", "01-06-2022", "13-02-2021"], "class": ["disinformation", "trustworthy", "disinformation"],
        "article_language": ["English"] * 3, "article_domain": ["d"] * 3,
    })
    d = tf.eu_prepare(eu)
    assert d["debunk_dt"].iloc[0] == pd.Timestamp("2022-06-01")          # not 6 January
    y = tf.eu_yearly(d).set_index("year")
    assert y.loc[2022, "debunks"] == 1 and y.loc[2022, "articles"] == 2   # 2 rows, 1 debunk
    kw = tf.eu_keywords(d).groupby("keyword")["debunks"].sum()
    assert kw["x"] == 2 and kw["y"] == 1


def test_fotn_percentages_and_rank():
    f = tf.build_fotn(pd.DataFrame({
        "country": ["A", "B", "C"], "iso3": ["AAA", "BBB", "CCC"], "data_year": 2024, "total_score": [90, 50, 50],
        "obstacles_to_access": [20, 10, 10], "limits_on_content": [35, 20, 20], "violations_of_user_rights": [35, 20, 20],
        "status_code": [1, 2, 2], "is_asean": False}))
    assert f.loc[0, "pct_access"] == 80
    assert mx.fotn_rank(f, "BBB", 2024) == (2, 3) and mx.fotn_rank(f, "CCC", 2024) == (2, 3)  # ties share rank


def test_aiid_flags_deepfake_scam_thai():
    inc = pd.DataFrame({
        "Incident ID": [1, 2], "date": pd.to_datetime(["2025-01-01", "2024-05-05"]),
        "title": ["Deepfake of Thai PM", "Robot vacuum"], "description": ["scam call", "bump"],
        "Implicated Systems": [None, None], "Risk Domain": ["Misinformation", None], "Intent": [None, None], "report_count": [3, 1]})
    f = tf.aiid_flags(inc)
    assert list(f["is_deepfake"]) == [True, False] and list(f["is_scam"]) == [True, False]
    assert list(f["is_thai"]) == [True, False] and list(f["classified"]) == [True, False]
