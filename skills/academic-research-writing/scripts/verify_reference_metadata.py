#!/usr/bin/env python3
"""Verify reference metadata against Crossref. Standard library only.

Verifies SOURCE EXISTENCE and bibliographic accuracy only. It does NOT verify
whether a work supports a claim — that is a separate step (see the evidence
ledger and evidence-extraction reference).

Usage:
  python verify_reference_metadata.py 10.1056/NEJMoa2034577
  python verify_reference_metadata.py --file refs.json --email you@example.com

refs.json format:  [ {"title": "...", "year": 2021, "doi": "10.xxxx/yyy"}, ... ]
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

UA = "academic-research-writing/1.0 (mailto:{email})"


def crossref(doi, email):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(
        url, headers={"User-Agent": UA.format(email=email or "example@example.com")}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["message"]


def summarize(m):
    issued = (m.get("issued", {}).get("date-parts") or [[None]])[0] or [None]
    return {
        "doi": m.get("DOI"),
        "title": (m.get("title") or [""])[0],
        "authors": [
            f"{a.get('family', '')} {a.get('given', '')}".strip() for a in m.get("author", [])
        ],
        "year": issued[0],
        "container": (m.get("container-title") or [""])[0],
        "type": m.get("type"),
    }


def check(ref, email):
    doi = ref.get("doi")
    if not doi:
        return {"input": ref, "error": "no doi"}
    try:
        canonical = summarize(crossref(doi, email))
        mism = []
        if ref.get("title") and canonical["title"]:
            if ref["title"].strip().lower() not in canonical["title"].lower():
                mism.append("title")
        try:
            if ref.get("year") and canonical["year"] and int(ref["year"]) != int(canonical["year"]):
                mism.append("year")
        except (TypeError, ValueError):
            pass
        return {"input": ref, "canonical": canonical, "mismatches": mism}
    except Exception as exc:  # network / 404 / malformed
        return {"input": ref, "error": str(exc)}


def main():
    ap = argparse.ArgumentParser(description="Crossref reference verification")
    ap.add_argument("doi", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--email", default="")
    args = ap.parse_args()

    if args.file:
        refs = json.load(open(args.file, encoding="utf-8"))
        results = [check(r, args.email) for r in refs]
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
        print()
    elif args.doi:
        json.dump(summarize(crossref(args.doi, args.email)), sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        ap.error("provide a DOI or --file")


if __name__ == "__main__":
    main()
