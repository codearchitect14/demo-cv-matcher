"""
Setup script to add project root to Python path
Run this before importing any project modules
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Added {project_root} to Python path")