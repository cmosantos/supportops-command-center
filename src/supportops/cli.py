"""Canonical command-line interface."""

import argparse
import logging
from collections.abc import Sequence

from supportops.bootstrap import Application, build_application
from supportops.errors import SupportOpsError

GENERIC_ERROR = "SupportOps could not complete the request safely."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="supportops")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("version", help="show the application version")

    config = commands.add_parser("config", help="configuration operations")
    config_commands = config.add_subparsers(dest="config_command", required=True)
    config_commands.add_parser("validate", help="validate local configuration")

    commands.add_parser("doctor", help="run offline, in-process diagnostics")
    return parser


def dispatch(args: argparse.Namespace, application: Application) -> int:
    if args.command == "version":
        print(application.version_provider.get_version())
        return 0
    if args.command == "config" and args.config_command == "validate":
        print("Configuration is valid.")
        return 0
    if args.command == "doctor":
        checks = application.diagnostics_provider.run(application.settings)
        for check in checks:
            status = "PASS" if check.passed else "FAIL"
            print(f"[{status}] {check.name}: {check.detail}")
        return 0 if all(check.passed for check in checks) else 1
    raise AssertionError("parser accepted an unsupported command")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return dispatch(args, build_application())
    except SupportOpsError as exc:
        print(f"Error: {exc.public_message}")
        return exc.exit_code
    except Exception:
        logging.getLogger("supportops").error("Unexpected CLI failure")
        print(f"Error: {GENERIC_ERROR}")
        return 1
