#!/usr/bin/env python3
"""
fetch_github.py
Lista los repositorios públicos de un usuario y los ordena por coincidencia con las palabras clave de la vacante.
Uso:
  python fetch_github.py --user https://github.com/usuario python "machine learning" flask --top 5 --readme
Opcional: variable de entorno GITHUB_TOKEN para evitar el límite de 60 peticiones/hora.
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.request


def get(url):
    headers = {"User-Agent": "cv-job-tailor", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
        return json.loads(r.read().decode())


def readme_excerpt(full_name, chars=600):
    try:
        content = base64.b64decode(get(f"https://api.github.com/repos/{full_name}/readme")["content"]).decode("utf-8", "ignore")
    except Exception:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[#>*`!\[\]()|-]", " ", content)).strip()[:chars]


def score(text, keywords):
    # Coincidencia por palabra completa: evita que "ai" coincida con "maintain".
    return sum(1 for kw in keywords if re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", text))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user", required=True, help="Usuario o URL de GitHub")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--readme", action="store_true", help="Incluye extracto del README (y lo usa para puntuar)")
    p.add_argument("keywords", nargs="*", default=["python", "ai", "machine learning"])
    args = p.parse_args()
    user = args.user.rstrip("/").split("github.com/")[-1].split("/")[0]
    keywords = [k.lower().strip() for k in args.keywords if k.strip()]

    try:
        repos = get(f"https://api.github.com/users/{user}/repos?per_page=100&sort=updated")
    except Exception as e:
        sys.exit(f"Error consultando GitHub: {e}")

    results = []
    for repo in repos:
        if repo.get("fork"):
            continue
        text = " ".join([repo["name"].replace("-", " ").replace("_", " "), repo.get("description") or "",
                         repo.get("language") or "", " ".join(repo.get("topics", []))]).lower()
        results.append({"name": repo["name"], "description": repo.get("description") or "",
                        "language": repo.get("language") or "", "topics": repo.get("topics", []),
                        "url": repo["html_url"], "updated": repo.get("pushed_at", "")[:10],
                        "stars": repo.get("stargazers_count", 0), "score": score(text, keywords),
                        "_full": repo["full_name"], "_text": text})

    if args.readme:  # un README suele ser la única descripción real de un repo de estudiante
        # shortcut: solo los 30 repos más recientes para no agotar las 60 peticiones/h sin token; súbelo si usas GITHUB_TOKEN.
        for r in results[:30]:
            r["readme"] = readme_excerpt(r["_full"])
            r["score"] = score(r["_text"] + " " + r["readme"].lower(), keywords)

    results.sort(key=lambda r: (r["score"], r["updated"]), reverse=True)
    out = [{k: v for k, v in r.items() if not k.startswith("_")} for r in results[:args.top]]
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
