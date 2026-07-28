# GREATGAME v0.1 — Benchmark Specification

**A canon-consistency benchmark for automated contradiction and supersession detection**

Third Signal Labs · Ground Truth Protocol · Draft 0.1

---

## 0. Why this exists first

Extraction cannot be measured without labels. The demo cannot be trusted without measurement. The paper has no §7 without either. This is the dependency root, and it is also the only artifact here that stays citable if the product never ships.

Named for the Sherlockian "Great Game" — the century-long scholarly practice of reconciling Doyle's contradictions by hand. The benchmark measures whether a system can do automatically what human scholars have been doing since 1911.

*(Alternate name if GREATGAME reads too playful for a paper: `CANON-50`. Keep GREATGAME for the release, use the formal name in the abstract.)*

---

## 1. The discriminative test

Most of the value is not "find contradictions." Any system that flags aggressively scores well on that.

**The real test: distinguish a contradiction from a supersession.**

- Watson's wound moves from shoulder to leg → **error**. Nobody intended it. Blocking.
- Holmes dies at Reichenbach, then didn't → **supersession**. Deliberate, in-world explained, and the earlier state remains true-as-believed.

A system that flags both identically is useless in production, because it will bury every ratified canon change in false alarms. Every design decision below serves this discrimination.

---

## 2. Corpus

- **Texts:** the full Doyle Holmes canon — 4 novels, 56 short stories. Public domain in the US as of January 1, 2023.
- **Source:** Project Gutenberg plain text, normalized. Pin the exact editions and checksum them; annotations reference character offsets and will silently rot otherwise.
- **Citation convention:** the standard four-letter Jay Finley Christ abbreviations — STUD, SIGN, FINA, EMPT, TWIS, SCAN, HOUN, MUSG, SPEC, REDH. Non-negotiable. It makes the dataset instantly legible to the scholarly community whose work it rests on, and it is how every source you will draw from cites.

---

## 3. Three tasks, scored separately

Scoring end-to-end only is how you end up unable to tell which component is broken.

| Task | Input | Output | Measures |
|---|---|---|---|
| **A — Extraction** | Raw passage | Claims (subject, predicate, value, effective interval) | Recall ceiling of the whole system |
| **B — Detection** | Gold claim set | Conflict / supersession / conform verdicts | Constraint engine quality |
| **C — End-to-end** | Raw corpus | Cited verdicts | The number that is actually true |

Expect C to be substantially worse than B. **Report all three.** The gap between B and C *is* the extraction risk from the paper's §8.1, quantified — that's a finding, not an embarrassment.

---

## 4. Instance schema

```json
{
  "id": "gg_003",
  "class": "conflict",
  "constraint_type": "cardinality",
  "subject": "Watson",
  "predicate": "wound_location",
  "assertions": [
    {
      "value": "shoulder",
      "source": "STUD",
      "locator": { "chapter": 1, "char_span": [4120, 4198] },
      "authority": "binding",
      "narrator_belief": true,
      "explicit": true
    },
    {
      "value": "leg",
      "source": "SIGN",
      "locator": { "chapter": 1, "char_span": [880, 942] },
      "authority": "binding",
      "narrator_belief": true,
      "explicit": true
    }
  ],
  "gold_verdict": "conflict",
  "severity": "blocking",
  "difficulty": "easy",
  "hazards": [],
  "scholarly_treatments": [
    {
      "summary": "Paraphrased account of the proposed reconciliation",
      "attributed_to": "Author, Work, Year",
      "type": "derived_reconciliation",
      "accepted_by_annotators": false
    }
  ],
  "notes": ""
}
```

Rules:

- `char_span` is authoritative; quoted text is never stored beyond a short locator excerpt (see §9).
- `narrator_belief` matters. Watson asserting something he believed at the time is different from Doyle asserting it as fact. This field is what lets a system reason about supersession correctly.
- `scholarly_treatments` are **paraphrased summaries with attribution**, never reproduced argument text.

---

## 5. Instance classes

A benchmark of contradictions alone measures recall and nothing else — a system that flags every passage scores perfectly. Four classes, all required.

| Class | What it is | Gold verdict | Target share |
|---|---|---|---|
| `conflict` | Genuine contradiction, no authorial intent | `conflict` | ~40% |
| `supersession` | Deliberate canon change, in-world explained | `supersession` | ~20% |
| `apparent` | Looks contradictory, resolves on inspection — different referent, different time, different speaker | `conform` | ~30% |
| `uncovered` | Canon takes no position; a plausible assertion the corpus never addresses | `uncovered` | ~10% |

**The `apparent` class is the precision floor and the most tempting one to skip.** Skip it and your benchmark rewards over-flagging, which is the exact behavior that makes continuity tools get uninstalled.

---

## 6. Difficulty and hazard tags

**Difficulty:**

- `easy` — both assertions explicit, same predicate, stated in plain text
- `medium` — one assertion implicit, or requires resolving a pronoun or epithet
- `hard` — requires temporal inference, cross-story chaining, or world knowledge

**Hazards** (drive Task A error analysis):

`implicit` · `pronoun` · `epithet` · `cross_story` · `temporal_inference` · `dialogue_attribution` · `unreliable_narrator` · `numeric`

Report per-hazard recall. "Extraction recall is 0.71" is a number; "extraction recall collapses to 0.34 on temporal inference" is a paper.

---

## 7. Annotation guidelines

**Decision tree for every candidate instance:**

1. Do two assertions about the same subject and predicate hold simultaneously with different values?
   → No: `uncovered` or discard.
2. Do they in fact refer to the same referent, at the same time, at equal authority?
   → No: `apparent`. Record why it resolves.
3. Is the later assertion accompanied by an in-world explanation of the change?
   → Yes: `supersession`. Record the explanatory passage.
4. Otherwise: `conflict`. Assign constraint type and severity.

**Process:**

- Two annotators per instance, independent, blind to each other.
- Adjudicate disagreements in a third pass; record the disagreement rather than erasing it.
- Report Cohen's κ per class. Expect it to be lowest on `apparent` vs `conflict` — say so in the paper.
- Where a well-known scholarly reconciliation exists, log it under `scholarly_treatments` but **do not let it override the annotation.** A contradiction that scholars have explained away is still a contradiction in the text, and a canon system must surface it before a human can rule on it. This is exactly the `resolutions` array in `datum.check`, and conflating "resolvable" with "not a conflict" collapses the distinction the whole protocol is built on.

**Anti-goal:** do not chase exhaustiveness. Fifty well-annotated instances across all four classes beats three hundred cardinality violations. If this work runs past three weeks, you have started doing literary scholarship instead of building a company.

---

## 8. Scoring

**Task A:** precision, recall, F1 on claim tuples. Partial credit for correct subject+predicate with wrong value; report separately.

**Task B and C:** macro-F1 across the four classes — macro, not micro, so the small `supersession` class cannot be ignored for free.

**Headline metric — Supersession Discrimination Rate:**

```
SDR = correct(supersession) / ( correct(supersession) + supersession_misread_as_conflict )
```

This is the number to lead with. It is the one no existing system can score above chance on, because none of them model supersession at all.

**Also report:** coverage (share of gold assertions the system had any position on) alongside every drift figure. Low drift at low coverage is ignorance wearing conformance's clothes.

---

## 9. Sources for candidate instances

The contradictions are already catalogued. You are transcribing scholarly judgments, not making them.

| Source | Use |
|---|---|
| Ronald Knox, *Studies in the Literature of Sherlock Holmes* (1911) | Founding text of the Great Game. Cite it in the paper's opening. |
| Dorothy L. Sayers, *Unpopular Opinions* (1946) | Includes the Watson given-name reconciliation — a clean `derived` example |
| William S. Baring-Gould, *The Annotated Sherlock Holmes* (1967) | Largest compilation of chronological problems; primary mine for `temporal` instances |
| Leslie Klinger, *The New Annotated Sherlock Holmes* (2004–05) | Modern annotations; good for `apparent` instances where a seeming conflict resolves |
| *The Baker Street Journal* | Ongoing venue; useful for disputed cases where scholars disagree — those make excellent `hard` instances |
| Competing published chronologies | Where two chronologies disagree, you have a temporal conflict with documented human dissent |

**Start here:** Watson's wound (STUD/SIGN), Watson's given name (TWIS), Reichenbach and the Great Hiatus (FINA/EMPT), Watson's marriages, Holmes's university, the Moriarty brothers' names. That is roughly a dozen instances in the first week and covers three of the four classes.

---

## 10. Licensing and attribution

- **Corpus:** public domain. Redistribute freely.
- **Annotations:** release CC-BY. This is the asset; make it maximally citable.
- **Scholarship:** Knox, Sayers, Baring-Gould, Klinger, and BSJ articles are under copyright. Paraphrase arguments, attribute every one, reproduce nothing. `scholarly_treatments.summary` is written in your own words — treat any verbatim text as a defect in the dataset.

A benchmark for a canon-governance company must have immaculate provenance on its own sources. That is not compliance overhead; it is the demo.

---

## 11. Release checklist

- [ ] 50 instances, distribution per §5
- [ ] Two annotators, adjudicated, κ reported per class
- [ ] Pinned and checksummed corpus editions
- [ ] Held-out split: 10 instances withheld, published as hashes only
- [ ] Baselines run: naive LLM prompt, retrieval + LLM, Datum
- [ ] Datasheet — motivation, composition, collection, limitations, known gaps
- [ ] Repository, DOI, CC-BY license, citation block
- [ ] Explicit statement of what the benchmark does **not** measure: single-author corpus, one genre, English, ~130-year-old prose

That last item matters. Naming your limitations before a reviewer does buys more credibility than another ten instances.
