# Datum Conformance Suite

A specification tells you what an implementation should do. A conformance suite tells you whether it did. Papers ship model cards; protocols ship test suites, and it is the reason some protocols spread while others only get read.

**39 vectors across six levels.** Declarative JSON, language-agnostic, executable against any implementation through a single adapter class.

```bash
python3 -m conformance.runner.run --adapter mock
python3 -m conformance.runner.run --adapter mock --level L3-supersession
python3 -m conformance.runner.run --adapter yourpkg.datum:Adapter --json
```

Exit code is non-zero when any MUST vector fails, so this drops into CI as a gate without wrapping.

## Levels

| Level | Vectors | What it establishes | Spec |
|---|---|---|---|
| **L1 read** | 6 | `as_of` time travel, `authority_floor` suppression, and the `contested` flag surviving into the payload a model sees | §4.1, §8.5 |
| **L2 check** | 10 | all seven constraint types, and that **every** violation carries a citation | §2, §4.2 |
| **L3 supersession** | 5 | the discrimination: supersession raises no conflict, the same change undeclared does | §3 |
| **L4 authority** | 5 | agents cannot commit; blocking violations reject; extraction cannot create canon | §4.3, §4.4, §8.1 |
| **L5 merge** | 8 | one vector per row of the §5 merge table | §5 |
| **L6 federation** | 5 | the §8.3 rights matrix, including that a licensee cannot supersede on `main` | §8.3 |

## Badges

| Badge | Requires |
|---|---|
| **Datum v0.2 Core** | L1–L4 |
| **Datum v0.2 Complete** | L1–L6 |

Results are always reported per level. An implementation that supports read and check but has no merge should be able to say so precisely and claim what it has earned — aggregate scoring makes a partial implementation indistinguishable from a broken one, and the same reasoning is why GREATGAME scores extraction, detection, and end-to-end separately rather than reporting one number.

## The three vectors to read first

**L3-001 and L3-005.** The same value change to the same claim, demanding opposite verdicts. The only difference is whether the change was declared as a supersession. Every existing continuity tool fails this pair, because none of them model supersession at all — they flag both as errors and bury every intentional canon change in false alarms.

**L4-001.** An agent principal calling `datum.commit` must be refused. This is the safety property the whole protocol is built to deliver: autonomous systems can enrich canon at unlimited volume without any one of them being able to corrupt it. An implementation that fails this vector has given an agent write access to truth, whatever else it does correctly.

**L1-004.** A contested claim must reach the model marked as contested. The spec mandates it (§8.5) and cannot enforce it. This vector is the enforcement — see threat model T10, where the failure is not an attack but a well-meaning integrator flattening a response into a prompt string and keeping only the value.

## Writing an adapter

Subclass `DatumAdapter`, implement what you support, return plain dicts.

```python
from conformance.runner.adapter import DatumAdapter

class Adapter(DatumAdapter):
    name = "my-implementation 1.0"

    def load_fixture(self, fixture):
        self.store = MyStore.from_dict(fixture)

    def read(self, args, principal):
        return self.store.read(**args)
```

Unimplemented tools raise `NotSupported` and are reported as level failures rather than crashes. Partial implementations are expected, and the response shape you return is the shape you are claiming conformance for.

## The mock is supposed to fail

`runner/adapters/mock.py` implements `read`, `check`, and the supersession path of `commit` — enough for L1 through L3 — and deliberately implements neither principal authority checks, nor `propose`, nor merge, nor import boundaries.

```
PASS  L1-read            6/6
PASS  L2-check           10/10
PASS  L3-supersession    5/5
FAIL  L4-authority       1/5
FAIL  L5-merge           0/8
FAIL  L6-federation      2/5

Badge: none. Core requires L1-read, L2-check, L3-supersession, L4-authority; failing: L4-authority
```

This matters more than it looks. It means the suite demonstrably passes what it should and fails what it should, **with no reference implementation in existence** — and a conformance suite that has never reported a failure has not been tested. CI asserts this exact profile on every push, so a change that quietly makes everything pass fails the build.

Note that L4 and L6 each pass a couple of vectors anyway, because those exercise read paths the mock does implement. Real partial implementations fail in patches, not at clean level boundaries. The per-vector report is what makes that difference diagnosable rather than mysterious.

## Validation

```bash
python3 -m conformance.runner.validate
```

Checks vector structure, and — more usefully — referential integrity across `canon/`: that superseded claims name a successor that exists and a reason that is not empty, that branch heads and commit parents resolve, and that every supersession is recorded by a commit rather than applied as an edit. It also cross-checks the `Datum-Commit` git trailers against `canon/commits.json`.

A canon store stays syntactically valid long after it stops being coherent. Those failures are what make an audit trail untrustworthy, and none of them are visible to a schema.
