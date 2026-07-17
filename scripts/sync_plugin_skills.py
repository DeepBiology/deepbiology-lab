#!/usr/bin/env python3
"""Mirror canonical root skills into the generated Codex plugin bundle."""

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills"
TARGET = ROOT / "codex-plugin-python" / "skills"


def _files(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def is_synchronized() -> bool:
    if not SOURCE.is_dir() or not TARGET.is_dir():
        return False
    source_files = _files(SOURCE)
    target_files = _files(TARGET)
    if source_files != target_files:
        return False
    return all(filecmp.cmp(SOURCE / path, TARGET / path, shallow=False) for path in source_files)


def synchronize() -> None:
    if not SOURCE.is_dir():
        raise SystemExit("Canonical skills directory is missing: {}".format(SOURCE))
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when the Codex copy differs")
    args = parser.parse_args()
    if args.check:
        if not is_synchronized():
            print("Codex skills are out of sync; run python scripts/sync_plugin_skills.py")
            return 1
        print("Canonical and Codex skills are synchronized.")
        return 0
    synchronize()
    print("Synchronized {} -> {}".format(SOURCE, TARGET))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
