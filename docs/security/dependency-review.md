# Dependency Review — V1 1.0.0

Reviewed from `pyproject.toml` and lock revision 3 on 2026-08-02.

Direct runtime ranges are Pydantic `>=2.10,<3`, pydantic-settings `>=2.7,<3`
and Streamlit `>=1.41,<2`. The lock resolves these to 2.13.4, 2.14.2 and 1.60.0.
Direct development tools are build 1.5.0, MyPy 1.19.1, Pytest 8.4.2 and Ruff
0.16.1. `uv.lock` contains exact versions and hashes for transitive packages.

Streamlit transitively includes browser/server and HTTP libraries (for example
Requests, Uvicorn and WebSockets) needed to serve the local UI. Product code has
no outbound adapter and tests enforce that non-presentation application modules
do not import network clients. No OpenAI, Ollama, LangChain, embedding, FAISS,
Chroma or vector-database product dependency is declared.

This was an offline metadata/inventory review, not a current vulnerability-
database query. It makes no claim that public advisories were checked on this
date. Before publication, run an organization-approved scanner with a current
advisory database, review transitive findings and update the lock deliberately.
