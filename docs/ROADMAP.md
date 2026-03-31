# Production Roadmap (Prototype -> Production)

This roadmap translates the current prototype into a production-oriented Google
Cloud architecture without overselling current scope.

## Current state (prototype baseline)

- Local PDF ingestion, custom cleaning, chunking, embeddings, vector retrieval
- Grounded RAG response path with citations and safe no-evidence behavior
- Demo CLI and CI-friendly offline tests using synthetic documents

## Phase 1: Pilot hardening (2-6 weeks)

### Platform and data flow

- Store source documents in `Google Cloud Storage` (bucket per environment).
- Introduce managed parsing fallback for difficult layouts via `Document AI`.
- Keep app runtime in `Cloud Run` for simple deployment and revision control.

### Security and governance

- Use service-account based access and least-privilege `IAM`.
- Enable CMEK where required for regulated datasets.
- Define environment separation (`dev`, `staging`, `prod`) and secret handling in
  `Secret Manager`.

### Evaluation and quality

- Add query/evidence test set for domain-reviewed factual checks.
- Track retrieval hit quality and refusal rates on low-evidence prompts.

## Phase 2: Controlled production rollout (6-12 weeks)

### Retrieval and model services

- Move embedding and generation to managed endpoints (e.g. `Vertex AI` models).
- Choose production vector backend:
  - `Vertex AI Vector Search` for managed retrieval at scale, or
  - `AlloyDB + pgvector` when SQL-native controls and joins are preferred.

Selection criteria:
- operational simplicity
- latency and recall targets
- cost profile at expected QPS
- metadata filter support

### Reliability and operations

- Define SLOs (e.g. p95 latency, availability, citation presence rate).
- Add structured logs, traceability, and alerting (Cloud Logging/Monitoring).
- Add ingestion runbook with retry/idempotency guarantees and failure alerts.

### Data lifecycle

- Formalize re-index cadence (e.g. nightly + on-demand document deltas).
- Track embedding model/version metadata for index reproducibility.
- Define retention and deletion controls for document and vector artifacts.

## Phase 3: Enterprise scale and control (12+ weeks)

### Security and compliance posture

- Consider VPC Service Controls for stronger data perimeter controls.
- Add policy gates for high-stakes outputs (human review for sensitive flows).
- Expand auditability with immutable run manifests for ingestion/index jobs.

### Resilience

- Add DR strategy: multi-zone setup and backup/restore drills.
- Validate recovery objectives (RTO/RPO) for vector index and metadata stores.

### Continuous model quality

- Introduce periodic regression suites for retrieval + answer grounding quality.
- Monitor drift in document templates and parser/cleaner extraction quality.

## Cost levers

- Chunk size/overlap tuning directly affects embedding volume and storage.
- Re-index strategy (full vs incremental) controls recurring compute spend.
- Model selection policy by route (stub/local in test; managed only where needed).
- Retrieval top-k and context budget tuning balance quality vs generation token cost.

## Business value and outcomes

- **Speed:** analysts query large PDF corpora in seconds instead of manual scans.
- **Consistency:** standardized retrieval + normalization reduces answer variance.
- **Risk reduction:** explicit citations and no-evidence refusal reduce unsupported claims.
- **Scalability:** repeatable architecture pattern for adjacent document-heavy workflows.

## Out-of-scope in this roadmap doc

- This is not legal or compliance advice.
- This does not claim current prototype is production-ready as-is.
