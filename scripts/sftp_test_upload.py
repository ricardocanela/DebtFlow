#!/usr/bin/env python
"""Upload test CSV files to the SFTP test server for development."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import paramiko


def main():
    host = os.getenv("SFTP_HOST", "localhost")
    port = int(os.getenv("SFTP_PORT", "2222"))
    username = os.getenv("SFTP_USER", "sftpuser")
    password = os.getenv("SFTP_PASSWORD", "sftppass")
    remote_dir = os.getenv("SFTP_REMOTE_DIR", "/upload")

    # Generate test CSV
    csv_content = (
        "external_ref,debtor_name,debtor_ssn_last4,debtor_email,debtor_phone,"
        "original_amount,due_date,creditor_name,account_type\n"
    )
    for i in range(100):
        csv_content += (
            f"SFTP-{i:06d},Test Person {i},{i % 10000:04d},"
            f"person{i}@email.com,555-{i:04d},{100 + i * 10}.00,"
            f"2024-{(i % 12) + 1:02d}-15,Test Creditor,medical\n"
        )

    # Upload via SFTP
    print(f"Connecting to SFTP {host}:{port}...")
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_path = f"{remote_dir}/test_import_{os.getpid()}.csv"
    print(f"Uploading to {remote_path}...")

    with sftp.open(remote_path, "w") as f:
        f.write(csv_content)

    print(f"Uploaded {len(csv_content)} bytes with 100 test records")
    sftp.close()
    transport.close()
    print("Done!")


if __name__ == "__main__":
    main()
