#!/usr/bin/env python3
"""Helpers for the daily generation run.

  pick  Decide this run's work: refresh stale pairs first, otherwise the source article
        with the fewest pairs (spreading new pairs across critical-thinking areas), along with the
        pairs already written from it and from its neighbours in the graph. Prints JSON.
  add   Turn drafted pairs (JSON) into question files, filling id, area, topic and source
        from the source article.

Usage:
  python3 scripts/generate.py pick [--source PATH] [--n 3]
  python3 scripts/generate.py add  [--source PATH] --input pairs.json

pairs.json:
  {"article": "articles/cognitive-biases/confirmation-bias.md",
   "pairs": [{"kind": "scenario", "true_statement": "...", "false_statement": "...",
              "explanation": "...", "difficulty": 1, "concepts": ["ct:confirmation-bias"]},
             {"kind": "figure", "as_of": "2024", ...}]}
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone

from common import (DEFAULT_SOURCE_REPO, KINDS, SKILL_KINDS, load_all, load_articles, next_id, print_json,
                    resolve_source_dir, save_question, source_blob, source_head)
from refresh import stale_queue

MAX_PAIRS_PER_ARTICLE = 6
RELATED_PAIRS_LIMIT = 60  # keeps pick's output readable for hub articles


def related_pairs(art: dict, records: list[dict], articles: dict) -> tuple[list[dict], int]:
    """Pairs written from other articles that sit next to this one in the graph: their concepts
    name this article, or their article has an edge to or from it. The same fact often appears
    in neighbouring articles (a theory's origin in both its own and its author's article), so
    the writer needs to see what is already covered. Returns the closest RELATED_PAIRS_LIMIT
    pairs and how many more were left out."""
    ids = {a["path"]: a.get("id") for a in articles.values()}
    scored = []
    for rec in records:
        path = rec["source"]["path"]
        if rec.get("status") == "retired" or path == art["path"]:
            continue
        other = articles.get(path) or {}
        score = (2 * (art["id"] in (rec.get("concepts") or []))  # the pair is about this article's node
                 + (ids.get(path) in art["neighbors"])
                 + (art["id"] in other.get("neighbors", [])))
        if score:
            scored.append((-score, rec["id"], {"id": rec["id"], "article": path,
                                               "true_statement": rec["true_statement"]}))
    scored.sort(key=lambda t: t[:2])
    return [item for _, _, item in scored[:RELATED_PAIRS_LIMIT]], max(0, len(scored) - RELATED_PAIRS_LIMIT)


def pick(src_dir, n: int) -> dict:
    articles = load_articles(src_dir)
    records = [rec for _, rec in load_all()]

    ready = stale_queue(records)
    if ready:
        batch = ready[:n]
        return {
            "mode": "refresh",
            "batch": [{"id": r["id"], "article": r["source"]["path"], "stale_reason": r.get("stale_reason")}
                      for r in batch],
            "stale_ready": len(ready),
        }

    live = [r for r in records if r.get("status") != "retired"]
    counts = Counter(r["source"]["path"] for r in live)
    area_counts = Counter(r["area"] for r in live)
    candidates = [a for a in articles.values() if counts.get(a["path"], 0) < MAX_PAIRS_PER_ARTICLE]
    if not candidates:
        return {"mode": "none", "reason": "every article already has the maximum number of pairs"}
    # Fewest pairs first; among those, the critical-thinking area with the fewest pairs, so practice
    # covers every area evenly; then the oldest article.
    candidates.sort(key=lambda a: (counts.get(a["path"], 0), area_counts.get(a["domain"], 0),
                                   a.get("created") or "", a["path"]))
    art = candidates[0]
    existing = [{"id": r["id"], "kind": r.get("kind"), "true_statement": r["true_statement"],
                 "false_statement": r["false_statement"]}
                for r in live if r["source"]["path"] == art["path"]]
    related, omitted = related_pairs(art, records, articles)
    used_kinds = Counter(p["kind"] for p in existing)
    return {
        "mode": "generate",
        "n": min(n, MAX_PAIRS_PER_ARTICLE - counts.get(art["path"], 0)),
        "article": art,
        # Kinds this article has no pair for yet: prefer these so each topic is learned from several sides.
        "kinds_not_yet_used": [k for k in KINDS if not used_kinds.get(k)],
        # The goal is better thinking, not trivia: until an article has a scenario or counter pair,
        # at least one of this run's pairs from it must be one of those kinds.
        "needs_skill_pair": not any(used_kinds.get(k) for k in SKILL_KINDS),
        "existing_pairs_for_article": existing,
        "related_pairs_in_other_articles": related,
        "related_pairs_omitted": omitted,
    }


def add(src_dir, input_path: str) -> list[str]:
    data = json.loads(open(input_path, encoding="utf-8").read())
    articles = load_articles(src_dir)
    head = source_head(src_dir)
    today = datetime.now(timezone.utc).date().isoformat()
    written = []
    for pair in data["pairs"]:
        art_path = pair.get("article") or data.get("article")
        art = articles.get(art_path)
        if not art:
            sys.exit(f"unknown source article {art_path!r}")
        concepts = pair.get("concepts") or [art["id"]]
        if art["id"] not in concepts:
            concepts = [art["id"], *concepts]
        rec = {
            "id": next_id(),
            "area": art["domain"],
            "kind": pair.get("kind"),
            "topic": art["title"],
            "topic_type": art.get("type"),
            "true_statement": pair["true_statement"].strip(),
            "false_statement": pair["false_statement"].strip(),
            "explanation": pair["explanation"].strip(),
            "as_of": pair.get("as_of"),
            "source": {"repo": DEFAULT_SOURCE_REPO, "path": art_path, "commit": head,
                       "blob": source_blob(src_dir, art_path)},
            "concepts": concepts,
            "related": pair.get("related") or [],
            "supersedes": pair.get("supersedes"),
            "difficulty": int(pair.get("difficulty", 2)),
            "created": today,
            "status": "active",
        }
        path = save_question(rec)
        written.append(rec["id"])
        print(f"wrote {path.relative_to(path.parent.parent.parent)}")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pick")
    p.add_argument("--source")
    p.add_argument("--n", type=int, default=3)
    a = sub.add_parser("add")
    a.add_argument("--source")
    a.add_argument("--input", required=True)
    args = ap.parse_args()
    src_dir = resolve_source_dir(args.source)
    if args.cmd == "pick":
        print_json(pick(src_dir, args.n))
    else:
        add(src_dir, args.input)
    return 0


if __name__ == "__main__":
    sys.exit(main())
