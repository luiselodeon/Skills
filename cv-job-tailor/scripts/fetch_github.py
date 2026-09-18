#!/usr/bin/env python3
"""
fetch_github.py
Consulta los repositorios de un usuario en GitHub y filtra aquellos que 
hagan match con las tecnologías o requerimientos de una vacante.
"""

import sys
import json
import urllib.request

def get_repos(username):
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Gemini-Skill-CVTailor"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return data
    except Exception as e:
        print(f"Error fetching GitHub repos: {e}", file=sys.stderr)
        return []
    return []

def match_projects(repos, keywords):
    matched = []
    keywords_lower = [k.lower().strip() for k in keywords]
    for repo in repos:
        name = repo.get("name", "")
        desc = repo.get("description") or ""
        lang = repo.get("language") or ""
        topics = repo.get("topics", [])
        
        searchable_text = f"{name} {desc} {lang} {' '.join(topics)}".lower()
        score = sum(1 for kw in keywords_lower if kw in searchable_text)
        
        if score > 0:
            matched.append({
                "name": name,
                "description": desc,
                "language": lang,
                "url": repo.get("html_url"),
                "score": score
            })
            
    matched.sort(key=lambda x: x["score"], reverse=True)
    return matched

if __name__ == "__main__":
    user = "luiselodeon"
    kw = sys.argv[1:] if len(sys.argv) > 1 else ["python", "ai", "machine learning"]
    repos = get_repos(user)
    results = match_projects(repos, kw)
    print(json.dumps(results[:3], indent=2, ensure_ascii=False))