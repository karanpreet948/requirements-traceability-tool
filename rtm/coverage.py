"""
Coverage metric computation.

All percentages are computed directly from the three raw entity lists (not
from the flattened :class:`~rtm.models.TraceRow` list) so that the
definition of each metric is unambiguous and independent of how many join
rows a given parent happens to fan out into.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from rtm.models import Requirement, TestCase, UserStory


@dataclass(frozen=True)
class CoverageMetrics:
    """Summary coverage percentages for a single RTM run."""

    total_requirements: int
    total_stories: int
    total_test_cases: int

    requirements_with_story: int
    stories_with_test: int
    test_cases_executed: int
    test_cases_passed: int

    @property
    def pct_requirements_with_story(self) -> float:
        return _safe_pct(self.requirements_with_story, self.total_requirements)

    @property
    def pct_stories_with_test(self) -> float:
        return _safe_pct(self.stories_with_test, self.total_stories)

    @property
    def pct_test_cases_executed(self) -> float:
        return _safe_pct(self.test_cases_executed, self.total_test_cases)

    @property
    def pct_test_cases_passed(self) -> float:
        return _safe_pct(self.test_cases_passed, self.total_test_cases)

    def as_dict(self) -> dict:
        return {
            "total_requirements": self.total_requirements,
            "total_stories": self.total_stories,
            "total_test_cases": self.total_test_cases,
            "requirements_with_story": self.requirements_with_story,
            "stories_with_test": self.stories_with_test,
            "test_cases_executed": self.test_cases_executed,
            "test_cases_passed": self.test_cases_passed,
            "pct_requirements_with_story": round(self.pct_requirements_with_story, 1),
            "pct_stories_with_test": round(self.pct_stories_with_test, 1),
            "pct_test_cases_executed": round(self.pct_test_cases_executed, 1),
            "pct_test_cases_passed": round(self.pct_test_cases_passed, 1),
        }


def _safe_pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * 100.0


def compute_coverage_metrics(
    requirements: Sequence[Requirement],
    stories: Sequence[UserStory],
    test_cases: Sequence[TestCase],
) -> CoverageMetrics:
    """Compute the four headline coverage percentages for a run."""

    requirement_ids_with_story = {s.requirement_id for s in stories}
    story_ids_with_test = {t.story_id for t in test_cases}

    requirements_with_story = sum(
        1 for r in requirements if r.requirement_id in requirement_ids_with_story
    )
    stories_with_test = sum(1 for s in stories if s.story_id in story_ids_with_test)
    test_cases_executed = sum(1 for t in test_cases if t.execution_status != "not_run")
    test_cases_passed = sum(1 for t in test_cases if t.execution_status == "passed")

    return CoverageMetrics(
        total_requirements=len(requirements),
        total_stories=len(stories),
        total_test_cases=len(test_cases),
        requirements_with_story=requirements_with_story,
        stories_with_test=stories_with_test,
        test_cases_executed=test_cases_executed,
        test_cases_passed=test_cases_passed,
    )
