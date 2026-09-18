---
name: cv-job-tailor
description: Reescribe y adapta CVs a vacantes específicas (LinkedIn o Indeed), integrando repositorios de GitHub (https://github.com/luiselodeon) y datos complementarios de LinkedIn (https://www.linkedin.com/in/luis-alberto-arias-llaguno/), traduciendo a inglés/español y exportando en DOCX o PDF.
---

# CV Job Tailor Skill

## Propósito
Esta skill analiza una oferta laboral (LinkedIn, Indeed o texto provisto), evalúa el perfil base del usuario (`references/cv_template.json`), consulta proyectos relevantes en su GitHub (`https://github.com/luiselodeon`) y verifica información adicional en su perfil de LinkedIn (`https://www.linkedin.com/in/luis-alberto-arias-llaguno/`) en caso de que la vacante requiera competencias, certificaciones o detalles extendidos que no estén en el CV base. Finalmente, genera una versión optimizada para ATS y reclutadores en formato `.docx` o `.pdf`.

---

## Flujo de Trabajo

### 1. Extracción y Análisis de la Vacante
- Extraer palabras clave técnicas, nivel de seniority, certificaciones y responsabilidades principales de la oferta.
- Identificar el idioma requerido para la postulación (español o inglés). Si no se explicita, utilizar el idioma original de la oferta.

### 2. Consulta de Proyectos en GitHub
- Ejecutar `scripts/fetch_github.py --user luiselodeon [keywords...]` o consultar vía API/scraping para identificar repositorios que hagan match con la vacante (ej. Python, Machine Learning, APIs, n8n, SQL).
- Seleccionar hasta 2 proyectos relevantes para poblar el campo `projects` del CV.

### 3. Conexión y Consulta a LinkedIn (Información Adicional)
- **URL de referencia:** `https://www.linkedin.com/in/luis-alberto-arias-llaguno/`
- **Criterio de activación:** Si la vacante solicita certificaciones adicionales, diplomas, roles secundarios, actividades extracurriculares o un desglose más profundo de logros que no aparezca en `cv_template.json`:
  - Consultar los datos extendidos del perfil mediante el script `scripts/fetch_linkedin.py --url https://www.linkedin.com/in/luis-alberto-arias-llaguno/` (o leer el archivo de contexto `references/linkedin_profile.json`).
  - Incorporar únicamente aquellos datos validados que aporten valor directo a los requisitos de la vacante.

### 4. Reescritura y Adaptación del Contenido
- **Summary:** Redactar un resumen profesional alineado con la misión de la vacante, sin alterar la veracidad de la experiencia.
- **Experiencia Profesional:** Reforzar logros con métricas y palabras clave prioritarias en cada bullet point.
- **Habilidades e Intereses:** Reordenar las competencias técnicas priorizando las exigidas en la vacante.
- **Idioma:** Traducir fielmente al inglés o español con terminología estándar de la industria IT.

### 5. Generación del Documento
- Guardar el nuevo contenido generado en un JSON temporal (siguiendo el esquema de `references/cv_template.json`).
- Ejecutar:
  ```bash
  python scripts/export_cv.py --data temp_tailored_cv.json --format docx --output Luis_Arias_CV.docx
  # o para PDF:
  python scripts/export_cv.py --data temp_tailored_cv.json --format pdf --output Luis_Arias_CV.pdf