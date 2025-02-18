#!/usr/bin/env -S uv run --script
import json
import re

import click
import os
from typing import Optional
import tempfile
import subprocess


@click.group()
def cli():
    """Repository benchmarking tool to analyze and compare code repositories."""


@cli.command()
@click.argument("repo_path")
def survey(repo_path: str):
    """Add a new repository to the benchmark database.

    REPO_PATH can be a GitHub URL or local path
    """
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
@click.argument("repo_name")
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
@click.argument("repo_path")
def extract_links(repo_path: str):
    """Extract all links from the repository's README file.

    REPO_PATH can be a GitHub URL or local path
    """
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
@click.argument("json_path")
@click.option("--db", default="github.db", help="Path to SQLite database")
def process_links(json_path: str, db: str):
    """Process a JSON file containing GitHub repository links.

    JSON_PATH should point to a file containing a list of GitHub URLs.
    Each URL will be processed using github-to-sqlite.
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
