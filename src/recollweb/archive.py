"""
Background search result file archiving and ZIP generation manager.
"""

import datetime
import os
import threading
import time
import uuid
import zipfile
from typing import Any, Dict, Optional
from recollweb.constants import EXPORT_DIR
from recollweb.logging import logger
from recollweb.search import RecollSearchEngine, extract_document_file


class ArchiveManager:
    """
    Thread-safe manager for asynchronous ZIP packaging of matching search files.
    """

    _jobs: Dict[str, Dict[str, Any]] = {}
    _lock = threading.Lock()

    @classmethod
    def create_job(cls, total: int) -> str:
        """
        Register a new archiving job and allocate target zip file path in EXPORT_DIR.
        """
        job_id = uuid.uuid4().hex[:12]
        now_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_{now_ts}.zip"
        zip_path = os.path.join(EXPORT_DIR, filename)

        counter = 1
        while os.path.exists(zip_path):
            filename = f"search_{now_ts}_{counter}.zip"
            zip_path = os.path.join(EXPORT_DIR, filename)
            counter += 1

        with cls._lock:
            # Clean up old jobs older than 1 hour (3600 seconds)
            curr_time = time.time()
            expired = [k for k, v in cls._jobs.items() if curr_time - v.get('created_at', 0) > 3600]
            for k in expired:
                cls._jobs.pop(k, None)

            cls._jobs[job_id] = {
                'id': job_id,
                'status': 'zipping',
                'processed': 0,
                'total': total,
                'current_file': '',
                'filename': filename,
                'zip_path': zip_path,
                'download_url': f"/api/archive/download/{job_id}",
                'error': None,
                'cancelled': False,
                'created_at': curr_time,
            }
        return job_id

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve state dictionary for the given job ID.
        """
        with cls._lock:
            return cls._jobs.get(job_id)

    @classmethod
    def cancel_job(cls, job_id: str):
        """
        Mark the job as cancelled.
        """
        with cls._lock:
            job = cls._jobs.get(job_id)
            if job:
                job['cancelled'] = True
                job['status'] = 'cancelled'

    @classmethod
    def update_job(cls, job_id: str, **kwargs):
        """
        Update fields in the job state dictionary.
        """
        with cls._lock:
            job = cls._jobs.get(job_id)
            if job:
                job.update(kwargs)


def _run_archive_worker(job_id: str, query_data: Dict[str, Any], config: Dict[str, Any]):
    """
    Background worker function executed in a separate thread.
    Fetches each matching document, extracts its content, and writes it into a ZIP archive.
    """
    job = ArchiveManager.get_job(job_id)
    if not job:
        return

    zip_path = job['zip_path']
    used_names = set()

    try:
        query_obj, _ = RecollSearchEngine._init_query(query_data, config)
        total_docs = query_obj.rowcount

        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            for i in range(total_docs):
                current_job = ArchiveManager.get_job(job_id)
                if not current_job or current_job.get('cancelled'):
                    break

                try:
                    doc = query_obj.fetchone()
                except Exception as exc:
                    logger.warning("ARCHIVE: fetchone error at doc #%d: %s", i, exc)
                    break

                if not doc:
                    break

                extracted_path, fname, is_temp = extract_document_file(doc)

                if extracted_path and os.path.isfile(extracted_path):
                    if not fname:
                        fname = f"document_{i+1}"

                    # Deduplicate filename if multiple files in the search results have the same name
                    arcname = fname
                    counter = 1
                    name_part, ext_part = os.path.splitext(fname)
                    while arcname in used_names:
                        arcname = f"{name_part} ({counter}){ext_part}"
                        counter += 1
                    used_names.add(arcname)

                    try:
                        zip_file.write(extracted_path, arcname=arcname)
                    except Exception as exc:
                        logger.warning("ARCHIVE: failed to write %s to zip: %s", arcname, exc)

                    if is_temp:
                        try:
                            os.unlink(extracted_path)
                        except Exception:
                            pass

                ArchiveManager.update_job(job_id, processed=i + 1, current_file=fname or f"file_{i+1}")

        final_job = ArchiveManager.get_job(job_id)
        if final_job and not final_job.get('cancelled'):
            ArchiveManager.update_job(job_id, status='ready', processed=final_job['total'])
            logger.info("ARCHIVE_READY: %s created with %d files", zip_path, len(used_names))
        elif final_job and final_job.get('cancelled'):
            try:
                if os.path.isfile(zip_path):
                    os.unlink(zip_path)
            except Exception:
                pass
    except Exception as exc:
        logger.error("ARCHIVE_ERROR: job %s failed: %s", job_id, exc)
        ArchiveManager.update_job(job_id, status='error', error=str(exc))
        try:
            if os.path.isfile(zip_path):
                os.unlink(zip_path)
        except Exception:
            pass
