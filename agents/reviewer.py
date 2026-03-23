"""
Reviewer Agent — powered by Claude Opus 4.6 (adaptive thinking)

Responsibility:
- Review all generated files for correctness, quality, and completeness
- Check for bugs, security issues, accessibility, and best practices
- Return specific, actionable fix requests
- Approve or reject the build
"""

import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a world-class Senior Code Reviewer and QA Engineer.

You will review generated files for:
1. Correctness — Does the code actually work? Any syntax errors?
2. Completeness — Are all required features implemented?
3. Best practices — Clean code, naming conventions, structure
4. Security — No XSS, injection vulnerabilities, etc.
5. Accessibility — Proper HTML semantics, ARIA labels, alt text
6. Responsiveness — Mobile-friendly CSS, proper viewport
7. Cross-file consistency — Do files work together correctly?

Return ONLY valid JSON in this format:
{
  "approved": true or false,
  "overall_quality": "excellent|good|needs_improvement|poor",
  "summary": "Brief overall assessment",
  "files_reviewed": [
    {
      "path": "file path",
      "status": "approved|needs_fixes",
      "issues": [
        "Specific issue description"
      ],
      "strengths": [
        "What was done well"
      ]
    }
  ],
  "critical_fixes": {
    "file_path": ["issue 1", "issue 2"]
  }
}

Rules:
- Return ONLY the JSON. No markdown, no extra text.
- Be specific about issues — name the exact line/element/function
- Only flag real problems, not stylistic preferences
- "approved" = true only if there are NO critical issues
- "critical_fixes" should only include files that MUST be fixed
"""


def run(generated_files: dict, plan: dict) -> dict:
    """
    Reviews all generated files against the plan.
    Uses adaptive thinking for thorough review.
    Returns review results with specific fixes needed.
    """
    print(f"\n  [Reviewer] Reviewing {len(generated_files)} file(s)...")

    goal = plan.get("goal_summary", "")
    review_focus = plan.get("review_focus", [])
    tech_stack = plan.get("tech_stack", [])

    # Build the review content
    focus_text = "\n".join(f"- {f}" for f in review_focus) if review_focus else "- General code quality"
    stack_text = ", ".join(tech_stack) if tech_stack else "web technologies"

    files_content = ""
    for path, content in generated_files.items():
        files_content += f"\n{'='*60}\n"
        files_content += f"FILE: {path}\n"
        files_content += f"{'='*60}\n"
        files_content += content
        files_content += "\n"

    prompt = f"""Project Goal: {goal}
Tech Stack: {stack_text}

Review Focus Areas:
{focus_text}

Generated Files to Review:
{files_content}

Review all files thoroughly and return your assessment as JSON.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
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
        review = json.loads(raw)

        approved = review.get("approved", False)
        quality = review.get("overall_quality", "unknown")
        fixes_needed = len(review.get("critical_fixes", {}))

        print(f"  [Reviewer] Result: {'✓ APPROVED' if approved else '✗ NEEDS FIXES'}")
        print(f"  [Reviewer] Quality: {quality.upper()}")
        if fixes_needed > 0:
            print(f"  [Reviewer] Critical fixes needed in {fixes_needed} file(s)")

        return review
    except json.JSONDecodeError as e:
        raise ValueError(f"Reviewer returned invalid JSON:\n{raw}\nError: {e}")
