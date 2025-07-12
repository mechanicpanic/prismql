#!/usr/bin/env python3
"""Version bumping script for PrismQL."""

import argparse
import re
import sys
from pathlib import Path


def bump_version(version_str, bump_type):
    """Bump version number."""
    major, minor, patch = map(int, version_str.split("."))

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def update_pyproject_toml(new_version):
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Update version line
    pattern = r'version = "[^"]+"'
    replacement = f'version = "{new_version}"'
    new_content = re.sub(pattern, replacement, content)

    pyproject_path.write_text(new_content)
    print(f"Updated pyproject.toml to version {new_version}")


def main():
    parser = argparse.ArgumentParser(description="Bump PrismQL version")
    parser.add_argument(
        "bump_type", choices=["major", "minor", "patch"], help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    args = parser.parse_args()

    # Read current version
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)

    content = pyproject_path.read_text()
    version_match = re.search(r'version = "([^"]+)"', content)
    if not version_match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)

    current_version = version_match.group(1)
    new_version = bump_version(current_version, args.bump_type)

    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")

    if args.dry_run:
        print("Dry run - no changes made")
        return

    update_pyproject_toml(new_version)
    print(f"Version bumped from {current_version} to {new_version}")


if __name__ == "__main__":
    main()
