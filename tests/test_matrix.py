from rtm.matrix import build_traceability


def test_build_traceability_row_count(sample_requirements, sample_stories, sample_test_cases):
    rows = build_traceability(sample_requirements, sample_stories, sample_test_cases)
    # R1->S1->T1, R1->S1->T2, R1->S2->(none), R2->S3->T3, R3->(none)->(none)
    assert len(rows) == 5


def test_build_traceability_orphan_requirement_has_null_story_and_test(
    sample_requirements, sample_stories, sample_test_cases
):
    rows = build_traceability(sample_requirements, sample_stories, sample_test_cases)
    r3_rows = [r for r in rows if r.requirement.requirement_id == "R3"]
    assert len(r3_rows) == 1
    assert r3_rows[0].story is None
    assert r3_rows[0].test_case is None
    assert r3_rows[0].execution_status == "no_test_case"


def test_build_traceability_orphan_story_has_null_test(
    sample_requirements, sample_stories, sample_test_cases
):
    rows = build_traceability(sample_requirements, sample_stories, sample_test_cases)
    s2_rows = [r for r in rows if r.story and r.story.story_id == "S2"]
    assert len(s2_rows) == 1
    assert s2_rows[0].test_case is None


def test_build_traceability_full_chain_row_fields(
    sample_requirements, sample_stories, sample_test_cases
):
    rows = build_traceability(sample_requirements, sample_stories, sample_test_cases)
    t1_rows = [r for r in rows if r.test_case and r.test_case.test_case_id == "T1"]
    assert len(t1_rows) == 1
    row = t1_rows[0]
    assert row.requirement.requirement_id == "R1"
    assert row.story.story_id == "S1"
    assert row.execution_status == "passed"
    d = row.as_dict
    assert d["requirement_id"] == "R1"
    assert d["story_id"] == "S1"
    assert d["test_case_id"] == "T1"
    assert d["execution_status"] == "passed"


def test_build_traceability_empty_inputs():
    assert build_traceability([], [], []) == []
