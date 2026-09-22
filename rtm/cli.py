"""
Command-line entry point for the RTM tool.

Usage
-----
    python -m rtm build \\
        --requirements data/requirements.yaml \\
        --stories data/user_stories.yaml \\
        --tests data/test_cases.yaml \\
        --output out/rtm.xlsx

Prints a coverage summary and gap findings to stdout, and writes a
3-sheet Excel workbook to ``--output``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from rtm.coverage import compute_coverage_metrics
from rtm.exporter import export_to_excel
from rtm.gaps import build_gap_report
from rtm.loader import DataLoadError, load_all
from rtm.matrix import build_traceability

logger = logging.getLogger("rtm.cli")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _print_summary(metrics, gap_report) -> None:
    print("=" * 60)
    print("REQUIREMENTS TRACEABILITY MATRIX - COVERAGE SUMMARY")
    print("=" * 60)
    print(f"Total requirements : {metrics.total_requirements}")
    print(f"Total user stories : {metrics.total_stories}")
    print(f"Total test cases   : {metrics.total_test_cases}")
    print("-" * 60)
    print(f"% requirements with >=1 linked story : {metrics.pct_requirements_with_story:.1f}%")
    print(f"% stories with >=1 linked test case   : {metrics.pct_stories_with_test:.1f}%")
    print(f"% test cases executed                 : {metrics.pct_test_cases_executed:.1f}%")
    print(f"% test cases passed                   : {metrics.pct_test_cases_passed:.1f}%")
    print("-" * 60)
    print("COVERAGE GAPS")
    print(f"  Orphan requirements (no story)      : {len(gap_report.orphan_requirements)}")
    for o in gap_report.orphan_requirements:
        print(f"    - {o.requirement_id}: {o.title} [{o.priority}]")
    print(f"  Orphan stories (no test case)       : {len(gap_report.orphan_stories)}")
    for o in gap_report.orphan_stories:
        print(f"    - {o.story_id} (req {o.requirement_id}): {o.title}")
    print(f"  Never-executed test cases           : {len(gap_report.never_executed_tests)}")
    for t in gap_report.never_executed_tests:
        print(f"    - {t.test_case_id} (story {t.story_id}): {t.title}")
    print("=" * 60)


def cmd_build(args: argparse.Namespace) -> int:
    try:
        requirements, stories, tests = load_all(args.requirements, args.stories, args.tests)
    except DataLoadError as exc:
        logger.error("Failed to load input data: %s", exc)
        return 1

    if not requirements:
        logger.error("No valid requirements were loaded; nothing to build. Aborting.")
        return 1

    trace_rows = build_traceability(requirements, stories, tests)
    metrics = compute_coverage_metrics(requirements, stories, tests)
    gap_report = build_gap_report(requirements, stories, tests)

    output_path = export_to_excel(args.output, trace_rows, metrics, gap_report)

    _print_summary(metrics, gap_report)
    print(f"\nExcel workbook written to: {output_path}")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtm",
        description="Requirements Traceability Matrix (RTM) builder.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")

    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build", help="load inputs, build the matrix, and export an Excel workbook"
    )
    build_parser.add_argument(
        "--requirements", required=True, type=Path, help="path to requirements YAML file"
    )
    build_parser.add_argument(
        "--stories", required=True, type=Path, help="path to user_stories YAML file"
    )
    build_parser.add_argument(
        "--tests", required=True, type=Path, help="path to test_cases YAML file"
    )
    build_parser.add_argument(
        "--output", required=True, type=Path, help="path to write the .xlsx output to"
    )
    build_parser.set_defaults(func=cmd_build)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
