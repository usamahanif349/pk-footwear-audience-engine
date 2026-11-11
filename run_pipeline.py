"""Rebuild every processed table from the raw data (after data/raw/ is filled).

Command Prompt:  python run_pipeline.py
"""
import runpy

for step in ["needs", "content", "segments"]:
    print(f"\n=== {step} ===")
    runpy.run_path(f"src/engine/{step}.py", run_name="__main__")
