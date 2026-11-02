"""Static metadata shown in the 'Data Explorer & Sources' tab: data dictionary and indicator -> source mapping.

These describe where each number comes from (file, column, calculation). They contain no data values.
Column names are the ones in the original files (see 00_Data_Guide_TH.pdf) or in the processed tables built by data_processing/.
"""
from __future__ import annotations

DICTIONARY = [
    # dataset, variable, meaning, unit, file, column
    ["AFNC", "date", "วันที่เผยแพร่โพสต์ (เวลาไทย, ค.ศ.)", "วันที่", "afnc_items.csv", "date"],
    ["AFNC", "item_type", "ประเภทโพสต์: Verdict (คำตัดสิน), Knowledge article, Online crime advisory, Other news, Activity, Announcement, Unlabelled", "ข้อความ", "afnc_items.csv", "item_type"],
    ["AFNC", "status (สถานะข่าว)", "ผลตัดสิน: ข่าวปลอม (Fake), ข่าวบิดเบือน (Distorted), ข่าวจริง (True); โพสต์ที่ไม่ใช่คำตัดสินจัดเป็น 'อื่น ๆ'", "ข้อความ", "afnc_items.csv", "verdict_en + item_type"],
    ["AFNC", "category (ประเภทข่าว)", "หมวดข่าวของศูนย์ฯ แปลเป็นไทย; หมวดเล็ก (Economy, Drugs, Other news) รวมเป็น 'อื่น ๆ'", "ข้อความ", "afnc_items.csv", "category_en"],
    ["AFNC", "checked_by_agency", "หน่วยงานที่ตรวจข้อเท็จจริง (ว่างราว 21%)", "ข้อความ", "afnc_items.csv", "checked_by_agency"],
    ["AFNC", "topic_tags", "แท็กหัวข้อคั่นด้วย ; (รวมตัวสะกดต่างกันแล้ว)", "ข้อความ", "afnc_items.csv", "topic_tags"],
    ["ACSC", "week_start / week_end", "วันอาทิตย์/เสาร์ของสัปดาห์ที่แถลง", "วันที่", "acsc_weekly.csv", "week_start, week_end"],
    ["ACSC", "cases", "จำนวนคดีที่แจ้งผ่าน Thaipoliceonline ในสัปดาห์นั้น (จำนวนเหตุการณ์ที่มีผู้แจ้ง ไม่ใช่จำนวนผู้เสียหาย)", "คดี", "acsc_weekly.csv", "cases"],
    ["ACSC", "loss_baht", "มูลค่าความเสียหายรวมของสัปดาห์ (ตั้งแต่ 9 ส.ค. 2026 ปัดเป็นล้านบาท)", "บาท", "acsc_weekly.csv", "loss_baht"],
    ["ACSC", "loss_per_case", "ความเสียหายต่อคดี = loss_baht ÷ cases (คำนวณใหม่)", "บาท/คดี", "acsc_weekly.csv", "loss_baht, cases"],
    ["ACSC", "top_type / highest_loss_type", "ประเภทคดีอันดับ 1 ด้านจำนวน / ด้านความเสียหาย (จัดกลุ่มสะกดต่างกันเป็น 6 กลุ่ม)", "ข้อความ", "acsc_weekly.csv", "top_type_th, highest_loss_type_th"],
    ["ACSC", "highest_loss_type_loss_baht", "ความเสียหายของประเภทที่สูงที่สุด (มีเพียงบางสัปดาห์, ส่วนใหญ่ปัด)", "บาท", "acsc_weekly.csv", "highest_loss_type_loss_baht"],
    ["ACSC", "flag", "ป้ายเตือนของสัปดาห์ที่ตัวเลขน่าสงสัย (16–22 ส.ค. 2026)", "ข้อความ", "acsc_weekly.csv", "flag"],
    ["ACSC", "source_url", "ลิงก์ข่าวต้นทางของตัวเลขรายสัปดาห์", "URL", "acsc_weekly.csv", "source_url"],
    ["EUvsDisinfo", "debunk_id", "รหัสการหักล้าง 1 เรื่อง (1 เรื่องมีได้หลายบทความ)", "รหัส", "euvsdisinfo_base.csv", "debunk_id"],
    ["EUvsDisinfo", "debunk_date", "วันที่เผยแพร่การหักล้าง (DD-MM-YYYY → แปลงเป็นวันที่)", "วันที่", "euvsdisinfo_base.csv", "debunk_date"],
    ["EUvsDisinfo", "keywords", "ประเด็น/เรื่องเล่าที่ถูกหักล้าง คั่นด้วยจุลภาค", "ข้อความ", "euvsdisinfo_base.csv", "keywords"],
    ["EUvsDisinfo", "class", "disinformation = บทความเผยแพร่ข้อมูลเท็จ · trustworthy = บทความจากสื่อน่าเชื่อถือที่ผูกกับการหักล้างเดียวกัน (ไม่ใช่ข่าวจริง/ปลอม)", "ข้อความ", "euvsdisinfo_base.csv", "class"],
    ["AIID", "Incident ID / date / title", "รหัส วันที่เกิดเหตุ และชื่อเหตุการณ์ AI ก่อปัญหา", "รหัส/วันที่/ข้อความ", "AIID_Excel_Export-20261026.xlsx (Incidents)", "Incident ID, date, title"],
    ["AIID", "Risk Domain / Intent", "ประเภทความเสี่ยงและเจตนา (MIT) — ว่างราว 16% ที่ยังไม่ถูกจัดหมวด", "ข้อความ", "AIID_Excel_Export-20261026.xlsx (Incidents)", "Risk Domain, Intent"],
    ["AIID", "is_deepfake / is_scam / is_thai", "ธงที่ค้นด้วยคำจากชื่อ คำอธิบาย และระบบที่เกี่ยวข้อง (ไม่แยกตัวพิมพ์) — ไม่ใช่คอลัมน์ในไฟล์ต้นทาง", "จริง/เท็จ", "คำนวณ", "title, description, Implicated Systems"],
    ["Freedom on the Net", "total_score", "คะแนนเสรีภาพอินเทอร์เน็ตรวม 0–100 (สูง = เสรี)", "คะแนน", "freedom_on_the_net_scores.csv", "total_score"],
    ["Freedom on the Net", "obstacles_to_access / limits_on_content / violations_of_user_rights", "3 ส่วนของคะแนน เต็ม 25 / 35 / 40", "คะแนน", "freedom_on_the_net_scores.csv", "ชื่อคอลัมน์เดียวกัน"],
    ["Freedom on the Net", "data_year / report_edition", "ปีของข้อมูล และปีของรายงานฉบับที่ตีพิมพ์ (= data_year + 1)", "ปี", "freedom_on_the_net_scores.csv", "data_year, report_edition"],
    ["Freedom on the Net", "status_code", "1 = เสรี (≥ 70), 2 = เสรีบางส่วน (40–69), 3 = ไม่เสรี (≤ 39)", "รหัส", "freedom_on_the_net_scores.csv", "status_code"],
]

SOURCE_MAP = [
    # indicator, dataset, file, columns, calculation, filters that apply
    ["จำนวนข่าวปลอม", "AFNC", "afnc_items.csv", "item_type, verdict_en", "นับโพสต์ที่ item_type = Verdict และ verdict_en = Fake", "ช่วงวันที่/ปี/ไตรมาส/เดือน, ประเภทข่าว, สถานะ"],
    ["จำนวนข่าวจริง", "AFNC", "afnc_items.csv", "item_type, verdict_en", "นับโพสต์ Verdict ที่ verdict_en = True", "เหมือนข้างบน"],
    ["สัดส่วนข่าวเท็จ", "AFNC", "afnc_items.csv", "verdict_en", "(Fake + Distorted) ÷ Verdict ทั้งหมด ในช่วง/หมวดที่เลือก (ตัวหารคือคำตัดสิน ไม่ใช่ข่าวทั้งสังคม)", "เหมือนข้างบน"],
    ["ประเภทข่าวที่พบมากที่สุด", "AFNC", "afnc_items.csv", "category_en", "นับตามหมวด (แปลไทย รวมหมวดเล็กเป็น 'อื่น ๆ')", "เหมือนข้างบน"],
    ["จำนวนการหักล้างนานาชาติ", "EUvsDisinfo", "euvsdisinfo_base.csv", "debunk_id, debunk_date", "นับ debunk_id ที่ไม่ซ้ำ", "ช่วงวันที่/ปี/ไตรมาส/เดือน, ต่างประเทศ"],
    ["ประเด็นนานาชาติ", "EUvsDisinfo", "euvsdisinfo_base.csv", "keywords", "แยก keywords แล้วนับต่อการหักล้างที่ไม่ซ้ำ", "เหมือนข้างบน"],
    ["มูลค่าความเสียหายจากมิจฉาชีพ", "ACSC", "acsc_weekly.csv", "loss_baht, flag", "รวมเฉพาะสัปดาห์ที่มีการแถลงและไม่ติดป้าย Suspect; สัปดาห์ที่ไม่มีตัวเลขไม่นับเป็น 0", "ช่วงวันที่/ปี/ไตรมาส/เดือน, หมวดหมู่ความเสียหาย, ประเทศไทย"],
    ["จำนวนคดี", "ACSC", "acsc_weekly.csv", "cases", "รวม cases ของสัปดาห์ที่ใช้ได้ (คดีที่มีผู้แจ้ง ไม่ใช่จำนวนผู้เสียหาย)", "เหมือนข้างบน"],
    ["จำนวนผู้เสียหาย", "—", "—", "—", "ไม่มีในชุดข้อมูล จึงไม่แสดง", "—"],
    ["ความเสียหายต่อคดี", "ACSC", "acsc_weekly.csv", "loss_baht, cases", "loss_baht ÷ cases (คำนวณใหม่ ไม่ใช้ค่าเปลี่ยนที่ตำรวจแถลง)", "เหมือนข้างบน"],
    ["ประเภทที่เสียหายสูงสุด", "ACSC", "acsc_weekly.csv", "highest_loss_type_th, highest_loss_type_loss_baht", "จัดกลุ่มป้ายที่สะกดต่างกันเป็น 6 กลุ่ม; ยอดเงินแยกประเภทมีเฉพาะบางสัปดาห์", "เหมือนข้างบน"],
    ["คะแนนเสรีภาพอินเทอร์เน็ต", "Freedom on the Net", "freedom_on_the_net_scores.csv", "total_score, data_year", "ค่าตรงจากไฟล์ (ปีข้อมูล ไม่ใช่ปีรายงาน)", "ช่วงปี, ประเทศ/กลุ่มประเทศ, ไทย/ต่างประเทศ (เดือน/ไตรมาสไม่ใช้)"],
    ["อันดับเสรีภาพ", "Freedom on the Net", "freedom_on_the_net_scores.csv", "total_score", "1 + จำนวนประเทศที่คะแนนสูงกว่าในปีเดียวกัน (คะแนนเท่ากันได้อันดับเดียวกัน)", "ปีที่เลือก"],
    ["เหตุการณ์ AI / deepfake / scam", "AIID", "AIID_Excel_Export-20261026.xlsx", "date, title, description, Implicated Systems", "นับเหตุการณ์ และธงจากการค้นคำ (deepfake, scam|fraud, Thai)", "ช่วงวันที่/ปี/ไตรมาส/เดือน, ไทย/ต่างประเทศ"],
    ["พยากรณ์", "AFNC / ACSC", "ตารางที่ประมวลผลแล้ว", "จำนวนข่าวเท็จรายเดือน / ความเสียหายรายสัปดาห์", "เปรียบเทียบ 5 แบบจำลองด้วย rolling-origin back-test เลือก RMSE ต่ำสุด; ปฏิเสธเมื่อข้อมูลน้อยกว่าเกณฑ์", "ไม่เปลี่ยนตามตัวกรอง (ใช้ข้อมูลทั้งช่วง)"],
]
