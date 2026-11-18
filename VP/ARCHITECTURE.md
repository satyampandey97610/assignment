# Care Concierge: architecture and delivery status

This is the proposed architecture based on the current repository. Confirm the assignment brief, provider contracts, and operational requirements before treating it as final. The repository is a foundation, not yet a complete patient-facing application.

## Target flow

```text
WhatsApp / client
  -> webhook: verify signature, normalize events, deduplicate delivery
  -> resolve and authorize patient and society
  -> safety gate
       -> emergency: immediate safe response + durable escalation
       -> classifier failure: safe fallback; do not execute ordinary tools
       -> otherwise: conversation controller
  -> scoped booking, symptom, or clinic-document tools
  -> response delivery with retry and delivery tracking
```

PostgreSQL stores patients, clinicians, bookings, symptoms, escalations and document metadata; pgvector supports document retrieval. The database is the authority for booking conflicts. The controller must never trust a patient or society ID supplied by a model. Use current, society-authorized documents, cite sources, and avoid presenting the assistant as a clinician. Protect sensitive data in logs and restrict access. Escalation needs a real notification and acknowledgement process, not just a database record.

## Present in the repository

- PostgreSQL models, migration, seed data, slot calculations, and a scoped repository.
- Booking, listing, symptom logging, document search, and escalation functions; database constraints for booking conflicts and request IDs.
- Safety classifier, emergency regex fallback, response templates, LLM cache and embeddings wrapper.
- Webhook fixture examples and tests for several tool, scoping, booking and safety cases.
- Booking replays now work after a slot has passed, and overlapping availability windows no longer generate duplicate suggestions. Invalid non-positive slot durations fail instead of looping indefinitely.

## Remaining work

1. Restore a reproducible development environment, document setup and run the PostgreSQL-backed suite. Compose currently references missing `app.retrieval.ingest` and `app.api.main` modules, so the application cannot start as configured.
2. Implement document ingestion, version/current handling and retrieval evaluation, including society isolation and an explicit no-answer path.
3. Implement the webhook/API: signature verification, sender-to-patient authorization, message and status handling, idempotent redelivery, unsupported media and outbound delivery.
4. Connect safety, conversation state, tools and responses; enforce tool limits and safe behavior when providers fail. Validate multilingual emergency and medical-advice handling with clinical stakeholders.
5. Complete booking edge cases, including trying other eligible clinicians, request-ID payload consistency, concurrent replay and validation; audit direct queries and enforce access boundaries end to end.
6. Implement operational escalation notification, acknowledgement, retries and SLA monitoring; evaluate privacy, retention, observability and security.
7. Add end-to-end and failure-path tests, CI, runbook and deployment documentation. Test with representative providers and realistic data only when authorized.

## Progress estimate

A preliminary estimate is 30–40% complete, 60–70% remaining. This is subjective: the assignment brief is unavailable and the full test suite has not been verified. Reassess against agreed acceptance criteria after the end-to-end flow works.
