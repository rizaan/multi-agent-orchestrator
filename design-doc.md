# Design Document — Multi-Agent Task Orchestration System

## 1. Architectural Decisions

### Agent Abstraction (Base Class Pattern)
All agents inherit from `BaseAgent`, which provides a unified `run(task)` interface. The orchestrator never knows which specific agent it's calling — it just calls `.run()`. This "Strategy Pattern" means adding a new agent (e.g., FactChecker) requires zero changes to the orchestrator — just create a subclass and plug it into the pipeline.

Each agent receives the full `Task` object, reads what it needs, mutates it, and returns it. This shared-state model is simple and avoids complex message-passing infrastructure.

### Orchestrator as State Machine
The task lifecycle is modeled as a state machine:

```
PENDING → PLANNING → RESEARCHING → WRITING → REVIEWING → DONE
                                                  ↓
                                              REVISING → REVIEWING → ...
```

Each state maps to exactly one agent. The orchestrator's `run_pipeline()` loop naturally handles the review/revise cycle by re-entering the Writer→Reviewer loop when `task.status == REVISING`. A `MAX_REVISIONS` cap prevents infinite loops.

### In-Memory State Store
Tasks are stored in a Python dict (`_task_store`). This was chosen over a database for simplicity within the time budget. The architecture fully supports swapping this for Redis or PostgreSQL — only `orchestrator.py` would change.

### Async Background Execution
When a task is submitted via `POST /tasks`, FastAPI's `BackgroundTasks` immediately returns a response while the pipeline runs asynchronously. This keeps the API responsive and lets the frontend start polling/streaming immediately.

---

## 2. Trade-offs Considered

### Polling vs. SSE vs. WebSockets
| Approach | Pros | Cons |
|---|---|---|
| **Polling** | Dead simple, works everywhere | Wasteful requests, 2s latency |
| **SSE** ✅ chosen | Real-time, one-way, native browser support, simple | Server must hold connections open |
| **WebSockets** | Bidirectional, lowest latency | Complex setup, overkill for status updates |

SSE is the right fit: updates flow server → client only, it's natively supported in browsers, and it's far simpler than WebSockets. Polling is implemented as an SSE fallback.

### Synchronous vs. Async Agents
Agents are synchronous internally (`_execute` is a regular function) but are called within an `async` pipeline using `await asyncio.sleep()` to simulate processing time. In production, real LLM calls would be `async` with `await`. This keeps the code readable without losing the async benefits at the API layer.

### Shared Task Object vs. Message Passing
Agents share a single `Task` object rather than passing messages between them. This is simpler but means agents are not independently deployable. For a production system, each agent would be a separate microservice communicating via a message queue (e.g., RabbitMQ, Kafka).

---

## 3. What I Would Add With More Time

1. **Real LLM Integration** — Replace hardcoded responses with Claude/GPT-4 API calls. The architecture is already set up for this: swap the body of each `_execute()` method.

2. **Persistent Storage** — Replace the in-memory dict with PostgreSQL + SQLAlchemy to survive server restarts.

3. **Parallel Research** — The Researcher Agent currently processes sub-tasks sequentially. With `asyncio.gather()`, they could run concurrently, cutting research time by ~4x.

4. **Testing** — Unit tests for the orchestrator state machine, agent outputs, and API endpoints using `pytest` and FastAPI's `TestClient`.

5. **Agent Configuration** — Let users toggle agents on/off, add a FactChecker, or adjust the max revisions via the UI.

6. **Error Retry Logic** — Implement exponential backoff for failed agent runs rather than immediately marking the task as FAILED.

7. **Authentication** — Per-user task isolation using JWT tokens.

---

## 4. Assumptions Made

- **No real LLM needed**: The assignment explicitly permits hardcoded/templated responses. The orchestration architecture is identical regardless.
- **Single server instance**: The in-memory store works on one process. Multi-instance deployment would require shared state (Redis).
- **One revision max**: Set `MAX_REVISIONS = 1` to demonstrate the feedback loop without infinite cycling in demos.
- **Simulated latency**: `asyncio.sleep()` calls simulate realistic processing times so the frontend progress UI is meaningful.
