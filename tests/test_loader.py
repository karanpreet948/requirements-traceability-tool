import pytest
import yaml

from rtm.loader import (
    DataLoadError,
    load_all,
    load_requirements,
    load_test_cases,
    load_user_stories,
)


def _write_yaml(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(yaml.dump(data))
    return path


def test_load_requirements_happy_path(tmp_path):
    path = _write_yaml(
        tmp_path,
        "requirements.yaml",
        {
            "requirements": [
                {"requirement_id": "REQ-1", "title": "Do a thing", "description": "d", "priority": "High"},
                {"requirement_id": "REQ-2", "title": "Do another thing", "priority": "Medium"},
            ]
        },
    )
    reqs = load_requirements(path)
    assert len(reqs) == 2
    assert reqs[0].requirement_id == "REQ-1"
    assert reqs[1].priority == "Medium"


def test_load_requirements_missing_file_raises(tmp_path):
    with pytest.raises(DataLoadError):
        load_requirements(tmp_path / "does_not_exist.yaml")


def test_load_requirements_empty_file_returns_empty_list(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("")
    assert load_requirements(path) == []


def test_load_requirements_skips_malformed_record_without_crashing(tmp_path, caplog):
    path = _write_yaml(
        tmp_path,
        "requirements.yaml",
        {
            "requirements": [
                {"requirement_id": "REQ-1", "title": "Valid one", "priority": "High"},
                "this is not a mapping",
                {"title": "Missing an ID entirely"},
            ]
        },
    )
    reqs = load_requirements(path)
    assert len(reqs) == 1
    assert reqs[0].requirement_id == "REQ-1"


def test_load_requirements_unknown_priority_defaults_to_medium(tmp_path):
    path = _write_yaml(
        tmp_path,
        "requirements.yaml",
        {"requirements": [{"requirement_id": "REQ-1", "title": "T", "priority": "Urgent!"}]},
    )
    reqs = load_requirements(path)
    assert reqs[0].priority == "Medium"


def test_load_requirements_duplicate_id_keeps_first(tmp_path):
    path = _write_yaml(
        tmp_path,
        "requirements.yaml",
        {
            "requirements": [
                {"requirement_id": "REQ-1", "title": "First"},
                {"requirement_id": "REQ-1", "title": "Second (duplicate)"},
            ]
        },
    )
    reqs = load_requirements(path)
    assert len(reqs) == 1
    assert reqs[0].title == "First"


def test_load_user_stories_dangling_foreign_key_is_warning_not_crash(tmp_path, caplog):
    path = _write_yaml(
        tmp_path,
        "stories.yaml",
        {
            "user_stories": [
                {"story_id": "S1", "requirement_id": "REQ-DOES-NOT-EXIST", "title": "Orphan by mistake"},
            ]
        },
    )
    with caplog.at_level("WARNING"):
        stories = load_user_stories(path, valid_requirement_ids={"REQ-1", "REQ-2"})
    assert len(stories) == 1  # not dropped -- surfaced as unlinked, not silently discarded
    assert stories[0].story_id == "S1"
    assert any("dangling foreign key" in rec.message for rec in caplog.records)


def test_load_test_cases_unknown_status_defaults_to_not_run(tmp_path):
    path = _write_yaml(
        tmp_path,
        "tests.yaml",
        {
            "test_cases": [
                {"test_case_id": "TC-1", "story_id": "S1", "title": "T", "execution_status": "in_progress"},
            ]
        },
    )
    tests = load_test_cases(path, valid_story_ids={"S1"})
    assert tests[0].execution_status == "not_run"


def test_load_test_cases_missing_story_id_is_skipped(tmp_path):
    path = _write_yaml(
        tmp_path,
        "tests.yaml",
        {"test_cases": [{"test_case_id": "TC-1", "title": "No story reference"}]},
    )
    tests = load_test_cases(path, valid_story_ids={"S1"})
    assert tests == []


def test_load_all_wires_fk_validation_across_all_three(tmp_path):
    req_path = _write_yaml(
        tmp_path, "req.yaml", {"requirements": [{"requirement_id": "REQ-1", "title": "T", "priority": "High"}]}
    )
    story_path = _write_yaml(
        tmp_path, "story.yaml", {"user_stories": [{"story_id": "S1", "requirement_id": "REQ-1", "title": "T"}]}
    )
    test_path = _write_yaml(
        tmp_path,
        "test.yaml",
        {"test_cases": [{"test_case_id": "TC-1", "story_id": "S1", "title": "T", "execution_status": "passed"}]},
    )
    reqs, stories, tests = load_all(req_path, story_path, test_path)
    assert len(reqs) == 1
    assert len(stories) == 1
    assert len(tests) == 1
