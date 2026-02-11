# ADR-007: SFTP Polling over Push-Based File Ingestion

**Date:** 2025-02-10

**Status:** Accepted

## Context

DebtFlow must ingest debt portfolio files from creditor clients. These files
contain account placements, balance updates, and payment records in CSV or
fixed-width formats. We need to decide how files enter the system.

Approaches considered:

- **API push:** Clients upload files via a REST API endpoint. DebtFlow processes
  them immediately.
- **S3 event-driven:** Clients upload to a shared S3 bucket. Lambda or S3 event
  notifications trigger processing.
- **SFTP polling:** Clients deposit files on an SFTP server. DebtFlow polls the
  server on a schedule and pulls new files for processing.

## Decision

We will use **SFTP polling on a 15-minute interval** as the primary file
ingestion mechanism.

Architecture:

- AWS Transfer Family provides a managed SFTP endpoint.
- Each client has an isolated SFTP directory with unique credentials.
- A Celery Beat task runs every 15 minutes, scanning client directories for
  new files.
- New files are moved to an S3 processing bucket, and a Celery task is
  enqueued for parsing and validation.
- Processed files are moved to an archive prefix in S3. Failed files are moved
  to a quarantine prefix with error metadata.

## Consequences

**Positive:**

- SFTP is the **industry standard** for debt collection file exchange. Creditor
  clients and partner agencies already have established SFTP workflows and
  tooling — no client-side development required.
- AWS Transfer Family eliminates the need to manage SFTP server infrastructure.
- Polling is simple to reason about and debug. The system pulls files at a
  predictable cadence.
- 15-minute intervals provide near-real-time ingestion for a batch-oriented
  workflow. Most clients deposit files once or twice daily.

**Negative:**

- Polling introduces up to 15 minutes of latency between file deposit and
  processing start. This is acceptable for batch file workflows.
- SFTP provides no built-in delivery confirmation to the client. Clients do
  not know if their file was received or processed without a separate
  notification mechanism.
- File-based integration is inherently less structured than API-based — files
  may have formatting errors, encoding issues, or unexpected schemas.

**Mitigations:**

- Configurable polling interval per client if lower latency is needed.
- Post-processing notification emails sent to clients with file receipt
  confirmation and any validation errors.
- Robust file validation layer with detailed error reporting and quarantine
  for malformed files.
- File checksums and duplicate detection to prevent reprocessing.
