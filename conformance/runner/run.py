"""Datum conformance runner.

    python3 -m conformance.runner.run --adapter mock
    python3 -m conformance.runner.run --adapter mock --level L3-supersession
    python3 -m conformance.runner.run --adapter yourpkg.mod:YourAdapter --json

Exit code is non-zero when any MUST vector fails, so this is usable as a gate.
"""

import argparse
import importlib
import json
import os
import sys
import traceback

from . import report
from .adapter import NotSupported

HERE = os.path.dirname(os.path.abspath(__file__))
VECTORS = os.path.normpath(os.path.join(HERE, "..", "vectors"))


def load_vectors(level=None):
    found = []
    for lv in sorted(os.listdir(VECTORS)):
        d = os.path.join(VECTORS, lv)
        if not os.path.isdir(d) or (level and lv != level):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".json"):
                with open(os.path.join(d, fn)) as f:
                    found.append(json.load(f))
    return found


def load_adapter(spec):
    """'mock' resolves to the bundled mock; otherwise 'module:Class'."""
    if ":" not in spec:
        spec = f"conformance.runner.adapters.{spec}:Adapter"
    module, _, cls = spec.partition(":")
    return getattr(importlib.import_module(module), cls)()


def run_vector(adapter, vector):
    result = {"id": vector["id"], "level": vector["level"],
              "normative": vector["normative"],
              "description": vector["description"],
              "passed": False, "details": []}

    op = vector["operation"]
    try:
        adapter.load_fixture(vector["fixture"])
        response = adapter.dispatch(op["tool"], op["args"], op.get("principal", "user:test"))
    except NotSupported as e:
        result["details"].append(f"adapter does not implement {e}")
        return result
    except Exception:
        result["details"].append("adapter raised: " +
                                 traceback.format_exc().strip().splitlines()[-1])
        return result

    if not isinstance(response, dict):
        result["details"].append(f"adapter returned {type(response).__name__}, expected dict")
        return result

    for exp in vector["expect"]:
        try:
            ok, detail = report.evaluate(response, exp)
        except Exception as e:
            ok, detail = False, f"{exp['path']}: {e}"
        if not ok:
            note = exp.get("note")
            result["details"].append(detail + (f"  ({note})" if note else ""))

    result["passed"] = not result["details"]
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description="Run the Datum conformance suite.")
    p.add_argument("--adapter", default="mock",
                   help="'mock', or 'module:Class' for your implementation")
    p.add_argument("--level", default=None, choices=report.LEVELS + [None],
                   help="run a single level")
    p.add_argument("--json", action="store_true", help="emit machine-readable results")
    p.add_argument("--expect-profile", default=None,
                   help="comma-separated levels expected to be conformant; "
                        "exits non-zero if the actual set differs. Used by CI to assert "
                        "that a deliberately partial adapter still fails where it should.")
    args = p.parse_args(argv)

    adapter = load_adapter(args.adapter)
    vectors = load_vectors(args.level)
    if not vectors:
        print("no vectors found", file=sys.stderr)
        return 2

    results = [run_vector(adapter, v) for v in vectors]
    levels, badge = report.score(results)

    if args.json:
        print(json.dumps({
            "adapter": getattr(adapter, "name", args.adapter),
            "badge": badge,
            "levels": {k: {kk: vv for kk, vv in v.items() if kk != "vectors"}
                       for k, v in levels.items()},
            "vectors": results,
        }, indent=2))
    else:
        print(report.render(levels, badge, getattr(adapter, "name", args.adapter)))

    if args.expect_profile is not None:
        want = {s for s in args.expect_profile.split(",") if s}
        got = {k for k, v in levels.items() if v["conformant"]}
        if want != got:
            print(f"\nprofile mismatch: expected conformant {sorted(want)}, "
                  f"got {sorted(got)}", file=sys.stderr)
            return 1
        print(f"\nprofile matches: {sorted(got)} conformant, "
              f"{sorted(set(report.LEVELS) - got)} not — as expected.")
        return 0

    return 0 if all(r["passed"] or r["normative"] != "MUST" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
