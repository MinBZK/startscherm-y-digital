#!/usr/bin/env python3

import os
import sys
import subprocess
from webdav3.client import Client
from pathlib import Path

nextcloud_user = subprocess.run(['pass', 'show', 'y/bsw-passwords/nextcloud/NC_ADMIN_USER'], capture_output=True, text=True).stdout.strip()
nextcloud_password = subprocess.run(['pass', 'show', 'y/bsw-passwords/nextcloud/NC_ADMIN_PASSWORD'], capture_output=True, text=True).stdout.strip()

DOSSIERS_PATH = Path(__file__).parent / "dossiers"
OPTIONS = {
    "webdav_hostname": "http://nextcloud.localhost:8080/remote.php/dav/files/admin/",
    "webdav_login": nextcloud_user,
    "webdav_password": nextcloud_password
}


class NextcloudDossierUploader():
    """Class for uploading dossiers to Nextcloud."""

    def __init__(self):
        self.client = Client(OPTIONS)


    def upload_dossiers(self):
        """List and upload dossiers to Nextcloud."""
        dossiers = os.listdir(DOSSIERS_PATH)
        for dossier in dossiers:
            try:
                self.upload_directory(self.client, DOSSIERS_PATH / dossier, "Dossiers/" + dossier)
                print(f"{dossier} successfully!")
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)


    def upload_directory(self, client, local_dir, remote_base):
        """Upload a dossier directory."""
        for root, dirs, files in os.walk(local_dir):
            # Compute relative path
            rel_path = os.path.relpath(root, local_dir)
            if rel_path == ".":
                remote_path = remote_base
            else:
                remote_path = os.path.join(remote_base, rel_path).replace(os.sep, "/")

            # Create directory if not exists
            if not client.check(remote_path):
                client.mkdir(remote_path)
                print(f"Created directory: {remote_path}")

            # Upload files
            for file in files:
                local_file = os.path.join(root, file)
                remote_file = os.path.join(remote_path, file).replace(os.sep, "/")
                client.upload(remote_file, local_file)
                print(f"Uploaded: {local_file} -> {remote_file}")


if __name__ == "__main__":
    nc_dossier_uploader = NextcloudDossierUploader()
    nc_dossier_uploader.upload_dossiers()
