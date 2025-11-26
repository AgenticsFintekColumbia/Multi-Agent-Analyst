"""
reorganize_project.py

Script to reorganize the project into a clean structure.
Run this from your project root directory.

WARNING: This will move files. Make sure you have a backup or git commit first!
"""

import os
import shutil
from pathlib import Path


def create_directory_structure():
    """Create the new directory structure."""
    print("Creating new directory structure...")
    
    directories = [
        "src/explainer",
        "src/recommender",
        "tests",
        "docs",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory}/")
    
    # Create __init__.py files for Python packages
    init_files = [
        "src/__init__.py",
        "src/explainer/__init__.py",
        "src/recommender/__init__.py",
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"  ✓ Created {init_file}")


def move_files():
    """Move files to their new locations."""
    print("\nMoving files to new structure...")
    
    # Define file movements: (source, destination)
    moves = [
        # Explainer files
        ("multi_explainer_agents.py", "src/explainer/agents.py"),
        ("multi_explainer_tasks.py", "src/explainer/tasks.py"),
        ("multi_explainer.py", "src/explainer/orchestrator.py"),
        
        # Recommender files
        ("multi_agents.py", "src/recommender/agents.py"),
        ("multi_tasks.py", "src/recommender/tasks.py"),
        ("multi_recommender.py", "src/recommender/orchestrator.py"),
        
        # Tests
        ("test_multi_explainer.py", "tests/test_explainer.py"),
        ("test_multi_recommender.py", "tests/test_recommender.py"),
        
        # Documentation
        ("EXPLAINER_ARCHITECTURE.md", "docs/EXPLAINER_ARCHITECTURE.md"),
        ("RECOMMENDER_ARCHITECTURE.md", "docs/RECOMMENDER_ARCHITECTURE.md"),
        ("IMPLEMENTATION_SUMMARY.md", "docs/IMPLEMENTATION_SUMMARY.md"),
    ]
    
    for source, dest in moves:
        if os.path.exists(source):
            shutil.move(source, dest)
            print(f"  ✓ Moved {source} → {dest}")
        else:
            print(f"  ⚠ Skipped {source} (not found)")


def list_files_to_delete():
    """List files that should be manually deleted."""
    print("\n" + "=" * 70)
    print("FILES TO DELETE MANUALLY:")
    print("=" * 70)
    
    to_delete = [
        "agents.py",
        "tasks.py",
        "crew_config.py",
        "show_feather_structure.py",
        "another_infographic.png",
        "infographic.png",
    ]
    
    for file in to_delete:
        if os.path.exists(file):
            print(f"  ❌ {file}")
        else:
            print(f"  ✓ {file} (already removed)")
    
    print("\nOptional to delete (if you don't need CLI):")
    print("  ❌ main.py")
    
    print("\nTo delete these files, run:")
    print("  rm agents.py tasks.py crew_config.py show_feather_structure.py")
    print("  rm another_infographic.png infographic.png")


def create_init_files_with_imports():
    """Create __init__.py files with proper imports."""
    print("\nCreating __init__.py files with imports...")
    
    # src/explainer/__init__.py
    explainer_init = '''"""
Explainer team: Multi-agent system to explain analyst recommendations.
"""

from .agents import (
    create_fundamental_explainer_analyst,
    create_technical_explainer_analyst,
    create_news_explainer_analyst,
    create_explainer_manager,
)

from .tasks import (
    create_fundamental_explainer_task,
    create_technical_explainer_task,
    create_news_explainer_task,
    create_explainer_manager_task,
)

from .orchestrator import run_multi_analyst_explainer

__all__ = [
    'create_fundamental_explainer_analyst',
    'create_technical_explainer_analyst',
    'create_news_explainer_analyst',
    'create_explainer_manager',
    'create_fundamental_explainer_task',
    'create_technical_explainer_task',
    'create_news_explainer_task',
    'create_explainer_manager_task',
    'run_multi_analyst_explainer',
]
'''
    
    # src/recommender/__init__.py
    recommender_init = '''"""
Recommender team: Multi-agent system to generate model recommendations.
"""

from .agents import (
    fundamental_agent,
    technical_agent,
    news_agent,
    recommender_manager,
)

from .tasks import (
    fundamental_task,
    technical_task,
    news_task,
    create_recommender_manager_task,
)

from .orchestrator import run_multi_analyst_recommendation

__all__ = [
    'fundamental_agent',
    'technical_agent',
    'news_agent',
    'recommender_manager',
    'fundamental_task',
    'technical_task',
    'news_task',
    'create_recommender_manager_task',
    'run_multi_analyst_recommendation',
]
'''
    
    # Write the files
    with open("src/explainer/__init__.py", "w") as f:
        f.write(explainer_init)
    print("  ✓ Created src/explainer/__init__.py with imports")
    
    with open("src/recommender/__init__.py", "w") as f:
        f.write(recommender_init)
    print("  ✓ Created src/recommender/__init__.py with imports")


def show_next_steps():
    """Show what needs to be done after reorganization."""
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("""
1. Update imports in gui_app.py:
   Change:
     from multi_explainer import run_multi_analyst_explainer
     from multi_recommender import run_multi_analyst_recommendation
   To:
     from src.explainer import run_multi_analyst_explainer
     from src.recommender import run_multi_analyst_recommendation

2. Update imports in tests/test_explainer.py:
   Change:
     from multi_explainer import run_multi_analyst_explainer
   To:
     from src.explainer import run_multi_analyst_explainer

3. Update imports in tests/test_recommender.py:
   Change:
     from multi_recommender import run_multi_analyst_recommendation
   To:
     from src.recommender import run_multi_analyst_recommendation

4. Update src/explainer/orchestrator.py imports:
   Change:
     from multi_explainer_agents import (...)
     from multi_explainer_tasks import (...)
   To:
     from .agents import (...)
     from .tasks import (...)

5. Update src/recommender/orchestrator.py imports:
   Change:
     from multi_agents import (...)
     from multi_tasks import (...)
   To:
     from .agents import (...)
     from .tasks import (...)

6. Test everything:
   python -m pytest tests/
   python -m streamlit run gui_app.py

7. Delete old files (listed above)

8. Commit to git:
   git add .
   git commit -m "Reorganize project structure"
""")


def main():
    """Main reorganization function."""
    print("=" * 70)
    print("PROJECT REORGANIZATION SCRIPT")
    print("=" * 70)
    print("\n⚠️  WARNING: This will move files around!")
    print("Make sure you have a backup or git commit first.\n")
    
    response = input("Continue? (yes/no): ").lower()
    if response != "yes":
        print("Aborted.")
        return
    
    try:
        create_directory_structure()
        move_files()
        create_init_files_with_imports()
        list_files_to_delete()
        show_next_steps()
        
        print("\n" + "=" * 70)
        print("✅ REORGANIZATION COMPLETE!")
        print("=" * 70)
        print("\nFollow the NEXT STEPS above to update imports.")
        
    except Exception as e:
        print(f"\n❌ Error during reorganization: {e}")
        print("You may need to manually fix some files.")


if __name__ == "__main__":
    main()