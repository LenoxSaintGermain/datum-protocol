# Datum

**A versioned canon layer for multi-agent systems.**

What is true, since when, on whose authority.

Third Signal Labs · Ground Truth Protocol · [Specification v0.2](spec/datum-v0.2.md)

---

## The problem

Existing agent primitives are append-or-retrieve. None of them can detect that two things are both asserted and cannot both be true.

| Primitive | Answers | Versioned | Reconciles contradiction |
|---|---|---|---|
| Skills | how to do | via files | no |
| Canvas | what we're making | no | no |
| Memory | what happened with this user | no | no |
| **Datum** | **what is true, since when, on whose authority** | **yes** | **yes** |

In geodesy a datum is not discovered, it is agreed — and once agreed, every downstream measurement is validated against it. Move the datum and every coordinate is wrong.

The design rule that governs everything: **agents get write access to proposals, never to truth.** Autonomous systems can enrich canon at unlimited volume without any single one of them being able to corrupt it.

## The distinction it is built on

Your agents cannot tell a contradiction from a deliberate change.

- Watson's wound moves from shoulder to leg → **error**. Nobody intended it.
- Holmes dies at Reichenbach, then didn't → **supersession**. Deliberate, explained, and the earlier state remains meaningful.

A system that flags both identically is useless in production, because it buries every intentional change in false alarms. In narrative this distinction is a **retcon**; in policy and law an **amendment**; in engineering a **superseded decision record**. Same operation, three domains — which is the argument that this is a primitive rather than a storytelling tool.

Version control handles change. Nothing handles *deliberate change to what was previously true, where both the old and new state remain meaningful.*

## The protocol governs its own definition

Between v0.1 and v0.2, five open positions were closed. They are not recorded here as a diff. They are recorded as **supersessions** in [canon/](canon/) — the specification, expressed as Datum data.

```
read canon as_of cm_0001   →   the five §8 positions are "open"
read canon at HEAD         →   "resolved", each with a reason and a superseding claim
```

Both states are true. Neither overwrote the other. Nothing was deleted. And three positions in §8.6 are *still* open at HEAD, because a canon that shows its own unfinished edges is worth more than a clean board.

CI enforces the rule that makes this real: **no pull request may change `spec/` without also changing `canon/`.** A silent edit to a ratified position fails the build.

## What is here

| | |
|---|---|
| [spec/datum-v0.2.md](spec/datum-v0.2.md) | The protocol. Data model, constraints, supersession, four MCP-native tools, merge semantics, canon drift score, domain bindings. |
| [spec/threat-model.md](spec/threat-model.md) | Ten threats, six adversaries, five trust boundaries. Three open against v0.2 and named as open. |
| [spec/CHANGELOG.md](spec/CHANGELOG.md) | v0.1 → v0.2 written as supersessions, not as a diff. |
| [benchmark/](benchmark/) | GREATGAME — a canon-consistency benchmark over the Doyle Holmes corpus, plus the pinned corpus builder and annotation harness. CC-BY-4.0. |
| [conformance/](conformance/) | 39 vectors across six levels, a runner, and an adapter interface. |
| [canon/](canon/) | This specification, as canon. |

## Conformance

A specification tells you what an implementation should do; a conformance suite tells you whether it did.

```bash
python3 -m conformance.runner.run --adapter mock
```

Six levels, badged as **Datum v0.2 Core** (L1–L4) and **Datum v0.2 Complete** (L1–L6). Results report per level, so a partial implementation can state precisely what it has earned.

The bundled mock adapter is deliberately partial — it passes L1–L3 and fails L4–L6, and CI asserts that exact profile on every push. A conformance suite that has never reported a failure has not been tested.

## Status

Pre-release, and quiet on purpose. **No results exist yet, and this README will not imply otherwise.**

| Artifact | State |
|---|---|
| Protocol specification v0.2 | ✅ published |
| Threat model | ✅ published, three threats open |
| Conformance suite | ✅ 39 vectors, runner, mock adapter |
| Self-hosted canon | ✅ 7 commits, 5 supersessions |
| GREATGAME specification v0.1 | ✅ published |
| Corpus pinned and checksummed | ✅ 60 works, 3.72M chars, reproducible |
| Annotation harness | ✅ two-pass, blind, κ per class |
| Candidate instances | 🟡 6 located, 5 ready to annotate |
| Annotated benchmark instances | ⬜ 0 / 50 |
| Extraction harness and baselines | ⬜ not started |
| Reference implementation | ⬜ not started |
| Supersession Discrimination Rate | ⬜ **not measured** |

The headline claim — that no existing system scores above chance on supersession discrimination — is a hypothesis until GREATGAME says otherwise. Everything above the line is construction. Nothing gets promoted before there is a number.

## Threat model, briefly

Three threats are open against v0.2. Naming them is cheaper than being asked:

- **T2 — corroboration collusion.** §8.4 calls corroboration count "signal, not noise," which means the defence against volume poisoning *amplifies* collusion poisoning. Corroboration must be weighted by independent provenance lineage, not agent count.
- **T5 — provenance forgery.** `provenance.source` is self-reported free text. The citation guarantee is the protocol's credibility claim, and nothing yet binds a claim's stated origin to its actual one.
- **T6 — supersession abuse.** Supersession by design does not raise a conflict. That sentence is also a complete description of the exploit: anyone holding the right holds a sanctioned path to retire canon without tripping detection. Auditable, not preventable.

A threat model where everything is mitigated is marketing. See [the full document](spec/threat-model.md), including what Datum explicitly does **not** defend against — starting with a compromised authorized principal, which is the design and not a gap.

## Licensing

Apache-2.0 on the specification, conformance suite, and reference implementation. CC-BY-4.0 on the benchmark. See [NOTICE](NOTICE) for the reasoning, and [CONTRIBUTING.md](CONTRIBUTING.md) for how changes are proposed and ratified — which is the protocol, applied to itself.

Open the protocol, commercialize the product.
