# Estilo de contenido docente

## Fuentes y citas visibles

- Los archivos internos de trabajo, como `sesion6.md`, `sesion7.md` o rutas bajo `02-material_de_referencia/`, no deben citarse como fuentes visibles en láminas, guías o materiales finales.
- Las fuentes visibles deben corresponder a materiales citables: normas, doctrina, jurisprudencia, informes, artículos, libros u otros documentos académicos o institucionales identificables.
- Las citas deben seguir APA 7 cuando corresponda. En pies de lámina puede usarse una forma abreviada, siempre que sea clara y permita reconocer la fuente.
- Si falta información bibliográfica suficiente, usar: `Fuente pendiente de verificación`.
- Para normas peruanas, citar el nombre oficial de la norma, número, año y materia.
- Cuando el contenido desarrolle instituciones de la Ley del Procedimiento Administrativo General, citar el Decreto Supremo N.° 006-2026-JUS, que aprueba el Texto Único Ordenado de la Ley N.° 27444, Ley del Procedimiento Administrativo General.

Ejemplo de fuente normativa completa:

> Ministerio de Justicia y Derechos Humanos. (2026). Decreto Supremo N.° 006-2026-JUS, que aprueba el Texto Único Ordenado de la Ley N.° 27444, Ley del Procedimiento Administrativo General.

Ejemplo de fuente abreviada para pie de lámina:

> Fuente: MINJUSDH, D.S. N.° 006-2026-JUS, TUO de la Ley N.° 27444.

## Presentaciones HTML

- Las presentaciones en HTML deben conservar navegación, miniaturas, vista general, numeración, progreso y puntero láser cuando esos controles ya existan.
- Las animaciones deben ser sobrias y funcionales: transiciones breves de entrada, énfasis ligero de la lámina activa y señales discretas al cambiar de sección.
- Toda animación debe respetar `@media (prefers-reduced-motion: reduce)` y quedar desactivada o reducida para usuarios que prefieran menos movimiento.
- Evitar dependencias externas para efectos visuales simples; preferir CSS y JavaScript local embebido cuando la presentación sea autocontenida.

## Logo institucional

- Usar el logo institucional desde `assets/` con ruta relativa local. No enlazar logos externos ni depender de hotlinks.
- Si existe `assets/Logo_de_la_Universidad_Científica_del_Sur.png`, usar ese archivo como referencia principal del logo de la Universidad Científica del Sur en salidas HTML.
- Verificar que el logo sea visible en láminas de espera, portada, secciones internas y cierre.

## Control de calidad

- Antes de publicar una presentación, revisar que no haya referencias visibles a archivos internos de trabajo ni rutas del repositorio.
- Verificar que las fuentes normativas y doctrinales visibles identifiquen materiales citables, especialmente el TUO de la Ley N.° 27444 cuando corresponda.
- Comprobar que las rutas locales de imágenes existan desde la ubicación del HTML generado.
