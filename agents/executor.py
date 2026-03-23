"""
Executor Agent — powered by Claude Opus 4.6

Responsibility:
- Generate complete, production-ready code for each file
- Use the plan + research to produce high-quality output
- Write actual files to disk
- Handle fixes when the Reviewer finds issues
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a world-class Senior Software Engineer and Full-Stack Developer.

Your job is to generate complete, production-ready code for a single file.

Rules:
- Write COMPLETE file contents — never use placeholders like "// add code here"
- Follow all best practices from the research provided
- The code must be fully functional and immediately usable
- Use modern approaches and clean code principles
- Add helpful comments where needed
- Return ONLY the raw file contents — no markdown fences, no explanation, just the code/content

If the file is HTML: return complete HTML
If the file is CSS: return complete CSS
If the file is JavaScript: return complete JavaScript
If the file is Python: return complete Python
etc.
"""

FIX_SYSTEM_PROMPT = """You are a world-class Senior Software Engineer fixing code issues.

You will receive:
1. The original file content
2. Specific issues found by a code reviewer

Your job is to fix ALL identified issues and return the corrected file.

Rules:
- Fix every issue mentioned
- Don't break anything that was working
- Return ONLY the complete corrected file contents — no explanation, no markdown fences
"""


def generate_file(
    file_path: str,
    file_description: str,
    goal_summary: str,
    research: str,
    tech_stack: list,
    execution_steps: list,
    all_files: list
) -> str:
    """
    Generates complete content for a single file.
    Returns the file content as a string.
    """
    stack_text = ", ".join(tech_stack) if tech_stack else "web technologies"
    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(execution_steps))
    files_text = "\n".join(f"- {f['path']}: {f['description']}" for f in all_files)

    prompt = f"""Project Goal: {goal_summary}
Tech Stack: {stack_text}

File to Create: {file_path}
File Purpose: {file_description}

Project File Structure:
{files_text}

Execution Steps:
{steps_text}

Research & Best Practices:
{research}

Generate the complete contents for: {file_path}
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def fix_file(file_path: str, original_content: str, issues: list) -> str:
    """
    Fixes a file based on reviewer feedback.
    Returns the corrected file content.
    """
    issues_text = "\n".join(f"- {issue}" for issue in issues)

    prompt = f"""File: {file_path}

Original Content:
{original_content}

Issues to Fix:
{issues_text}

Return the complete corrected file.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        system=FIX_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def run(plan: dict, research: str, output_dir: str) -> dict:
    """
    Executes the full plan: generates all files and writes them to disk.
    Returns a dict of {file_path: content}.
    """
    files = plan.get("file_structure", [])
    goal = plan.get("goal_summary", "")
    tech_stack = plan.get("tech_stack", [])
    steps = plan.get("execution_steps", [])

    generated = {}

    print(f"\n  [Executor] Building {len(files)} file(s)...")

    for i, file_info in enumerate(files, 1):
        rel_path = file_info["path"]
        description = file_info["description"]

        print(f"    [{i}/{len(files)}] Generating: {rel_path}")

        content = generate_file(
            file_path=rel_path,
            file_description=description,
            goal_summary=goal,
            research=research,
            tech_stack=tech_stack,
            execution_steps=steps,
            all_files=files
        )

        # Write file to output directory
        full_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        generated[rel_path] = content
        print(f"    [✓] Written: {full_path}")

    return generated


def apply_fixes(fixes: dict, output_dir: str) -> dict:
    """
    Applies reviewer-requested fixes to files.
    fixes: {file_path: [list of issues]}
    Returns updated generated dict.
    """
    fixed = {}

    for rel_path, issues in fixes.items():
        full_path = os.path.join(output_dir, rel_path)

        # Read current content
        with open(full_path, "r", encoding="utf-8") as f:
            original = f.read()

        print(f"    [Fixing] {rel_path} ({len(issues)} issue(s))")
        corrected = fix_file(rel_path, original, issues)

        # Write corrected content
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(corrected)

        fixed[rel_path] = corrected
        print(f"    [✓] Fixed: {full_path}")

    return fixed
