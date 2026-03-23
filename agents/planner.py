"""
Planner Agent — powered by Claude Opus 4.6 (adaptive thinking)

Responsibility:
- Understand the user's high-level goal
- Break it into a structured execution plan
- Define the file structure (for website/app builds)
- Assign clear tasks to Researcher and Executor
"""

import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a world-class Technical Project Planner.

When given a user goal, you must:
1. Understand what needs to be built
2. Break the work into clear, ordered steps
3. Define the exact file structure needed
4. Identify what research is needed before building
5. Define what the Executor agent should create

Return ONLY valid JSON in this exact format:
{
  "goal_summary": "One sentence summary of what we're building",
  "research_topics": [
    "Topic or question the researcher should investigate"
  ],
  "file_structure": [
    {
      "path": "relative/path/to/file.ext",
      "description": "What this file does and what it should contain"
    }
  ],
  "execution_steps": [
    "Step 1: ...",
    "Step 2: ..."
  ],
  "tech_stack": ["HTML", "CSS", "JavaScript"],
  "review_focus": [
    "What the reviewer should specifically check for"
  ]
}

Rules:
- Return ONLY the JSON. No markdown, no extra text.
- Be specific and detailed in descriptions.
- For websites: always include index.html, style.css, script.js at minimum.
- For web apps: include all necessary files.
"""


def run(user_goal: str) -> dict:
    """
    Takes a user goal and returns a structured execution plan.
    Uses adaptive thinking for deep planning.
    """
    print("\n  [Planner] Analyzing goal and creating execution plan...")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Create a detailed execution plan for this goal:\n\n{user_goal}"
            }
        ]
    )

    # Extract text from response (skip thinking blocks)
    raw = ""
    for block in response.content:
        if block.type == "text":
            raw = block.text.strip()
            break

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        plan = json.loads(raw)
        print(f"  [Planner] Plan created:")
        print(f"    Goal: {plan.get('goal_summary', 'N/A')}")
        print(f"    Files to create: {len(plan.get('file_structure', []))}")
        print(f"    Research topics: {len(plan.get('research_topics', []))}")
        return plan
    except json.JSONDecodeError as e:
        raise ValueError(f"Planner returned invalid JSON:\n{raw}\nError: {e}")
