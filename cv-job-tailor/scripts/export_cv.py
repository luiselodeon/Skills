#!/usr/bin/env python3
"""
export_cv.py
Genera un CV .docx (y opcionalmente .pdf) a partir de un JSON con el esquema de references/cv_template.json.
Uso:
  python export_cv.py --data cv.json --format docx --output Luis_Arias_CV.docx
  python export_cv.py --data cv.json --format pdf  --output Luis_Arias_CV.pdf
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

LABELS = {
    "en": {"summary": "Professional Summary", "education": "Education", "experience": "Professional Experience",
           "projects": "Relevant Projects", "skills": "Skills", "certifications": "Certifications",
           "technical": "Technical", "languages": "Languages", "interests": "Interests"},
    "es": {"summary": "Perfil Profesional", "education": "Educación", "experience": "Experiencia Profesional",
           "projects": "Proyectos Relevantes", "skills": "Habilidades", "certifications": "Certificaciones",
           "technical": "Técnicas", "languages": "Idiomas", "interests": "Intereses"},
}
ACCENT = (31, 78, 121)


def create_docx(data, output_path):
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    L = LABELS.get(data.get("lang", "en"), LABELS["en"])
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(0)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Inches(0.5)
        s.left_margin = s.right_margin = Inches(0.6)
    text_width = doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin

    def para(align=None, before=0, after=0):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        if align:
            p.alignment = align
        return p

    def left_right(left, right, bold=False, italic=False):
        # Texto a la izquierda y fecha alineada a la derecha con tabulador (ATS lo lee como una sola línea).
        p = para()
        p.paragraph_format.tab_stops.add_tab_stop(text_width, alignment=2)  # 2 = RIGHT
        r = p.add_run(left)
        r.bold, r.italic = bold, italic
        if right:
            p.add_run("\t" + right).italic = italic
        return p

    def bullet(text):
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(1)
        p.add_run(text)

    def header(text):
        p = para(before=8, after=3)
        r = p.add_run(text.upper())
        r.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(*ACCENT)
        border = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        for k, v in {"w:val": "single", "w:sz": "6", "w:space": "1", "w:color": "1F4E79"}.items():
            bottom.set(qn(k), v)
        border.append(bottom)
        p._p.get_or_add_pPr().append(border)

    # Encabezado
    name = para(WD_ALIGN_PARAGRAPH.CENTER).add_run(data.get("name", ""))
    name.bold = True
    name.font.size = Pt(16)
    if data.get("headline"):
        para(WD_ALIGN_PARAGRAPH.CENTER).add_run(data["headline"]).font.size = Pt(11)
    for line in ([data.get(k) for k in ("location", "phone", "email")], [data.get(k) for k in ("linkedin", "github")]):
        parts = [x for x in line if x]
        if parts:
            para(WD_ALIGN_PARAGRAPH.CENTER).add_run(" • ".join(parts)).font.size = Pt(9.5)

    if data.get("summary"):
        header(L["summary"])
        para(after=2).add_run(data["summary"])

    def experience():
        if not data.get("experience"):
            return
        header(L["experience"])
        for exp in data["experience"]:
            left_right(f"{exp.get('role', '')} | {exp.get('company', '')}", exp.get("period", ""), bold=True)
            if exp.get("location"):
                left_right(exp["location"], "", italic=True)
            for b in exp.get("bullets", []):
                bullet(b)

    def education():
        if not data.get("education"):
            return
        header(L["education"])
        for edu in data["education"]:
            left_right(edu.get("institution", ""), edu.get("period", ""), bold=True)
            degree = edu.get("degree", "")
            if edu.get("gpa"):
                degree += f" — GPA: {edu['gpa']}"
            left_right(degree, edu.get("location", ""), italic=True)
            for d in edu.get("details", []):
                bullet(d)

    def projects():
        if not data.get("projects"):
            return
        header(L["projects"])
        for proj in data["projects"]:
            left_right(proj.get("name", ""), proj.get("tech", ""), bold=True)
            if proj.get("description"):
                bullet(proj["description"])
            for b in proj.get("bullets", []):
                bullet(b)
            if proj.get("url"):
                para().add_run(proj["url"]).font.size = Pt(9)

    def certifications():
        if not data.get("certifications"):
            return
        header(L["certifications"])
        for c in data["certifications"]:
            bullet(" — ".join(x for x in (c.get("title"), c.get("issuer"), c.get("date")) if x))

    def skills():
        sk = data.get("skills") or {}
        if not sk:
            return
        header(L["skills"])
        for key, value in sk.items():
            if not value:
                continue
            p = para(after=1)
            p.add_run(f"{L.get(key, key.capitalize())}: ").bold = True
            p.add_run(value)

    sections = {"experience": experience, "education": education, "projects": projects,
                "certifications": certifications, "skills": skills}
    order = data.get("section_order") or ["experience", "projects", "education", "certifications", "skills"]
    for key in order:
        sections[key]()

    doc.save(output_path)
    print(f"DOCX guardado: {output_path}")


def to_pdf(docx_path, pdf_path):
    """Convierte con Word (docx2pdf) o LibreOffice; falla en voz alta si ninguno está disponible."""
    try:
        from docx2pdf import convert
        convert(docx_path, pdf_path)
    except ImportError:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            sys.exit("No hay conversor PDF: instala `pip install docx2pdf` (requiere Word) o LibreOffice. "
                     f"El DOCX quedó en {docx_path}.")
        outdir = os.path.dirname(os.path.abspath(pdf_path))
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path], check=True)
        produced = os.path.join(outdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
        if os.path.abspath(produced) != os.path.abspath(pdf_path):
            os.replace(produced, pdf_path)
    if not os.path.exists(pdf_path):
        sys.exit(f"La conversión a PDF no generó {pdf_path}")
    print(f"PDF guardado: {pdf_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="JSON con el contenido del CV")
    parser.add_argument("--format", choices=["docx", "pdf"], default="docx")
    parser.add_argument("--output", required=True, help="Ruta del archivo de salida")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.format == "docx":
        create_docx(data, args.output)
    else:
        docx_path = os.path.splitext(args.output)[0] + ".docx"
        create_docx(data, docx_path)
        to_pdf(docx_path, args.output)


if __name__ == "__main__":
    main()
