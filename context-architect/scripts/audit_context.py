#!/usr/bin/env python3
"""Audit an EXISTING Claude context setup against best practices.

Usage:
  python audit_context.py [ROOT]          # human report
  python audit_context.py [ROOT] --json   # machine-readable

Checks CLAUDE.md files, .claude/rules, .claude/standards, scratchpad.md and legacy
agent files (GEMINI.md, AGENTS.md, .cursorrules...). Read-only; always exits 0.
Secret-looking values are never printed, only file:line.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import MANIFESTS, SOURCE_EXT, list_files, strip_code  # noqa: E402
from detect_drift import IMPORT_RE, health_checks, read  # noqa: E402

LEGACY_FILES = ("GEMINI.md", "AGENTS.md", ".cursorrules", "copilot-instructions.md")
DOC_FILES = ("CONTRIBUTING.md", "ARCHITECTURE.md", "DEVELOPMENT.md")
SEVERITY_COST = {"high": 10, "medium": 4, "low": 2}

TOPICS = [  # (regex on heading, suggested standard file)
    (r"test|coverage|qa\b", "testing.md"),
    (r"secur|secret|auth|privacy|pii", "security.md"),
    (r"\bapi\b|endpoint|rest\b|graphql|rpc", "api-design.md"),
    (r"style|convention|naming|format|lint|typing", "code-style.md"),
    (r"git|commit|branch|pull request|\bpr\b|workflow", "git-and-workflow.md"),
    (r"database|migration|orm|sql|schema", "database-and-orm.md"),
    (r"error|logging|observab|monitor", "error-handling-and-observability.md"),
    (r"react|component|css|styling|state manage|frontend|ui\b", "frontend.md"),
    (r"infra|terraform|docker|deploy|ci/cd|kubernetes", "infra.md"),
]
FILETYPE_HINT = re.compile(
    r"(\*\.\w+|\*\*/|\bcomponents?\b|\broutes?\b|\bcontrollers?\b|\bmigrations?\b|"
    r"\bterraform\b|\bworkflows?\b|\.test\.|\.spec\.|\bmodels?\b)", re.I)
VAGUE = re.compile(
    r"(write clean code|follow best practices|be careful|high[- ]quality code|"
    r"write good code|use common sense|keep code clean|code should be readable)", re.I)
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{30,}"),
    re.compile(r"\bxox[abp]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*['\"]?[A-Za-z0-9/+_\-]{12,}"),
]
CMD_HINT = re.compile(r"\b(npm|pnpm|yarn|bun|pytest|pip|poetry|uv|go (test|build|run)|cargo|make|mvn|gradle|dotnet|rake|bundle|composer|just)\b")


class Findings:
    def __init__(self):
        self.items = []

    def add(self, fid, sev, where, msg, fix):
        self.items.append({"id": fid, "severity": sev, "where": where, "message": msg, "fix": fix})


def sections(text):
    """Yield (level, heading, body_nonblank_lines) for markdown sections (fences respected)."""
    lines, out, cur, in_fence = text.splitlines(), [], None, False
    for ln in lines:
        if ln.strip().startswith("```"):
            in_fence = not in_fence
        m = re.match(r"^(#{1,6})\s+(.*)$", ln) if not in_fence else None
        if m:
            if cur:
                out.append(cur)
            cur = [len(m.group(1)), m.group(2).strip(), 0]
        elif cur and ln.strip():
            cur[2] += 1
    if cur:
        out.append(cur)
    return out


def import_graph(root, start, files_set):
    """Return (set_of_reached_files, max_depth) following @imports from `start`."""
    reached, max_depth = set(), 0
    stack = [(start, 1)]
    while stack:
        f, d = stack.pop()
        if f in reached:
            continue
        reached.add(f)
        max_depth = max(max_depth, d)
        fdir = os.path.dirname(f)
        for m in IMPORT_RE.finditer(strip_code(read(os.path.join(root, f)))):
            t = os.path.normpath(os.path.join(fdir, m.group(1))).replace(os.sep, "/")
            if t in files_set or os.path.isfile(os.path.join(root, t)):
                stack.append((t, d + 1))
    return reached, max_depth


def audit(root):
    F = Findings()
    files, _ = list_files(root)
    fset = set(files)
    base = os.path.basename

    claude_mds = sorted(f for f in files if base(f) == "CLAUDE.md")
    root_md = "CLAUDE.md" if "CLAUDE.md" in fset else (".claude/CLAUDE.md" if ".claude/CLAUDE.md" in fset else None)
    rules = sorted(f for f in files if f.startswith(".claude/rules/") and f.endswith(".md"))
    standards = sorted(f for f in files if f.startswith(".claude/standards/") and f.endswith(".md"))
    legacy = sorted(f for f in files if base(f) in LEGACY_FILES or f.startswith(".cursor/rules/"))
    ctx = claude_mds + rules + standards + (["scratchpad.md"] if "scratchpad.md" in fset else [])
    texts = {f: read(os.path.join(root, f)) for f in ctx}

    inventory = {"claude_md": len(claude_mds), "rules": len(rules), "standards": len(standards),
                 "scratchpad": "scratchpad.md" in fset, "legacy_files": legacy}

    # ---- structure ----
    if not root_md:
        F.add("NO_ROOT_CLAUDE", "high", "(root)", "No root CLAUDE.md.", "Create it (INIT templates) from the scan.")
    root_text = texts.get(root_md, "") if root_md else ""
    root_lines = root_text.count("\n") + 1 if root_text else 0
    if root_lines > 200:
        F.add("ROOT_TOO_LONG", "high", root_md, f"Root CLAUDE.md has {root_lines} lines (budget ~120, ceiling 200).",
              "Extract topic sections to standards, file-type sections to rules, folder sections to scoped CLAUDE.md.")
    elif root_lines > 120:
        F.add("ROOT_TOO_LONG", "medium", root_md, f"Root CLAUDE.md has {root_lines} lines (budget ~120).",
              "Move detail out to standards/rules/scoped CLAUDE.md.")

    # ---- imports ----
    legacy_import = [(f, i + 1) for f, t in texts.items() for i, ln in enumerate(t.splitlines())
                     if re.match(r"^\s*@import\s+\S+", ln)]
    for f, ln in legacy_import:
        F.add("LEGACY_IMPORT_SYNTAX", "high", f"{f}:{ln}", "Uses `@import path` (Gemini-style); Claude Code expects `@path/to/file.md`.",
              "Rewrite as `@relative/path.md` on its own line.")
    valid_imports = {f: [m.group(1) for m in IMPORT_RE.finditer(strip_code(t))] for f, t in texts.items()}
    total_imports = sum(len(v) for v in valid_imports.values())
    if total_imports == 0 and (root_lines > 60 or standards or len(claude_mds) > 1):
        F.add("NO_IMPORTS", "medium", "(all CLAUDE.md)", "No @imports anywhere, so shared knowledge is duplicated or inlined.",
              "Move shared content into .claude/standards/ and import it from the CLAUDE.md files that need it.")
    if root_md:
        reached, depth = import_graph(root, root_md, fset)
        heavy = sum(read(os.path.join(root, f)).count("\n") + 1 for f in reached)
        if heavy > 300:
            F.add("ROOT_LOADS_TOO_MUCH", "medium", root_md,
                  f"Root plus its transitive imports load ~{heavy} lines every session.",
                  "Import only short global standards at root; move area-specific ones into scoped CLAUDE.md files.")
        if depth > 5:
            F.add("IMPORT_TOO_DEEP", "low", root_md, f"Import chain is {depth} hops deep (Claude Code follows up to 5).",
                  "Flatten the import chain.")

    # ---- missing building blocks ----
    if not rules:
        F.add("NO_RULES_DIR", "medium", ".claude/rules/", "No path-scoped rules.",
              "Create rules (with `paths:` frontmatter) for file types/areas that have their own conventions.")
    if not standards:
        F.add("NO_STANDARDS_DIR", "medium", ".claude/standards/", "No shared standards library.",
              "Extract topic sections (testing, security, API, style, workflow) into standards; run the standards interview for gaps.")
    pkg_roots = sorted({os.path.dirname(f) for f in files if base(f) in MANIFESTS and "/" in f and base(f) != "requirements.txt"})
    uncovered = [p for p in pkg_roots if f"{p}/CLAUDE.md" not in fset]
    if uncovered:
        F.add("NO_SCOPED_CLAUDE", "medium", ", ".join(uncovered[:8]) + (" ..." if len(uncovered) > 8 else ""),
              f"{len(uncovered)} package folder(s) have no scoped CLAUDE.md.",
              "Add a scoped CLAUDE.md per package importing only the standards it needs.")
    src_by_dir = defaultdict(int)
    for f in files:
        if os.path.splitext(f)[1].lower() in SOURCE_EXT and "/" in f:
            parts = f.split("/")
            for d in (1, 2):
                if len(parts) > d:
                    src_by_dir["/".join(parts[:d])] += 1
    big_uncovered = [d for d, n in src_by_dir.items() if n >= 60 and f"{d}/CLAUDE.md" not in fset
                     and d not in pkg_roots and not any(c.startswith(d + "/") for c in claude_mds)]
    if big_uncovered:
        F.add("LARGE_DIR_NO_CLAUDE", "low", ", ".join(sorted(big_uncovered)[:6]),
              "Large source directories without any scoped CLAUDE.md.", "Consider a scoped CLAUDE.md if they have their own conventions.")
    if "scratchpad.md" not in fset:
        F.add("NO_SCRATCHPAD", "medium", "scratchpad.md", "No architecture scratchpad.", "Create it from assets/scratchpad-template.md.")
    elif "context-sync" not in texts.get("scratchpad.md", ""):
        F.add("NO_SYNC_BASELINE", "low", "scratchpad.md", "No sync baseline comment.", "Run detect_drift.py --stamp after the upgrade.")
    if root_text and not re.search(r"(?im)^#+\s*context maintenance", root_text):
        F.add("NO_MAINTENANCE_BLOCK", "low", root_md, "Root CLAUDE.md lacks the Context maintenance block.",
              "Add the block from references/sync-mode.md section 8.")
    if root_text and not (re.search(r"(?im)^#+\s*(commands|scripts|development|build|getting started)", root_text) or CMD_HINT.search(root_text)):
        F.add("NO_COMMANDS", "medium", root_md, "Root CLAUDE.md lists no build/test/lint commands.",
              "Add verified commands from manifests/scripts.")

    # ---- content quality ----
    for f in claude_mds:
        for lvl, head, n in sections(texts[f]):
            if n < 10:
                continue
            if FILETYPE_HINT.search(head):
                F.add("INLINE_RULE_CANDIDATE", "medium", f"{f} > {head}", f"{n}-line section is file-type/area specific.",
                      "Move to a path-scoped rule (derive globs from real files, verify they match) or to a scoped CLAUDE.md.")
                continue
            for rx, target in TOPICS:
                if re.search(rx, head, re.I):
                    F.add("INLINE_STANDARD", "medium", f"{f} > {head}", f"{n}-line section looks like a standard.",
                          f"Extract to .claude/standards/{target} (provenance: decision, migrated) and @import it.")
                    break
    for f in standards:
        if not re.search(r"^>\s*Source:", texts[f], re.M):
            F.add("STANDARD_NO_PROVENANCE", "low", f, "Standard lacks a `> Source:` provenance header.",
                  "Add `> Source: decision (migrated YYYY-MM-DD)` or `observed (scan)` so SYNC can treat it correctly.")
    vague = sum(len(VAGUE.findall(t)) for t in texts.values())
    if vague:
        F.add("VAGUE_INSTRUCTIONS", "low", "(context files)", f"{vague} generic instruction(s) that add tokens but no guidance.",
              "Replace with concrete, checkable rules or delete (list deletions for approval).")
    abs_hits = [f for f, t in texts.items() if re.search(r"(/Users/|/home/\w+|[A-Z]:\\\\)", t)]
    if abs_hits:
        F.add("ABSOLUTE_PATHS", "low", ", ".join(abs_hits[:5]), "Machine-specific absolute paths.", "Use repo-relative paths.")

    # duplication
    seen = defaultdict(set)
    for f, t in texts.items():
        for ln in strip_code(t).splitlines():
            n = re.sub(r"\s+", " ", ln.strip().lstrip("-*0123456789. ").lower())
            if len(n) > 45 and not n.startswith(("@", "#", ">")):
                seen[n].add(f)
    dups = [(n, fs) for n, fs in seen.items() if len(fs) > 1]
    if dups:
        fs = sorted({x for _, s in dups for x in s})
        F.add("DUPLICATED_CONTENT", "medium", ", ".join(fs[:5]), f"{len(dups)} line(s) repeated across context files.",
              "Keep each statement in one place (standard/rule) and import or rely on glob matching.")

    # secrets
    for f, t in texts.items():
        for i, ln in enumerate(t.splitlines(), 1):
            if any(p.search(ln) for p in SECRET_PATTERNS):
                F.add("SECRET_IN_CONTEXT", "high", f"{f}:{i}", "Secret-looking value in a context file (value not shown).",
                      "Remove it, reference the variable name only, and advise rotating the credential.")

    # legacy / docs / local
    mentioned = "\n".join(texts.values())
    for lf in legacy:
        if base(lf) not in mentioned and lf not in mentioned:
            F.add("LEGACY_NOT_INTEGRATED", "medium", lf, "Other-tool agent file not integrated into the Claude setup.",
                  "Migrate its still-valid rules (keep nothing silently dropped) or `@import` it if it is shared with other tools (e.g. @AGENTS.md).")
    for d in DOC_FILES:
        if d in fset and d not in mentioned:
            F.add("DOC_NOT_REFERENCED", "low", d, "Existing project doc not referenced from context files.",
                  "Reference it from root CLAUDE.md (@import if short, plain pointer if long) instead of duplicating its content.")
    if "CLAUDE.local.md" in fset:
        F.add("LOCAL_FILE_NOT_IGNORED", "medium", "CLAUDE.local.md", "CLAUDE.local.md is visible to git (not ignored).",
              "Ask the user, then add it to .gitignore.")

    # reuse drift health checks (skip size: covered above)
    sev = {"broken-import": "high", "rule-frontmatter": "medium", "stale-glob": "medium",
           "dangling-path": "medium", "orphan-standard": "low"}
    for issue in health_checks(root, files):
        m = re.match(r"\[([\w-]+)\]\s+(\S+?):?\s+(.*)", issue)
        if not m or m.group(1) == "size":
            continue
        kind, where, msg = m.groups()
        F.add(kind.upper().replace("-", "_"), sev.get(kind, "low"), where, msg,
              "See references/sync-mode.md section 4 (health issue fixes).")

    return F.items, inventory


def score(items):
    """First occurrence of each finding id costs full; repeats cost 1/3 (max 3 repeats)."""
    cost, counts = 0.0, defaultdict(int)
    for i in items:
        counts[i["id"]] += 1
        c = counts[i["id"]]
        if c == 1:
            cost += SEVERITY_COST[i["severity"]]
        elif c <= 4:
            cost += SEVERITY_COST[i["severity"]] / 3
    s = max(0, round(100 - cost))
    label = ("Excellent" if s >= 90 else "Good" if s >= 75 else "Needs work" if s >= 50 else "Poor")
    return s, label


def render(items, inventory):
    s, label = score(items)
    L = ["CONTEXT AUDIT",
         f"Inventory: {inventory['claude_md']} CLAUDE.md, {inventory['rules']} rules, {inventory['standards']} standards, "
         f"scratchpad: {'yes' if inventory['scratchpad'] else 'no'}, legacy: {', '.join(inventory['legacy_files']) or 'none'}",
         f"Score: {s}/100 ({label}) | high: {sum(i['severity']=='high' for i in items)}, "
         f"medium: {sum(i['severity']=='medium' for i in items)}, low: {sum(i['severity']=='low' for i in items)}"]
    for sev in ("high", "medium", "low"):
        group = [i for i in items if i["severity"] == sev]
        if not group:
            continue
        L.append(f"\n[{sev.upper()}]")
        for i in group:
            L.append(f"  - {i['id']} @ {i['where']}: {i['message']}\n      fix: {i['fix']}")
    if not items:
        L.append("\nNo findings. Setup follows the checked best practices.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    items, inv = audit(root)
    if a.json:
        s, label = score(items)
        print(json.dumps({"score": s, "label": label, "inventory": inv, "findings": items}, indent=2))
    else:
        print(render(items, inv))


if __name__ == "__main__":
    main()
