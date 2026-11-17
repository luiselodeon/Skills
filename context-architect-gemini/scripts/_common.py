"""Shared helpers for context-architect scripts (stdlib only)."""
import os
import re
import subprocess

EXCLUDE_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".nuxt", "target", "vendor",
    "__pycache__", ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".gradle", ".idea", ".vscode", "coverage", ".turbo", ".cache",
    "obj", "Pods", ".terraform", ".serverless", ".svelte-kit", ".parcel-cache",
}

SOURCE_EXT = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".swift": "Swift",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".c": "C", ".h": "C/C++",
    ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".scala": "Scala", ".ex": "Elixir",
    ".exs": "Elixir", ".dart": "Dart", ".vue": "Vue", ".svelte": "Svelte",
    ".sql": "SQL", ".tf": "Terraform", ".sh": "Shell", ".ps1": "PowerShell",
    ".lua": "Lua", ".r": "R", ".zig": "Zig",
}

MANIFESTS = {
    "package.json": "node", "pnpm-workspace.yaml": "node", "pyproject.toml": "python",
    "requirements.txt": "python", "setup.py": "python", "setup.cfg": "python",
    "Pipfile": "python", "go.mod": "go", "go.work": "go", "Cargo.toml": "rust",
    "pom.xml": "java", "build.gradle": "java", "build.gradle.kts": "java",
    "settings.gradle": "java", "Gemfile": "ruby", "composer.json": "php",
    "mix.exs": "elixir", "pubspec.yaml": "dart", "Package.swift": "swift",
    "deno.json": "deno",
}

# (regex on repo-relative path, tool label, category)
TOOLING = [
    (r"(^|/)\.?eslint(rc)?(\.[\w]+)?$|(^|/)eslint\.config\.\w+$", "ESLint", "lint-format"),
    (r"(^|/)\.prettierrc(\.\w+)?$|(^|/)prettier\.config\.\w+$", "Prettier", "lint-format"),
    (r"(^|/)biome\.jsonc?$", "Biome", "lint-format"),
    (r"(^|/)\.?ruff\.toml$", "Ruff", "lint-format"),
    (r"(^|/)\.flake8$|(^|/)\.pylintrc$", "flake8/pylint", "lint-format"),
    (r"(^|/)\.golangci\.ya?ml$", "golangci-lint", "lint-format"),
    (r"(^|/)rustfmt\.toml$|(^|/)clippy\.toml$", "rustfmt/clippy", "lint-format"),
    (r"(^|/)\.rubocop\.yml$", "RuboCop", "lint-format"),
    (r"(^|/)\.editorconfig$", "EditorConfig", "lint-format"),
    (r"(^|/)tsconfig(\.[\w-]+)?\.json$", "TypeScript", "typecheck"),
    (r"(^|/)mypy\.ini$|(^|/)pyrightconfig\.json$", "mypy/pyright", "typecheck"),
    (r"(^|/)jest\.config\.\w+$", "Jest", "test"),
    (r"(^|/)vitest\.config\.\w+$|(^|/)vitest\.workspace\.\w+$", "Vitest", "test"),
    (r"(^|/)playwright\.config\.\w+$", "Playwright", "test"),
    (r"(^|/)cypress\.config\.\w+$", "Cypress", "test"),
    (r"(^|/)pytest\.ini$|(^|/)conftest\.py$|(^|/)tox\.ini$", "pytest", "test"),
    (r"(^|/)phpunit\.xml(\.dist)?$", "PHPUnit", "test"),
    (r"(^|/)\.pre-commit-config\.ya?ml$", "pre-commit", "hooks"),
    (r"(^|/)\.husky/", "Husky", "hooks"),
    (r"(^|/)commitlint\.config\.\w+$|(^|/)\.commitlintrc", "commitlint", "hooks"),
    (r"(^|/)(vite|webpack|rollup|next|nuxt|astro|svelte)\.config\.\w+$", "bundler/framework config", "build"),
    (r"(^|/)tailwind\.config\.\w+$", "Tailwind", "build"),
    (r"(^|/)(Makefile|justfile|Taskfile\.ya?ml)$", "task runner", "build"),
    (r"(^|/)turbo\.json$|(^|/)nx\.json$|(^|/)lerna\.json$", "monorepo tool", "build"),
    (r"(^|/)Dockerfile(\.[\w-]+)?$|(^|/)docker-compose(\.[\w-]+)?\.ya?ml$|(^|/)compose\.ya?ml$", "Docker", "container"),
    (r"(^|/)\.github/workflows/[^/]+\.ya?ml$", "GitHub Actions", "ci"),
    (r"(^|/)\.gitlab-ci\.ya?ml$|(^|/)Jenkinsfile$|(^|/)azure-pipelines\.ya?ml$|(^|/)\.circleci/", "CI", "ci"),
    (r"(^|/)[^/]+\.tf$", "Terraform", "infra"),
    (r"(^|/)(k8s|kubernetes|helm|charts)/", "Kubernetes/Helm", "infra"),
    (r"(^|/)serverless\.ya?ml$|(^|/)cdk\.json$|(^|/)Pulumi\.ya?ml$", "IaC", "infra"),
    (r"(^|/)\.env(\.[\w-]+)?\.(example|sample|template)$|(^|/)\.env\.example$", ".env example", "env"),
    (r"(^|/)(prisma/schema\.prisma|alembic\.ini|drizzle\.config\.\w+|knexfile\.\w+)$", "DB/ORM", "database"),
    (r"(^|/)(migrations?|alembic/versions)/", "DB migrations", "database"),
    (r"(^|/)(openapi|swagger)[\w.-]*\.(ya?ml|json)$", "OpenAPI", "api"),
]
_TOOLING_RE = [(re.compile(p), t, c) for p, t, c in TOOLING]


def classify_tooling(path):
    """Return [(tool, category)] matched by a repo-relative path."""
    return [(t, c) for rx, t, c in _TOOLING_RE if rx.search(path)]


def git_head(root):
    try:
        out = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return None


def list_files(root):
    """Repo-relative file list honoring .gitignore when git is available."""
    files, is_git = [], False
    try:
        out = subprocess.run(
            ["git", "-C", root, "ls-files", "-co", "--exclude-standard", "-z"],
            capture_output=True, check=True).stdout
        files = [f for f in out.decode("utf-8", "replace").split("\0") if f]
        files = [f for f in files if os.path.isfile(os.path.join(root, f))]
        is_git = True
    except Exception:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
            for fn in fns:
                files.append(os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/"))
    files = [f for f in files if not (set(f.split("/")[:-1]) & EXCLUDE_DIRS)]
    return files, is_git


def count_lines(path, cap=2_000_000):
    try:
        if os.path.getsize(path) > cap:
            return 0
        with open(path, "rb") as fh:
            return fh.read().count(b"\n")
    except OSError:
        return 0


def _expand_braces(s):
    m = re.search(r"\{([^{}]*)\}", s)
    if not m:
        return [s]
    out = []
    for opt in m.group(1).split(","):
        out += _expand_braces(s[:m.start()] + opt + s[m.end():])
    return out


def glob_to_regex(glob):
    """Gitignore-style glob -> compiled regex on repo-relative posix paths."""
    if "/" not in glob:
        glob = "**/" + glob
    parts = []
    for pat in _expand_braces(glob):
        i, r = 0, ""
        while i < len(pat):
            c = pat[i]
            if pat.startswith("**/", i):
                r += "(?:.*/)?"
                i += 3
                continue
            if pat.startswith("**", i):
                r += ".*"
                i += 2
                continue
            if c == "*":
                r += "[^/]*"
            elif c == "?":
                r += "[^/]"
            elif c in ".+()|^$\\[]{}":
                r += "\\" + c
            else:
                r += c
            i += 1
        parts.append(r)
    return re.compile("^(?:" + "|".join(parts) + ")$")


FENCE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def strip_code(text):
    """Remove fenced and inline code so @imports inside them are ignored (as Gemini CLI does)."""
    return INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))
