#!/usr/bin/env python3
"""Combine monthly speech files into chunked datasets for the frontend."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

CHUNK_SIZE = 5000
LATEST_PREVIEW = 1000

PROJECT_ROOT = Path(__file__).parent.parent.parent
SPEECHES_DIR = PROJECT_ROOT / "frontend" / "public" / "data" / "speeches"

DATE_RE = re.compile(r"speeches_\d{6}01_\d{6}\.json")


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(value[:10], fmt)
        except ValueError:
            continue
    return None


def load_monthly_files() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not SPEECHES_DIR.exists():
        return records

    for file_path in sorted(SPEECHES_DIR.glob("speeches_*.json")):
        name = file_path.name
        if name in {"speeches_latest.json", "speeches_index.json", "party_aliases.json"}:
            continue
        if name.startswith("speeches_chunk_"):
            continue
        if not DATE_RE.fullmatch(name):
            continue

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            entries = data.get("data") if isinstance(data, dict) else data
            if not isinstance(entries, list):
                continue
            records.extend(entries)
        except Exception as exc:
            print(f"⚠️  {name} 読み込み失敗: {exc}")
            continue
    return records


def sort_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def sort_key(item: Dict[str, Any]):
        dt = parse_date(item.get("date"))
        # None dates go to end by using datetime.min
        dt_value = dt or datetime.min
        return (dt_value, item.get("id", ""))

    return sorted(records, key=sort_key, reverse=True)


def write_chunk_file(index: int, chunk: List[Dict[str, Any]]):
    filename = SPEECHES_DIR / f"speeches_chunk_{index:02}.json"
    start_date = next((c.get("date") for c in reversed(chunk) if c.get("date")), None)
    end_date = next((c.get("date") for c in chunk if c.get("date")), None)
    payload = {
        "metadata": {
            "data_type": "speeches_chunk",
            "chunk_number": index,
            "count": len(chunk),
            "generated_at": datetime.now().isoformat(),
            "date_range": {
                "from": start_date,
                "to": end_date,
            },
        },
        "data": chunk,
    }
    with filename.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def build_chunks(records: List[Dict[str, Any]]) -> List[str]:
    # Remove existing chunk files
    for chunk_file in SPEECHES_DIR.glob("speeches_chunk_*.json"):
        chunk_file.unlink(missing_ok=True)

    chunk_filenames: List[str] = []
    for idx in range(0, len(records), CHUNK_SIZE):
        chunk = records[idx: idx + CHUNK_SIZE]
        chunk_index = idx // CHUNK_SIZE + 1
        write_chunk_file(chunk_index, chunk)
        chunk_filenames.append(f"speeches_chunk_{chunk_index:02}.json")
    return chunk_filenames


def write_index(total_count: int, chunk_files: List[str], records: List[Dict[str, Any]]):
    first_date = next((rec.get("date") for rec in records if rec.get("date")), None)
    last_date = next((rec.get("date") for rec in reversed(records) if rec.get("date")), None)
    metadata = {
        "total_count": total_count,
        "chunk_size": CHUNK_SIZE,
        "total_chunks": len(chunk_files),
        "date_range": {
            "from": last_date,
            "to": first_date,
        },
        "generated_at": datetime.now().isoformat(),
    }
    payload = {
        "metadata": metadata,
        "chunks": [
            {
                "chunk_number": idx + 1,
                "filename": filename,
            }
            for idx, filename in enumerate(chunk_files)
        ],
        "available_files": chunk_files,
    }
    with (SPEECHES_DIR / "speeches_index.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def write_latest(records: List[Dict[str, Any]]):
    preview = records[:LATEST_PREVIEW]
    first = preview[0].get("date") if preview else None
    last = preview[-1].get("date") if preview else None
    payload = {
        "metadata": {
            "data_type": "speeches_preview",
            "total_count": len(records),
            "preview_count": len(preview),
            "generated_at": datetime.now().isoformat(),
            "date_range": {
                "from": last,
                "to": first,
            },
        },
        "data": preview,
    }
    with (SPEECHES_DIR / "speeches_latest.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    records = load_monthly_files()
    if not records:
        print("No speech records found.")
        return

    sorted_records = sort_records(records)
    chunk_files = build_chunks(sorted_records)
    write_index(len(sorted_records), chunk_files, sorted_records)
    write_latest(sorted_records)
    print(f"✅ Speeches dataset rebuilt: {len(sorted_records)} records, {len(chunk_files)} chunks")


if __name__ == "__main__":
    main()
