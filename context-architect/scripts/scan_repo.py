#!/usr/bin/env python3
"""Deterministic repository inventory for context-architect.

Usage:
  python scan_repo.py [ROOT] [--json] [--partition-loc N]

Prints topology, languages, manifests, tooling, existing context files, a
delegation verdict (inline vs. subagents) and suggested partitions for subagents.
Reads file metadata only; never modifies the repository.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (MANIFESTS, SOURCE_EXT, classify_tooling, count_lines,  # noqa: E402
                     list_files)

# Delegation thresholds (see references/subagent-delegation.md)
DELEGATE_FILES = 800
DELEGATE_LOC = 80_000
DELEGATE_PACKAGES = 6
MAX_AGG_DEPTH = 5

CONTEXT_FILES = ("CLAUDE.md", "GEMINI.md", "AGENTS.md", ".cursorrules", "scratchpad.md",
                 "copilot-instructions.md")
WORKSPACE_MARKERS = ("pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json", "go.work")
MONOREPO_DIRS = ("apps", "packages", "services", "libs", "modules", "crates")


def build_partitions(agg, children, target):
    """Recursively split heavy dirs, then bin-pack small siblings."""
    def split(d):
        st = agg[d]
        kids = children.get(d, [])
        if st["loc"] <= target or not kids:
            return [d]
        out = []
        for k in kids:
            out += split(k)
        return out

    leaves = []
    for top in children.get("", []):
        leaves += split(top)

    by_parent = defaultdict(list)
    for leaf in leaves:
        by_parent[leaf.rsplit("/", 1)[0] if "/" in leaf else ""].append(leaf)

    parts = []
    for parent, group in sorted(by_parent.items()):
        group.sort(key=lambda g: -agg[g]["loc"])
        bins = []
        for g in group:
            for b in bins:
                if b["loc"] + agg[g]["loc"] <= target:
                    b["paths"].append(g)
                    b["loc"] += agg[g]["loc"]
                    b["files"] += agg[g]["files"]
                    break
            else:
                bins.append({"paths": [g], "loc": agg[g]["loc"], "files": agg[g]["files"]})
        for b in bins:
            b["oversize"] = b["loc"] > target * 1.5
            parts.append(b)
    parts.sort(key=lambda p: -p["loc"])
    return parts


def scan(root, target):
    files, is_git = list_files(root)
    lang_loc, lang_files = defaultdict(int), defaultdict(int)
    agg = defaultdict(lambda: {"files": 0, "loc": 0})
    children = defaultdict(set)
    manifests, tooling, context_found = [], defaultdict(set), []
    package_roots, root_files = set(), []
    total_loc = 0

    for rel in files:
        parts = rel.split("/")
        base = parts[-1]
        for tool, cat in classify_tooling(rel):
            tooling[cat].add(tool)
        if base in MANIFESTS:
            manifests.append(rel)
            if len(parts) > 1 and base not in ("requirements.txt",):
                package_roots.add("/".join(parts[:-1]))
        if base in CONTEXT_FILES or rel.startswith((".claude/", ".gemini/")):
            context_found.append(rel)
        ext = os.path.splitext(base)[1].lower()
        if len(parts) == 1:
            root_files.append(rel)
        if ext in SOURCE_EXT:
            loc = count_lines(os.path.join(root, rel))
            lang_loc[SOURCE_EXT[ext]] += loc
            lang_files[SOURCE_EXT[ext]] += 1
            total_loc += loc
            for depth in range(1, min(len(parts), MAX_AGG_DEPTH + 1)):
                key = "/".join(parts[:depth])
                agg[key]["files"] += 1
                agg[key]["loc"] += loc
                parent = "/".join(parts[:depth - 1])
                children[parent].add(key)

    children = {k: sorted(v) for k, v in children.items()}
    src_files = sum(lang_files.values())

    markers = [m for m in WORKSPACE_MARKERS if m in root_files]
    top_dirs = {p.split("/")[0] for p in files if "/" in p}
    mono_dirs = [d for d in MONOREPO_DIRS if d in top_dirs]
    if "package.json" in root_files:
        try:
            with open(os.path.join(root, "package.json"), encoding="utf-8") as fh:
                if "workspaces" in json.load(fh):
                    markers.append("package.json#workspaces")
        except (OSError, ValueError):
            pass
    is_monorepo = bool(markers) or (len(package_roots) >= 3 and bool(mono_dirs))

    reasons = []
    if len(files) >= DELEGATE_FILES:
        reasons.append(f"{len(files)} files >= {DELEGATE_FILES}")
    if total_loc >= DELEGATE_LOC:
        reasons.append(f"~{total_loc} source LOC >= {DELEGATE_LOC}")
    if len(package_roots) >= DELEGATE_PACKAGES:
        reasons.append(f"{len(package_roots)} packages >= {DELEGATE_PACKAGES}")
    delegate = bool(reasons)

    partitions = build_partitions(agg, children, target) if delegate else []

    top_stats = sorted(((k, v) for k, v in agg.items() if "/" not in k),
                       key=lambda kv: -kv[1]["loc"])

    return {
        "root": os.path.abspath(root),
        "git": is_git,
        "total_files": len(files),
        "source_files": src_files,
        "source_loc": total_loc,
        "languages": sorted(({"language": k, "files": lang_files[k], "loc": v}
                             for k, v in lang_loc.items()), key=lambda x: -x["loc"]),
        "topology": {"monorepo": is_monorepo, "markers": markers,
                     "package_roots": sorted(package_roots)},
        "manifests": sorted(manifests)[:60],
        "tooling": {k: sorted(v) for k, v in sorted(tooling.items())},
        "existing_context": sorted(context_found),
        "top_level_dirs": [{"path": k, **v} for k, v in top_stats[:30]],
        "delegation": {"recommended": delegate, "reasons": reasons,
                       "partition_target_loc": target},
        "partitions": [{"id": i + 1, "paths": p["paths"], "files": p["files"],
                        "loc": p["loc"], "oversize": p["oversize"]}
                       for i, p in enumerate(partitions)],
    }


def render_text(r):
    L = []
    L.append(f"REPO SCAN: {r['root']}")
    L.append(f"git: {'yes' if r['git'] else 'no'} | files: {r['total_files']} | "
             f"source files: {r['source_files']} | source LOC: ~{r['source_loc']}")
    langs = ", ".join(f"{x['language']} {x['loc']}" for x in r["languages"][:8]) or "none detected"
    L.append(f"Languages (LOC): {langs}")
    t = r["topology"]
    kind = "MONOREPO" if t["monorepo"] else "single project"
    L.append(f"Topology: {kind}" + (f" (markers: {', '.join(t['markers'])})" if t["markers"] else ""))
    if t["package_roots"]:
        shown = t["package_roots"][:25]
        more = f" (+{len(t['package_roots']) - 25} more)" if len(t["package_roots"]) > 25 else ""
        L.append(f"Package roots ({len(t['package_roots'])}): {', '.join(shown)}{more}")
    L.append(f"Manifests: {', '.join(r['manifests'][:15]) or 'none'}")
    for cat, tools in r["tooling"].items():
        L.append(f"Tooling[{cat}]: {', '.join(tools)}")
    L.append("Existing context files: " + (", ".join(r["existing_context"][:25]) or "none"))
    L.append("Top-level dirs (source files / LOC):")
    for d in r["top_level_dirs"][:20]:
        L.append(f"  {d['path']}/  {d['files']} / {d['loc']}")
    d = r["delegation"]
    if d["recommended"]:
        L.append(f"\nDELEGATION: REQUIRED -> {'; '.join(d['reasons'])}")
        L.append(f"Partitions (target ~{d['partition_target_loc']} LOC each), {len(r['partitions'])} total:")
        for p in r["partitions"]:
            flag = "  [OVERSIZE: split manually]" if p["oversize"] else ""
            L.append(f"  #{p['id']}: {', '.join(p['paths'])}  ({p['files']} files, {p['loc']} LOC){flag}")
    else:
        L.append("\nDELEGATION: not needed -> scan inline (repo is small enough for one context).")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--partition-loc", type=int, default=40_000,
                    help="target LOC per subagent partition (default 40000)")
    a = ap.parse_args()
    if not os.path.isdir(a.root):
        sys.exit(f"Not a directory: {a.root}")
    result = scan(a.root, a.partition_loc)
    print(json.dumps(result, indent=2) if a.json else render_text(result))


if __name__ == "__main__":
    main()
