# Candidates

A candidate is a **located tension**, not a labelled one: a subject, a predicate, and the assertions in play, each carrying a `char_span` verified against the pinned corpus.

Candidates deliberately carry no `class`, `gold_verdict`, `difficulty`, or `hazards`. Those are the annotators' calls. A candidate that arrives pre-labelled has contaminated the annotation before it starts, and the κ it produces measures nothing.

## What is here

Six candidates covering the §9 starting set. Every span was located by search against the pinned text and verified to resolve — none were transcribed from memory or from a secondary source.

| id | subject · predicate | sources | note |
|---|---|---|---|
| `gg_001` | Watson · wound_location | STUD, SIGN | The founding example. One Jezail bullet, two body parts. |
| `gg_002` | Watson · given_name | STUD, TWIS | Signs himself John H.; his wife calls him James. |
| `gg_003` | Holmes · status | FINA, EMPT | Reichenbach. The payoff case. |
| `gg_004` | Holmes · university | GLOR, MUSG | Neither passage names it. Likely `uncovered`. |
| `gg_005` | Moriarty · given_name | FINA | **Incomplete** — see below. |
| `gg_006` | Watson · marital_status | SIGN, FINA | Entry point to the marriages problem. |

Five are ready to annotate.

## gg_005 is incomplete on purpose

The Moriarty-brothers problem is that the Colonel is named James and the Professor appears to be named James too. FINA gives the Colonel plainly — *"the recent letters in which Colonel James Moriarty defends the memory of his brother."*

**The second attribution was searched for in the pinned editions and not found.** FINA, EMPT, and VALL contain no "James Moriarty" referring to the Professor.

That leaves two possibilities, and they are very different instances:

- it lives in a story not yet searched, in which case locate it and the candidate completes normally; or
- it is a scholarly inference rather than a textual assertion, in which case this is not a two-assertion conflict at all — it may be `uncovered`, with the Great Game argument belonging in `scholarly_treatments`.

Resolve which before labelling. Shipping it as a conflict because the reputation of the problem says it is one would be exactly the failure this benchmark exists to measure.

## Adding candidates

Locate the passage by searching `benchmark/corpus/texts/`, take the exact match bounds, and check it resolves:

```bash
python3 benchmark/annotate.py validate
python3 benchmark/annotate.py show gg_00N
```

`validate` rejects a span that runs past the end of its work or names a source outside the pinned manifest. `show` prints the passage in context so you can confirm the offsets point at the words you meant.

Do not write a `char_span` you have not seen resolve. That is the one error in this dataset that is invisible at review time and fatal at reproduction time.
