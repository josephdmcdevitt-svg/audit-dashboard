from __future__ import annotations

import pandas as pd
import streamlit as st

import data
import theme as T
from helpers import GREEN_THRESHOLD, LEVELS, WEEK_HOURS, member_week_hours, week_keys


def render(audits, members, activity, role: str) -> None:
    weeks = week_keys()
    is_editor = role == "editor"
    mwh = member_week_hours(audits, members, weeks)
    current_week = weeks[0]

    if is_editor:
        cols = st.columns([6, 1])
        if cols[1].button("＋ Add Person", type="primary", use_container_width=True):
            st.session_state["edit_member_id"] = "__new__"
            st.rerun()

    sorted_members = sorted(members, key=lambda m: (LEVELS.index(m.level) if m.level in LEVELS else 99, m.name))

    rows = []
    for m in sorted_members:
        this_week = mwh.get(m.id, {}).get(current_week, 0)
        annual = sum(mwh.get(m.id, {}).get(w, 0) for w in weeks)
        assigned = ", ".join(a.name for a in audits if any(asgn.member_id == m.id for asgn in a.assignments))
        status = "Overloaded" if this_week > WEEK_HOURS else "Available" if this_week < GREEN_THRESHOLD else "Utilized"
        rows.append({
            "Name": m.name,
            "Level": m.level,
            "Email": m.email or "",
            "This Week": f"{this_week}h / {WEEK_HOURS}h",
            "Annual": f"{annual:,}h",
            "Status": status,
            "Assigned Audits": assigned or "-",
            "_id": m.id,
        })
    df = pd.DataFrame(rows)

    def color_status(v):
        if v == "Overloaded":
            return f"background-color:{T.DANGER};color:white;font-weight:700;text-align:center"
        if v == "Available":
            return f"background-color:{T.SUCCESS};color:white;font-weight:700;text-align:center"
        return f"background-color:{T.WARNING};color:white;font-weight:700;text-align:center"

    display = df.drop(columns=["_id"])
    st.dataframe(
        display.style.map(color_status, subset=["Status"]),
        use_container_width=True, hide_index=True,
        column_config={
            "Name": st.column_config.TextColumn(width="medium"),
            "Email": st.column_config.TextColumn(width="medium"),
            "Assigned Audits": st.column_config.TextColumn(width="large"),
        },
    )

    if is_editor and members:
        st.write("")
        st.markdown("##### Manage individual members")
        cols = st.columns([3, 1, 1])
        sel = cols[0].selectbox(
            "Select member",
            options=sorted_members, format_func=lambda m: f"{m.name} ({m.level})",
            label_visibility="collapsed",
        )
        if cols[1].button("Edit", use_container_width=True, key="team_edit_btn"):
            st.session_state["edit_member_id"] = sel.id
            st.rerun()
        if cols[2].button("Remove", use_container_width=True, key="team_remove_btn"):
            st.session_state["delete_member_id"] = sel.id
            st.rerun()

    edit_id = st.session_state.get("edit_member_id")
    if edit_id:
        _member_edit_dialog(edit_id)
    delete_id = st.session_state.get("delete_member_id")
    if delete_id:
        _member_delete_dialog(delete_id)



@st.dialog("Team member")
def _member_edit_dialog(member_id: str):
    is_new = member_id == "__new__"
    m = None if is_new else next((x for x in data.list_members() if x.id == member_id), None)
    if not is_new and m is None:
        st.error("Member not found.")
        if st.button("Close"):
            st.session_state.pop("edit_member_id", None)
            st.rerun()
        return

    st.markdown(f"### {'Add Team Member' if is_new else 'Edit Team Member'}")
    with st.form("member_form"):
        name = st.text_input("Full name", value="" if is_new else m.name)
        email = st.text_input("Email", value="" if is_new else (m.email or ""), placeholder="name@walgreens.com")
        c1, c2 = st.columns(2)
        level = c1.selectbox("Level", LEVELS, index=LEVELS.index("Staff") if is_new else LEVELS.index(m.level))
        hours = c2.number_input("Hours/week", min_value=0, max_value=80, value=40 if is_new else m.hours_per_week, step=5)

        save_col, cancel_col = st.columns(2)
        save = save_col.form_submit_button("Add Member" if is_new else "Save", type="primary", use_container_width=True)
        cancel = cancel_col.form_submit_button("Cancel", use_container_width=True)

    if cancel:
        st.session_state.pop("edit_member_id", None)
        st.rerun()
    if save:
        if not name.strip():
            st.error("Name is required.")
            return
        fields = dict(name=name.strip(), email=email.strip() or None, level=level, hours_per_week=int(hours))
        if is_new:
            data.upsert_member(None, **fields)
            data.log_activity("Added Team Member", name, st.session_state.get("name", "Editor"))
        else:
            data.upsert_member(member_id, **fields)
            data.log_activity("Updated Team Member", name, st.session_state.get("name", "Editor"))
        st.session_state.pop("edit_member_id", None)
        st.rerun()


@st.dialog("Remove team member?")
def _member_delete_dialog(member_id: str):
    m = next((x for x in data.list_members() if x.id == member_id), None)
    if m is None:
        st.session_state.pop("delete_member_id", None)
        st.rerun()
        return
    st.markdown(f"**{T.safe(m.name)}** will be removed from the roster and unassigned from every audit.")
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True):
        st.session_state.pop("delete_member_id", None)
        st.rerun()
    if c2.button("Remove", use_container_width=True, type="primary"):
        data.delete_member(member_id)
        data.log_activity("Removed Team Member", m.name, st.session_state.get("name", "Editor"))
        st.session_state.pop("delete_member_id", None)
        st.rerun()
