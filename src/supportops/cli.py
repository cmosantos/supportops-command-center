# ruff: noqa: E501
"""Canonical command-line interface; contains presentation logic and no SQL."""

import argparse
import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from supportops.bootstrap import Application, build_application
from supportops.domain.documentation import ExportFormat, PerformedProcedureInput
from supportops.domain.incidents import ApprovalInput, IncidentCreate, IncidentUpdate
from supportops.domain.triage import TriageEvidence, TriageResult
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

    triage = commands.add_parser("triage", help="deterministic incident triage")
    triage_commands = triage.add_subparsers(dest="triage_command", required=True)
    triage_run = triage_commands.add_parser("run")
    triage_run.add_argument("incident_id")
    triage_run.add_argument("--evidence-json", required=True)
    triage_run.add_argument("--actor")
    triage_run.add_argument("--format", choices=("human", "json"), default="human")
    triage_history = triage_commands.add_parser("history")
    triage_history.add_argument("incident_id")
    triage_history.add_argument("--format", choices=("human", "json"), default="human")

    knowledge = commands.add_parser("knowledge", help="local knowledge operations")
    knowledge_commands = knowledge.add_subparsers(
        dest="knowledge_command", required=True
    )
    knowledge_search = knowledge_commands.add_parser("search")
    knowledge_search.add_argument("query")
    knowledge_search.add_argument("--limit", type=int, default=10)
    knowledge_search.add_argument(
        "--format", choices=("human", "json"), default="human"
    )

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

    performed = commands.add_parser("performed", help="reported performed procedures")
    performed_commands = performed.add_subparsers(
        dest="performed_command", required=True
    )
    performed_record = performed_commands.add_parser("record")
    performed_record.add_argument("incident_id")
    performed_record.add_argument("--description", required=True)
    performed_record.add_argument("--result", required=True)
    performed_record.add_argument("--actor", required=True)
    performed_record.add_argument("--suggested-action-id")
    performed_record.add_argument("--suggested-action-version", type=int)
    performed_record.add_argument("--suggested-action-digest")
    performed_record.add_argument(
        "--format", choices=("human", "json"), default="human"
    )
    performed_list = performed_commands.add_parser("list")
    performed_list.add_argument("incident_id")
    performed_list.add_argument("--format", choices=("human", "json"), default="human")

    document = commands.add_parser("document", help="persisted incident documentation")
    document_commands = document.add_subparsers(dest="document_command", required=True)
    document_generate = document_commands.add_parser("generate")
    document_generate.add_argument("incident_id")
    document_generate.add_argument("--actor", required=True)
    document_generate.add_argument(
        "--format", choices=("human", "json"), default="human"
    )
    document_show = document_commands.add_parser("show")
    document_show.add_argument("incident_id")
    document_show.add_argument("--revision", type=int)
    document_show.add_argument("--format", choices=("human", "json"), default="human")
    document_history = document_commands.add_parser("history")
    document_history.add_argument("incident_id")
    document_history.add_argument(
        "--format", choices=("human", "json"), default="human"
    )

    export = commands.add_parser("export", help="safe persisted documentation export")
    export.add_argument("incident_id")
    export.add_argument("--revision", type=int)
    export.add_argument("--format", choices=("markdown", "json"), required=True)
    export.add_argument("--output", choices=("human", "json"), default="human")
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
    elif args.command == "triage":
        return _dispatch_triage(args, application)
    elif args.command == "knowledge":
        return _dispatch_knowledge(args, application)
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
    elif args.command == "performed":
        return _dispatch_performed(args, application)
    elif args.command == "document":
        return _dispatch_document(args, application)
    elif args.command == "export":
        result = application.documentation_service.export(
            args.incident_id, ExportFormat(args.format), args.revision
        )
        if args.output == "json":
            _print_model(result)
        else:
            print(f"Exported {result.format.value} revision {result.revision}")
            print(f"incident: {result.incident_id}")
            print(f"media_type: {result.media_type}")
            print(f"filename: {result.filename}")
            print(f"relative_path: {result.relative_path}")
    return 0


def _dispatch_performed(args: argparse.Namespace, application: Application) -> int:
    service = application.documentation_service
    items: tuple[Any, ...]
    if args.performed_command == "record":
        items = (
            service.record_performed(
                args.incident_id,
                PerformedProcedureInput(
                    description=args.description,
                    result=args.result,
                    actor_reference=args.actor,
                    suggested_action_id=args.suggested_action_id,
                    suggested_action_version=args.suggested_action_version,
                    suggested_action_digest=args.suggested_action_digest,
                ),
            ),
        )
    else:
        items = service.list_performed(args.incident_id)
    if args.format == "json":
        print(
            json.dumps(
                [item.model_dump(mode="json") for item in items],
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    else:
        if not items:
            print("No performed procedures recorded.")
        for item in items:
            print(
                f"performed id={item.id} incident={item.incident_id} "
                f"sequence={item.sequence}"
            )
            print(f"performed_at: {item.performed_at.isoformat()}")
            print(f"actor: {item.actor_reference}")
            suggestion = (
                f"{item.suggested_action_id}/v{item.suggested_action_version}/"
                f"{item.suggested_action_digest}"
                if item.suggested_action_id
                else "none"
            )
            print(f"suggestion_reference: {suggestion}")
            print(f"description: {item.description}")
            print(f"result: {item.result}")
    return 0


def _dispatch_document(args: argparse.Namespace, application: Application) -> int:
    service = application.documentation_service
    items: tuple[Any, ...]
    if args.document_command == "generate":
        items = (service.generate(args.incident_id, args.actor),)
    elif args.document_command == "history":
        items = service.history(args.incident_id)
    else:
        items = (service.get(args.incident_id, args.revision),)
    if args.format == "json":
        payload: object = (
            items[0].model_dump(mode="json")
            if len(items) == 1
            else [item.model_dump(mode="json") for item in items]
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        for item in items:
            print(
                f"document={item.id} incident={item.incident_id} "
                f"revision={item.revision}"
            )
            print(
                f"generated_at={item.generated_at.isoformat()} "
                f"generated_by={item.generated_by}"
            )
            for key, value in item.sections.model_dump().items():
                print(f"{key}:")
                if isinstance(value, tuple):
                    for entry in value:
                        print(f"- {entry}")
                else:
                    print(value)
    return 0


def _dispatch_knowledge(args: argparse.Namespace, application: Application) -> int:
    results = application.knowledge_service.search(args.query, args.limit)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "query": args.query,
                    "results": [item.model_dump(mode="json") for item in results],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    if not results:
        print("No knowledge matches found.")
        return 0
    print(f"Knowledge matches: {len(results)}")
    for rank, item in enumerate(results, start=1):
        print(f"{rank}. {item.title}")
        print(f"   score: {item.score}; matched: {', '.join(item.matched_terms)}")
        print(f"   revision: {item.revision}; source: {item.source_path}")
        print(f"   evidence: {item.excerpt}")
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


def _dispatch_triage(args: argparse.Namespace, application: Application) -> int:
    service = application.triage_service
    if args.triage_command == "run":
        payload = json.loads(args.evidence_json)
        if not isinstance(payload, dict):
            raise InputValidationError("Triage evidence must be a JSON object.")
        result = service.triage(
            args.incident_id,
            TriageEvidence.model_validate(payload),
            args.actor,
        )
        _print_triage_result(result, args.format)
    else:
        history = service.history(args.incident_id)
        if args.format == "json":
            print(
                json.dumps(
                    [item.model_dump(mode="json") for item in history],
                    ensure_ascii=False,
                )
            )
        else:
            for item in history:
                print(
                    f"sequence={item.sequence} outcome={item.outcome.value} "
                    f"priority={item.priority.value if item.priority else 'none'} "
                    f"rule={item.rule_id or 'none'} revision={item.policy_checksum}"
                )
    return 0


def _print_triage_result(result: TriageResult, output_format: str) -> None:
    question_payload = [
        question.model_dump(mode="json") for question in result.questions
    ]
    if output_format == "json":
        result_payload = result.model_dump(mode="json", exclude={"questions"})
        print(
            json.dumps(
                {
                    "questions": question_payload,
                    "outcome": result.outcome.value,
                    "result": result_payload,
                },
                ensure_ascii=False,
            )
        )
        return
    print(f"outcome: {result.outcome.value}")
    print("questions:")
    if not result.questions:
        print("- none")
    for question in result.questions:
        marker = "BLOCKING" if question.blocking else "OPTIONAL"
        print(f"- [{marker}] {question.question_id}: {question.question}")
    print("classification:")
    print(f"- policy: {result.policy_id}/{result.matrix_version}")
    print(f"- revision: {result.policy_checksum}")
    print(f"- rule: {result.rule_id or 'none'}")
    print(f"- priority: {result.priority.value if result.priority else 'none'}")
    print(
        "- route: "
        f"{result.recommended_route.value if result.recommended_route else 'none'}"
    )
    print(
        "- escalation: "
        f"{'yes' if result.escalation_required else 'no'} "
        f"({','.join(result.escalation_reason_ids) or 'none'})"
    )
    print(
        "- stop: "
        f"{'yes' if result.stop.required else 'no'} "
        f"({','.join(result.stop.reason_ids) or 'none'})"
    )


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
