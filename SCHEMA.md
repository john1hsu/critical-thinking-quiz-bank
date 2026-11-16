# Question schema

Each true/false **pair** is one YAML file: `questions/<area>/<id>.yaml`. The folder names match the article domains in [critical-thinking-graph](https://github.com/john1hsu/critical-thinking-graph) (informal-fallacies, cognitive-biases, formal-logic, …). The quiz serves one side of a pair at random and never both sides in one session.

```yaml
id: ct-000002                     # stable, never reused
area: informal-fallacies          # = source article's domain = folder
kind: scenario                    # scenario | counter | definition | mechanism | evidence | origin | figure
topic: Ad hominem                 # the source article's title, shown after answering
topic_type: InformalFallacy       # the article's class: InformalFallacy, CognitiveBias, Technique, ReasoningForm, Person, ...
true_statement: A team lead dismisses a cost comparison because the analyst who wrote it once worked for the vendor, without checking its figures. That is an ad hominem.
false_statement: A team lead dismisses a cost comparison because the analyst who wrote it once worked for the vendor, without checking its figures. That is a straw man.
explanation: The lead attacks who made the case instead of its numbers, the mark of an ad hominem. A straw man would misstate the analyst's argument; here the argument is never engaged at all.
as_of: '2018'                     # only on figure pairs: the year the number is for
source:
  repo: john1hsu/critical-thinking-graph
  path: articles/informal-fallacies/ad-hominem.md
  commit: <source repo HEAD when written or last verified>
  blob: <git blob of the article at that point>
concepts: [ct:ad-hominem, ct:straw-man-fallacy]   # graph node ids; the source article's id comes first
related: []                       # optional: other pair ids
supersedes: ct-000041             # only on a pair that replaced an outdated one
difficulty: 2                     # 1 foundations | 2 practitioner | 3 advanced
created: '2026-11-16'
status: active                    # active | stale | retired
stale_reason: ...                 # only while stale
retired_reason: ...               # optional, on retired pairs
```

`schema/question.schema.json` has the same rules as a JSON Schema for editors.

## Kinds

Each pair says what it teaches. The first two practise the skill itself; the rest build the knowledge behind it. Every article that describes a move you can make or meet (fallacies, biases, heuristics, reasoning forms, schemes, techniques) gets at least one skill pair.

| kind | App label | Tests |
| --- | --- | --- |
| scenario | Spot it | A short, realistic everyday or workplace situation, and what it shows: which fallacy, bias, heuristic or form, or whether the reasoning holds |
| counter | Ask and counter | The critical question to ask, the check or debiasing technique to use, how to repair the argument, or when the move is actually reasonable |
| definition | What it is | What the idea is, and what it is not |
| mechanism | How it works | The form, the cognitive process, why it misleads or why it works |
| evidence | Evidence and replication | What research shows, replication status, the main critiques and limits |
| origin | Who and when | Who introduced it, where, and when |
| figure | Numbers and dates | A dated number (`as_of` required, and dated in the statement) |

## Lifecycle

Ideas about reasoning don't ship in releases, so a pair changes only when its source article does (for example, when a replication changes an effect's evidence status).

| Status | Meaning | In the quiz? |
| --- | --- | --- |
| active | Matches the latest version of its source article | Yes |
| stale | The source article changed (or disappeared) since the pair was verified | Only with `--include-stale` |
| retired | The fact changed (a newer pair `supersedes` it), the article is gone, or the pair repeated a fact another pair already tests | No |

## Checks (`scripts/validate.py`)

| Check | Fails when |
| --- | --- |
| Schema | A required field is missing, malformed or unknown |
| Unique ID | An ID repeats, or the file name or folder doesn't match |
| Kind | `kind` isn't one of the seven kinds |
| Dated figures | A `figure` pair has no `as_of`, `as_of` names no year, or the true statement doesn't mention it |
| Duplicate | A statement closely matches one in another non-retired pair |
| Same fact | Two non-retired pairs, from any articles, have true statements that state one fact in different words: most of their words match, or they share their numbers and most of the shorter statement's words |
| Pair quality | The two statements are identical or differ only by negation |
| Explanation | Shorter than 60 characters |
| Statement form | A statement is a question, under 20 characters, or over 280 (360 for `scenario`) |
| Source | Repo, path, commit or blob is malformed; with `--source`, the article's domain differs, a concept isn't an edge of the article, or an active pair's article is missing or changed (run `refresh.py mark-stale` first; stale pairs are exempt because they are waiting to be refreshed or retired) |
| Supersedes | Points to an ID that is missing or not retired |
| Exam-like wording | "Which of the following", "Choose two", "according to the article" and similar |
