#!/usr/bin/env python3
"""Fetch, normalize, split, and checksum the Doyle corpus.

    python3 benchmark/corpus/build.py           # build and write manifest.json
    python3 benchmark/corpus/build.py --verify  # rebuild and assert checksums match

Corpus text is never committed. This script reconstructs it byte-for-byte from
pinned Project Gutenberg editions, and `--verify` is what proves the
reconstruction is exact. Annotation character offsets are meaningless without
that guarantee: they are offsets into *this* normalized text and will silently
point at the wrong words in any other edition.

Normalization is deliberately minimal — Project Gutenberg wrapper removed, CRLF
to LF, outer whitespace stripped, nothing else. Every additional transformation
is another chance for offsets to drift, and the text's own curly quotes,
em-dashes, and italics markers are left exactly as Gutenberg has them.

Standard library only.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TEXTS = os.path.join(HERE, "texts")
CACHE = os.path.join(HERE, ".cache")
WORKS = os.path.join(HERE, "works.json")
MANIFEST = os.path.join(HERE, "manifest.json")

URL = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"

# A work shorter than this is almost certainly a mis-split rather than a story.
MIN_WORK_CHARS = 8000
# The table of contents is a contiguous run of titles near the top. If every
# title's first occurrence falls inside a span this small, that span is the TOC.
TOC_SPAN = 6000


def download(url, path):
    """urllib first; fall back to curl.

    Corporate proxies and MITM TLS inspection break urllib's certificate chain
    routinely, and a corpus builder that only runs on unproxied networks is a
    corpus nobody else can verify. curl uses the system trust store and usually
    works where urllib does not.
    """
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            open(path, "wb").write(r.read())
        return
    except urllib.error.URLError as e:
        print(f"    urllib failed ({e.reason}); trying curl")

    import shutil
    import subprocess
    if not shutil.which("curl"):
        raise SystemExit(f"cannot fetch {url}: urllib failed and curl is not installed")
    subprocess.run(["curl", "-sSL", "--fail", "-o", path, url], check=True)


def fetch(gid):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"pg{gid}.txt")
    if not os.path.exists(path):
        print(f"    fetching {gid}")
        download(URL.format(id=gid), path)
    return open(path, encoding="utf-8").read()


def strip_wrapper(raw):
    """Remove the Project Gutenberg header and footer."""
    start = re.search(r"\*\*\* START OF TH(?:E|IS) PROJECT GUTENBERG EBOOK.*?\*\*\*\r?\n", raw)
    end = re.search(r"\*\*\* END OF TH(?:E|IS) PROJECT GUTENBERG EBOOK", raw)
    if not start or not end:
        raise SystemExit("could not locate Project Gutenberg start/end markers")
    return raw[start.end():end.start()]


def normalize(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def key(s):
    """Comparison form for a title line: drop a roman-numeral prefix, unify
    quotes and dashes, collapse whitespace, casefold."""
    s = re.sub(r"^\s*[IVXL]+\.\s*", "", s)
    s = s.replace("_", "")
    s = re.sub(r"[‘’“”]", "'", s)
    s = re.sub(r"[‐-―]", "-", s)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return s.strip()


def line_offsets(text):
    """(offset, line) for every line."""
    out, pos = [], 0
    for line in text.split("\n"):
        out.append((pos, line))
        pos += len(line) + 1
    return out


def find_starts(body, titles):
    """Locate the body start offset of each work, in order.

    Returns a list of offsets aligned with `titles`. Raises if any title cannot
    be located unambiguously — a corpus that splits wrong is worse than one that
    refuses to split, because the failure shows up months later as an annotation
    pointing at the wrong sentence.
    """
    wanted = [key(t) for t in titles]
    lines = line_offsets(body)

    matches = {i: [] for i in range(len(wanted))}
    for off, line in lines:
        k = key(line)
        if not k:
            continue
        for i, w in enumerate(wanted):
            if k == w:
                matches[i].append(off)

    missing = [titles[i] for i in range(len(wanted)) if not matches[i]]
    if missing:
        raise SystemExit(f"could not locate: {missing}")

    # Drop the table of contents: if the first occurrence of every title falls
    # within one short span, that span is the TOC and none of it is body text.
    firsts = [matches[i][0] for i in range(len(wanted))]
    if len(wanted) > 1 and max(firsts) - min(firsts) < TOC_SPAN:
        cutoff = max(firsts)
        for i in matches:
            later = [m for m in matches[i] if m > cutoff]
            if later:
                matches[i] = later

    # Greedy in-order selection: each work starts after the previous one.
    starts, prev = [], -1
    for i in range(len(wanted)):
        nxt = next((m for m in matches[i] if m > prev), None)
        if nxt is None:
            raise SystemExit(f"no in-order occurrence of {titles[i]!r} after offset {prev}")
        starts.append(nxt)
        prev = nxt
    return starts


def split_source(src, body):
    titles = [w["title"] for w in src["works"]]

    if len(titles) == 1:
        return [(src["works"][0], 0, len(body), body)]

    starts = find_starts(body, titles)
    out = []
    for i, w in enumerate(src["works"]):
        a = starts[i]
        b = starts[i + 1] if i + 1 < len(starts) else len(body)
        text = body[a:b].strip()
        out.append((w, a, b, text))
    return out


def build(verify=False):
    spec = json.load(open(WORKS))
    os.makedirs(TEXTS, exist_ok=True)

    manifest = {
        "corpus": "Doyle Sherlock Holmes canon",
        "public_domain": "United States, as of 1 January 2023",
        "retrieved_from": "Project Gutenberg",
        "normalization": [
            "Project Gutenberg header and footer removed",
            "CRLF and CR normalized to LF",
            "leading and trailing whitespace of each work stripped",
            "no other transformation — curly quotes, dashes, and italic markers left as-is"
        ],
        "offset_convention": "char_span indices are Python string indices into the normalized per-work text produced by this script, decoded as UTF-8",
        "sources": [],
        "works": {},
    }

    total = 0
    for src in spec["sources"]:
        gid = src["gutenberg_id"]
        raw = fetch(gid)
        body = normalize(strip_wrapper(raw))

        entry = {
            "gutenberg_id": gid,
            "title": src["title"],
            "kind": src["kind"],
            "url": URL.format(id=gid),
            "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "normalized_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "normalized_chars": len(body),
            "works": [w["abbrev"] for w in src["works"]],
        }
        if "edition_note" in src:
            entry["edition_note"] = src["edition_note"]
        manifest["sources"].append(entry)

        for w, a, b, text in split_source(src, body):
            if len(text) < MIN_WORK_CHARS:
                raise SystemExit(
                    f"{w['abbrev']} split to {len(text)} chars, below the {MIN_WORK_CHARS} "
                    f"floor — this is a mis-split, not a short story")
            manifest["works"][w["abbrev"]] = {
                "title": w["title"],
                "source": gid,
                "chars": len(text),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
            open(os.path.join(TEXTS, f"{w['abbrev']}.txt"), "w", encoding="utf-8").write(text)
            total += 1

        print(f"  {gid:>5}  {src['title'][:44]:44s} {len(src['works']):2d} work(s)")

    manifest["work_count"] = total
    manifest["story_count"] = sum(1 for s in spec["sources"] if s["kind"] == "collection"
                                  for _ in s["works"])
    manifest["novel_count"] = sum(1 for s in spec["sources"] if s["kind"] == "novel")

    if verify:
        if not os.path.exists(MANIFEST):
            raise SystemExit("no manifest.json to verify against")
        old = json.load(open(MANIFEST))
        drift = [k for k, v in manifest["works"].items()
                 if old["works"].get(k, {}).get("sha256") != v["sha256"]]
        gone = sorted(set(old["works"]) - set(manifest["works"]))
        if drift or gone:
            print(f"\nCHECKSUM DRIFT — every annotation offset into these works is now suspect.")
            for k in drift:
                print(f"  changed: {k}")
            for k in gone:
                print(f"  missing: {k}")
            return 1
        print(f"\nVerified: {total} works, all checksums match the pinned manifest.")
        return 0

    json.dump(manifest, open(MANIFEST, "w"), indent=2)
    open(MANIFEST, "a").write("\n")
    print(f"\n{total} works ({manifest['novel_count']} novels, "
          f"{manifest['story_count']} stories) written to texts/ and pinned in manifest.json")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--verify", action="store_true",
                   help="rebuild and assert every checksum matches the pinned manifest")
    sys.exit(build(p.parse_args().verify))
