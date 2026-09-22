from rtm.gaps import (
    build_gap_report,
    find_never_executed_tests,
    find_orphan_requirements,
    find_orphan_stories,
)


def test_find_orphan_requirements(sample_requirements, sample_stories):
    orphans = find_orphan_requirements(sample_requirements, sample_stories)
    assert [o.requirement_id for o in orphans] == ["R3"]
    assert orphans[0].title == "Requirement Three"
    assert orphans[0].priority == "Low"


def test_find_orphan_stories(sample_stories, sample_test_cases):
    orphans = find_orphan_stories(sample_stories, sample_test_cases)
    assert [o.story_id for o in orphans] == ["S2"]
    assert orphans[0].requirement_id == "R1"


def test_find_never_executed_tests(sample_test_cases):
    never_run = find_never_executed_tests(sample_test_cases)
    assert [t.test_case_id for t in never_run] == ["T3"]


def test_build_gap_report_bundles_all_three(
    sample_requirements, sample_stories, sample_test_cases
):
    report = build_gap_report(sample_requirements, sample_stories, sample_test_cases)
    assert len(report.orphan_requirements) == 1
    assert len(report.orphan_stories) == 1
    assert len(report.never_executed_tests) == 1
    assert report.total_findings == 3


def test_no_gaps_when_everything_is_linked_and_run():
    from rtm.models import Requirement, TestCase, UserStory

    reqs = [Requirement("R1", "T", "", "High")]
    stories = [UserStory("S1", "R1", "T")]
    tests = [TestCase("T1", "S1", "T", "passed")]
    report = build_gap_report(reqs, stories, tests)
    assert report.total_findings == 0
    assert report.orphan_requirements == []
    assert report.orphan_stories == []
    assert report.never_executed_tests == []
