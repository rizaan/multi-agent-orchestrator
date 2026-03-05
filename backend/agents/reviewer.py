"""
agents/reviewer.py — Reviewer Agent

RESPONSIBILITY: Evaluate the draft report. Either APPROVE it (done!) 
or REQUEST REVISION with specific feedback.

This creates the feedback loop — the most interesting part of the pipeline.
MAX_REVISIONS prevents infinite loops.
"""

from agents.base import BaseAgent
from models import AgentName, Task, TaskStatus, ReviewDecision

MAX_REVISIONS = 1  # After this many revisions, always approve


class ReviewerAgent(BaseAgent):
    name = AgentName.REVIEWER

    def _execute(self, task: Task) -> Task:
        # Safety valve: never loop forever
        if task.revision_count >= MAX_REVISIONS:
            return self._approve(task, reason="Max revisions reached — approving final draft.")

        # Evaluate draft quality
        decision, feedback = self._evaluate(task)

        if decision == ReviewDecision.APPROVED:
            return self._approve(task, reason=feedback)
        else:
            return self._request_revision(task, feedback=feedback)

    def _evaluate(self, task: Task) -> tuple[ReviewDecision, str]:
        """
        Simulate intelligent review. 
        In production: LLM evaluates against a rubric.
        Here: Rule-based checks on draft content.
        """
        draft = task.draft_report or ""
        word_count = len(draft.split())
        section_count = draft.count("##")

        issues = []

        if word_count < 200:
            issues.append("The report is too brief — needs more depth and detail.")

        if section_count < 3:
            issues.append("The report lacks sufficient structure. Add more sections.")

        if "conclusion" not in draft.lower():
            issues.append("Missing a conclusion section with actionable recommendations.")

        if task.revision_count == 0 and not issues:
            # First draft — always request at least one revision for realism
            issues.append(
                "The draft is good but needs stronger specificity. "
                "Please add concrete examples and make the conclusion more actionable "
                "with numbered next steps."
            )

        if issues:
            return ReviewDecision.REVISION, " ".join(issues)
        else:
            return ReviewDecision.APPROVED, "The report meets all quality criteria. Well structured, comprehensive, and actionable."

    def _approve(self, task: Task, reason: str) -> Task:
        task.review_decision = ReviewDecision.APPROVED
        task.review_feedback = reason
        task.final_report = task.draft_report
        task.status = TaskStatus.DONE
        task.current_agent = None
        return task

    def _request_revision(self, task: Task, feedback: str) -> Task:
        task.review_decision = ReviewDecision.REVISION
        task.review_feedback = feedback
        task.status = TaskStatus.REVISING
        return task

    def _input_summary(self, task: Task) -> str:
        word_count = len(task.draft_report.split()) if task.draft_report else 0
        return f"Reviewing draft ({word_count} words, revision #{task.revision_count})"

    def _output_summary(self, task: Task) -> str:
        if task.review_decision == ReviewDecision.APPROVED:
            return f"✅ APPROVED — {task.review_feedback}"
        else:
            return f"🔄 REVISION REQUESTED — {task.review_feedback}"
