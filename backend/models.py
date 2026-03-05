"""
models.py — Data Models for the Multi-Agent Orchestration System
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
import uuid


class AgentName(str, Enum):
    PLANNER    = "planner"
    RESEARCHER = "researcher"
    WRITER     = "writer"
    REVIEWER   = "reviewer"


class TaskStatus(str, Enum):
    PENDING     = "pending"
    PLANNING    = "planning"
    RESEARCHING = "researching"
    WRITING     = "writing"
    REVIEWING   = "reviewing"
    REVISING    = "revising"
    DONE        = "done"
    FAILED      = "failed"


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REVISION = "revision"


class AgentStep(BaseModel):
    agent: AgentName
    status: str = "running"
    input_summary: str = ""
    output: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class SubTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str
    research_result: Optional[str] = None
    status: str = "pending"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_request: str
    status: TaskStatus = TaskStatus.PENDING
    current_agent: Optional[AgentName] = None
    sub_tasks: list[SubTask] = []
    research_data: dict[str, str] = {}
    draft_report: Optional[str] = None
    final_report: Optional[str] = None
    review_decision: Optional[ReviewDecision] = None
    review_feedback: Optional[str] = None
    revision_count: int = 0
    steps: list[AgentStep] = []
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateTaskRequest(BaseModel):
    request: str = Field(..., min_length=10, max_length=500)


class TaskStatusResponse(BaseModel):
    id: str
    status: TaskStatus
    current_agent: Optional[AgentName]
    revision_count: int
    steps: list[AgentStep]
    error: Optional[str]
    progress_percent: int


class TaskResultResponse(BaseModel):
    id: str
    status: TaskStatus
    user_request: str
    sub_tasks: list[SubTask]
    draft_report: Optional[str]
    final_report: Optional[str]
    review_decision: Optional[ReviewDecision]
    review_feedback: Optional[str]
    revision_count: int
    steps: list[AgentStep]
    created_at: datetime
    updated_at: datetime
