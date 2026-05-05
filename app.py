from __future__ import annotations

import streamlit as st

import auth
import data
import theme as T
from seed import seed_if_empty
from views import activity, audit_plan, dashboard, executive, exports, team

st.set_page_config(
    page_title="Ledger · Internal Audit",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(T.CSS, unsafe_allow_html=True)


def _ensure_initialized() -> None:
    data.get_engine()
    if seed_if_empty():
        st.toast("Seeded sample workspace.", icon="◆")


def _render_sidebar(role: str, username: str) -> str:
    with st.sidebar:
        st.markdown(
            f'<div class="ledger-brand">'
            f'<div class="crest">L</div>'
            f'<div><div class="name">Ledger</div>'
            f'<div class="tag">Audit Planning</div></div></div>',
            unsafe_allow_html=True,
        )

        editor_tabs = ["Dashboard", "Audit Plan", "Team", "Executive", "Activity", "Export"]
        viewer_tabs = ["Dashboard", "Executive"]
        tabs = editor_tabs if role == "editor" else viewer_tabs

        if "tab" not in st.session_state or st.session_state.tab not in tabs:
            st.session_state.tab = tabs[0]

        for tab in tabs:
            if st.button(tab, key=f"nav_{tab}", use_container_width=True,
                         type="primary" if st.session_state.tab == tab else "secondary"):
                st.session_state.tab = tab
                st.rerun()

        st.markdown("---")
        st.markdown(
            f'<div style="font-size:11px;color:{T.TEXT_MUTED}">Signed in as</div>'
            f'<div style="font-size:13px;font-weight:700;color:{T.INK}">{username}</div>'
            f'<div style="font-size:10px;color:{T.TEXT_DIM};text-transform:uppercase;'
            f'letter-spacing:1px;margin-top:2px">{role}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign out", use_container_width=True):
            for k in ("authentication_status", "name", "username"):
                st.session_state.pop(k, None)
            st.rerun()

        return st.session_state.tab


def _render_header(tab: str) -> None:
    subs = {
        "Dashboard": "High-level snapshot with full 52-week capacity view",
        "Audit Plan": "Manage active audits, allocate hours, and edit engagements",
        "Team": "Team roster, utilization, and availability",
        "Executive": "Audit Committee status report",
        "Activity": "Audit trail of changes made to this workspace",
        "Export": "Download Excel workbooks for any view",
    }
    st.markdown(
        f'<h1 style="margin-bottom:0">{tab}</h1>'
        f'<p style="margin-top:2px;color:{T.TEXT_DIM};font-size:13px">{subs.get(tab, "")}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")


def main() -> None:
    _ensure_initialized()
    authenticator = auth.get_authenticator()
    name, status, username = auth.render_login(authenticator)

    if status is False:
        st.error("Username/password incorrect.")
        return
    if status is None:
        st.info("Please sign in to continue.")
        return

    role = auth.get_role(username)
    tab = _render_sidebar(role, name)
    _render_header(tab)

    audits = data.list_audits()
    members = data.list_members()
    activity_entries = data.list_activity()

    view_map = {
        "Dashboard": dashboard.render,
        "Audit Plan": audit_plan.render,
        "Team": team.render,
        "Executive": executive.render,
        "Activity": activity.render,
        "Export": exports.render,
    }
    view_map[tab](audits, members, activity_entries, role)


if __name__ == "__main__":
    main()
