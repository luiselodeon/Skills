#!/usr/bin/env python3
"""
fetch_linkedin.py
Script auxiliar para consultar información complementaria de LinkedIn
(certificaciones, voluntariado, reconocimientos y experiencia extendida)
para robustecer el CV según los requerimientos específicos de la vacante.
"""

import sys
import json
import os
import argparse

DEFAULT_LINKEDIN_URL = "https://www.linkedin.com/in/luis-alberto-arias-llaguno/"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "references", "linkedin_profile.json")

def load_local_profile():
    """Carga información de respaldo estructurada si existe localmente."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def search_additional_info(profile_data, keywords):
    """Busca dentro de certificaciones, honores y experiencia complementaria."""
    matches = {
        "certifications": [],
        "extra_experience": [],
        "volunteering": []
    }
    kw_lower = [k.lower().strip() for k in keywords]

    # Certificaciones y Cursos
    for cert in profile_data.get("certifications", []):
        text = f"{cert.get('title', '')} {cert.get('issuer', '')}".lower()
        if any(k in text for k in kw_lower):
            matches["certifications"].append(cert)

    # Experiencia adicional / Proyectos extracurriculares
    for exp in profile_data.get("additional_experience", []):
        text = f"{exp.get('title', '')} {exp.get('description', '')}".lower()
        if any(k in text for k in kw_lower):
            matches["extra_experience"].append(exp)

    return matches

def main():
    parser = argparse.ArgumentParser(description="Consulta datos adicionales del perfil de LinkedIn.")
    parser.add_argument("--url", default=DEFAULT_LINKEDIN_URL, help="URL del perfil de LinkedIn")
    parser.add_argument("--keywords", nargs="*", default=[], help="Palabras clave requeridas por la vacante")
    args = parser.parse_args()

    profile_data = load_local_profile()
    
    if not profile_data:
        print(json.dumps({
            "status": "online_reference_only",
            "url": args.url,
            "message": "Consultar URL directamente en navegación para detalles adicionales."
        }, indent=2, ensure_ascii=False))
        return

    if args.keywords:
        results = search_additional_info(profile_data, args.keywords)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(profile_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()