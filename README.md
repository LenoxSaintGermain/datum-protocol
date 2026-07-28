# Datum

**A versioned canon layer for multi-agent systems.**

Third Signal Labs · Ground Truth Protocol

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

The design rule that governs everything: **agents get write access to proposals, never to truth.**

## The distinction the protocol is built on

Your agents cannot tell a contradiction from a deliberate change.

- Watson's wound moves from shoulder to leg → **error**. Nobody intended it.
- Holmes dies at Reichenbach, then didn't → **supersession**. Deliberate, explained, and the earlier state remains meaningful.

A system that flags both identically is useless in production, because it buries every intentional change in false alarms. In narrative this distinction is a retcon; in policy it is an amendment; in engineering it is a superseded ADR. Same operation, three domains — which is the argument that this is a primitive rather than a storytelling tool.

## Status

Pre-release. Nothing here has numbers attached to it yet, and this README will not claim otherwise.

| Artifact | State |
|---|---|
| Protocol specification v0.2 | drafted |
| GREATGAME benchmark specification v0.1 | drafted |
| Threat model | pending |
| Conformance suite | pending |
| Annotated benchmark instances | 0 / 50 |
| Reference implementation | not started |
| Measured results | none |

## Repository map

```
spec/          protocol specification, threat model, changelog
benchmark/     GREATGAME — canon-consistency benchmark (CC-BY-4.0)
conformance/   test vectors and runner for claiming Datum compliance
canon/         this specification, expressed as Datum canon
```

## Licensing

Apache-2.0 on the specification, conformance suite, and reference implementation. CC-BY-4.0 on the benchmark. See [NOTICE](NOTICE) for the reasoning.

Open the protocol, commercialize the product.
