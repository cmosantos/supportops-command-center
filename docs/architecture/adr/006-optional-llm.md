# ADR-006: Optional LLM provider with deterministic fallback

Status: Accepted for Phase 2

## Decision

Default to `NullLLMProvider`; enable Ollama only by validated environment config.
Validate structured outputs, enforce timeouts, and fall back to local behavior.
Mandatory tests use fake/mock providers and never require an Ollama daemon.

## Consequences

The product remains reliable offline. A real-provider smoke test is optional and
cannot be cited as passed unless actually executed.

