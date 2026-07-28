# Contributing

This repository is governed by the protocol it defines. The rules below are not analogy — they are the same operations, applied to the specification.

## The mapping

| Datum | Here |
|---|---|
| `datum.propose` | open a pull request |
| proposal branch | your branch |
| `datum.commit` | merge, by a maintainer |
| binding authority | maintainer review |
| supersession | changing a position the spec already took |
| apocrypha | designs considered and rejected, kept in `canon/` |

**Anyone may propose. Only a maintainer may ratify.** That asymmetry is the protocol's central safety property (§4.3), and it applies to agents and humans identically here. Agent-authored pull requests are welcome and are held to exactly the same bar.

## Changing the specification

**A change to `spec/` must come with a change to `canon/`.** CI enforces this and will fail your pull request otherwise.

The specification is versioned as canon in [canon/](canon/). A normative statement is a claim; changing a claim requires a commit with an authority and, where it reverses a prior position, a recorded reason.

**Reversing a position is a supersession, not an edit.** Do not delete the old claim and do not reword it into the new one. Mark it `superseded`, point `superseded_by` at its replacement, and write down why it changed.

```json
{
  "id": "cl_0041",
  "predicate": "status",
  "value": "open",
  "status": "superseded",
  "superseded_by": "cl_0042",
  "supersession_reason": "Ratified in v0.2 section 8.4. Threat model T2 finds mechanism 1 exploitable as written; the correction is open against v0.3."
}
```

A supersession with no recorded reason is a deletion wearing supersession's clothes, and the validator rejects it. This is threat model [T6](spec/threat-model.md) applied to the repository — the mechanism that makes deliberate change safe is the same mechanism that makes quiet removal easy, so the reason field is the whole defence.

Add a `Datum-Commit:` trailer to your git commit so the two logs stay mutually verifiable:

```
Datum-Commit: cm_0008
Datum-Authority: binding
Datum-Supersedes: cl_0042
```

**Deletion is a smell** (§5). Canon does not forget. If you think something should be removed rather than superseded, say why in the pull request — legal removal is the only sanctioned case.

## Before you open a pull request

```bash
python3 -m conformance.runner.validate
python3 -m conformance.runner.run --adapter mock --expect-profile L1-read,L2-check,L3-supersession
```

Both must pass. The second asserts the mock's *exact* profile, so if your change makes a previously-failing level pass, that is either a real fix to the mock — update the expected profile and say so — or a vector that stopped testing anything.

## Adding conformance vectors

Every vector must trace to a normative statement via its `requirement` field. A vector with no requirement is an opinion about implementation rather than a test of the specification, and the validator rejects it.

New vectors are welcome, especially ones that catch a real implementation being subtly wrong. If you found it by breaking something, put that in the `rationale`.

## Benchmark instances

`benchmark/instances/` follows a stricter process, in [greatgame-v0.1.md §7](benchmark/greatgame-v0.1.md): two independent annotators, blind to each other, disagreements adjudicated in a third pass and recorded rather than erased.

Reproduce no copyrighted scholarly text. `scholarly_treatments.summary` is written in your own words, with attribution. Verbatim text from Knox, Sayers, Baring-Gould, Klinger, or the *Baker Street Journal* is a defect in the dataset — report it as an issue and it will be fixed.

## Reporting a security issue

Threat model findings are welcome as public issues. Three threats are already open against v0.2 and named as open — [T2](spec/threat-model.md) corroboration collusion, [T5](spec/threat-model.md) provenance forgery, [T6](spec/threat-model.md) supersession abuse. A fourth would be genuinely useful.

There is no embargo process, because there is nothing deployed to embargo yet.

## Licensing

Contributions to `spec/`, `conformance/`, and `canon/` are Apache-2.0. Contributions to `benchmark/` are CC-BY-4.0. By opening a pull request you agree your contribution ships under the license covering the directory you touched. See [NOTICE](NOTICE).
