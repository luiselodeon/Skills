#!/usr/bin/env python3
"""
export_cv.py
Genera un documento .docx o .pdf a partir de un archivo JSON estructurado de CV.
Uso:
  python export_cv.py --data cv_data.json --format docx --output Luis_Arias_CV.docx
  python export_cv.py --data cv_data.json --format pdf --output Luis_Arias_CV.pdf
"""

import argparse
import json
import os

def create_docx(data, output_path):
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    
    # Márgenes estándar de 0.5 pulgadas
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.6)
        section.right_margin = Inches(0.6)

    # Encabezado / Datos de contacto
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_name = title.add_run(data.get("name", ""))
    run_name.font.size = Pt(16)
    run_name.font.bold = True
    run_name.font.name = "Calibri"

    contact = doc.add_paragraph()
    contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_text = f"{data.get('location', '')} • {data.get('phone', '')} • {data.get('email', '')}"
    run_contact = contact.add_run(contact_text)
    run_contact.font.size = Pt(9.5)
    run_contact.font.name = "Calibri"

    links = doc.add_paragraph()
    links.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_links = links.add_run(f"LinkedIn: {data.get('linkedin', '')} | GitHub: {data.get('github', '')}")
    run_links.font.size = Pt(9.5)
    run_links.font.name = "Calibri"

    def add_section_header(title_text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(title_text)
        run.bold = True
        run.font.size = Pt(11)
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(31, 78, 121)

    # Resumen
    if data.get("summary"):
        p_sum = doc.add_paragraph()
        p_sum.paragraph_format.space_after = Pt(4)
        run_sum = p_sum.add_run(data["summary"])
        run_sum.font.size = Pt(10)
        run_sum.font.name = "Calibri"

    # Educación
    add_section_header("Education" if data.get("lang") == "en" else "Educación")
    for edu in data.get("education", []):
        p_edu = doc.add_paragraph()
        p_edu.paragraph_format.space_after = Pt(2)
        r_inst = p_edu.add_run(f"{edu.get('institution')} | {edu.get('location')}\n")
        r_inst.bold = True
        r_deg = p_edu.add_run(f"{edu.get('degree')} - GPA: {edu.get('gpa')}\n")
        r_deg.italic = True
        for detail in edu.get("details", []):
            p_det = doc.add_paragraph(style='List Bullet')
            p_det.paragraph_format.space_after = Pt(1)
            p_det.add_run(detail).font.size = Pt(9.5)

    # Experiencia
    add_section_header("Professional Experience" if data.get("lang") == "en" else "Experiencia Profesional")
    for exp in data.get("experience", []):
        p_exp = doc.add_paragraph()
        p_exp.paragraph_format.space_after = Pt(2)
        r_comp = p_exp.add_run(f"{exp.get('company')} | {exp.get('location')} — {exp.get('period')}\n")
        r_comp.bold = True
        r_role = p_exp.add_run(f"{exp.get('role')}\n")
        r_role.italic = True
        for point in exp.get("bullets", []):
            p_pt = doc.add_paragraph(style='List Bullet')
            p_pt.paragraph_format.space_after = Pt(1)
            p_pt.add_run(point).font.size = Pt(9.5)

    # Proyectos
    if data.get("projects"):
        add_section_header("Relevant Projects (GitHub)" if data.get("lang") == "en" else "Proyectos Relevantes (GitHub)")
        for proj in data.get("projects", []):
            p_proj = doc.add_paragraph(style='List Bullet')
            p_proj.paragraph_format.space_after = Pt(1)
            r_pname = p_proj.add_run(f"{proj.get('name')}: ")
            r_pname.bold = True
            p_proj.add_run(f"{proj.get('description')} ({proj.get('url')})").font.size = Pt(9.5)

    # Habilidades e intereses
    add_section_header("Abilities and Interests" if data.get("lang") == "en" else "Habilidades e Intereses")
    p_skills = doc.add_paragraph()
    skills = data.get("skills", {})
    p_skills.add_run(f"Technical: {skills.get('technical', '')}\n").bold = True
    p_skills.add_run(f"Languages: {skills.get('languages', '')}\n")
    p_skills.add_run(f"Interests: {skills.get('interests', '')}")

    doc.save(output_path)
    print(f"Document saved: {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Ruta al archivo JSON con el contenido")
    parser.add_argument("--format", choices=["docx", "pdf"], default="docx")
    parser.add_argument("--output", required=True, help="Ruta del archivo de salida")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.format == "docx":
        create_docx(data, args.output)
    elif args.format == "pdf":
        docx_temp = args.output.replace(".pdf", ".docx")
        create_docx(data, docx_temp)
        # Conversión a PDF vía LibreOffice o docx2pdf
        os.system(f"soffice --headless --convert-to pdf {docx_temp} --outdir .")
        print(f"PDF generado: {args.output}")

if __name__ == "__main__":
    main()