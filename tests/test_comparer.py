from backend.core.comparer import compare_transcripts


def test_weekly_pair_comparison(sample, settings):
    """week1 vs week2 transcripts -> renewal endpoint completed, login bug unresolved/open, CI pipeline is new"""
    sa, sb, r = compare_transcripts(sample("weekly_pair_week1.txt"), sample("weekly_pair_week2.txt"), settings)
    completed = [m.action.task for m in r.by_status("completed")]
    assert any("renewal API endpoint" in t for t in completed)
    open_tasks = [m.action.task for m in r.actions if m.status in ("unresolved", "still_open", "uncertain")]
    assert any("login timeout" in t for t in open_tasks)
    assert any("CI pipeline" in x.task for x in r.new_actions)
    assert all(m.reason for m in r.actions)  # every match is explained


def test_carried_over_question(sample, settings):
    """demo-room question asked in both weeks -> reported as carried-over"""
    _, _, r = compare_transcripts(sample("weekly_pair_week1.txt"), sample("weekly_pair_week2.txt"), settings)
    assert any("demo room" in q[0] for q in r.carried_questions)


def test_identical_meetings_have_no_new_actions(sample, settings):
    """same transcript twice -> no new actions, nothing completed"""
    _, _, r = compare_transcripts(sample("short_meeting.txt"), sample("short_meeting.txt"), settings)
    assert r.new_actions == [] and not r.by_status("completed")
