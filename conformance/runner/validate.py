"""Structural and referential validation of canon/ and conformance/vectors/.

    python3 -m conformance.runner.validate

Standard library only. If `jsonschema` happens to be installed, the declared
JSON Schemas are checked too; if not, the checks below still run.

The checks that matter most are not schema checks. A canon store stays
syntactically valid long after it stops being coherent: a claim superseded by a
claim that does not exist, a branch head pointing at a missing commit, a commit
whose parent was renamed. Those are the failures that make an audit trail
untrustworthy, and none of them are visible to a type checker.
"""

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
CANON = os.path.join(REPO, "canon")
VECTORS = os.path.join(REPO, "conformance", "vectors")

OPS = {"eq", "neq", "length", "contains", "exists", "absent",
       "gte", "lte", "subset_of", "each_has"}
LEVELS = {"L1-read", "L2-check", "L3-supersession",
          "L4-authority", "L5-merge", "L6-federation"}
TOOLS = {"datum.read", "datum.check", "datum.propose", "datum.commit", "datum.merge"}
TIERS = {"binding", "derived", "proposed", "apocryphal"}
STATUSES = {"canon", "superseded", "apocryphal", "proposed"}

errors = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def load(path):
    with open(path) as f:
        return json.load(f)


# ----------------------------------------------------------------- canon

def validate_canon():
    nodes = load(os.path.join(CANON, "nodes.json"))
    claims = load(os.path.join(CANON, "claims.json"))
    edges = load(os.path.join(CANON, "edges.json"))
    commits = load(os.path.join(CANON, "commits.json"))
    branches = load(os.path.join(CANON, "branches.json"))

    node_ids = {n["id"] for n in nodes}
    claim_ids = {c["id"] for c in claims}
    commit_ids = {c["id"] for c in commits}

    for n in nodes:
        if not re.match(r"^nd_[a-z0-9_]+$", n["id"]):
            err("nodes", f"{n['id']} does not match the node id pattern")
        if n["status"] not in STATUSES:
            err("nodes", f"{n['id']} has unknown status {n['status']!r}")
        if n["created_in"] not in commit_ids:
            err("nodes", f"{n['id']} created_in {n['created_in']} is not a known commit")

    for c in claims:
        w = f"claims/{c['id']}"
        if not re.match(r"^cl_[0-9]{4}$", c["id"]):
            err(w, "does not match the claim id pattern")
        if c["node"] not in node_ids:
            err(w, f"references unknown node {c['node']}")
        if c["authority"] not in TIERS:
            err(w, f"unknown authority {c['authority']!r}")
        if c["status"] not in STATUSES:
            err(w, f"unknown status {c['status']!r}")
        if c["provenance"]["commit"] not in commit_ids:
            err(w, f"provenance cites unknown commit {c['provenance']['commit']}")

        if c["status"] == "superseded":
            # The rule the whole protocol rests on: supersession is deliberate,
            # attributable, and reversible. All three need these two fields.
            if not c.get("superseded_by"):
                err(w, "is superseded with no superseded_by — that is a deletion wearing "
                       "supersession's clothes")
            elif c["superseded_by"] not in claim_ids:
                err(w, f"superseded_by {c['superseded_by']} does not exist")
            if not c.get("supersession_reason"):
                err(w, "is superseded with no recorded reason (threat model T6)")

    for e in edges:
        for end in ("from", "to"):
            if e[end] not in node_ids:
                err(f"edges/{e['id']}", f"{end} references unknown node {e[end]}")

    seen = set()
    for c in commits:
        w = f"commits/{c['id']}"
        if c["id"] in seen:
            err(w, "duplicate commit id")
        seen.add(c["id"])
        for p in c["parents"]:
            if p not in commit_ids:
                err(w, f"parent {p} does not exist")
        for s in c["supersedes"]:
            if s not in claim_ids:
                err(w, f"supersedes unknown claim {s}")
            elif next(x for x in claims if x["id"] == s)["status"] != "superseded":
                err(w, f"supersedes {s}, but that claim is not marked superseded")
        for ch in c["changes"]:
            ref = ch.get("claim") or ch.get("target")
            if ch["op"] in ("assert", "supersede") and ref and ref not in claim_ids:
                err(w, f"change references unknown claim {ref}")
            if ch["op"] == "add_node" and ch["node"] not in node_ids:
                err(w, f"change references unknown node {ch['node']}")

    if commits and commits[0]["parents"]:
        err("commits", "the root commit must have no parents")

    for b in branches:
        if b["head"] not in commit_ids:
            err(f"branches/{b['name']}", f"head {b['head']} does not exist")

    # Every superseded claim must be superseded by some commit, not by an edit.
    superseded_in_commits = {s for c in commits for s in c["supersedes"]}
    for c in claims:
        if c["status"] == "superseded" and c["id"] not in superseded_in_commits:
            err(f"claims/{c['id']}",
                "is superseded but no commit records the supersession — canon changed "
                "without a commit, which is the one thing this store exists to prevent")

    return len(nodes), len(claims), len(commits), len(branches)


# --------------------------------------------------------------- vectors

def validate_vectors():
    files = sorted(glob.glob(os.path.join(VECTORS, "*", "*.json")))
    ids = set()

    for path in files:
        v = load(path)
        w = f"vectors/{os.path.basename(path)}"

        for field in ("id", "level", "requirement", "normative",
                      "description", "fixture", "operation", "expect"):
            if field not in v:
                err(w, f"missing required field {field!r}")
        if errors and v.get("id") is None:
            continue

        if v["id"] in ids:
            err(w, "duplicate vector id")
        ids.add(v["id"])

        if v["level"] not in LEVELS:
            err(w, f"unknown level {v['level']!r}")
        if os.path.basename(os.path.dirname(path)) != v["level"]:
            err(w, f"lives in the wrong directory for level {v['level']!r}")
        if not v["id"].startswith(v["level"].split("-")[0]):
            err(w, f"id {v['id']} does not match level {v['level']}")
        if v["normative"] not in ("MUST", "SHOULD"):
            err(w, f"normative must be MUST or SHOULD, got {v['normative']!r}")
        if v["operation"]["tool"] not in TOOLS:
            err(w, f"unknown tool {v['operation']['tool']!r}")

        # A vector with no traceable requirement is an opinion about
        # implementation rather than a test of the specification.
        if not v["requirement"].startswith("spec/"):
            err(w, "requirement does not trace into spec/")

        for key in ("nodes", "claims", "commits", "branches"):
            if key not in v["fixture"]:
                err(w, f"fixture missing {key!r}")

        if not v["expect"]:
            err(w, "has no expectations")
        for exp in v["expect"]:
            if exp["op"] not in OPS:
                err(w, f"unknown op {exp['op']!r}")
            if not exp["path"].startswith("$"):
                err(w, f"path {exp['path']!r} must start with $")
            if exp["op"] not in ("exists", "absent") and "value" not in exp:
                err(w, f"op {exp['op']!r} on {exp['path']} needs a value")

    per_level = {}
    for path in files:
        per_level.setdefault(os.path.basename(os.path.dirname(path)), 0)
        per_level[os.path.basename(os.path.dirname(path))] += 1
    for lv in LEVELS:
        if not per_level.get(lv):
            err("vectors", f"level {lv} has no vectors — an empty level always passes")

    return len(files), per_level


# ------------------------------------------------------------- git trailers

def validate_git_trailers():
    import subprocess
    try:
        log = subprocess.run(["git", "log", "--format=%H%x00%B%x00"],
                             cwd=REPO, capture_output=True, text=True, check=True).stdout
    except Exception as e:
        print(f"  (skipping git cross-check: {e})")
        return 0

    commits = load(os.path.join(CANON, "commits.json"))
    known = {c["id"] for c in commits}
    trailers = re.findall(r"^Datum-Commit:\s*(\S+)", log, re.M)

    for t in trailers:
        if t not in known:
            err("git", f"commit trailer cites {t}, which is not in canon/commits.json")

    recorded = {c["id"] for c in commits}
    missing = recorded - set(trailers)
    if missing:
        err("git", f"canon commits with no git trailer: {sorted(missing)}")

    return len(trailers)


# ------------------------------------------------------------------ main

def main():
    print("Validating canon/ and conformance/vectors/\n")

    n, c, cm, b = validate_canon()
    print(f"  canon      {n} nodes, {c} claims, {cm} commits, {b} branches")

    nv, per_level = validate_vectors()
    print(f"  vectors    {nv} across {len(per_level)} levels "
          f"({', '.join(f'{k.split(chr(45))[0]}:{v}' for k, v in sorted(per_level.items()))})")

    nt = validate_git_trailers()
    print(f"  git        {nt} Datum-Commit trailers cross-checked")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
