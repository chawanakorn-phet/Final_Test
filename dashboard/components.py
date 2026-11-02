"""Small reusable UI pieces."""
from __future__ import annotations

import streamlit as st

import config


def fmt_int(x) -> str:
    return "–" if x is None or x != x else f"{x:,.0f}"


def fmt_million(x) -> str:
    return "–" if x is None or x != x else f"{x / 1e6:,.0f} ล้านบาท"


def delta_html(pct: float | None, label: str, higher_is_worse: bool = True) -> str:
    if pct is None or pct != pct:
        return f'<div class="delta">{label}: –</div>'
    cls = "up" if (pct > 0) == higher_is_worse else "down"
    arrow = "▲" if pct > 0 else "▼"
    return f'<div class="delta {cls}">{arrow} {abs(pct):.1f}% {label}</div>'


def kpi(label: str, value: str, delta: str = "", accent: str = config.COLORS["scam"], icon: str = "#") -> None:
    st.markdown(f'<div class="kpi" style="--accent:{accent}"><div class="ic">{icon}</div><div class="body">'
                f'<div class="label">{label}</div><div class="value">{value}</div>{delta}</div></div>', unsafe_allow_html=True)


def notes_on() -> bool:
    """Speaker-notes switch (header toggle). Off by default: the dashboard shows charts, the presenter does the talking."""
    return bool(st.session_state.get("show_notes", False))


def caption(text: str) -> None:
    if notes_on():
        st.caption(text)


def note(text: str, kind: str = "warn") -> None:
    if not notes_on():
        return
    st.markdown(f'<div class="note {"info" if kind == "info" else ""}">{text}</div>', unsafe_allow_html=True)


def read_hint(text: str) -> None:
    if not notes_on():
        return
    st.markdown(f'<div class="read">อ่านอย่างไร: {text}</div>', unsafe_allow_html=True)


def source(text: str) -> None:
    if not notes_on():
        return
    st.markdown(f'<div class="source">แหล่งข้อมูล: {text}</div>', unsafe_allow_html=True)


def chart(fig, key: str) -> None:
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})
