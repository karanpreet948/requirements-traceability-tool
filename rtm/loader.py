"""
Loaders for the three RTM input entities.

Input files are YAML (a plain list of mappings under a top-level key, or a
bare list) and can equally be produced from CSV upstream -- the loaders only
care about the in-memory list-of-dicts shape, so :func:`load_requirements`,
:func:`load_user_stories` and :func:`load_test_cases` would work unchanged
against rows read with :mod:`csv.DictReader`.

Design goals:

* Never crash on a single bad record. A missing required field, an unknown
  enum value, or a dangling foreign key is logged as a warning and the
  offending record is either coerced to a safe default or skipped -- the
  caller finds out what happened by reading the logs (and, for dangling
  foreign keys, via the return value described below).
* Be predictable: fields are read defensively with ``.get`` and coerced to
  strings/trimmed, so extra whitespace or YAML quirks do not create subtly
  duplicate IDs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterable, List, Union

import yaml

from rtm.models import (
    VALID_EXECUTION_STATUSES,
    VALID_PRIORITIES,
    Requirement,
    TestCase,
    UserStory,
)

logger = logging.getLogger("rtm.loader")

PathLike = Union[str, Path]


class DataLoadError(Exception):
    """Raised when an input file cannot be read or parsed at all."""


def _read_yaml_records(path: PathLike, top_level_key: str) -> List[dict]:
    """
    Read a YAML file and return a list of raw record dicts.

    Accepts either:
      - a bare top-level list, e.g. ``- requirement_id: REQ-001 ...``
      - a mapping with the expected key, e.g. ``requirements: [...]``
    """
    file_path = Path(path)
    if not file_path.exists():
        raise DataLoadError(f"Input file not found: {file_path}")

    try:
        with file_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise DataLoadError(f"Could not parse YAML in {file_path}: {exc}") from exc

    if raw is None:
        logger.warning("Input file %s is empty; treating as zero records.", file_path)
        return []

    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict) and top_level_key in raw:
        records = raw[top_level_key] or []
    else:
        raise DataLoadError(
            f"{file_path} must be a YAML list or a mapping with a '{top_level_key}' key"
        )

    if not isinstance(records, list):
        raise DataLoadError(f"{file_path}: expected a list of records under '{top_level_key}'")

    clean: List[dict] = []
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            logger.warning("Skipping malformed record #%d in %s (not a mapping): %r", i, file_path, rec)
            continue
        clean.append(rec)
    return clean


def _clean_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def load_requirements(path: PathLike) -> List[Requirement]:
    """Load and validate requirements from a YAML file."""
    records = _read_yaml_records(path, "requirements")
    results: List[Requirement] = []
    seen_ids = set()

    for i, rec in enumerate(records):
        req_id = _clean_str(rec.get("requirement_id"))
        title = _clean_str(rec.get("title"))

        if not req_id:
            logger.warning("Skipping requirement record #%d: missing 'requirement_id'.", i)
            continue
        if req_id in seen_ids:
            logger.warning("Duplicate requirement_id '%s' encountered; keeping first occurrence.", req_id)
            continue
        if not title:
            logger.warning("Requirement '%s' has no title; using placeholder.", req_id)
            title = "(untitled requirement)"

        priority = _clean_str(rec.get("priority"), "Medium") or "Medium"
        if priority not in VALID_PRIORITIES:
            logger.warning(
                "Requirement '%s' has unrecognized priority '%s'; defaulting to 'Medium'.",
                req_id, priority,
            )
            priority = "Medium"

        results.append(
            Requirement(
                requirement_id=req_id,
                title=title,
                description=_clean_str(rec.get("description")),
                priority=priority,
            )
        )
        seen_ids.add(req_id)

    logger.info("Loaded %d requirement(s) from %s", len(results), path)
    return results


def load_user_stories(
    path: PathLike, valid_requirement_ids: Iterable[str] | None = None
) -> List[UserStory]:
    """
    Load and validate user stories from a YAML file.

    If ``valid_requirement_ids`` is given, a story whose ``requirement_id``
    does not match any known requirement is a *dangling foreign key*: it is
    logged as a warning and still returned (so it shows up, deliberately, as
    unlinked in the matrix) rather than silently dropped or crashing the run.
    """
    records = _read_yaml_records(path, "user_stories")
    results: List[UserStory] = []
    seen_ids = set()
    valid_req_ids = set(valid_requirement_ids) if valid_requirement_ids is not None else None

    for i, rec in enumerate(records):
        story_id = _clean_str(rec.get("story_id"))
        req_id = _clean_str(rec.get("requirement_id"))
        title = _clean_str(rec.get("title"))

        if not story_id:
            logger.warning("Skipping user story record #%d: missing 'story_id'.", i)
            continue
        if story_id in seen_ids:
            logger.warning("Duplicate story_id '%s' encountered; keeping first occurrence.", story_id)
            continue
        if not req_id:
            logger.warning("Skipping user story '%s': missing 'requirement_id'.", story_id)
            continue
        if not title:
            title = "(untitled user story)"

        if valid_req_ids is not None and req_id not in valid_req_ids:
            logger.warning(
                "User story '%s' references unknown requirement_id '%s' "
                "(dangling foreign key). It will appear unlinked in reports.",
                story_id, req_id,
            )

        results.append(UserStory(story_id=story_id, requirement_id=req_id, title=title))
        seen_ids.add(story_id)

    logger.info("Loaded %d user stor(y/ies) from %s", len(results), path)
    return results


def load_test_cases(
    path: PathLike, valid_story_ids: Iterable[str] | None = None
) -> List[TestCase]:
    """
    Load and validate test cases from a YAML file.

    Same dangling-foreign-key handling as :func:`load_user_stories`, applied
    to ``story_id``. An unrecognized ``execution_status`` is coerced to
    ``not_run`` with a warning rather than rejected outright.
    """
    records = _read_yaml_records(path, "test_cases")
    results: List[TestCase] = []
    seen_ids = set()
    valid_sids = set(valid_story_ids) if valid_story_ids is not None else None

    for i, rec in enumerate(records):
        tc_id = _clean_str(rec.get("test_case_id"))
        story_id = _clean_str(rec.get("story_id"))
        title = _clean_str(rec.get("title"))
        status = _clean_str(rec.get("execution_status"), "not_run") or "not_run"

        if not tc_id:
            logger.warning("Skipping test case record #%d: missing 'test_case_id'.", i)
            continue
        if tc_id in seen_ids:
            logger.warning("Duplicate test_case_id '%s' encountered; keeping first occurrence.", tc_id)
            continue
        if not story_id:
            logger.warning("Skipping test case '%s': missing 'story_id'.", tc_id)
            continue
        if not title:
            title = "(untitled test case)"

        if status not in VALID_EXECUTION_STATUSES:
            logger.warning(
                "Test case '%s' has unrecognized execution_status '%s'; defaulting to 'not_run'.",
                tc_id, status,
            )
            status = "not_run"

        if valid_sids is not None and story_id not in valid_sids:
            logger.warning(
                "Test case '%s' references unknown story_id '%s' "
                "(dangling foreign key). It will appear unlinked in reports.",
                tc_id, story_id,
            )

        results.append(
            TestCase(test_case_id=tc_id, story_id=story_id, title=title, execution_status=status)
        )
        seen_ids.add(tc_id)

    logger.info("Loaded %d test case(s) from %s", len(results), path)
    return results


def load_all(
    requirements_path: PathLike, stories_path: PathLike, tests_path: PathLike
):
    """
    Convenience helper: load all three entities in the right order so that
    foreign-key validation can happen against already-loaded parents.

    Returns a ``(requirements, user_stories, test_cases)`` tuple.
    """
    requirements = load_requirements(requirements_path)
    req_ids = {r.requirement_id for r in requirements}

    stories = load_user_stories(stories_path, valid_requirement_ids=req_ids)
    story_ids = {s.story_id for s in stories}

    tests = load_test_cases(tests_path, valid_story_ids=story_ids)

    return requirements, stories, tests
