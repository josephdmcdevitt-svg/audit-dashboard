from __future__ import annotations

import streamlit as st

import theme as T


def render(audits, members, activity, role: str) -> None:
    st.markdown('<div class="ledger-card">', unsafe_allow_html=True)
    st.markdown("#### Recent Activity")

    if not activity:
        st.caption("No activity recorded yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for e in activity:
        dot_color = T.DANGER if "Delete" in e.action or "Removed" in e.action else (
            T.SUCCESS if "Added" in e.action else T.PRIMARY
        )
        ts = e.timestamp.strftime("%b %-d  %-I:%M %p") if hasattr(e.timestamp, "strftime") else str(e.timestamp)
        st.markdown(
            f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid {T.BORDER};align-items:flex-start">'
            f'<div style="width:8px;height:8px;border-radius:50%;background:{dot_color};margin-top:6px;flex-shrink:0"></div>'
            f'<div style="flex:1">'
            f'<div style="font-size:13px"><b>{e.action}</b>'
            + (f' <span style="color:{T.TEXT_MUTED}">- {e.detail}</span>' if e.detail else "")
            + "</div>"
            f'<div style="font-size:11px;color:{T.TEXT_DIM};margin-top:3px">'
            + (f'<span style="color:{T.TEXT_MUTED};font-weight:600">{e.user} · </span>' if e.user else "")
            + f"{ts}</div></div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

