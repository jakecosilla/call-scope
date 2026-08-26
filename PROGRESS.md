# Project Progress

## Current Status
Current phase: Production hardening and validation
Overall status: Core workflow implemented; benchmark and hosted deployment still require final verification
Last updated: 2026-08-27

## Completed in Latest Pass
- Removed hard-coded authentication backdoors and frontend credential auto-fill.
- Replaced custom JWT implementation with PyJWT.
- Added genuine browser folder selection and relative-path packaging.
- Made malformed manifest labels fail explicitly.
- Added background-noise-type evaluation.
- Added bounded CPU inference concurrency.
- Removed committed SQLite runtime database and made its path configurable.
- Wired CPU and memory cost inputs through configuration.
- Added browser E2E wiring.
- Added Azure OIDC, frontend TEST/PROD deployment, and exact TEST-approved backend image promotion.

## Still Requires Verification
- Run both real assessment benchmarks and record factual metrics.
- Validate acoustic thresholds on independent audio; three supplied calls are insufficient to prove generalization.
- Execute TEST and PROD Azure workflows with real resources/secrets.
- Replace container-local SQLite with externally durable storage before enabling multi-replica production.
- Add durable audio staging if restart-resumable in-flight jobs are required.

## Rule
Do not claim 100% accuracy, production hardening, or deployment success unless the corresponding evidence was actually produced.

## 2026-08-27 — Upload/type/E2E dependency fixes
- Corrected `BatchProcessor.process_zip_bytes` return typing so manifest validation is explicitly optional when no manifest is supplied.
- Added a typed `ManifestValidation` contract for backend validation results.
- Added a manifest-specific error for standalone `labels.csv` uploads.
- Updated the React upload flow so separately selected audio files and `labels.csv` are merged into one batch instead of replacing the previous selection.
- Added client-side validation for CSV-only batches, multiple manifests, and ZIP-plus-loose-file combinations.
- Added `@playwright/test` as an explicit dev dependency and changed `test:e2e` to use the installed Playwright binary.
- Added React typing for `webkitdirectory` folder input support.
- Added backend regression tests for no-manifest return typing behavior and standalone CSV handling.
- Backend validation: `19 passed`.
- Frontend install/build remains to be run in an environment with npm registry access; the dependency and lockfile entries were updated consistently.
