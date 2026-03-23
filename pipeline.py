"""
Multi-Agent Pipeline Orchestrator

Pipeline:
  User Goal
     ↓
  [1] Planner Agent     → Creates structured execution plan
     ↓
  [2] Researcher Agent  → Gathers best practices & patterns
     ↓
  [3] Executor Agent    → Generates all code files (writes to disk)
     ↓
  [4] Reviewer Agent    → Reviews code quality & correctness
     ↓
  [5] Auto-Fix Loop     → Executor fixes issues found by Reviewer
     ↓
  Final Output (files written to /output/<project_name>/)
"""

import os
import time
from datetime import datetime

from agents import planner, researcher, executor, reviewer


MAX_FIX_ROUNDS = 2  # Maximum auto-fix iterations before accepting as-is


def run(user_goal: str, project_name: str = None) -> dict:
    """
    Runs the full multi-agent pipeline for a given goal.

    Args:
        user_goal: The user's high-level request (e.g., "Build me a portfolio website")
        project_name: Optional name for the output folder

    Returns:
        dict with keys: plan, research, generated_files, review, output_dir, success
    """
    start_time = time.time()

    # Create output directory
    if not project_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"project_{timestamp}"

    output_dir = os.path.join(
        os.path.dirname(__file__), "output", project_name
    )
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Multi-Agent Pipeline Starting")
    print(f"  Goal: {user_goal[:60]}{'...' if len(user_goal) > 60 else ''}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    # ─────────────────────────────────────────────
    # STAGE 1: PLANNER
    # ─────────────────────────────────────────────
    print("\n[STAGE 1/4] PLANNER — Breaking down the goal...")
    plan = planner.run(user_goal)

    # ─────────────────────────────────────────────
    # STAGE 2: RESEARCHER
    # ─────────────────────────────────────────────
    print("\n[STAGE 2/4] RESEARCHER — Gathering best practices...")
    research_report = researcher.run(
        goal_summary=plan.get("goal_summary", user_goal),
        tech_stack=plan.get("tech_stack", []),
        research_topics=plan.get("research_topics", [])
    )

    # ─────────────────────────────────────────────
    # STAGE 3: EXECUTOR — Generate all files
    # ─────────────────────────────────────────────
    print("\n[STAGE 3/4] EXECUTOR — Building the project...")
    generated_files = executor.run(
        plan=plan,
        research=research_report,
        output_dir=output_dir
    )

    # ─────────────────────────────────────────────
    # STAGE 4: REVIEWER + AUTO-FIX LOOP
    # ─────────────────────────────────────────────
    print("\n[STAGE 4/4] REVIEWER — Checking code quality...")
    final_review = None
    fix_round = 0

    while fix_round <= MAX_FIX_ROUNDS:
        review_result = reviewer.run(generated_files, plan)
        final_review = review_result

        critical_fixes = review_result.get("critical_fixes", {})
        approved = review_result.get("approved", False)

        if approved or not critical_fixes:
            print(f"\n  [✓] Build APPROVED by Reviewer!")
            break

        if fix_round >= MAX_FIX_ROUNDS:
            print(f"\n  [!] Max fix rounds ({MAX_FIX_ROUNDS}) reached. Accepting current state.")
            break

        fix_round += 1
        print(f"\n  [AUTO-FIX Round {fix_round}] Executor applying {len(critical_fixes)} fix(es)...")

        fixed = executor.apply_fixes(critical_fixes, output_dir)
        generated_files.update(fixed)

    # ─────────────────────────────────────────────
    # DONE
    # ─────────────────────────────────────────────
    elapsed = time.time() - start_time
    approved = final_review.get("approved", False) if final_review else False
    quality = final_review.get("overall_quality", "unknown") if final_review else "unknown"

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Files: {len(generated_files)}")
    print(f"  Quality: {quality.upper()}")
    print(f"  Status: {'✓ APPROVED' if approved else '⚠ ACCEPTED WITH NOTES'}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    # List all generated files
    print("\nGenerated Files:")
    for path in generated_files:
        size = len(generated_files[path])
        print(f"  • {path} ({size} chars)")

    return {
        "success": True,
        "plan": plan,
        "research": research_report,
        "generated_files": generated_files,
        "review": final_review,
        "output_dir": output_dir,
        "elapsed_seconds": elapsed,
    }
