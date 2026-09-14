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

from recollweb.config import RecollConfManager
from recollweb.db import get_global_setting, set_global_setting
from recollweb.logging import logger


class IndexManager:
    """Manages Recoll indexer execution, status inspection, and maintenance tasks."""

    _lock = threading.Lock()
    _current_job: Optional[Dict[str, Any]] = None
    _recent_logs: List[str] = []
    _active_process: Optional[subprocess.Popen] = None

    _data_size_lock = threading.Lock()
    _data_size_cache: Dict[str, Any] = {
        "bytes": None,
        "human": None,
        "calculating": False,
        "updated_at": None,
    }
    _data_size_thread: Optional[threading.Thread] = None

    @classmethod
    def _append_log(cls, line: str):
        with cls._lock:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            cls._recent_logs.append(f"[{ts}] {line.rstrip()}")
            if len(cls._recent_logs) > 2000:
                cls._recent_logs.pop(0)

    @classmethod
    def get_logs(cls) -> List[str]:
        with cls._lock:
            return list(cls._recent_logs)

    @classmethod
    def reset_data_size_cache(cls):
        """Reset in-memory data size cache (primarily for tests)."""
        with cls._data_size_lock:
            cls._data_size_cache = {
                "bytes": None,
                "human": None,
                "calculating": False,
                "updated_at": None,
            }

    @classmethod
    def get_cached_data_size(cls, conf_dir: str) -> Dict[str, Any]:
        """
        Retrieve cached data size metrics without blocking.
        If cache is empty, attempts to load from SQLite global_settings.
        """
        with cls._data_size_lock:
            cached_bytes = cls._data_size_cache["bytes"]
            is_calculating = cls._data_size_cache["calculating"]
            updated_at = cls._data_size_cache["updated_at"]

        if cached_bytes is None:
            try:
                db_val = get_global_setting(conf_dir, "cached_data_size_bytes")
                db_time = get_global_setting(conf_dir, "cached_data_size_time")
                if db_val is not None and str(db_val).strip().isdigit():
                    cached_bytes = int(str(db_val).strip())
                    updated_at = db_time
                    with cls._data_size_lock:
                        cls._data_size_cache["bytes"] = cached_bytes
                        cls._data_size_cache["human"] = cls._format_bytes(cached_bytes)
                        cls._data_size_cache["updated_at"] = updated_at
            except Exception as exc:
                logger.warning("Failed to load cached data size from DB: %s", exc)

        if is_calculating:
            size_human = "-"
        elif cached_bytes is not None:
            size_human = cls._format_bytes(cached_bytes)
        else:
            size_human = "-"

        return {
            "bytes": cached_bytes if cached_bytes is not None else 0,
            "human": size_human,
            "calculating": is_calculating,
            "updated_at": updated_at,
        }

    @classmethod
    def trigger_data_size_calculation(cls, conf_dir: str, force: bool = False) -> bool:
        """
        Trigger asynchronous calculation of /data directory size via 'du'.
        Returns True if a new background task was started, False if already running.
        """
        with cls._data_size_lock:
            if cls._data_size_cache["calculating"] and not force:
                return False
            cls._data_size_cache["calculating"] = True
            cls._data_size_cache["human"] = "-"

        thread = threading.Thread(
            target=cls._run_data_size_worker,
            args=(conf_dir,),
            daemon=True,
            name="du-data-size-worker",
        )
        cls._data_size_thread = thread
        thread.start()
        return True

    @classmethod
    def _run_data_size_worker(cls, conf_dir: str):
        """
        Background worker running 'du -s -b' on /data or configured topdirs.
        Updates in-memory cache and persists to SQLite global_settings.
        """
        logger.info("Starting background data size calculation via 'du'...")
        data_size_bytes = None

        # Resolve target paths to measure
        data_dir = "/data"
        target_dirs = []
        if os.path.exists(data_dir):
            target_dirs.append(data_dir)
        else:
            # Fallback to topdirs from recoll.conf
            conf_file = os.path.join(conf_dir, "recoll.conf")
            if os.path.isfile(conf_file):
                try:
                    with open(conf_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("topdirs"):
                                parts = line.split("=", 1)
                                if len(parts) == 2:
                                    target_dirs = [d for d in parts[1].strip().split() if os.path.exists(d)]
                except Exception:
                    pass

        if target_dirs:
            total_bytes = 0
            success = True
            for td in target_dirs:
                try:
                    out = subprocess.check_output(
                        ["du", "-s", "-b", td],
                        stderr=subprocess.DEVNULL,
                        text=True,
                        timeout=600,
                    )
                    parts = out.strip().split()
                    if parts and parts[0].isdigit():
                        total_bytes += int(parts[0])
                    else:
                        success = False
                except Exception as exc:
                    logger.warning("Asynchronous 'du -s -b %s' failed: %s", td, exc)
                    success = False
            if success:
                data_size_bytes = total_bytes

        with cls._data_size_lock:
            cls._data_size_cache["calculating"] = False
            if data_size_bytes is not None:
                cls._data_size_cache["bytes"] = data_size_bytes
                cls._data_size_cache["human"] = cls._format_bytes(data_size_bytes)
                cls._data_size_cache["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        if data_size_bytes is not None:
            try:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                set_global_setting(conf_dir, "cached_data_size_bytes", str(data_size_bytes))
                set_global_setting(conf_dir, "cached_data_size_time", now_str)
                logger.info("Data size calculation complete: %d bytes (%s)", data_size_bytes, cls._format_bytes(data_size_bytes))
            except Exception as exc:
                logger.warning("Failed to save data size to DB: %s", exc)

    @classmethod
    def get_status(cls, conf_dir: str) -> Dict[str, Any]:
        """
        Inspect the current status of the search index:
        - Active / Idle state
        - Document count
        - Database disk size
        - Topdirs from recoll.conf
        - Last indexed timestamp
        - Asynchronously cached data size
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

        # Try to resolve document count via python3-recoll query on dir:/
        doc_count = 0
        try:
            from recoll import recoll as rcl
            db = rcl.connect(conf_dir)
            q = db.query()
            q.execute('dir:/')
            if q.rowcount is not None and q.rowcount >= 0:
                doc_count = q.rowcount
        except Exception:
            pass

        if doc_count <= 0 and db_exists:
            # Fallback to recollq CLI
            try:
                out = subprocess.check_output(
                    ['recollq', '-c', conf_dir, '-Q', 'dir:/'],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=3
                )
                for line in out.splitlines():
                    if 'results' in line:
                        parts = line.strip().split()
                        if parts and parts[0].isdigit():
                            doc_count = int(parts[0])
                            break
            except Exception:
                pass

        # Asynchronously cached data size (never blocks request thread)
        size_info = cls.get_cached_data_size(conf_dir)
        data_size_bytes = size_info["bytes"]
        data_size_human = size_info["human"]
        data_size_calculating = size_info["calculating"]

        # If cache is completely empty and no calculation is running, trigger one in background
        if size_info["updated_at"] is None and not data_size_calculating:
            cls.trigger_data_size_calculation(conf_dir)
            data_size_calculating = True
            data_size_human = "-"

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
            "data_size_bytes": data_size_bytes,
            "data_size_human": data_size_human,
            "data_size_calculating": data_size_calculating,
            "last_indexed": datetime.datetime.fromtimestamp(db_mtime).strftime("%Y-%m-%d %H:%M") if db_mtime else "Never",
            "topdirs": topdirs,
            "conf_dir": conf_dir,
            "logs": cls.get_logs()[-500:],
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

        mode_str = "full re-index" if full else "Incremental update"
        cls._append_log(f"Starting {mode_str} with confdir: {conf_dir}")

        # Trigger asynchronous data size recalculation
        cls.trigger_data_size_calculation(conf_dir, force=True)

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

        # Trigger asynchronous data size recalculation
        cls.trigger_data_size_calculation(conf_dir, force=True)

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
    def get_index_config(cls, conf_dir: str) -> Dict[str, Any]:
        """Fetch the current 9 managed index configuration parameters."""
        return RecollConfManager.get_index_config(conf_dir)

    @classmethod
    def update_index_config(cls, conf_dir: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate, update, and atomically save index configuration parameters."""
        return RecollConfManager.update_index_config(conf_dir, updates)

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
            # Update data size calculation upon indexing completion
            cls.trigger_data_size_calculation(conf_dir, force=True)
