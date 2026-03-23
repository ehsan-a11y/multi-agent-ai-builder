"""
Multi-Agent System v2 — Entry Point

4 Specialized Agents working in a pipeline:
  [1] Planner    → Breaks goal into structured plan + file structure
  [2] Researcher → Gathers best practices and patterns
  [3] Executor   → Generates all code files (writes to disk)
  [4] Reviewer   → Reviews quality, triggers auto-fixes if needed

Example prompts:
  "Build me a personal portfolio website with dark theme"
  "Create a landing page for a coffee shop called Brew & Co"
  "Build a to-do list web app with local storage"
  "Create a restaurant menu website with modern design"
"""

import sys
import os

# Make pipeline importable from this directory
sys.path.insert(0, os.path.dirname(__file__))

import pipeline


def get_project_name(goal: str) -> str:
    """Generate a clean folder name from the goal."""
    name = goal.lower()
    name = name.replace("build me", "").replace("create", "").replace("make", "")
    name = name.strip()
    # Keep only alphanumeric and spaces, then convert to underscores
    name = "".join(c if c.isalnum() or c == " " else "" for c in name)
    name = "_".join(name.split())[:30]
    return name or "project"


def main():
    print("=" * 60)
    print("  Multi-Agent AI Builder — v2")
    print("  Planner → Researcher → Executor → Reviewer")
    print("=" * 60)
    print("\nExample prompts:")
    print("  • Build me a portfolio website with dark theme")
    print("  • Create a landing page for a coffee shop")
    print("  • Build a to-do list web app with local storage")
    print("\nType 'quit' to exit.\n")

    while True:
        user_input = input("What should I build? ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        project_name = get_project_name(user_input)

        try:
            result = pipeline.run(
                user_goal=user_input,
                project_name=project_name
            )

            print(f"\n✓ Done! Open your project at:")
            print(f"  {result['output_dir']}")

            # Show reviewer summary if available
            review = result.get("review", {})
            if review and review.get("summary"):
                print(f"\nReviewer says: {review['summary']}")

        except Exception as e:
            print(f"\n[Error] {e}")
            import traceback
            traceback.print_exc()

        print()


if __name__ == "__main__":
    main()
