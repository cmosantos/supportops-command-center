"""Canonical command-line interface; contains presentation logic and no SQL."""

import argparse
import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from supportops.bootstrap import Application, build_application
from supportops.domain.incidents import ApprovalInput, IncidentCreate, IncidentUpdate
from supportops.errors import InputValidationError, SupportOpsError

GENERIC_ERROR = "SupportOps could not complete the request safely."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="supportops")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("version", help="show the application version")
    config = commands.add_parser("config", help="configuration operations")
    config.add_subparsers(dest="config_command", required=True).add_parser("validate")
    commands.add_parser("doctor", help="run offline, in-process diagnostics")

    database = commands.add_parser("db", help="database lifecycle")
    database_commands = database.add_subparsers(dest="db_command", required=True)
    database_commands.add_parser("init")
    database_commands.add_parser("status")

    incident = commands.add_parser("incident", help="incident lifecycle")
    incident_commands = incident.add_subparsers(dest="incident_command", required=True)
    create = incident_commands.add_parser("create")
    for name in (
        "title",
        "description",
        "affected-party",
        "affected-service",
        "impact",
        "urgency",
        "symptoms",
    ):
        create.add_argument(f"--{name}", required=True)
    create.add_argument("--error-message", action="append", default=[])
    create.add_argument("--action-taken", action="append", default=[])
    create.add_argument("--actor")
    get = incident_commands.add_parser("get")
    get.add_argument("incident_id")
    incident_commands.add_parser("list")
    update = incident_commands.add_parser("update")
    update.add_argument("incident_id")
    update.add_argument("--expected-version", required=True, type=int)
    for name in (
        "title",
        "description",
        "affected-party",
        "affected-service",
        "symptoms",
    ):
        update.add_argument(f"--{name}")
    update.add_argument("--actor")
    for operation in ("close", "reopen"):
        transition = incident_commands.add_parser(operation)
        transition.add_argument("incident_id")
        transition.add_argument("--actor")
    delete = incident_commands.add_parser("delete")
    delete.add_argument("incident_id")
    delete.add_argument("--reason", required=True)
    delete.add_argument("--confirm", action="store_true")
    delete.add_argument("--actor")
    history = incident_commands.add_parser("history")
    history.add_argument("incident_id")

    approval = commands.add_parser("approval", help="record human decisions")
    approval_commands = approval.add_subparsers(dest="approval_command", required=True)
    record = approval_commands.add_parser("record")
    record.add_argument("--incident-id", required=True)
    record.add_argument("--action-id", required=True)
    record.add_argument("--action-version", required=True, type=int)
    record.add_argument("--action-digest", required=True)
    record.add_argument("--action-snapshot", required=True)
    record.add_argument("--decision", required=True)
    record.add_argument("--approver", required=True)
    record.add_argument("--note")
    return parser


def _print_model(model: Any) -> None:
    print(json.dumps(model.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))


def dispatch(args: argparse.Namespace, application: Application) -> int:
    if args.command == "version":
        print(application.version_provider.get_version())
    elif args.command == "config":
        print("Configuration is valid.")
    elif args.command == "doctor":
        checks = application.diagnostics_provider.run(application.settings)
        for check in checks:
            print(
                f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.detail}"
            )
        return 0 if all(check.passed for check in checks) else 1
    elif args.command == "db":
        if args.db_command == "init":
            count = application.migration_runner.apply(datetime.now(UTC).isoformat())
            print(f"Database ready. Applied migrations: {count}.")
        else:
            current, pending = application.migration_runner.status()
            pending_text = ",".join(map(str, pending)) if pending else "none"
            print(f"Current migration: {current}; pending: {pending_text}.")
    elif args.command == "incident":
        return _dispatch_incident(args, application)
    elif args.command == "approval":
        snapshot = json.loads(args.action_snapshot)
        if not isinstance(snapshot, dict):
            raise InputValidationError("Action snapshot must be a JSON object.")
        approval = application.incident_service.record_approval(
            ApprovalInput(
                incident_id=args.incident_id,
                action_id=args.action_id,
                action_version=args.action_version,
                action_digest=args.action_digest,
                action_snapshot=snapshot,
                decision=args.decision,
                approver_reference=args.approver,
                note=args.note,
            )
        )
        _print_model(approval)
    return 0


def _dispatch_incident(args: argparse.Namespace, application: Application) -> int:
    service = application.incident_service
    if args.incident_command == "create":
        incident = service.create(
            IncidentCreate(
                title=args.title,
                description=args.description,
                affected_party=args.affected_party,
                affected_service=args.affected_service,
                impact=args.impact,
                urgency=args.urgency,
                symptoms=args.symptoms,
                error_messages=tuple(args.error_message),
                actions_already_taken=tuple(args.action_taken),
                actor_reference=args.actor,
            )
        )
        _print_model(incident)
    elif args.incident_command == "get":
        _print_model(service.get(args.incident_id))
    elif args.incident_command == "list":
        print(
            json.dumps(
                [item.model_dump(mode="json") for item in service.list()],
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    elif args.incident_command == "update":
        data = IncidentUpdate(
            expected_version=args.expected_version,
            title=args.title,
            description=args.description,
            affected_party=args.affected_party,
            affected_service=args.affected_service,
            symptoms=args.symptoms,
        )
        _print_model(service.update(args.incident_id, data, args.actor))
    elif args.incident_command == "close":
        _print_model(service.close(args.incident_id, args.actor))
    elif args.incident_command == "reopen":
        _print_model(service.reopen(args.incident_id, args.actor))
    elif args.incident_command == "delete":
        service.soft_delete(args.incident_id, args.reason, args.confirm, args.actor)
        print("Incident logically deleted.")
    elif args.incident_command == "history":
        print(
            json.dumps(
                [
                    item.model_dump(mode="json")
                    for item in service.history(args.incident_id)
                ],
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        return dispatch(parser.parse_args(argv), build_application())
    except ValidationError:
        print("Error: Invalid input. Correct the documented fields and retry.")
        return 2
    except (json.JSONDecodeError, TypeError):
        print("Error: Invalid JSON input. Provide a JSON object.")
        return 2
    except SupportOpsError as exc:
        print(f"Error: {exc.public_message}")
        return exc.exit_code
    except Exception:
        logging.getLogger("supportops").error("Unexpected CLI failure")
        print(f"Error: {GENERIC_ERROR}")
        return 1
