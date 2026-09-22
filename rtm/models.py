"""
Data model for the RTM tool.

Three simple, dependency-free dataclasses represent the three input
entities. They intentionally carry no behaviour beyond field storage so
that they can be constructed directly by the loader, by tests, or by any
future adapter (e.g. a database-backed loader) without extra coupling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

VALID_EXECUTION_STATUSES = {"not_run", "passed", "failed", "blocked"}
VALID_PRIORITIES = {"High", "Medium", "Low"}


@dataclass(frozen=True)
class Requirement:
    """A single business/functional requirement."""

    requirement_id: str
    title: str
    description: str = ""
    priority: str = "Medium"


@dataclass(frozen=True)
class UserStory:
    """A user story (or design item) that implements a requirement."""

    story_id: str
    requirement_id: str
    title: str


@dataclass(frozen=True)
class TestCase:
    """A test case that verifies a user story, with its UAT/execution status."""

    test_case_id: str
    story_id: str
    title: str
    execution_status: str = "not_run"


@dataclass
class TraceRow:
    """
    One row of the fully-joined traceability matrix.

    ``story`` and/or ``test_case`` may be ``None`` when a requirement has no
    linked story, or a story has no linked test case -- this is exactly how
    the matrix surfaces coverage gaps to a human reader, and it is also what
    the gap-detection functions in :mod:`rtm.gaps` key off of.
    """

    requirement: Requirement
    story: Optional[UserStory] = None
    test_case: Optional[TestCase] = None

    @property
    def execution_status(self) -> str:
        if self.test_case is None:
            return "no_test_case"
        return self.test_case.execution_status

    @property
    def as_dict(self) -> dict:
        return {
            "requirement_id": self.requirement.requirement_id,
            "requirement_title": self.requirement.title,
            "priority": self.requirement.priority,
            "story_id": self.story.story_id if self.story else "",
            "story_title": self.story.title if self.story else "(no linked user story)",
            "test_case_id": self.test_case.test_case_id if self.test_case else "",
            "test_case_title": self.test_case.title if self.test_case else "(no linked test case)",
            "execution_status": self.execution_status,
        }
