# Annotation runbook

The §7 workflow, as commands. Read [greatgame-v0.1.md](greatgame-v0.1.md) §5–§7 first — this file assumes it.

**Budget: two weeks. Hard stop at three.** If this runs past week 3 you have started doing literary scholarship instead of building a company. Fifty well-annotated instances across all four classes beats three hundred cardinality violations, and the class distribution matters more than the count.

## 0. Build the corpus

```bash
python3 benchmark/corpus/build.py
```

Reconstructs 60 works — 4 novels, 56 stories — from nine pinned Project Gutenberg editions into `benchmark/corpus/texts/`, which is gitignored. The text is never committed; the checksums are.

```bash
python3 benchmark/corpus/build.py --verify
```

Run this before any annotation session and after any environment change. Every `char_span` in the dataset is an offset into *this exact normalized text*. In another edition those offsets point at the wrong words, silently, and you will not find out until someone tries to reproduce your numbers.

## 1. Write candidates

A candidate is a located tension: subject, predicate, and the assertions in play, each with a verified `char_span`. It carries **no** `class`, `gold_verdict`, `difficulty`, or `hazards` — those are the annotators' calls, and a candidate that pre-labels itself has contaminated the annotation before it starts.

Six candidates are already in `benchmark/candidates/`, covering the §9 starting set.

Sources for more, per §9: Knox (1911), Sayers (1946), Baring-Gould (1967), Klinger (2004–05), the *Baker Street Journal*, and competing published chronologies. **The contradictions are already catalogued — you are transcribing scholarly judgments, not making them.** Where two chronologies disagree you have a `hard` instance with documented human dissent, which is worth more than another easy one.

Watch the class balance while writing candidates, not after. `apparent` is 30% of the target and the class most likely to be under-collected, because looking for contradictions does not surface passages that merely look like contradictions. Go find them deliberately.

## 2. Two independent passes

```bash
python3 benchmark/annotate.py annotate --annotator A
python3 benchmark/annotate.py annotate --annotator B
```

Different people. Blind to each other — the tool will not show you the other pass and will not let you re-open an instance you have already labelled. Progress saves per instance, so stopping mid-session costs nothing.

The decision tree is printed at the start of every session and runs in order:

1. Two assertions, same subject and predicate, holding simultaneously with different values? → no: `uncovered`, or discard
2. Same referent, same time, equal authority? → no: `apparent`, and record why it resolves
3. Later assertion carries an in-world explanation of the change? → yes: `supersession`
4. Otherwise → `conflict`, with constraint type and severity

**A known scholarly reconciliation does not override the annotation.** The tool shows treatments and then makes you run the tree anyway. A contradiction that scholars have explained away is still a contradiction in the text, and a canon system must surface it before a human can rule on it — that is exactly the `resolutions` array in `datum.check`. Conflating "resolvable" with "not a conflict" collapses the distinction the entire protocol is built on.

`narrator_belief` is the field that makes supersession tractable. Watson asserting something he believed at the time is not the text asserting it as fact.

## 3. Adjudicate

```bash
python3 benchmark/annotate.py adjudicate --adjudicator <name>
```

Agreements finalize automatically. Disagreements stop and ask why the two annotators differed, and **the reason is recorded on the instance rather than erased.** The disagreements are data: they are where the class boundaries are genuinely unclear, and a reader deciding whether to trust this benchmark will look at them first.

## 4. Report agreement

```bash
python3 benchmark/annotate.py kappa
```

Cohen's κ overall and per class, one-vs-rest, plus the confusion matrix. Classes nobody assigned report `n/a` rather than a spurious 1.000.

**Expect the lowest κ on `apparent` vs `conflict`.** That expectation is recorded in the datasheet in advance, so the result cannot be presented afterwards as a surprise. If κ comes in high across the board, check that the annotators were actually blind before celebrating.

## 5. Hold out and validate

```bash
python3 benchmark/annotate.py holdout --n 10
python3 benchmark/annotate.py validate
```

`holdout` marks ten instances and writes their SHA-256 digests to `instances/holdout.json`. The instances are withheld from the public release; the digests let anyone verify after the fact that the split was fixed in advance rather than chosen once the scores were known. The seed defaults to 1911 — Knox.

`validate` checks every `char_span` against the pinned manifest, that `class` and `gold_verdict` agree, and that no scholarly summary has grown long enough to be a reproduction rather than a paraphrase.

## Status at any time

```bash
python3 benchmark/annotate.py status
python3 benchmark/annotate.py show gg_003
```

`status` reports counts, outstanding disagreements, and class distribution against target with an off-target flag. `show` prints an instance with its passages pulled live from the pinned corpus.

## Copyright

Corpus: public domain, redistribute freely — though this repository doesn't, in favour of pinned checksums.

Scholarship: Knox, Sayers, Baring-Gould, Klinger, and BSJ articles are **under copyright**. Paraphrase arguments, attribute every one, reproduce nothing. `scholarly_treatments.summary` is written in your own words. Verbatim scholarly text is a defect in the dataset, not a citation, and `validate` flags summaries long enough to be suspect.

A benchmark for a canon-governance company must have immaculate provenance on its own sources. That is not compliance overhead — it is the demo.
