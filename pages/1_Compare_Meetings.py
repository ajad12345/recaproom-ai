"""Compare two meetings: which actions are completed, still open, unresolved or new."""
import streamlit as st

from backend.core.comparer import compare_transcripts
from backend.services.llm_service import LLMError
from backend.utils.logging_utils import get_logger
from backend.utils.samples import list_samples, read_sample
from backend.utils.validators import validate_text_input
from components.sidebar import render_sidebar

st.set_page_config(page_title="Compare Meetings · RecapRoom AI", page_icon="🔁", layout="wide")
log = get_logger("compare_page")
settings = render_sidebar()

st.title("🔁 Compare Two Meetings")
st.write("Find out which action items from **Meeting A** were completed, are still open, or have no follow-up in "
         "**Meeting B**, and which actions are new. Matching is rule-based and explained; weak matches are "
         "flagged as *uncertain* instead of being forced.")
st.session_state.setdefault("cmp_a", read_sample("weekly_pair_week1.txt"))
st.session_state.setdefault("cmp_b", read_sample("weekly_pair_week2.txt"))


def _load(key: str, picker: str):
    choice = st.session_state.get(picker)
    if choice and choice != "—":
        st.session_state[key] = read_sample(choice)


col_a, col_b = st.columns(2)
for col, label, key in ((col_a, "Meeting A (earlier)", "cmp_a"), (col_b, "Meeting B (later)", "cmp_b")):
    with col:
        st.selectbox(f"Load sample for {label}", ["—"] + list_samples(), key=f"{key}_pick",
                     on_change=_load, args=(key, f"{key}_pick"))
        st.text_area(label, key=key, height=260)

if st.button("Compare meetings", type="primary"):
    try:
        text_a, _ = validate_text_input(st.session_state["cmp_a"])
        text_b, _ = validate_text_input(st.session_state["cmp_b"])
        bar = st.progress(0.0, text="Working…")
        with st.spinner("Summarising both meetings…"):
            sa, sb, res = compare_transcripts(text_a, text_b, settings,
                                              progress=lambda d, t, m: bar.progress(min(d / t, 1.0), text=m))
        bar.empty()
        st.session_state["cmp_result"] = (sa, sb, res)
    except ValueError as err:
        st.warning(str(err))
    except LLMError as err:
        st.error(str(err))
        st.info("Tip: switch to **Demo Mode** in the sidebar.")
    except Exception:  # noqa: BLE001
        log.exception("Comparison failed")
        st.error("Something went wrong. Please try again.")

if "cmp_result" in st.session_state:
    sa, sb, res = st.session_state["cmp_result"]
    st.divider()
    if sa.meta.mode == "DEMO":
        st.info("🟠 **DEMO MODE**: summaries were produced by simple rules.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Completed", len(res.by_status("completed")))
    m2.metric("Still open / repeated", len(res.by_status("still_open")))
    m3.metric("Unresolved", len(res.by_status("unresolved")))
    m4.metric("New in Meeting B", len(res.new_actions))

    icons = {"completed": "✅ Completed", "still_open": "🔁 Still open", "unresolved": "❗ Unresolved", "uncertain": "⚠️ Uncertain match"}
    st.subheader("Actions from Meeting A")
    if res.actions:
        st.dataframe([{"Status": icons[m.status], "Action (A)": m.action.task, "Owner": m.action.owner,
                       "Deadline": m.action.deadline, "Matched in B": m.matched_text or "—",
                       "Similarity": round(m.score), "Why": m.reason} for m in res.actions],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("Meeting A has no action items.")
    if res.by_status("uncertain"):
        st.warning("Some matches are uncertain. Check them against the transcripts.")

    st.subheader("New actions in Meeting B")
    if res.new_actions:
        st.dataframe([{"Action": a.task, "Owner": a.owner, "Deadline": a.deadline} for a in res.new_actions],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("No new actions.")

    st.subheader("Open questions carried over")
    if res.carried_questions:
        st.dataframe([{"Meeting A": a, "Meeting B": b, "Similarity": round(s)} for a, b, s in res.carried_questions],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("No open question appears in both meetings.")

    st.subheader("Decisions that may have changed")
    if res.changed_decisions:
        st.dataframe([{"Meeting A": a, "Meeting B": b, "Similarity": round(s)} for a, b, s in res.changed_decisions],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("No similar-but-different decisions found.")
    st.caption("AI-generated comparisons can be wrong. Verify against the original transcripts.")
