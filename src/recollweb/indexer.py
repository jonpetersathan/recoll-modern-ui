"""
Recoll index lifecycle management, status reporting, background reindexing, and purge operations.
"""

import datetime
import os
import shutil
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

from recollweb.logging import logger


class IndexManager:
    """Manages Recoll indexer execution, status inspection, and maintenance tasks."""

    _lock = threading.Lock()
    _current_job: Optional[Dict[str, Any]] = None
    _recent_logs: List[str] = []
    _active_process: Optional[subprocess.Popen] = None

    @classmethod
    def _append_log(cls, line: str):
        with cls._lock:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            cls._recent_logs.append(f"[{ts}] {line.rstrip()}")
            if len(cls._recent_logs) > 200:
                cls._recent_logs.pop(0)

    @classmethod
    def get_logs(cls) -> List[str]:
        with cls._lock:
            return list(cls._recent_logs)

    @classmethod
    def get_status(cls, conf_dir: str) -> Dict[str, Any]:
        """
        Inspect the current status of the search index:
        - Active / Idle state
        - Document count
        - Database disk size
        - Topdirs from recoll.conf
        - Last indexed timestamp
        """
        xapian_dir = os.path.join(conf_dir, "xapiandb")
        db_exists = os.path.isdir(xapian_dir)
        db_size_bytes = 0
        db_mtime = None

        if db_exists:
            try:
                for root, _, files in os.walk(xapian_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            db_size_bytes += os.path.getsize(fp)
                        except OSError:
                            pass
                db_mtime = os.path.getmtime(xapian_dir)
            except Exception:
                pass

        # Parse topdirs from recoll.conf
        topdirs: List[str] = []
        conf_file = os.path.join(conf_dir, "recoll.conf")
        if os.path.isfile(conf_file):
            try:
                with open(conf_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("topdirs"):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                topdirs = parts[1].strip().split()
            except Exception:
                pass

        # Try to resolve document count via python3-recoll
        doc_count = 0
        try:
            from recoll import recoll as rcl
            db = rcl.connect(conf_dir)
            doc_count = db.doccount()
        except Exception:
            # Fallback estimation or 0
            pass

        # Determine job status
        with cls._lock:
            job = dict(cls._current_job) if cls._current_job else {
                "status": "idle",
                "mode": None,
                "start_time": None,
                "exit_code": None,
                "error": None,
            }

        # Check if process is still running
        if cls._active_process:
            poll = cls._active_process.poll()
            if poll is None:
                job["status"] = "running"
            else:
                cls._active_process = None

        return {
            "exists": db_exists,
            "status": job["status"],
            "job": job,
            "doc_count": doc_count,
            "size_bytes": db_size_bytes,
            "size_human": cls._format_bytes(db_size_bytes),
            "last_indexed": datetime.datetime.fromtimestamp(db_mtime).strftime("%Y-%m-%d %H:%M:%S") if db_mtime else "Never",
            "topdirs": topdirs,
            "conf_dir": conf_dir,
            "logs": cls.get_logs()[-30:],
        }

    @staticmethod
    def _format_bytes(size: int) -> str:
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        s = float(size)
        for u in units:
            if s < 1024.0 or u == units[-1]:
                return f"{s:.1f} {u}"
            s /= 1024.0
        return f"{size} B"

    @classmethod
    def start_indexing(cls, conf_dir: str, full: bool = False) -> Dict[str, Any]:
        """
        Trigger background indexing (full or incremental).
        full=True runs `recollindex -z -c <confdir>` (rebuilds entire index)
        full=False runs `recollindex -c <confdir>` (incremental update)
        """
        with cls._lock:
            if cls._current_job and cls._current_job.get("status") == "running":
                return {"success": False, "error": "An indexing task is already running."}

            cls._current_job = {
                "status": "running",
                "mode": "full" if full else "incremental",
                "start_time": time.time(),
                "exit_code": None,
                "error": None,
            }
            cls._recent_logs.clear()

        mode_str = "Full re-index (-z)" if full else "Incremental update"
        cls._append_log(f"Starting {mode_str} with confdir: {conf_dir}")

        thread = threading.Thread(
            target=cls._run_indexer_worker,
            args=(conf_dir, full),
            daemon=True,
        )
        thread.start()

        return {"success": True, "mode": "full" if full else "incremental"}

    @classmethod
    def purge_index(cls, conf_dir: str) -> Dict[str, Any]:
        """
        Purge/reset the search index by removing xapiandb.
        """
        with cls._lock:
            if cls._current_job and cls._current_job.get("status") == "running":
                return {"success": False, "error": "Cannot purge index while an indexing task is active."}

        xapian_dir = os.path.join(conf_dir, "xapiandb")
        cls._append_log(f"Purging search index at {xapian_dir}...")

        try:
            if os.path.exists(xapian_dir):
                shutil.rmtree(xapian_dir)
                cls._append_log("Index directory successfully removed.")
            else:
                cls._append_log("No index directory found to remove.")
            return {"success": True}
        except Exception as exc:
            cls._append_log(f"Failed to purge index: {exc}")
            logger.error("INDEX_PURGE_ERROR: %s", exc)
            return {"success": False, "error": str(exc)}

    @classmethod
    def _run_indexer_worker(cls, conf_dir: str, full: bool):
        cmd = ["recollindex", "-c", conf_dir]
        if full:
            cmd.insert(1, "-z")

        cls._append_log(f"Executing command: {' '.join(cmd)}")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            cls._active_process = proc

            if proc.stdout:
                for line in proc.stdout:
                    if line:
                        cls._append_log(line.strip())

            proc.wait()
            exit_code = proc.returncode
            cls._append_log(f"recollindex finished with exit code {exit_code}")

            with cls._lock:
                if cls._current_job:
                    cls._current_job["status"] = "completed" if exit_code == 0 else "failed"
                    cls._current_job["exit_code"] = exit_code
        except Exception as exc:
            cls._append_log(f"Worker exception: {exc}")
            with cls._lock:
                if cls._current_job:
                    cls._current_job["status"] = "failed"
                    cls._current_job["error"] = str(exc)
        finally:
            cls._active_process = None
