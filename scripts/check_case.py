#!/usr/bin/env python3
"""Verify a case's registered law citations against pinned evidence."""

import argparse
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def iso_date(value):
    parsed = date.fromisoformat(value)
    require(parsed.isoformat() == value, f"Datum muss YYYY-MM-DD sein: {value}")
    return parsed


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_capture(root, captures, capture_id):
    entry = captures.get(capture_id)
    require(entry is not None, f"Nachweis fehlt: {capture_id}")
    require(entry["http_status"] == 200 and entry["curl_exit"] == 0, f"Kein vollständiger erfolgreicher Abruf: {capture_id}")
    path = (root / entry["path"]).resolve()
    evidence_roots = (root / "docs/evidence", root / "private/evidence")
    require(any(path.is_relative_to(base) for base in evidence_roots), f"Pfad außerhalb der Nachweisablage: {capture_id}")
    data = path.read_bytes()
    require(
        len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"],
        f"Bytes oder SHA-256 weichen ab: {capture_id}",
    )
    if entry["classification"] == "raw":
        require(len(data) == entry["transport_body_bytes"], f"Antwortkörper unvollständig: {capture_id}")
    retrieved = datetime.fromisoformat(entry["retrieved_at_utc"].replace("Z", "+00:00"))
    require(retrieved.utcoffset() == timedelta(0), f"Abrufzeit ohne UTC: {capture_id}")
    return entry, path, retrieved


def check_citation(claim, as_of, sources, captures, root):
    source_id = claim["source_id"]
    source = sources.get(source_id)
    require(source is not None, f"Quelle nicht registriert: {source_id}")
    require(
        source["issuer_class"] == "official" and source["kind"] == "legislation",
        f"Quelle ist keine amtliche Norm: {source_id}",
    )
    version = source["version"]
    require(version is not None and version["id"] == claim["version_id"], f"Falsche oder unbelegte Fassung: {source_id}")
    require(
        iso_date(source["published_on"]) <= iso_date(version["in_force_from"])
        <= iso_date(version["applies_from"]) <= as_of <= iso_date(version["checked_through"]),
        f"Stichtag {as_of} liegt außerhalb des belegten Anwendungszeitraums: {source_id}",
    )
    if version["applies_until_exclusive"] is not None:
        require(as_of < iso_date(version["applies_until_exclusive"]), f"Fassung abgelöst: {source_id}")

    locator = claim["locator"]
    provision = source["provisions"].get(locator)
    require(provision is not None, f"Fundstelle nicht geprüft: {source_id}, {locator}")
    require(claim["quote"] and claim["quote"] == provision["quote"], f"Zitat weicht ab: {source_id}, {locator}")
    original, path, _ = verify_capture(root, captures, provision["capture_id"])
    require(original["classification"] == "raw" and original["format"] == "pdf", f"Amtsblatt-PDF fehlt: {source_id}")
    require(original["source_url"] == source["access_url"], f"Abruf-URL weicht ab: {source_id}")

    reviews = [verify_capture(root, captures, capture_id)[2] for capture_id in version["review_capture_ids"]]
    require(reviews and max(reviews).date() >= iso_date(version["checked_through"]), f"Prüfstand ohne datierten Fassungsbeleg: {source_id}")

    page = str(provision["pdf_page"])
    content = subprocess.run(
        ["pdftotext", "-f", page, "-l", page, "-layout", str(path), "-"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    require(" ".join(claim["quote"].split()) in " ".join(content.split()), f"Zitat fehlt im PDF auf Seite {page}: {source_id}")
    return {
        "source_id": source_id,
        "checked_through": version["checked_through"],
        "jurisdiction": source["jurisdiction"],
        "citation": f'{source["publication_citation"]}, {locator}, {provision["pinpoint"]}',
        "version_id": version["id"],
        "language": source["language"],
        "quote": claim["quote"],
        "publication_url": source["publisher_url"],
        "access_url": source["access_url"],
        "host_class": source["host_class"],
        "retrieved_at_utc": original["retrieved_at_utc"],
        "sha256": original["sha256"],
    }


def check_case(case, catalog, manifest, root):
    require(case["schema_version"] == catalog["schema_version"] == manifest["schema_version"] == 1, "Unbekannter Datenvertrag")
    as_of = iso_date(case["as_of"])
    require(case["citations"], "Fall enthält keine zu prüfenden Zitate")
    citations = [
        check_citation(claim, as_of, catalog["sources"], manifest["captures"], root)
        for claim in case["citations"]
    ]
    return {"case_id": case["id"], "as_of": as_of.isoformat(), "citations": citations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--catalog", type=Path, default=ROOT / "sources/cy-eu.json")
    args = parser.parse_args()
    try:
        case = read_json(args.case)
        catalog = read_json(args.catalog)
        manifest = read_json(ROOT / catalog["manifest_path"])
        checked = check_case(case, catalog, manifest, ROOT)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Quellenprüfung fehlgeschlagen: {error}\n")
    print(json.dumps(checked, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
