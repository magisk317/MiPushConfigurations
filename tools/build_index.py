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
    return git("log", "-1", "--format=%cI", "--", path)


def iter_config_files() -> list[ConfigFile]:
    files: list[ConfigFile] = []
    for file in sorted(REPO_ROOT.glob("*.json")):
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
                path=file.name,
                name=file.stem,
                sha=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                size=len(content),
                updated_at=get_last_updated_at(file.name),
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
