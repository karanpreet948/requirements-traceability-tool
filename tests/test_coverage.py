import pytest

from rtm.coverage import compute_coverage_metrics


def test_totals(sample_requirements, sample_stories, sample_test_cases):
    metrics = compute_coverage_metrics(sample_requirements, sample_stories, sample_test_cases)
    assert metrics.total_requirements == 3
    assert metrics.total_stories == 3
    assert metrics.total_test_cases == 3


def test_requirements_with_story(sample_requirements, sample_stories, sample_test_cases):
    metrics = compute_coverage_metrics(sample_requirements, sample_stories, sample_test_cases)
    assert metrics.requirements_with_story == 2
    assert metrics.pct_requirements_with_story == pytest.approx(66.666, abs=0.01)


def test_stories_with_test(sample_requirements, sample_stories, sample_test_cases):
    metrics = compute_coverage_metrics(sample_requirements, sample_stories, sample_test_cases)
    assert metrics.stories_with_test == 2
    assert metrics.pct_stories_with_test == pytest.approx(66.666, abs=0.01)


def test_execution_and_pass_rates(sample_requirements, sample_stories, sample_test_cases):
    metrics = compute_coverage_metrics(sample_requirements, sample_stories, sample_test_cases)
    assert metrics.test_cases_executed == 2
    assert metrics.test_cases_passed == 1
    assert metrics.pct_test_cases_executed == pytest.approx(66.666, abs=0.01)
    assert metrics.pct_test_cases_passed == pytest.approx(33.333, abs=0.01)


def test_as_dict_rounds_percentages(sample_requirements, sample_stories, sample_test_cases):
    metrics = compute_coverage_metrics(sample_requirements, sample_stories, sample_test_cases)
    d = metrics.as_dict()
    assert d["pct_requirements_with_story"] == 66.7
    assert d["pct_test_cases_passed"] == 33.3


def test_empty_dataset_does_not_divide_by_zero():
    metrics = compute_coverage_metrics([], [], [])
    assert metrics.pct_requirements_with_story == 0.0
    assert metrics.pct_stories_with_test == 0.0
    assert metrics.pct_test_cases_executed == 0.0
    assert metrics.pct_test_cases_passed == 0.0


def test_full_coverage_case():
    from rtm.models import Requirement, TestCase, UserStory

    reqs = [Requirement("R1", "T", "", "High")]
    stories = [UserStory("S1", "R1", "T")]
    tests = [TestCase("T1", "S1", "T", "passed")]
    metrics = compute_coverage_metrics(reqs, stories, tests)
    assert metrics.pct_requirements_with_story == 100.0
    assert metrics.pct_stories_with_test == 100.0
    assert metrics.pct_test_cases_executed == 100.0
    assert metrics.pct_test_cases_passed == 100.0
