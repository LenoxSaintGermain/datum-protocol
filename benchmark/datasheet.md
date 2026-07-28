# GREATGAME — Datasheet

Following Gebru et al., *Datasheets for Datasets*. Written before the data exists, so that collection is constrained by the document rather than justified by it after the fact.

**Status: 0 of 50 instances annotated.** Every quantitative field below is marked `pending` and will be filled from measurement, not estimation. This datasheet ships empty on purpose — a datasheet written after the numbers are known is a press release.

---

## Motivation

**For what purpose was the dataset created?**

To measure whether an automated system can distinguish a *contradiction* from a *supersession* — a deliberate, explained change to what was previously true. This distinction is the entire basis of the Datum protocol (see [../spec/datum-v0.2.md](../spec/datum-v0.2.md) §3), and no existing benchmark measures it, because no existing system models supersession at all.

The secondary purpose is a dependency one: extraction quality cannot be measured without labels, the demo cannot be trusted without measurement, and the paper has no results section without either. This is the dependency root of the entire program.

**Who created it and who funded it?**

Third Signal Labs. Self-funded.

---

## Composition

**What do the instances represent?**

Each instance is one point of canon tension in the Doyle Sherlock Holmes corpus: a subject, a predicate, and one or more textual assertions about it, annotated with an adjudicated verdict.

**How many instances?**

Target 50. Ten additionally withheld as a held-out split, published as hashes only.

The anti-goal is stated in the benchmark spec and repeated here because it is the constraint most likely to be violated: **do not chase exhaustiveness.** Fifty well-annotated instances across all four classes beats three hundred cardinality violations. Work running past three weeks means literary scholarship has replaced engineering.

**Class distribution (target / actual):**

| Class | Target | Actual |
|---|---|---|
| `conflict` | ~40% | pending |
| `supersession` | ~20% | pending |
| `apparent` | ~30% | pending |
| `uncovered` | ~10% | pending |

The `apparent` class — passages that look contradictory and resolve on inspection — is the precision floor and the most tempting one to skip. Skipping it produces a benchmark that rewards over-flagging, which is the exact behavior that gets continuity tools uninstalled.

**Is any information missing?**

Yes, deliberately. Corpus text is not redistributed. Instances reference pinned, checksummed Project Gutenberg editions by character offset. Scholarly arguments are paraphrased and attributed, never reproduced.

**Does the dataset contain confidential or offensive content?**

The corpus is 19th-century popular fiction and contains period attitudes on race, empire, and gender that a contemporary reader will find objectionable. Instances are selected for canon consistency properties, not for content, and no filtering for period attitudes is applied. Users building generation systems on this corpus should not treat its contents as endorsed.

---

## Collection

**How was the data acquired?**

Candidate instances are transcribed from a century of existing Sherlockian scholarship — Knox (1911), Sayers (1946), Baring-Gould (1967), Klinger (2004-05), *The Baker Street Journal*, and competing published chronologies. The contradictions are already catalogued. This work is transcription of scholarly judgments, not the making of them.

**Who annotated, and how?**

Two annotators per instance, independent and blind to each other, following the decision tree in benchmark spec §7. Disagreements are adjudicated in a third pass and **recorded rather than erased**.

| Field | Value |
|---|---|
| Annotator A | pending |
| Annotator B | pending |
| Adjudicator | pending |
| Annotation period | pending |
| Cohen's κ, overall | pending |
| Cohen's κ, per class | pending |

κ is expected to be lowest on `apparent` vs `conflict`. That expectation is recorded here in advance so that the result cannot be presented as a surprise.

**Were scholarly reconciliations allowed to override annotation?**

No. A contradiction that scholars have explained away is still a contradiction in the text. Known reconciliations are logged under `scholarly_treatments` and populate the `resolutions` array of a `datum.check` verdict — they do not change the gold verdict. Conflating "resolvable" with "not a conflict" collapses the distinction the whole protocol is built on.

---

## Preprocessing

Project Gutenberg plain text, normalized for whitespace and encoding, then pinned and checksummed. Character offsets are authoritative and will silently rot against any other edition.

| Field | Value |
|---|---|
| Editions pinned | pending |
| Checksums recorded | pending |
| Normalization script | pending |

---

## Uses

**What tasks is it intended for?**

Three, scored separately, per benchmark spec §3:

- **Task A — Extraction.** Raw passage to claims. Measures the recall ceiling of any end-to-end system.
- **Task B — Detection.** Gold claims to verdicts. Measures constraint engine quality in isolation.
- **Task C — End-to-end.** Raw corpus to cited verdicts. The number that is actually true.

Task C is expected to be substantially worse than Task B. The gap *is* the extraction risk quantified. That is a finding, not an embarrassment, and reporting only C — or only B — is how a benchmark becomes unable to tell which component is broken.

**Headline metric.** Supersession Discrimination Rate:

```
SDR = correct(supersession) / ( correct(supersession) + supersession_misread_as_conflict )
```

**What should it not be used for?**

It should not be used to claim general canon-consistency performance. See limitations.

---

## Limitations

Stated before a reviewer states them, which buys more credibility than another ten instances.

- **Single author.** One writer's inconsistencies across one body of work. Multi-author canon — a writers' room, a regulatory body, a standards committee — is the actual commercial case and is not represented here at all.
- **One genre.** Victorian detective fiction. Nothing here transfers automatically to policy documents or engineering decision records, which the protocol claims to serve (spec §7).
- **English, and ~130 years old.** Prose register, sentence construction, and vocabulary are far from any modern production corpus. Extraction performance on this text is not a prediction of extraction performance on a series bible or a compliance manual.
- **Small.** Fifty instances supports comparison between systems. It does not support fine-grained per-hazard claims with confidence intervals anyone should trust. Per-hazard recall is reported as directional, not as measurement.
- **Scholarship is not ground truth.** Where a century of Sherlockians disagree, the annotation records a judgment. Those instances are marked `hard` and their disagreement is preserved rather than resolved.
- **Selection bias toward the catalogued.** Instances are drawn from contradictions scholars found interesting enough to write about. Contradictions no one noticed are, by construction, absent — which likely makes the benchmark easier than the real problem.

---

## Distribution and maintenance

| | |
|---|---|
| License | CC-BY-4.0 ([LICENSE](LICENSE)) |
| Repository | https://github.com/LenoxSaintGermain/datum-protocol |
| DOI | pending |
| Citation | see [../CITATION.cff](../CITATION.cff) |
| Maintainer | Third Signal Labs |
| Erratum process | GitHub issues; corrections are supersessions with a recorded reason, never silent edits |

A benchmark for a canon-governance company must have immaculate provenance on its own sources. That is not compliance overhead — it is the demo.
