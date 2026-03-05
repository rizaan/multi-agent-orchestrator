# Multi-Agent Task Orchestration System

A lightweight platform where multiple AI agents collaborate to research a topic and produce a written report. Built with FastAPI (Python) + Next.js (React).

## Architecture

```
User Request → Planner → Researcher → Writer → Reviewer → Final Report
                                                    ↓ (if revision needed)
                                                 Writer → Reviewer → Done
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+

---

### 1. Backend Setup (Terminal 1)

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

---

### 2. Frontend Setup (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tasks` | Submit a new research task |
| GET | `/tasks` | List all tasks |
| GET | `/tasks/{id}` | Get full task data |
| GET | `/tasks/{id}/status` | Lightweight status check |
| GET | `/tasks/{id}/stream` | SSE stream for real-time updates |

## Project Structure

```
backend/
├── main.py           # FastAPI app, API endpoints
├── orchestrator.py   # Pipeline coordinator
├── models.py         # Pydantic data models
├── agents/
│   ├── base.py       # Abstract base agent
│   ├── planner.py    # Breaks task into sub-tasks
│   ├── researcher.py # Gathers research per sub-task
│   ├── writer.py     # Synthesizes research into report
│   └── reviewer.py   # Reviews and approves/requests revision

frontend/src/
├── app/page.tsx               # Main page
├── components/TaskForm.tsx    # Request submission form
├── components/Pipeline.tsx    # Agent pipeline visualization + SSE
└── components/ResultsPanel.tsx # Report display with tabs
```
