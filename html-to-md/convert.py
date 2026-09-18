#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
import html2text


def extract_metadata(soup: BeautifulSoup) -> dict:
    """Extrae metadatos relevantes del HTML (title, description, author, etc.)."""
    metadata = {}
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        metadata["title"] = title_tag.string.strip()

    for meta in soup.find_all("meta"):
        name = meta.get("name") or meta.get("property")
        content = meta.get("content")
        if name and content:
            name_clean = name.lower().strip()
            if name_clean in ["description", "author", "keywords", "og:title", "og:description"]:
                metadata[name_clean] = content.strip()
    return metadata


def html_to_markdown(html_content: str) -> str:
    """Convierte una cadena de HTML a Markdown preservando contenido, tablas y enlaces."""
    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Extraer metadatos
    metadata = extract_metadata(soup)

    # 2. Descomponer scripts, estilos y elementos decorativos/invisibles
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    # 3. Configurar html2text para máxima fidelidad
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_tables = False
    h.body_width = 0          # Sin ajuste de línea forzado (evita cortar párrafos o tablas)
    h.protect_links = True
    h.unicode_snob = True     # Mantiene caracteres UTF-8 puros sin escapar a HTML entities
    h.mark_code = True        # Delimita bloques de código claramente
    h.single_line_break = False

    # Extraer contenido principal
    target = soup.body if soup.body else soup
    markdown_body = h.handle(str(target)).strip()

    # 4. Generar Frontmatter si existen metadatos
    result = []
    if metadata:
        result.append("---")
        for k, v in metadata.items():
            # Escapar comillas dobles en el valor si existen
            v_escaped = v.replace('"', '\\"')
            result.append(f'{k}: "{v_escaped}"')
        result.append("---\n")

    result.append(markdown_body)
    return "\n".join(result)


def process_single_file(src_path: Path, dest_path: Path) -> bool:
    """Lee un archivo HTML, lo convierte y lo escribe en dest_path."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()

        md_content = html_to_markdown(html_content)

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return True
    except Exception as e:
        print(f"[ERROR] Error al procesar '{src_path}': {e}", file=sys.stderr)
        return False


def convert_directory(src_dir: Path, dest_dir: Path, extensions: list) -> tuple[int, int]:
    """Recorre de forma recursiva src_dir y replica la estructura en dest_dir con .md."""
    total_files = 0
    successful_files = 0

    for root, _, files in os.walk(src_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in extensions:
                total_files += 1
                
                # Calcular ruta relativa para replicar subcarpetas
                rel_path = file_path.relative_to(src_dir)
                dest_file_path = (dest_dir / rel_path).with_suffix(".md")

                print(f"-> Convirtiendo: {rel_path} -> {dest_file_path.relative_to(dest_dir)}")
                if process_single_file(file_path, dest_file_path):
                    successful_files += 1

    return total_files, successful_files


def main():
    parser = argparse.ArgumentParser(
        description="Convierte archivos HTML a Markdown de forma individual o recursiva en directorios."
    )
    parser.add_argument(
        "input",
        type=str,
        help="Ruta al archivo .html o directorio de entrada."
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        type=str,
        help="Ruta al archivo .md o directorio de salida (opcional)."
    )
    parser.add_argument(
        "--ext",
        nargs="+",
        default=[".html", ".htm", ".xhtml"],
        help="Extensiones a procesar en modo directorio (por defecto: .html .htm .xhtml)."
    )

    args = parser.parse_args()

    src_path = Path(args.input).resolve()

    if not src_path.exists():
        print(f"Error: La ruta de entrada '{src_path}' no existe.", file=sys.stderr)
        sys.exit(1)

    # Extensiones normalizadas en minúsculas
    extensions = [e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.ext]

    # MODO 1: Directorio recursivo
    if src_path.is_dir():
        dest_dir = Path(args.output).resolve() if args.output else src_path / "markdown_output"
        print("=== Iniciando conversión recursiva ===")
        print(f"Origen:  {src_path}")
        print(f"Destino: {dest_dir}\n")

        total, success = convert_directory(src_path, dest_dir, extensions)

        print("\n=== Resumen ===")
        print(f"Archivos encontrados: {total}")
        print(f"Archivos convertidos exitosamente: {success}")
        print(f"Archivos fallidos: {total - success}")

    # MODO 2: Archivo individual
    elif src_path.is_file():
        if args.output:
            dest_file = Path(args.output).resolve()
            # Si el destino dado es una carpeta existente, guardar dentro con el mismo nombre y .md
            if dest_file.is_dir():
                dest_file = dest_file / src_path.with_suffix(".md").name
        else:
            dest_file = src_path.with_suffix(".md")

        print(f"Convirtiendo archivo individual: {src_path.name} -> {dest_file.name}")
        if process_single_file(src_path, dest_file):
            print(f"Archivo generado exitosamente en: {dest_file}")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()