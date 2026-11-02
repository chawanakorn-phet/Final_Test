"""Central configuration: paths, source file names, label mappings and colours."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = ROOT / "data" / "processed"
LOG_DIR = ROOT / "logs"

# Raw data is looked up in this order (first folder that contains the 4 dataset folders wins).
RAW_DIR_ENV = "FT_RAW_DIR"
RAW_CANDIDATES = [ROOT / "data" / "raw", ROOT]

# Dataset folders / files inside the raw directory.
AIID_DIR = "01_AI_Incident_Database"
AIID_LATEST = "AIID_Excel_Export-20261026.xlsx"
AIID_WEEKLY_DIR = "weekly_versions"
FOTN_FILE = Path("02_Freedom_on_the_Net") / "freedom_on_the_net_scores.csv"
EU_FILE = Path("03_EUvsDisinfo") / "euvsdisinfo_base.csv"
THAI_DIR = Path("04_Thai_Disinformation_and_Scams") / "csv"
PANEL_FILE = THAI_DIR / "weekly_panel.csv"
ACSC_FILE = THAI_DIR / "acsc_weekly.csv"
AFNC_FILE = THAI_DIR / "afnc_items.csv"


def find_raw_dir() -> Path | None:
    """Return the folder that holds the raw dataset folders, or None."""
    env = os.environ.get(RAW_DIR_ENV)
    candidates = ([Path(env)] if env else []) + RAW_CANDIDATES
    for c in candidates:
        if (c / PANEL_FILE).exists() and (c / FOTN_FILE).exists():
            return c
    return None


# ---------------------------------------------------------------------------
# ACSC: the same scam type is spelled many ways in the source -> group them.
# Rules are checked in order; first match wins.
# ---------------------------------------------------------------------------
ACSC_TYPE_RULES: list[tuple[str, str]] = [
    ("ลงทุน", "หลอกลงทุน"),
    ("แอบอ้าง", "แอบอ้างบุคคลอื่น"),
    ("ข่มขู่", "ข่มขู่ทางโทรศัพท์"),
    ("รางวัล", "โอนเงินรับรางวัล/รายได้พิเศษ"),
    ("รายได้พิเศษ", "โอนเงินรับรางวัล/รายได้พิเศษ"),
    ("ทำงานออนไลน์", "หลอกทำงานออนไลน์"),
    ("สินค้า", "หลอกซื้อขายสินค้า/บริการ"),
]
ACSC_TYPE_OTHER = "อื่น ๆ"

# ---------------------------------------------------------------------------
# AFNC categories and tags
# ---------------------------------------------------------------------------
CATEGORY_TH = {
    "Government policy & news": "นโยบายรัฐ/ข่าวสาร",
    "Health products": "ผลิตภัณฑ์สุขภาพ",
    "Finance & stocks": "การเงิน-หุ้น",
    "Disasters": "ภัยพิบัติ",
    "Public order & security": "ความสงบ/ความมั่นคง",
    "Online crime": "อาชญากรรมออนไลน์ (หมวดใหม่ 2026)",
}
CATEGORY_OTHER_TH = "อื่น ๆ"
CATEGORY_ORDER = list(CATEGORY_TH.values()) + [CATEGORY_OTHER_TH]

VERDICT_TH = {"Fake": "ข่าวปลอม", "Distorted": "ข่าวบิดเบือน", "True": "ข่าวจริง"}

TAG_GENERIC = {"AntiFakeNewsCenter", "ข่าวเด่นประจำสัปดาห์", "เกาะติดกระแสด่วน"}
TAG_ALIASES = {
    "โควิด-19": ["โควิด-19", "COVID-19", "โควิด19", "COVID19", "ไวรัสโคโรนาสายพันธุ์ใหม่2019", "โควิด"],
    "ธนาคารออมสิน": ["ธนาคารออมสิน", "ออมสิน"],
    "สินเชื่อ/เงินกู้": ["สินเชื่อ", "กู้เงิน", "เงินกู้", "กู้สินเชื่อ", "กู้เงินออนไลน์"],
    "มะเร็ง": ["มะเร็ง", "โรคมะเร็ง", "รักษามะเร็ง"],
    "ชวนลงทุน/หุ้น": ["ลงทุนหุ้น", "การลงทุน", "ชวนลงทุน", "ชักชวนลงทุน"],
    "ใบขับขี่": ["ทำใบขับขี่ออนไลน์", "ใบขับขี่", "ทำใบขับขี่"],
    "หางาน/รับสมัครงาน": ["รับสมัครงาน", "หางานทำ", "หางาน", "ทำงานต่างประเทศ"],
    "ธนาคารกรุงไทย": ["ธนาคารกรุงไทย", "กรุงไทย"],
    "ไทย-กัมพูชา": ["ไทยกัมพูชา", "ชายแดนไทยกัมพูชา", "กัมพูชา"],
    "ฝนตก/พายุ": ["ฝนตกหนัก", "ฝนตก", "พายุ", "พายุเข้า"],
}
# Tags that mark a false item as scam / impersonation related (used for the "fake news -> scams" bridge)
SCAM_TAGS = {"เพจปลอม", "มิจฉาชีพ", "แอบอ้าง", "หลอกลวง", "ไลน์ปลอม", "SMS", "ชวนลงทุน/หุ้น", "สินเชื่อ/เงินกู้"}
TAG_LOOKUP = {alias: canon for canon, aliases in TAG_ALIASES.items() for alias in aliases}

# ---------------------------------------------------------------------------
# Data-quality constants (see docs/ANALYSIS_AND_DESIGN.md)
# ---------------------------------------------------------------------------
SUSPECT_FLAG_PREFIX = "Suspect"
ACSC_ROUNDED_FROM = "2026-08-09"  # loss figures are rounded to million baht from this week
DEEPFAKE_PATTERN = r"deepfake"
SCAM_PATTERN = r"scam|fraud"
THAI_PATTERN = r"\bThai(?:land)?\b"
AIID_CITE_URL = "https://incidentdatabase.ai/cite/{id}"

# Themes used to compare global AI harms (AIID, English text) with Thai fact-checked items (AFNC, Thai text).
# (key, Thai label, AIID regex on title+description, AFNC regex on title + tags). Multi-label: an item can match several.
THEMES = [
    ("impersonation_scam", "แอบอ้าง/ปลอมตัวเพื่อหลอกลวง", r"impersonat|scam|fraud|phishing|fake (?:account|profile|website)", r"แอบอ้าง|ปลอมแปลง|มิจฉาชีพ|หลอกลวง|เพจปลอม|ไลน์ปลอม|เว็บปลอม"),
    ("deepfake_ai", "deepfake / เนื้อหาที่ AI สร้าง", r"deepfake|synthetic|ai-generated|voice clon|generated", r"ดีปเฟค|ดีพเฟค|deepfake|เอไอ|ปัญญาประดิษฐ์|\bAI\b|ตัดต่อ|คลิปปลอม|เสียงปลอม|ภาพปลอม"),
    ("political", "การเมือง/การเลือกตั้ง", r"election|politic|candidate|propaganda|president|prime minister|government", r"เลือกตั้ง|พรรค|นายก|การเมือง|รัฐบาล|กกต|รัฐประหาร|ชุมนุม"),
    ("investment_finance", "การลงทุน/การเงิน", r"invest|crypto|financ|bank|stock|loan", r"ลงทุน|หุ้น|คริปโต|กู้|สินเชื่อ|ธนาคาร|ออมสิน"),
    ("health", "สุขภาพ/การแพทย์", r"health|medical|medicine|patient|vaccine|diagnos|drug", r"สุขภาพ|รักษา|โรค|มะเร็ง|วัคซีน|สมุนไพร|อาหารเสริม|โควิด"),
    ("sexual_abuse", "เนื้อหาทางเพศ/ล่วงละเมิด", r"sexual|nude|porn|explicit|minors?\b|child", r"อนาจาร|ลามก|ล่วงละเมิด"),
    ("chatbot_llm", "แชตบอต/โมเดลภาษา", r"chatbot|chatgpt|\bllm\b|language model|grok|gemini|claude", r"ChatGPT|แชตบอต|chatbot"),
    ("bias_discrimination", "อคติ/การเลือกปฏิบัติ", r"bias|discriminat|racis|facial recognition|face recognition", r"เลือกปฏิบัติ|อคติ"),
    ("physical_safety", "ความปลอดภัยทางกายภาพ (ยานยนต์/หุ่นยนต์/อาวุธ)", r"autonomous vehicle|self-driving|robot|drone|crash|tesla|weapon", r"โดรน|หุ่นยนต์|รถไร้คนขับ"),
    ("disaster", "ภัยพิบัติ", r"earthquake|flood|disaster|wildfire|hurricane", r"แผ่นดินไหว|น้ำท่วม|พายุ|ภัยพิบัติ|ฝนตก"),
]
COVID_TAGS_TH = {"โควิด-19", "วัคซีน", "ฉีดวัคซีน", "โรคระบาด"}
COVID_KEYWORDS_EU = {"coronavirus", "vaccination", "Virus / bacteria threat"}

# AIID has almost no country field, so countries are inferred from text. Ambiguous names are skipped.
COUNTRY_TEXT_ALIASES = {
    "Russian Federation (the)": ["Russia", "Russian"],
    "United States of America (the)": ["United States", "U.S.", "American"],
    "United Kingdom of Great Britain and Northern Ireland (the)": ["United Kingdom", "Britain", "British"],
    "China": ["China", "Chinese"], "Iran (Islamic Republic of)": ["Iran", "Iranian"], "Viet Nam": ["Vietnam"],
    "Korea (the Republic of)": ["South Korea", "Korea"], "Myanmar": ["Myanmar", "Burma"], "Thailand": ["Thailand", "Thai"],
    "India": ["India", "Indian"], "Ukraine": ["Ukraine", "Ukrainian"], "Taiwan (Province of China)": ["Taiwan"],
}
COUNTRY_TEXT_SKIP = {"Georgia", "Jordan", "Chad", "Turkey"}  # person/state/animal names collide with text

ASEAN = {
    "THA": "ไทย", "SGP": "สิงคโปร์", "MYS": "มาเลเซีย", "IDN": "อินโดนีเซีย", "PHL": "ฟิลิปปินส์",
    "VNM": "เวียดนาม", "KHM": "กัมพูชา", "MMR": "เมียนมา",
}
STATUS_TH = {1: "เสรี", 2: "เสรีบางส่วน", 3: "ไม่เสรี"}

# ---------------------------------------------------------------------------
# Colours (one meaning per hue)
# ---------------------------------------------------------------------------
COLORS = {
    "scam": "#7B1E3A",        # online scams (primary, maroon)
    "fake": "#E08A3C",        # fake news
    "ai": "#8E4B8F",          # AI incidents
    "freedom": "#3E5C8A",     # internet freedom
    "global": "#2F7F79",      # EUvsDisinfo
    "ink": "#2B2326",
    "muted": "#8B8386",
    "grid": "#EAE4E4",
    "paper": "#F5F2F2",
    "warn": "#D4A017",
}
CATEGORY_COLORS = {
    "นโยบายรัฐ/ข่าวสาร": "#7B1E3A",
    "ผลิตภัณฑ์สุขภาพ": "#C0506E",
    "การเงิน-หุ้น": "#E08A3C",
    "ภัยพิบัติ": "#F2C078",
    "ความสงบ/ความมั่นคง": "#3E5C8A",
    "อาชญากรรมออนไลน์ (หมวดใหม่ 2026)": "#2B2326",
    "อื่น ๆ": "#B9B3AE",
}
