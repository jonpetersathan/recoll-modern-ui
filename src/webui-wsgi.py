#!/usr/bin/env python3
"""
WSGI Application Entrypoint for Recoll Modern UI
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR:
    os.chdir(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import webui

application = webui.app
