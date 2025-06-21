"""Tests for the rb CLI."""

import json
import os
import socket
import subprocess
import tempfile
import time
from contextlib import closing

import pytest
import requests
from click.testing import CliRunner

from rb import cli


def find_free_port():
    """Find and return an available port."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def datasette_instance():
    """
    Starts a Datasette instance in a subprocess for testing.
    The instance is configured with a root token and permissions
    to allow all write operations.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        open(db_path, "a").close()  # Create the database file
        port = find_free_port()
        base_url = f"http://127.0.0.1:{port}"
        token = "test-token"

        metadata = {
            "plugins": {
                "datasette-auth-tokens": {
                    "tokens": [{"token": token, "actor": {"id": "root"}}]
                }
            },
            "permissions": {
                "create-table": {"id": "root"},
                "insert-row": {"id": "root"},
                "update-row": {"id": "root"},
                "delete-row": {"id": "root"},
                "drop-table": {"id": "root"},
            },
        }
        metadata_path = os.path.join(tmpdir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        process = subprocess.Popen(
            [
                "uv",
                "run",
                "--with",
                "datasette-auth-tokens",
                "datasette",
                "serve",
                db_path,
                "--port",
                str(port),
                "--metadata",
                metadata_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for the server to start
        for _ in range(10):
            try:
                response = requests.get(base_url)
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            process.terminate()
            stdout, stderr = process.communicate()
            pytest.fail(
                f"Datasette server failed to start.\\n"
                f"STDOUT: {stdout.decode()}\\n"
                f"STDERR: {stderr.decode()}"
            )

        yield {"base_url": base_url, "token": token, "db_name": "test"}

        process.terminate()
        process.wait()


def test_create_insert_and_verify(datasette_instance):
    """
    Tests creating a table, inserting a row, and verifying the data
    using the datasette CLI commands.
    """
    runner = CliRunner()
    token = datasette_instance["token"]
    base_url = datasette_instance["base_url"]
    db_name = datasette_instance["db_name"]

    # Set the auth token as an environment variable for the CLI
    os.environ["DATASETTE_AUTH_TOKEN"] = token

    # 1. Create a table
    table_payload = {
        "table": "people",
        "columns": [
            {"name": "name", "type": "text"},
            {"name": "age", "type": "integer"},
        ],
        "pk": "name",
    }
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump(table_payload, f)
        payload_path = f.name

    result = runner.invoke(
        cli,
        [
            "datasette",
            "create-table",
            "--database",
            db_name,
            "--payload-file",
            payload_path,
            "--base-url",
            base_url,
        ],
    )
    assert result.exit_code == 0, result.output
    assert '"ok": true' in result.output
    os.remove(payload_path)

    # 2. Insert a row and test the --return flag
    insert_payload = {"rows": [{"name": "Cleo", "age": 5}]}
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump(insert_payload, f)
        payload_path = f.name

    result = runner.invoke(
        cli,
        [
            "datasette",
            "insert-rows",
            "--database",
            db_name,
            "--table",
            "people",
            "--payload-file",
            payload_path,
            "--base-url",
            base_url,
            "--return",
        ],
    )
    assert result.exit_code == 0, result.output
    os.remove(payload_path)

    # Verify the output from the --return flag
    returned_data = json.loads(result.output)
    assert returned_data["ok"] is True
    assert returned_data["rows"] == [{"name": "Cleo", "age": 5}]

    # 3. Verify the data with a direct API call
    response = requests.get(f"{base_url}/{db_name}/people.json?_shape=object")
    assert response.status_code == 200
    data = response.json()
    assert data["Cleo"] == {"name": "Cleo", "age": 5}

    del os.environ["DATASETTE_AUTH_TOKEN"]
