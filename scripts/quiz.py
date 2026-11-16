#!/usr/bin/env python3
"""Practice true/false critical-thinking questions in the terminal.

Questions are drawn completely at random: every eligible pair is equally likely, nothing
repeats within a session, and past answers never affect the order. Each pair shows either
its true or its false statement, chosen at random.

Usage:
  python3 scripts/quiz.py                          # 10 random questions
  python3 scripts/quiz.py --area corporate-finance --n 25
  python3 scripts/quiz.py --kind origin            # who introduced what, and when
  python3 scripts/quiz.py --concept ct:confirmation-bias
  python3 scripts/quiz.py --seed 42                # replay the same set
  python3 scripts/quiz.py --list                   # show areas and question kinds

Answer with t (true), f (false) or q (quit). Scores are appended to a git-ignored
.quiz-progress.jsonl (or --progress PATH).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from common import INDEX_FILE, KINDS, ROOT


def load_pool(args) -> list[dict]:
    if not INDEX_FILE.exists():
        sys.exit("index/questions.json is missing; run python3 scripts/build_index.py")
    qs = json.loads(INDEX_FILE.read_text(encoding="utf-8"))["questions"]
    pool = []
    for q in qs:
        if q["status"] == "stale" and not args.include_stale:
            continue
        if args.area and q["area"] not in args.area:
            continue
        if args.kind and q["kind"] not in args.kind:
            continue
        if args.concept and args.concept not in q["concepts"]:
            continue
        if args.difficulty and q["difficulty"] != args.difficulty:
            continue
        pool.append(q)
    return pool


def wrap(text: str, indent: str = "  ") -> str:
    return textwrap.fill(text, width=88, initial_indent=indent, subsequent_indent=indent)


def ask(prompt: str) -> str:
    while True:
        ans = input(prompt).strip().lower()
        if ans in ("t", "true", "f", "false", "q", "quit"):
            return ans[0]
        print("  Type t, f or q.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=10, help="questions per session (default 10)")
    ap.add_argument("--area", action="append", help="critical-thinking area folder; repeat for several")
    ap.add_argument("--kind", action="append", choices=list(KINDS), help="question kind; repeat for several")
    ap.add_argument("--concept", help="concept id, e.g. ct:base-rate-fallacy")
    ap.add_argument("--difficulty", type=int, choices=(1, 2, 3))
    ap.add_argument("--include-stale", action="store_true", help="include pairs waiting to be re-checked")
    ap.add_argument("--seed", type=int, help="random seed, to replay the same set")
    ap.add_argument("--progress", default=str(ROOT / ".quiz-progress.jsonl"))
    ap.add_argument("--list", action="store_true", help="list areas and kinds, then exit")
    args = ap.parse_args()

    pool = load_pool(args)
    if args.list:
        print("Areas:")
        for area, n in sorted(Counter(q["area"] for q in pool).items()):
            print(f"  {area} ({n})")
        print("Kinds:")
        for kind, n in sorted(Counter(q["kind"] for q in pool).items()):
            print(f"  {kind}: {KINDS.get(kind, kind)} ({n})")
        return 0
    if not pool:
        print("No questions match those filters.")
        return 1

    rng = random.Random(args.seed)
    session = rng.sample(pool, min(args.n, len(pool)))
    correct = answered = 0
    missed = []
    print(f"{len(session)} question(s). Answer t (true), f (false) or q (quit).\n")
    for i, q in enumerate(session, 1):
        shows_true = rng.random() < 0.5
        statement = q["t"] if shows_true else q["f"]
        print(f"[{i}/{len(session)}] {q['topic']}  ({KINDS.get(q['kind'], q['kind'])})")
        print(wrap(statement))
        ans = ask("  True or false? ")
        if ans == "q":
            break
        answered += 1
        right = (ans == "t") == shows_true
        correct += right
        if not right:
            missed.append(q["topic"])
        print(f"  {'Correct' if right else 'Incorrect'}: this statement is {'TRUE' if shows_true else 'FALSE'}.")
        if not shows_true:
            print("  True version:")
            print(wrap(q["t"], "    "))
        print(wrap(q["x"]))
        print(f"  Read more: {q['source']}\n")

    if answered:
        print(f"Score: {correct}/{answered}")
        if missed:
            print("Topics to review: " + "; ".join(dict.fromkeys(missed)))
        entry = {"date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "answered": answered,
                 "correct": correct, "area": args.area, "kind": args.kind, "missed_topics": missed}
        with Path(args.progress).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)
