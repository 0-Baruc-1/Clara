# Clara

Clara es un copiloto de enseñanza para docentes de Chile. Su diferencia no es solo generar material: verifica las afirmaciones curriculares contra una fuente de Objetivos de Aprendizaje (OA), revisa la coherencia entre los artefactos y declara con honestidad lo que no pudo comprobar.

Una docente puede generar un pack, editarlo, pedir una nueva revisión, crear hojas imprimibles bajo demanda, auditar material creado fuera de Clara y observar cobertura curricular acumulada en su sesión local.

## Qué entrega

El flujo principal crea un pack editable para una clase:

- Plan de clase con OA verificados, arco pedagógico, conceptos, prerrequisitos y materiales.
- Guía de actividades con pasos docentes, productos esperados, agrupamiento y diferenciación.
- Evaluación con instrumento, respuestas esperadas, rúbrica y tabla de especificaciones agregada por objetivo.
- Revisión cruzada que comprueba coherencia, grounding de la evaluación, códigos OA y contradicciones internas.

Los materiales imprimibles se generan bajo demanda después de revisar el pack. La evaluación se muestra en versiones separadas para estudiante y docente. La interfaz permite imprimir el pack, solo la evaluación estudiantil o solo los materiales, y exportar Markdown.

## Arquitectura de agentes

1. **Planner**: busca OA usando herramientas curriculares, verifica cada código y define la estructura de la clase.
2. **Designer**: transforma la estructura en actividades de aula dentro de los presupuestos de tiempo.
3. **Assessment**: crea el instrumento, las respuestas y la rúbrica; la tabla de especificaciones se deriva de los ítems.
4. **Reviewer**: verifica los OA contra la fuente, revisa objetivos, evidencias, grounding y contradicciones. Si hay un hallazgo bloqueante atribuible a Designer o Assessment, solicita una sola corrección focalizada y vuelve a revisar.
5. **Materials**: genera únicamente las hojas que las actividades piden. Un segundo paso del Reviewer audita su correspondencia con la actividad.

Todos los agentes comparten un prefijo de sistema estable con reglas pedagógicas, de trazabilidad y de honestidad curricular. Esto favorece el prompt caching. La referencia curricular no se inyecta como un blob: Planner y Reviewer llaman `buscar_objetivos` y `verificar_objetivo` sobre el mismo proveedor local. Cada código citado debe estar verificado durante esa ejecución; si el proveedor falla, Clara falla cerrada en vez de aceptar un OA sin comprobar.

## Flujos adicionales

- **Auditar material existente**: importa planificación o evaluación en prosa, la interpreta de forma conservadora y utiliza el mismo Reviewer. Las conclusiones que dependen de una ausencia se muestran solo con suficiente confianza de lectura; un OA inexistente sigue siendo un hallazgo bloqueante porque es verificable por presencia.
- **Revisar mis cambios**: después de editar el pack en el navegador, la docente puede solicitar una auditoría de esa versión. Mantiene el mismo criterio de precisión que el material importado.
- **Cobertura curricular**: SQLite local registra solo asignatura, nivel, OA declarado, estado de verificación y evidencia de actividad. Un OA cuenta como cubierto únicamente si fue verificado y las actividades lo trabajaron. La vista declara de forma visible que solo representa los packs que Clara ha visto, no toda la planificación anual.
- **MCP**: Clara expone la auditoría y las herramientas curriculares para que otros agentes verifiquen su propio material antes de entregarlo.

## Ejecutar localmente

Requisitos: Python 3.11+ y Node.js 20+.

```powershell
# Terminal 1: API
cd backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```powershell
# Terminal 2: interfaz
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Abre la URL que muestra Vite (normalmente `http://localhost:5173`). La API queda en `http://localhost:8000` y su documentación en `http://localhost:8000/docs`.

## Modelos y variables de entorno

Para usar los agentes reales se requiere una clave de OpenAI y acceso a estos IDs de modelo:

- `gpt-5.6-terra`: razonamiento y generación principal (Planner, Designer, Assessment y Materials).
- `gpt-5.6-luna`: revisión de consistencia por defecto; puede sustituirse por Terra si se requiere más calidad.

Configura `backend/.env` así:

```dotenv
OPENAI_API_KEY=tu_clave
# Fallback global si no hay override por agente.
OPENAI_MODEL=gpt-5.6-terra
PLANNER_MODEL=gpt-5.6-terra
DESIGNER_MODEL=gpt-5.6-terra
ASSESSMENT_MODEL=gpt-5.6-terra
MATERIALS_MODEL=gpt-5.6-terra
REVIEWER_MODEL=gpt-5.6-luna
FRONTEND_ORIGIN=http://localhost:5173
```

Nunca se incluye una clave en código ni en el repositorio.

### Demo backend sin créditos

Para una demostración sin API ni acceso a modelos, activa explícitamente el modo fixture:

```dotenv
# backend/.env
CLARA_MOCK_MODE=true
```

Con ese flag, `/generate`, `/generate-materials`, `/audit` y `/review-edits` sirven datos deterministas de una clase de 6° básico sobre cambios de estado del agua y no crean un cliente de OpenAI. El stream conserva los eventos de los agentes y el beat de corrección del Reviewer para que se pueda recorrer la experiencia completa. No es el comportamiento predeterminado: con `false` o sin la variable, Clara usa los modelos configurados.

La interfaz también tiene una vista previa independiente: define `VITE_MOCK=true` en `frontend/.env` o abre la aplicación con `?mock`. Esto reproduce los eventos SSE en el navegador sin iniciar el backend.

## API y streaming

`POST /generate` recibe una solicitud de clase y devuelve SSE. Emite, entre otros:

`planner_started` → `planner_completed` → `designer_started` → `designer_completed` → `assessment_started` → `assessment_completed` → `reviewer_started` → `reviewer_correcting` (si aplica) → `reviewer_completed`.

Los eventos `agent_tool_completed` muestran consultas de currículo realizadas por Planner o Reviewer. Los errores de dominio se emiten como `failure`, sin stack trace para la docente.

También existen:

- `POST /generate-materials`: Materials → Reviewer, con streaming propio.
- `POST /audit`: importador conservador → Reviewer.
- `POST /review-edits`: revisión de la versión editada.
- `GET /coverage`: cobertura local por sesión, asignatura y nivel.

## MCP: verificación para otros agentes

El servidor MCP no reemplaza la API. Se monta en Streamable HTTP junto a FastAPI:

```text
http://localhost:8000/mcp
```

Expone tres herramientas:

- `auditar_material_educativo(material, asignatura?, nivel?)`
- `verificar_objetivo(codigo)`
- `buscar_objetivos(asignatura, nivel, tema?)`

`verificar_objetivo` responde explícitamente `existe: false` y una acción recomendada cuando un código no existe. Un agente generador puede entonces eliminar o corregir un OA antes de que una docente vea el material.

Ejemplo de configuración HTTP:

```json
{
  "mcpServers": {
    "clara-verifica": { "url": "http://localhost:8000/mcp" }
  }
}
```

Para clientes locales también hay transporte stdio:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.mcp_server
```

## Pruebas útiles

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests
```

La suite cubre, entre otros casos, el ciclo de corrección focalizada del Reviewer, la precisión de las auditorías importadas, herramientas curriculares, OA alucinados y cobertura longitudinal.

## How Codex built this

Codex implementó Clara por capas: primero contratos Pydantic y el Planner; luego Designer, Assessment y Reviewer; después la interfaz SSE, edición y auditorías. La regla central evolucionó de una instrucción de prompt a una garantía host-enforced: el Planner y Reviewer usan herramientas sobre un único proveedor curricular, y los OA deben verificarse dentro de la ejecución.

La separación de responsabilidades evita que los agentes se reescriban: Planner define estructura; Designer diseña la coreografía; Assessment construye el instrumento; Reviewer comprueba y corrige una vez cuando corresponde. Materials se deja bajo demanda para no gastar tokens en hojas que una docente puede descartar al regenerar el pack. Finalmente, cobertura local y MCP extienden esa misma verificación desde una clase a una secuencia de packs y a herramientas externas.
