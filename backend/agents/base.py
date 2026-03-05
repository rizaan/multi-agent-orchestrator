"""
agents/base.py — Abstract Base Agent

WHY AN ABSTRACT BASE CLASS?
Think of this as a "contract". Every agent MUST implement run().
This lets the Orchestrator treat all agents the same way — it doesn't
care if it's talking to the Planner or Reviewer, it just calls .run().

This pattern is called the "Strategy Pattern" in software design.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from models import AgentStep, AgentName, Task


class BaseAgent(ABC):
    """
    Every agent inherits from this class.
    
    The Orchestrator only ever calls: agent.run(task)
    Each agent reads what it needs from `task` and writes its output back.
    """

    name: AgentName  # Must be set by each subclass

    def run(self, task: Task) -> Task:
        """
        Public method called by the Orchestrator.
        Wraps _execute() with timing, step logging, and error handling.
        """
        step = AgentStep(
            agent=self.name,
            status="running",
            input_summary=self._input_summary(task),
            started_at=datetime.utcnow()
        )
        task.steps.append(step)
        task.current_agent = self.name

        try:
            task = self._execute(task)
            # Mark the step as done
            step.status = "done"
            step.finished_at = datetime.utcnow()
            step.duration_seconds = (
                step.finished_at - step.started_at
            ).total_seconds()
            step.output = self._output_summary(task)

        except Exception as e:
            step.status = "failed"
            step.finished_at = datetime.utcnow()
            step.output = f"Error: {str(e)}"
            raise  # Re-raise so Orchestrator can handle it

        return task

    @abstractmethod
    def _execute(self, task: Task) -> Task:
        """
        Core logic — each agent implements this.
        Receives the full task, mutates it, returns it.
        """
        ...

    def _input_summary(self, task: Task) -> str:
        """Override in subclass to give a meaningful input description."""
        return f"Processing task: {task.user_request[:80]}"

    def _output_summary(self, task: Task) -> str:
        """Override in subclass to summarize what was produced."""
        return "Completed"
