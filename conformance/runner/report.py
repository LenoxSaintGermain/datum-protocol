"""Assertion evaluation, path resolution, and level scoring."""

import re

LEVELS = ["L1-read", "L2-check", "L3-supersession",
          "L4-authority", "L5-merge", "L6-federation"]

CORE = LEVELS[:4]
COMPLETE = LEVELS

_MISSING = object()


def resolve(obj, path):
    """Resolve a vector path into a list of matched values.

    Grammar: '$' root, '.key', '[n]' index, '[*]' every element,
    '[?key=value]' select array members whose field equals value.

    Returns [] when nothing matches, which is what 'absent' tests for.
    """
    if not path.startswith("$"):
        raise ValueError(f"path must start with $: {path}")

    current = [obj]
    for token in _tokenize(path[1:]):
        nxt = []
        for node in current:
            nxt.extend(_step(node, token))
        current = nxt
    return current


def _tokenize(path):
    return re.findall(r"\.([A-Za-z_][A-Za-z0-9_]*)|\[([^\]]*)\]", path)


def _step(node, token):
    key, bracket = token
    if key:
        if isinstance(node, dict) and key in node:
            return [node[key]]
        return []

    if bracket == "*":
        return list(node) if isinstance(node, list) else []

    if bracket.startswith("?"):
        field, _, want = bracket[1:].partition("=")
        if not isinstance(node, list):
            return []
        return [m for m in node
                if isinstance(m, dict) and _as_text(m.get(field, _MISSING)) == want]

    if isinstance(node, list):
        try:
            return [node[int(bracket)]]
        except (ValueError, IndexError):
            return []
    return []


def _as_text(v):
    if v is _MISSING:
        return None
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def evaluate(response, expectation):
    """Return (ok, detail) for one expectation against a response."""
    path, op = expectation["path"], expectation["op"]
    want = expectation.get("value")
    got = resolve(response, path)

    if op == "absent":
        return (not got, f"{path} resolved to {got!r}, expected nothing")

    if op == "exists":
        ok = bool(got) and any(v is not None for v in got)
        return (ok, f"{path} not present")

    if op == "each_has":
        if not got:
            return (False, f"{path} matched nothing, so 'every' is vacuous — "
                           f"a guarantee that holds over an empty set is not a guarantee")
        missing = [i for i, v in enumerate(got)
                   if not isinstance(v, dict) or want not in v]
        return (not missing, f"{path}: elements {missing} lack {want!r}")

    if op == "length":
        if len(got) != 1 or not isinstance(got[0], list):
            return (False, f"{path} is not a single list (got {got!r})")
        return (len(got[0]) == want,
                f"{path} has length {len(got[0])}, expected {want}")

    if not got:
        return (False, f"{path} not present")

    if op == "eq":
        bad = [v for v in got if v != want]
        return (not bad, f"{path} = {got if len(got) > 1 else got[0]!r}, expected {want!r}")

    if op == "neq":
        bad = [v for v in got if v == want]
        return (not bad, f"{path} = {want!r}, expected anything else")

    if op == "contains":
        bad = [v for v in got if want not in (v or "")]
        return (not bad, f"{path} = {got[0]!r}, expected to contain {want!r}")

    if op in ("gte", "lte"):
        cmp = (lambda v: v >= want) if op == "gte" else (lambda v: v <= want)
        bad = [v for v in got if not cmp(v)]
        return (not bad, f"{path} = {got[0]!r}, expected {op} {want!r}")

    if op == "subset_of":
        vals = got[0] if len(got) == 1 and isinstance(got[0], list) else got
        extra = [v for v in vals if v not in want]
        return (not extra, f"{path} has members outside {want!r}: {extra!r}")

    raise ValueError(f"unknown op: {op}")


def score(results):
    """Group per-vector results into level verdicts and a badge."""
    levels = {}
    for r in results:
        lv = levels.setdefault(r["level"], {"pass": 0, "fail": 0, "must_fail": 0,
                                            "should_fail": 0, "vectors": []})
        lv["vectors"].append(r)
        if r["passed"]:
            lv["pass"] += 1
        else:
            lv["fail"] += 1
            lv["must_fail" if r["normative"] == "MUST" else "should_fail"] += 1

    for lv in levels.values():
        lv["conformant"] = lv["must_fail"] == 0 and lv["pass"] > 0

    def clears(names):
        return all(levels.get(n, {}).get("conformant") for n in names)

    badge = ("Datum v0.2 Complete" if clears(COMPLETE)
             else "Datum v0.2 Core" if clears(CORE)
             else None)

    return levels, badge


def render(levels, badge, adapter_name):
    out = [f"Datum conformance — adapter: {adapter_name}", ""]

    for name in LEVELS:
        lv = levels.get(name)
        if not lv:
            out.append(f"  {name:18s}  no vectors")
            continue
        mark = "PASS" if lv["conformant"] else "FAIL"
        out.append(f"  {mark}  {name:18s} {lv['pass']}/{lv['pass'] + lv['fail']}")
        for v in lv["vectors"]:
            if not v["passed"]:
                out.append(f"          {v['id']}  {v['description']}")
                for d in v["details"]:
                    out.append(f"              - {d}")

    out.append("")
    if badge:
        out.append(f"  Badge: {badge}")
    else:
        core = [n for n in CORE if not levels.get(n, {}).get("conformant")]
        out.append(f"  Badge: none. Core requires {', '.join(CORE)}; failing: {', '.join(core)}")
    return "\n".join(out)
