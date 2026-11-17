#!/usr/bin/env python3
"""Detect repo changes since the last context sync and validate context files.

Usage:
  python detect_drift.py [ROOT]            # human report
  python detect_drift.py [ROOT] --json     # machine-readable
  python detect_drift.py [ROOT] --quiet    # plain text, prints only if action is needed
  python detect_drift.py [ROOT] --hook     # Gemini CLI SessionStart hook: JSON only on stdout
  python detect_drift.py [ROOT] --stamp    # record HEAD + timestamp as the new baseline

Baseline lives in the first <!-- context-sync ... --> comment of scratchpad.md.
Never edits anything except the baseline comment when --stamp is used.
Always exits 0 so it is safe inside hooks.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (EXCLUDE_DIRS, FENCE_RE, MANIFESTS, SOURCE_EXT,  # noqa: E402
                     classify_tooling, git_head, glob_to_regex, list_files, strip_code)

META_RE = re.compile(r"<!--\s*context-sync\b(.*?)-->", re.S)
IMPORT_RE = re.compile(r"(?:^|\s)@(\.{0,2}/?[\w.\-]+(?:/[\w.\-]+)*\.[A-Za-z0-9]+)")
PATH_REF_RE = re.compile(r"`((?:\.{0,2}/)?[\w.\-]+(?:/[\w.\-]+)+/?)`")
MAX_GEMINI_MD_LINES = 200
MAX_IMPORT_DEPTH_HINT = 3  # Gemini CLI's import processor has a depth limit; stay shallow
NEW_AREA_MIN_FILES = 5

CATEGORY_TARGETS = {
    "manifest": "scratchpad.md (stack) + root GEMINI.md (commands/stack) + affected package GEMINI.md",
    "lint-format": "standards/code-style (+ lint rules)",
    "typecheck": "standards/code-style (type strictness)",
    "test": "standards/testing + testing rule",
    "build": "root GEMINI.md (build commands) + scratchpad.md",
    "hooks": "standards/git-and-workflow",
    "container": ".gemini/rules/infra or docker rule + scratchpad.md (deployment)",
    "ci": ".gemini/rules/ci-cd + root GEMINI.md (commands)",
    "infra": ".gemini/rules/infra (terraform/k8s) + scratchpad.md",
    "env": "config-and-env rule + root GEMINI.md (env vars)",
    "database": "standards/database + migrations rule + scratchpad.md (data model)",
    "api": "standards/api-design + api rule",
    "dir_added": "root GEMINI.md (directory map) + scratchpad.md (module map); consider scoped GEMINI.md",
    "dir_removed": "remove stale refs: GEMINI.md maps, rule globs, imports, scratchpad.md",
    "new_area": "create scoped GEMINI.md (+ rule if it has its own conventions)",
}


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def parse_meta(root):
    m = META_RE.search(read(os.path.join(root, "scratchpad.md")))
    if not m:
        return None
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def stamp(root):
    path = os.path.join(root, "scratchpad.md")
    if not os.path.isfile(path):
        sys.exit("scratchpad.md not found at repo root; create it before stamping.")
    head = git_head(root) or "none"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    block = (f"<!-- context-sync\nlast_synced_commit: {head}\nlast_synced_at: {now}\n"
             f"generated_by: context-architect-gemini\n-->\n")
    text = read(path)
    text = META_RE.sub("", text, count=1).lstrip("\n") if META_RE.search(text) else text
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(block + text)
    print(f"Stamped baseline: commit={head} at={now}")


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)


def collect_changes(root, meta, is_git):
    """Return (changes, note). changes: list of (status, path) with status in A/M/D/R."""
    changes, note = [], None
    base = (meta or {}).get("last_synced_commit", "none")
    if is_git and base not in ("none", ""):
        if git(root, "cat-file", "-e", f"{base}^{{commit}}").returncode != 0:
            return [], f"baseline commit {base[:10]} not found (rebase/force-push?). Run a full re-scan."
        diff = git(root, "diff", "--name-status", "-M", base, "HEAD").stdout
        for line in diff.splitlines():
            parts = line.split("\t")
            st = parts[0][0]
            if st == "R" and len(parts) >= 3:
                changes.append(("D", parts[1]))
                changes.append(("A", parts[2]))
            elif len(parts) >= 2:
                changes.append((st, parts[-1]))
        for line in git(root, "status", "--porcelain").stdout.splitlines():
            code, path = line[:2].strip(), line[3:].split(" -> ")[-1]
            st = "A" if code in ("??", "A") else "D" if code == "D" else "M"
            changes.append((st, path.strip('"')))
        return changes, note
    ts = (meta or {}).get("last_synced_at")
    if ts and ts != "none":
        try:
            since = datetime.fromisoformat(ts).timestamp()
        except ValueError:
            return [], "unparseable last_synced_at"
        files, _ = list_files(root)
        for f in files:
            try:
                if os.path.getmtime(os.path.join(root, f)) > since:
                    changes.append(("M", f))
            except OSError:
                pass
        return changes, "non-git mode: only modified files are detected (adds/deletes not distinguishable)"
    return [], "no baseline"


def analyze_changes(changes, context_dirs):
    sig = defaultdict(list)
    seen = set()
    added_by_area = defaultdict(list)
    for st, p in changes:
        if (st, p) in seen:
            continue
        seen.add((st, p))
        base = os.path.basename(p)
        parts = p.split("/")
        if set(parts[:-1]) & EXCLUDE_DIRS:
            continue
        if p == "scratchpad.md" or base == "GEMINI.md" or p.startswith((".gemini/", "standards/")):
            sig["context_edited"].append(f"{st} {p}")
            continue
        if base in MANIFESTS:
            sig["manifest"].append(f"{st} {p}")
        for tool, cat in classify_tooling(p):
            sig[cat].append(f"{st} {p} ({tool})")
        ext = os.path.splitext(base)[1].lower()
        if ext in SOURCE_EXT and st == "A":
            area = "/".join(parts[:2]) if len(parts) > 2 else (parts[0] if len(parts) > 1 else ".")
            added_by_area[area].append(p)
    new_areas = []
    for area, fl in added_by_area.items():
        covered = any(area == d or area.startswith(d + "/") for d in context_dirs if d != ".")
        if len(fl) >= NEW_AREA_MIN_FILES and not covered:
            new_areas.append(f"{area}/ (+{len(fl)} source files, no scoped GEMINI.md)")
    if new_areas:
        sig["new_area"] = new_areas
    return sig


def structure_diff(root, meta, files, is_git):
    """Compare directories (depth<=2) between baseline commit and now."""
    base = (meta or {}).get("last_synced_commit", "none")
    if not is_git or base in ("none", ""):
        return {}
    r = git(root, "ls-tree", "-r", "-d", "--name-only", base)
    if r.returncode != 0:
        return {}

    def shallow(paths):
        out = set()
        for p in paths:
            parts = p.split("/")
            if set(parts) & EXCLUDE_DIRS:
                continue
            for d in (1, 2):
                if len(parts) >= d:
                    out.add("/".join(parts[:d]))
        return out

    before = shallow(r.stdout.splitlines())
    now = shallow(os.path.dirname(f) for f in files if "/" in f)
    sig = {}
    if now - before:
        sig["dir_added"] = sorted(f"{d}/" for d in now - before)
    if before - now:
        sig["dir_removed"] = sorted(f"{d}/" for d in before - now)
    return sig


def health_checks(root, files):
    issues = []
    fileset = set(files)
    gemini_mds = [f for f in files if os.path.basename(f) == "GEMINI.md"]
    ctx_files = gemini_mds + [f for f in files if f.startswith((".gemini/", "standards/")) and f.endswith(".md")]
    if os.path.isfile(os.path.join(root, "scratchpad.md")):
        ctx_files.append("scratchpad.md")
    imported = set()

    for f in ctx_files:
        text = read(os.path.join(root, f))
        n_lines = text.count("\n") + 1
        if os.path.basename(f) == "GEMINI.md" and n_lines > MAX_GEMINI_MD_LINES:
            issues.append(f"[size] {f} has {n_lines} lines (> {MAX_GEMINI_MD_LINES}); move detail to standards/rules")
        body = strip_code(text)
        fdir = os.path.dirname(f)
        for m in IMPORT_RE.finditer(body):
            ref = m.group(1)
            target = os.path.normpath(os.path.join(fdir, ref)).replace(os.sep, "/")
            if os.path.isfile(os.path.join(root, target)):
                if not target.lower().endswith(".md"):
                    issues.append(f"[non-md-import] {f}: @{ref} is not a .md file (Gemini CLI imports only .md)")
                    continue
                imported.add(target)
                if not ref.startswith(("./", "../", "/")):
                    issues.append(f"[import-style] {f}: @{ref} should be written @./{ref} (explicit relative path)")
            elif not ref.startswith(("types/", "babel/")):
                issues.append(f"[broken-import] {f}: @{ref} -> {target} does not exist")
        if f.endswith("GEMINI.md") or f == "scratchpad.md":
            for m in PATH_REF_RE.finditer(FENCE_RE.sub("", text)):
                ref = m.group(1)
                if "*" in ref or ref.startswith(("http", "~", "@")):
                    continue
                cand = [os.path.normpath(os.path.join(fdir, ref)), os.path.normpath(ref)]
                if not any(os.path.exists(os.path.join(root, c)) for c in cand):
                    issues.append(f"[dangling-path] {f}: `{ref}` not found (renamed/removed?)")

    texts = {f: read(os.path.join(root, f)) for f in ctx_files}

    def referenced_elsewhere(f):
        """Imported by a context file, or mentioned by path/name in some OTHER context file."""
        if f in imported:
            return True
        name = os.path.basename(f)
        return any(name in t or f in t for g, t in texts.items() if g != f)

    # Gemini CLI has no glob-triggered rules: a rule only reaches the model if something loads it.
    # Its `paths:` frontmatter is metadata used to wire it (Rules index in root GEMINI.md, or an
    # @import from the scoped GEMINI.md of the folder it applies to) and to verify globs.
    for f in [x for x in files if x.startswith(".gemini/rules/") and x.endswith(".md")]:
        text = texts.get(f) or read(os.path.join(root, f))
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            issues.append(f"[rule-frontmatter] {f}: no YAML frontmatter (`paths:` globs are needed to wire and verify the rule)")
        else:
            globs = re.findall(r"^\s*-\s*[\"']?([^\"'\n]+?)[\"']?\s*$", m.group(1), re.M)
            if "paths" not in m.group(1) or not globs:
                issues.append(f"[rule-frontmatter] {f}: missing `paths:` list")
            else:
                for g in globs:
                    rx = glob_to_regex(g)
                    if not any(rx.match(x) for x in fileset):
                        issues.append(f"[stale-glob] {f}: `{g}` matches no files")
        if not referenced_elsewhere(f):
            issues.append(f"[unwired-rule] {f}: not in the root Rules index nor @imported by a scoped GEMINI.md, so Gemini CLI will never load it")

    for f in [x for x in files if x.startswith("standards/") and x.endswith(".md")]:
        if not referenced_elsewhere(f):
            issues.append(f"[orphan-standard] {f} is neither @imported nor mentioned anywhere")
    return issues


def build_report(root):
    meta = parse_meta(root)
    files, is_git = list_files(root)
    context_dirs = {os.path.dirname(f) or "." for f in files if os.path.basename(f) == "GEMINI.md"}
    changes, note = collect_changes(root, meta, is_git) if meta else ([], "no baseline (scratchpad.md missing or unstamped)")
    sig = analyze_changes(changes, context_dirs)
    sig.update(structure_diff(root, meta, files, is_git) if meta else {})
    actionable = {k: v for k, v in sig.items() if k != "context_edited"}
    return {
        "baseline": meta,
        "note": note,
        "changed_files": len({p for _, p in changes}),
        "signals": {k: sorted(set(v)) for k, v in actionable.items()},
        "context_files_edited_since_baseline": sorted(set(sig.get("context_edited", []))),
        "health_issues": health_checks(root, files),
        "suggested_targets": {k: CATEGORY_TARGETS[k] for k in actionable if k in CATEGORY_TARGETS},
    }


def render(r, quiet):
    has_drift = bool(r["signals"]) or bool(r["health_issues"]) or (r["note"] and "baseline" in r["note"])
    if quiet and not has_drift:
        return ""
    L = ["CONTEXT SYNC CHECK"]
    b = r["baseline"] or {}
    L.append(f"Baseline: commit={b.get('last_synced_commit', 'n/a')[:10]} at={b.get('last_synced_at', 'n/a')}")
    if r["note"]:
        L.append(f"Note: {r['note']}")
    L.append(f"Files changed since baseline: {r['changed_files']}")
    if r["signals"]:
        L.append("\nChange signals -> context to review:")
        for k, v in r["signals"].items():
            tgt = r["suggested_targets"].get(k)
            L.append(f"  * {k}: {len(v)} change(s)" + (f"  => {tgt}" if tgt else ""))
            for item in v[:6 if not quiet else 3]:
                L.append(f"      - {item}")
            if len(v) > (6 if not quiet else 3):
                L.append(f"      ... +{len(v) - (6 if not quiet else 3)} more")
    if r["health_issues"]:
        L.append("\nHealth issues in context files:")
        for i in r["health_issues"][:25 if not quiet else 8]:
            L.append(f"  - {i}")
    if not r["signals"] and not r["health_issues"]:
        L.append("\nNo drift detected; context files look current.")
    elif quiet:
        L.append("\nAction: run the context-architect-gemini skill in SYNC mode (or /sync-context) to update.")
    return "\n".join(L)


def render_hook(r):
    """Gemini CLI hook protocol: stdout must be ONE JSON object and nothing else."""
    text = render(r, quiet=True)
    if not text:
        return ""
    n = len(r["signals"]) + len(r["health_issues"])
    return json.dumps({
        "systemMessage": f"context-architect-gemini: {n} drift/health item(s) in GEMINI.md context",
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text},
    })


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="hook mode: silent when nothing to do")
    ap.add_argument("--hook", action="store_true", help="Gemini CLI SessionStart hook: JSON-only output")
    ap.add_argument("--stamp", action="store_true", help="write new baseline into scratchpad.md")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    if a.stamp:
        stamp(root)
        return
    report = build_report(root)
    if a.hook:
        out = render_hook(report)
    else:
        out = json.dumps(report, indent=2) if a.json else render(report, a.quiet)
    if out:
        print(out)


if __name__ == "__main__":
    main()
