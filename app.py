"""ภัยข่าวปลอมและการหลอกลวงออนไลน์ — Streamlit entry point.

Run:  streamlit run app.py
"""
from __future__ import annotations

import logging
import logging.handlers

import streamlit as st

import config
from dashboard import pages, question_pages as qp, summary as sm, theme
from data_processing import pipeline, store

st.set_page_config(page_title="ภัยข่าวปลอมและการหลอกลวงออนไลน์", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")


def _setup_logging() -> None:
    root = logging.getLogger()
    if any(getattr(h, "_ft", False) for h in root.handlers):
        return
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(config.LOG_DIR / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    fh._ft = True  # type: ignore[attr-defined]
    root.addHandler(fh)
    root.setLevel(logging.INFO)


_setup_logging()
st.markdown(theme.CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner="กำลังโหลดตารางข้อมูล…", max_entries=2)
def _load(signature: str):  # signature only keys the cache
    return store.load_tables(), store.load_meta()


def _rebuild() -> None:
    with st.spinner("กำลังประมวลผลข้อมูลดิบ (ราว 1 นาที)…"):
        try:
            pipeline.run()
        except FileNotFoundError as e:
            st.error(str(e))
            return
        except Exception as e:  # noqa: BLE001 - show the reason, keep the old tables
            logging.getLogger(__name__).exception("pipeline failed")
            st.error(f"ประมวลผลไม่สำเร็จ ตารางเดิมยังอยู่: {e}")
            return
    st.cache_data.clear()
    st.rerun()


if not store.is_built():
    st.title("ภัยข่าวปลอมและการหลอกลวงออนไลน์")
    st.warning("ยังไม่มีตารางที่ประมวลผลแล้วใน data/processed/")
    raw = config.find_raw_dir()
    if raw is None:
        st.info("วางโฟลเดอร์ข้อมูลดิบ (01_AI_Incident_Database … 04_Thai_Disinformation_and_Scams) ไว้ใน data/raw/ "
                f"หรือกำหนดตัวแปร {config.RAW_DIR_ENV} แล้วรีเฟรชหน้านี้")
    elif st.button("ประมวลผลข้อมูลดิบ", type="primary"):
        _rebuild()
    st.stop()

tables, meta = _load(store.signature())

@st.dialog("สรุปแดชบอร์ดทั้งหมด", width="large")
def _show_summary() -> None:
    """Full written summary (all three questions, data, cleaning, limits), built by Python from the same tables."""
    md = sm.build_summary_markdown(tables, meta, qp.analysis(meta["built_at"]))
    st.download_button("ดาวน์โหลดสรุป (.md)", md, file_name="dashboard_summary.md", mime="text/markdown", type="primary")
    st.markdown(md)


NAV = [
    ("ภาพรวม", pages.overview),
    ("Q1 ข้อมูลบิดเบือน: สากล vs ไทย", qp.q1),
    ("Q2 ภัยหลอกลวงและความผิดปกติ", qp.q2),
    ("Q3 เสรีภาพอินเทอร์เน็ตและภัย AI", qp.q3),
    ("รายละเอียดแต่ละชุดข้อมูล", qp.details),
    ("คุณภาพข้อมูล", pages.quality),
]

with st.sidebar:
    st.markdown('<div class="brand">🛡️ ภัยข่าวปลอมและ<br>การหลอกลวงออนไลน์</div>', unsafe_allow_html=True)
    choice = st.radio("เมนู", [n for n, _ in NAV], label_visibility="collapsed", key="nav")
    st.markdown("---")
    if st.button("📄 สรุปแดชบอร์ดทั้งหมด", key="open_summary", width="stretch"):
        _show_summary()
    st.toggle("แสดงหมายเหตุ", key="show_notes", help="เปิดเพื่อดูคำอธิบายวิธีอ่าน ข้อควรระวัง และแหล่งข้อมูล (ปิดไว้ตอนนำเสนอ)")
    if config.find_raw_dir() is not None and st.button("ประมวลผลใหม่", help="อ่านไฟล์ดิบและสร้างตารางใหม่"):
        _rebuild()

st.markdown(
    f'<div class="topbar"><div><div class="t">{choice}</div>'
    f'<div class="s">ข่าวปลอมถึง {meta["afnc_last_date"]} · คดีถึงสัปดาห์ {meta["acsc_last_week"]} · AIID ฉบับ {meta["aiid_snapshot"]}'
    f' · ตัวเลขคดีรวบรวมจากข่าว ไม่ใช่ข้อมูลเปิดของตำรวจ</div></div></div>', unsafe_allow_html=True)

dict(NAV)[choice](tables, meta)
