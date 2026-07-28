# Datum — Threat Model

**Companion to** [datum-v0.2.md](datum-v0.2.md) · Third Signal Labs · Draft 0.1

---

## 0. Scope and stance

Datum's security claim is narrow and should be stated narrowly: **autonomous systems can enrich canon at unlimited volume without any single one of them being able to corrupt it.** That is the property agents-propose-humans-ratify buys. It is not a claim that canon is correct, that ratifiers are competent, or that a determined insider can be stopped.

This document exists because a governance protocol without a threat model gets one question in the first serious room and does not recover. Every entry below carries a **residual risk**. A threat model in which everything is mitigated is marketing, and the two threats worth reading first — T2 and T6 — are ones where v0.2 is actively weak.

**Two structural observations shape everything below.**

First: **Datum's most valuable primitive is its largest attack surface.** Supersession exists precisely so that deliberate change does not raise a conflict (§3). That is the same thing as saying supersession is a sanctioned path to make canon change without tripping detection. Anyone who holds the right holds the exploit.

Second: **detection coverage is a security control, not a quality metric.** The spec already says low drift at low coverage is ignorance wearing conformance's clothes (§6). Restated as security: an attacker's cheapest move is not defeating a constraint, it is asserting into a region where no constraint is declared. Coverage is the attack surface map.

---

## 1. Assets

Ranked by what an attacker gains from compromising them.

| # | Asset | Why it is the target |
|---|---|---|
| A1 | The binding claim set on `main` | Binding claims bind generation. Corrupting one claim corrupts every downstream artifact validated against it, silently, until someone notices by eye. |
| A2 | Authority tier assignments | The tier, not the value, decides whether a claim binds. Promoting a claim from `proposed` to `binding` is cheaper than arguing about its content. |
| A3 | Supersession rights | The right to retire canon without raising a conflict. In a federated deployment this is also the commercial asset (§8.3). |
| A4 | The provenance chain | Provenance is the entire basis of the citation guarantee. A verdict without receipts is an opinion; a verdict with forged receipts is worse than an opinion. |
| A5 | Commit DAG integrity | `as_of` retrieval, audit, and rollback all assume history is append-only and honest. |
| A6 | The constraint schema | Constraints are the whole basis of contradiction detection (§2). Deleting a constraint is equivalent to legalizing every contradiction it would have caught, and leaves no conflicting claim behind as evidence. |
| A7 | Ratification throughput | Canon that cannot be updated is canon that gets bypassed. Availability of the ratification path is a real asset, not an operational footnote. |

---

## 2. Trust boundaries

```
   untrusted                      semi-trusted                     trusted
 ┌────────────┐   TB1   ┌──────────────────┐   TB2   ┌─────────────────────┐
 │   agents   │ ──────► │ proposal branches │ ──────► │  binding canon/main │
 └────────────┘         └──────────────────┘         └─────────────────────┘
       ▲                                                       │
       │ TB3                                              TB5  │
 ┌────────────┐                                       ┌────────▼────────┐
 │ extractors │                                       │ harness → model │
 └────────────┘                                       └─────────────────┘

 TB4: import boundary — foreign canon crossing an authority mapping (§8.3)
```

| | Boundary | Crossing control | Weakest point |
|---|---|---|---|
| **TB1** | agent → proposal | Quota, dedup, pre-flight `check` (§8.4) | Dedup is exploitable — see T2 |
| **TB2** | proposal → binding canon | Human or delegated ratification (§4.4) | Auto-ratification thresholds — see T3 |
| **TB3** | extractor → claim | Machine claims default `proposed`; extractor recorded in provenance (§8.1) | Extractor version supply chain — see T8 |
| **TB4** | import boundary | Asymmetric supersession rights (§8.3) | Scoped-branch laundering — see T7 |
| **TB5** | harness → model context | `contested` flag mandated in payload (§8.5) | Nothing enforces it — see T10 |

TB2 is the boundary the entire protocol is built to defend. TB5 is the one most likely to be broken by a well-meaning integrator.

---

## 3. Adversaries

| | Adversary | Capability | Motivation |
|---|---|---|---|
| **ADV-1** | Misaligned or compromised agent | Unlimited `read`, `check`, `propose`. No `commit`. | Land a false claim; or exhaust the ratification path |
| **ADV-2** | Coordinated agent fleet | ADV-1 × N, with shared objective and forged independence | Manufacture corroboration |
| **ADV-3** | Malicious licensee | Read + propose against imported canon; supersede within a granted scoped branch (§8.3) | Escape a licensing constraint without renegotiating it |
| **ADV-4** | Insider curator | Delegated, scoped, audited ratification authority (§8.4.4) | Retire inconvenient canon quietly |
| **ADV-5** | Upstream corpus poisoner | Controls a document the extractor ingests | Launder a claim through a trusted-looking source |
| **ADV-6** | Extractor supply chain attacker | Controls an extractor version or its weights | Mass claim mutation with correct provenance |

Out of scope as an adversary: **the authorized principal.** See §6.

---

## 4. Threat catalogue

Each entry: attack path → mitigation with spec anchor → **residual risk** → detection signal.

---

### T1 — Canon poisoning by proposal volume
**ADV-1 · TB1 · asset A1 · severity: low**

Flood the proposal path with plausible false claims so that reviewer fatigue lets one through.

**Mitigation (§8.4.1–2).** Deduplication by claim hash collapses repeats. Per-agent ratification budgets apply backpressure; exceeded quota queues rather than rejects, so the honest case degrades gracefully.

**Residual risk.** Low for the naive version. Volume alone is the cheapest attack and the best defended. Note that quota backpressure converts this threat into T9 — the attacker who cannot poison can still congest.

**Detection.** Proposal-rate anomaly per agent; ratification rate collapse against a stable proposal rate.

---

### T2 — Poisoning by corroboration collusion
**ADV-2 · TB1 · asset A1 · severity: HIGH · v0.2 is weak here**

This is the important one.

Section 8.4.1 states that fifty agents proposing the same fact collapse into one proposal with fifty corroborations, and that **corroboration count is signal, not noise.** As written, that is exploitable, and worse than exploitable: it means the defense against T1 *amplifies* T2. An attacker who splits one false claim across fifty agents does not get throttled — they get a proposal that arrives pre-endorsed, and if auto-ratification (§8.4.3) is enabled, corroboration is precisely the kind of confidence signal a threshold is built from.

**Attack path.** Instantiate N agents. Have each independently "discover" the same false claim from sources that trace back to one origin. Submit. Dedup merges them into a single high-corroboration proposal. A reviewer sees consensus.

**Mitigation.** v0.2 does not adequately mitigate this. The required correction:

> **Corroboration MUST be weighted by independent provenance lineage, not by agent count.** Two corroborations whose `provenance.source` resolves to the same upstream document are one corroboration. Corroborations sharing an extractor version, an ingestion batch, or a principal owner are correlated and MUST be discounted as such.

Recommended companions: cap the contribution of any single lineage to a corroboration score; treat corroboration as evidence *of propagation*, which is what it actually measures, rather than evidence of truth.

**Residual risk.** High until lineage weighting is specified normatively. Even with it, an attacker controlling genuinely independent upstream sources defeats the control — this reduces to T5, and provenance forgery is itself unmitigated in v0.2. Lineage weighting raises the cost of the attack; it does not close it.

**Detection.** Corroboration clusters with low lineage entropy. Sudden corroboration on a predicate with no prior proposal history. Agents whose corroboration overlap with each other exceeds their overlap with the general population.

**Status.** Open. This must be resolved before v1.0 and is a candidate §8 position for v0.3.

---

### T3 — Authority escalation via auto-ratification
**ADV-1, ADV-2 · TB2 · asset A2 · severity: medium**

Section 8.4.3 lets a proposal ratify without human review given zero blocking violations, coverage above threshold, an allowlisted predicate, and an authoring agent whose historical ratification rate clears a bar. Every one of those four is a resource an attacker can farm.

**Attack path.** Build ratification history on low-stakes allowlisted predicates until the reputation bar is cleared, then spend the accumulated reputation on a claim that matters. Classic reputation-laundering, and it works because reputation is modelled as a scalar.

**Mitigation.** Reputation MUST be scoped per predicate-risk-class and MUST NOT transfer upward. An agent trusted on `hair_color` is not thereby trusted on `date_of_death`. The predicate allowlist should be a small, deliberately curated set — the mechanism is a throughput optimization for boring facts, not a general trust system. Reputation should decay; a rate earned last quarter is not evidence about this quarter.

**Residual risk.** Medium. The mechanism trades safety for throughput by design, and any deployment that widens the allowlist under operational pressure widens this hole. AIR integration (§8.4) makes this sharper in both directions: an agent's integrity score gating its canon authority is a real control, and it also means **compromising the integrity scorer is now a canon attack.** That dependency should be stated wherever the integration is described.

**Detection.** Predicate-class distribution shift in an agent's accepted proposals. Auto-ratifications on predicates first proposed by that agent. Reputation gains concentrated in a narrow time window before a high-value assertion.

---

### T4 — Escalation through derived claims
**ADV-1 · TB2 · assets A1, A2 · severity: medium**

`derived` claims bind generation (§1.2) but are computed rather than ratified. Attack the inputs, not the output.

**Attack path.** Land a low-scrutiny `binding` claim that is an input to a derivation. The recomputation propagates the consequence into a `derived` claim that binds, and the derived claim's provenance points at the derivation, not at the attacker's assertion. The blast radius exceeds the review that was applied.

**Mitigation.** The `derivation` constraint (§2) flags stale derived claims. Derivation dependency graphs SHOULD be computed and surfaced at review time: a ratifier approving an input claim must be shown what it will cause downstream. Reviewing a claim whose consequences are invisible is not review.

**Residual risk.** Medium. Datum has no notion of derivation depth limits, and a long derivation chain launders authority by distance. Deployments with deep derivation graphs should treat inputs to high-fan-out derivations as a distinct, higher-scrutiny predicate-risk-class per T3.

**Detection.** Derived-claim churn following a single input commit. Fan-out size of a ratified change, reported to the ratifier before the fact rather than after.

---

### T5 — Provenance forgery
**ADV-1, ADV-5 · TB1, TB3 · asset A4 · severity: HIGH · v0.2 has no control**

The citation guarantee — "every violation carries a citation: node, claim, commit, source" (§4.2) — is the protocol's core credibility claim. In v0.2, `provenance.source` is a self-reported free-text string. `asserted_by` is an unverified identifier. Nothing binds a claim's stated origin to its actual origin.

**Attack path.** Assert a claim with `provenance.source: "series-bible-v3"`. It is now indistinguishable from a claim that actually came from the series bible. Every downstream verdict citing it inherits false authority, and the audit trail is worse than useless because it is confidently wrong.

Variant (ADV-5): don't forge the field, forge the source. Poison a document the extractor legitimately ingests. Provenance is then accurate and the claim is still false — provenance records where a claim came from, never whether it is true.

**Mitigation.** Not present in v0.2. Required for v1.0:
- Commits MUST be cryptographically signed by their ratifying principal.
- `asserted_by` MUST resolve against a principal registry; unresolvable principals are rejected rather than recorded.
- `provenance.source` MUST reference a registered source artifact by content hash, not by a human-readable name.

**Residual risk.** High. Source registration raises the bar to *compromise a registered source* rather than *type a string*, which is materially harder but not hard. The ADV-5 variant is not addressed by any cryptographic control and never will be — trust in source content is a curation problem, and curation is where a rights holder's judgment is irreducible.

**Detection.** Source-hash mismatches on re-validation sweep. Claims citing sources with no corresponding ingestion record. Unsigned commits on `main`.

---

### T6 — Supersession abuse
**ADV-3, ADV-4 · TB2 · asset A3 · severity: HIGH**

The second important one, and the one that follows from taking the protocol's own design seriously.

Section 3 states that supersession **does not raise a conflict**, because it is the sanctioned path for deliberate contradiction. That is correct design and it is also a complete description of the exploit: an actor holding supersession rights can retire any inconvenient claim *without tripping a single detection mechanism*, because not tripping detection is the feature.

**Attack path.** Rather than contradict a binding claim — which raises a blocking violation, cites receipts, and demands resolution — supersede it. Record a thin reason. The old claim is preserved at `as_of` and suppressed at `HEAD`, drift score is unaffected, and no alarm fires anywhere. Then assert freely into the vacated space.

**Mitigation (partial, §3).** Supersession never deletes; it marks `superseded`, records `superseded_by`, a reason, and the ratifying authority. History is intact and the act is fully attributable *after* someone thinks to look.

That is auditability, not prevention, and the distinction matters: T6 is not a stealth attack, it is a **low-salience** one. Everything is in the log; nothing draws attention to it.

**Required additions.**
- **Supersession rate MUST be a first-class drift signal**, reported alongside `drift(W)` and coverage (§6). A canon whose supersession rate rises without a corresponding authoring event is a canon being rewritten.
- Supersession of a `binding` claim SHOULD require strictly greater ceremony than assertion — a second ratifier, or a delay window, at deployment's discretion.
- Superseding a claim younger than some threshold SHOULD be flagged: rapid assert-then-supersede is how history gets laundered into looking deliberate.

**Residual risk.** High, and irreducible in part. Datum cannot distinguish a legitimate retcon from a malicious one, because that distinction is a judgment about intent and the protocol's entire thesis is that intent must be *declared by an authority* rather than inferred. What Datum can guarantee is that the declaration is recorded, attributable, and reversible. The control is organizational; the protocol's job is to make sure the organization has something to look at.

**Detection.** Supersession rate per principal against baseline. Supersessions with reasons below a length or specificity floor. Assert-then-supersede within a short window. Supersessions clustered on a single subject.

---

### T7 — Import-boundary laundering
**ADV-3 · TB4 · assets A1, A3 · severity: medium**

Section 8.3 grants a licensee supersession rights *within their own scoped branch* but never on the rights holder's `main`. The gap is what happens on the way back up.

**Attack path.** Supersede an imported binding claim inside the granted scoped branch, where it is permitted. Build downstream work on the superseded state. Then propose a merge upward whose diff no longer *looks* like a supersession — it looks like a set of ordinary claims that happen to be consistent with a canon that no longer exists on `main`. Alternatively, let the scoped branch drift far enough that reverting it is commercially unacceptable, and negotiate the supersession as a fait accompli.

**Mitigation (§8.3).** Cross-boundary conflicts are `advisory` by default, cannot auto-resolve, and escalate to the rights holder as a review item.

**Required addition.** Merges crossing an import boundary MUST be evaluated against the **rights holder's** `main`, not against the licensee's branch base. A scoped supersession MUST NOT be transitively applied by a merge; it must be re-proposed explicitly and ratified by the rights holder as a supersession in its own right.

**Residual risk.** Medium, and mostly commercial rather than technical. The fait-accompli variant is not a protocol problem — it is a contract problem, and the protocol's contribution is making the divergence measurable early enough that the contract can be enforced while reverting is still cheap. Rights holders should monitor scoped-branch divergence as an operational metric, not review it at merge time.

**Detection.** Supersession count within scoped branches. Divergence depth between a scoped branch and rights-holder `main`. Merge proposals whose base is a superseded state.

---

### T8 — Extractor supply chain
**ADV-6 · TB3 · assets A1, A4 · severity: medium-high**

Section 8.1 makes re-validation sweeps a first-class operation and states, correctly, that new conflicts surfacing after an extractor upgrade is right behavior rather than a regression. That property is also a delivery mechanism.

**Attack path.** Compromise an extractor version. Trigger or wait for a scheduled sweep. The sweep mutates claims at scale with entirely correct provenance — `provenance.extractor` faithfully records the compromised version — and the resulting diff is *expected to be large*, which is exactly the condition under which it will not be read line by line.

**Mitigation.** Machine-extracted claims default to `proposed` and can never be `binding` (§8.1), so a compromised extractor cannot directly write truth. Sweeps are explicit, scheduled, and produce a diff report.

**Required additions.**
- Extractor versions MUST be pinned by content hash, not by version string.
- Sweep diff reports MUST be reviewed at claim granularity for `binding` targets, and a sweep that proposes changes exceeding a deployment-set threshold SHOULD require explicit re-authorization rather than proceeding.
- Sweeps MUST be reversible as a unit — a sweep is one commit, not many.

**Residual risk.** Medium-high. The `proposed`-only default is a genuinely strong control and it is doing most of the work here. The residual is entirely about review capacity: a sweep proposing ten thousand changes will be spot-checked, and an attacker only needs the one they care about to be outside the sample. Sweep size is therefore a security parameter, and treating "the diff was large" as normal is the failure mode.

**Detection.** Sweep diff size against historical baseline. Extractor hash mismatch. Claims whose value changed on a sweep without a corresponding source change.

---

### T9 — Denial of ratification
**ADV-1, ADV-2 · TB2 · asset A7 · severity: medium**

Availability, which governance protocols routinely forget they have.

**Attack path.** Saturate the curator queue with proposals that are individually plausible and collectively exhausting — each requiring genuine judgment, none obviously junk. Legitimate changes queue behind them. Canon staleness rises, and the organization begins routing around canon to ship, which achieves the attacker's goal without any false claim ever being ratified.

**Mitigation.** Ratification budgets throttle per-agent volume (§8.4.2). Dedup collapses repeats.

**Residual risk.** Medium. Budgets bound a single agent, not the aggregate; a fleet of individually-compliant agents saturates the queue without any of them exceeding quota. There is no aggregate admission control in v0.2. Deployments should monitor queue depth and time-to-ratification as reliability metrics with alerting, exactly as they would for any other production queue.

Worth naming plainly: **canon that cannot be updated at the speed of work gets bypassed**, and a bypassed canon has a drift score of zero and a coverage of zero. That is the ignorance-wearing-conformance failure (§6) arrived at through an availability attack.

**Detection.** Queue depth and age. Time-to-ratification percentiles. Rising share of generated assets validated against a canon HEAD older than some threshold.

---

### T10 — Contested-flag stripping
**integrator error, or ADV-1 with harness access · TB5 · asset A1 · severity: medium-high**

Section 8.5 is unambiguous: **the `contested` flag must appear in the payload the model actually sees.** Handing a generation context a disputed fact without marking it disputed is worse than not answering.

Nothing in the protocol enforces this, and it sits at the boundary furthest from the protocol's control.

**Attack path.** Usually not an attack at all. A harness flattens Datum's response into a prompt string. Whoever wrote that flattening kept `value` and dropped the metadata, because the metadata is not what the prompt template needed. The model now treats contested canon as settled canon, generates confidently on it, and `datum.check` on the output finds no violation — the output is consistent with a claim that exists. The failure is invisible from both ends.

**Mitigation.** The **conformance suite is the enforcement mechanism.** L1 requires that `contested: true` survives into the payload an implementation exposes to a model, and an implementation that strips it does not pass L1 and cannot claim compliance. This is precisely why the threat model and the conformance suite ship together: a normative statement with no test is a suggestion.

**Residual risk.** Medium-high. Conformance is voluntary and tests the implementation, not the deployment. An integrator can pass L1 with their Datum client and still drop the flag in their own prompt assembly two layers up. The recommended posture is that the `contested` flag be rendered as *text inside the claim value itself* at the serialization boundary — visibly, not as a sibling field a template can quietly omit.

**Detection.** Hard from inside the protocol; this is a code-review and conformance-testing control. `read` calls returning contested claims to contexts that never subsequently call `check` are a weak signal worth logging.

---

## 5. Summary

| # | Threat | Severity | v0.2 status |
|---|---|---|---|
| T1 | Poisoning by volume | low | mitigated |
| **T2** | **Poisoning by corroboration collusion** | **high** | **open — spec change required** |
| T3 | Escalation via auto-ratification | medium | partial |
| T4 | Escalation through derived claims | medium | partial |
| **T5** | **Provenance forgery** | **high** | **open — no control in v0.2** |
| **T6** | **Supersession abuse** | **high** | **partial — auditable, not preventable** |
| T7 | Import-boundary laundering | medium | partial |
| T8 | Extractor supply chain | medium-high | partial |
| T9 | Denial of ratification | medium | partial |
| T10 | Contested-flag stripping | medium-high | enforced by conformance suite |

**Three carry into v0.3 as normative work:** T2 (lineage-weighted corroboration), T5 (signed commits, principal registry, content-hashed sources), T6 (supersession rate as a first-class drift signal).

---

## 6. Non-goals

Stated explicitly, because a threat model's boundaries are load-bearing.

**Datum does not defend against a compromised authorized principal.** A principal with binding ratification authority can assert anything. This is not a gap to be closed; it is the design. Truth requires an authority, an authority is a trusted party, and a trusted party can be wrong or corrupt. Datum's contribution is that the authority's actions are attributable, timestamped, cited, and reversible — the guarantee is *accountability*, never *prevention*. Any deployment treating Datum as protection against its own ratifiers has misread the protocol.

**Datum does not attest that a claim is true.** Provenance records where a claim came from. Authority records who stands behind it. Neither is a truth predicate, and a system built on the assumption that binding means correct will be surprised.

**Datum does not cryptographically attest extraction fidelity.** That a claim faithfully represents the passage it cites is unverifiable by any mechanism in the protocol. It is measured statistically, by GREATGAME Task A, and a measured recall of 0.71 means roughly three in ten contradictions are simply not seen.

**Constraint expressiveness bounds detection, and therefore bounds security.** Section 8.6 notes that narrative rules like "magic has a cost" resist formalization. Undeclared constraints are undefended regions, and the cheapest attack on any Datum deployment is to assert into one. Coverage (§6) is the map of that exposure — which is the strongest reason to report it alongside every drift figure rather than treating it as a secondary statistic.

**Datum does not defend the canon it imports.** Under federation (§8.3), a licensee inherits the rights holder's canon *and* the rights holder's threat exposure. Import is a trust decision, made once, about an entire namespace.

---

## 7. Revision

This document is canon. It is versioned in [../canon/](../canon/) alongside the specification, and changes to it follow the same rule as changes to the spec: **positions are superseded with a recorded reason, never silently edited.** Reversing a judgment here without preserving the prior one would be a governance protocol failing to govern its own threat model, which is a thing a reviewer will check.
