"""Fill tasks.json with N tasks so GET /tasks has a realistic payload.

Usage: python -m tasks.seed [N]   (default 5000)
"""
import sys
from pathlib import Path

from .models import Task
from .storage import TaskStorage

count = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
TaskStorage(Path("tasks.json")).save(
    [Task(id=i, title=f"Seed task {i}", tags=["seed"]) for i in range(1, count + 1)]
)
print(f"Seeded {count} tasks into tasks.json")
