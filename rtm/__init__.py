"""
rtm - Requirements Traceability Matrix Tool
=============================================

A small, dependency-light library and CLI for building a Requirements
Traceability Matrix (RTM) from three related data sources:

    requirements  --1:N-->  user_stories  --1:N-->  test_cases

It computes coverage metrics (percentage of requirements with at least one
linked story, percentage of stories with at least one linked test case,
percentage of test cases executed / passed) and produces a coverage-gap
report (orphan requirements, orphan stories, never-executed test cases).

This package is a portfolio / demonstration project. All data shipped in
``data/`` is synthetic and fictional. See the top-level README.md for the
full write-up, architecture diagram, and sample output.
"""

__version__ = "1.0.0"
