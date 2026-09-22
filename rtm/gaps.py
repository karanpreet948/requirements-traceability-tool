"""
Coverage-gap detection.

Three findings a BA reviewing an RTM cares about most:

1. **Orphan requirements** -- requirements with no linked user story at all
   (nobody has scoped the work yet).
2. **Orphan stories** -- user stories with no linked test case (delivered,
   maybe, but never set up to be verified).
3. **Never-executed test cases** -- test cases that exist but have not been
   run at least once (``execution_status == "not_run"``), i.e. UAT/QA debt.

Each finding is returned as a small, serializable dataclass list so the
same data can back the CLI's printed summary, the Excel "Coverage Gaps"
sheet, and unit tests without duplicating formatting logic three times.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from rtm.models import Requirement, TestCase, UserStory


@dataclass(frozen=True)
class OrphanRequirement:
    requirement_id: str
    title: str
    priority: str


@dataclass(frozen=True)
class OrphanStory:
    story_id: str
    requirement_id: str
    title: str


@dataclass(frozen=True)
class NeverExecutedTestCase:
    test_case_id: str
    story_id: str
    title: str


@dataclass(frozen=True)
class GapReport:
    orphan_requirements: List[OrphanRequirement]
    orphan_stories: List[OrphanStory]
    never_executed_tests: List[NeverExecutedTestCase]

    @property
    def total_findings(self) -> int:
        return (
            len(self.orphan_requirements)
            + len(self.orphan_stories)
            + len(self.never_executed_tests)
        )


def find_orphan_requirements(
    requirements: Sequence[Requirement], stories: Sequence[UserStory]
) -> List[OrphanRequirement]:
    """Requirements with zero linked user stories."""
    requirement_ids_with_story = {s.requirement_id for s in stories}
    return [
        OrphanRequirement(r.requirement_id, r.title, r.priority)
        for r in requirements
        if r.requirement_id not in requirement_ids_with_story
    ]


def find_orphan_stories(
    stories: Sequence[UserStory], test_cases: Sequence[TestCase]
) -> List[OrphanStory]:
    """User stories with zero linked test cases."""
    story_ids_with_test = {t.story_id for t in test_cases}
    return [
        OrphanStory(s.story_id, s.requirement_id, s.title)
        for s in stories
        if s.story_id not in story_ids_with_test
    ]


def find_never_executed_tests(test_cases: Sequence[TestCase]) -> List[NeverExecutedTestCase]:
    """Test cases whose execution_status is still 'not_run'."""
    return [
        NeverExecutedTestCase(t.test_case_id, t.story_id, t.title)
        for t in test_cases
        if t.execution_status == "not_run"
    ]


def build_gap_report(
    requirements: Sequence[Requirement],
    stories: Sequence[UserStory],
    test_cases: Sequence[TestCase],
) -> GapReport:
    """Run all three gap-detection checks and bundle the results."""
    return GapReport(
        orphan_requirements=find_orphan_requirements(requirements, stories),
        orphan_stories=find_orphan_stories(stories, test_cases),
        never_executed_tests=find_never_executed_tests(test_cases),
    )
