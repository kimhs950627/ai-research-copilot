#!/usr/bin/env python3
"""Validate an evidence ledger JSON file. Standard library only.

Checks required fields, enum values, and flags unverified/unsupported claims.
Exit code 1 when errors are found (usable as a completion gate).

Usage:
  python validate_evidence_ledger.py evidence-ledger.json
"""
import json
import sys

REQUIRED = [
    "claim_id",
    "claim",
    "source",
    "access_level",
    "support_status",
    "verification_status",
]
ENUMS = {
    "access_level": {"full_text", "abstract", "metadata_only"},
    "support_status": {"direct", "partial", "conflicting", "unsupported"},
    "verification_status": {"unverified", "verified", "flagged"},
}


def main():
    if len(sys.argv) < 2:
        print("usage: validate_evidence_ledger.py ledger.json")
        sys.exit(2)
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    entries = data if isinstance(data, list) else data.get("entries", [])

    errors, warnings = [], []
    for i, e in enumerate(entries):
        cid = e.get("claim_id", "#%d" % i)
        for key in REQUIRED:
            if key not in e or e[key] in ("", None):
                errors.append("%s: missing %s" % (cid, key))
        for key, allowed in ENUMS.items():
            if e.get(key) and e[key] not in allowed:
                errors.append("%s: %s=%r not in %s" % (cid, key, e[key], sorted(allowed)))
        if not (e.get("source") or {}).get("title"):
            errors.append("%s: source.title missing" % cid)
        if e.get("access_level") in ("abstract", "metadata_only") and e.get("support_status") == "direct":
            warnings.append("%s: access_level=%s but support_status=direct (can the claim really be direct without full text?)" % (cid, e["access_level"]))
        if e.get("support_status") in ("unsupported", "conflicting"):
            warnings.append("%s: support_status=%s -> fix or soften the claim" % (cid, e["support_status"]))
        if e.get("verification_status") == "unverified":
            warnings.append("%s: verification_status=unverified" % cid)

    print("entries: %d  errors: %d  warnings: %d" % (len(entries), len(errors), len(warnings)))
    for x in errors:
        print("ERROR", x)
    for x in warnings:
        print("WARN ", x)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
