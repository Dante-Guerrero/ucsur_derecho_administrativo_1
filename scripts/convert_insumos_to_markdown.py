#!/usr/bin/env python3
"""Convert source documents from 01-insumos_originales to Markdown."""

from __future__ import annotations

import argparse
import html
import re
import sys
import textwrap
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "01-insumos_originales"
OUTPUT_DIR = ROOT / "02-material_de_referencia"
INDEX_PATH = OUTPUT_DIR / "README.md"

SUPPORTED_FORMATS = {".txt", ".md", ".html", ".htm", ".docx", ".pdf"}
PDF_MIN_TEXT_CHARS = 500
PDF_MIN_AVG_CHARS_PER_PAGE = 80

AUTO_NOTE = (
    "> Documento convertido automáticamente desde el insumo original. Revisar "
    "estructura, citas y posibles errores de extracción antes de usarlo como "
    "fuente docente."
)


@dataclass
class ConversionResult:
    source: Path
    output: Path | None
    formato: str
    estado: str
    observaciones: str = ""
    error: str = ""


class SimpleMarkdownHTMLParser(HTMLParser):
    """Small HTML to Markdown-ish text parser used when BeautifulSoup is absent."""

    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "footer",
        "header",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.heading_level: int | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._newline(2)
            self.heading_level = int(tag[1])
            self.parts.append("#" * self.heading_level + " ")
        elif tag == "li":
            self._newline(1)
            self.parts.append("- ")
        elif tag in self.BLOCK_TAGS:
            self._newline(1 if tag == "br" else 2)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_level = None
            self._newline(2)
        elif tag in self.BLOCK_TAGS:
            self._newline(2)

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = " ".join(html.unescape(data).split())
        if not text:
            return
        if self.parts and not self.parts[-1].endswith(("\n", " ", "# ", "- ")):
            self.parts.append(" ")
        self.parts.append(text)

    def get_markdown(self) -> str:
        return normalize_markdown("".join(self.parts))

    def _newline(self, count: int) -> None:
        current = "".join(self.parts[-3:])
        existing = len(current) - len(current.rstrip("\n"))
        if existing < count:
            self.parts.append("\n" * (count - existing))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convierte documentos de 01-insumos_originales a Markdown."
    )
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not input_dir.exists():
        print(f"No existe el directorio de insumos: {input_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(path for path in input_dir.iterdir() if path.is_file())
    output_names = allocate_output_names(sources)
    results: list[ConversionResult] = []

    for source in sources:
        formato = source.suffix.lower().lstrip(".") or "sin_extension"
        output_path = output_dir / output_names[source]

        if source.suffix.lower() not in SUPPORTED_FORMATS:
            results.append(
                ConversionResult(
                    source=source,
                    output=None,
                    formato=formato,
                    estado="omitido",
                    observaciones="Formato no soportado todavia.",
                )
            )
            continue

        try:
            body, observation = extract_markdown(source)
            markdown = build_markdown(source, formato, body, observation)
            output_path.write_text(markdown, encoding="utf-8")
            results.append(
                ConversionResult(
                    source=source,
                    output=output_path,
                    formato=formato,
                    estado="convertido",
                    observaciones=observation,
                )
            )
        except Exception as exc:  # Keep processing the rest of the batch.
            results.append(
                ConversionResult(
                    source=source,
                    output=output_path,
                    formato=formato,
                    estado="error",
                    error=str(exc),
                )
            )

    index_path = output_dir / "README.md"
    write_index(index_path, results, input_dir, output_dir)
    print_summary(results, index_path)
    return 0


def allocate_output_names(sources: list[Path]) -> dict[Path, str]:
    counters: dict[str, int] = {}
    allocated: dict[Path, str] = {}

    for source in sources:
        stem = sanitize_stem(source.stem)
        count = counters.get(stem, 0) + 1
        counters[stem] = count
        suffix = "" if count == 1 else f"_{count:02d}"
        allocated[source] = f"{stem}{suffix}.md"

    return allocated


def sanitize_stem(stem: str) -> str:
    cleaned = re.sub(r"\s+", " ", stem.strip())
    return cleaned or "documento"


def extract_markdown(source: Path) -> tuple[str, str]:
    suffix = source.suffix.lower()
    extractors: dict[str, Callable[[Path], tuple[str, str]]] = {
        ".txt": extract_plain_text,
        ".md": extract_plain_text,
        ".html": extract_html,
        ".htm": extract_html,
        ".docx": extract_docx,
        ".pdf": extract_pdf,
    }
    return extractors[suffix](source)


def extract_plain_text(source: Path) -> tuple[str, str]:
    text = source.read_text(encoding="utf-8", errors="replace")
    return normalize_markdown(text), ""


def extract_html(source: Path) -> tuple[str, str]:
    raw = source.read_text(encoding="utf-8", errors="replace")
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        lines: list[str] = []
        for element in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote"]
        ):
            text = " ".join(element.get_text(" ", strip=True).split())
            if not text:
                continue
            tag_name = element.name.lower()
            if tag_name.startswith("h") and tag_name[1:].isdigit():
                level = min(int(tag_name[1:]), 6)
                lines.append(f"{'#' * level} {text}")
            elif tag_name == "li":
                lines.append(f"- {text}")
            elif tag_name == "blockquote":
                lines.append(f"> {text}")
            else:
                lines.append(text)

        if lines:
            return normalize_markdown("\n\n".join(lines)), ""
    except ImportError:
        pass

    fallback = SimpleMarkdownHTMLParser()
    fallback.feed(raw)
    return fallback.get_markdown(), "HTML convertido con parser basico de Python."


def extract_docx(source: Path) -> tuple[str, str]:
    try:
        import docx
    except ImportError as exc:
        raise RuntimeError(
            "Falta la dependencia python-docx. Ejecuta: pip install -r requirements.txt"
        ) from exc

    document = docx.Document(source)
    blocks: list[str] = []
    for paragraph in document.paragraphs:
        text = " ".join(paragraph.text.split())
        if not text:
            continue
        style_name = paragraph.style.name.lower() if paragraph.style else ""
        if style_name.startswith("heading"):
            level_match = re.search(r"(\d+)", style_name)
            level = min(int(level_match.group(1)), 6) if level_match else 2
            blocks.append(f"{'#' * level} {text}")
        else:
            blocks.append(text)

    for table in document.tables:
        for row in table.rows:
            cells = [" ".join(cell.text.split()) for cell in row.cells]
            if any(cells):
                blocks.append(" | ".join(cells))

    return normalize_markdown("\n\n".join(blocks)), ""


def extract_pdf(source: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "Falta la dependencia pypdf. Ejecuta: pip install -r requirements.txt"
        ) from exc

    reader = PdfReader(str(source))
    pages_text: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = normalize_pdf_text(text)
        if text:
            pages_text.append(text)
        else:
            pages_text.append(f"<!-- Pagina {index}: sin texto extraido -->")

    body = normalize_markdown("\n\n".join(pages_text))
    extracted_chars = len(re.sub(r"\s+", "", body))
    page_count = max(len(reader.pages), 1)
    observation = ""
    if (
        extracted_chars < PDF_MIN_TEXT_CHARS
        or extracted_chars / page_count < PDF_MIN_AVG_CHARS_PER_PAGE
    ):
        observation = (
            "Posible PDF escaneado o extracción insuficiente; requiere OCR o "
            "revisión manual."
        )
    return body, observation


def normalize_pdf_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)

    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs)


def normalize_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def build_markdown(source: Path, formato: str, body: str, observation: str) -> str:
    title = sanitize_title(source.stem)
    frontmatter = {
        "titulo": title,
        "archivo_origen": source.relative_to(ROOT).as_posix(),
        "formato_origen": formato,
        "fecha_conversion": date.today().isoformat(),
        "estado_conversion": "borrador",
        "observaciones": observation,
    }
    yaml = "\n".join(
        [
            "---",
            f'titulo: "{yaml_escape(frontmatter["titulo"])}"',
            f'archivo_origen: "{yaml_escape(frontmatter["archivo_origen"])}"',
            f'formato_origen: "{yaml_escape(frontmatter["formato_origen"])}"',
            f'fecha_conversion: "{frontmatter["fecha_conversion"]}"',
            f'estado_conversion: "{frontmatter["estado_conversion"]}"',
            f'observaciones: "{yaml_escape(frontmatter["observaciones"])}"',
            "---",
        ]
    )
    body = body or "_No se extrajo texto del documento original._"
    return f"{yaml}\n\n{AUTO_NOTE}\n\n{body}\n"


def sanitize_title(stem: str) -> str:
    return re.sub(r"\s+", " ", stem.strip()) or "Documento sin titulo"


def yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def write_index(
    index_path: Path, results: list[ConversionResult], input_dir: Path, output_dir: Path
) -> None:
    converted = sum(1 for result in results if result.estado == "convertido")
    omitted = sum(1 for result in results if result.estado == "omitido")
    errors = sum(1 for result in results if result.estado == "error")

    lines = [
        "# Índice de conversión",
        "",
        f"Fecha de conversión: {date.today().isoformat()}",
        "",
        f"Directorio de origen: `{relative_or_absolute(input_dir)}`",
        f"Directorio de salida: `{relative_or_absolute(output_dir)}`",
        "",
        "## Resumen",
        "",
        f"- Archivos detectados: {len(results)}",
        f"- Archivos convertidos: {converted}",
        f"- Archivos omitidos: {omitted}",
        f"- Archivos con error: {errors}",
        "",
        "## Detalle",
        "",
        "| Archivo original | Markdown generado | Formato | Estado | Observaciones / errores |",
        "| --- | --- | --- | --- | --- |",
    ]

    for result in results:
        source = relative_or_absolute(result.source)
        output = relative_or_absolute(result.output) if result.output else ""
        note = result.error or result.observaciones
        lines.append(
            "| "
            + " | ".join(
                [
                    table_escape(f"`{source}`"),
                    table_escape(f"`{output}`" if output else ""),
                    table_escape(result.formato),
                    table_escape(result.estado),
                    table_escape(note),
                ]
            )
            + " |"
        )

    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def relative_or_absolute(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def print_summary(results: list[ConversionResult], index_path: Path) -> None:
    converted = sum(1 for result in results if result.estado == "convertido")
    omitted = sum(1 for result in results if result.estado == "omitido")
    errors = sum(1 for result in results if result.estado == "error")
    message = f"""
    Conversión finalizada.
    Total de archivos detectados: {len(results)}
    Archivos convertidos: {converted}
    Archivos omitidos: {omitted}
    Archivos con error: {errors}
    Índice generado: {relative_or_absolute(index_path)}
    """
    print(textwrap.dedent(message).strip())


if __name__ == "__main__":
    raise SystemExit(main())
