# AURA

**Adaptive Unified Routing Architecture for Cost-Efficient and Reliable Multi-LLM Systems**

AURA is a local multi-LLM routing platform that selects an appropriate model for each request instead of sending every prompt to the largest available model.

The system combines query analysis, privacy-aware routing, confidence-based escalation, adaptive learning, and normalized compute analytics.

This project was developed for a hackathon problem statement focused on **cost optimisation using LLM routing**.

## Core Idea

AURA routes requests across three local Ollama model tiers:

| Tier | Model | Normalized Compute Score |
| --- | --- | ---: |
| LOW | `qwen3:1.7b` | 1 |
| MEDIUM | `qwen3:4b` | 2 |
| HIGH | `qwen3:8b` | 4 |

All primary models run locally through Ollama.

**Actual external API spend: ?0**

AURA reports normalized compute/resource metrics rather than fabricated monetary API costs.

## Key Features

- multi-model registry
- deterministic query analysis
- complexity scoring
- task-type classification
- intelligent model-tier routing
- explainable routing decisions
- manual routing overrides
- confidence evaluation
- automatic confidence-based escalation
- deterministic arithmetic verification for safely evaluable prompts
- multi-task decomposition
- independent subtask routing
- privacy and sensitive-data detection
- local-execution enforcement
- latency analytics
- token analytics
- normalized compute analytics
- persistent learning history
- adaptive routing recommendations
- React dashboard
- benchmark framework
- deterministic benchmark evaluation
- adaptive-vs-Always-HIGH comparison

## Routing Architecture

```text
User Prompt
    |
    v
Query Analysis
    |
    +--> Task Type
    +--> Complexity
    +--> Reasoning Requirement
    |
    v
Privacy Assessment
    |
    v
Adaptive Routing Policy
    |
    v
Initial Model Tier
    |
    +--> LOW    qwen3:1.7b
    +--> MEDIUM qwen3:4b
    +--> HIGH   qwen3:8b
    |
    v
Local Ollama Inference
    |
    v
Confidence Evaluation
    |
    +--> Accept response
    |
    +--> Escalate when confidence is insufficient
            |
            v
        Stronger Model Tier
    |
    v
Analytics + Learning History
    |
    v
API Response / Dashboard
```

## Technology Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic
- httpx
- pytest
- Ollama
- Qwen3 local models

### Frontend

- React
- TypeScript
- Vite
- Vitest
- oxlint

## Requirements

- Python 3.12+
- Node.js
- npm
- Git
- Ollama

Required local models:

- qwen3:1.7b
- qwen3:4b
- qwen3:8b

## Backend Setup

```powershell
Set-Location "D:\Sona_Hack\AURA-LLM-Router\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

```powershell
Set-Location "D:\Sona_Hack\AURA-LLM-Router\frontend"
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

The frontend uses http://127.0.0.1:8000 as the default backend API.

The backend URL can be overridden using VITE_API_BASE_URL.

The dashboard navigation contains Overview, Route Prompt, and Multi-Task.
Route metrics remain embedded in the Route Prompt results, while adaptive
learning and query analysis operate internally as routing capabilities.

## Main API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | API metadata and status |
| GET | `/health` | Backend health check |
| GET | `/models` | Available model registry |
| POST | `/analysis` | Analyze prompt complexity and task type |
| POST | `/route` | Route and execute a single prompt |
| POST | `/multi-route` | Decompose and execute multi-task prompts |
| GET | `/learning/history` | View adaptive learning history |
| GET | `/learning/history/{task_type}` | View task-specific history |
| GET | `/learning/recommendation/{task_type}` | View adaptive tier recommendation |

## Confidence-Based Escalation

AURA evaluates each generated response before returning it.

The confidence layer checks deterministic quality signals such as:

- empty responses
- failure language
- uncertainty language
- reasoning leakage
- insufficient detail for complex tasks
- deterministic arithmetic correctness for safely evaluable arithmetic prompts

If confidence falls below the acceptance threshold, AURA can escalate:

```text
LOW -> MEDIUM -> HIGH
```

A live Phase 13 validation confirmed this recovery path:

```text
Prompt: 2+2
LOW qwen3:1.7b -> incorrect answer detected
Confidence -> 0.0
Automatic escalation -> MEDIUM
MEDIUM qwen3:4b -> 4
Final confidence -> 1.0
```

## Phase 12 Benchmark

The saved Phase 12 benchmark contains 18 deterministic evaluation cases covering nine task types.

### Adaptive AURA

- Pass rate: 88.89%
- Passed: 16 / 18
- Mean quality score: 0.8889
- Total latency: 170.79 seconds
- Total tokens: 6221
- Total normalized compute cost: 556.217
- Tier usage: LOW 6, MEDIUM 6, HIGH 6

### Always-HIGH Baseline

- Pass rate: 100%
- Passed: 18 / 18
- Mean quality score: 1.0
- Total latency: 90.64 seconds
- Total tokens: 4078
- Total normalized compute cost: 362.56
- Tier usage: HIGH 18

### Benchmark Interpretation

This single saved 18-case local benchmark does not support a claim that adaptive routing reduced aggregate compute or latency.

In this run, smaller models sometimes generated longer responses, which offset their lower per-second compute scores.

The benchmark still demonstrates that AURA can match HIGH-tier quality with lower compute on selected cases, while also exposing where routing and output control require further optimization.

The two Adaptive AURA quality failures were low-tier classification cases.

Saved benchmark artifacts:

- `backend/benchmark_results/adaptive.json`
- `backend/benchmark_results/always_high.json`
- `backend/benchmark_results/comparison.json`
- `backend/benchmark_results/phase12_benchmark_report.md`

## Demo Flow

For a live demo:

1. Start Ollama and confirm the required models are installed.
2. Start the FastAPI backend on port 8000.
3. Start the Vite frontend on port 5173.
4. Open the AURA dashboard.
5. Submit prompts with different complexity levels.
6. Observe selected tier, model, explanation, privacy result, confidence, and analytics.
7. Demonstrate arithmetic verification with `2+2`; if LOW returns an incorrect answer, AURA automatically escalates.
8. Demonstrate Multi-Task decomposition and per-task routing analytics.

### Suggested Demo Examples

- Simple extraction or transformation -> LOW
- Explanation or moderate task -> MEDIUM
- Complex reasoning/planning task -> HIGH
- `2+2` -> demonstrates confidence verification and escalation when LOW is incorrect
- Sensitive-data prompt -> demonstrates privacy-aware local routing
- Multi-requirement prompt -> demonstrates decomposition and independent subtask routing

## Project Status

Completed capabilities include:

- backend and Ollama foundation
- multi-model registry
- query analysis and complexity scoring
- intelligent routing
- explainable routing
- confidence evaluation and escalation
- multi-task decomposition
- privacy-aware routing
- compute/token/latency analytics
- adaptive learning
- React dashboard
- deterministic benchmarking
- final integration hardening

AURA is currently configured as a local development and demonstration system using Ollama-hosted models.

## Testing

Backend tests:

```powershell
Set-Location "D:\Sona_Hack\AURA-LLM-Router\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

Frontend tests:

```powershell
Set-Location "D:\Sona_Hack\AURA-LLM-Router\frontend"
npm test
npm run lint
npm run build
```

## Demo Helper Scripts

Reusable PowerShell scripts are available in the `scripts` directory.

### Start Backend

```powershell
.\scripts\start-backend.ps1
```

### Start Frontend

Open another PowerShell terminal and run:

```powershell
.\scripts\start-frontend.ps1
```

### Verify the Full Demo Stack

With Ollama, the backend, and the frontend running:

```powershell
.\scripts\verify-demo.ps1
```

The verification script checks:

- Ollama availability
- required LOW, MEDIUM, and HIGH models
- backend health
- API version 1.0.0
- frontend availability
- a real routed inference request
- response confidence and analytics
- preservation of persistent learning history

The verification request uses real local model inference and restores `backend/data/learning_history.json` afterward so the demo check does not alter persistent adaptive-learning state.
