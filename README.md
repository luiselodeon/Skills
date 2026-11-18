# Skills

Colección de skills reutilizables para agentes de código.

## Instalación

Cada skill es una carpeta con un `SKILL.md`. Para instalarla basta con copiar esa carpeta (completa, con sus `scripts/` y `references/`) al directorio de skills del agente. Primero clona el repositorio:

```bash
git clone https://github.com/luiselodeon/Skills.git
cd Skills
```

### Claude Code (`context-architect`, `cv-job-tailor`, `html-to-md`)

| Alcance | Destino |
|---|---|
| Personal (todos tus proyectos) | `~/.claude/skills/<nombre-skill>/` |
| Solo un proyecto (se comparte vía git) | `<proyecto>/.claude/skills/<nombre-skill>/` |

```bash
# macOS / Linux / Git Bash
mkdir -p ~/.claude/skills
cp -r cv-job-tailor ~/.claude/skills/
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse cv-job-tailor "$env:USERPROFILE\.claude\skills\"
```

Reinicia Claude Code; la skill se activa sola cuando la tarea coincide con su descripción, o puedes invocarla con `/<nombre-skill>`.

### Claude.ai (web / escritorio)

Comprime la carpeta de la skill en un `.zip` (con la carpeta en la raíz del zip) y súbelo en **Configuración → Capacidades → Skills**:

```bash
zip -r cv-job-tailor.zip cv-job-tailor
```

Las skills que ejecutan scripts locales (`cv-job-tailor`, `context-architect`) funcionan mejor en Claude Code, donde tienen acceso a tu sistema de archivos y a Python.

### Antigravity CLI (`context-architect-gemini`, `cv-job-tailor`, `html-to-md`)

| Alcance | Destino |
|---|---|
| Personal (todos tus proyectos) | `~/.gemini/config/skills/<nombre-skill>/` |
| Solo un proyecto (se comparte vía git) | `<proyecto>/.agents/skills/<nombre-skill>/` |

```bash
# macOS / Linux / Git Bash
mkdir -p ~/.gemini/config/skills
cp -r context-architect-gemini ~/.gemini/config/skills/
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.gemini\config\skills" | Out-Null
Copy-Item -Recurse context-architect-gemini "$env:USERPROFILE\.gemini\config\skills\"
```

También puedes registrar la carpeta del clon sin copiarla mediante `entries` en `~/.gemini/config/skills.json` o `<proyecto>/.agents/skills.json`. Al iniciar `agy`, la skill se descubre automáticamente, se activa cuando la tarea coincide con su descripción o puedes invocarla con `/<nombre-skill>`.

### Dependencias

Algunas skills necesitan Python 3 y paquetes adicionales:

| Skill | Instalar |
|---|---|
| `cv-job-tailor` | `pip install python-docx docx2pdf` (+ Microsoft Word o LibreOffice para generar PDF) |
| `html-to-md` | `pip install -r html-to-md/requirements.txt` |
| `context-architect`, `context-architect-gemini` | Solo Python 3 (biblioteca estándar) |

Para actualizar una skill, haz `git pull` y vuelve a copiar la carpeta.

## `context-architect-gemini`

Skill para diseñar, migrar y mantener una arquitectura de contexto modular y eficiente en tokens para **Gemini CLI** (compatible con `GEMINI.md` en **Antigravity CLI**) ([`context-architect-gemini/SKILL.md`](context-architect-gemini/SKILL.md)).

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

Skill para adaptar un CV a una vacante de LinkedIn o Indeed y entregarlo en PDF optimizado para ATS, con reporte de compatibilidad ([`cv-job-tailor/SKILL.md`](cv-job-tailor/SKILL.md)).

### Flujo de trabajo

1. **Datos de entrada**: pide el link de LinkedIn, el de GitHub y el de la vacante (más el PDF del perfil de LinkedIn, porque LinkedIn bloquea la lectura automática).
2. **Perfil persistente**: crea o reutiliza `~/cv-job-tailor/<usuario-linkedin>/profile.json` con la información y experiencia de la persona; las respuestas nuevas se guardan ahí.
3. **Análisis de la vacante**: must-haves, keywords exactas, seniority e idioma; cruce con el perfil y GitHub (✅/🟡/❌).
4. **Redacción**: resumen, bullets y habilidades alineados a la vacante sin inventar datos.
5. **Exportación**: PDF de una página en `~/cv-job-tailor/<usuario>/aplicaciones/<fecha>_<empresa>/`, junto con la vacante y el JSON usado.

### Estructura de la skill

```text
cv-job-tailor/
├── SKILL.md                          # Flujo e instrucciones de adaptación de CV
├── references/
│   └── cv_template.json              # Esquema JSON del CV
└── scripts/
    ├── fetch_github.py               # Ordena repositorios de GitHub según keywords (con README opcional)
    └── export_cv.py                  # Exporta el JSON a .docx y .pdf (Word vía docx2pdf o LibreOffice)
```

### Scripts incluidos

| Script | Propósito | Uso |
|---|---|---|
| [`fetch_github.py`](cv-job-tailor/scripts/fetch_github.py) | Ordena repositorios públicos de GitHub por coincidencia con la vacante | `python cv-job-tailor/scripts/fetch_github.py --user <url-github> --readme [keywords...]` |
| [`export_cv.py`](cv-job-tailor/scripts/export_cv.py) | Genera el CV en Word o PDF | `python cv-job-tailor/scripts/export_cv.py --data <cv.json> --format pdf --output <archivo.pdf>` |

Requiere `pip install python-docx docx2pdf` (y Microsoft Word o LibreOffice para el PDF).

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


