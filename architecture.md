# Multi-Agent Task Orchestration System

## Introduction

I built a Multi-Agent Task Orchestration System using **FastAPI** and **Next.js**. The system accepts a research request from the user and passes it through four AI agents in a pipeline:

- **Planner** — breaks the request into sub-tasks
- **Researcher** — gathers information per sub-task
- **Writer** — synthesizes everything into a report
- **Reviewer** — either approves the report or sends it back to the Writer for revision

The key architectural decisions were: modeling the pipeline as a state machine, using an abstract base class so all agents share a single interface, running the pipeline asynchronously in the background so the API stays responsive, and using polling on the frontend to show live progress updates. The whole system is designed so swapping in a real LLM requires changing only one method per agent.

---

## System Architecture

The system has three layers:

### Backend (FastAPI + Python)

| File | Responsibility |
|---|---|
| `models.py` | Defines all data shapes using Pydantic — `Task`, `SubTask`, `AgentStep`, enums for status |
| `agents/base.py` | Abstract base class — every agent inherits from it and implements `_execute()` |
| `planner / researcher / writer / reviewer` | Each has a single responsibility |
| `orchestrator.py` | Coordinator — holds the in-memory task store, instantiates agents, runs the pipeline as an async state machine |
| `main.py` | Exposes REST endpoints and wires everything together |

### Frontend (Next.js + React)

| File | Responsibility |
|---|---|
| `page.tsx` | Top-level task state; switches between the landing view and active task view |
| `TaskForm.tsx` | Submits the request to the backend and creates a minimal task object immediately |
| `Pipeline.tsx` | Polls the backend every 1.5 seconds and updates the UI live — showing agent progress, sub-tasks, and timing |
| `ResultsPanel.tsx` | Shows the final report with three tabs: Report, Research, Agent Steps |

### Communication

- REST endpoints for task creation and data fetching
- Polling every 1.5 seconds for live updates *(chosen over SSE due to cross-origin reliability)*

---

## Design Decisions

### State Machine

A state machine is the natural fit because the pipeline has a fixed, well-defined lifecycle where each state maps to exactly one agent and one next action. This gives us:

1. **Predictability** — you always know what happens next given the current state
2. **Revision loop for free** — when the Reviewer sets status to `REVISING`, the `while` loop in `run_pipeline()` naturally sends execution back to the Writer without any special case logic
3. **Easy debugging** — if something goes wrong, the `status` field tells you exactly where in the pipeline it failed
4. **Auditability** — `TaskStatus` is an enum, so invalid states are impossible at the type level

The alternative — a hardcoded sequence of `if/else` — would be much harder to extend. Adding a `FactChecker` agent to the state machine just means adding a new status and a new agent call.

---

### Abstract Base Class

`BaseAgent` uses Python's ABC (Abstract Base Class) pattern:

```python
class BaseAgent(ABC):
    def run(self, task: Task) -> Task:          # Public — called by Orchestrator
        step = AgentStep(...)                   # Start timing
        task.steps.append(step)
        task = self._execute(task)              # Call subclass logic
        step.status = "done"
        step.duration_seconds = ...             # Record timing
        return task

    @abstractmethod
    def _execute(self, task: Task) -> Task:     # Subclasses MUST implement this
        ...
```

The key insight is the separation between `run()` and `_execute()`:

- `run()` handles cross-cutting concerns — timing, step logging, error handling — the same for every agent
- `_execute()` is the agent's unique logic — the only thing subclasses need to implement

This is the **Template Method pattern**. The Orchestrator only ever calls `agent.run(task)` — it never knows or cares which specific agent it's talking to. This means:

- Adding a new agent requires **zero changes** to the Orchestrator
- All agents automatically get timing and logging for free
- If an `_execute()` raises an exception, `run()` catches it, marks the step as failed, and re-raises for the Orchestrator to handle

---

### Memory Management

In-memory storage was a deliberate trade-off for this scope. The in-memory dict (`_task_store: dict[str, Task] = {}`) gives us:

- **Zero setup** — no database, no migrations, no connection pooling
- **Instant reads and writes** — O(1) lookups
- **Simple code** — `_task_store[task.id] = task`

The accepted trade-offs:

- Data loss on restart — all tasks disappear when the server restarts
- Single process only — can't run multiple server instances since each has its own dict
- No persistence — can't revisit past tasks after restart

The architecture is specifically designed to make this easy to replace. Only `orchestrator.py` touches `_task_store`. Swapping it for Redis would mean changing just four functions — `create_task`, `get_task`, `get_all_tasks`, and the store update in `run_pipeline`. Nothing else in the codebase would change.

---

### Why FastAPI?

Three reasons specific to this project:

1. **Native async support** — the pipeline uses `asyncio` and `await`. FastAPI is built on Starlette which supports async natively. Flask requires extensions for async and Django's async support is newer and more limited.
2. **BackgroundTasks** — FastAPI's built-in `BackgroundTasks` lets us kick off the pipeline after sending the response in two lines. In Flask you'd need Celery or threading.
3. **Pydantic integration** — FastAPI uses Pydantic models natively for request validation and response serialization. `CreateTaskRequest`, `TaskStatusResponse`, and `TaskResultResponse` serve double duty as both validation and auto-generated API docs.

The auto-generated Swagger UI at `/docs` was also genuinely useful for testing all endpoints during development without needing Postman.

---

### API Design

Designed around separating concerns between speed and completeness:

```
POST /tasks              → Creates task, returns immediately with just the ID
GET  /tasks/{id}/status  → Lightweight — only progress fields, fast to serialize
GET  /tasks/{id}         → Full task — all data including full report text
GET  /tasks              → List for task history
GET  /tasks/{id}/stream  → SSE for real-time (backup to polling)
```

The reason for a separate `/status` endpoint is **performance**. During active polling (every 1.5 seconds), we don't need to send the full report text — that could be thousands of words. The status endpoint returns only 6 fields. Once the task is `done`, the frontend makes one final call to `/tasks/{id}` to get everything including the report.

This pattern — **lightweight polling + one full fetch at the end** — is much more efficient than sending the complete task object on every poll.