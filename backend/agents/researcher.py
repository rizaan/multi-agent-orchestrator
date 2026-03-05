"""
agents/researcher.py — Researcher Agent

RESPONSIBILITY: For each sub-task, gather relevant information.

REAL WORLD: Would call web search APIs, RAG pipelines, or LLMs.
HERE: Returns detailed templated research content per topic.
"""

from agents.base import BaseAgent
from models import AgentName, Task, TaskStatus


# Simulated research database — maps topic keywords to rich content
RESEARCH_DB = {
    "microservices architecture overview": """
**Microservices Architecture** is an approach where an application is structured as a 
collection of small, independently deployable services. Each service:
- Runs in its own process
- Communicates via well-defined APIs (REST, gRPC, message queues)
- Is owned by a small team and can be deployed independently
- Is organized around business capabilities

Contrast with a **Monolith**: a single deployable unit where all functionality 
is tightly coupled. Monoliths are simpler to develop initially but grow harder 
to scale and maintain over time.

Key pioneers: Netflix, Amazon, and Uber all migrated from monoliths to 
microservices to handle massive scale.
""",
    "advantages of microservices": """
**Core Advantages of Microservices:**

1. **Independent Scalability** — Scale only the services under load (e.g., scale 
   payment service during sales events without scaling everything).

2. **Technology Diversity** — Each service can use the best tool for its job 
   (Python for ML, Go for high-throughput APIs, Node for real-time features).

3. **Fault Isolation** — A crash in the recommendation service doesn't take 
   down checkout. Failures stay contained.

4. **Independent Deployment** — Teams deploy their services without coordinating 
   with every other team. Enables true CI/CD.

5. **Team Autonomy** — Small teams own their services end-to-end, reducing 
   cross-team bottlenecks (Conway's Law in action).

6. **Easier to Understand** — Each service is small enough to fit in one 
   developer's head, reducing cognitive load.
""",
    "disadvantages of microservices": """
**Core Disadvantages of Microservices:**

1. **Operational Complexity** — You now run 50 services instead of 1. Need 
   Kubernetes, service mesh, distributed tracing, centralized logging.

2. **Network Latency** — What was a function call is now an HTTP request. 
   Adds latency and introduces potential points of failure.

3. **Distributed Systems Challenges** — Data consistency is hard. Transactions 
   spanning multiple services require sagas or 2-phase commits.

4. **Testing Complexity** — Integration testing requires spinning up multiple 
   services. Contract testing becomes essential.

5. **Higher Initial Investment** — Getting infrastructure right (K8s, CI/CD 
   pipelines, observability stack) takes significant upfront effort.

6. **Data Management** — Each service ideally owns its database. Joining data 
   across services requires API calls or event-driven sync.
""",
    "monolithic architecture overview": """
**Monolithic Architecture** packages all application functionality into a 
single deployable unit.

**When Monoliths Work Well:**
- Early-stage startups: Ship fast, iterate quickly
- Small teams (< 10 engineers): Low coordination overhead
- Simple domains: Not every problem needs distributed systems
- Tight deadlines: No infrastructure investment needed upfront

**Famous examples:** 
- Basecamp (DHH actively advocates for monoliths)
- Shopify (runs on a massive, well-maintained Rails monolith)
- Stack Overflow (serves billions of requests from a monolith)

**The "Majestic Monolith"** — a well-structured monolith with clear internal 
module boundaries can scale surprisingly far and remain maintainable.
""",
    "decision framework": """
**When to Choose Microservices:**
✓ Team > 20 engineers with clear domain ownership
✓ Different components have radically different scaling needs  
✓ You need technology diversity across components
✓ You have DevOps maturity (K8s, CI/CD, observability)
✓ Business domains are well-understood and stable

**When to Choose a Monolith:**
✓ Early stage / MVP / startup
✓ Small team (< 10 engineers)
✓ Domain is not yet well-understood
✓ Speed of delivery is paramount
✓ Limited DevOps resources

**The Pragmatic Path:** Start with a well-structured monolith. Extract 
services when you feel real pain — not before. Martin Fowler calls this 
the "Strangler Fig" pattern.
""",
}

DEFAULT_RESEARCH = """
This topic encompasses several important dimensions worth exploring.

**Key Findings:**
Research indicates this is a multi-faceted subject with both clear benefits 
and notable trade-offs. Expert consensus suggests a pragmatic, context-driven 
approach rather than dogmatic adherence to any single methodology.

**Evidence Base:**
Industry surveys, case studies from large-scale deployments, and academic 
literature all point to the importance of understanding your specific context 
before making architectural decisions.

**Practical Implications:**
Teams should evaluate their current maturity, team size, business requirements, 
and growth trajectory when making decisions in this domain.
"""


def _find_research(title: str) -> str:
    """Find the best matching research content for a sub-task title."""
    title_lower = title.lower()
    for key, content in RESEARCH_DB.items():
        # Check if any word from the key appears in the title
        key_words = key.split()
        matches = sum(1 for w in key_words if w in title_lower)
        if matches >= 2:
            return content
    return DEFAULT_RESEARCH


class ResearcherAgent(BaseAgent):
    name = AgentName.RESEARCHER

    def _execute(self, task: Task) -> Task:
        for sub_task in task.sub_tasks:
            research = _find_research(sub_task.title)
            sub_task.research_result = research.strip()
            sub_task.status = "done"
            task.research_data[sub_task.id] = research.strip()

        task.status = TaskStatus.WRITING
        return task

    def _input_summary(self, task: Task) -> str:
        return f"Researching {len(task.sub_tasks)} sub-tasks"

    def _output_summary(self, task: Task) -> str:
        done = sum(1 for st in task.sub_tasks if st.status == "done")
        return f"Completed research for {done}/{len(task.sub_tasks)} sub-tasks"
