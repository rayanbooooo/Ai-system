"""Updates vault/Accounts/*.md frontmatter (drawdown/loss/day-count state)
in place, without disturbing the rest of the note's body.
"""
from __future__ import annotations

from pathlib import Path

import yaml

_FRONTMATTER_DELIM = "---"


def update_frontmatter(path: Path, updates: dict) -> None:
    text = path.read_text(encoding="utf-8")
    parts = text.split(_FRONTMATTER_DELIM, 2)
    if len(parts) < 3:
        raise ValueError(f"{path} has no YAML frontmatter block to update")

    frontmatter = yaml.safe_load(parts[1]) or {}
    frontmatter.update(updates)
    new_frontmatter = yaml.safe_dump(frontmatter, sort_keys=False).strip()

    new_text = f"{_FRONTMATTER_DELIM}\n{new_frontmatter}\n{_FRONTMATTER_DELIM}{parts[2]}"
    path.write_text(new_text, encoding="utf-8")


def account_note_path(vault_path: Path, account_id: str) -> Path:
    return vault_path / "Accounts" / f"{account_id}.md"
