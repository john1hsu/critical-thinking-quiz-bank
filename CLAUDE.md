# Critical thinking quiz bank: daily run playbook

This repo is a bank of paired true/false questions that help John **think better**, not just memorise terms. Every pair is generated from the cited articles in [john1hsu/critical-thinking-graph](https://github.com/john1hsu/critical-thinking-graph). A daily scheduled run handles up to **100 pairs**: it refreshes stale pairs first, then spends the rest of the budget on new ones, at most **3 per article**. Everything goes to `main` as **one combined commit** with one push, and only when every check passes. Read `SCHEMA.md` before writing.

## 1. Sync

```bash
git pull --rebase origin main
rm -rf .source && git clone --depth 1 https://github.com/john1hsu/critical-thinking-graph .source/critical-thinking-graph
python3 scripts/validate.py   # the repo's own checks, without the source; must print OK; fix the repo first if not
```

Don't pass `--source` here: source articles change between runs, and step 2 is what handles that.

## 2. Mark stale pairs

```bash
python3 scripts/refresh.py mark-stale
python3 scripts/validate.py --source .source/critical-thinking-graph   # must print OK now; fix the repo first if not
```

`mark-stale` marks active pairs stale when their source article changed since they were verified (a corrected date, a new replication result, a changed evidence status, a reworded claim), or when the article was removed or renamed. Always run it before validating against the source: a changed or missing article is an error on an active pair, but expected on a stale one that is waiting for step 4a.

## 3. Pick this run's work

The budget is 100 pairs per run (refreshed plus new). Repeat this step until the budget is used or `pick` returns `"none"`:

```bash
python3 scripts/generate.py pick --n 3
```

- `"mode": "refresh"` → do step 4a for every pair in `batch`.
- `"mode": "generate"` → do step 4b for `article`, writing `n` pairs.
- `"mode": "none"` → stop picking and go to step 5. If nothing was refreshed or added but step 2 marked pairs stale, commit that with the message `quiz: mark <n> pairs stale`; if nothing changed at all, stop without committing.

Don't commit between picks. Run `python3 scripts/validate.py --source .source/critical-thinking-graph` after roughly every 15 new pairs to catch problems early.

Stale pairs always come before new ones (dated figures first). New articles are picked fewest-pairs first, and among those from the area with the fewest pairs, so practice stays spread across fallacies, biases, logic, evidence, decisions and the rest.

## 4a. Refresh a stale pair

Read the pair (`questions/*/<id>.yaml`) and the **current** source article in full. Decide:

| Outcome | Command |
| --- | --- |
| Both statements still hold (true one true, false one false) per the article | `python3 scripts/refresh.py verify <id>` |
| The fact changed (a failed replication, a new meta-analysis, a corrected date or attribution) | Write one replacement pair to a JSON file (format in 4b), then `python3 scripts/refresh.py supersede <id> --input <file>` |
| The article is gone, or no longer supports the fact | `python3 scripts/refresh.py retire <id> --reason "<why>"` |

If the article now says something that makes the explanation wrong but both statements still hold, supersede rather than verify. Watch `evidence_status` in particular: a pair that presents an effect as solid must be superseded if the article now marks it `contested` or `failed-replication`.

## 4b. Write new pairs

Read the whole article (`.source/critical-thinking-graph/<path>`), including its frontmatter. `pick` also hands you the article's `critical_questions`, `argument_map` and `evidence_status`: these are the best raw material for skill pairs. Check `existing_pairs_for_article` and `related_pairs_in_other_articles` so you don't repeat a fact: the second list holds the true statements already written from neighbouring articles, and a fact any of them tests is taken, even if this article words it differently. Write `n` pairs to a JSON file outside the repo (the scratchpad):

```json
{"article": "articles/<domain>/<slug>.md",
 "pairs": [{"kind": "scenario", "true_statement": "<a short situation>, which is <the right fallacy, bias, form or verdict>.",
            "false_statement": "<the same situation>, which is <a neighbouring one that is easy to confuse>.",
            "explanation": "...", "difficulty": 2, "concepts": ["ct:<article-id>", "ct:<other-node>"]},
           {"kind": "counter", "true_statement": "...", "false_statement": "...", "explanation": "...", "difficulty": 2}]}
```

### The goal: practise the skill, not just the vocabulary

John wants this bank to improve his critical thinking rather than quiz him on facts about it. So:

- **If `needs_skill_pair` is true, at least one of the article's pairs this run must be a `scenario` or `counter` pair.** Write both when the article supports them (fallacies, biases, heuristics, reasoning forms, schemes and techniques nearly always do). Person, work and history articles may have only knowledge kinds.
- Then prefer the kinds in `kinds_not_yet_used` (listed skill kinds first), so a topic is learned from several sides.

| kind | App label | Tests | Example true statement |
| --- | --- | --- | --- |
| `scenario` | Spot it | Recognising the move in a realistic everyday or workplace situation: which fallacy, bias, heuristic or form it is, or whether the reasoning holds | A manager dismisses an analyst's cost comparison because the analyst once worked for the vendor, which is an ad hominem. |
| `counter` | Ask and counter | What to ask, check or do about it: a critical question, a debiasing technique, how to repair the argument, when the move is actually reasonable | Asking whether an argument would still stand if someone with no stake had made it is a check against ad hominem reasoning. |
| `definition` | What it is | What the idea is, and what it is not | Affirming the consequent infers P from "if P then Q" and Q. |
| `mechanism` | How it works | Why it misleads or why it works: the form, the cognitive process, cause and effect | The availability heuristic judges frequency by how easily examples come to mind. |
| `evidence` | Evidence and replication | What research shows, replication status, main critiques and limits | Large multi-lab replications have not reproduced the ego depletion effect. |
| `origin` | Who and when | Who introduced it, where and when | Tversky and Kahneman described the anchoring heuristic in a 1974 Science paper. |
| `figure` | Numbers and dates | A dated number (needs `as_of`) | A sample size, effect size or result, with the year written into the statement |

Rules for each pair:

- **Grounding:** every pair must be answerable from this article alone. Don't add facts from memory, even true ones. A `scenario` may describe a new situation, but the verdict must follow from the article's own definition, conditions or examples, and the explanation must say which feature of the situation decides it.
- **Scenarios:** neutral everyday or workplace settings (meetings, procurement, hiring, project reviews, news reading, household decisions). No real, named private individuals, no current partisan figures or parties, and no real company accused of anything. One or two sentences of setup, then the verdict, within 360 characters.
- **Plausible false twin:** keep the situation identical and swap the label for a neighbour that is easy to confuse (ad hominem vs tu quoque, straw man vs red herring, availability vs representativeness, affirming the consequent vs modus ponens, base-rate neglect vs conjunction fallacy), flip the verdict when it hinges on a stated condition (valid vs invalid, reasonable appeal to expertise vs fallacious), or swap the person, year, number, cause or direction of an effect. Never make the false statement by just adding "not".
- **One fact per pair**, and a different fact or situation for each pair in the run and from every pair already in the bank, whichever article it came from.
- **Statements:** declarative, 20–280 characters (360 for `scenario`), readable on a phone card. No exam phrasing ("Which of the following", "Choose two") and never "according to the article".
- **Evidence honesty:** never present a `contested` or `failed-replication` effect as established. If the article flags replication problems, that is itself a good `evidence` pair.
- **Dates and figures:** a study's sample size, effect size or result is only a `figure` pair, with `as_of` set and that year written into the true statement. Never undated.
- **Explanation:** 1–3 sentences in your own words saying why the true statement is true and what's wrong with the false one. Make it teach: name the tell-tale feature, the question to ask, or why the neighbouring label doesn't fit. No quote over 15 words.
- **Difficulty:** 1 = foundations (core definitions, classic examples), 2 = practitioner (spotting it in realistic situations, key distinctions, what to ask), 3 = advanced (evidence and replication, edge cases where the move is reasonable, formal subtleties).
- **Concepts:** the article's own id plus any graph node ids the fact involves (from the article's edges).

Then add them:

```bash
python3 scripts/generate.py add --input <file>
```

## 5. Validate, build, commit, push

```bash
python3 scripts/validate.py --source .source/critical-thinking-graph
python3 scripts/build_index.py
git add -A
git commit -m "<message>"
git pull --rebase origin main && git push origin main
```

- Make **one** commit for the whole run, containing every refresh and new pair, and push it once.
- If validation fails on a new or replacement pair, delete that pair's file, rewrite it once, and validate again. If it still fails, drop just that pair (remove its new file, or undo that refresh) and carry on, so the final commit always validates. Report dropped pairs in the run output.
- If validation says a new pair states the same fact as an existing one, the rewrite must test a different fact or situation from the article, not the same one reworded. If it flags two pairs that were both already in the bank, keep the older one and run `python3 scripts/refresh.py retire <newer id> --reason "duplicate of <older id>"`.
- Commit message subject: `quiz: refresh <r> pairs, +<n> pairs from <k> articles` (drop the part that is zero). In the body, list one line per pair (`ct-000123: verified` / `superseded by ct-000130` / `retired: <why>` / `added`).
- If the push is rejected, pull --rebase, re-run `build_index.py`, amend that same commit (don't add a second one) and push again (once).

## Don'ts

- Don't handle more than 100 pairs in one run, or write more than 3 pairs from one article in one run.
- Don't make more than one commit or push per run.
- Don't edit `index/` or `coverage/` by hand; `build_index.py` writes them.
- Don't delete question files or reuse an id; retire instead.
- Don't edit critical-thinking-graph from this run, and never commit `.source/`.
- Don't commit if validation fails.
