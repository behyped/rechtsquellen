#!/usr/bin/env python3
"""Find bounded legal-source context in curated local metadata (no network)."""
import argparse
from datetime import date
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]

def folded(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))

def select(catalogs, jurisdiction=None, query="", source_id=None, as_of=None, limit=6):
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    when = date.fromisoformat(as_of) if as_of else None
    found = []
    for catalog in catalogs:
        for key, s in catalog["sources"].items():
            if jurisdiction and s["jurisdiction"] != jurisdiction:
                continue
            if source_id and key != source_id:
                continue
            text = folded(" ".join([key, s["publication_citation"], s["authority"], *s.get("keywords", [])]))
            if query and not all(term in text for term in folded(query).split()):
                continue
            v = s.get("version")
            state = "not_a_verified_provision"
            if v:
                state = "date_not_requested"
                if when:
                    end = date.fromisoformat(v["applies_until_exclusive"]) if v["applies_until_exclusive"] else None
                    state = "within_review_window" if date.fromisoformat(v["applies_from"]) <= when <= date.fromisoformat(v["checked_through"]) and (end is None or when < end) else "outside_review_window"
            row = {"source_id": key, **{k: s[k] for k in ("jurisdiction", "publication_citation", "kind", "language", "issuer_class", "host_class", "publisher_url", "access_url", "data_license")}, "version_id": v["id"] if v else None, "checked_through": v["checked_through"] if v else None, "date_status": state, "related_source_ids": s.get("related_source_ids", []), "limits": s.get("limits", "")}
            if source_id:
                row["provisions"] = s.get("provisions", {})
                row["version"] = v
            found.append(row)
    found.sort(key=lambda row: (row["version_id"] is None, row["source_id"]))
    return {"meaning": "Metadata selection only; run check_case.py against the evidence before relying on a quotation.", "total_matches": len(found), "returned": min(len(found), limit), "truncated": len(found) > limit, "sources": found[:limit]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jurisdiction", choices=["CY", "EU", "ZA"])
    p.add_argument("--query", default="")
    p.add_argument("--source")
    p.add_argument("--as-of")
    p.add_argument("--limit", type=int, default=6)
    args = p.parse_args()
    try:
        catalogs = [json.loads(path.read_text()) for path in sorted((ROOT / "sources").glob("*.json"))]
        result = select(catalogs, args.jurisdiction, args.query, args.source, args.as_of, args.limit)
    except (OSError, KeyError, ValueError, TypeError) as error:
        p.exit(1, f"Context selection failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
