"""Tests for SFTP client wrapper."""
import os
from unittest.mock import MagicMock, patch

import pytest

from apps.integrations.sftp_client import SFTPClient


class TestSFTPClient:
    def test_init_with_explicit_params(self):
        client = SFTPClient(host="sftp.example.com", port=2222, username="user", password="pass")
        assert client.host == "sftp.example.com"
        assert client.port == 2222
        assert client.username == "user"
        assert client.password == "pass"

    @patch("apps.integrations.sftp_client.paramiko")
    def test_connect_creates_transport(self, mock_paramiko):
        mock_transport = MagicMock()
        mock_paramiko.Transport.return_value = mock_transport
        mock_paramiko.SFTPClient.from_transport.return_value = MagicMock()

        client = SFTPClient(host="localhost", port=22, username="user", password="pass")
        client.connect()

        mock_paramiko.Transport.assert_called_once_with(("localhost", 22))
        mock_transport.connect.assert_called_once_with(username="user", password="pass")
        mock_paramiko.SFTPClient.from_transport.assert_called_once_with(mock_transport)

    @patch("apps.integrations.sftp_client.paramiko")
    def test_disconnect_closes_connections(self, mock_paramiko):
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_paramiko.Transport.return_value = mock_transport
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        client = SFTPClient(host="localhost", port=22, username="user", password="pass")
        client.connect()
        client.disconnect()

        mock_sftp.close.assert_called_once()
        mock_transport.close.assert_called_once()

    @patch("apps.integrations.sftp_client.paramiko")
    def test_context_manager(self, mock_paramiko):
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_paramiko.Transport.return_value = mock_transport
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with SFTPClient(host="localhost", port=22, username="user", password="pass") as client:
            assert client._sftp is not None

        mock_sftp.close.assert_called_once()
        mock_transport.close.assert_called_once()

    @patch("apps.integrations.sftp_client.paramiko")
    def test_list_files_returns_csv_only(self, mock_paramiko):
        mock_sftp = MagicMock()
        mock_sftp.listdir.return_value = ["data.csv", "readme.txt", "import.csv", "photo.jpg"]
        mock_paramiko.Transport.return_value = MagicMock()
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with SFTPClient(host="localhost", port=22, username="user", password="pass") as client:
            files = client.list_files("/upload")

        assert files == ["data.csv", "import.csv"]

    @patch("apps.integrations.sftp_client.paramiko")
    def test_list_files_empty_dir(self, mock_paramiko):
        mock_sftp = MagicMock()
        mock_sftp.listdir.return_value = []
        mock_paramiko.Transport.return_value = MagicMock()
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with SFTPClient(host="localhost", port=22, username="user", password="pass") as client:
            files = client.list_files("/empty")

        assert files == []

    @patch("apps.integrations.sftp_client.paramiko")
    def test_list_files_dir_not_found(self, mock_paramiko):
        mock_sftp = MagicMock()
        mock_sftp.listdir.side_effect = FileNotFoundError
        mock_paramiko.Transport.return_value = MagicMock()
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with SFTPClient(host="localhost", port=22, username="user", password="pass") as client:
            files = client.list_files("/nonexistent")

        assert files == []

    @patch("apps.integrations.sftp_client.paramiko")
    def test_download_file(self, mock_paramiko):
        mock_sftp = MagicMock()
        mock_paramiko.Transport.return_value = MagicMock()
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with SFTPClient(host="localhost", port=22, username="user", password="pass") as client:
            local_path = client.download_file("/upload/test.csv")

        assert local_path.endswith("test.csv")
        mock_sftp.get.assert_called_once()

    @patch("apps.integrations.sftp_client.paramiko")
    def test_move_file_creates_dest_dir(self, mock_paramiko):
        mock_sftp = MagicMock()
        mock_sftp.stat.side_effect = FileNotFoundError
        mock_paramiko.Transport.return_value = MagicMock()
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        with SFTPClient(host="localhost", port=22, username="user", password="pass") as client:
            client.move_file("/upload/test.csv", "/upload/processed/test.csv")

        mock_sftp.mkdir.assert_called_once_with("/upload/processed")
        mock_sftp.rename.assert_called_once_with("/upload/test.csv", "/upload/processed/test.csv")
