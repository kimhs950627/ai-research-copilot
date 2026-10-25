#!/usr/bin/env python3
"""Retrieve PubMed records via NCBI E-utilities. Standard library only.

This is a real, runnable helper: it performs esearch + esummary and prints
JSON records (pmid, title, journal, year, authors, doi).

Usage:
  python retrieve_pubmed.py "sglt2 inhibitors heart failure" --retmax 20
  python retrieve_pubmed.py "..." --email you@example.com   # recommended by NCBI
  NCBI_API_KEY=... python retrieve_pubmed.py "..."          # raise rate limit

Note: records here are DISCOVERY aids. Reading the record is not evidence; read
the full text (or abstract) and record the access level in the evidence ledger.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "academic-research-writing/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _params(email, api_key, **kw):
    p = dict(kw)
    if email:
        p["email"] = email
    if api_key:
        p["api_key"] = api_key
    return p


def esearch(term, retmax, email, api_key):
    url = BASE + "/esearch.fcgi?" + urllib.parse.urlencode(
        _params(email, api_key, db="pubmed", term=term, retmode="json", retmax=retmax)
    )
    return _get_json(url)


def esummary(ids, email, api_key):
    url = BASE + "/esummary.fcgi?" + urllib.parse.urlencode(
        _params(email, api_key, db="pubmed", id=",".join(ids), retmode="json")
    )
    return _get_json(url)


def main():
    ap = argparse.ArgumentParser(description="PubMed search via E-utilities")
    ap.add_argument("query")
    ap.add_argument("--retmax", type=int, default=20)
    ap.add_argument("--email", default=os.environ.get("NCBI_EMAIL", ""))
    args = ap.parse_args()
    api_key = os.environ.get("NCBI_API_KEY", "")

    search = esearch(args.query, args.retmax, args.email, api_key)
    ids = search.get("esearchresult", {}).get("idlist", [])
    if not ids:
        print("[]")
        return

    summary = esummary(ids, args.email, api_key)
    out = []
    for pmid in ids:
        rec = summary.get("result", {}).get(pmid, {})
        doi = ""
        for aid in rec.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
        out.append(
            {
                "pmid": pmid,
                "title": rec.get("title", ""),
                "journal": rec.get("fulljournalname") or rec.get("source", ""),
                "year": (rec.get("pubdate", "").split(" ")[0] if rec.get("pubdate") else ""),
                "authors": [a.get("name", "") for a in rec.get("authors", [])],
                "doi": doi,
            }
        )
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
