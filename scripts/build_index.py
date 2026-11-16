#!/usr/bin/env python3
"""Generate index/questions.json (read by quiz.py and the mobile app) and coverage/coverage.json.

Usage:
  python3 scripts/build_index.py           # write both files
  python3 scripts/build_index.py --check   # exit 1 if either file is out of date
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict

from common import COVERAGE_FILE, INDEX_FILE, load_all, article_url


def build() -> tuple[str, str]:
    records = [rec for _, rec in load_all()]
    questions = []
    for rec in sorted(records, key=lambda r: r["id"]):
        if rec.get("status") == "retired":
            continue
        q = {
            "id": rec["id"],
            "area": rec["area"],
            "kind": rec["kind"],
            "topic": rec["topic"],
            "t": rec["true_statement"],
            "f": rec["false_statement"],
            "x": rec["explanation"],
            "concepts": rec.get("concepts") or [],
            "difficulty": rec["difficulty"],
            "status": rec["status"],
            "source": article_url(rec),
        }
        if rec.get("as_of"):
            q["asOf"] = rec["as_of"]
        questions.append(q)
    index = {
        "version": 1,
        "count": len(questions),
        "active": sum(q["status"] == "active" for q in questions),
        "questions": questions,
    }

    per_article = defaultdict(Counter)
    per_area = defaultdict(Counter)
    per_kind = defaultdict(Counter)
    for rec in records:
        per_article[rec["source"]["path"]][rec["status"]] += 1
        per_area[rec["area"]][rec["status"]] += 1
        per_kind[rec.get("kind")][rec["status"]] += 1
    coverage = {
        "totals": dict(Counter(r["status"] for r in records)),
        "areas": {k: dict(v) for k, v in sorted(per_area.items())},
        "kinds": {k: dict(v) for k, v in sorted(per_kind.items(), key=lambda kv: str(kv[0]))},
        "articles": {k: dict(v) for k, v in sorted(per_article.items())},
    }
    dump = lambda obj: json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
    return dump(index), dump(coverage)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if the generated files are out of date")
    args = ap.parse_args()
    index, coverage = build()
    targets = ((INDEX_FILE, index), (COVERAGE_FILE, coverage))
    if args.check:
        stale = [p.name for p, text in targets if not p.exists() or p.read_text(encoding="utf-8") != text]
        if stale:
            print(f"OUT OF DATE: {', '.join(stale)}; run python3 scripts/build_index.py")
            return 1
        print("OK: index and coverage are up to date")
        return 0
    for path, text in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"Wrote {INDEX_FILE.relative_to(INDEX_FILE.parent.parent)} and "
          f"{COVERAGE_FILE.relative_to(COVERAGE_FILE.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
