#!/usr/bin/env python3
"""
Axiom Omni - Floating Button & Desktop Voice Controller Launcher
===============================================================
Launches the omnipresent desktop floating orb and voice control HUD.
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from src.omni_floating_widget import main

if __name__ == "__main__":
    main()
