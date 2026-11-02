"""Plotly figure builders. Every function takes processed tables and returns a go.Figure."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import config
from dashboard.theme import style_fig

C = config.COLORS


def _iso(ts) -> str:
    """Plain ISO string: avoids plotly mis-reading pandas 3 datetime64 resolutions in shapes."""
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


def _gap_bands(weekly: pd.DataFrame, fig, row: int | None = None):
    """Grey bands for ACSC weeks with no briefing (so the gap is visible, not a zero)."""
    start = weekly.loc[weekly["acsc_reported"], "week_start"].min()
    miss = weekly[(weekly["week_start"] >= start) & ~weekly["acsc_reported"]]
    for _, r in miss.iterrows():
        fig.add_vrect(x0=_iso(r["week_start"]), x1=_iso(r["week_end"] + pd.Timedelta(days=1)), fillcolor="#999", opacity=0.15,
                      line_width=0, row=row, col=1 if row else None)


def scam_vs_fake(weekly: pd.DataFrame) -> go.Figure:
    """Three stacked panels on one time axis: cases, loss, fake-news share."""
    start = weekly.loc[weekly["acsc_reported"], "week_start"].min()
    w = weekly[weekly["week_start"] >= start].sort_values("week_start")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.36, 0.36, 0.28],
                        subplot_titles=("คดีออนไลน์ที่แจ้งต่อสัปดาห์ (คดี)", "ความเสียหายต่อสัปดาห์ (ล้านบาท)",
                                        "สัดส่วนข่าวเท็จในคำตัดสิน AFNC (%)"))
    fig.add_trace(go.Scatter(x=w["week_start"], y=w["acsc_cases_plot"], mode="lines+markers", name="คดี",
                             line=dict(color=C["scam"], width=2), marker=dict(size=5), connectgaps=False,
                             hovertemplate="%{y:,.0f} คดี"), row=1, col=1)
    exact, rnd = w[~w["acsc_rounded"]], w[w["acsc_rounded"]]
    fig.add_trace(go.Scatter(x=w["week_start"], y=w["acsc_loss_baht_plot"] / 1e6, mode="lines", name="ความเสียหาย",
                             line=dict(color=C["scam"], width=2), connectgaps=False, hoverinfo="skip", showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=exact["week_start"], y=exact["acsc_loss_baht_plot"] / 1e6, mode="markers",
                             name="ตัวเลขเต็มจำนวน", marker=dict(color=C["scam"], size=6),
                             hovertemplate="%{y:,.0f} ล้านบาท"), row=2, col=1)
    fig.add_trace(go.Scatter(x=rnd["week_start"], y=rnd["acsc_loss_baht_plot"] / 1e6, mode="markers",
                             name="ตัวเลขปัดเป็นล้านบาท", marker=dict(color="white", size=7, line=dict(color=C["scam"], width=2)),
                             hovertemplate="%{y:,.0f} ล้านบาท (ปัด)"), row=2, col=1)
    fig.add_trace(go.Scatter(x=w["week_start"], y=w["afnc_false_share_pct"], mode="lines+markers", name="สัดส่วนข่าวเท็จ",
                             line=dict(color=C["fake"], width=2), marker=dict(size=5), connectgaps=False,
                             hovertemplate="%{y:.1f}%"), row=3, col=1)
    for r in (1, 2):  # the AFNC panel has data in those weeks, so no gap band there
        _gap_bands(w, fig, row=r)
    sus = w[w["acsc_suspect"]]
    for _, r in sus.iterrows():
        fig.add_vrect(x0=_iso(r["week_start"]), x1=_iso(r["week_end"] + pd.Timedelta(days=1)), fillcolor=C["warn"], opacity=0.28,
                      line_width=0, row="all", col=1)
    if len(sus):
        fig.add_annotation(x=_iso(sus["week_start"].iloc[0]), y=1.0, yref="y domain", text="ตัวเลขน่าสงสัย<br>(ตัดออก)",
                           showarrow=False, font=dict(size=11, color="#7a5a00"), xanchor="left", yanchor="top",
                           xref="x", row=1, col=1)
    fig.update_yaxes(rangemode="tozero", row=1, col=1)
    fig.update_yaxes(rangemode="tozero", row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=3, col=1)
    for a in fig.layout.annotations:
        if a.xref == "paper":  # subplot titles only; keep data-anchored annotations where they are
            a.update(x=0, xanchor="left", font=dict(size=13))
    return style_fig(fig, height=640)


def scam_monthly(monthly: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=monthly["month"], y=monthly["cases"], name="คดี/สัปดาห์ (เฉลี่ย)", marker_color="#E8B4AD",
                         hovertemplate="%{y:,.0f} คดี"), secondary_y=False)
    fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["loss_per_case"], name="ความเสียหาย/คดี (บาท)",
                             mode="lines+markers", line=dict(color=C["scam"], width=3),
                             hovertemplate="%{y:,.0f} บาท/คดี"), secondary_y=True)
    fig.update_yaxes(title_text="คดี/สัปดาห์", secondary_y=False, rangemode="tozero")
    fig.update_yaxes(title_text="บาท/คดี", secondary_y=True, rangemode="tozero", showgrid=False)
    fig.update_layout(title="รายเดือน: จำนวนคดีเฉลี่ยกับความเสียหายต่อคดี")
    return style_fig(fig, height=360)


def hbar(df: pd.DataFrame, x: str, y: str, color: str, title: str, height: int = 360, text_fmt: str = ",.0f",
         x_title: str | None = None) -> go.Figure:
    d = df.sort_values(x)
    fig = go.Figure(go.Bar(x=d[x], y=d[y], orientation="h", marker_color=color, text=d[x], texttemplate="%{text:" + text_fmt + "}",
                           textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:" + text_fmt + "}<extra></extra>"))
    fig.update_layout(title=title, hovermode="closest", xaxis_title=x_title)
    fig.update_xaxes(showgrid=True, gridcolor=C["grid"], range=[0, float(d[x].max()) * 1.18])
    fig.update_yaxes(showgrid=False, automargin=True)
    return style_fig(fig, height=height, legend_bottom=False)


def scam_types(types: pd.DataFrame) -> go.Figure:
    t = types.melt(id_vars="scam_type", var_name="measure", value_name="weeks")
    t["measure"] = t["measure"].map({"weeks_top_by_cases": "ประเภทที่มีคดีมากที่สุด", "weeks_top_by_loss": "ประเภทที่เสียหายสูงที่สุด"})
    order = types.assign(s=types.sum(axis=1, numeric_only=True)).sort_values("s")["scam_type"]
    fig = go.Figure()
    for m, col in (("ประเภทที่มีคดีมากที่สุด", "#E8B4AD"), ("ประเภทที่เสียหายสูงที่สุด", C["scam"])):
        d = t[t["measure"] == m].set_index("scam_type").reindex(order)
        fig.add_trace(go.Bar(y=d.index, x=d["weeks"], orientation="h", name=m, marker_color=col,
                             hovertemplate="%{y}: %{x} สัปดาห์"))
    fig.update_layout(barmode="group", title="ประเภทคดีที่เป็นอันดับ 1 (จำนวนสัปดาห์ที่แถลง)", hovermode="closest",
                      xaxis_title="จำนวนสัปดาห์")
    return style_fig(fig, height=360)


# ---------------------------------------------------------------- AFNC


def category_monthly(monthly: pd.DataFrame, year_from: int, as_share: bool) -> go.Figure:
    f = monthly[monthly["verdict_en"].isin(["Fake", "Distorted"]) & (monthly["month_start"].dt.year >= year_from)]
    g = f.groupby(["month_start", "category_th"])["n"].sum().reset_index()
    if as_share:
        g["n"] = g["n"] / g.groupby("month_start")["n"].transform("sum") * 100
    fig = go.Figure()
    for cat in config.CATEGORY_ORDER:
        d = g[g["category_th"] == cat]
        if d.empty:
            continue
        fig.add_trace(go.Bar(x=d["month_start"], y=d["n"], name=cat, marker_color=config.CATEGORY_COLORS[cat],
                             hovertemplate="%{y:.0f}" + ("%" if as_share else " เรื่อง")))
    fig.update_layout(barmode="stack", title="ข่าวเท็จ (ปลอม + บิดเบือน) รายเดือนตามหมวด" + (" — สัดส่วน %" if as_share else ""))
    fig.add_shape(type="line", x0="2026-01-01", x1="2026-01-01", y0=0, y1=1, yref="paper", line=dict(dash="dot", color=C["muted"]))
    fig.add_annotation(x="2026-01-01", y=1, yref="paper", text="เพิ่มหมวด 'อาชญากรรมออนไลน์'", showarrow=False,
                       xanchor="right", font=dict(size=11, color=C["muted"]))
    return style_fig(fig, height=420)


def verdict_mix(yearly: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, name, color in (("afnc_fake", "ข่าวปลอม", C["fake"]), ("afnc_distorted", "ข่าวบิดเบือน", "#F2C08B"),
                             ("afnc_true", "ข่าวจริง", C["global"])):
        fig.add_trace(go.Bar(x=yearly["year"].astype(str), y=yearly[col] / yearly["afnc_verdicts"] * 100, name=name,
                             marker_color=color, hovertemplate="%{y:.1f}%"))
    fig.update_layout(barmode="stack", title="ผลคำตัดสินต่อปี (% ของคำตัดสินทั้งหมด)")
    fig.update_yaxes(range=[0, 100])
    return style_fig(fig, height=360)


# ---------------------------------------------------------------- AIID


def aiid_yearly(y: pd.DataFrame, latest_year: int) -> go.Figure:
    y = y[y["year"] >= 2010]
    fig = go.Figure()
    colors = [("#E3CFE4" if yr == latest_year else "#C79BC9") for yr in y["year"]]
    fig.add_trace(go.Bar(x=y["year"], y=y["incidents"], name="เหตุการณ์ทั้งหมด", marker_color=colors,
                         hovertemplate="%{y} เหตุการณ์"))
    fig.add_trace(go.Scatter(x=y["year"], y=y["deepfake"], name="เกี่ยวกับ deepfake", mode="lines+markers",
                             line=dict(color=C["ai"], width=3), hovertemplate="%{y} deepfake"))
    fig.add_trace(go.Scatter(x=y["year"], y=y["scam"], name="เกี่ยวกับ scam/fraud", mode="lines+markers",
                             line=dict(color=C["scam"], width=3, dash="dot"), hovertemplate="%{y} scam/fraud"))
    fig.update_layout(title=f"เหตุการณ์ AI ก่อปัญหาต่อปี (ปี {latest_year} ยังไม่ครบ — สีจาง)")
    return style_fig(fig, height=400)


def aiid_risk(risk: pd.DataFrame) -> go.Figure:
    order = risk.groupby("risk_domain")["n"].sum().sort_values().index
    fig = go.Figure()
    palette = {"Intentional": C["scam"], "Unintentional": C["freedom"], "Other": "#C9A227", "ยังไม่จัดหมวด": "#CFCCC4"}
    for intent in ("Intentional", "Unintentional", "Other", "ยังไม่จัดหมวด"):
        d = risk[risk["intent"] == intent].set_index("risk_domain").reindex(order).fillna(0)
        fig.add_trace(go.Bar(y=d.index, x=d["n"], orientation="h", name={"Intentional": "ตั้งใจ", "Unintentional": "ไม่ตั้งใจ",
                                                                         "Other": "อื่น ๆ"}.get(intent, intent),
                             marker_color=palette[intent], hovertemplate="%{y}: %{x}"))
    fig.update_layout(barmode="stack", title="ประเภทความเสี่ยง (MIT) แยกตามเจตนา", hovermode="closest")
    return style_fig(fig, height=400)


def aiid_growth(g: pd.DataFrame) -> go.Figure:
    d = g.dropna(subset=["new"])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=d["snapshot"], y=d["new"] - d["new_with_old_event_date"], name="เกิดเหตุในช่วง 60 วันก่อนฉบับนั้น",
                         marker_color=C["ai"]))
    fig.add_trace(go.Bar(x=d["snapshot"], y=d["new_with_old_event_date"], name="เหตุการณ์เก่าที่เพิ่งถูกบันทึก (>60 วัน)",
                         marker_color="#E3CFE4"))
    fig.update_layout(barmode="stack", title="เหตุการณ์ใหม่ที่เพิ่มเข้าฐานข้อมูลในแต่ละสัปดาห์")
    return style_fig(fig, height=340)


# ---------------------------------------------------------------- FOTN


def fotn_asean(fotn: pd.DataFrame) -> go.Figure:
    a = fotn[fotn["iso3"].isin(config.ASEAN)]
    fig = go.Figure()
    for iso, name in config.ASEAN.items():
        d = a[a["iso3"] == iso].sort_values("data_year")
        if d.empty:
            continue
        is_th = iso == "THA"
        fig.add_trace(go.Scatter(x=d["data_year"], y=d["total_score"], name=name, mode="lines+markers" if is_th else "lines",
                                 line=dict(color=C["freedom"] if is_th else "#B9B6AE", width=4 if is_th else 1.6),
                                 hovertemplate=name + ": %{y}"))
        fig.add_annotation(x=d["data_year"].iloc[-1], y=d["total_score"].iloc[-1], text=name, showarrow=False, xanchor="left",
                           xshift=6, font=dict(size=11, color=C["freedom"] if is_th else C["muted"]))
    fig.add_hrect(y0=0, y1=39.5, fillcolor="#C0392B", opacity=0.05, line_width=0)
    fig.add_hrect(y0=39.5, y1=69.5, fillcolor="#D4A017", opacity=0.05, line_width=0)
    fig.add_hrect(y0=69.5, y1=100, fillcolor="#1E8C7E", opacity=0.05, line_width=0)
    fig.update_layout(title="คะแนนเสรีภาพอินเทอร์เน็ต ไทยเทียบอาเซียน (ยิ่งสูงยิ่งเสรี)", showlegend=False,
                      margin=dict(r=70))
    fig.update_yaxes(range=[0, 100], title="คะแนน (0–100)")
    return style_fig(fig, height=400, legend_bottom=False)


def fotn_components(th_row: pd.Series) -> go.Figure:
    items = [("สิทธิผู้ใช้", th_row["violations_of_user_rights"], 40), ("การจำกัดเนื้อหา", th_row["limits_on_content"], 35),
             ("อุปสรรคการเข้าถึง", th_row["obstacles_to_access"], 25)]
    fig = go.Figure(go.Bar(y=[i[0] for i in items], x=[i[1] / i[2] * 100 for i in items], orientation="h", marker_color=C["freedom"],
                           text=[f"{i[1]:.0f}/{i[2]}" for i in items], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:.0f}% ของคะแนนเต็ม<extra></extra>"))
    fig.update_xaxes(range=[0, 100], title="% ของคะแนนเต็มของส่วนนั้น")
    fig.update_layout(title=f"ไทย ปี {int(th_row['data_year'])}: 3 ส่วนของคะแนน", hovermode="closest")
    return style_fig(fig, height=260, legend_bottom=False)


def fotn_map(fotn: pd.DataFrame, year: int) -> go.Figure:
    y = fotn[fotn["data_year"] == year].copy()
    y["status_th"] = y["status_code"].map(config.STATUS_TH)
    scale = {1: C["global"], 2: C["warn"], 3: C["scam"]}
    fig = go.Figure()
    for code, name in config.STATUS_TH.items():
        d = y[y["status_code"] == code]
        fig.add_trace(go.Choropleth(locations=d["iso3"], z=[1] * len(d), showscale=False, name=name, showlegend=True,
                                    colorscale=[[0, scale[code]], [1, scale[code]]], marker_line_color="white",
                                    customdata=np.stack([d["country"], d["total_score"]], axis=-1),
                                    hovertemplate="%{customdata[0]}<br>" + name + " · %{customdata[1]} คะแนน<extra></extra>"))
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth", bgcolor="rgba(0,0,0,0)",
                    landcolor="#ECE9E1", showcountries=False)
    fig.update_layout(title=f"สถานะเสรีภาพอินเทอร์เน็ต ปี {year} (เทาอ่อน = ไม่มีข้อมูล ไม่ใช่ 0 คะแนน)", hovermode="closest")
    return style_fig(fig, height=420)


def fotn_change(ch: pd.DataFrame, n: int = 8) -> go.Figure:
    d = pd.concat([ch.head(n), ch.tail(n)]).drop_duplicates("country").sort_values("change")
    fig = go.Figure(go.Bar(y=d["country"], x=d["change"], orientation="h",
                           marker_color=[C["scam"] if v < 0 else C["global"] for v in d["change"]],
                           text=[f"{v:+.0f}" for v in d["change"]], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:+.0f} คะแนน<extra></extra>"))
    fig.update_layout(title="ประเทศที่คะแนนเปลี่ยนมากที่สุด", hovermode="closest")
    return style_fig(fig, height=420, legend_bottom=False)


# ---------------------------------------------------------------- EUvsDisinfo


def eu_yearly(y: pd.DataFrame) -> go.Figure:
    colors = ["#A5D4CD" if p else C["global"] for p in y["partial_year"]]
    fig = go.Figure(go.Bar(x=y["year"].astype(str), y=y["debunks"], marker_color=colors,
                           hovertemplate="%{y:,} การหักล้าง<extra></extra>"))
    last = y.loc[y["partial_year"], "year"]
    suffix = f" (ปี {int(last.iloc[0])} มีข้อมูลถึง ส.ค. — สีจาง)" if len(last) else ""
    fig.update_layout(title="จำนวนการหักล้างที่ไม่ซ้ำ ต่อปี" + suffix, hovermode="closest")
    return style_fig(fig, height=340, legend_bottom=False)


def eu_keywords(k: pd.DataFrame, top: int = 15) -> go.Figure:
    d = k.groupby("keyword")["debunks"].sum().nlargest(top).reset_index()
    return hbar(d, "debunks", "keyword", C["global"], "ประเด็น/เรื่องเล่าที่พบบ่อย (นับต่อการหักล้างที่ไม่ซ้ำ)", height=440)


# ---------------------------------------------------------------- analysis charts


def loss_waterfall(d) -> go.Figure:
    fig = go.Figure(go.Waterfall(
        x=["ช่วงสูงสุด", "ผลจากจำนวนคดี", "ผลจากความเสียหายต่อคดี", "ช่วงต่ำสุด"],
        measure=["absolute", "relative", "relative", "total"],
        y=[d.loss_peak / 1e6, d.cases_effect / 1e6, d.severity_effect / 1e6, d.loss_trough / 1e6],
        text=[f"{v:,.0f}" for v in (d.loss_peak / 1e6, d.cases_effect / 1e6, d.severity_effect / 1e6, d.loss_trough / 1e6)],
        textposition="outside", connector=dict(line=dict(color=C["grid"])),
        increasing=dict(marker_color=C["global"]), decreasing=dict(marker_color=C["scam"]), totals=dict(marker_color=C["muted"]),
        hovertemplate="%{x}: %{y:,.0f} ล้านบาท/สัปดาห์<extra></extra>"))
    fig.update_layout(title="แยกส่วนการลดลงของความเสียหายรายสัปดาห์ (ล้านบาท/สัปดาห์)", hovermode="closest", showlegend=False)
    return style_fig(fig, height=360, legend_bottom=False)


def change_point_chart(u: pd.DataFrame, cp_cases, cp_lpc) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("คดีต่อสัปดาห์", "ความเสียหายต่อคดี (บาท)"))
    for row, col, cp, color in ((1, "acsc_cases", cp_cases, C["scam"]), (2, "acsc_loss_per_case_calc", cp_lpc, C["scam"])):
        x = u["week_start"].map(_iso)
        fig.add_trace(go.Scatter(x=x, y=u[col], mode="lines+markers", line=dict(color=color, width=1.8), marker=dict(size=4),
                                 showlegend=False, hovertemplate="%{y:,.0f}"), row=row, col=1)
        if cp:
            k = cp.index
            fig.add_trace(go.Scatter(x=x.iloc[:k], y=[cp.mean_before] * k, mode="lines", line=dict(color=C["ink"], dash="dash", width=2),
                                     showlegend=False, hovertemplate="เฉลี่ยก่อน: %{y:,.0f}"), row=row, col=1)
            fig.add_trace(go.Scatter(x=x.iloc[k:], y=[cp.mean_after] * (len(x) - k), mode="lines", line=dict(color=C["ink"], dash="dash", width=2),
                                     showlegend=False, hovertemplate="เฉลี่ยหลัง: %{y:,.0f}"), row=row, col=1)
            fig.add_shape(type="line", x0=_iso(cp.date), x1=_iso(cp.date), y0=0, y1=1, yref="y domain" if row == 1 else "y2 domain",
                          xref="x" if row == 1 else "x2", line=dict(color=C["warn"], width=2))
    fig.update_yaxes(rangemode="tozero")
    for a in fig.layout.annotations:
        a.update(x=0, xanchor="left", font=dict(size=13))
    fig.update_layout(title="จุดเปลี่ยนที่ชัดที่สุด (เส้นประ = ค่าเฉลี่ยก่อน/หลัง · เส้นเหลือง = จุดแบ่ง)")
    return style_fig(fig, height=460, legend_bottom=False)


def lag_chart(lag: pd.DataFrame) -> go.Figure:
    ci = float(lag["ci95"].mean())
    fig = go.Figure(go.Bar(x=lag["lag"], y=lag["r"], marker_color=[C["fake"] if s else "#CFCCC4" for s in lag["significant"]],
                           customdata=lag[["n", "ci95"]].to_numpy(), hovertemplate="lag %{x} สัปดาห์: r = %{y:+.2f} (n=%{customdata[0]}, เกณฑ์ ±%{customdata[1]:.2f})<extra></extra>"))
    fig.add_hrect(y0=-ci, y1=ci, fillcolor="#999", opacity=0.12, line_width=0)
    fig.update_layout(title="สหสัมพันธ์ของการเปลี่ยนแปลงรายสัปดาห์: สัดส่วนข่าวเท็จ ↔ จำนวนคดี", hovermode="closest",
                      xaxis=dict(title="lag (สัปดาห์) · บวก = ข่าวเท็จนำหน้าคดี", dtick=1), yaxis=dict(title="r", range=[-0.6, 0.6]))
    return style_fig(fig, height=340, legend_bottom=False)


def residual_heatmap(ms) -> go.Figure:
    r = ms.residuals
    fig = go.Figure(go.Heatmap(z=r.to_numpy(), x=list(r.columns), y=[str(i) for i in r.index], zmid=0, colorscale="RdBu_r", zmin=-12, zmax=12,
                               text=r.round(1).to_numpy(), texttemplate="%{text}", hovertemplate="%{y} · %{x}: %{z:+.1f}<extra></extra>",
                               colorbar=dict(title="เกิน/ขาด<br>จากที่คาด")))
    fig.update_layout(title="หมวดข่าวเท็จที่ 'เกิน' (แดง) หรือ 'ขาด' (น้ำเงิน) เมื่อเทียบกับการกระจายเฉลี่ย 2020–2025", hovermode="closest")
    fig.update_yaxes(autorange="reversed")
    return style_fig(fig, height=360, legend_bottom=False)


def scam_tag_share(sh: pd.DataFrame) -> go.Figure:
    d = sh[sh["year"] >= 2020]
    fig = go.Figure(go.Scatter(x=d["year"], y=d["scam_share_of_tagged_pct"], mode="lines+markers", line=dict(color=C["scam"], width=3),
                               customdata=d[["scam_tagged", "tagged"]].to_numpy(),
                               hovertemplate="%{y:.1f}% (%{customdata[0]:,} จาก %{customdata[1]:,} เรื่อง)<extra></extra>"))
    fig.update_layout(title="ข่าวเท็จที่เกี่ยวกับการแอบอ้าง/หลอกลวง (% ของข่าวเท็จที่มีแท็ก)", hovermode="closest",
                      yaxis=dict(range=[0, 50], title="%"), xaxis=dict(dtick=1))
    return style_fig(fig, height=340, legend_bottom=False)


def asean_bars(table: pd.DataFrame, median_others: float) -> go.Figure:
    d = table.sort_values("total_score")
    colors = [C["freedom"] if c == "Thailand" else "#B9B6AE" for c in d["country"]]
    fig = go.Figure(go.Bar(y=d["country"], x=d["total_score"], orientation="h", marker_color=colors, text=d["total_score"], textposition="outside",
                           cliponaxis=False, hovertemplate="%{y}: %{x} คะแนน<extra></extra>"))
    fig.add_vline(x=median_others, line_dash="dot", line_color=C["ink"], annotation_text=f"มัธยฐานประเทศอื่น {median_others:.0f}", annotation_position="top")
    fig.update_xaxes(range=[0, 100])
    fig.update_layout(title="คะแนนรวมอาเซียน (ปีล่าสุด)", hovermode="closest")
    return style_fig(fig, height=340, legend_bottom=False)
