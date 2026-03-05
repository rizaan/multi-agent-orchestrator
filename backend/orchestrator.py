"""
orchestrator.py — The Task Orchestrator

This is the "factory manager" — it doesn't do the work itself,
it coordinates WHO does WHAT and WHEN.

KEY DESIGN DECISIONS:
1. In-memory store (dict) — simple, fast, no DB setup needed
2. Async execution via asyncio — non-blocking, frontend can poll freely  
3. State machine pattern — each status maps to exactly one next action
4. The review feedback loop is handled naturally by the state machine
"""

import asyncio
from datetime import datetime
from typing import Optional

from models import Task, TaskStatus, CreateTaskRequest
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.reviewer import ReviewerAgent


# ── In-Memory Task Store ───────────────────────────────────────────────────────
# Maps task_id → Task. In production, replace with Redis or a database.
_task_store: dict[str, Task] = {}

# ── Agent Instances ────────────────────────────────────────────────────────────
# We instantiate once and reuse — agents are stateless (all state lives in Task)
_planner    = PlannerAgent()
_researcher = ResearcherAgent()
_writer     = WriterAgent()
_reviewer   = ReviewerAgent()


def create_task(request: CreateTaskRequest) -> Task:
    """Create a new Task and store it. Returns immediately (non-blocking)."""
    task = Task(user_request=request.request)
    _task_store[task.id] = task
    return task


def get_task(task_id: str) -> Optional[Task]:
    """Retrieve a task by ID."""
    return _task_store.get(task_id)


def get_all_tasks() -> list[Task]:
    """Return all tasks, newest first."""
    tasks = list(_task_store.values())
    return sorted(tasks, key=lambda t: t.created_at, reverse=True)


def compute_progress(task: Task) -> int:
    """
    Convert task status to a 0–100 progress percentage.
    Used by the frontend progress bar.
    """
    progress_map = {
        TaskStatus.PENDING:     0,
        TaskStatus.PLANNING:    15,
        TaskStatus.RESEARCHING: 35,
        TaskStatus.WRITING:     60,
        TaskStatus.REVIEWING:   75,
        TaskStatus.REVISING:    85,
        TaskStatus.DONE:        100,
        TaskStatus.FAILED:      0,
    }
    return progress_map.get(task.status, 0)


async def run_pipeline(task_id: str) -> None:
    """
    THE MAIN PIPELINE — runs asynchronously in the background.
    
    State Machine:
    PENDING → [Planner] → RESEARCHING → [Researcher] → WRITING 
    → [Writer] → REVIEWING → [Reviewer] → DONE
                                              ↓ (if revision requested)
                                           REVISING → [Writer] → REVIEWING → ...
    
    The loop naturally handles the review/revise cycle by checking
    task.status after each agent runs.
    """
    task = _task_store.get(task_id)
    if not task:
        return

    try:
        # ── Stage 1: Planning ─────────────────────────────────────────────────
        task.status = TaskStatus.PLANNING
        task.updated_at = datetime.utcnow()
        await asyncio.sleep(1.5)  # Simulate processing time for realistic UX
        task = _planner.run(task)
        task.updated_at = datetime.utcnow()

        # ── Stage 2: Research ─────────────────────────────────────────────────
        await asyncio.sleep(2.0)
        task = _researcher.run(task)
        task.updated_at = datetime.utcnow()

        # ── Stage 3: Write → Review → (Revise → Review)* loop ─────────────────
        # This loop runs at least once and repeats if reviewer requests revisions.
        max_cycles = 3  # Safety cap
        cycles = 0

        while cycles < max_cycles:
            cycles += 1

            # Writing phase
            task.status = TaskStatus.WRITING if task.revision_count == 0 else TaskStatus.REVISING
            task.updated_at = datetime.utcnow()
            await asyncio.sleep(2.0)
            task = _writer.run(task)
            task.updated_at = datetime.utcnow()

            # Review phase
            task.status = TaskStatus.REVIEWING
            task.updated_at = datetime.utcnow()
            await asyncio.sleep(1.5)
            task = _reviewer.run(task)
            task.updated_at = datetime.utcnow()

            # Check if we're done
            if task.status == TaskStatus.DONE:
                break

            # If revising, loop back (Writer will pick up the feedback)
            # task.status will be REVISING here, loop continues

        # Failsafe: if somehow we exit loop without DONE, mark done
        if task.status not in (TaskStatus.DONE, TaskStatus.FAILED):
            task.final_report = task.draft_report
            task.status = TaskStatus.DONE
            task.current_agent = None

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        task.current_agent = None
        task.updated_at = datetime.utcnow()

    finally:
        _task_store[task_id] = task
