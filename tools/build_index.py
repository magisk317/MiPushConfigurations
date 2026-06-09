#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
META_DIR = REPO_ROOT / "_meta"
OUTPUT_PATH = META_DIR / "config-index.json"
SOURCE_REPO = "magisk317/MiPushConfigurations"
INDEXED_SUBDIRS = ("icon",)


@dataclass(frozen=True)
class ConfigFile:
    path: str
    name: str
    sha: str
    size: int
    updated_at: str


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_current_branch() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD")


def get_last_updated_at(path: str) -> str:
    updated_at = git("log", "-1", "--format=%cI", "--", path)
    return updated_at or datetime.fromtimestamp((REPO_ROOT / path).stat().st_mtime, timezone.utc).isoformat()


def iter_json_paths() -> list[Path]:
    files = list(REPO_ROOT.glob("*.json"))
    for directory_name in INDEXED_SUBDIRS:
        directory = REPO_ROOT / directory_name
        if directory.is_dir():
            files.extend(directory.glob("*.json"))
    return sorted(files, key=lambda file: file.relative_to(REPO_ROOT).as_posix())


def iter_config_files() -> list[ConfigFile]:
    files: list[ConfigFile] = []
    for file in iter_json_paths():
        relative_path = file.relative_to(REPO_ROOT).as_posix()
        raw_text = file.read_text(encoding="utf-8-sig")
        canonical = json.dumps(
            json.loads(raw_text),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        content = raw_text.encode("utf-8")
        files.append(
            ConfigFile(
                path=relative_path,
                name=relative_path.removesuffix(".json"),
                sha=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                size=len(content),
                updated_at=get_last_updated_at(relative_path),
            )
        )
    return files


def build_index() -> dict:
    return {
        "sourceRepo": SOURCE_REPO,
        "branch": get_current_branch(),
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "files": [
            {
                "path": item.path,
                "name": item.name,
                "sha": item.sha,
                "size": item.size,
                "updatedAt": item.updated_at,
            }
            for item in iter_config_files()
        ],
    }


def main() -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(build_index(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
