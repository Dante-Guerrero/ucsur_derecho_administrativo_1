# UCSUR Derecho Administrativo 1

Repositorio de trabajo para organizar insumos, materiales de referencia y modelos
del curso.

## Conversión de insumos a Markdown

Los documentos originales se guardan en `01-insumos_originales/` y no deben
modificarse. Para convertirlos a Markdown revisable en
`02-material_de_referencia/`, instala las dependencias y ejecuta:

```bash
pip install -r requirements.txt
python scripts/convert_insumos_to_markdown.py
```

Si tu entorno no tiene `python`, usa:

```bash
pip3 install -r requirements.txt
python3 scripts/convert_insumos_to_markdown.py
```

El indice de resultados se genera en `02-material_de_referencia/README.md`.
Cada Markdown convertido debe revisarse antes de usarse como fuente docente,
especialmente cuando proviene de PDF.
