# Skills

Colección de skills reutilizables para agentes de código.

## `context-architect-gemini`

Skill para diseñar, migrar y mantener una arquitectura de contexto modular y eficiente en tokens para **Gemini CLI** ([`context-architect-gemini/SKILL.md`](context-architect-gemini/SKILL.md)).

### ¿Qué genera y gestiona?

- **`GEMINI.md` (raíz y por carpeta)**: identidad del proyecto, comandos, mapa de directorios, índice de reglas (*Rules index*) e importaciones `@./`.
- **`.gemini/rules/*.md`**: convenciones por tipo de archivo o área (enlazadas desde el *Rules index* o mediante `@./` en un `GEMINI.md` específico de carpeta, ya que Gemini CLI no carga reglas por glob automáticamente).
- **`standards/*.md`**: especificaciones compartidas (estilo de código, pruebas, API, seguridad, flujo Git) diferenciando políticas decididas por el usuario (`decision`) y hechos observados del repositorio (`observed`).
- **`scratchpad.md`**: mapa vivo de arquitectura, registro de cambios y línea base de sincronización (referenciado bajo demanda, sin `@import`).

### Modos de operación

1. **INIT**: analiza el repositorio desde cero, entrevista al usuario para definir estándares y genera la arquitectura completa.
2. **UPGRADE**: audita una configuración existente (`GEMINI.md`, `.gemini/`, `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, etc.) y la migra sin perder contenido hacia buenas prácticas.
3. **SYNC**: detecta desviaciones (*drift*) tras cambios en el código y actualiza documentación, reglas y `scratchpad.md`.

### Estructura de la skill

```text
context-architect-gemini/
├── SKILL.md                          # Flujo principal e instrucciones de la skill
├── assets/
│   └── scratchpad-template.md        # Plantilla base para scratchpad.md
├── references/
│   ├── standards-questionnaire.md    # Cuestionario por categorías para definir estándares
│   ├── subagent-delegation.md        # Estrategia de partición y delegación en repos grandes
│   ├── sync-mode.md                  # Procedimiento de sincronización y hooks opcionales
│   ├── templates.md                  # Plantillas para GEMINI.md raíz, scoped y reglas
│   └── upgrade-mode.md               # Guía de auditoría y migración sin pérdidas
└── scripts/
    ├── _common.py                    # Utilidades compartidas (recorrido, globs, conteo)
    ├── scan_repo.py                  # Inventario determinista y veredicto de delegación
    ├── audit_context.py              # Auditoría y puntuación de contexto existente
    └── detect_drift.py               # Validación de imports/globs, detección de drift y --stamp
```

### Scripts incluidos

| Script | Propósito | Uso |
|---|---|---|
| [`scan_repo.py`](context-architect-gemini/scripts/scan_repo.py) | Inventario de lenguajes, manifiestos, herramientas y particiones sugeridas | `python context-architect-gemini/scripts/scan_repo.py [ROOT] [--json]` |
| [`audit_context.py`](context-architect-gemini/scripts/audit_context.py) | Audita archivos de contexto existentes y reporta hallazgos | `python context-architect-gemini/scripts/audit_context.py [ROOT] [--json]` |
| [`detect_drift.py`](context-architect-gemini/scripts/detect_drift.py) | Valida imports/reglas, detecta cambios desde el último sync y actualiza la línea base | `python context-architect-gemini/scripts/detect_drift.py [ROOT] [--json\|--quiet\|--hook\|--stamp]` |

## `context-architect`

Variación para **Claude Code** orientada a diseñar, migrar y mantener una arquitectura de contexto modular y eficiente en tokens ([`context-architect/SKILL.md`](context-architect/SKILL.md)).

### ¿Qué genera y gestiona?

- **`CLAUDE.md` (raíz y por carpeta)**: identidad del proyecto, comandos, mapa de directorios e importaciones `@`; el archivo raíz se carga al inicio y los de subcarpetas cuando Claude lee archivos en ellas.
- **`.claude/rules/*.md`**: convenciones acotadas por rutas mediante frontmatter YAML `paths:`, cargadas cuando Claude trabaja con archivos que coinciden con esos globs.
- **`.claude/standards/*.md`**: especificaciones compartidas (estilo de código, pruebas, API, seguridad, flujo Git) construidas con decisiones del usuario (`decision`) y hechos detectados en el repo (`observed`), cargadas solo al importarse con `@`.
- **`scratchpad.md`**: mapa vivo de arquitectura, registro de cambios y línea base de sincronización (referenciado bajo demanda, sin `@import`).

### Modos de operación

1. **INIT**: analiza el repositorio desde cero (con subagentes en paralelo si el tamaño lo requiere), entrevista al usuario para definir estándares y genera toda la arquitectura.
2. **UPGRADE**: audita una configuración existente (`CLAUDE.md`, `.claude/`, `GEMINI.md`, `AGENTS.md`, `.cursorrules`, etc.) y la migra sin perder contenido hacia buenas prácticas.
3. **SYNC**: detecta desviaciones (*drift*) tras cambios en el código y actualiza reglas, estándares, `CLAUDE.md` y `scratchpad.md`.

### Estructura de la skill

```text
context-architect/
├── SKILL.md                          # Flujo principal e instrucciones de la skill
├── assets/
│   └── scratchpad-template.md        # Plantilla base para scratchpad.md
├── references/
│   ├── standards-questionnaire.md    # Cuestionario por categorías para definir estándares
│   ├── subagent-delegation.md        # Estrategia de partición y subagentes en paralelo
│   ├── sync-mode.md                  # Procedimiento de sincronización y hooks opcionales
│   ├── templates.md                  # Plantillas para CLAUDE.md raíz, scoped y reglas
│   └── upgrade-mode.md               # Guía de auditoría y migración sin pérdidas
└── scripts/
    ├── _common.py                    # Utilidades compartidas (recorrido, globs, conteo)
    ├── scan_repo.py                  # Inventario determinista y veredicto de delegación
    ├── audit_context.py              # Auditoría y puntuación de contexto existente
    └── detect_drift.py               # Validación de imports/globs, detección de drift y --stamp
```

### Scripts incluidos

| Script | Propósito | Uso |
|---|---|---|
| [`scan_repo.py`](context-architect/scripts/scan_repo.py) | Inventario de lenguajes, manifiestos, herramientas y particiones sugeridas | `python context-architect/scripts/scan_repo.py [ROOT] [--json]` |
| [`audit_context.py`](context-architect/scripts/audit_context.py) | Audita archivos de contexto existentes y reporta hallazgos | `python context-architect/scripts/audit_context.py [ROOT] [--json]` |
| [`detect_drift.py`](context-architect/scripts/detect_drift.py) | Valida imports/reglas, detecta cambios desde el último sync y actualiza la línea base | `python context-architect/scripts/detect_drift.py [ROOT] [--json\|--quiet\|--stamp]` |

## `cv-job-tailor`

Skill para adaptar y reescribir CVs según vacantes específicas (LinkedIn, Indeed o texto libre), integrando repositorios de GitHub y datos complementarios de LinkedIn, con traducción español/inglés y exportación a `.docx` o `.pdf` ([`cv-job-tailor/SKILL.md`](cv-job-tailor/SKILL.md)).

### Flujo de trabajo

1. **Extracción y análisis de vacante**: identifica palabras clave técnicas, seniority, certificaciones, responsabilidades e idioma requerido.
2. **Consulta en GitHub**: busca hasta 2 proyectos relevantes mediante `fetch_github.py` según las tecnologías de la oferta.
3. **Consulta en LinkedIn**: si faltan certificaciones, diplomas o experiencia complementaria en `cv_template.json`, consulta `linkedin_profile.json` o `fetch_linkedin.py`.
4. **Adaptación del contenido**: ajusta resumen, logros con métricas, habilidades e idioma (español o inglés).
5. **Exportación**: genera el CV final en `.docx` o `.pdf` a partir de un JSON con el esquema de `cv_template.json`.

### Estructura de la skill

```text
cv-job-tailor/
├── SKILL.md                          # Flujo e instrucciones de adaptación de CV
├── references/
│   ├── cv_template.json              # Plantilla base y esquema JSON del CV
│   └── linkedin_profile.json         # Perfil de respaldo con datos extendidos de LinkedIn
└── scripts/
    ├── fetch_github.py               # Consulta repositorios en GitHub según keywords
    ├── fetch_linkedin.py             # Busca información complementaria en linkedin_profile.json
    └── export_cv.py                  # Exporta el JSON estructurado a .docx o .pdf
```

### Scripts incluidos

| Script | Propósito | Uso |
|---|---|---|
| [`fetch_github.py`](cv-job-tailor/scripts/fetch_github.py) | Filtra repositorios públicos de GitHub por palabras clave | `python cv-job-tailor/scripts/fetch_github.py --user luiselodeon [keywords...]` |
| [`fetch_linkedin.py`](cv-job-tailor/scripts/fetch_linkedin.py) | Recupera certificaciones y experiencia extendida del perfil local de LinkedIn | `python cv-job-tailor/scripts/fetch_linkedin.py --url <URL_PERFIL>` |
| [`export_cv.py`](cv-job-tailor/scripts/export_cv.py) | Genera el documento final en formato Word o PDF | `python cv-job-tailor/scripts/export_cv.py --data <cv.json> --format <docx\|pdf> --output <archivo>` |

## `html-to-md`

Skill (`v1.1.0`) para convertir archivos HTML individuales o directorios completos a Markdown limpio y estructurado, preservando enlaces, imágenes, tablas en sintaxis GFM y metadatos en frontmatter YAML ([`html-to-md/SKILL.md`](html-to-md/SKILL.md)).

### Capacidades principales

- **Extracción de metadatos**: convierte `<title>`, `description`, `author`, `keywords`, `og:title` y `og:description` en frontmatter YAML.
- **Limpieza estructural**: elimina `script`, `style`, `noscript` y `svg`, aplanando contenedores semánticos sin perder el texto.
- **Modo individual o recursivo**: procesa un archivo `.html` o recorre carpetas completas filtrando por extensión (`.html`, `.htm`, `.xhtml` por defecto).

### Estructura de la skill

```text
html-to-md/
├── SKILL.md                          # Reglas de conversión y guía de uso
├── convert.py                        # Conversor CLI basado en BeautifulSoup y html2text
└── requirements.txt                  # Dependencias Python (beautifulsoup4, html2text)
```

### Uso

```bash
pip install -r html-to-md/requirements.txt

# Archivo individual
python html-to-md/convert.py ruta/al/archivo.html [salida.md]

# Directorio recursivo
python html-to-md/convert.py ruta/al/directorio [carpeta_salida] [--ext .html .htm .xhtml]
```


