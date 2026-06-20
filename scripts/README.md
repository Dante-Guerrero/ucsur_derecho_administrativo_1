# Flujo de conversión de insumos

Este directorio contiene scripts reutilizables para convertir documentos fuente de
`01-insumos_originales/` en Markdown revisable dentro de
`02-material_de_referencia/`.

## Instalación

```bash
pip install -r requirements.txt
```

Si tu entorno no tiene el comando `python`, usa `python3` y `pip3`.

## Uso

```bash
python scripts/convert_insumos_to_markdown.py
```

El script:

- lee los archivos ubicados en `01-insumos_originales/`;
- convierte `.txt`, `.md`, `.html`, `.htm`, `.docx` y `.pdf`;
- omite archivos que ya tengan conversión registrada por frontmatter, índice,
  manifiesto o nombre base equivalente;
- no modifica los documentos originales;
- no sobrescribe Markdown existentes; si detecta un mismo nombre con contenido
  distinto, genera una salida versionada;
- escribe los Markdown resultantes en `02-material_de_referencia/`;
- genera `02-material_de_referencia/README.md` con el detalle de conversión;
- actualiza `02-material_de_referencia/conversion_manifest.json` con hash
  SHA-256 de cada insumo detectado.

Los PDF se procesan por extracción de texto, sin OCR. Si un PDF parece escaneado
o extrae muy poco texto, queda marcado para revisión manual.
