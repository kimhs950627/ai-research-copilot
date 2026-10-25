#!/usr/bin/env python3
"""Multi-source literature retrieval for an answer-first (Perplexity-style) pass.

Runs one query across **Europe PMC** and **OpenAlex** (plus optional Crossref
resolution) and prints a single numbered candidate list — the "raw sources"
stage before synthesis. PubMed is handled by retrieve_pubmed.py; use both when
you want MEDLINE coverage.

These records are DISCOVERY aids. A retrieved title/abstract is not evidence:
read the source and record the access level (`full_text` | `abstract` |
`metadata_only`) in the evidence ledger before you cite it.

Usage:
  python search_sources.py "SGLT2 inhibitor heart failure" --limit 10
  python search_sources.py "..." --source europepmc          # one source only
  python search_sources.py "..." --json                       # machine-readable
  python search_sources.py "..." --years 5                    # last 5 years only
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import date

UA = "academic-research-writing/1.0 (mailto:you@example.com)"


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.load(resp)


def europepmc(query, limit, since):
    q = query if not since else "%s AND (FIRST_PDATE:[%s TO %s])" % (query, since, date.today().isoformat())
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
        {"query": q, "format": "json", "pageSize": limit, "resultType": "core"}
    )
    out = []
    for r in _get_json(url).get("resultList", {}).get("result", []):
        out.append({
            "source": "Europe PMC (%s)" % r.get("source", "?"),
            "title": r.get("title", "").strip(),
            "journal": (r.get("journalInfo", {}) or {}).get("journal", {}).get("title", ""),
            "year": r.get("pubYear", ""),
            "authors": r.get("authorString", ""),
            "doi": r.get("doi", ""),
            "pmid": r.get("pmid", ""),
            "type": r.get("pubType", ""),
            "is_oa": r.get("isOpenAccess", ""),
        })
    return out


def openalex(query, limit, since):
    params = {"search": query, "per-page": limit, "mailto": "you@example.com"}
    if since:
        params["filter"] = "from_publication_date:%s" % since
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    out = []
    for w in _get_json(url).get("results", []):
        loc = w.get("primary_location", {}) or {}
        src = loc.get("source", {}) or {}
        out.append({
            "source": "OpenAlex",
            "title": w.get("title") or "",
            "journal": src.get("display_name", ""),
            "year": w.get("publication_year", ""),
            "authors": ", ".join(a["author"]["display_name"] for a in (w.get("authorships") or [])[:4]),
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "pmid": "",
            "type": w.get("type", ""),
            "is_oa": w.get("open_access", {}).get("is_oa", ""),
            "cited_by": w.get("cited_by_count", ""),
        })
    return out


def main():
    ap = argparse.ArgumentParser(description="Search Europe PMC and OpenAlex.")
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=10, help="hits per source")
    ap.add_argument("--years", type=int, default=0, help="restrict to the last N years (0 = all)")
    ap.add_argument("--source", action="append", choices=["europepmc", "openalex"],
                    help="limit to specific sources (repeatable)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    since = ""
    if args.years:
        since = "%d-01-01" % (date.today().year - args.years + 1)

    wanted = args.source or ["europepmc", "openalex"]
    rows = []
    for name in wanted:
        try:
            rows += (europepmc if name == "europepmc" else openalex)(args.query, args.limit, since)
        except Exception as exc:  # noqa: BLE001
            print("WARN: %s failed: %s" % (name, exc), file=sys.stderr)

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    if not rows:
        print("No records. Reformulate the query before concluding 'no evidence'.")
        sys.exit(1)

    print("# %d candidate sources for: %s\n" % (len(rows), args.query))
    for i, r in enumerate(rows, 1):
        ident = []
        if r["doi"]:
            ident.append("doi:%s" % r["doi"])
        if r["pmid"]:
            ident.append("pmid:%s" % r["pmid"])
        print("[%d] %s (%s)" % (i, r["title"] or "(no title)", r["year"] or "n.d."))
        print("    %s | %s | OA=%s" % (r["journal"] or "-", " ".join(ident) or "-", r["is_oa"]))
        print("    via %s | type=%s" % (r["source"], r["type"] or "-"))
    print("\nNext: read each hit and record access_level before citing it as evidence.")


if __name__ == "__main__":
    main()
