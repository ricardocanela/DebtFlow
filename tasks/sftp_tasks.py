"""Celery tasks for SFTP polling and file import."""
import logging
import os

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sftp_poll_all_agencies(self):
    """Poll SFTP servers for all agencies with SFTP config.

    Runs every 15 minutes via Celery Beat.
    For each agency: connects, lists new files, downloads, and triggers import.
    """
    from apps.accounts.models import Agency

    agencies = Agency.objects.filter(is_active=True)
    results = []

    for agency in agencies:
        sftp_config = agency.settings.get("sftp", {})
        if not sftp_config.get("enabled", False):
            continue

        try:
            result = _poll_agency(agency, sftp_config)
            results.append({"agency": str(agency.id), "files": result})
        except Exception as e:
            logger.exception("SFTP poll failed for agency %s", agency.name)
            results.append({"agency": str(agency.id), "error": str(e)})

    return {"polled": len(results), "results": results}


def _poll_agency(agency, sftp_config: dict) -> list[str]:
    """Poll a single agency's SFTP server."""
    from apps.integrations.sftp_client import SFTPClient

    host = sftp_config.get("host", settings.SFTP_HOST)
    port = sftp_config.get("port", settings.SFTP_PORT)
    username = sftp_config.get("username", settings.SFTP_USER)
    password = sftp_config.get("password", settings.SFTP_PASSWORD)
    remote_dir = sftp_config.get("remote_dir", settings.SFTP_REMOTE_DIR)

    processed_files = []
    processed_dir = sftp_config.get("processed_dir", f"{remote_dir}/processed")

    with SFTPClient(host=host, port=port, username=username, password=password) as client:
        files = client.list_files(remote_dir)
        for file_name in files:
            remote_path = f"{remote_dir}/{file_name}"
            local_path = client.download_file(remote_path)
            process_import_file.delay(str(agency.id), local_path, file_name, host)
            # Move processed file to avoid re-processing
            try:
                client.move_file(remote_path, f"{processed_dir}/{file_name}")
            except Exception:
                logger.warning("Could not move %s to processed dir", remote_path)
            processed_files.append(file_name)

    return processed_files


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def process_import_file(self, agency_id: str, file_path: str, file_name: str, source_host: str):
    """Process a single downloaded SFTP file."""
    from apps.accounts.models import Agency
    from apps.integrations.importers import BatchImporter
    from apps.integrations.models import SFTPImportJob

    try:
        agency = Agency.objects.get(id=agency_id)
    except Agency.DoesNotExist:
        logger.error("Agency %s not found", agency_id)
        return

    import_job = SFTPImportJob.objects.create(
        agency=agency,
        source_host=source_host,
        file_name=file_name,
    )

    try:
        importer = BatchImporter(agency, import_job)
        importer.import_file(file_path)
    except Exception as e:
        import_job.status = SFTPImportJob.Status.FAILED
        import_job.error_details.append({"line": 0, "error": f"Fatal: {e}"})
        import_job.save()
        logger.exception("Import job %s failed", import_job.id)
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.unlink(file_path)
