import json
import os
import re
import subprocess
import tempfile
from typing import Optional

import click
import requests


@click.group()
def cli():
    """Repository benchmarking tool to analyze and compare code repositories."""


@cli.group()
def datasette():
    """Datasette management commands."""
    pass


@datasette.command()
@click.option(
    "--username",
    help="The username to create the token for.",
    default=os.getenv("DATASETTE_USERNAME"),
)
@click.option(
    "--secret",
    help="The secret to use for the token.",
    default=os.getenv("DATASETTE_SECRET"),
)
def get_auth_token(username: str, secret: str):
    """Get the Datasette auth token."""
    result = subprocess.run(
        ["uv", "run", "datasette", "create-token", username, "--secret", secret],
        check=True,
    )
    click.echo(result.stdout)


def datasette_post(url: str, token: str, payload: dict):
    """Helper function to make POST requests to Datasette."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        error_message = f"Error: {e.response.status_code} {e.response.reason}"
        try:
            error_details = e.response.json()
            if "errors" in error_details:
                error_message += "\\n" + "\\n".join(error_details["errors"])
        except json.JSONDecodeError:
            pass
        raise click.ClickException(error_message) from e
    except requests.exceptions.RequestException as e:
        raise click.ClickException(f"Request failed: {e}") from e


@datasette.command(name="insert-rows")
@click.option("--database", required=True, help="Name of the database.")
@click.option("--table", required=True, help="Name of the table.")
@click.option(
    "--payload-file",
    "payload_file",
    required=True,
    type=click.File("r"),
    help="Path to the JSON payload file.",
)
@click.option(
    "--base-url",
    default=os.getenv("DATASETTE_ENDPOINT", "http://127.0.0.1:8001"),
    help="Datasette base URL",
)
@click.option("--return", "return_flag", is_flag=True, help="Return the inserted rows.")
def insert_rows(
    database: str, table: str, payload_file, base_url: str, return_flag: bool
):
    """Insert rows into a table from a JSON file.

    PAYLOAD_FILE: Path to a JSON file containing an object with a "rows" key,
    which is a list of objects to insert.

    Example:
    {
        "rows": [
            {"text_column": "A text string", "integer_column": 1},
            {"text_column": "Another string", "integer_column": 2}
        ]
    }

    See: https://docs.datasette.io/en/latest/json_api.html#inserting-rows
    """
    token = os.getenv("DATASETTE_AUTH_TOKEN")
    if not token:
        raise click.ClickException("DATASETTE_AUTH_TOKEN environment variable not set")
    url = f"{base_url}/{database}/{table}/-/insert"
    try:
        payload = json.load(payload_file)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in payload file: {e}") from e
    if return_flag:
        payload["return"] = True
    datasette_post(url, token, payload)


@datasette.command(name="upsert-rows")
@click.option("--database", required=True, help="Name of the database.")
@click.option("--table", required=True, help="Name of the table.")
@click.option(
    "--payload-file",
    "payload_file",
    required=True,
    type=click.File("r"),
    help="Path to the JSON payload file.",
)
@click.option(
    "--base-url",
    default=os.getenv("DATASETTE_ENDPOINT", "http://127.0.0.1:8001"),
    help="Datasette base URL",
)
@click.option("--return", "return_flag", is_flag=True, help="Return the upserted rows.")
def upsert_rows(
    database: str, table: str, payload_file, base_url: str, return_flag: bool
):
    """Upsert rows into a table from a JSON file.

    PAYLOAD_FILE: Path to a JSON file for upserting rows. Must include "rows"
    and "pk" keys.

    Example:
    {
        "rows": [
            {"id": 1, "name": "Updated name for row 1"},
            {"id": 3, "name": "A new row"}
        ],
        "pk": "id"
    }

    See: https://docs.datasette.io/en/latest/json_api.html#upserting-rows
    """
    token = os.getenv("DATASETTE_AUTH_TOKEN")
    if not token:
        raise click.ClickException("DATASETTE_AUTH_TOKEN environment variable not set")
    url = f"{base_url}/{database}/{table}/-/upsert"
    try:
        payload = json.load(payload_file)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in payload file: {e}") from e
    if return_flag:
        payload["return"] = True
    datasette_post(url, token, payload)


@datasette.command(name="update-row")
@click.option("--database", required=True, help="Name of the database.")
@click.option("--table", required=True, help="Name of the table.")
@click.option("--pks", required=True, help="Primary key(s) of the row to update.")
@click.option(
    "--payload-file",
    "payload_file",
    required=True,
    type=click.File("r"),
    help="Path to the JSON payload file.",
)
@click.option(
    "--base-url",
    default=os.getenv("DATASETTE_ENDPOINT", "http://127.0.0.1:8001"),
    help="Datasette base URL",
)
@click.option("--return", "return_flag", is_flag=True, help="Return the updated row.")
def update_row(
    database: str, table: str, pks: str, payload_file, base_url: str, return_flag: bool
):
    """Update a row in a table.

    PKS: The primary key of the row to update.
    PAYLOAD_FILE: Path to a JSON file with an "update" key containing the
    columns and values to update.

    Example:
    {
        "update": {
            "text_column": "New text string",
            "integer_column": 3
        }
    }

    See: https://docs.datasette.io/en/latest/json_api.html#updating-a-row
    """
    token = os.getenv("DATASETTE_AUTH_TOKEN")
    if not token:
        raise click.ClickException("DATASETTE_AUTH_TOKEN environment variable not set")
    url = f"{base_url}/{database}/{table}/{pks}/-/update"
    try:
        payload = json.load(payload_file)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in payload file: {e}") from e
    if return_flag:
        payload["return"] = True
    datasette_post(url, token, payload)


@datasette.command(name="delete-row")
@click.option("--database", required=True, help="Name of the database.")
@click.option("--table", required=True, help="Name of the table.")
@click.option("--pks", required=True, help="Primary key(s) of the row to delete.")
@click.option(
    "--base-url",
    default=os.getenv("DATASETTE_ENDPOINT", "http://127.0.0.1:8001"),
    help="Datasette base URL",
)
def delete_row(database: str, table: str, pks: str, base_url: str):
    """Delete a row from a table."""
    token = os.getenv("DATASETTE_AUTH_TOKEN")
    if not token:
        raise click.ClickException("DATASETTE_AUTH_TOKEN environment variable not set")
    url = f"{base_url}/{database}/{table}/{pks}/-/delete"
    datasette_post(url, token, {})


@datasette.command(name="create-table")
@click.option("--database", required=True, help="Name of the database.")
@click.option(
    "--payload-file",
    "payload_file",
    required=True,
    type=click.File("r"),
    help="Path to the JSON payload file.",
)
@click.option(
    "--base-url",
    default=os.getenv("DATASETTE_ENDPOINT", "http://127.0.0.1:8001"),
    help="Datasette base URL",
)
def create_table(database: str, payload_file, base_url: str):
    """Create a table.

    PAYLOAD_FILE: Path to a JSON file describing the table to create.
    It should contain "table", and either "columns" or "rows".

    Example with columns:
    {
        "table": "name_of_new_table",
        "columns": [
            {"name": "id", "type": "integer"},
            {"name": "title", "type": "text"}
        ],
        "pk": "id"
    }

    Example with rows:
    {
        "table": "creatures",
        "rows": [
            {"id": 1, "name": "Tarantula"},
            {"id": 2, "name": "Kākāpō"}
        ],
        "pk": "id"
    }

    See: https://docs.datasette.io/en/latest/json_api.html#creating-a-table
    """
    token = os.getenv("DATASETTE_AUTH_TOKEN")
    if not token:
        raise click.ClickException("DATASETTE_AUTH_TOKEN environment variable not set")
    url = f"{base_url}/{database}/-/create"
    try:
        payload = json.load(payload_file)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in payload file: {e}") from e
    datasette_post(url, token, payload)


@datasette.command(name="drop-table")
@click.option("--database", required=True, help="Name of the database.")
@click.option("--table", required=True, help="Name of the table.")
@click.option("--confirm", is_flag=True, help="Confirm dropping the table.")
@click.option(
    "--base-url",
    default=os.getenv("DATASETTE_ENDPOINT", "http://127.0.0.1:8001"),
    help="Datasette base URL",
)
def drop_table(database: str, table: str, confirm: bool, base_url: str):
    """Drop a table.

    Use the --confirm flag to finalize the deletion.
    """
    token = os.getenv("DATASETTE_AUTH_TOKEN")
    if not token:
        raise click.ClickException("DATASETTE_AUTH_TOKEN environment variable not set")
    url = f"{base_url}/{database}/{table}/-/drop"
    payload = {}
    if confirm:
        payload["confirm"] = True
    datasette_post(url, token, payload)


@cli.command()
@click.option(
    "--repo-path",
    required=True,
    help="Add a new repository to the benchmark database. REPO_PATH can be a GitHub URL or local path",
)
def survey(repo_path: str):
    """Survey a repository."""
    if repo_path.startswith("http"):
        click.echo(f"Surveying remote repository: {repo_path}")
        with tempfile.TemporaryDirectory(prefix="tmp_repo_") as tmp_dir:
            try:
                click.echo(f"Cloning repository to {tmp_dir}...")
                subprocess.run(
                    ["git", "clone", "--depth=1", repo_path, tmp_dir],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                click.echo("Repository cloned successfully")
                # TODO: Analyze the cloned repository
            except subprocess.CalledProcessError as e:
                raise click.ClickException(f"Failed to clone repository: {e.stderr}")
    else:
        if not os.path.exists(repo_path):
            raise click.BadParameter(f"Local path does not exist: {repo_path}")

    # Now we'll pipe this into llm and simon's github plugin.
    click.secho(f"Surveying repository: {repo_path}")
    # TODO: Implement local repo analysis


@cli.command()
@click.option("--filter", help="Filter repositories by keyword")
def list_repos(filter_term: Optional[str]):
    """List all repositories in the benchmark database."""
    click.echo("Listing repositories...")
    if filter_term:
        click.echo(f"Applying filter: {filter_term}")
    # TODO: Implement repository listing logic


@cli.command()
@click.option("--repo-name", required=True, help="Name of the repository to inspect.")
@click.option("--stats", is_flag=True, help="Show detailed statistics")
@click.option("--embeddings", is_flag=True, help="Show repository embeddings")
def inspect(repo_name: str, stats: bool, embeddings: bool):
    """View detailed information about a specific repository."""
    click.echo(f"Inspecting repository: {repo_name}")

    if stats:
        click.echo("Showing detailed statistics:")
        # TODO: Implement statistics display
        click.echo("- Code quality metrics")
        click.echo("- Documentation coverage")
        click.echo("- Test coverage")
        click.echo("- Dependency health")

    if embeddings:
        click.echo("Showing repository embeddings:")
        # TODO: Implement embeddings display


@cli.command()
@click.option(
    "--repo-path",
    required=True,
    help="Path to the repository to extract links from. Can be a GitHub URL or local path",
)
def extract_links(repo_path: str):
    """Extract all links from the repository's README file."""
    if repo_path.startswith("http"):
        with tempfile.TemporaryDirectory(prefix="tmp_repo_") as tmp_dir:
            subprocess.run(
                ["git", "clone", "--depth=1", repo_path, tmp_dir],
                check=True,
                capture_output=True,
                text=True,
            )
            links = parse_repo(tmp_dir)
    else:
        if not os.path.exists(repo_path):
            raise click.BadParameter(f"Local path does not exist: {repo_path}")
        links = parse_repo(repo_path)

    click.secho(json.dumps(links, indent=2))


def parse_repo(repo_path: str) -> list[str]:
    """Parse a repository and extract all links from its README file.

    Args:
        repo_path: Path to the local repository

    Returns:
        List of unique URLs found in the README

    Raises:
        click.ClickException: If no README is found
    """
    readme_path = find_readme(repo_path)
    if not readme_path:
        raise click.ClickException("No README file found in the repository")

    return extract_links_from_readme(readme_path)


def find_readme(repo_path: str) -> Optional[str]:
    """Find the README file in the repository."""
    readme_variants = ["README.md", "README.MD", "Readme.md", "readme.md"]
    for variant in readme_variants:
        path = os.path.join(repo_path, variant)
        if os.path.exists(path):
            return path
    return None


def extract_links_from_readme(readme_path: str) -> list[str]:
    """Extract all markdown and regular URLs from the README file."""

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Only include github.com URLs that follow the pattern username/repo without additional paths
    # example repo: https://github.com/skydoves/landscapist
    repo_pattern = r"https:\/\/github\.com\/[^\/]+\/[^\/\s\n)]+"
    links = []

    # Extract bare URLs from the cleaned content
    bare_urls = re.findall(repo_pattern, content)
    links.extend(url.rstrip("/") for url in bare_urls)

    return list(set(links))  # Remove duplicates


@cli.command()
@click.option(
    "--json-path",
    required=True,
    help="Path to a JSON file containing GitHub repository links.",
)
@click.option("--db", default="github.db", help="Path to SQLite database")
def process_links(json_path: str, db: str):
    """Process a JSON file containing GitHub repository links.

    Each URL will be processed using github-to-sqlite and have it's result
    written to the SQLite database.

    """
    if not os.path.exists(json_path):
        raise click.BadParameter(f"JSON file does not exist: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            links = json.load(f)
    except json.JSONDecodeError as exc:
        raise click.ClickException("Invalid JSON file") from exc

    if not isinstance(links, list):
        raise click.ClickException("JSON file must contain a list of URLs")

    repo_pattern = r"github\.com\/([^/]+/[^/]+)"

    for link in links:
        match = re.search(repo_pattern, link)
        if match:
            repo = match.group(1)
            # Remove any trailing parts like /tree/main or .git
            repo = repo.split("/tree/")[0].split(".git")[0]

            click.echo(f"Processing: {repo}")
            try:
                subprocess.run(
                    ["uv", "run", "github-to-sqlite", "repos", db, "-r", repo],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                click.echo(f"✓ Processed: {repo}")
            except subprocess.CalledProcessError as e:
                click.echo(f"✗ Error processing {repo}: {e.stderr}", err=True)


if __name__ == "__main__":
    cli()
