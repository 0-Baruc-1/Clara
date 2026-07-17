# Evaluación del Reviewer

Este directorio mide al Reviewer sin modificar su lógica de producción.

El hito 1 entrega fixtures escritos a mano, matching estricto de cuatro anclas
(`category`, `artifact_type`, `artifact_id`, `responsible_agent`), diagnósticos
de atribución errónea separados y la métrica de supresión de la compuerta de
precisión. Sus 68 casos se distribuyen así:

- 40 errores sintéticos: 8 por cada una de las cinco clases requeridas.
- 10 controles correctos.
- 2 fallas capturadas de ejecuciones reales.
- 16 casos de compuerta de precisión: 8 pares alta/baja confianza.

Los controles son la clase individual más grande; los dos tipos de casos por
ausencia se prueban con confianza alta y baja. Un OA inexistente debe emitirse
incluso bajo confianza baja porque es verificable por presencia.

Ejecuta la prueba determinista del harness desde `backend/`:

```powershell
$env:CLARA_MOCK_MODE = "true"
python scripts/run_reviewer_eval.py
```

La salida se etiqueta `mock_harness_self_test`: verifica el evaluador, no el
desempeño de un modelo. El adaptador real, repeticiones y desviación estándar se
agregarán en el hito 2.

Antes de usar métricas reales, ejecuta la calibración adversarial:

```powershell
$env:CLARA_MOCK_MODE = "true"
python scripts/run_reviewer_eval.py --adversarial
```

Sus seis salidas mock son deliberadamente incorrectas: una omisión, un falso
positivo de control, una atribución errónea, una violación de supresión, un
hallazgo host-enforced y un id de artefacto incorrecto. Las pruebas fijan sus
resultados calculados a mano; por ejemplo, omitir uno de ocho errores
aritméticos exige recall `0.875`, y un falso positivo en uno de diez controles
exige FPR `0.1`.
