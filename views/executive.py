from __future__ import annotations

from datetime import date
import streamlit as st
import theme as T
from helpers import BUSINESS_UNITS, traffic_light_status


def render(audits, members, activity, role: str) -> None:
    today = date.today()

    counts = {"Green": 0, "Yellow": 0, "Red": 0}
    for a in audits:
        counts[traffic_light_status(a)] += 1

    st.markdown(
        f'<div style="padding:26px 28px;background:linear-gradient(135deg,{T.INK} 0%,#2d3d58 100%);'
        f'color:{T.PAPER};border-radius:14px;margin-bottom:18px">'
        f'<div style="font-family:Georgia,serif;font-size:22px;font-weight:600;letter-spacing:-0.3px">'
        f'Executive Summary</div>'
        f'<div style="color:#c9c0a8;font-size:13px;margin-top:4px">'
        f'Audit Committee status · {today.strftime("%B %-d, %Y")}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:22px">'
        f'<div style="text-align:center;padding:18px;background:rgba(255,255,255,0.05);border-radius:10px;border:1px solid {T.SUCCESS}66">'
        f'<div style="font-family:Georgia,serif;font-size:42px;font-weight:500;color:#8ab39a;line-height:1">{counts["Green"]}</div>'
        f'<div style="font-size:10px;color:#c9c0a8;text-transform:uppercase;font-weight:700;letter-spacing:1px;margin-top:6px">On Track</div></div>'
        f'<div style="text-align:center;padding:18px;background:rgba(255,255,255,0.05);border-radius:10px;border:1px solid {T.WARNING}66">'
        f'<div style="font-family:Georgia,serif;font-size:42px;font-weight:500;color:#d4a755;line-height:1">{counts["Yellow"]}</div>'
        f'<div style="font-size:10px;color:#c9c0a8;text-transform:uppercase;font-weight:700;letter-spacing:1px;margin-top:6px">Monitoring</div></div>'
        f'<div style="text-align:center;padding:18px;background:rgba(255,255,255,0.05);border-radius:10px;border:1px solid {T.DANGER}66">'
        f'<div style="font-family:Georgia,serif;font-size:42px;font-weight:500;color:#c97a68;line-height:1">{counts["Red"]}</div>'
        f'<div style="font-size:10px;color:#c9c0a8;text-transform:uppercase;font-weight:700;letter-spacing:1px;margin-top:6px">At Risk</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # By Business Unit
    st.markdown('<div class="ledger-card">', unsafe_allow_html=True)
    st.markdown("#### Active Audits, Status by Business Unit")
    by_bu = [(bu, [a for a in audits if a.business_unit == bu]) for bu in BUSINESS_UNITS]
    by_bu = [(bu, items) for bu, items in by_bu if items]
    light_color = {"Red": T.DANGER, "Yellow": T.WARNING, "Green": T.SUCCESS}
    for bu, items in by_bu:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:14px 0 8px">'
            f'<div style="font-size:12px;font-weight:700;color:{T.PRIMARY};text-transform:uppercase;letter-spacing:0.8px">{bu}</div>'
            f'<div style="flex:1;height:1px;background:{T.BORDER}"></div>'
            f'<div style="font-size:11px;color:{T.TEXT_MUTED}">{len(items)} audit{"s" if len(items) > 1 else ""}</div></div>',
            unsafe_allow_html=True,
        )
        for a in items:
            l = traffic_light_status(a)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:12px;padding:10px 12px;'
                f'background:{T.PAPER_ALT};border-radius:8px;margin-bottom:6px;border:1px solid {T.BORDER}">'
                f'<div style="width:12px;height:12px;border-radius:50%;background:{light_color[l]};'
                f'box-shadow:0 0 12px {light_color[l]}88"></div>'
                f'<div style="flex:1"><div style="font-size:13px;font-weight:600">{T.safe(a.name)}</div>'
                f'<div style="font-size:11px;color:{T.TEXT_MUTED};margin-top:2px">'
                f'{a.phase} · {a.risk_rating} risk · {T.safe(a.owner) or "-"} · {a.completion_pct or 0}% complete</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="ledger-card">', unsafe_allow_html=True)
        st.markdown("#### Plan Metrics")
        active = [a for a in audits if a.phase != "Complete"]
        complete = [a for a in audits if a.phase == "Complete"]
        rows = [
            ("Total Audits in Plan", len(audits)),
            ("Active", len(active)),
            ("Complete", len(complete)),
            ("Critical/High Risk", sum(1 for a in audits if a.risk_rating in ("Critical", "High"))),
            ("Total Hours Budgeted", f"{sum(a.budgeted_hours for a in audits):,}h"),
            ("Team Size", len(members)),
        ]
        for k, v in rows:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {T.BORDER}">'
                f'<span style="font-size:13px;color:{T.TEXT_MUTED}">{k}</span>'
                f'<span style="font-size:13px;font-weight:700;font-family:Menlo,monospace">{v}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="ledger-card">', unsafe_allow_html=True)
        st.markdown("#### Audits by Business Unit")
        for bu in BUSINESS_UNITS:
            cnt = sum(1 for a in audits if a.business_unit == bu)
            if not cnt:
                continue
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {T.BORDER}">'
                f'<span style="font-size:13px;color:{T.TEXT_MUTED}">{bu}</span>'
                f'<span style="font-size:13px;font-weight:700;font-family:Menlo,monospace">{cnt}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

