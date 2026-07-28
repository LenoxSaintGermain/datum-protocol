"""A deliberately partial Datum implementation.

This exists to prove the conformance suite works — that it passes what it
should and fails what it should — before any real implementation exists. A
conformance suite that has never reported a failure has not been tested.

Implemented: datum.read, datum.check, and the supersession path of
datum.commit. Enough for L1, L2, and L3.

NOT implemented, on purpose:

  datum.propose            no proposal branches
  principal authority      commit does not check who is calling, so an agent
                           can write truth — the exact failure L4-001 exists
                           to catch
  commit-time validation   commit does not run check on ordinary assertions
  datum.merge              no three-way merge at all
  import boundaries        no federation awareness

The expected profile is: L1, L2, L3 conformant; L4, L5, L6 not. Some L4 and L6
vectors pass anyway, because they exercise read paths this adapter does
implement. That is realistic — partial implementations fail in patches, not at
clean level boundaries — and the per-vector report is what makes the difference
diagnosable.
"""

import re

from ..adapter import DatumAdapter, NotSupported

TIERS = {"apocryphal": 0, "proposed": 1, "derived": 2, "binding": 3}


class Adapter(DatumAdapter):
    name = "mock (deliberately partial)"

    # ---------------------------------------------------------------- setup

    def load_fixture(self, fixture):
        self.nodes = [dict(n) for n in fixture.get("nodes", [])]
        self.claims = [dict(c) for c in fixture.get("claims", [])]
        self.commits = [dict(c) for c in fixture.get("commits", [])]
        self.branches = [dict(b) for b in fixture.get("branches", [])]
        self.constraints = fixture.get("constraints", [])
        self.imports = fixture.get("imports", [])

    def _head(self, branch):
        for b in self.branches:
            if b["name"] == branch:
                return b["head"]
        return self.commits[-1]["id"] if self.commits else None

    def _ancestors(self, commit_id):
        """Commit ids reachable from commit_id, inclusive."""
        by_id = {c["id"]: c for c in self.commits}
        seen, stack = set(), [commit_id]
        while stack:
            cid = stack.pop()
            if cid in seen or cid not in by_id:
                continue
            seen.add(cid)
            stack.extend(by_id[cid].get("parents", []))
        return seen

    def _visible(self, branch="main", as_of=None):
        """Claims live at a point in history, with supersession applied as of
        that point rather than as of now."""
        point = as_of or self._head(branch)
        if point is None:
            return list(self.claims)
        reach = self._ancestors(point)
        by_id = {c["id"]: c for c in self.claims}

        live = []
        for c in self.claims:
            if c["provenance"]["commit"] not in reach:
                continue
            if c.get("status") == "superseded":
                successor = by_id.get(c.get("superseded_by"))
                # Superseded only from the commit that superseded it onward.
                if successor and successor["provenance"]["commit"] in reach:
                    continue
                c = dict(c, status="canon")
            live.append(c)
        return live

    # ---------------------------------------------------------- contradiction

    def _equal_authority_conflicts(self, claims):
        """Group live claims by (node, predicate) and report groups holding more
        than one value at the same authority tier.

        Equal authority is the whole point: two sources disagreeing is a conflict
        only when they carry equal binding force.
        """
        groups = {}
        for c in claims:
            groups.setdefault((c["node"], c["predicate"], c["authority"]), []).append(c)

        out = []
        for (node, pred, auth), members in groups.items():
            if len({str(m["value"]) for m in members}) > 1:
                out.append({"node": node, "predicate": pred,
                            "authority": auth, "claims": members})
        return out

    @staticmethod
    def _cite(c):
        return {"claim": c["id"], "value": c["value"], "authority": c["authority"],
                "commit": c["provenance"]["commit"], "source": c["provenance"]["source"]}

    # ------------------------------------------------------------ datum.read

    def read(self, args, principal):
        branch = args.get("branch", "main")
        claims = self._visible(branch, args.get("as_of"))

        if args.get("node_ids"):
            claims = [c for c in claims if c["node"] in args["node_ids"]]

        contested = {}
        for grp in self._equal_authority_conflicts(claims):
            for c in grp["claims"]:
                other = [o for o in grp["claims"] if o["id"] != c["id"]]
                contested[c["id"]] = self._cite(other[0])

        floor = TIERS.get(args.get("authority_floor", "apocryphal"), 0)
        kept, omitted = [], []
        mode = args.get("mode", "permissive")

        for c in claims:
            if TIERS[c["authority"]] < floor:
                continue
            if c["id"] in contested:
                if mode in ("strict", "gate"):
                    omitted.append({"claim": c["id"], "reason": "contested"})
                    continue
                c = dict(c, contested=True, conflicts_with=contested[c["id"]])
            kept.append(c)

        if mode == "gate" and omitted:
            return {"status": "error", "claims": [], "omitted": omitted,
                    "violations": self._contested_violations(contested, claims)}

        return {"status": "ok", "claims": kept, "omitted": omitted,
                "nodes": [n for n in self.nodes
                          if not args.get("node_ids") or n["id"] in args["node_ids"]]}

    def _contested_violations(self, contested, claims):
        by_id = {c["id"]: c for c in claims}
        seen, out = set(), []
        for cid, other in contested.items():
            key = frozenset((cid, other["claim"]))
            if key in seen:
                continue
            seen.add(key)
            out.append({"constraint": "cardinality", "severity": "blocking",
                        "predicate": by_id[cid]["predicate"],
                        "candidate": by_id[cid]["value"],
                        "conflicts_with": other})
        return out

    # ----------------------------------------------------------- datum.check

    def check(self, args, principal):
        branch = args.get("branch", "main")
        live = self._visible(branch)
        scope = args.get("scope")
        if scope:
            live = [c for c in live if c["node"] in scope]

        candidates = [dict(c) for c in args.get("claims", [])]
        violations = []

        for con in self.constraints:
            violations.extend(self._apply(con, live, candidates))

        if not candidates:
            # No candidate set: validate canon against itself.
            status = "conflict" if any(v["severity"] == "blocking" for v in violations) else (
                "conform" if violations else "conform")
        elif any(v["severity"] == "blocking" for v in violations):
            status = "conflict"
        elif any(v["constraint"] == "derivation" for v in violations):
            status = "stale"
        elif self._uncovered(live, candidates):
            status = "uncovered"
        else:
            status = "conform"

        return {"status": status, "violations": violations,
                "coverage": self._coverage(live, candidates)}

    def _uncovered(self, live, candidates):
        """A candidate canon has no position on: no existing claim on the same
        (node, predicate) and no constraint governing that predicate."""
        governed = {c.get("predicate") for c in self.constraints if c.get("predicate")}
        for cand in candidates:
            same = [c for c in live if c["node"] == cand["node"]
                    and c["predicate"] == cand["predicate"]]
            if not same and cand["predicate"] not in governed:
                return True
        return False

    @staticmethod
    def _coverage(live, candidates):
        if not candidates:
            return 1.0
        covered = sum(1 for cand in candidates
                      if any(c["node"] == cand["node"] and c["predicate"] == cand["predicate"]
                             for c in live))
        return round(covered / len(candidates), 3)

    def _apply(self, con, live, candidates):
        kind = con["kind"]
        sev = con.get("severity", "blocking")
        handler = getattr(self, f"_c_{kind}", None)
        return handler(con, sev, live, candidates) if handler else []

    def _c_cardinality(self, con, sev, live, candidates):
        """A candidate conflicts with canon at or above its own tier.

        Not equal-tier: check asks whether asserting this would violate canon,
        and a proposed candidate contradicting binding canon is exactly the case
        the tool exists for. Equal-tier comparison belongs to stored claims,
        where it decides whether a dispute is real — see _equal_authority_conflicts.
        """
        pred = con.get("predicate")
        out = []
        for cand in candidates:
            if cand["predicate"] != pred:
                continue
            for c in live:
                if (c["node"] == cand["node"] and c["predicate"] == pred
                        and str(c["value"]) != str(cand["value"])
                        and TIERS[c["authority"]] >= TIERS[cand["authority"]]):
                    out.append({"constraint": "cardinality", "severity": sev,
                                "predicate": pred, "candidate": cand["value"],
                                "conflicts_with": self._cite(c)})
        return out

    def _c_domain(self, con, sev, live, candidates):
        pred, allowed = con.get("predicate"), con.get("values", [])
        return [{"constraint": "domain", "severity": sev, "predicate": pred,
                 "candidate": cand["value"],
                 "conflicts_with": {"claim": None, "value": allowed, "authority": "binding",
                                    "commit": None, "source": "constraint:domain"}}
                for cand in candidates
                if cand["predicate"] == pred and cand["value"] not in allowed]

    def _c_temporal(self, con, sev, live, candidates):
        out = []
        for cand in candidates:
            for c in live:
                if (c["node"] == cand["node"] and c["predicate"] == cand["predicate"]
                        and str(c["value"]) != str(cand["value"])
                        and _overlaps(c["effective"], cand["effective"])):
                    out.append({"constraint": "temporal", "severity": sev,
                                "predicate": cand["predicate"], "candidate": cand["value"],
                                "conflicts_with": self._cite(c)})
        return out

    def _c_exclusion(self, con, sev, live, candidates):
        pairs = [tuple(s.split("=", 1)) for s in con.get("claims", [])]
        held = {(c["predicate"], str(c["value"])): c for c in live + candidates}
        matched = [held[p] for p in pairs if p in held]
        if len(matched) < 2:
            return []
        return [{"constraint": "exclusion", "severity": sev,
                 "predicate": matched[-1]["predicate"], "candidate": matched[-1]["value"],
                 "conflicts_with": self._cite(matched[0])}]

    def _c_referential(self, con, sev, live, candidates):
        known = {n["id"] for n in self.nodes}
        return [{"constraint": "referential", "severity": sev,
                 "predicate": cand["predicate"], "candidate": cand["node"],
                 "conflicts_with": {"claim": None, "value": None, "authority": "binding",
                                    "commit": None, "source": "branch:node-set"}}
                for cand in candidates if cand["node"] not in known]

    def _c_derivation(self, con, sev, live, candidates):
        """Crude: any derived claim on a node whose non-derived inputs a candidate
        changes is treated as stale. A real implementation walks a declared
        derivation graph — see spec section 8.2 step 3."""
        out = []
        for cand in candidates:
            for c in live:
                if (c["authority"] == "derived" and c["node"] == cand["node"]
                        and c["predicate"] != cand["predicate"]):
                    out.append({"constraint": "derivation", "severity": sev,
                                "predicate": c["predicate"], "candidate": cand["value"],
                                "conflicts_with": self._cite(c)})
        return out

    def _c_authority(self, con, sev, live, candidates):
        out = []
        pool = live + candidates
        for i, a in enumerate(pool):
            for b in pool[i + 1:]:
                if (a["node"] == b["node"] and a["predicate"] == b["predicate"]
                        and str(a["value"]) != str(b["value"])
                        and TIERS[a["authority"]] != TIERS[b["authority"]]):
                    lower, higher = sorted((a, b), key=lambda c: TIERS[c["authority"]])
                    out.append({"constraint": "authority", "severity": sev,
                                "predicate": a["predicate"], "candidate": lower["value"],
                                "conflicts_with": self._cite(higher)})
        return out

    # ---------------------------------------------------------- datum.commit

    def commit(self, args, principal):
        """Supersession only.

        Note what is missing: no principal check, and no pre-commit validation of
        ordinary assertions. Both are deliberate. L4-001 and L4-003 catch them.
        """
        changes = args.get("changes", [])
        by_id = {c["id"]: c for c in self.claims}
        new_id = f"cm_{len(self.commits) + 45:04d}"

        for ch in changes:
            if ch["op"] == "supersede":
                target = by_id.get(ch["target"])
                if not target:
                    return {"status": "error", "violations": [],
                            "claims": self.claims,
                            "error": f"unknown target {ch['target']}"}
                successor = next((c["claim"] for c in changes if c["op"] == "assert"), None)
                target["status"] = "superseded"
                target["superseded_by"] = successor
                target["supersession_reason"] = ch.get("note", "")
            elif ch["op"] == "assert":
                self.claims.append({
                    "id": ch["claim"], "node": ch.get("node"),
                    "predicate": ch.get("predicate"), "value": ch.get("value"),
                    "effective": {"from": None, "to": None},
                    "authority": args.get("authority", "binding"),
                    "provenance": {"source": "commit", "asserted_by": principal,
                                   "commit": new_id},
                    "status": "canon"})

        self.commits.append({"id": new_id, "parents": [self._head(args.get("into", "main"))],
                             "author": principal, "authority": args.get("authority", "binding"),
                             "message": args.get("message", ""), "changes": changes,
                             "supersedes": args.get("supersedes", [])})
        for b in self.branches:
            if b["name"] == args.get("into", "main"):
                b["head"] = new_id

        return {"status": "ok", "commit": new_id, "violations": [], "claims": self.claims}

    # ------------------------------------------------------- not implemented

    def propose(self, args, principal):
        raise NotSupported("datum.propose")

    def merge(self, args, principal):
        raise NotSupported("datum.merge")


def _ordinal(marker):
    """Extract a trailing integer from an event marker so intervals can be
    compared. Real implementations resolve markers against an event chain."""
    if marker is None:
        return None
    m = re.search(r"(\d+)$", str(marker))
    return int(m.group(1)) if m else None


def _overlaps(a, b):
    a0, a1 = _ordinal(a.get("from")), _ordinal(a.get("to"))
    b0, b1 = _ordinal(b.get("from")), _ordinal(b.get("to"))
    if None in (a0, b0):
        return False
    a1 = a1 if a1 is not None else float("inf")
    b1 = b1 if b1 is not None else float("inf")
    return a0 < b1 and b0 < a1
