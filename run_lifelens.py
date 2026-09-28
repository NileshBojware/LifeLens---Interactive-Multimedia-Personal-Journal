"""
LifeLens Root Launcher
Convenience launcher to run LifeLens from the repository root.
"""
import os
import sys

project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LifeLens")
sys.path.insert(0, project_dir)

from main import main

if __name__ == "__main__":
    main()
