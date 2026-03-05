"""
main.py — FastAPI Application Entry Point

ENDPOINTS:
  POST /tasks          → Submit a new task (starts pipeline in background)
  GET  /tasks          → List all tasks
  GET  /tasks/{id}     → Get full task details
  GET  /tasks/{id}/status → Lightweight status check (for polling)
  GET  /tasks/{id}/stream → SSE stream for real-time updates

CORS is enabled so the Next.js frontend (port 3000) can talk to this (port 8000).
"""

import asyncio
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import (
    CreateTaskRequest, TaskStatus,
    TaskStatusResponse, TaskResultResponse
)
import orchestrator

app = FastAPI(
    title="Multi-Agent Orchestration API",
    description="Orchestrates AI agents to research and write reports.",
    version="1.0.0"
)

# ── CORS ───────────────────────────────────────────────────────────────────────
# Allow the Next.js dev server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Multi-Agent Orchestration API", "status": "running"}


@app.post("/tasks", status_code=201)
async def create_task(
    request: CreateTaskRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a new task. 
    - Creates the task record immediately (fast response to user)
    - Kicks off the agent pipeline in the background (non-blocking)
    
    WHY BackgroundTasks?
    The pipeline takes 10-15 seconds. We can't make the user wait.
    FastAPI's BackgroundTasks runs the function after the response is sent.
    """
    task = orchestrator.create_task(request)

    # Schedule the pipeline to run without blocking the response
    background_tasks.add_task(orchestrator.run_pipeline, task.id)

    return {
        "id": task.id,
        "status": task.status,
        "message": "Task created. Pipeline starting.",
        "created_at": task.created_at.isoformat()
    }


@app.get("/tasks")
def list_tasks():
    """Return all tasks (for task history sidebar)."""
    tasks = orchestrator.get_all_tasks()
    return [
        {
            "id": t.id,
            "user_request": t.user_request[:100],
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "progress_percent": orchestrator.compute_progress(t)
        }
        for t in tasks
    ]


@app.get("/tasks/{task_id}", response_model=TaskResultResponse)
def get_task(task_id: str):
    """Return full task data including all agent steps and reports."""
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """
    Lightweight status endpoint — only returns progress fields.
    Frontend polls this every 2 seconds to update the UI.
    """
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return TaskStatusResponse(
        id=task.id,
        status=task.status,
        current_agent=task.current_agent,
        revision_count=task.revision_count,
        steps=task.steps,
        error=task.error,
        progress_percent=orchestrator.compute_progress(task)
    )


@app.get("/tasks/{task_id}/stream")
async def stream_task(task_id: str):
    """
    Server-Sent Events (SSE) endpoint for real-time updates.
    
    WHY SSE over WebSockets?
    - SSE is simpler: one-way (server → client), native browser support
    - WebSockets: bidirectional, more complex, better for chat apps
    - For progress updates, SSE is the right tool
    
    The frontend connects once, and we push updates until DONE/FAILED.
    """
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    async def event_generator():
        last_status = None
        last_step_count = 0
        timeout = 120  # Max seconds to stream
        elapsed = 0

        while elapsed < timeout:
            task = orchestrator.get_task(task_id)
            if not task:
                break

            current_step_count = len(task.steps)
            status_changed = task.status != last_status
            new_steps = current_step_count > last_step_count

            if status_changed or new_steps:
                last_status = task.status
                last_step_count = current_step_count

                payload = {
                    "id": task.id,
                    "status": task.status.value,
                    "current_agent": task.current_agent.value if task.current_agent else None,
                    "progress_percent": orchestrator.compute_progress(task),
                    "revision_count": task.revision_count,
                    "step_count": current_step_count,
                    "updated_at": task.updated_at.isoformat(),
                }

                # SSE format: "data: <json>\n\n"
                yield f"data: {json.dumps(payload)}\n\n"

            # Stop streaming when terminal state reached
            if task.status in (TaskStatus.DONE, TaskStatus.FAILED):
                yield f"data: {json.dumps({'event': 'complete', 'status': task.status.value})}\n\n"
                break

            await asyncio.sleep(0.5)
            elapsed += 0.5

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Important for Nginx proxying
        }
    )
