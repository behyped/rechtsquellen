#!/usr/bin/env python3
"""Import one lawfully obtained local evidence file by its pinned hash. No network."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from check_case import ROOT, EvidenceError, read_json, require

def import_capture(root, entry, source):
    target = (root / entry["path"]).resolve()
    require(target.is_relative_to((root / "private/evidence").resolve()), "Importziel muss unter private/evidence liegen")
    data = source.read_bytes()
    require(len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"], "Datei passt nicht zum belegten Hash/Umfang; Fassung manuell prüfen")
    require(not target.exists() or target.read_bytes() == data, "Vorhandenen abweichenden Beleg nicht überschreiben")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(source, target)
    return {"path": str(target.relative_to(root)), "sha256": entry["sha256"], "imported_at_utc": datetime.now(timezone.utc).isoformat(), "meaning": "Local copy verified; original retrieval time and legal review date unchanged."}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=ROOT / "sources/cy-eu.json")
    p.add_argument("--capture-id", required=True)
    p.add_argument("--file", type=Path, required=True)
    args = p.parse_args()
    try:
        catalog = read_json(args.catalog)
        manifest = read_json(ROOT / catalog["manifest_path"])
        entry = manifest["captures"][args.capture_id]
        result = import_capture(ROOT, entry, args.file)
    except (OSError, KeyError, ValueError, TypeError) as error:
        p.exit(1, f"Import failed: {error}\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
