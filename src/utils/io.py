"""Petits helpers de lecture/ecriture JSON partages par tout le pipeline."""

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
OUTPUT_DIR = REPO_ROOT / "output"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ga4_path(market: str) -> Path:
    return DATA_RAW / f"ga4_{market.lower()}.json"


def shopify_path(market: str) -> Path:
    return DATA_RAW / f"shopify_{market.lower()}.json"


def join_path(market: str) -> Path:
    return DATA_PROCESSED / f"join_{market.lower()}.json"


def mapping_log_path(market: str) -> Path:
    return DATA_PROCESSED / f"mapping_log_{market.lower()}.json"
