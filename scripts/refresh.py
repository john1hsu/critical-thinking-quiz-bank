#!/usr/bin/env python3
"""Keep pairs in step with their source articles in critical-thinking-graph.

Ideas about reasoning don't ship in releases, so a pair goes stale only when its source article
changes (a corrected date, a newer figure, a reworded claim) or disappears.

  mark-stale  Mark active pairs stale when their source article changed since they were
              verified (drift), or was removed or renamed.
  queue       List stale pairs in refresh order (dated figures first, then other numbers, then the rest).
  verify      The pair still holds: stamp the article's latest version and title.
  supersede   The fact changed: retire the old pair and add a new one that points back to it.
  retire      The article or the fact is gone: retire the pair.

Usage:
  python3 scripts/refresh.py mark-stale [--source PATH]
  python3 scripts/refresh.py queue
  python3 scripts/refresh.py verify     [--source PATH] ct-000123
  python3 scripts/refresh.py supersede  [--source PATH] ct-000123 --input new_pair.json
  python3 scripts/refresh.py retire     ct-000123 --reason "article removed"
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from common import (find_question, load_all, load_articles, print_json, resolve_source_dir,
                    save_question, source_blob, source_head)

DIGIT_RE = re.compile(r"\d")


def priority(rec: dict) -> tuple:
    if rec.get("kind") == "figure":
        tier = 0  # dated figures change most often
    elif DIGIT_RE.search(rec.get("true_statement", "") + rec.get("false_statement", "")):
        tier = 1
    else:
        tier = 2
    return (tier, rec["id"])


def stale_queue(records: list[dict]) -> list[dict]:
    """Stale pairs in refresh order. Every stale pair is ready: its article has already changed."""
    return sorted((r for r in records if r.get("status") == "stale"), key=priority)


def mark_stale(src_dir) -> None:
    articles = load_articles(src_dir)
    marked = []
    for _, rec in load_all():
        if rec.get("status") != "active":
            continue
        path = rec["source"]["path"]
        reason = None
        if path not in articles:
            reason = "source article removed or renamed"
        elif source_blob(src_dir, path) != rec["source"]["blob"]:
            reason = "drift: source article changed since this pair was verified"
        if reason:
            rec["status"], rec["stale_reason"] = "stale", reason
            save_question(rec)
            marked.append({"id": rec["id"], "reason": reason})
    print_json({"marked_stale": marked})


def show_queue() -> None:
    ready = stale_queue([r for _, r in load_all()])
    print_json({"stale": [{"id": r["id"], "article": r["source"]["path"], "reason": r.get("stale_reason")}
                          for r in ready]})


def verify(src_dir, qid: str) -> None:
    articles = load_articles(src_dir)
    _, rec = find_question(qid)
    art = articles.get(rec["source"]["path"])
    if art is None:
        sys.exit(f"{qid}: source article is gone; retire the pair instead")
    rec["topic"] = art["title"]
    rec["topic_type"] = art.get("type")
    rec["source"].update(commit=source_head(src_dir), blob=source_blob(src_dir, art["path"]))
    rec["status"] = "active"
    rec.pop("stale_reason", None)
    save_question(rec)
    print(f"{qid}: verified against the article's latest version")


def retire(qid: str, reason: str) -> None:
    _, rec = find_question(qid)
    rec["status"] = "retired"
    rec["retired_reason"] = reason
    rec.pop("stale_reason", None)
    save_question(rec)
    print(f"{qid}: retired ({reason})")


def supersede(src_dir, qid: str, input_path: str) -> None:
    from generate import add
    data = json.loads(open(input_path, encoding="utf-8").read())
    _, old = find_question(qid)
    data.setdefault("article", old["source"]["path"])
    if len(data.get("pairs", [])) != 1:
        sys.exit("supersede takes exactly one replacement pair")
    new = data["pairs"][0]
    new["supersedes"] = qid
    for key in ("difficulty", "concepts", "kind"):
        new.setdefault(key, old.get(key))
    tmp = input_path + ".tmp"
    open(tmp, "w", encoding="utf-8").write(json.dumps(data))
    retire(qid, "fact changed; superseded by a newer pair")
    new_ids = add(src_dir, tmp)
    _, old = find_question(qid)
    old["retired_reason"] = f"fact changed; superseded by {new_ids[0]}"
    save_question(old)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mark-stale").add_argument("--source")
    sub.add_parser("queue")
    v = sub.add_parser("verify")
    v.add_argument("--source")
    v.add_argument("id")
    s = sub.add_parser("supersede")
    s.add_argument("--source")
    s.add_argument("id")
    s.add_argument("--input", required=True)
    r = sub.add_parser("retire")
    r.add_argument("id")
    r.add_argument("--reason", required=True)
    args = ap.parse_args()

    if args.cmd == "retire":
        retire(args.id, args.reason)
    elif args.cmd == "queue":
        show_queue()
    elif args.cmd == "mark-stale":
        mark_stale(resolve_source_dir(args.source))
    elif args.cmd == "verify":
        verify(resolve_source_dir(args.source), args.id)
    else:
        supersede(resolve_source_dir(args.source), args.id, args.input)
    return 0


if __name__ == "__main__":
    sys.exit(main())
