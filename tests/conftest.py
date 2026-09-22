"""Shared fixtures for the RTM test suite.

The fixture data here is a small, hand-picked dataset (independent from the
larger data/ sample fixtures) with a known, worked-out set of expected
coverage numbers and gap findings, so tests can assert exact values rather
than just "it ran without crashing":

    Requirements: R1, R2, R3         (R3 has no story -> orphan requirement)
    Stories:      S1, S2 (both -> R1), S3 (-> R2)
                                       (S2 has no test case -> orphan story)
    Test cases:   T1 (-> S1, passed), T2 (-> S1, failed), T3 (-> S3, not_run)
                                       (T3 is never executed)

Expected coverage:
    requirements_with_story = 2 of 3  -> 66.7%
    stories_with_test       = 2 of 3  -> 66.7%
    test_cases_executed     = 2 of 3  -> 66.7%
    test_cases_passed       = 1 of 3  -> 33.3%
"""

import pytest

from rtm.models import Requirement, TestCase, UserStory


@pytest.fixture
def sample_requirements():
    return [
        Requirement("R1", "Requirement One", "First requirement", "High"),
        Requirement("R2", "Requirement Two", "Second requirement", "Medium"),
        Requirement("R3", "Requirement Three", "Third requirement, never scoped", "Low"),
    ]


@pytest.fixture
def sample_stories():
    return [
        UserStory("S1", "R1", "Story One"),
        UserStory("S2", "R1", "Story Two, never tested"),
        UserStory("S3", "R2", "Story Three"),
    ]


@pytest.fixture
def sample_test_cases():
    return [
        TestCase("T1", "S1", "Test One", "passed"),
        TestCase("T2", "S1", "Test Two", "failed"),
        TestCase("T3", "S3", "Test Three, never executed", "not_run"),
    ]
