"""Page CSS and the shared Plotly layout."""
from __future__ import annotations

import config

FONT = "'Noto Sans Thai', 'Sarabun', 'Segoe UI', sans-serif"
C = config.COLORS

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button {{ font-family: {FONT}; }}
.stApp {{ background: {C['paper']}; }}
.block-container {{ padding-top: 1rem; max-width: 1400px; }}
h1, h2, h3, h4 {{ color: {C['ink']}; letter-spacing: -0.01em; }}
h3 {{ font-size: 1.05rem !important; font-weight: 700; margin: .9rem 0 .4rem; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* top bar */
.topbar {{ background: {C['scam']}; color: #fff; border-radius: 10px; padding: .7rem 1.1rem; margin-bottom: .9rem;
           display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; }}
.topbar .t {{ font-size: 1.15rem; font-weight: 700; }}
.topbar .s {{ font-size: .78rem; opacity: .85; }}

/* sidebar */
section[data-testid="stSidebar"] {{ background: {C['scam']}; }}
section[data-testid="stSidebar"] * {{ color: #fff !important; }}
section[data-testid="stSidebar"] .brand {{ font-weight: 700; font-size: 1.05rem; padding: .3rem .2rem .8rem;
           border-bottom: 1px solid rgba(255,255,255,.25); margin-bottom: .6rem; }}
section[data-testid="stSidebar"] div[role="radiogroup"] {{ gap: .15rem; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label {{ padding: .5rem .7rem; border-radius: 8px; width: 100%; cursor: pointer; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div > div:first-child {{ display: none; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{ background: rgba(255,255,255,.12); }}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] {{ background: #fff; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] * {{ color: {C['scam']} !important; font-weight: 700; }}
section[data-testid="stSidebar"] button {{ background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.4); }}

/* cards: every chart / table sits on a white rounded card */
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {{ background: #fff; border: 1px solid {C['grid']}; border-radius: 12px;
           padding: .5rem .6rem; box-shadow: 0 1px 2px rgba(60,20,30,.05); }}
.kpi {{ background: #fff; border: 1px solid {C['grid']}; border-radius: 12px; padding: .7rem .8rem; height: 100%;
        display: flex; gap: .65rem; align-items: flex-start; box-shadow: 0 1px 2px rgba(60,20,30,.05); }}
.kpi .ic {{ flex: 0 0 38px; height: 38px; border-radius: 50%; border: 2px solid var(--accent, {C['scam']}); color: var(--accent, {C['scam']});
            display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .95rem; }}
.kpi .body {{ min-width: 0; }}
.kpi .label {{ font-size: .74rem; color: {C['muted']}; font-weight: 500; }}
.kpi .value {{ white-space: nowrap; font-size: 1.45rem; font-weight: 700; color: {C['ink']}; line-height: 1.2; }}
.kpi .delta {{ font-size: .74rem; margin-top: .1rem; color: {C['muted']}; }}
.kpi .delta.up {{ color: {C['scam']}; }}
.kpi .delta.down {{ color: {C['global']}; }}
.find {{ background: #fff; border: 1px solid {C['grid']}; border-left: 4px solid {C['scam']}; border-radius: 10px;
         padding: .6rem .8rem; font-size: .88rem; font-weight: 600; min-height: 4.2rem; height: 100%; color: {C['ink']}; margin-bottom: .5rem; }}
.find .n {{ color: {C['scam']}; font-weight: 700; margin-right: .3rem; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] .filterbar) {{ background: #fff; border-radius: 12px; border: 1px solid {C['grid']}; }}
.filterbar {{ font-size: .72rem; color: {C['muted']}; margin: 0 0 .2rem; }}
.note {{ background: #fff8e6; border-left: 4px solid {C['warn']}; padding: .55rem .8rem; border-radius: 6px;
         font-size: .85rem; color: #5a4a14; margin: .4rem 0 .8rem; }}
.note.info {{ background: #f3eef0; border-left-color: {C['scam']}; color: #4a2a35; }}
.read {{ color: {C['muted']}; font-size: .82rem; margin: -.2rem 0 .9rem; }}
.source {{ color: {C['muted']}; font-size: .75rem; margin-top: .3rem; }}
@media (max-width: 640px) {{ .kpi .value {{ font-size: 1.3rem; }} .topbar .t {{ font-size: 1rem; }} }}
</style>
"""


def style_fig(fig, height: int = 380, legend_bottom: bool = True):
    fig.update_layout(
        height=height, font=dict(family=FONT, size=13, color=C["ink"]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=36, b=10), hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0) if legend_bottom else dict(),
        title=dict(font=dict(size=15), x=0, xanchor="left"),
    )
    fig.update_xaxes(showgrid=False, linecolor=C["grid"], zeroline=False)
    fig.update_yaxes(gridcolor=C["grid"], zeroline=False)
    return fig
