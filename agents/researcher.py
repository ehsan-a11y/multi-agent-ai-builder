"""
Researcher Agent — powered by Claude Opus 4.6

Responsibility:
- Research best practices for the specific tech stack
- Find patterns, conventions, and approaches
- Provide rich context to the Executor agent
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a Senior Technical Researcher and Solutions Architect.

Your job is to research and provide detailed, actionable guidance on:
- Best practices for the given tech stack
- Common patterns and conventions
- Specific implementation details
- Potential pitfalls to avoid
- Modern approaches and standards

Format your response as:
## Research Findings

### [Topic Name]
[Detailed findings with specific examples]

Be thorough, specific, and technical. Your output will be used directly by a coder to build the project.
"""


def run(goal_summary: str, tech_stack: list, research_topics: list) -> str:
    """
    Researches best practices and patterns for the plan.
    Returns a detailed research report.
    """
    print(f"\n  [Researcher] Researching {len(research_topics)} topic(s)...")

    topics_text = "\n".join(f"- {t}" for t in research_topics)
    stack_text = ", ".join(tech_stack) if tech_stack else "web technologies"

    prompt = f"""Project Goal: {goal_summary}
Tech Stack: {stack_text}

Research Topics:
{topics_text}

Provide detailed research findings on all topics above.
Include specific code patterns, best practices, and implementation guidance.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.content[0].text
    print(f"  [Researcher] Research complete ({len(result)} chars)")
    return result
