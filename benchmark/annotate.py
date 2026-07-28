#!/usr/bin/env python3
"""GREATGAME annotation harness — the section 7 workflow, enforced.

    python3 benchmark/annotate.py status
    python3 benchmark/annotate.py annotate --annotator A
    python3 benchmark/annotate.py adjudicate --adjudicator lenox
    python3 benchmark/annotate.py kappa
    python3 benchmark/annotate.py holdout --n 10
    python3 benchmark/annotate.py validate
    python3 benchmark/annotate.py show gg_001

Two annotators work independently and blind to each other. Disagreements go to a
third pass and are recorded rather than erased. Cohen's kappa is reported per
class.

Two rules this tool enforces mechanically, because both are easy to violate
under deadline and neither failure is visible afterwards:

  1. An annotator never sees the other's label. `annotate` refuses to display a
     verdict from the other pass and refuses to re-open an instance you have
     already labelled.

  2. A known scholarly reconciliation does not override the annotation. It is
     recorded under scholarly_treatments and shown, but the decision tree still
     runs. A contradiction that scholars have explained away is still a
     contradiction in the text — conflating "resolvable" with "not a conflict"
     collapses the distinction the whole protocol is built on.

Standard library only.
"""

import argparse
import glob
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = os.path.join(HERE, "candidates")
PASSES = os.path.join(HERE, "annotation")
INSTANCES = os.path.join(HERE, "instances")
TEXTS = os.path.join(HERE, "corpus", "texts")
MANIFEST = os.path.join(HERE, "corpus", "manifest.json")

CLASSES = ["conflict", "supersession", "apparent", "uncovered"]
VERDICT_FOR = {"conflict": "conflict", "supersession": "supersession",
               "apparent": "conform", "uncovered": "uncovered"}
HAZARDS = ["implicit", "pronoun", "epithet", "cross_story", "temporal_inference",
           "dialogue_attribution", "unreliable_narrator", "numeric"]
CONSTRAINTS = ["cardinality", "domain", "temporal", "exclusion",
               "referential", "derivation", "authority"]

TARGET = {"conflict": 0.40, "supersession": 0.20, "apparent": 0.30, "uncovered": 0.10}


# ------------------------------------------------------------------ helpers

def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def candidates():
    return [load_json(p) for p in sorted(glob.glob(os.path.join(CANDIDATES, "*.json")))]


def pass_path(annotator, gid):
    return os.path.join(PASSES, annotator, f"{gid}.json")


def read_pass(annotator, gid):
    p = pass_path(annotator, gid)
    return load_json(p) if os.path.exists(p) else None


def excerpt(source, span, pad=220):
    """Pull the passage from the pinned corpus. Refuses to invent context."""
    path = os.path.join(TEXTS, f"{source}.txt")
    if not os.path.exists(path):
        return f"[{source} not built — run: python3 benchmark/corpus/build.py]"
    text = open(path, encoding="utf-8").read()
    a, b = span
    if b > len(text):
        return f"[span {a}:{b} is past the end of {source} ({len(text)} chars) — stale offsets]"
    lo, hi = max(0, a - pad), min(len(text), b + pad)
    return (("…" if lo else "") + text[lo:a] + "  ⟪" + text[a:b] + "⟫  "
            + text[b:hi] + ("…" if hi < len(text) else ""))


def ask(prompt, options=None, allow_blank=False):
    while True:
        if options:
            for i, o in enumerate(options, 1):
                print(f"    {i}. {o}")
        raw = input(f"  {prompt}: ").strip()
        if not raw and allow_blank:
            return None
        if not options:
            if raw:
                return raw
            continue
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        print("    -- not one of the options")


# ------------------------------------------------------------------ commands

def cmd_status(args):
    cands = candidates()
    if not cands:
        print("No candidates. Add instances to benchmark/candidates/ first.")
        return 0

    a = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(PASSES, "A", "*.json"))}
    b = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(PASSES, "B", "*.json"))}
    final = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(INSTANCES, "gg_*.json"))}
    ids = {c["id"] for c in cands}

    print(f"candidates      {len(ids)}")
    print(f"annotator A     {len(a & ids)}")
    print(f"annotator B     {len(b & ids)}")
    print(f"both passes     {len(a & b & ids)}")
    print(f"adjudicated     {len(final)}")
    print(f"target          50 instances, 10 additionally held out\n")

    both = a & b & ids
    if both:
        dis = [g for g in sorted(both)
               if read_pass("A", g)["class"] != read_pass("B", g)["class"]]
        print(f"disagreements   {len(dis)}/{len(both)}"
              + (f" — {', '.join(dis)}" if dis else ""))

    if final:
        counts = {}
        for g in final:
            counts[load_json(os.path.join(INSTANCES, f"{g}.json"))["class"]] = \
                counts.get(load_json(os.path.join(INSTANCES, f"{g}.json"))["class"], 0) + 1
        print("\nclass distribution (adjudicated):")
        for c in CLASSES:
            n = counts.get(c, 0)
            share = n / len(final)
            flag = "" if abs(share - TARGET[c]) < 0.12 else "   <- off target"
            print(f"  {c:14s} {n:3d}  {share:5.0%}  target {TARGET[c]:.0%}{flag}")
    return 0


def cmd_annotate(args):
    who = args.annotator
    if who not in ("A", "B"):
        print("annotator must be A or B", file=sys.stderr)
        return 2

    todo = [c for c in candidates() if not read_pass(who, c["id"])]
    if not todo:
        print(f"Annotator {who}: nothing left.")
        return 0

    print(f"Annotator {who} — {len(todo)} to label. Ctrl-C to stop; progress is saved "
          f"per instance.\n")
    print("Decision tree (section 7):")
    print("  1. Two assertions, same subject and predicate, holding simultaneously")
    print("     with different values?           no -> uncovered or discard")
    print("  2. Same referent, same time, equal authority?")
    print("                                      no -> apparent (record why)")
    print("  3. Later assertion carries an in-world explanation of the change?")
    print("                                     yes -> supersession")
    print("  4. Otherwise                           -> conflict\n")

    for c in todo:
        print("=" * 78)
        print(f"{c['id']}   {c['subject']} · {c['predicate']}")
        if c.get("note"):
            print(f"\n  {c['note']}")
        print()
        for i, a in enumerate(c["assertions"], 1):
            print(f"  [{i}] {a['source']}  {a['value']!r}"
                  f"   authority={a['authority']}"
                  f" narrator_belief={a['narrator_belief']} explicit={a['explicit']}")
            print(f"      {excerpt(a['source'], a['locator']['char_span'])}\n")

        for t in c.get("scholarly_treatments", []):
            print(f"  scholarship — {t['attributed_to']}")
            print(f"      {t['summary']}")
        if c.get("scholarly_treatments"):
            print("\n  A reconciliation does not change the verdict. It populates the\n"
                  "  resolutions array; the text still contains what it contains.\n")

        cls = ask("class", CLASSES)
        rec = {"id": c["id"], "annotator": who, "class": cls,
               "gold_verdict": VERDICT_FOR[cls]}

        if cls == "conflict":
            rec["constraint_type"] = ask("constraint type", CONSTRAINTS)
            rec["severity"] = ask("severity", ["blocking", "advisory"])
        elif cls == "apparent":
            rec["resolution"] = ask("why does it resolve")
        elif cls == "supersession":
            src = ask("explanatory passage source (four-letter)")
            span = ask("explanatory char_span as start,end")
            rec["explanatory_passage"] = {
                "source": src.upper(),
                "char_span": [int(x) for x in span.replace(" ", "").split(",")]}

        rec["difficulty"] = ask("difficulty", ["easy", "medium", "hard"])
        hz = ask("hazards, comma-separated numbers (blank for none)",
                 HAZARDS, allow_blank=True)
        rec["hazards"] = ([HAZARDS[int(i) - 1] for i in hz.replace(" ", "").split(",")]
                          if hz else [])
        note = ask("note (blank to skip)", allow_blank=True)
        if note:
            rec["notes"] = note

        save_json(pass_path(who, c["id"]), rec)
        print(f"  saved {c['id']}\n")
    return 0


def cmd_adjudicate(args):
    cands = {c["id"]: c for c in candidates()}
    pending = []
    for gid in sorted(cands):
        a, b = read_pass("A", gid), read_pass("B", gid)
        if a and b and a["class"] != b["class"]:
            pending.append((gid, a, b))

    agreed = [gid for gid in sorted(cands)
              if read_pass("A", gid) and read_pass("B", gid)
              and read_pass("A", gid)["class"] == read_pass("B", gid)["class"]]

    # Agreement still produces a final instance; it just needs no judgment.
    for gid in agreed:
        finalize(cands[gid], read_pass("A", gid), read_pass("B", gid),
                 read_pass("A", gid), args.adjudicator, agreed=True)
    print(f"{len(agreed)} agreed instance(s) finalized.")

    if not pending:
        print("No disagreements to adjudicate.")
        return 0

    print(f"\n{len(pending)} disagreement(s).\n")
    for gid, a, b in pending:
        c = cands[gid]
        print("=" * 78)
        print(f"{gid}   {c['subject']} · {c['predicate']}")
        for i, asr in enumerate(c["assertions"], 1):
            print(f"\n  [{i}] {asr['source']}  {asr['value']!r}")
            print(f"      {excerpt(asr['source'], asr['locator']['char_span'])}")
        print(f"\n  A said: {a['class']:14s}  B said: {b['class']}")
        note = ask("why did they differ (recorded, not erased)")
        winner = ask("adjudicated class", CLASSES)
        src = a if winner == a["class"] else (b if winner == b["class"] else None)
        finalize(c, a, b, src, args.adjudicator, agreed=False,
                 disagreement_note=note, override_class=winner)
        print(f"  finalized {gid} as {winner}\n")
    return 0


def finalize(cand, a, b, src, adjudicator, agreed, disagreement_note=None,
             override_class=None):
    """Compose the released instance from the candidate and the winning pass."""
    cls = override_class or src["class"]
    inst = {
        "id": cand["id"],
        "class": cls,
        "subject": cand["subject"],
        "predicate": cand["predicate"],
        "assertions": cand["assertions"],
        "gold_verdict": VERDICT_FOR[cls],
        "difficulty": (src or a)["difficulty"],
        "hazards": (src or a)["hazards"],
    }
    if cls == "conflict":
        inst["constraint_type"] = (src or a).get("constraint_type", "cardinality")
        inst["severity"] = (src or a).get("severity", "blocking")
    if cls == "apparent":
        inst["resolution"] = (src or a).get("resolution", "")
    if cls == "supersession" and (src or a).get("explanatory_passage"):
        inst["explanatory_passage"] = (src or a)["explanatory_passage"]
    if cand.get("scholarly_treatments"):
        inst["scholarly_treatments"] = cand["scholarly_treatments"]

    inst["annotation"] = {
        "annotator_a": a["annotator"], "annotator_b": b["annotator"],
        "initial_agreement": agreed, "adjudicated_by": adjudicator,
    }
    if disagreement_note:
        inst["annotation"]["disagreement_note"] = disagreement_note
    if cand.get("notes"):
        inst["notes"] = cand["notes"]

    save_json(os.path.join(INSTANCES, f"{cand['id']}.json"), inst)


def cohens_kappa(pairs):
    """Cohen's kappa over (label_a, label_b) pairs, or None where undefined.

    When both annotators used only one label — which for a one-vs-rest slice
    means the class never occurred — chance agreement is 1 and kappa has no
    value. Returning 1.0 there would put a perfect score next to a class nobody
    ever assigned, and a spurious 1.000 in a results table is worse than a gap.
    """
    n = len(pairs)
    if not n:
        return None
    labels = sorted({x for p in pairs for x in p})
    po = sum(1 for x, y in pairs if x == y) / n
    pe = sum((sum(1 for x, _ in pairs if x == L) / n) *
             (sum(1 for _, y in pairs if y == L) / n) for L in labels)
    return None if pe >= 1 else (po - pe) / (1 - pe)


def cmd_kappa(args):
    ids = [c["id"] for c in candidates()
           if read_pass("A", c["id"]) and read_pass("B", c["id"])]
    if not ids:
        print("No doubly-annotated instances yet.")
        return 0

    pairs = [(read_pass("A", g)["class"], read_pass("B", g)["class"]) for g in ids]
    overall = cohens_kappa(pairs)
    print(f"n = {len(pairs)} doubly annotated")
    print(f"observed agreement  {sum(1 for x, y in pairs if x == y) / len(pairs):.3f}")
    print("Cohen's kappa       " + (f"{overall:.3f}" if overall is not None else "n/a")
          + "\n")
    print("per class (one-vs-rest):")
    for c in CLASSES:
        sub = [(x == c, y == c) for x, y in pairs]
        k = cohens_kappa(sub)
        n = sum(1 for x, y in pairs if c in (x, y))
        note = "" if n else "   (class never assigned)"
        print(f"  {c:14s} n={n:3d}  kappa=" +
              (f"{k:.3f}" if k is not None else "n/a") + note)

    print("\nconfusion (A down, B across):")
    print("       " + "".join(f"{c[:6]:>8s}" for c in CLASSES))
    for ca in CLASSES:
        row = "".join(f"{sum(1 for x, y in pairs if x == ca and y == cb):8d}"
                      for cb in CLASSES)
        print(f"  {ca[:5]:5s}{row}")
    print("\nExpect the lowest kappa on apparent vs conflict. That expectation is in\n"
          "the datasheet in advance, so the result cannot be presented as a surprise.")
    return 0


def cmd_holdout(args):
    files = sorted(glob.glob(os.path.join(INSTANCES, "gg_*.json")))
    if len(files) < args.n:
        print(f"only {len(files)} instances; need at least {args.n}", file=sys.stderr)
        return 2
    rng = random.Random(args.seed)
    chosen = sorted(rng.sample(files, args.n))
    out = {"seed": args.seed, "n": args.n,
           "note": "Held-out split, published as hashes only. The instances are "
                   "withheld from the public release; these digests let anyone verify "
                   "after the fact that the split was fixed in advance.",
           "hashes": {}}
    for f in chosen:
        inst = load_json(f)
        inst["held_out"] = True
        save_json(f, inst)
        out["hashes"][inst["id"]] = hashlib.sha256(
            json.dumps(inst, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    save_json(os.path.join(INSTANCES, "holdout.json"), out)
    print(f"{args.n} instances marked held_out; digests in instances/holdout.json")
    return 0


def cmd_validate(args):
    errs = []
    manifest = load_json(MANIFEST) if os.path.exists(MANIFEST) else {"works": {}}
    files = sorted(glob.glob(os.path.join(INSTANCES, "gg_*.json")))
    files += sorted(glob.glob(os.path.join(CANDIDATES, "*.json")))

    for path in files:
        inst = load_json(path)
        w = os.path.basename(path)
        for a in inst.get("assertions", []):
            src, span = a.get("source"), a.get("locator", {}).get("char_span")
            if src not in manifest["works"]:
                errs.append(f"{w}: {src} is not a work in the pinned manifest")
                continue
            if not span or len(span) != 2 or span[0] >= span[1]:
                errs.append(f"{w}: malformed char_span {span}")
                continue
            if span[1] > manifest["works"][src]["chars"]:
                errs.append(f"{w}: span {span} exceeds {src} "
                            f"({manifest['works'][src]['chars']} chars)")
        if "class" in inst and inst["class"] not in CLASSES:
            errs.append(f"{w}: unknown class {inst['class']!r}")
        if "gold_verdict" in inst and inst["gold_verdict"] != VERDICT_FOR[inst["class"]]:
            errs.append(f"{w}: class {inst['class']} implies gold_verdict "
                        f"{VERDICT_FOR[inst['class']]}, found {inst['gold_verdict']}")
        for t in inst.get("scholarly_treatments", []):
            if len(t.get("summary", "")) > 400:
                errs.append(f"{w}: scholarly summary over 400 chars — paraphrase, "
                            f"never reproduce")

    print(f"checked {len(files)} file(s)")
    if errs:
        print(f"\n{len(errs)} error(s):")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("All checks passed.")
    return 0


def cmd_show(args):
    for c in candidates():
        if c["id"] != args.id:
            continue
        print(f"{c['id']}   {c['subject']} · {c['predicate']}\n")
        for i, a in enumerate(c["assertions"], 1):
            print(f"[{i}] {a['source']}  {a['value']!r}  span={a['locator']['char_span']}")
            print(f"    {excerpt(a['source'], a['locator']['char_span'], pad=400)}\n")
        for w in ("A", "B"):
            p = read_pass(w, c["id"])
            print(f"pass {w}: {p['class'] if p else '—'}")
        return 0
    print(f"no candidate {args.id}", file=sys.stderr)
    return 2


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(fn=cmd_status)

    ann = sub.add_parser("annotate")
    ann.add_argument("--annotator", required=True, help="A or B")
    ann.set_defaults(fn=cmd_annotate)

    adj = sub.add_parser("adjudicate")
    adj.add_argument("--adjudicator", required=True)
    adj.set_defaults(fn=cmd_adjudicate)

    sub.add_parser("kappa").set_defaults(fn=cmd_kappa)

    ho = sub.add_parser("holdout")
    ho.add_argument("--n", type=int, default=10)
    ho.add_argument("--seed", type=int, default=1911,
                    help="fixed so the split is reproducible; 1911 is Knox")
    ho.set_defaults(fn=cmd_holdout)

    sub.add_parser("validate").set_defaults(fn=cmd_validate)

    sh = sub.add_parser("show")
    sh.add_argument("id")
    sh.set_defaults(fn=cmd_show)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
