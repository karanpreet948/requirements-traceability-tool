"""
Traceability chain builder.

Joins ``requirements -> user_stories -> test_cases`` into a flat list of
:class:`~rtm.models.TraceRow`. The join is a *left outer join* at each hop:
a requirement with no stories still produces one row (with ``story=None``),
and a story with no test cases still produces one row (with
``test_case=None``). This is what lets the exported matrix double as a
gap report at a glance, and it is exactly what :mod:`rtm.gaps` inspects.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Sequence

from rtm.models import Requirement, TestCase, TraceRow, UserStory

logger = logging.getLogger("rtm.matrix")


def build_traceability(
    requirements: Sequence[Requirement],
    stories: Sequence[UserStory],
    test_cases: Sequence[TestCase],
) -> List[TraceRow]:
    """Build the full requirement -> story -> test case chain."""

    stories_by_requirement: Dict[str, List[UserStory]] = defaultdict(list)
    for story in stories:
        stories_by_requirement[story.requirement_id].append(story)

    tests_by_story: Dict[str, List[TestCase]] = defaultdict(list)
    for test_case in test_cases:
        tests_by_story[test_case.story_id].append(test_case)

    rows: List[TraceRow] = []
    for requirement in requirements:
        linked_stories = stories_by_requirement.get(requirement.requirement_id, [])
        if not linked_stories:
            rows.append(TraceRow(requirement=requirement, story=None, test_case=None))
            continue

        for story in linked_stories:
            linked_tests = tests_by_story.get(story.story_id, [])
            if not linked_tests:
                rows.append(TraceRow(requirement=requirement, story=story, test_case=None))
                continue

            for test_case in linked_tests:
                rows.append(TraceRow(requirement=requirement, story=story, test_case=test_case))

    logger.info(
        "Built traceability matrix: %d requirement(s), %d stor(y/ies), "
        "%d test case(s) -> %d matrix row(s)",
        len(requirements), len(stories), len(test_cases), len(rows),
    )
    return rows
