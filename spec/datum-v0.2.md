# DATUM v0.2 — Protocol Specification

**A versioned canon layer for multi-agent systems**

Third Signal Labs · Ground Truth Protocol · Draft 0.2

---

## 0. Position

Existing agent primitives are append-or-retrieve. None of them can detect that two things are both asserted and cannot both be true.

| Primitive | Answers | Versioned | Reconciles contradiction |
|---|---|---|---|
| Skills | how to do | via files | no |
| Canvas | what we're making | no | no |
| Memory | what happened with this user | no | no |
| **Datum** | **what is true, since when, on whose authority** | **yes** | **yes** |

Datum is the reference frame. In geodesy a datum is not discovered, it is agreed — and once agreed, every downstream measurement is validated against it. Move the datum and every coordinate is wrong.

**Design rule that governs everything below: agents get write access to proposals, never to truth.**

---

## 1. Data model

### 1.1 Node

A typed entity in the canon graph. Types are domain-defined; the engine treats them opaquely.

```json
{
  "id": "nd_7f3a2c",
  "type": "character",
  "label": "Rin",
  "branch": "main",
  "created_in": "cm_0001",
  "status": "canon"
}
```

`status`: `canon` | `superseded` | `apocryphal` | `proposed`

### 1.2 Claim

The atomic unit of truth. Nodes are containers; **claims are what conflict.**

```json
{
  "id": "cl_9b21",
  "node": "nd_7f3a2c",
  "predicate": "eye_color",
  "value": "green",
  "effective": { "from": "ev_birth", "to": null },
  "authority": "binding",
  "provenance": {
    "source": "series-bible-v3",
    "asserted_by": "user:lenox",
    "commit": "cm_0044"
  },
  "status": "canon"
}
```

**`authority` tiers — the dimension git does not have:**

| Tier | Meaning | Binds generation | Can be contradicted by |
|---|---|---|---|
| `binding` | Ratified canon | yes | binding only |
| `derived` | Computed from binding claims | yes | binding |
| `proposed` | Awaiting ratification | no | anything |
| `apocryphal` | Exists, does not bind (Legends, draft guidance, fan wiki) | no | n/a — never conflicts |

Authority is what makes this a *canon* layer rather than a knowledge graph. Two sources disagreeing is not automatically a conflict — it is a conflict only when they carry equal binding force.

### 1.3 Edge

```json
{ "id": "eg_331", "from": "nd_7f3a2c", "to": "nd_11b0", "type": "loyal_to", "authority": "binding" }
```

### 1.4 Commit

Atomic change set. Parents form a DAG, not a tree — merge is a first-class operation.

```json
{
  "id": "cm_0102",
  "parents": ["cm_0101"],
  "author": "user:lenox",
  "authority": "binding",
  "message": "Ratify Rin's pre-Fall timeline",
  "changes": [ /* claim/node/edge deltas */ ],
  "supersedes": []
}
```

### 1.5 Branch

Named pointer to a commit. Conventional branches:

- `main` — ratified canon
- `proposal/*` — agent- or human-authored candidate changes
- `draft/*` — long-lived exploratory canon (an unaired season, a pending policy revision)
- `apocrypha/*` — deliberately non-binding material

---

## 2. Constraints

A constraint is a rule that a claim set can violate. Constraints are declared per node type and are the entire basis of contradiction detection.

| Type | Violated when | Default severity |
|---|---|---|
| `cardinality` | A single-valued predicate carries two live values | blocking |
| `domain` | Value falls outside declared enumeration or range | blocking |
| `temporal` | Effective intervals overlap with different values, or event ordering inverts | blocking |
| `exclusion` | Two claims declared mutually exclusive both hold | blocking |
| `referential` | Edge or claim references a node not canon on this branch | blocking |
| `derivation` | A `derived` claim's inputs changed and it was not recomputed | advisory (stale) |
| `authority` | A lower-tier claim contradicts a higher-tier claim | advisory (lower tier simply does not bind) |

Declaration example:

```yaml
type: character
constraints:
  - predicate: eye_color
    kind: cardinality
    max: 1
  - kind: temporal
    rule: no_claim_effective_after(predicate: "*", event: "death")
  - kind: exclusion
    claims: [status=alive, status=dead]
```

---

## 3. Supersession — the primitive nobody has

Version control handles *change*. Canon requires **deliberate change to what was previously true, where both the old and new state remain meaningful.**

- In narrative this is a **retcon**.
- In policy and law this is an **amendment**.
- In engineering this is a **superseded ADR**.

Same operation, three domains. This is the strongest evidence that Datum is a primitive rather than a storytelling tool.

A supersession commit:

1. Marks target claims `status: superseded` — never deletes them
2. Records `superseded_by`, a reason, and the ratifying authority
3. Suppresses the old claims from `datum.read` at `HEAD`, while leaving them retrievable at any prior `as_of`
4. **Does not raise a conflict** — supersession is the sanctioned path for contradiction

Without this, every intentional canon change looks identical to an error. That distinction is the difference between a system of record and a pile of documents.

---

## 4. Tool surface

Four tools. MCP-native.

### 4.1 `datum.read`

Retrieve canon context. This is the layer Lorebook-class products stop at.

```json
{
  "query": "Rin's relationship to the Fall",
  "node_ids": [],
  "branch": "main",
  "as_of": null,
  "depth": 2,
  "authority_floor": "derived",
  "max_tokens": 4000
}
```

- `as_of` — commit id or timestamp. Time travel is free; canon is a DAG.
- `authority_floor` — suppress claims below this tier. Generation contexts should set `derived`; research contexts may drop to `apocryphal`.
- `depth` — graph traversal hops from matched nodes.

Returns nodes, claims, edges, each with provenance and originating commit.

### 4.2 `datum.check`

**The differentiator.** Validate a candidate artifact or claim set against canon and return a cited verdict.

```json
{
  "content": "Rin's blue eyes narrowed as she recalled the Fall.",
  "claims": [],
  "branch": "main",
  "scope": ["nd_7f3a2c"],
  "mode": "strict"
}
```

Accepts either prose (extracted to candidate claims) or structured claims directly.

**Verdict:**

```json
{
  "status": "conflict",
  "drift_score": 0.34,
  "violations": [
    {
      "constraint": "cardinality",
      "severity": "blocking",
      "predicate": "eye_color",
      "candidate": "blue",
      "conflicts_with": {
        "claim": "cl_9b21",
        "value": "green",
        "authority": "binding",
        "commit": "cm_0044",
        "source": "series-bible-v3"
      },
      "resolutions": [
        { "action": "amend_candidate", "to": "green" },
        { "action": "supersede", "target": "cl_9b21", "requires_authority": "binding" },
        { "action": "scope_apocryphal", "branch": "apocrypha/alt-rin" }
      ]
    }
  ]
}
```

`status`: `conform` | `conflict` | `stale` | `unresolvable` | `uncovered`

`uncovered` is deliberate and important: the candidate asserts something canon has no position on. That is not a violation — it is a **gap**, and gaps are the highest-value input to canon expansion. Log them.

**Every violation carries a citation: node, claim, commit, source.** A verdict without receipts is an opinion.

### 4.3 `datum.propose`

Write a change to a proposal branch. Runs `check` pre-flight and returns the verdict alongside the proposal.

```json
{
  "branch_from": "main",
  "changes": [ { "op": "assert", "node": "nd_7f3a2c", "predicate": "rank", "value": "Warden" } ],
  "author": "agent:showrunner",
  "rationale": "Established in Ep. 4 draft, needs ratification"
}
```

Returns `proposal_id`, target branch, pre-flight verdict.

**Agents may call `read`, `check`, and `propose`. Agents may not call `commit`.** This is the safety property of the entire protocol: autonomous systems can enrich canon at unlimited volume without any single one of them being able to corrupt it.

### 4.4 `datum.commit`

Ratify a proposal into a branch. Requires an authorized principal.

```json
{
  "proposal_id": "pr_0088",
  "into": "main",
  "authority": "binding",
  "resolutions": [
    { "violation": "v_01", "action": "amend_candidate", "to": "green" }
  ],
  "supersedes": [],
  "message": "Ratify Rin's Warden rank"
}
```

Rejects if any `blocking` violation is unresolved. Returns the new commit id and post-merge branch state.

---

## 5. Merge semantics

Three-way merge over claims, using the DAG base.

| Case | Behavior |
|---|---|
| Disjoint claims edited | auto-merge |
| Same claim, identical value | auto-merge |
| Same claim, different values, equal authority | **conflict** — requires explicit resolution |
| Same claim, different values, unequal authority | higher tier wins; override recorded on the commit |
| Modify vs. supersede | supersession wins; modification is rebased onto the new claim or rejected |
| Delete vs. modify | conflict — deletion is discouraged; prefer supersession |
| Temporal claims with overlapping intervals | conflict unless intervals can be split without contradiction |
| Derived claim with changed inputs | auto-recompute; flag `stale` if recomputation is not deterministic |

**Deletion is a smell.** Canon does not forget; it supersedes. Hard delete exists only for legal removal (rights reversion, redaction) and is recorded as a tombstone commit.

---

## 6. Canon Drift Score

The bridge to AIR. Same shape as agent drift: measure divergence between a declared charter and observed behavior. Here the charter is canon and the behavior is generated output.

For a window `W`:

```
drift(W) = ( w_b · B + w_a · A ) / N   +   λ · aging(U)
```

- `N` — assets validated in `W`
- `B` — blocking violations
- `A` — advisory violations
- `U` — unresolved conflicts open at end of `W`
- `aging(U)` — sum of open-conflict age in days, normalized

Report alongside **coverage** — the share of generated assertions that canon had a position on. High coverage with low drift is a healthy canon. **Low drift with low coverage is not conformance, it is ignorance**, and it is the failure mode most likely to be mistaken for success.

---

## 7. Domain bindings

The engine is domain-agnostic. Bindings are constraint packs plus type vocabularies.

| | Narrative | Policy / compliance | Engineering |
|---|---|---|---|
| Node types | character, location, event, artifact, faction | rule, jurisdiction, entity, obligation | decision, service, interface, constraint |
| Binding source | series bible | ratified regulation | approved ADR |
| Apocrypha | Legends, fan canon | draft guidance, commentary | rejected RFCs |
| Supersession | retcon | amendment | superseded ADR |
| `check` runs on | script, panel, render prompt | draft policy, marketing claim | design doc, PR description |

If the same engine serves all three columns without modification, the infra thesis is proven. If only column one has users after 90 days, this is an excellent vertical product with an infra-shaped architecture.

---

## 8. Resolved positions

### 8.1 Extraction is an adapter, not part of the protocol

The protocol operates on claims. Turning prose into claims is a pluggable adapter with its own model card and its own version. Putting extraction inside the spec would bound the spec's quality by model quality, which changes quarterly.

Three consequences:

- **Machine-extracted claims default to `proposed`, never `binding`.** Extraction cannot create canon. It can only ask.
- **Provenance records the extractor.** `provenance.extractor = { name, version }` on every machine-origin claim.
- **Re-validation sweeps are a first-class operation.** Upgrading the extractor is a re-survey: previously-conforming assets may surface new conflicts, and that is correct behavior, not a regression. Sweeps are explicit, scheduled, and produce a diff report.

**Tune extraction for recall, not precision.** A missed contradiction ships; a false one costs a human thirty seconds. In `gate` mode, accept low precision and route to a reviewer. In `advisory` mode, threshold higher.

### 8.2 Constraint evaluation is dirty-set scoped

Never evaluate the full graph on the write path.

1. Index constraints by `(subject_type, predicate)`.
2. On commit, collect touched subjects and predicates from the delta.
3. Expand by declared constraint dependency — `temporal` pulls the subject's event chain, `referential` pulls the edge neighborhood, `derivation` pulls downstream derived claims.
4. Evaluate only that closure.

Cache verdicts keyed by `(claim_set_hash, constraint_schema_version, branch_head)`. Full sweeps are explicit operations triggered by constraint schema changes or extractor upgrades — the equivalent of a reindex, never on the write path.

Scale note worth stating plainly in the paper: canon graphs are small. A large franchise is on the order of 10⁵ claims. This is a write-latency problem, not a big-data problem.

### 8.3 Federation is authority-scoped imports — and it is the licensing product

Submodules copy. Imports reference. Datum uses imports.

A universe imports another's namespace read-only under a declared authority mapping. The critical primitive: **supersession rights are separable from read rights.**

| Right | Rights holder | Licensee |
|---|---|---|
| Read imported canon | yes | yes |
| Propose against imported canon | yes | yes |
| Supersede on `main` | yes | **no** |
| Supersede within own scoped branch | yes | yes, if granted |

Conflicts crossing an import boundary are `advisory` by default and cannot auto-resolve; they escalate to the rights holder as a review item.

This is not a technical footnote. Rights holders and licensees maintaining a shared canon with asymmetric supersession rights, under audit, is the exact workflow currently executed by PDF style guides and approval emails. Federation is the commercial surface.

### 8.4 Proposal load is managed by budget, corroboration, and delegated authority

Four mechanisms, in order of cheapness:

1. **Deduplicate by claim hash.** Fifty agents proposing the same fact collapse into one proposal with fifty corroborations. Corroboration count is signal, not noise.
2. **Ratification budget.** Per-agent proposal quotas with backpressure. Exceeded quota queues rather than rejects.
3. **Auto-ratification thresholds.** A proposal ratifies without human review only if it has zero blocking violations, coverage above threshold, a predicate on an allowlist, **and** an authoring agent whose historical ratification rate clears a bar.
4. **Curator delegation.** A named principal with scoped, audited, revocable ratification authority. Delegation, not automation.

Mechanism 3 is where AIR integrates directly: **an agent's integrity score gates its delegated canon authority.** Drift-monitored agents earn write latitude; drifting agents lose it automatically.

### 8.5 Reader-side enforcement is policy, with a mandatory flag

`read` never silently hides contested canon. Any claim under an unresolved blocking conflict returns with `contested: true` and the conflicting claim attached.

Three modes, harness-selected:

- `permissive` *(default)* — return contested claims, flagged
- `strict` — omit contested claims, report the omission
- `gate` — error, with the blocking violation cited

Default is `permissive` because silently omitting canon is worse than returning disputed canon, and hard-failing generation over an unresolved dispute turns the tool into an obstacle. **The `contested` flag must appear in the payload the model actually sees** — handing a generation context a disputed fact without marking it disputed is worse than not answering.

### 8.6 Remaining open

- Claim extraction recall on `temporal_inference` hazards is the dominant unknown. Quantified by GREATGAME Task A.
- Constraint expressiveness: declarative constraints cover the taxonomy in §2, but narrative rules like "magic has a cost" resist formalization. Out of scope for v1.
- Canon poisoning under adversarial proposal load — see [threat model](threat-model.md). Three threats there are open against this version and carry into v0.3 as normative work: corroboration collusion (T2, which the §8.4.1 dedup mechanism actively worsens), provenance forgery (T5, uncontrolled in v0.2), and supersession abuse (T6, auditable but not preventable).

---

## 9. Reference implementation

Worldtree, running on LANDSAT, across live IP properties. Local-first Markdown vaults plus Firestore, retrieval through the Librarian, render validation at the FFmpeg / Veo boundary.

The pitch, compressed: **studios buy Worldtree; developers mount Datum; same engine.**

<!-- gate proof: a spec edit with no canon commit -->
