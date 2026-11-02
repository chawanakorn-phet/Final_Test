"""Correlation with validity gates. Refuses (ok=False) instead of computing a number that would mislead."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

INSUFFICIENT = "ไม่มีข้อมูลเพียงพอสำหรับการวิเคราะห์นี้"


def correlate(x: pd.Series, y: pd.Series, method: str = "spearman", min_n: int = 10) -> dict:
    """Pearson or Spearman r with two-sided p-value. n counts complete pairs; below `min_n` nothing is computed."""
    d = pd.concat([pd.Series(x).reset_index(drop=True), pd.Series(y).reset_index(drop=True)], axis=1).dropna()
    n = len(d)
    out = {"method": method, "n": n, "r": np.nan, "p": np.nan, "ok": False, "reason": "", "slope": np.nan}
    if n < min_n:
        out["reason"] = f"{INSUFFICIENT}: มีคู่ข้อมูลที่ใช้ได้ {n} คู่ (ต้องการอย่างน้อย {min_n})"
        return out
    a, b = d.iloc[:, 0].to_numpy(float), d.iloc[:, 1].to_numpy(float)
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        out["reason"] = f"{INSUFFICIENT}: ตัวแปรหนึ่งมีค่าคงที่ทุกแถว"
        return out
    r, p = (stats.spearmanr(a, b) if method == "spearman" else stats.pearsonr(a, b))[:2]
    out.update(r=float(r), p=float(p), ok=True, slope=float(np.polyfit(a, b, 1)[0]))
    return out


def strength(r: float) -> str:
    a = abs(r)
    return "ไม่มี/อ่อนมาก" if a < 0.2 else "อ่อน" if a < 0.4 else "ปานกลาง" if a < 0.6 else "ค่อนข้างแรง" if a < 0.8 else "แรง"


def interpret(res: dict, alpha: float = 0.05) -> str:
    """One sentence, always with n and the 'correlation is not causation' guard."""
    if not res["ok"]:
        return res["reason"]
    direction = "ไปทางเดียวกัน" if res["r"] > 0 else "สวนทางกัน"
    sig = "มีนัยสำคัญทางสถิติ" if res["p"] < alpha else "ไม่มีนัยสำคัญทางสถิติ"
    return (f"{res['method'].capitalize()} r = {res['r']:+.2f} (ความสัมพันธ์{strength(res['r'])} {direction}), p = {res['p']:.3g} ({sig} ที่ α = {alpha}), "
            f"n = {res['n']} · ไม่ใช่หลักฐานเชิงเหตุและผล")


def correlation_table(df: pd.DataFrame, pairs: list[tuple[str, str, str]], method: str = "spearman", min_n: int = 10) -> pd.DataFrame:
    """pairs = [(label, col_x, col_y)] -> one row per pair with r, p, n, status."""
    rows = []
    for label, cx, cy in pairs:
        r = correlate(df[cx], df[cy], method, min_n)
        rows.append({"คู่ตัวแปร": label, "n": r["n"], "r": r["r"], "p-value": r["p"], "ผล": strength(r["r"]) if r["ok"] else "ไม่คำนวณ", "หมายเหตุ": r["reason"]})
    return pd.DataFrame(rows)
