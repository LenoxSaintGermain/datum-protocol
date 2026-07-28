# The specification, as canon

This directory holds the Datum specification expressed as Datum data. The protocol governs its own definition.

This is not decoration. It is the cheapest available answer to the question a protocol always gets asked — *has anyone actually used this?* — and it is answered in the one way that cannot be staged: the commit log is a byproduct of writing the spec, not a demo built afterward.

## The claim this directory makes

Between v0.1 and v0.2, five open positions in §8 were closed. In an ordinary repository that is a diff: the questions disappear and the answers appear, and the fact that a question was ever open survives only in prose nobody reads.

Here, the five closures are recorded as **supersessions**. The `status: "open"` claims still exist. They are marked `superseded`, they carry a `superseded_by` pointer and a recorded reason, and they are retrievable at any prior `as_of`. Nothing was deleted, because canon does not forget — it supersedes (spec §3, §5).

Which means the demo is a diff you can run yourself:

| Read at | The five §8 positions read |
|---|---|
| `cm_0001` (v0.1) | `open` |
| `HEAD` (v0.2) | `resolved`, each with a reason and a superseding claim |

Both states are true. Neither overwrote the other. That is the distinction the entire protocol exists to make, applied to the protocol.

**And three positions are still open.** §8.6 — temporal-inference extraction recall, constraint expressiveness, and canon poisoning under adversarial load — remain `status: "open"` at HEAD. A canon showing its own unfinished edges is more convincing than a clean board, and hiding them would be exactly the drift the protocol is built to catch.

## Files

| File | Contents |
|---|---|
| `schema.json` | JSON Schema for all five stores. Formalizes spec §1.1–1.5. |
| `nodes.json` | Sections, positions, primitives, tools |
| `claims.json` | The atomic units. This is where supersession is visible. |
| `edges.json` | Typed relations between nodes |
| `commits.json` | The canon commit DAG |
| `branches.json` | Branch pointers, including `apocrypha/rejected-alternates` |

## The domain binding

A `spec` binding in the sense of §7 — the same engine, a different vocabulary:

| | Narrative | **This repository** |
|---|---|---|
| Node types | character, location, event | **section, position, primitive, tool** |
| Binding source | series bible | **the ratified specification** |
| Apocrypha | Legends, fan canon | **designs considered and rejected** |
| Supersession | retcon | **a closed open question** |

If a canon of protocol positions and a canon of fictional characters run on the same engine without modification, the domain-agnostic claim in §7 has one more piece of evidence behind it than an assertion.

## Cross-checking git against canon

Every git commit that changes canon carries trailers:

```
Datum-Commit: cm_0003
Datum-Authority: binding
Datum-Supersedes: cl_0021
```

So the two logs verify each other, by hand, in one command:

```bash
git log --format='%H%n%b' | grep -A2 'Datum-Commit'
```

Each trailer must correspond to an entry in `commits.json`, and each `Datum-Supersedes` claim must be `status: "superseded"` in `claims.json` with a matching `superseded_by`. A mismatch is a defect. CI checks it.

## What is enforced today

The CI gate at `.github/workflows/canon-gate.yml` enforces four things now: canon files validate against the schema, conformance vectors validate against theirs, the conformance suite produces its expected result profile, and **no pull request may change `spec/` without also changing `canon/`.**

That last rule is the self-governance property in its enforceable form. It has been tested in both directions: a pull request touching only `spec/` is rejected, and the same pull request passes once `canon/` is touched. A gate that has never been made to fail is decoration.

**Its known limitation, stated rather than left to be discovered.** The rule is path-based. It checks that files under `canon/` changed — not that the *claims* changed coherently with the spec edit — so it is satisfiable by editing this README. That is a real gap, and it has the same shape as the coverage problem in §6: the check is cheap and honest about what it covers, and low coverage mistaken for conformance is the failure worth naming precisely rather than vaguely.

What closes it: running `datum.check` against this canon so a proposed spec change is validated against standing positions. That needs the reference implementation and arrives with it. Claiming that capability now would be the one unforced error available in this repository.
