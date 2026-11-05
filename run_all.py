#!/usr/bin/env python3
"""Run the full Week 6 pipeline in the documented order. Figures go to assets/."""
import subprocess
import sys
from pathlib import Path

STEPS = [
    "src.multi_scale_engine",
    "viz.plot_potential_field",
    "viz.plot_current_density",
    "viz.plot_dissolution_map",
    "viz.plot_inverse_posterior",
    "viz.plot_parameter_sensitivity",
    "viz.generate_gif",
]

for step in STEPS:
    print(f"\n=== {step} ===", flush=True)
    subprocess.run([sys.executable, "-m", step], check=True, cwd=Path(__file__).parent)
