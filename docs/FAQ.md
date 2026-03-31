# Technical Q&A Primer

## Why citations in every answer?

Citations make the answer auditable for technical reviewers and reduce trust
risk for business stakeholders. Each citation links to `chunk_id`, `doc_id`,
and page span.

## How do you reduce hallucinations?

- Retrieval-grounded prompt with explicit "use provided context only" instruction.
- No-evidence path returns `insufficient_evidence=True` instead of inventing facts.
- Score threshold and context budget guardrails are configurable.

## How often should we re-index?

For pilot scale, nightly plus manual runs on document drops is sufficient.
Production should move to incremental/event-driven indexing where possible.

## Why not use default PDF loaders only?

Default loaders pass through repeated headers, page markers, and inconsistent
formatting. The cleaning stage normalizes noisy patterns before chunking.

## Can this move to managed cloud services?

Yes. The adapter-based design supports migration to managed embedding/LLM and
vector backends with minimal pipeline code changes.
