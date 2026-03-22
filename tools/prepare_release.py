#!/usr/bin/env python3
"""Bump the project version and print release steps.

This helper updates the version in ``pyproject.toml`` and shows the exact git
and verification commands to run next. By default it prompts for the bump type,
but you can also pass ``--bump`` non-interactively.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


VERSION_RE = re.compile(r'^(version\s*=\s*")(?P<version>\d+\.\d+\.\d+)("\s*)$')


def parse_version(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def bump_version(version: str, bump: str) -> str:
    major, minor, patch = parse_version(version)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump type: {bump}")


def choose_bump() -> str:
    print("Select release type:")
    print("  1) patch  - docs, packaging, CI, small fixes")
    print("  2) minor  - new capabilities or meaningful feature additions")
    print("  3) major  - breaking public API/CLI changes")
    while True:
        choice = input("Enter 1, 2, or 3: ").strip()
        mapping = {"1": "patch", "2": "minor", "3": "major"}
        if choice in mapping:
            return mapping[choice]
        print("Invalid selection. Please enter 1, 2, or 3.")


def update_pyproject(pyproject_path: Path, new_version: str) -> str:
    lines = pyproject_path.read_text().splitlines()
    current_version = None
    updated_lines: list[str] = []

    for line in lines:
        match = VERSION_RE.match(line)
        if match and current_version is None:
            current_version = match.group("version")
            updated_lines.append(f'version = "{new_version}"')
        else:
            updated_lines.append(line)

    if current_version is None:
        raise RuntimeError("Could not find version line in pyproject.toml")

    pyproject_path.write_text("\n".join(updated_lines) + "\n")
    return current_version


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare the next release version")
    parser.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        help="Release bump type. If omitted, prompt interactively.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "pyproject.toml",
        help="Path to pyproject.toml",
    )
    args = parser.parse_args()

    pyproject_path = args.path.resolve()
    bump = args.bump or choose_bump()

    text = pyproject_path.read_text().splitlines()
    current_version = None
    for line in text:
        match = VERSION_RE.match(line)
        if match:
            current_version = match.group("version")
            break

    if current_version is None:
        raise SystemExit("Could not determine current version from pyproject.toml")

    new_version = bump_version(current_version, bump)
    previous_version = update_pyproject(pyproject_path, new_version)

    print(f"Updated version: {previous_version} -> {new_version}")
    print()
    print("Next steps:")
    print("  ruff check presonus cli")
    print("  python3 -m pytest tests/ -q")
    print("  python3 -m build")
    print("  git add pyproject.toml")
    print(f"  git commit -m \"release: prepare v{new_version}\"")
    print("  git push origin main")
    print(f"  git tag v{new_version}")
    print(f"  git push origin v{new_version}")


if __name__ == "__main__":
    main()
