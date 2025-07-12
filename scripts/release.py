#!/usr/bin/env python3
"""Release script for PrismQL."""

import argparse
import subprocess
import sys


def run_command(cmd, check=True):
    """Run a shell command."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def main():
    parser = argparse.ArgumentParser(description="Release PrismQL")
    parser.add_argument("version", help="Version to release (e.g., 0.2.0)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually release")
    args = parser.parse_args()

    version = args.version
    if not version.startswith("v"):
        version = f"v{version}"

    print(f"Releasing PrismQL {version}")

    # Check we're on main branch
    result = run_command("git branch --show-current")
    if result.stdout.strip() != "main":
        print("Error: Must be on main branch to release")
        sys.exit(1)

    # Check working directory is clean
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("Error: Working directory must be clean")
        sys.exit(1)

    # Run tests
    print("Running tests...")
    run_command("uv run pytest")

    # Run linting
    print("Running linting...")
    run_command("uv run ruff format .")
    run_command("uv run ruff check .")
    run_command("uv run mypy src/prismql")

    # Build package
    print("Building package...")
    run_command("uv build")

    if args.dry_run:
        print("Dry run complete!")
        return

    # Create and push tag
    print(f"Creating tag {version}...")
    run_command(f"git tag {version}")
    run_command(f"git push origin {version}")

    print(f"Release {version} created! GitHub Actions will handle publishing.")


if __name__ == "__main__":
    main()
