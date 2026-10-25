#!/usr/bin/env python3
"""Fetch FDA-approved drug label sections from the openFDA API (standard library only).

This anchors a prescribing plan to the **regulatory label** instead of recall:
indications, dosage, contraindications, warnings, interactions, and use in
specific populations come back as verbatim label text with a citable set id.

openFDA is US FDA labeling (DailyMed/Spl). It does NOT cover Korean MFDS labels
or non-US products; use the MFDS/식약처 product page in addition when the patient
is in Korea. Always confirm the section exists — absence of a section in the API
response is NOT evidence that the warning does not exist.

Usage:
  python fetch_drug_label.py metformin
  python fetch_drug_label.py "sitagliptin metformin" --field brand_name --limit 5
  python fetch_drug_label.py apixaban --section contraindications --section drug_interactions
  python fetch_drug_label.py warfarin --json > label.json
  # free-text label search (slower, noisier):
  python fetch_drug_label.py --search 'openfda.rxcui:"1191"' --section boxed_warning
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

API = "https://api.fda.gov/drug/label.json"

# Label sections a prescribing decision commonly needs, in print order.
DEFAULT_SECTIONS = [
    "boxed_warning",
    "indications_and_usage",
    "dosage_and_administration",
    "contraindications",
    "warnings_and_cautions",
    "adverse_reactions",
    "drug_interactions",
    "use_in_specific_populations",
    "overdosage",
]


def _get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "clinical-prescribing-safety/1.0"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.load(resp)


def query(name=None, field="openfda.generic_name", limit=3, raw=None):
    if raw:
        search = raw
    else:
        # Exact-phrase match; openFDA is exact and case-insensitive on the field.
        search = '%s:"%s"' % (field, name.replace('"', ""))
    data = _get({"search": search, "limit": limit})
    return data.get("results", [])


def pick(records):
    """Prefer a record that actually has an indications_and_usage section."""
    for r in records:
        if r.get("indications_and_usage"):
            return r
    return records[0] if records else None


def main():
    ap = argparse.ArgumentParser(description="Fetch openFDA drug label sections.")
    ap.add_argument("name", nargs="?", help="drug generic or brand name")
    ap.add_argument("--field", default="openfda.generic_name",
                    help="openfda field to match on (openfda.generic_name | openfda.brand_name)")
    ap.add_argument("--search", help="raw openFDA search expression (bypasses name/field)")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--section", action="append",
                    help="label section key to print (repeatable); default: all core sections")
    ap.add_argument("--max-chars", type=int, default=1200,
                    help="truncate each section to N chars (0 = no limit)")
    ap.add_argument("--json", action="store_true", help="print raw JSON record")
    args = ap.parse_args()

    if not args.name and not args.search:
        ap.error("give a drug name or --search")

    try:
        records = query(name=args.name, field=args.field, limit=args.limit, raw=args.search)
    except Exception as exc:  # noqa: BLE001 - report network/404 cleanly
        print("openFDA query failed: %s" % exc, file=sys.stderr)
        print("(a 404 means 'no label matched'; it is NOT evidence the drug is unsafe)", file=sys.stderr)
        sys.exit(1)

    if not records:
        print("No label matched %r." % (args.search or args.name), file=sys.stderr)
        print("Try --field openfda.brand_name, or search DailyMed/MFDS directly.", file=sys.stderr)
        sys.exit(1)

    rec = pick(records)
    if args.json:
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return

    of = rec.get("openfda", {})
    print("== OpenFDA label anchor ==")
    print("brand:   %s" % ", ".join(of.get("brand_name", []) or ["(none)"]))
    print("generic: %s" % ", ".join(of.get("generic_name", []) or ["(none)"]))
    print("rxcui:   %s" % ", ".join(of.get("rxcui", []) or ["(none)"]))
    print("spl_set_id: %s" % (rec.get("set_id", "(none)")))
    print("effective_time: %s" % (rec.get("effective_time", "(none)")))
    print("cite as: FDA label (openFDA set_id %s), retrieved via api.fda.gov" % rec.get("set_id", "?"))
    print("note: US label only; confirm the MFDS/식약처 product label for Korea.\n")

    sections = args.section or DEFAULT_SECTIONS
    for key in sections:
        vals = rec.get(key)
        if not vals:
            print("--- %s: (absent in this label — do not treat as 'no warning') ---" % key)
            continue
        text = " ".join(vals)
        text = " ".join(text.split())  # collapse whitespace
        if args.max_chars and len(text) > args.max_chars:
            text = text[: args.max_chars] + " … [truncated]"
        print("--- %s ---" % key)
        print(text + "\n")


if __name__ == "__main__":
    main()
