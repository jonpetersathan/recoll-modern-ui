#!/usr/bin/env python3
"""
Standalone Server Runner for Recoll Modern UI
"""

import argparse
import logging
import os
import signal
import sys
import warnings

# Suppress ResourceWarning noise from Waitress/asyncore socket and file wrappers
warnings.filterwarnings("ignore", category=ResourceWarning)

# Change to script directory and ensure it's in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR:
    os.chdir(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import webui


def handle_shutdown(signum, frame):
    """Handle graceful shutdown on SIGTERM / SIGINT from Docker/Podman."""
    webui.logger.info("Received termination signal (%d), shutting down cleanly...", signum)
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    parser = argparse.ArgumentParser(description="Recoll Modern UI Standalone Web Server")
    parser.add_argument('-a', '--addr', default='127.0.0.1', help='Address to bind to [default: 127.0.0.1]')
    parser.add_argument('-p', '--port', default=8080, type=int, help='Port to listen on [default: 8080]')
    parser.add_argument('-c', '--config', default=None, type=str, help='Recoll configuration directory')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    if args.config:
        os.environ["RECOLL_CONFDIR"] = args.config

    if args.debug:
        webui.bottle.debug(True)

    log_level_name = os.environ.get('RECOLL_LOGLEVEL', 'INFO').upper()
    webui.logger.info("Starting Recoll Modern UI on http://%s:%d (Log Level: %s)", args.addr, args.port, log_level_name)

    webui.bottle.run(app=webui.app, server='waitress', host=args.addr, port=args.port)


if __name__ == '__main__':
    main()
