"""Kept for older commands: same as ``launch.py play …``."""

import os
import sys

sys.argv.insert(1, "play")
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launch.py")).read())
