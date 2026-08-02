# Known Limitations

- Local single-node SQLite is subject to file locking and is not intended for high-concurrency or horizontally scaled deployment.
- Actor/approver references are declared by users and are not authenticated.
- Logical deletion is irreversible in V1; there is no restore or physical purge.
- Lexical search depends on curated terms and does not infer semantic synonyms.
- The Streamlit triage screen accepts raw JSON rather than guided, schema-aware fields. Unknown schema fields are rejected and validation feedback is currently generic.
- Public documentation is English, while the V1 interface and curated runbooks are Portuguese-first.
- Operators own incident content quality and must avoid credentials and unnecessary personal information.
- There is no GLPI/ServiceNow integration or SLA pause calculation.
- No automatic data-retention policy exists; retention and backups are operator duties.
- Increment 7/Ollama is optional, excluded, unimplemented, and untested.
- Windows hosts may disallow symlink-creation security tests without privilege; resolved-path containment is still covered by non-privileged adversarial tests.
- Docker and GitHub Actions evidence depends on the available engine/host; local execution does not claim that an unpublished GitHub workflow has run remotely.
