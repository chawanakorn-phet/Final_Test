"""Charts for the three question pages. Chart type follows the data: lines for time, bars for rankings,
diverging bars for change, scatter for relationships."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import config
from dashboard.theme import style_fig

C = config.COLORS


def _iso(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- Q1


def covid_compare(cs: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for src, color in (("AFNC (ไทย)", C["fake"]), ("EUvsDisinfo", C["global"])):
        d = cs[(cs["source"] == src) & (cs["year"] >= 2018)].sort_values("year")
        fig.add_trace(go.Scatter(x=d["year"], y=d["share_pct"], name=src, mode="lines+markers", line=dict(color=color, width=3),
                                 customdata=d[["n", "total"]].to_numpy(),
                                 hovertemplate=src + ": %{y:.1f}% (%{customdata[0]:,} จาก %{customdata[1]:,} เรื่อง)<extra></extra>"))
    fig.update_layout(title="สัดส่วนเรื่องที่เกี่ยวกับโควิด (% ของข่าวเท็จ/การหักล้างในปีนั้น)", hovermode="x unified")
    fig.update_yaxes(title="%", rangemode="tozero")
    fig.update_xaxes(dtick=1)
    return style_fig(fig, height=340)


def eu_class_mix(y: pd.DataFrame) -> go.Figure:
    y = y[y["year"] >= 2017]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=y["year"].astype(str), y=100 - y["trustworthy_share_pct"], name="disinformation", marker_color=C["global"],
                         hovertemplate="%{y:.0f}%"))
    fig.add_trace(go.Bar(x=y["year"].astype(str), y=y["trustworthy_share_pct"], name="trustworthy", marker_color="#A5D4CD",
                         hovertemplate="%{y:.0f}%"))
    fig.update_layout(barmode="stack", title="EUvsDisinfo: ประเภทบทความที่ผูกกับการหักล้าง (%) — ไม่ใช่ปลอม/บิดเบือน/จริง")
    fig.update_yaxes(range=[0, 100])
    return style_fig(fig, height=340)


def category_share_year(share: pd.DataFrame, title: str | None = None) -> go.Figure:
    """100% stacked bars of false items by category and year (share table from metrics.category_share)."""
    fig = go.Figure()
    for cat in config.CATEGORY_ORDER:
        d = share[share["category_th"] == cat]
        if d.empty:
            continue
        fig.add_trace(go.Bar(x=d["year"].astype(str), y=d["share_pct"], name=cat, marker_color=config.CATEGORY_COLORS[cat],
                             hovertemplate="%{y:.1f}%"))
    fig.update_layout(barmode="stack", title=title or "ข่าวเท็จไทยตามหมวด (% ต่อปี) — ปี 2026 เพิ่มหมวด 'อาชญากรรมออนไลน์'")
    fig.update_yaxes(range=[0, 100])
    return style_fig(fig, height=380)


def topic_change(df: pd.DataFrame, title: str, n: int = 6, color_up: str = C["scam"], color_down: str = C["muted"]) -> go.Figure:
    d = pd.concat([df.head(n), df.tail(n)]).drop_duplicates("topic").sort_values("change_pp")
    fig = go.Figure(go.Bar(y=d["topic"], x=d["change_pp"], orientation="h",
                           marker_color=[color_up if v > 0 else color_down for v in d["change_pp"]],
                           text=[f"{v:+.1f}" for v in d["change_pp"]], textposition="outside", cliponaxis=False,
                           customdata=d[["share_start", "share_end"]].to_numpy(),
                           hovertemplate="%{y}: %{customdata[0]:.1f}% → %{customdata[1]:.1f}% (%{x:+.1f} จุด)<extra></extra>"))
    fig.update_layout(title=title, hovermode="closest")
    fig.update_xaxes(title="เปลี่ยนแปลง (จุดเปอร์เซ็นต์)", range=[min(d["change_pp"].min() * 1.3, -1), d["change_pp"].max() * 1.25])
    fig.update_yaxes(automargin=True)
    return style_fig(fig, height=380, legend_bottom=False)


# ---------------------------------------------------------------- Q2


def anomaly_chart(weekly: pd.DataFrame, an: pd.DataFrame, col: str, label: str, series_label: str, year_from: int = 2020) -> go.Figure:
    w = weekly[weekly["week_start"].dt.year >= year_from].sort_values("week_start")
    fig = go.Figure(go.Scatter(x=w["week_start"].map(_iso), y=w[col], mode="lines", line=dict(color=C["fake"], width=1.6),
                               name=label, hovertemplate="%{y:.1f}"))
    a = an[an["series"] == series_label] if len(an) else an
    if len(a):
        fig.add_trace(go.Scatter(x=a["week_start"].map(_iso), y=a["value"], mode="markers", name="ผิดปกติ (|z| > 3.5)",
                                 marker=dict(color=C["scam"], size=11, line=dict(color="white", width=2)),
                                 customdata=np.stack([a["expected"], a["z"]], axis=-1),
                                 hovertemplate="%{y:.1f} (คาด %{customdata[0]:.1f}, z = %{customdata[1]:+.1f})<extra></extra>"))
    fig.update_layout(title=label + " รายสัปดาห์ — จุดแดง = ผิดปกติเทียบสัปดาห์รอบข้าง")
    return style_fig(fig, height=320)


def cases_loss_scatter(u: pd.DataFrame, rel: dict) -> go.Figure:
    x, y = u["acsc_cases"], u["acsc_loss_baht"] / 1e6
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="สัปดาห์", marker=dict(size=9, color=u["week_start"].map(pd.Timestamp.toordinal),
                             colorscale=[[0, "#E5A0A9"], [1, C["scam"]]], line=dict(color="white", width=1), showscale=False),
                             customdata=u["week_start"].dt.strftime("%Y-%m-%d"),
                             hovertemplate="สัปดาห์ %{customdata}<br>%{x:,.0f} คดี · %{y:,.0f} ล้านบาท<extra></extra>"))
    k, b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 20)
    fig.add_trace(go.Scatter(x=xs, y=k * xs + b, mode="lines", name=f"แนวโน้ม (r = {rel['r']:+.2f})", line=dict(color=C["ink"], dash="dash")))
    fig.update_layout(title="จำนวนคดี vs ความเสียหายต่อสัปดาห์ (สีเข้ม = ใหม่กว่า)", hovermode="closest",
                      xaxis_title="คดีต่อสัปดาห์", yaxis_title="ล้านบาท")
    return style_fig(fig, height=360)


def block_changes(b: pd.DataFrame) -> go.Figure:
    lab = b["from"].dt.strftime("%d/%m") + "–" + b["to"].dt.strftime("%d/%m")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=lab, y=b["cases_chg_pct"], name="จำนวนคดี", marker_color="#E5A0A9", hovertemplate="%{y:+.1f}%"))
    fig.add_trace(go.Bar(x=lab, y=b["lpc_chg_pct"], name="บาท/คดี", marker_color=C["scam"], hovertemplate="%{y:+.1f}%"))
    for i, hit in enumerate(b["cases_down_lpc_up"]):
        if hit:
            fig.add_vrect(x0=i - 0.5, x1=i + 0.5, fillcolor=C["warn"], opacity=0.22, line_width=0)
    fig.update_layout(barmode="group", title="เปลี่ยนแปลงต่อบล็อก 4 สัปดาห์ (%) — แถบเหลือง = คดีลดแต่บาท/คดีเพิ่ม", yaxis_title="%")
    fig.update_xaxes(tickangle=-35, automargin=True)
    out = style_fig(fig, height=380)
    out.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return out


# ---------------------------------------------------------------- Q3


def theme_overlap_chart(ov: pd.DataFrame) -> go.Figure:
    d = ov.sort_values("share_pct_AIID")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=d["theme"], x=d["share_pct_AIID"], orientation="h", name="AIID (สากล) % ของเหตุการณ์", marker_color=C["ai"],
                         hovertemplate="%{y}: %{x:.1f}%"))
    fig.add_trace(go.Bar(y=d["theme"], x=d["share_pct_AFNC"], orientation="h", name="AFNC (ไทย) % ของข่าวเท็จ", marker_color=C["fake"],
                         hovertemplate="%{y}: %{x:.1f}%"))
    fig.update_layout(barmode="group", title="ธีมภัย: สากล (AI) เทียบข่าวเท็จไทย", hovermode="closest", xaxis_title="% ของรายการทั้งหมดในแหล่งนั้น")
    fig.update_yaxes(automargin=True)
    return style_fig(fig, height=520)


def peers_chart(peers: pd.DataFrame) -> go.Figure:
    d = peers.sort_values("total_score")
    colors = [C["freedom"] if i == "THA" else "#B9B6AE" for i in d["iso3"]]
    fig = go.Figure(go.Bar(y=d["country"], x=d["total_score"], orientation="h", marker_color=colors, text=d["total_score"], textposition="outside",
                           cliponaxis=False, customdata=d[["change_5y"]].to_numpy(),
                           hovertemplate="%{y}: %{x} คะแนน (5 ปี: %{customdata[0]:+.0f})<extra></extra>"))
    fig.update_layout(title="ประเทศที่คะแนนใกล้ไทย (±6)", hovermode="closest")
    fig.update_xaxes(range=[0, 60])
    return style_fig(fig, height=340, legend_bottom=False)


def country_scatter(country: pd.DataFrame, rho: float) -> go.Figure:
    d = country[country["mentions"] > 0]
    status = {1: ("เสรี", C["global"]), 2: ("เสรีบางส่วน", C["warn"]), 3: ("ไม่เสรี", C["scam"])}
    fig = go.Figure()
    for code, (name, color) in status.items():
        s = d[d["status_code"] == code]
        fig.add_trace(go.Scatter(x=s["total_score"], y=s["mentions"], mode="markers", name=name, marker=dict(size=10, color=color, line=dict(color="white", width=1)),
                                 text=s["country"].str.replace(r" \(.*\)", "", regex=True),
                                 hovertemplate="%{text}<br>คะแนน %{x} · ถูกกล่าวถึง %{y} เรื่อง<extra></extra>"))
    top = d.nlargest(6, "mentions")
    for _, r in top.iterrows():
        fig.add_annotation(x=r["total_score"], y=np.log10(r["mentions"]), text=r["country"].split(" (")[0], showarrow=False, yshift=12, font=dict(size=11))
    fig.update_yaxes(type="log", title="จำนวนเหตุการณ์ที่กล่าวถึงประเทศ (log)")
    fig.update_xaxes(title="คะแนนเสรีภาพอินเทอร์เน็ต (สูง = เสรี)")
    fig.update_layout(title=f"เสรีภาพ vs การถูกกล่าวถึงใน AIID (สำรวจ · ρ = {rho:+.2f})", hovermode="closest")
    return style_fig(fig, height=380)


def fotn_lines(fotn: pd.DataFrame, iso3s: list[str]) -> go.Figure:
    """Selected countries over time; Thailand is always drawn and highlighted."""
    keep = list(dict.fromkeys(["THA"] + list(iso3s)))
    fig = go.Figure()
    greys = ["#8B8386", "#B9B3AE", "#A39B9D", "#C9C3C0", "#7E7478", "#D3CDCB"]
    for k, iso in enumerate(keep):
        d = fotn[fotn["iso3"] == iso].sort_values("data_year")
        if d.empty:
            continue
        name = d["country"].iloc[0].split(" (")[0]
        th = iso == "THA"
        fig.add_trace(go.Scatter(x=d["data_year"], y=d["total_score"], name=name, mode="lines+markers" if th else "lines",
                                 line=dict(color=C["freedom"] if th else greys[k % len(greys)], width=4 if th else 1.8),
                                 hovertemplate=name + ": %{y}<extra></extra>"))
        fig.add_annotation(x=d["data_year"].iloc[-1], y=d["total_score"].iloc[-1], text=name, showarrow=False, xanchor="left", xshift=6,
                           font=dict(size=11, color=C["freedom"] if th else C["muted"]))
    fig.add_hrect(y0=0, y1=39.5, fillcolor="#C0392B", opacity=0.05, line_width=0)
    fig.add_hrect(y0=39.5, y1=69.5, fillcolor="#D4A017", opacity=0.05, line_width=0)
    fig.add_hrect(y0=69.5, y1=100, fillcolor="#1E8C7E", opacity=0.05, line_width=0)
    fig.update_layout(title="คะแนนเสรีภาพอินเทอร์เน็ตรายประเทศ (ยิ่งสูงยิ่งเสรี)", showlegend=False, margin=dict(r=90))
    fig.update_yaxes(range=[0, 100], title="คะแนน (0–100)")
    return style_fig(fig, height=400, legend_bottom=False)
