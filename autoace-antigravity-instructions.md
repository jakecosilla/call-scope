# CallScope AI Software Engineer Assessment — Antigravity Build Instructions

## Mission

Build a complete, hosted, production-ready submission for the software engineering assessment.

Prioritize a reliable vertical slice over architectural breadth.

The application must be:

- correct
- testable
- hosted
- cost-conscious
- easy to explain in an interview
- structured so it can evolve into future Azure production environment
- free of AI-style code comments or references to coding assistants

The most important scoring priority is **hidden-set prediction performance**, followed by cost efficiency, technical rigor, production practicality, dashboard usability, and communication.

Do not spend excessive time polishing UI or building infrastructure that does not directly improve the assessment score.

---

# 1. Read the Assessment First

The assessment files are located inside this folder at the repository root:

```text
/Software Engineer Assessment
```

Treat this directory as the source location for all supplied assessment assets.

Before writing implementation code:

1. Inspect `/Software Engineer Assessment`.
2. Read every assessment document and supplied file in that directory.
3. Inspect the provided labeled production calls.
4. Inspect `labels.csv`.
5. Extract all required output fields and allowed values.
6. Identify all mandatory dashboard, upload, validation, export, hosting, cost, latency, and documentation requirements.
7. Create a short internal implementation checklist from the assessment.
8. Do not invent requirements that conflict with the assessment document.

Do not move, rename, overwrite, or delete the original assessment files unless there is a clear technical need.

When tests or local smoke checks need sample fixtures, reference or copy from `/Software Engineer Assessment` in a controlled way rather than modifying the originals.

Treat the supplied assessment document as the source of truth.

# 3. Required Stack

## Frontend

Use:

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- TanStack Query
- React Hook Form where forms justify it
- Zod for client-side validation
- Vitest
- React Testing Library
- Playwright for the main end-to-end workflow

Do not use Next.js unless a concrete assessment requirement requires SSR or server components.

This is an authenticated operational dashboard. A React SPA is sufficient.

## Backend

Use:

- Python 3.12+
- FastAPI
- Pydantic
- pytest
- httpx / FastAPI testing utilities
- FFmpeg
- torchaudio and/or librosa
- PyTorch / Hugging Face where useful
- ONNX Runtime where it provides measurable latency or cost benefits

Prefer Python over .NET for this assessment because the core workload is audio inference and ML experimentation.

Keep the backend containerized and portable so it can later run unchanged or with minimal configuration changes in Azure Container Apps.

---

# 4. Initial Hosting Target

Deploy directly to Azure if practical within the assessment window.

Preferred minimal Azure architecture:

```text
React + Vite
    |
    v
Azure Static Web Apps
    |
    v
FastAPI
Azure Container Apps
    |
    +--> Audio / ML inference
    |
    +--> Blob Storage if required
    |
    +--> Persistent metadata storage if required
```

Keep infrastructure minimal.

Use Azure Container Apps Consumption where practical.

Prefer:

```text
min replicas: 0
max replicas: 1 or 2
```

for the assessment deployment if cold starts are acceptable.

Use CPU inference first.

Do not provision GPU infrastructure unless measurements show it is genuinely required.

The application must remain portable. Business and ML logic must not depend directly on Azure-specific APIs.

---

# 5. Architecture Principle

Use a **modular monolith**.

Do not start with microservices.

Suggested backend structure:

```text
backend/
  app/
    api/
    application/
    domain/
    audio/
    inference/
    evaluation/
    storage/
    persistence/
    security/
    observability/
  tests/
```

Suggested frontend structure:

```text
frontend/
  src/
    app/
    features/
      auth/
      upload/
      batches/
      results/
      evaluation/
    components/
    api/
    hooks/
    lib/
    types/
    test/
```

Separate:

- HTTP/API handling
- batch orchestration
- audio preprocessing
- inference
- evaluation
- confidence calculation
- storage
- persistence
- exports

The inference implementation must sit behind a clean interface so models can be swapped without rewriting API or batch-processing code.

---

# 6. Exact Required Prediction Schema

Produce the assessment's exact required prediction structure:

```json
{
  "emotional_tone": "neutral",
  "emotional_intensity": "low",
  "background_noise_present": true,
  "background_noise_type": "",
  "background_noise_severity": "low",
  "audio_quality": "clear",
  "speaker_overlap_present": false,
  "long_silence_present": false,
  "confidence": 0.82
}
```

Use strongly validated internal enums.

Allowed values must match the assessment exactly.

Do not add extra fields to exported assessment results unless the assessment explicitly allows them.

Internal metadata such as model version, processing duration, and cost may be stored separately.

---

# 7. Do Not Hard-Code Assessment Answers

Never:

- special-case supplied filenames
- hard-code labels from `labels.csv`
- hard-code confidence to `0.82`
- return fixed predictions
- fake evaluation metrics
- fake cost measurements
- fake progress
- claim validation that was not actually performed

The system must work on unseen audio.

---

# 8. Treat Prediction Dimensions Independently

Do not infer unrelated dimensions from the same simplistic signal.

Examples:

- loudness alone does not mean frustration
- high energy alone does not mean distress
- poor quality alone does not mean environmental background noise
- static is not automatically environmental noise
- silence detection should not require an LLM
- clipping should not be classified through semantic transcript analysis

Use the appropriate method for each output dimension.

---

# 9. Build the ML Pipeline Before the Dashboard

The assessment's hidden-set performance is the highest-value scoring category.

Do not build a polished dashboard first.

Start with a command-line or test harness capable of:

```text
audio file
  ->
preprocessing
  ->
prediction
  ->
exact result schema
```

Run this against the supplied calls before building the full web application.

---

# 10. Approach A — Task-Specific / Acoustic Pipeline

Implement one serious baseline using task-specific models and deterministic signal processing.

Potential components:

## Emotion

Use one or more of:

- pretrained speech emotion recognition model
- prosodic features
- pitch
- speaking rate
- energy
- transcript sentiment/emotion when useful

Do not fine-tune a large model on only the three supplied calls.

## Long Silence

Use deterministic:

- VAD
- silence duration thresholds

This should be inexpensive and reproducible.

## Audio Quality

Evaluate signals such as:

- clipping
- distortion
- static
- SNR
- low volume
- excessive noise
- codec artifacts where reasonably detectable

## Background Noise

Use:

- acoustic event classification where useful
- noise features
- signal analysis

Separate:

```text
background_noise_present
background_noise_type
background_noise_severity
```

## Speaker Overlap

Use a practical overlap / diarization technique appropriate to the time constraint.

Avoid building a large diarization system from scratch.

---

# 11. Approach B — Materially Different Baseline

The assessment expects comparison of materially different approaches.

Implement a second baseline.

Good options include:

- an audio-capable foundation model
- transcript + language-model classification
- a different pretrained acoustic architecture
- another genuinely distinct inference strategy

Do not call two slightly different thresholds on the same model two different approaches.

For each approach measure:

- prediction quality on available labeled examples
- latency
- estimated cost per audio minute
- privacy implications
- operational complexity

---

# 12. Select the Final Pipeline

Choose the production inference approach based on evidence.

Evaluate:

1. likely generalization
2. available validation performance
3. macro F1 where meaningful
4. per-field accuracy
5. latency
6. cost
7. privacy
8. operational complexity

A hybrid pipeline is allowed if it demonstrably improves results.

Do not build an ensemble merely to look sophisticated.

---

# 13. Confidence Calculation

Confidence must be meaningful.

Do not return a fixed value.

Potential inputs:

- classifier probabilities
- prediction margins
- agreement between independent signals/models
- audio quality
- model uncertainty

Ensure:

```text
0.0 <= confidence <= 1.0
```

Document the calculation in the technical memo.

---

# 14. Cost Requirement

The assessment requires inference cost to remain at or below the specified per-minute limit.

Measure and document:

- audio duration
- preprocessing time
- inference time
- total processing time
- model/runtime used
- compute assumptions
- estimated inference cost
- cost per audio minute

Do not make unsupported Azure cost claims.

Explicitly show the formula.

Example:

```text
worker compute cost per hour
x processing hours
/ processed audio minutes
= compute cost per audio minute
```

Separate infrastructure cost from inference cost.

Use CPU inference first.

---

# 15. Latency Measurement

Record:

- audio duration
- preprocessing duration
- inference duration
- total duration

Calculate real-time factor:

```text
RTF = processing_seconds / audio_seconds
```

Report aggregate measurements in the memo.

---

# 16. Upload Workflow

Support the assessment-required batch workflow.

At minimum support:

- ZIP upload
- supported audio files
- optional CSV manifest

Support common formats accepted by FFmpeg, including the formats required by the supplied data.

Normalize audio internally when necessary.

Do not permanently retain normalized duplicates unless needed.

---

# 17. ZIP Security and Validation

Implement:

- ZIP-slip/path traversal protection
- maximum upload size
- maximum decompressed size
- supported extension validation
- safe generated internal filenames
- rejection of unexpected executable files

Do not trust filenames from uploads.

---

# 18. Manifest Validation

Support the required CSV shape:

```text
name,result_json
```

Validate:

- duplicate names
- missing audio files
- manifest entries with no matching file
- files with no manifest entry where relevant
- invalid JSON
- invalid expected schema
- unsupported files

Hidden evaluation batches may not contain labels.

Do not require `result_json` to run inference.

---

# 19. Batch Processing

Represent each upload as a batch.

Useful batch statuses:

```text
uploaded
validating
processing
completed
completed_with_errors
failed
```

Each file should have its own processing status.

One failed file must not fail the entire batch.

Persist or retain enough information to show the evaluator:

- processed files
- failed files
- failure reason
- results

Do not expose stack traces.

---

# 20. Progress

Expose batch progress through the API.

The UI should show:

```text
17 / 25 processed
68%
```

For the initial assessment, polling is acceptable.

Use TanStack Query polling.

Stop polling when the batch reaches a terminal state.

Do not introduce WebSockets unless genuinely necessary.

---

# 21. Required API Surface

Keep the API small.

Suggested endpoints:

```text
POST /api/auth/login

POST /api/batches
GET  /api/batches/{batchId}
GET  /api/batches/{batchId}/results

GET  /api/batches/{batchId}/results.csv
GET  /api/batches/{batchId}/results.json

GET  /api/health
```

A readiness endpoint may be added if useful.

Use structured error responses and correct HTTP status codes.

---

# 22. Authentication

The evaluator must be able to log in.

Implement the simplest secure authentication appropriate for the trial.

Requirements:

- no plaintext passwords
- no committed credentials
- secure password hashing
- HTTP-only secure cookie or appropriately handled token
- working evaluator credentials documented securely for submission

Do not build:

- enterprise SSO
- complicated OAuth
- role hierarchies

unless explicitly required.

---

# 23. Persistence Strategy

Do not add PostgreSQL merely because it looks production-ready.

Use it only if needed for reliable hosted operation within the available time.

A simpler persistent store is acceptable if it satisfies the assessment cleanly.

However:

- do not rely exclusively on in-memory state if a restart would destroy the evaluator's active batch
- do not permanently store confidential audio unnecessarily

If PostgreSQL is used, keep the schema small.

Suggested entities:

```text
Batch
BatchFile
Prediction
```

---

# 24. Storage

Prefer Azure Blob Storage if persistent uploaded audio or generated exports are required.

Keep containers private.

Use short retention.

Avoid storing confidential audio longer than necessary.

Document the retention strategy.

The application should abstract object storage enough that the implementation can be swapped, but do not build a large storage framework.

---

# 25. React Dashboard

Build a simple professional operational UI.

Required screens:

## Login

- username/email
- password
- login action
- clear error handling

## Upload

- drag-and-drop or file chooser
- ZIP/audio support
- optional CSV manifest
- validation feedback
- explicit Start Analysis action

## Processing

Show:

- status
- total files
- processed count
- failed count
- percentage
- elapsed processing time where practical

## Results

Show a table containing the assessment output fields.

At minimum:

- filename
- emotional tone
- emotional intensity
- background noise present
- background noise type
- background noise severity
- audio quality
- speaker overlap
- long silence
- confidence
- processing status

## Download

Provide:

- CSV download
- JSON download

Preserve original filename mapping.

---

# 26. UI Rules

Keep UI functional and clean.

Do not spend assessment time on elaborate styling.

Use accessible shadcn/ui components.

Ensure:

- keyboard accessibility
- semantic HTML
- form labels
- loading states
- disabled states
- understandable error states

Do not rely on color alone for status.

Desktop is the primary target.

Reasonable tablet/mobile behavior is enough.

---

# 27. Evaluation Utilities

When labels are available, provide an evaluation utility or optional page.

Calculate appropriate metrics.

For emotional tone:

- accuracy
- macro F1
- per-class precision
- per-class recall
- per-class F1
- confusion matrix when meaningful

For other dimensions calculate suitable accuracy/F1 values.

Clearly state that three provided labeled examples are far too small to establish reliable production accuracy.

Do not exaggerate statistical significance.

---

# 28. Tests Are Mandatory

Do not consider the project complete unless tests pass.

## Backend Unit Tests

Prioritize:

- prediction schema
- enums
- manifest parser
- ZIP validation
- safe filenames
- batch failure isolation
- deterministic silence logic
- quality calculations
- confidence boundaries
- cost calculations

## API Integration Tests

Prioritize:

- login
- valid upload
- invalid ZIP
- invalid CSV
- unsupported audio
- partial batch failure
- status/progress
- CSV export
- JSON export

## ML Tests

Test deterministic contracts rather than arbitrary probabilistic output.

Examples:

- preprocessing output
- supported sample rates
- schema validity
- valid enum values
- confidence range
- corrupted audio handling

Use supplied calls as smoke/integration fixtures where practical.

## Frontend Tests

Test:

- login validation
- upload behavior
- progress UI
- completed results
- partial failure state
- export actions

## E2E

Add one Playwright happy path:

```text
login
-> upload
-> process
-> view results
-> download
```

Add one partial-failure flow only if time permits.

---

# 29. Code Quality

Use:

- explicit types
- cohesive functions
- dependency injection where useful
- composition
- straightforward control flow
- clean boundaries

Avoid:

- God classes
- unnecessary base classes
- generic abstraction for its own sake
- excessive repositories
- premature patterns
- duplicated logic
- giant React page components
- excessive custom hooks
- unnecessary global state
- unnecessary `useMemo`
- unnecessary `useCallback`
- unnecessary `useEffect`

Use TanStack Query for server state.

Do not copy query responses into redundant React state.

---

# 30. No AI-Style Comments

Do not add comments that narrate obvious code.

Do not write comments such as:

```text
// Fetch the data
// Loop through the files
// Validate the request
// Handle the response
// Generated by AI
```

Code should be understandable through naming and structure.

Comments are acceptable only when explaining:

- a non-obvious algorithm
- an important tradeoff
- a surprising constraint
- the reason for a workaround

Comments should explain **why**, not **what**.

Never mention any coding assistant in:

- source code
- comments
- README
- documentation
- commit messages
- generated configuration

Do not mention:

- Antigravity
- ChatGPT
- Claude
- Copilot
- AI-generated code

---

# 31. Security and Privacy

Production call audio is confidential.

Implement practical safeguards:

- upload limits
- filename sanitization
- private storage
- safe ZIP extraction
- no raw audio logging
- no credential logging
- no stack traces returned to clients
- configuration through environment variables
- short configurable audio retention

Document:

- where audio is stored
- whether audio leaves the deployed environment
- when it is deleted
- whether any third-party inference service receives it

---

# 32. Model Lifecycle

Do not load ML models separately for every audio file.

Load model(s) once per application/worker process and reuse them.

Avoid downloading large models on every request.

Pin important model and dependency versions.

Track an internal pipeline version.

Example:

```text
2026-08-26.1
```

Do not add pipeline metadata to the exported prediction JSON if doing so violates the required schema.

---

# 33. Docker

Provide a production Dockerfile for FastAPI/inference.

It must include:

- Python runtime
- application dependencies
- FFmpeg
- audio dependencies
- required ML runtime

The same image should work locally and later in Azure Container Apps.

---

# 34. Local Development

Provide simple local instructions.

Prefer:

```bash
docker compose up
```

or an equally simple workflow.

Do not require Azure to run core application tests locally.

---

# 35. CI

If time permits, add a concise GitHub Actions pipeline:

```text
frontend install
frontend lint
frontend tests
frontend build

backend install
backend tests
backend lint/type checks where configured
```

Do not spend major assessment time building elaborate deployment pipelines.

---

# 36. README

A production-ready `README.md` is mandatory.

The README must be sufficient for:

1. a new engineer to run the entire system locally
2. a reviewer to understand the architecture
3. an engineer to deploy the application to TEST
4. an engineer to promote the tested version to PROD
5. an engineer to verify and troubleshoot a deployment
6. an engineer to roll back to a previous known-good release

Do not write a minimal README that only contains a few commands.

The README should be accurate to the actual repository and deployment implementation.

## 36.1 Required README Sections

Include at minimum:

1. project overview
2. architecture
3. technology choices
4. repository structure
5. prerequisites
6. local setup
7. local environment variables
8. running the frontend locally
9. running the backend locally
10. running background processing locally if applicable
11. local database/storage setup if applicable
12. model setup and model artifact requirements
13. running tests
14. supported batch/upload format
15. API overview
16. local troubleshooting
17. TEST deployment
18. PROD deployment
19. CI/CD pipeline behavior
20. environment-specific configuration
21. database migrations
22. deployment verification / smoke tests
23. rollback procedure
24. versioning / image tags
25. Azure resources used
26. cost assumptions
27. privacy and audio retention
28. known limitations

A new engineer should be able to clone the repository and follow the README without relying on undocumented tribal knowledge.

---

## 36.2 Local Setup Instructions

The README must provide exact local setup steps.

Prefer a workflow such as:

```bash
git clone <repository>
cd <repository>

cp .env.example .env

docker compose up
```

or document the actual equivalent used by the project.

If frontend and backend are started separately, provide exact commands.

Example:

```bash
# backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install ...
uvicorn app.main:app --reload

# frontend
cd frontend
npm ci
npm run dev
```

Do not include commands that are not verified against the repository.

Document:

- required Python version
- required Node.js version
- Docker requirement
- FFmpeg requirement if not provided by Docker
- database requirements
- storage emulator requirements
- model download/setup
- default local ports
- frontend/backend URLs

---

## 36.3 `.env.example`

Provide a committed:

```text
.env.example
```

containing all required configuration keys with safe placeholder values.

Document every variable in the README.

Examples may include:

```text
APP_ENV
DATABASE_URL
STORAGE_CONNECTION
FRONTEND_ORIGIN
API_BASE_URL
MODEL_PATH
MODEL_VERSION
AUDIO_RETENTION_DAYS
LOG_LEVEL
```

Never include real secrets.

Clearly identify which variables are:

- required locally
- required in TEST
- required in PROD
- optional

---

## 36.4 Local Dependencies

Document how to run required dependencies locally.

Examples:

```text
PostgreSQL
Azurite / local object storage
worker
```

If Docker Compose is used, explain what each service does.

Example:

```text
frontend
backend
worker
postgres
azurite
```

If a service is optional for the initial architecture, say so explicitly.

---

## 36.5 Running Tests Locally

Provide exact verified commands for:

### Frontend

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

### Backend

```bash
pytest
```

and any configured lint/type-check commands.

### End-to-End

Document the Playwright command.

Explain prerequisites for E2E tests.

Do not claim a command works unless it was actually validated.

---

## 36.6 Local Smoke Test

Document a short manual local verification workflow.

Example:

```text
1. Start application.
2. Open frontend.
3. Log in using local evaluator credentials.
4. Upload a small sample batch.
5. Start processing.
6. Verify progress updates.
7. Verify results.
8. Download CSV.
9. Download JSON.
```

This should give a new engineer a quick way to confirm the environment is working.

---

## 36.7 TEST Deployment Instructions

Document the complete TEST deployment path.

Explain:

```text
feature branch
-> Pull Request
-> CI
-> merge to develop
-> automatic TEST deployment
```

Include:

- branch that deploys TEST
- GitHub Actions workflow name
- Azure resources targeted
- required GitHub Environment
- required Azure OIDC/workload identity setup
- container registry
- frontend hosting target
- backend hosting target
- TEST environment variables
- migration behavior
- health checks
- smoke tests

Explain how to determine whether deployment succeeded.

Include commands or Azure Portal locations only when they are actually relevant and verified.

---

## 36.8 PROD Deployment Instructions

Document the complete production promotion process.

Preferred flow:

```text
tested immutable artifact
-> Pull Request / release to main
-> CI verification
-> production environment approval
-> deploy same immutable artifact
-> health checks
-> production smoke test
```

Document:

- production branch/release trigger
- GitHub Actions workflow
- manual approval step
- exact artifact/image promotion behavior
- production environment variables
- migrations
- health verification
- smoke tests

Make it clear that PROD should use the same backend image that passed TEST when practical.

---

## 36.9 First-Time Azure Setup

If Azure resources require one-time provisioning outside the normal deployment pipeline, document it separately.

Include only the actual resources used.

Examples:

```text
Azure Static Web Apps
Azure Container Apps
Azure Container Registry
Azure Blob Storage
Azure Database for PostgreSQL
```

Explain:

- resource purpose
- required naming/configuration
- identity/RBAC requirements
- GitHub OIDC setup
- environment setup

Do not assume the reader already knows which Azure resources must exist.

If infrastructure is fully provisioned through IaC later, point the README to the IaC commands instead of duplicating manual instructions.

---

## 36.10 CI/CD Documentation

Document what happens for each workflow.

### Pull Request

Explain:

- lint
- type checking
- tests
- build
- Docker validation
- lightweight ML contract tests

### TEST

Explain:

- artifact build
- image tagging
- registry push
- deployment
- health checks
- smoke tests

### PROD

Explain:

- approval
- artifact promotion
- deployment
- verification

Include the workflow filenames.

Example:

```text
.github/workflows/pr.yml
.github/workflows/deploy-test.yml
.github/workflows/deploy-prod.yml
```

---

## 36.11 Versioning and Artifact Promotion

Explain the versioning strategy.

Example:

```text
Git SHA:
sha-a8d31f2

Optional release:
v1.0.0
```

Document how to identify:

- version currently running in TEST
- version currently running in PROD
- previous known-good version

Explain that mutable `latest` tags are not the source of truth.

---

## 36.12 Database Migration Instructions

If a relational database exists, document:

- migration framework
- creating migrations
- applying migrations locally
- applying migrations in TEST
- applying migrations in PROD
- rollback/forward-fix policy

Prefer backward-compatible migrations.

If the initial implementation has no database, explicitly state that migrations are not applicable rather than leaving unclear instructions.

---

## 36.13 Deployment Verification

Document post-deployment verification.

At minimum:

```text
GET /api/health
GET /api/ready
```

plus appropriate frontend verification.

Explain what success looks like.

Document TEST smoke tests.

Document the smaller non-destructive PROD smoke test.

---

## 36.14 Rollback Instructions

The README must explain how to roll back a bad production deployment.

At minimum cover:

1. identify the previous known-good version
2. redeploy the immutable previous backend image
3. restore frontend release if necessary
4. verify health/readiness
5. execute smoke tests
6. review logs
7. handle schema compatibility if a migration was involved

Do not write vague instructions such as:

```text
Rollback the deployment.
```

Provide the actual project-specific process.

---

## 36.15 Troubleshooting

Include common problems relevant to the project.

Examples:

- backend cannot find FFmpeg
- model cannot load
- storage connection fails
- CORS blocks frontend
- database connection fails
- Azure Container App fails to start
- health check fails
- upload size is rejected
- ML model memory usage is too high
- TEST deploy succeeds but smoke tests fail

For each, provide a concise diagnostic direction.

---

## 36.16 README Validation

Before considering documentation complete, follow the README from a clean or reasonably clean environment.

Verify that:

- [ ] prerequisites are correct
- [ ] local setup works
- [ ] frontend starts
- [ ] backend starts
- [ ] dependencies start
- [ ] tests can be run using documented commands
- [ ] sample processing works
- [ ] TEST deployment process is documented
- [ ] PROD promotion process is documented
- [ ] environment variables are documented
- [ ] migrations are documented if applicable
- [ ] smoke tests are documented
- [ ] rollback is documented
- [ ] no secret values are present
- [ ] no coding-assistant references are present

Record README validation in `PROGRESS.md`.

---

# 37. Technical Memo

Create a concise technical memo covering:

## Problem

Explain the prediction dimensions and why they should be evaluated independently.

## Approaches

Document at least two materially different approaches.

For each:

- architecture
- strengths
- weaknesses
- validation observations
- latency
- cost
- privacy implications

## Final Selection

Explain why the chosen production pipeline was selected.

## Validation

Include:

- metrics
- available results
- per-class performance where meaningful
- confusion matrix where meaningful
- data limitations

## Cost

Show the actual calculation.

## Latency

Show measured runtime and RTF.

## Privacy

State whether audio leaves the environment.

## Failure Modes

Discuss realistic limitations such as:

- sarcasm
- subtle frustration
- mixed emotional states
- severe compression
- multiple speakers
- overlapping speech
- environmental music
- short calls
- non-English calls
- telephony codecs

## Next Steps

Explain what additional labeled production data would enable.

---

# 38. Execution Plan

## Day 1 — Inference First

### Step 1 — Requirements and Samples

Target: ~1 hour

- inspect every supplied file
- confirm exact required schema
- inspect labels
- inspect audio durations/codecs
- create evaluation harness

### Step 2 — Approach A

Target: ~3 hours

- preprocessing
- task-specific/acoustic baseline
- deterministic silence/quality/noise features
- produce exact schema

### Step 3 — Approach B

Target: ~2 hours

- implement materially different baseline
- run against supplied labeled calls

### Step 4 — Compare

Target: ~1 hour

Compare:

- predictions
- available metrics
- latency
- cost
- privacy
- complexity

Select final pipeline or justified hybrid.

### Step 5 — Confidence and Output

Target: ~1 hour

- implement confidence calculation
- verify enums
- verify exact schema
- add model/pipeline version internally

### Step 6 — Core Backend

Target: ~2 hours

- FastAPI
- upload
- batch processing
- per-file failure isolation
- status
- results
- export

---

# 39. Productize and Ship

### Step 7 — React Dashboard

Target: ~2 hours

Build:

- login
- upload
- processing progress
- results table
- download actions

### Step 8 — Validation and Edge Cases

Target: ~1 hour

Cover:

- ZIP validation
- CSV validation
- corrupt audio
- unsupported file
- partial batch failure

### Step 9 — Tests

Target: ~2 hours

Focus on high-value backend and frontend behavior.

Do not chase arbitrary coverage percentages.

### Step 10 — Azure Deployment

Target: ~1–2 hours

Deploy the smallest reliable hosted architecture.

Prefer:

- React static hosting
- Azure Container Apps for FastAPI/inference
- Blob Storage only if needed
- minimal persistence

### Step 11 — Benchmark

Target: ~1 hour

Capture:

- latency
- RTF
- compute assumptions
- cost per audio minute

### Step 12 — Documentation

Target: ~1–2 hours

Finish:

- README
- technical memo
- evaluator credentials/instructions
- known limitations
- architecture diagram

### Step 13 — Final Verification

Run:

- backend tests
- frontend tests
- E2E happy path
- supplied evaluation batch
- deployed hosted workflow
- CSV download
- JSON download

Confirm no secrets or coding-assistant references are committed.

---

# 40. Definition of Done for the Assessment

Do not mark the assessment complete until all mandatory items work.

- [ ] hosted application is reachable
- [ ] evaluator can log in
- [ ] ZIP/batch upload works
- [ ] CSV manifest validation works
- [ ] supplied audio formats work
- [ ] unseen files can be processed
- [ ] one bad file does not fail the entire batch
- [ ] progress is visible
- [ ] exact prediction schema is returned
- [ ] confidence is meaningful
- [ ] CSV export works
- [ ] JSON export works
- [ ] original filenames are preserved
- [ ] at least two materially different inference approaches were compared
- [ ] final inference approach is justified
- [ ] latency was measured
- [ ] cost per audio minute was calculated
- [ ] inference cost satisfies the assessment limit
- [ ] tests pass
- [ ] README exists
- [ ] technical memo exists
- [ ] privacy implications are documented
- [ ] supplied calls have predictions
- [ ] hosted system has been manually verified
- [ ] no assessment labels are hard-coded
- [ ] no secrets are committed
- [ ] no AI-style comments exist
- [ ] no coding-assistant references exist

---


# 41. CI/CD Pipeline — Required Before Submission

CI/CD is part of the production-ready implementation and must be included in the core assessment scope.

Use GitHub Actions.

The pipeline must support:

```text
feature branch
    |
    v
Pull Request
    |
    +--> frontend checks
    +--> backend checks
    +--> tests
    +--> security checks where practical
    +--> Docker build validation
    |
    v
merge to develop
    |
    v
deploy TEST automatically
    |
    +--> health checks
    +--> smoke tests
    |
    v
merge/release to main
    |
    v
manual PROD approval
    |
    v
deploy PROD
    |
    +--> production smoke test
    +--> rollback capability
```

---

## 41.1 Branch Strategy

Use a simple branch strategy:

```text
feature/*
   |
   v
develop
   |
   v
main
```

Use:

- feature branches for development
- `develop` as the TEST integration branch
- `main` as the PROD/release branch

Do not introduce unnecessary GitFlow complexity.

Pull requests should target either:

```text
develop
```

or, for release promotion:

```text
main
```

---

## 41.2 Pull Request Pipeline

Every pull request must automatically run CI.

A pull request must not be considered ready to merge unless mandatory CI checks pass.

### Frontend Checks

Run:

- dependency installation using the lockfile
- lint
- TypeScript type checking
- Vitest tests
- React Testing Library tests
- production build

Example logical flow:

```text
npm ci
-> lint
-> typecheck
-> test
-> build
```

Do not deploy normal PR branches to TEST or PROD.

---

## 41.3 Backend Checks

Run:

- install locked Python dependencies
- lint
- type checking where configured
- pytest unit tests
- API integration tests
- application startup validation
- Docker image build validation

Example:

```text
install
-> lint
-> typecheck
-> pytest
-> integration tests
-> docker build
```

A failed mandatory backend test must fail the PR check.

---

## 41.4 ML / Inference Validation in CI

Do not run expensive full ML inference across large datasets on every PR.

CI should run lightweight deterministic checks such as:

- inference pipeline imports successfully
- model configuration validates
- preprocessing works on a small fixture
- exact output schema is produced
- enums are valid
- confidence remains between `0.0` and `1.0`
- corrupted input is handled correctly

If a lightweight model fixture is practical, run one smoke inference.

Do not make CI dependent on expensive external model APIs unless unavoidable.

---

## 41.5 Security Checks

Where practical within the assessment window, add:

- dependency vulnerability scanning
- secret detection
- container image vulnerability scanning

These should be useful and reliable.

Do not spend excessive assessment time configuring complex security tooling if it risks delaying the core submission.

Never commit:

- cloud credentials
- database passwords
- API tokens
- signing secrets
- evaluator passwords in plaintext

---

## 41.6 TEST Deployment

Merging into:

```text
develop
```

must trigger automatic TEST deployment.

The deployment workflow should:

1. run the complete required CI suite
2. build the frontend production artifact
3. build the backend Docker image
4. tag the backend image using the Git commit SHA
5. push the immutable image to the configured container registry
6. deploy the frontend to TEST
7. deploy the exact backend image to TEST
8. run database migrations if applicable
9. wait for the deployment to become healthy
10. run TEST smoke tests
11. mark deployment failed if health checks or smoke tests fail

Example image version:

```text
callscope-api:sha-a8d31f2
```

Do not rely exclusively on:

```text
latest
```

for deployments.

---

## 41.7 TEST Environment

TEST must use separate configuration from PROD.

At minimum separate:

- API base URL
- database connection
- storage configuration
- authentication configuration
- allowed frontend origin
- log level
- application environment

Example:

```text
APP_ENV=test
DATABASE_URL=...
STORAGE_CONNECTION=...
FRONTEND_ORIGIN=...
API_BASE_URL=...
LOG_LEVEL=Information
```

Do not hard-code environment URLs in application source code.

---

## 41.8 TEST Smoke Tests

After TEST deployment, automatically verify:

- frontend is reachable
- backend health endpoint succeeds
- backend readiness endpoint succeeds if implemented
- login works
- basic API access works
- a minimal upload/process/results path works where practical

Prefer a tiny deterministic audio fixture for deployed smoke testing.

Do not run a large or expensive ML benchmark after every deployment.

If a smoke test fails, the TEST deployment must be reported as failed.

---

## 41.9 Production Deployment

Production must deploy from:

```text
main
```

or from an explicit versioned release/tag.

Preferred promotion flow:

```text
TEST-approved commit/image
        |
        v
Pull Request to main
        |
        v
CI
        |
        v
manual production approval
        |
        v
deploy exact immutable artifact to PROD
```

Use a manual approval gate for PROD.

Do not automatically deploy every development merge directly to production.

---

## 41.10 Build Once, Promote the Same Artifact

Do not rebuild different backend binaries/images independently for TEST and PROD if avoidable.

The backend image tested in TEST should be the same immutable image promoted to PROD.

Example:

```text
TEST:
callscope-api:sha-a8d31f2

PROD:
callscope-api:sha-a8d31f2
```

Only configuration should differ.

This reduces environment drift and proves that PROD is running the artifact that passed TEST.

For the React frontend, use the same principle where the hosting platform and runtime configuration strategy allow it.

---

## 41.11 GitHub Environments

Use GitHub Environments:

```text
test
production
```

Use environment-specific:

- variables
- secrets
- deployment approvals

Configure:

```text
production
```

with a manual approval requirement where supported.

Do not reuse TEST credentials in PROD.

---

## 41.12 Azure Authentication from GitHub

When deploying to Azure, prefer:

```text
GitHub Actions
      |
      v
OIDC / Workload Identity Federation
      |
      v
Azure
```

Avoid long-lived Azure username/password credentials when OIDC is available.

Use least-privilege Azure permissions for deployment identities.

---

## 41.13 Container Registry

Store backend images in an appropriate container registry.

For Azure production hosting, prefer:

```text
Azure Container Registry
```

Use immutable Git SHA tags.

Optionally also attach semantic release tags:

```text
sha-a8d31f2
v1.0.0
```

Never delete the previous known-good production image immediately after deployment.

---

## 41.14 Database Migrations

If a relational database is used, migrations must be deployment-safe.

Preferred flow:

```text
CI passes
    |
    v
run compatible migration
    |
    v
deploy application
    |
    v
health check
```

Prefer backward-compatible migrations.

Avoid automatic destructive changes such as:

- dropping required columns
- irreversible data deletion
- incompatible schema changes

without an explicit migration plan.

If no database is required for the initial assessment, do not add one solely for pipeline complexity.

---

## 41.15 Backend Health Endpoints

Provide:

```text
GET /api/health
GET /api/ready
```

`/api/health` should verify that the process is alive.

`/api/ready` should verify dependencies required to serve production traffic where practical.

Do not execute expensive ML inference from health endpoints.

Deployment pipelines should call these endpoints after rollout.

---

## 41.16 Production Smoke Test

After PROD deployment, run a small non-destructive smoke test.

Verify:

- frontend is reachable
- API is reachable
- health endpoint succeeds
- readiness endpoint succeeds
- authentication endpoint behaves correctly

Do not run expensive batch inference against production merely as a deployment health check.

---

## 41.17 Rollback

The pipeline must support rollback to the previous known-good release.

Keep immutable historical image versions.

If PROD deployment fails health checks:

1. mark the deployment as failed
2. stop promotion where possible
3. redeploy the previous known-good image/configuration
4. verify health
5. preserve logs for investigation

Do not overwrite immutable release tags.

---

## 41.18 Versioning

Use the Git commit SHA as the primary build identifier.

Example:

```text
sha-a8d31f2
```

Optionally create semantic version tags for formal releases:

```text
v1.0.0
v1.0.1
```

Expose application version/build metadata through an internal endpoint or health metadata where useful.

Do not add deployment metadata to the required assessment prediction JSON.

---

## 41.19 CI/CD Files

Create GitHub Actions workflows with clear responsibility.

Suggested structure:

```text
.github/
  workflows/
    pr.yml
    deploy-test.yml
    deploy-prod.yml
```

Keep workflows understandable.

Do not create one giant workflow containing unrelated conditional logic if separate workflows are clearer.

---

## 41.20 Suggested `pr.yml`

Trigger on pull requests.

Responsibilities:

```text
frontend lint
frontend typecheck
frontend tests
frontend build

backend lint
backend typecheck
backend tests
backend integration tests
backend Docker build

lightweight inference contract checks
security checks where practical
```

No PROD deployment.

No normal TEST deployment from arbitrary feature branches.

---

## 41.21 Suggested `deploy-test.yml`

Trigger on successful merge/push to:

```text
develop
```

Responsibilities:

```text
run/verify CI
-> build immutable artifacts
-> push backend image
-> deploy TEST
-> run migrations if required
-> health check
-> smoke test
```

If deployment verification fails, report the workflow as failed.

---

## 41.22 Suggested `deploy-prod.yml`

Trigger from:

```text
main
```

or a versioned release/tag.

Use the GitHub:

```text
production
```

environment with manual approval.

Responsibilities:

```text
verify release
-> promote immutable artifact
-> deploy PROD
-> health check
-> production smoke test
```

Do not silently continue if deployment checks fail.

---

## 41.23 CI/CD Testing Philosophy

The pipeline should give confidence without making iteration painfully slow.

PR pipelines should prioritize:

- deterministic tests
- short feedback cycles
- compilation/build validation
- API contracts
- safety

Long-running ML benchmarks should run manually or in a dedicated workflow rather than every PR.

---

## 41.24 CI/CD Definition of Done

Do not mark CI/CD complete until:

- [ ] PR pipeline runs automatically
- [ ] frontend lint runs
- [ ] frontend type checking runs
- [ ] frontend tests run
- [ ] frontend production build succeeds
- [ ] backend lint/type checks run where configured
- [ ] backend unit tests run
- [ ] backend API integration tests run
- [ ] backend Docker build succeeds
- [ ] lightweight inference contract validation runs
- [ ] merge to `develop` deploys TEST automatically
- [ ] TEST uses separate configuration
- [ ] TEST health checks run
- [ ] TEST smoke tests run
- [ ] production deploy is separated from TEST
- [ ] PROD requires explicit approval
- [ ] immutable build/image identifiers are used
- [ ] the same tested backend artifact can be promoted to PROD
- [ ] PROD health check runs after deployment
- [ ] rollback path exists
- [ ] secrets are not committed
- [ ] Azure deployment uses OIDC/workload identity where practical

---


# 42. STOP POINT — Submit Before Optional Enhancements

Once every item in the Definition of Done is satisfied:

1. create a clean release/commit
2. verify deployment
3. preserve the working submission
4. do not destabilize the required solution with unnecessary refactors

Only then continue to the optional production-hardening backlog below.

The assessment submission must remain usable while these improvements are added.

---

# 43. Post-MVP Production Hardening — Continue Here After Assessment Is Complete

These items are intentionally deferred until the mandatory assessment requirements are complete and verified.

Antigravity should continue through them sequentially only after all mandatory assessment requirements and tests pass.

For every item:

1. create or update tests first where practical
2. implement the smallest production-worthy solution
3. run the full affected test suite
4. verify no regression to the hosted assessment flow
5. update documentation when architecture changes
6. continue to the next item only when the current item is stable

---

## 43.1 Azure Service Bus

### Goal

Introduce durable asynchronous processing for production-scale call workloads.

### Implement

```text
FastAPI
   |
   v
Azure Service Bus
   |
   v
Inference Worker
```

Add:

- durable job messages
- batch/file identifiers
- retry policy
- dead-letter handling
- idempotent processing
- correlation IDs

Keep queue concerns outside domain and inference logic.

Do not embed Service Bus SDK calls throughout application code.

### Tests

Test:

- enqueueing
- duplicate delivery
- retry behavior
- idempotency
- dead-letter path
- successful worker completion

---

## 43.2 Separate API and Worker Deployments

### Goal

Allow web traffic and ML inference to scale independently.

Continue using the same repository and shared application code unless there is a strong reason not to.

Deploy:

```text
Azure Container App
  API

Azure Container App
  Worker
```

Prefer the same container image with different entry points when practical.

Avoid creating separate repositories.

### Success Criteria

- API does not perform long-running inference
- worker can scale independently
- API remains responsive during large batches
- batch status remains reliable

---

## 43.3 Elaborate Worker Orchestration

Only add orchestration when actual workflow complexity justifies it.

Potential future needs:

- fan-out across many audio files
- retries
- resumable batches
- cancellation
- priority queues
- concurrency limits
- per-model routing
- scheduled cleanup
- dead-letter recovery

Do not introduce orchestration technology merely for architecture aesthetics.

Benchmark first.

---

## 43.4 Azure Key Vault Integration

Move production secrets to Azure Key Vault.

Use Managed Identity where possible.

Potential secrets:

- database credentials
- external model API keys
- signing keys
- storage credentials where Managed Identity cannot replace them

Prefer:

```text
Container App
   |
Managed Identity
   |
Key Vault
```

over long-lived secrets.

Keep local development simple through `.env` or development secret mechanisms.

---

## 43.5 Full Infrastructure as Code

Once the production Azure layout is stable, provision infrastructure through IaC.

Prefer:

- Bicep for an Azure-focused stack

or Terraform if project standards justify it.

Manage:

- Container Apps environment
- API Container App
- Worker Container App
- Service Bus
- Storage Account
- Blob containers
- PostgreSQL if used
- Key Vault
- Application Insights
- identities
- RBAC
- networking where necessary
- Container Registry

Do not create enterprise networking complexity without a requirement.

Add deployment documentation.

---

## 43.6 Advanced Analytics Dashboard

Only after the operational assessment flow is stable, enhance analytics.

Potential additions:

- processing volume
- success/failure rate
- average confidence
- emotional-tone distribution
- noise distribution
- average latency
- cost per minute
- model-version comparison
- batch history
- trend analysis

Keep operational metrics separate from the required prediction output.

Do not clutter the basic evaluator workflow.

---

## 43.7 Complex Observability

Expand basic structured logging into production observability.

Use:

- OpenTelemetry
- Azure Application Insights
- Azure Monitor

Track:

- request IDs
- batch IDs
- file IDs
- queue message IDs
- model version
- inference latency
- RTF
- cost
- retries
- errors
- worker saturation
- queue depth

Never log confidential audio or raw sensitive transcripts by default.

Add dashboards and alerts only for actionable signals.

---

## 43.8 Advanced Role-Based Authentication

Add RBAC only when real production personas exist.

Potential roles:

```text
admin
operator
reviewer
read_only
```

Implement authorization at the API boundary.

Do not rely only on hiding buttons in React.

Consider Microsoft Entra ID when moving into future production Azure environment.

Keep the assessment evaluator-login path simple until this work begins.

---

## 43.9 Extensive Frontend Filtering

After real usage demonstrates the need, add filtering such as:

- filename search
- emotional tone
- emotional intensity
- noise presence
- noise severity
- audio quality
- overlap
- silence
- confidence range
- processing status
- batch
- date
- pipeline version

Use URL/query-state when useful for shareable views.

Do not load unnecessary client-side complexity for small result sets.

---

## 43.10 Fancy UI / Product Polish

Do this last.

Potential improvements:

- stronger information hierarchy
- richer progress state
- responsive tables
- result details drawer
- charts
- batch history
- better empty states
- refined skeletons
- better error recovery
- keyboard shortcuts
- polished visual system
- dark mode if product direction calls for it

Do not compromise accessibility.

Do not turn the application into a visual demo at the expense of inference reliability.

---

# 44. Future Azure Production Target

After the optional hardening work, the architecture may evolve toward:

```text
React
  |
  v
Azure Static Web Apps
  |
  v
Azure Container Apps - API
  |
  v
Azure Service Bus
  |
  v
Azure Container Apps - Worker
  |
  +--> Audio / ML Pipeline
  |
  +--> Azure Blob Storage
  |
  +--> PostgreSQL
  |
  +--> Application Insights

Managed Identity
  |
  +--> Key Vault
  +--> Blob Storage
  +--> Service Bus
```

This is a future production direction, not the minimum assessment architecture.

---


# 45. Progress Tracking File — Mandatory During Implementation

Antigravity must maintain a project progress file throughout the implementation.

Create:

```text
PROGRESS.md
```

at the repository root.

This file is part of the required development workflow.

Do not wait until the end of the project to create it.

Create it at the beginning of implementation and update it continuously.

---

## 45.1 Update `PROGRESS.md` After Every Meaningful Change

After every completed implementation step, Antigravity must update `PROGRESS.md`.

This includes:

- completed feature work
- completed backend endpoint
- completed frontend screen/component
- completed ML experiment
- completed model comparison
- completed test coverage
- bug fix
- refactor that changes architecture or behavior
- Azure infrastructure change
- CI/CD pipeline change
- TEST deployment
- PROD deployment
- documentation update
- security improvement
- performance improvement
- cost measurement
- latency benchmark
- failure discovered
- blocker discovered
- important implementation decision

Do not batch all progress updates until the end.

The progress file should reflect the current state of the repository at all times.

---

## 45.2 Required `PROGRESS.md` Structure

Use this structure:

```md
# Project Progress

## Current Status

Current phase:
Overall status:
Last updated:

## Completed

### YYYY-MM-DD HH:mm

- Completed:
- Files changed:
- Tests added/updated:
- Validation performed:
- Result:

## In Progress

- Current task:
- Relevant files:
- Expected outcome:

## Next

1. Next task
2. Following task
3. Following task

## Decisions

### Decision: <short title>

- Context:
- Decision:
- Reason:
- Tradeoff:

## Issues / Blockers

- Issue:
- Impact:
- Current workaround or next action:

## Test Status

- Frontend:
- Backend:
- Integration:
- E2E:
- ML/inference:
- Deployment smoke tests:

## Deployment Status

### TEST

- Version:
- Commit:
- Deployment status:
- URL:
- Smoke test:
- Notes:

### PROD

- Version:
- Commit:
- Deployment status:
- URL:
- Smoke test:
- Notes:

## Assessment Checklist

- [ ] hosted application
- [ ] login
- [ ] ZIP/batch upload
- [ ] CSV validation
- [ ] progress
- [ ] partial failure handling
- [ ] exact output schema
- [ ] confidence calculation
- [ ] CSV export
- [ ] JSON export
- [ ] two inference approaches compared
- [ ] cost measured
- [ ] latency measured
- [ ] tests passing
- [ ] TEST deployment
- [ ] PROD deployment
- [ ] README
- [ ] technical memo
```

---

## 45.3 Progress Entry Rules

Every progress entry must be factual.

Do not write vague entries such as:

```text
Made progress on backend.
Improved some tests.
Worked on UI.
```

Prefer:

```text
Implemented POST /api/batches with ZIP validation and per-file error isolation.

Files changed:
- backend/app/api/batches.py
- backend/app/application/batch_processor.py
- backend/tests/api/test_batches.py

Validation:
- 8 API tests passing
- malformed audio fixture correctly results in completed_with_errors
```

Entries should make it possible for another engineer to understand what changed without reading the entire Git diff.

---

## 45.4 Record Tests With Each Update

Whenever code is changed, record the tests that were run.

Example:

```md
### 2026-08-26 15:20

- Completed: Manifest validation for duplicate and unmatched filenames.
- Files changed:
  - `backend/app/application/manifest.py`
  - `backend/tests/application/test_manifest.py`
- Tests added:
  - duplicate manifest name
  - missing audio file
  - unmatched audio file
  - malformed result JSON
- Validation performed:
  - `pytest backend/tests/application/test_manifest.py`
- Result:
  - 12 passed
```

Do not claim a test passed unless it was actually executed.

---

## 45.5 Record ML Experiments

Every materially different inference experiment must be logged.

Use a concise table where useful.

Example:

```md
## ML Experiments

| Experiment | Approach | Accuracy / F1 | Latency | Cost/min | Notes |
|---|---|---:|---:|---:|---|
| A1 | Acoustic SER + deterministic audio features | ... | ... | ... | ... |
| B1 | Transcript semantic classifier | ... | ... | ... | ... |
```

For each experiment record:

- model/version
- preprocessing
- configuration
- input samples
- measured result
- latency
- cost assumption
- reason for keeping or rejecting the approach

Do not overwrite prior experiment results.

Preserve the history so decisions remain auditable.

---

## 45.6 Record Architecture Decisions

Important architectural choices must be added to the `Decisions` section.

Examples:

- Python/FastAPI instead of .NET
- React SPA instead of Next.js
- polling instead of WebSockets
- modular monolith instead of microservices
- CPU inference instead of GPU
- Azure Container Apps
- Blob Storage
- choosing or rejecting PostgreSQL
- queue introduction
- Service Bus adoption
- model selection
- confidence strategy

Each decision should include:

```text
Context
Decision
Reason
Tradeoff
```

Keep these concise.

---

## 45.7 Record Failures and Blockers

Do not hide failed attempts.

When something fails, log:

- what failed
- error or symptom
- likely cause
- impact
- resolution or next action

Example:

```md
## Issues / Blockers

### Azure Container startup failure

- Symptom: Container exits during startup.
- Cause: FFmpeg package missing from runtime image.
- Impact: TEST deployment unavailable.
- Resolution: Added FFmpeg installation to Dockerfile and redeployed.
- Status: Resolved.
```

This is useful engineering evidence and should not be removed simply because the issue was later fixed.

---

## 45.8 Keep `Next` Current

After every update, refresh the `Next` section.

It should contain the next 1–3 concrete actions.

Bad:

```text
Continue working.
Finish project.
```

Good:

```text
1. Implement Approach B transcript-based classifier.
2. Benchmark both approaches against supplied labeled calls.
3. Select final inference pipeline and document the decision.
```

Antigravity should use this section as the continuation point when resuming work.

---

## 45.9 Update Deployment Status Automatically

Whenever TEST or PROD is deployed, update the deployment section.

Record:

- environment
- Git commit SHA
- image/version
- deployment result
- hosted URL
- smoke-test result
- relevant notes

Example:

```md
### TEST

- Version: `sha-a8d31f2`
- Commit: `a8d31f2`
- Deployment status: Successful
- URL: `https://test.example.com`
- Smoke test: Passed
- Notes: Login, upload, processing, and results verified.
```

Do not put credentials or secrets in `PROGRESS.md`.

---

## 45.10 Update the Assessment Checklist Continuously

The assessment checklist must reflect actual completion status.

Only mark:

```text
[x]
```

when the requirement is genuinely implemented and verified.

Do not mark an item complete merely because code exists.

For example:

```text
[x] CSV export
```

requires that export was executed and validated.

---

## 45.11 Commit the Progress File

`PROGRESS.md` should normally be committed to the repository.

Do not add secrets, credentials, tokens, private keys, or sensitive customer data.

The file should be safe for reviewers to read.

It should provide a concise engineering history of the project.

---

## 45.12 Progress Update Before Stopping

Before Antigravity stops work for any reason, it must update `PROGRESS.md`.

This includes:

- reaching the end of an execution session
- encountering a blocker
- finishing a major phase
- hitting a tool or environment limitation
- completing the assessment
- moving into optional production-hardening work

The final update before stopping must clearly state:

```text
Current status
What was completed
What remains
What should happen next
Known blockers
Latest test status
Latest deployment status
```

This allows another session or engineer to continue immediately.

---

## 45.13 Progress Update After Resuming

When beginning a new work session:

1. read `PROGRESS.md`
2. inspect the current repository state
3. verify that the progress file still matches the code
4. continue from the `Next` section
5. update the file after completing the next meaningful task

Do not restart planning from scratch unless the repository state contradicts the progress file.

---

## 45.14 Progress File Definition of Done

- [ ] `PROGRESS.md` exists at repository root
- [ ] current phase/status is present
- [ ] completed work is logged
- [ ] changed files are recorded for meaningful changes
- [ ] test execution is recorded
- [ ] ML experiments are recorded
- [ ] important decisions are recorded
- [ ] blockers/failures are recorded
- [ ] next actions are current
- [ ] TEST deployment status is recorded
- [ ] PROD deployment status is recorded when available
- [ ] assessment checklist is current
- [ ] no secrets are stored in the file
- [ ] progress is updated before every work session ends


# 46. Final Engineering Principle

When choosing between:

```text
clever
```

and:

```text
simple, correct, measurable, tested, cheap, and deployable
```

choose the second option.

The assessment should demonstrate senior engineering judgment:

- select technology based on workload
- measure instead of guessing
- avoid premature complexity
- protect confidential data
- write tests
- understand cost
- ship a working product
- leave clear architectural seams for future scaling

Finish the required assessment first.

Then continue through the production-hardening backlog.
