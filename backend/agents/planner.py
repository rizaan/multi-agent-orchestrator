"""
agents/planner.py — Planner Agent

RESPONSIBILITY: Break the user's request into discrete sub-tasks.

REAL WORLD: This would call an LLM with a prompt like:
  "Given this request, list 3-5 concrete research sub-tasks as JSON."
  
HERE: We use keyword matching to simulate intelligent planning.
The architecture is identical — swap _execute() body for a real LLM call.
"""

import re
from agents.base import BaseAgent
from models import AgentName, Task, SubTask, TaskStatus


# Pre-defined sub-task templates keyed by topic keywords.
# In production, an LLM generates these dynamically.
TOPIC_PLANS = {
    "microservices": [
        SubTask(title="Microservices Architecture Overview",
                description="Research what microservices are, core principles, and how they differ from monoliths."),
        SubTask(title="Advantages of Microservices",
                description="Research scalability, independent deployment, tech diversity, fault isolation benefits."),
        SubTask(title="Disadvantages of Microservices",
                description="Research operational complexity, network latency, distributed systems challenges."),
        SubTask(title="Monolithic Architecture Overview",
                description="Research monolith structure, when it works well, and its inherent simplicity."),
        SubTask(title="Decision Framework: When to Choose Which",
                description="Research guidelines for choosing microservices vs monolith based on team size, scale, and maturity."),
    ],
    "ai": [
        SubTask(title="Current State of AI",
                description="Research latest developments in artificial intelligence and machine learning."),
        SubTask(title="AI Applications and Use Cases",
                description="Research real-world applications across industries."),
        SubTask(title="Risks and Ethical Concerns",
                description="Research bias, safety, job displacement, and governance challenges."),
        SubTask(title="Future Outlook",
                description="Research predictions and emerging trends in AI development."),
    ],
    "cloud": [
        SubTask(title="Cloud Computing Fundamentals",
                description="Research IaaS, PaaS, SaaS models and major providers."),
        SubTask(title="Benefits of Cloud Adoption",
                description="Research cost savings, scalability, and reliability advantages."),
        SubTask(title="Cloud Migration Challenges",
                description="Research security, vendor lock-in, and migration complexity."),
        SubTask(title="Multi-Cloud vs Single Cloud Strategy",
                description="Research trade-offs of using multiple cloud providers."),
    ],
}

DEFAULT_PLAN = [
    SubTask(title="Background and Context",
            description="Research the background and foundational context of the topic."),
    SubTask(title="Key Benefits and Advantages",
            description="Research the primary advantages and positive aspects."),
    SubTask(title="Challenges and Limitations",
            description="Research drawbacks, risks, and known limitations."),
    SubTask(title="Best Practices and Recommendations",
            description="Research expert recommendations and proven best practices."),
]


class PlannerAgent(BaseAgent):
    name = AgentName.PLANNER

    def _execute(self, task: Task) -> Task:
        request_lower = task.user_request.lower()

        # Find which template best matches the user's request
        chosen_plan = DEFAULT_PLAN
        for keyword, plan in TOPIC_PLANS.items():
            if keyword in request_lower:
                chosen_plan = plan
                break

        # Deep copy so each task gets fresh SubTask instances
        import copy
        task.sub_tasks = copy.deepcopy(chosen_plan)
        task.status = TaskStatus.RESEARCHING
        return task

    def _input_summary(self, task: Task) -> str:
        return f"User request: \"{task.user_request}\""

    def _output_summary(self, task: Task) -> str:
        titles = [st.title for st in task.sub_tasks]
        return f"Created {len(task.sub_tasks)} sub-tasks: {', '.join(titles)}"
