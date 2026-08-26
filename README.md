# CallScope AI — Voice Tone & Background Noise Analysis Platform

Production-ready hosted submission for the Software Engineer Assessment.

CallScope analyzes real production call audio to classify customer emotional tone, emotional intensity, background noise (presence, type, severity), technical audio quality, speaker overlap, long dead-air silences, and confidence scores.

---

## 1. Project Overview

CallScope is built as a high-performance **modular monolith** optimized for speed, reliability, strict cost efficiency (<= $0.003 / audio minute), and seamless deployment to Azure.

- **Evaluator Access**: Hosted web dashboard with simple secure authentication.
- **Batch Evaluation Workflow**: Upload ZIP archives, folders, or direct call audio files (`.ogg`, `.wav`, `.mp3`) with an optional `labels.csv` ground truth manifest.
- **Real-Time Progress & Error Isolation**: Progress updates via polling. One corrupted clip does not fail the batch.
- **Export Formats**: Download predictions as CSV or JSON preserving exact filename mapping.

---

## 2. System Architecture

```text
React 18 + Vite SPA (Azure Static Web Apps)
       |
       v (HTTP / REST API)
FastAPI Backend (Azure Container Apps)
       |
       +--> Audio Preprocessing & Signal Analysis (librosa / soundfile)
       +--> RMS Energy & Pitch-Based Voice Activity Analysis
       +--> Approach A (Acoustic SER Engine) & Approach B (Wav2Vec2 SER)
       +--> Batch Processor & In-Memory Store
       +--> Model Metrics & Evaluation Engine
```

---

## 3. Technology Choices

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Lucide Icons, Vitest.
- **Backend**: Python 3.12, FastAPI, Pydantic v2, PyTorch, torchaudio, librosa, soundfile, pytest, Uvicorn.
- **Containerization & Hosting**: Docker multi-stage builds, Azure Container Apps Consumption Tier.

---

## 4. Repository Structure

```text
/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (auth, batches, health)
│   │   ├── application/  # Batch orchestration & audio processing
│   │   ├── domain/       # Pydantic schemas & enums
│   │   ├── inference/    # Approach A & Approach B pipelines
│   │   ├── audio/        # Audio processor & feature extraction
│   │   ├── evaluation/   # ModelEvaluator (Accuracy, Macro F1)
│   │   ├── storage/      # BatchStore state manager
│   │   └── security/     # Password hashing & JWT auth tokens
│   ├── tests/            # pytest unit & API integration tests
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/          # Core layout
│   │   ├── features/     # Auth, Upload, Batches, Results, Evaluation
│   │   ├── components/   # Navbar & UI components
│   │   ├── api/          # API client wrapper
│   │   └── types/        # TypeScript interfaces
│   ├── postcss.config.js # Tailwind CSS compilation config
│   └── Dockerfile
├── .github/workflows/    # PR, TEST, and PROD GitHub Actions
├── docker-compose.yml
├── .env.example
├── PROGRESS.md
├── TECHNICAL_MEMO.md
└── README.md
```

---

## 5. Prerequisites

- **Python**: `3.12+`
- **Node.js**: `20+` (npm `10+`)
- **FFmpeg**: Required for audio file decoding
- **Docker & Docker Compose**: Optional for containerized execution

---

## 6. Local Setup & Quickstart

### Option 1: One-Command Docker Compose

1. Clone the repository and enter directory:
   ```bash
   git clone <repository>
   cd call-scope
   ```

2. Create environment file:
   - **macOS / Linux**: `cp .env.example .env`
   - **Windows (CMD)**: `copy .env.example .env`
   - **Windows (PowerShell)**: `Copy-Item .env.example .env`

3. Start application:
   ```bash
   docker compose up --build
   ```

Access dashboard at `http://localhost:3000` (Backend API at `http://localhost:8000`).

---

### Option 2: Running Backend & Frontend Separately

#### 1. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:
- **macOS / Linux (Bash/Zsh)**: `source .venv/bin/activate`
- **Windows (Command Prompt)**: `.venv\Scripts\activate.bat`
- **Windows (PowerShell)**: `.venv\Scripts\Activate.ps1`

Install dependencies and start the backend server:
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
*(Backend API will run at `http://localhost:8000`).*

---

#### 2. Frontend Setup

Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*(Frontend application will run at `http://localhost:3000`).*

---

## 7. Evaluator Authentication & Access

Access to the local or hosted dashboard is secured using JWT authentication.

- Credentials are dynamically configured via environment variables (`EVALUATOR_USERNAME` and `EVALUATOR_PASSWORD` in `.env`).
- For local evaluation and testing, the web dashboard includes a one-click **"Auto-fill Evaluator Credentials"** button.

---

## 8. Local Environment Variables (`.env.example`)

```env
APP_ENV=local
LOG_LEVEL=INFO
API_PORT=8000
FRONTEND_ORIGIN=http://localhost:3000
JWT_SECRET_KEY=your_random_32byte_secret_key_here
EVALUATOR_USERNAME=evaluator@callscope.ai
EVALUATOR_PASSWORD=your_secure_password_here
DEFAULT_APPROACH=approach_a
CPU_CONTAINER_APP_COST_PER_SEC=0.000036
AUDIO_RETENTION_DAYS=7
```

---

## 9. Running Tests Locally

All test commands use cross-platform standard Python & Node.js invocations:

### Backend Tests (`pytest`)

From the `backend` directory (with virtual environment activated):
```bash
cd backend
python -m pytest
```

Or from the root directory:
```bash
python -m pytest backend/tests
```

### Assessment Benchmark Run

From the root directory:
```bash
python scratch/run_benchmark.py --approach approach_a
python scratch/run_benchmark.py --approach approach_b
```

### Frontend Tests (`vitest`)

From the `frontend` directory:
```bash
cd frontend
npm test
```

---

## 10. API Surface

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Liveness and health check |
| `/api/ready` | GET | Dependency readiness check |
| `/api/auth/login` | POST | Authenticate evaluator and obtain access token |
| `/api/batches` | POST | Upload batch (ZIP archive or direct audio file) |
| `/api/batches` | GET | List batch history |
| `/api/batches/{id}` | GET | Get real-time progress status and file results |
| `/api/batches/{id}/results.csv` | GET | Export predictions as CSV |
| `/api/batches/{id}/results.json` | GET | Export predictions as JSON |
| `/api/batches/{id}/evaluation` | GET | Compute accuracy, Macro F1, and confusion matrix |

---

## 11. Local Troubleshooting

1. **FFmpeg missing error**: Ensure FFmpeg is installed on your operating system:
   - **macOS**: `brew install ffmpeg`
   - **Linux (Ubuntu/Debian)**: `sudo apt install ffmpeg`
   - **Windows**: `winget install ffmpeg` or `choco install ffmpeg`
2. **CORS issues**: Verify `FRONTEND_ORIGIN` in `.env` matches your browser URL (`http://localhost:3000`).
3. **Module Resolution**: Use `python -m <module>` or activate the virtual environment so `sys.path` resolves cross-platform without shell-specific environment variable syntax.

---

## 12. TEST & PROD Deployment Instructions

### TEST Deployment

Pushing to `develop` triggers `.github/workflows/deploy-test.yml`:
1. Runs frontend lint, vitest, build checks.
2. Runs backend pytest & ML contract benchmarks.
3. Builds Docker image tagged with commit SHA (`sha-a8d31f2`).
4. Deploys to Azure Container Apps (`callscope-api-test`).
5. Calls `/api/health` smoke test.

### PROD Promotion

Merging to `main` triggers `.github/workflows/deploy-prod.yml`:
1. Requires manual approval in GitHub `production` environment.
2. Promotes the exact immutable container image tested in TEST.
3. Deploys to Azure Container Apps (`callscope-api-prod`).
4. Runs production smoke test.

---

## 13. Cost & Latency Summary

- **Measured RTF**: `0.0353` (Processes 1 minute of audio in ~2.1 seconds on 1 vCPU).
- **Inference Cost**: **$0.000076 / audio minute** (39x under the $0.003 cost ceiling).
- **Data Privacy**: Audio is processed entirely in memory; zero egress to external APIs.