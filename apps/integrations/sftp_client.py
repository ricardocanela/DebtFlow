"""Paramiko-based SFTP client wrapper."""
import logging
import os
import tempfile
from pathlib import Path

import paramiko
from django.conf import settings

logger = logging.getLogger(__name__)


class SFTPClient:
    """Manages SFTP connections for file polling and download.

    Wraps paramiko.SFTPClient with connection management,
    file listing, download, and move operations.
    """

    def __init__(self, host: str = "", port: int = 0, username: str = "", password: str = ""):
        self.host = host or settings.SFTP_HOST
        self.port = port or settings.SFTP_PORT
        self.username = username or settings.SFTP_USER
        self.password = password or settings.SFTP_PASSWORD
        self._transport = None
        self._sftp = None

    def connect(self):
        """Establish SFTP connection."""
        self._transport = paramiko.Transport((self.host, self.port))
        self._transport.connect(username=self.username, password=self.password)
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)
        logger.info("SFTP connected to %s:%d", self.host, self.port)

    def disconnect(self):
        """Close SFTP connection."""
        if self._sftp:
            self._sftp.close()
        if self._transport:
            self._transport.close()
        logger.info("SFTP disconnected from %s:%d", self.host, self.port)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def list_files(self, remote_dir: str = "") -> list[str]:
        """List CSV files in the remote directory."""
        remote_dir = remote_dir or settings.SFTP_REMOTE_DIR
        try:
            files = self._sftp.listdir(remote_dir)
            csv_files = [f for f in files if f.endswith(".csv")]
            logger.info("Found %d CSV files in %s", len(csv_files), remote_dir)
            return csv_files
        except FileNotFoundError:
            logger.warning("Remote directory %s not found", remote_dir)
            return []

    def download_file(self, remote_path: str) -> str:
        """Download a file to a temporary local path. Returns the local path."""
        local_path = os.path.join(tempfile.mkdtemp(), Path(remote_path).name)
        self._sftp.get(remote_path, local_path)
        logger.info("Downloaded %s to %s", remote_path, local_path)
        return local_path

    def move_file(self, source: str, destination: str):
        """Move a file on the remote server (rename)."""
        try:
            # Ensure destination directory exists
            dest_dir = str(Path(destination).parent)
            try:
                self._sftp.stat(dest_dir)
            except FileNotFoundError:
                self._sftp.mkdir(dest_dir)

            self._sftp.rename(source, destination)
            logger.info("Moved %s to %s", source, destination)
        except Exception:
            logger.exception("Failed to move %s to %s", source, destination)
            raise
