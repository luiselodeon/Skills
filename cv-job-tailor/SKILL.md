---
name: cv-job-tailor
description: Adapta un CV a una vacante concreta y entrega un PDF optimizado para ATS y reclutadores, más un reporte de compatibilidad. Pide al usuario su LinkedIn, su GitHub y el link de la vacante (LinkedIn o Indeed), guarda un perfil persistente con su información y experiencia para reutilizarlo en futuras postulaciones, y genera el CV en español o inglés. Usa esta skill siempre que alguien comparta una vacante, oferta, job posting o link de LinkedIn/Indeed jobs, pida "adaptar/hacer/optimizar mi CV", "CV para este puesto", "resume for this job", quiera saber qué tan bien encaja en un puesto o traducir su CV, aunque no mencione la skill.
---

# CV Job Tailor

Objetivo: un CV de **una página**, en **PDF**, que un reclutador entienda en 10 segundos y que un ATS puntúe alto para *esta* vacante, sin afirmar nada que la persona no pueda defender en una entrevista.

## Archivos

- **Perfil de la persona** (persistente): `~/cv-job-tailor/<slug>/profile.json` (o la ruta indicada por el usuario), donde `<slug>` es el usuario de LinkedIn (`linkedin.com/in/<slug>/`). Es la fuente de verdad: todo lo que se sabe de la persona vive aquí y se reutiliza en cada postulación.
- **Cada postulación**: `~/cv-job-tailor/<slug>/aplicaciones/<AAAA-MM-DD>_<empresa>/` (o la carpeta/ruta de exportación indicada por el usuario) con `vacante.md` (texto de la vacante — los anuncios se borran), `cv.json`, `CV_<Nombre>_<Empresa>.pdf` y el `.docx` intermedio. Si el usuario da una sola ruta base, guarda ahí tanto `profile.json` como los archivos exportados.
- `references/cv_template.json` — esquema del JSON de CV que recibe `scripts/export_cv.py`.

`~` es el home del usuario (en Windows `C:\Users\<usuario>`). Resuélvelo a ruta absoluta antes de escribir.

## Principio rector: verdad antes que keywords

Un CV con logros inventados se cae en la primera entrevista técnica y quema la candidatura. Por eso:
- No inventes métricas, tecnologías, roles, fechas ni certificaciones. Si una cifra haría más fuerte un bullet y no la tienes, pregúntala (paso 4).
- Puedes **reformular** (mejores verbos, el término exacto de la vacante para algo que la persona sí hizo) y **reordenar/priorizar**. No puedes **añadir** hechos.
- Un requisito sin evidencia va al reporte de brechas, no al CV.

## Flujo

### 1. Pedir los datos (un solo mensaje)
Al invocarse, si el usuario no los dio ya, pide de una vez:
1. Link de su perfil de **LinkedIn**.
2. Link de su perfil de **GitHub** (opcional si no tiene).
3. Link de la **vacante** en LinkedIn o Indeed (o el texto de la vacante).
4. **Ruta donde guardar el perfil (`profile.json`) y exportar el PDF** (opcional; si ya tienes ahí tu `profile.json` o archivos previos con tu info, indícala; por defecto usa `~/cv-job-tailor/<slug>/`).
5. **PDF de un CV anterior o actual** (opcional, adjunto o ruta en disco) para leerlo y combinar su información con la de LinkedIn.
6. Idioma del CV si no quiere el de la vacante.

Avisa en el mismo mensaje que LinkedIn e Indeed suelen bloquear la lectura automática, así que conviene compartir también **el PDF de su perfil de LinkedIn** (en su perfil: *Más → Guardar en PDF*) además de su CV anterior/actual si tiene, y tener a la mano el texto de la vacante por si el link no carga. Pedirlo desde el inicio ahorra una vuelta de conversación.

### 2. Cargar o crear el perfil
Calcula `<slug>` del link de LinkedIn y determina la carpeta del perfil (la ruta indicada por el usuario o, por defecto, `~/cv-job-tailor/<slug>/`). **Analiza primero qué hay en esa carpeta**: revisa si existe `profile.json` y también si hay otros archivos con información del usuario (`.pdf` de CV o de LinkedIn, `.docx`, `.md`, `.txt` u otros `.json`).

- **Si `profile.json` ya existe**:
  - Léelo y revisa `sources.linkedin_checked` y `sources.pdf_cv_checked` (si alguno falta, trátalo como `false`).
  - **Si ambos son `true`** y no hay archivos nuevos en la carpeta ni compartidos por el usuario: **usa `profile.json` directamente sin volver a buscar en la web la información del usuario**. Dile al usuario que lo vas a usar (fecha de `sources.updated`) y pregúntale solo si hay algo nuevo (nuevo empleo, certificación, proyecto).
  - **Si alguno es `false`** o hay archivos sin integrar (en la carpeta o compartidos ahora): extrae la información de las fuentes faltantes o nuevas (liga/PDF de LinkedIn y/o CV en PDF u otros archivos en la carpeta) y **complétalo** integrando lo nuevo en `profile.json` sin duplicar registros (si hay discrepancias en fechas o puestos, confírmalas antes de asumir). Actualiza los booleanos a `true` conforme se haya logrado revisar cada fuente y actualiza `sources.updated`.
- **Si `profile.json` no existe**, constrúyelo leyendo y **combinando** todas las fuentes disponibles:
  - Los archivos con información del usuario que ya estén en la carpeta (CV en PDF, PDF de LinkedIn, `.docx`, `.md`, `.txt`, etc.).
  - El **PDF de su CV anterior/actual** y/o el **PDF de su perfil de LinkedIn** compartidos (adjuntos o por ruta en disco).
  - El perfil de LinkedIn vía lectura web, por si es legible (normalmente devuelve un muro de login; no insistas).
  - Fusiona toda la información conservando el historial completo y complementando roles, métricas, proyectos o habilidades para obtener el perfil más completo posible; si hay discrepancias (fechas o puestos distintos), confírmalas antes de asumir. Si no hay nada legible, pide que pegue su experiencia o comparta el PDF. No inventes un perfil con lo que dice la URL.

Formato de `profile.json`: el mismo esquema de `references/cv_template.json` (sin `section_order`), con **todo** el historial (no solo lo relevante a una vacante), más:
```json
"additional_experience": [{"title": "", "issuer": "", "date": "", "description": ""}],
"volunteering": [],
"facts": ["Datos confirmados por el usuario que no están en su CV: p. ej. 'El chatbot de Cimiento atendía ~300 conversaciones/semana'"],
"sources": {
  "linkedin": "<url>",
  "github": "<url>",
  "linkedin_checked": true,
  "pdf_cv_checked": true,
  "updated": "AAAA-MM-DD"
}
```
- `linkedin_checked`: `true` solo si se logró extraer información del perfil de LinkedIn (vía web o vía PDF exportado de LinkedIn); `false` si bloqueó o no se ha revisado.
- `pdf_cv_checked`: `true` si se leyó e integró al menos un CV en PDF del usuario; `false` en caso contrario.

Guárdalo en la ruta elegida antes de seguir y dile al usuario dónde quedó: así la próxima vez solo tendrá que dar el link de la vacante.

### 3. Leer y analizar la vacante
- Intenta leer el link con WebFetch. Para LinkedIn, la forma `https://www.linkedin.com/jobs/view/<id>/` suele ser más legible que URLs con `currentJobId=`; extrae el id y prueba esa. Si sale vacío, un login o un captcha, pide el texto pegado.
- Guarda el texto en `vacante.md` de la carpeta de la postulación.
- Extrae: **must-have** y **nice-to-have**; **keywords exactas** tal como están escritas (el ATS compara cadenas: "Power BI", "scikit-learn", "LLMs"); seniority; idioma; empresa y puesto.

### 4. Cruce con el perfil y preguntas
Para cada must-have y keyword, busca evidencia en `profile.json` y GitHub. Clasifica: ✅ cubierto · 🟡 parcial/transferible · ❌ sin evidencia.

GitHub:
```bash
python scripts/fetch_github.py --user <url-github> --readme --top 6 python flask "machine learning"
```
Pasa las keywords técnicas de la vacante. El README suele ser la única descripción real del repo; léelo antes de elegir. Elige 1–3 proyectos que cubran must-haves que la experiencia laboral no cubre; si ninguno encaja, no pongas proyectos.

Si hay 🟡/❌ en must-haves o bullets clave sin resultado medible, haz **una sola ronda** de máximo 3–4 preguntas concretas ("¿Cuántos usuarios usaban el sistema?", "La vacante pide Docker, ¿lo has usado? ¿dónde?"). Guarda cada respuesta útil en `facts` (o en la sección que corresponda) de `profile.json` — así no se vuelve a preguntar. Si el usuario quiere ir directo, sigue sin esos datos y anótalos en el reporte.

### 5. Redactar el CV
Construye `cv.json` con el esquema de `references/cv_template.json`, seleccionando del perfil solo lo que sirve para esta vacante.

- **headline**: título objetivo alineado al puesto, p. ej. "Data Science Intern | Python · ML · Automation". Solo con lo que el perfil respalde.
- **summary**: 2–3 líneas, sin "yo"/"I" ni adjetivos vacíos ("apasionado", "hard-working"). Fórmula: *quién es (nivel + carrera/rol) → 2–3 fortalezas que la vacante pide, con evidencia → qué aporta al puesto*.
- **experience** (2–4 bullets por rol, el más relevante primero): *verbo de acción en pasado + qué hizo + con qué (keywords de la vacante) + resultado o alcance*.
  - Antes: "Integration of artificial intelligence agents for analysis, recommendation, and automated response tasks within the platform."
  - Después: "Integrated AI agents into a university information system to automate analysis, recommendations and responses for UANL." — se añade alcance real, no un resultado supuesto.
  - Una línea, máximo dos. Verbos distintos en cada bullet. Sin pronombres.
- **projects**: `name`, `tech` (stack corto), `description` (qué resuelve y resultado), `url`.
- **skills**: primero lo que la vacante pide, con su misma escritura. Quita lo irrelevante. Evita autoevaluaciones tipo "(Beginner)" salvo que la vacante pida nivel.
- **section_order**: estudiante o recién egresado → `experience, projects, education, certifications, skills` suele funcionar; si no tiene experiencia laboral, o la vacante pesa lo académico (trainee, beca, investigación), pon `education` o `projects` primero.
- **Idioma**: un solo idioma en todo el documento, incluidos meses (en: Jan, Dec · es: ene, dic) y títulos de diplomas. Empresas y tecnologías no se traducen.
- **Longitud**: una página. Si sobra, corta lo menos relevante.

### 6. Revisión antes de exportar
- [ ] Cada must-have ✅ aparece con la keyword exacta al menos una vez (idealmente summary + bullet o skills).
- [ ] Ningún dato que no esté en `profile.json` o en lo que respondió el usuario.
- [ ] Ningún bullet repite verbo inicial ni pasa de dos líneas.
- [ ] Idioma y formato de fechas consistentes.
- [ ] Cabe en una página (≈ 450–550 palabras como referencia).

### 7. Exportar a PDF
Dependencias: `python -c "import docx, docx2pdf"`; si falla, `pip install python-docx docx2pdf`. `docx2pdf` usa Microsoft Word; sin Word, el script intenta LibreOffice.

```bash
python scripts/export_cv.py --data "<carpeta>/cv.json" --format pdf --output "<ruta_pdf>/CV_<Nombre>_<Empresa>.pdf"
```
Usa la ruta de exportación que indicó el usuario (si dio la ruta de un archivo `.pdf`, úsala tal cual; si no indicó ninguna, usa `<carpeta>/CV_<Nombre>_<Empresa>.pdf`). Abre el PDF (lectura de archivo) y comprueba que sea **una página** y que no haya texto cortado. Si pasa de una página, recorta contenido en `cv.json` y vuelve a exportar. Si la conversión a PDF falla, entrega el `.docx` y explica qué falta instalar.

### 8. Entregar
Responde con la ruta del PDF y un reporte breve:

```
**PDF:** <ruta absoluta>
**Compatibilidad:** 6/8 must-haves cubiertos
**Keywords incluidas:** Python, SQL, scikit-learn, REST API, ...
**Brechas:** Docker (sin evidencia), Power BI (sin evidencia)
**Cómo cerrarlas:** qué decir en la entrevista, proyecto rápido o curso concreto
**Datos que mejorarían el CV:** métricas pendientes, etc.
**Perfil guardado:** <ruta de profile.json>
```

El reporte vale tanto como el CV: le dice a la persona dónde está fuerte, qué le van a preguntar y qué no conviene afirmar.
