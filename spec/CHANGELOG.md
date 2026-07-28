# Changelog

Written as supersessions rather than as a diff, because that is what the protocol says a change to a ratified position is. Every entry names the claim that was superseded, its replacement, and the reason — the three things §3 requires and the three things an ordinary changelog throws away.

The machine-readable form is [canon/](../canon/). This file is the prose rendering of the same commits.

---

## v0.2 — 2026-07-28

Five open positions closed. The version claim itself was superseded in the same commit as the fifth, because v0.2 exists exactly when the last position is ratified.

| Canon commit | Position | Superseded | Replacement |
|---|---|---|---|
| `cm_0002` | §8.1 extraction | `cl_0011` | `cl_0012`, `cl_0013` |
| `cm_0003` | §8.2 constraint evaluation | `cl_0021` | `cl_0022`, `cl_0023` |
| `cm_0004` | §8.3 federation | `cl_0031` | `cl_0032`, `cl_0033` |
| `cm_0005` | §8.4 proposal load | `cl_0041` | `cl_0042`, `cl_0043` |
| `cm_0006` | §8.5 reader enforcement | `cl_0051` | `cl_0052`, `cl_0053` |
| `cm_0006` | version | `cl_0001` | `cl_0003` |

### §8.1 — Extraction is an adapter, not part of the protocol

The protocol operates on claims. Turning prose into claims is pluggable, versioned, and carries its own model card.

*Why it changed:* putting extraction inside the spec would bound the spec's quality by model quality, which changes quarterly.

Machine-extracted claims default to `proposed` and can never be `binding` — extraction cannot create canon, it can only ask. Provenance records the extractor name and version. Re-validation sweeps become a first-class operation, and new conflicts surfacing after an extractor upgrade is correct behaviour rather than a regression.

### §8.2 — Constraint evaluation is dirty-set scoped

Never evaluate the full graph on the write path. Index by `(subject_type, predicate)`, collect touched subjects from the delta, expand by declared constraint dependency, evaluate only that closure. Cache verdicts on `(claim_set_hash, constraint_schema_version, branch_head)`.

*Why it changed:* canon graphs are small — a large franchise is on the order of 10⁵ claims. This is a write-latency problem, not a big-data problem, and treating it as the latter produces an architecture nobody needs.

### §8.3 — Federation is authority-scoped imports, and it is the licensing product

Submodules copy; imports reference; Datum uses imports. **Supersession rights are separable from read rights.** A licensee may read and propose against imported canon and may not supersede on the rights holder's `main`. Cross-boundary conflicts are advisory, cannot auto-resolve, and escalate to the rights holder.

*Why it changed:* copies fork silently and cannot express asymmetric rights.

This closure changed the business, not only the architecture. Rights holders and licensees maintaining a shared canon with asymmetric supersession rights under audit is the workflow currently executed by PDF style guides and approval emails. Federation is the commercial surface.

### §8.4 — Proposal load is managed by budget, corroboration, and delegated authority

Four mechanisms in order of cheapness: deduplicate by claim hash; per-agent ratification budgets with backpressure that queues rather than rejects; auto-ratification thresholds; curator delegation — scoped, audited, revocable. An agent's integrity score gates its delegated canon authority.

**Ratified with a known defect, recorded rather than discovered later.** Threat model [T2](threat-model.md) shows mechanism 1 counts corroboration by agent, which means the defence against volume poisoning *amplifies* collusion poisoning: fifty sockpuppet agents produce one proposal that arrives pre-endorsed. Corroboration must be weighted by independent provenance lineage. That correction is open against v0.3.

### §8.5 — Reader-side enforcement is policy, with a mandatory flag

`read` never silently hides contested canon. Three harness-selected modes — `permissive` (default), `strict`, `gate`. The `contested` flag must appear in the payload the model actually sees.

*Why it changed:* silently omitting canon is worse than returning disputed canon, and hard-failing generation over an unresolved dispute turns the tool into an obstacle.

The mandate is normative and unenforceable by the spec alone. Conformance vector [L1-004](../conformance/vectors/L1-read/L1-004.json) is what enforces it — see threat model T10.

### Still open at v0.2

Not deleted, not reworded, not quietly dropped. §8.6 carries three:

- **Temporal-inference extraction recall.** The dominant unknown in the system. Quantified by GREATGAME Task A.
- **Constraint expressiveness.** Narrative rules like "magic has a cost" resist formalization. Out of scope for v1, and a bound on detection coverage — therefore, per the threat model, a bound on security.
- **Canon poisoning under adversarial proposal load.** Now documented in the [threat model](threat-model.md) rather than resolved by it. T2, T5, and T6 are open.

### Added in v0.2

- [threat-model.md](threat-model.md) — ten threats, six adversaries, five trust boundaries, three open
- [../conformance/](../conformance/) — 39 vectors across six levels
- [../canon/](../canon/) — the specification versioned as Datum canon
- [../benchmark/](../benchmark/) — GREATGAME v0.1 specification and datasheet

---

## v0.1

Initial draft. Data model, constraints, supersession, the four-tool surface, merge semantics, canon drift score, domain bindings. Section 8 open.

Never published. It exists here as commit `cm_0001` in `canon/`, which is the point — reading canon `as_of cm_0001` returns the five positions as open questions, exactly as they stood.
