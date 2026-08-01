# ADR-002: CLI-first presentation architecture

Status: Accepted for Phase 2

## Decision

Implement and prove every essential use case through application services and the
CLI before accepting its Streamlit presentation. Both interfaces share one
composition root. The dashboard is observational.

## Consequences

The system remains operable without UI and complies with the AIOX Constitution.
UI-specific business rules or direct database access are prohibited.

