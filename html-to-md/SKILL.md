---
name: html-to-md
description: Convierte archivos HTML completos a Markdown limpio y fiel sin perder enlaces, metadatos, tablas ni contenido estructural.
version: 1.1.0
---

# HTML to Markdown Converter

Convierte documentos HTML a Markdown preservando el 100% de la semántica de contenido textual y estructural.

## Reglas de Conversión
1. **Preservación total**: Conservar todo texto visible, enlaces (`href`), imágenes (`src`, `alt`), tablas completas y fragmentos de código.
2. **Metadatos frontmatter**: Si el HTML incluye etiquetas `<title>`, `<meta name="description">` o `<meta name="author">`, extraerlos al bloque YAML frontmatter inicial.
3. **Manejo de elementos incompatibles**: Contenedores semánticos (`<article>`, `<section>`, `<div>`) o clases de diseño se aplanan conservando su contenido textual.
4. **Tablas complejas**: Utilizar sintaxis GFM (GitHub Flavored Markdown).
5. **Procesamiento individual y en lote**: Capacidad de procesar un único archivo o árboles de carpetas recursivamente.

## Uso

### Archivo individual
```bash
python scripts/convert.py ruta/al/archivo.html [salida.md]