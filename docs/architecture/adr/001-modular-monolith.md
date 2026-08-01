# ADR-001: Modular monolith with ports and adapters

Status: Accepted for Phase 2

## Decision

Use one local Python deployment divided into presentation, application, domain,
and infrastructure modules. Dependencies point inward; external facilities
implement ports.

## Consequences

Local installation remains simple, rules are testable without UI/database, and
future adapters can change independently. Module boundaries require explicit
contracts and discipline.

