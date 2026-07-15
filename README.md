# Clara

Clara is a multi-agent teaching copilot for teachers in Latin America, starting with the Chilean national curriculum. A teacher describes a class in plain language and Clara will produce an editable, coherent teaching pack: a lesson plan, activity guide, and assessment with rubric.

## Agent architecture

All agents are designed to use GPT-5.6 through the configurable `gpt-5.6-terra` model ID. They will share a stable, cached system-context prefix containing common pedagogy instructions and verified curriculum context.

1. **Planner** maps a lesson request to curriculum objectives and a structured plan.
2. **Designer** creates activities from that plan.
3. **Assessment** creates an aligned assessment and rubric.
4. **Reviewer** checks the three artifacts for consistency before returning them.

The current `/generate` endpoint returns typed placeholder data. Agent classes and the OpenAI client seam are scaffolded and intentionally marked `TODO` for the next feature iteration.

## Run locally

Prerequisites: Python 3.11+ and Node.js 20+.

```powershell
# Terminal 1 — API
cd backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```powershell
# Terminal 2 — web app
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open the URL Vite prints (normally `http://localhost:5173`). The API is available at `http://localhost:8000`; interactive API docs are at `/docs`.

`POST /generate` returns an SSE-formatted stream so the web app can show the
Planner and Designer as they complete. It emits `planner_started`,
`planner_completed`, `designer_started`, `designer_completed`, or `failure`.
The browser uses `fetch` to consume the stream because the request contains the
lesson JSON; native `EventSource` only supports GET requests.

### Test the Planner with the bundled curriculum sample

After configuring `OPENAI_API_KEY` in `backend/.env`, run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python examples/run_planner.py
```

The example requests a 6° básico Ciencias Naturales lesson on changes of state
of water. It should only cite OA codes in `app/curriculum/sample_objectives.json`.

To run the Planner followed by the Designer and print its timing checks:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python examples/run_pipeline.py
```

## Environment variables

`backend/.env` (not committed):

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.6-terra
# Optional per-agent overrides; unset values fall back to OPENAI_MODEL.
PLANNER_MODEL=gpt-5.6-terra
DESIGNER_MODEL=gpt-5.6-terra
ASSESSMENT_MODEL=gpt-5.6-terra
REVIEWER_MODEL=gpt-5.6-luna
FRONTEND_ORIGIN=http://localhost:5173
```

`frontend/.env` (optional):

```dotenv
VITE_API_BASE_URL=http://localhost:8000
VITE_MOCK=false
```

### Vista previa sin API

Para recorrer la interfaz sin consumir créditos ni iniciar el backend, agrega
`VITE_MOCK=true` a `frontend/.env` o abre la app con `?mock`. Clara reproducirá
un pack de 6° básico sobre cambios de estado del agua, incluyendo el ciclo del
Reviewer que devuelve una corrección al Evaluador. El selector de velocidad de
la pantalla inicial permite alternar entre lenta, normal y rápida.

## MCP: Clara como capa de verificación

Clara expone su auditoría curricular como un servidor MCP adicional: no genera material; verifica afirmaciones curriculares y coherencia antes de que otro agente entregue el resultado a una docente.

- `auditar_material_educativo(material, asignatura?, nivel?)`: reutiliza el importador y Reviewer de Clara y devuelve un `AuditReport` estructurado con confianza de lectura, notas de interpretación y hallazgos accionables.
- `verificar_objetivo(codigo)`: consulta la fuente curricular. Si devuelve `existe: false`, el código no debe citarse como OA oficial; Clara indica eliminarlo o reemplazarlo.
- `buscar_objetivos(asignatura, nivel, tema?)`: devuelve los OA oficiales disponibles para esa cobertura curricular.

### Conectar por HTTP

Al ejecutar la API de Clara, el MCP Streamable HTTP queda disponible en `http://localhost:8000/mcp`. Comparte la aplicación FastAPI con la API existente, sin reemplazarla.

```json
{
  "mcpServers": {
    "clara-verifica": { "url": "http://localhost:8000/mcp" }
  }
}
```

Para la demo, el MCP Inspector puede conectarse a esa URL. En un despliegue público, protege el endpoint con la capa de autorización propia del entorno antes de compartirlo.

### Conectar por stdio

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.mcp_server
```

Ejemplo de configuración local en Windows:

```json
{
  "mcpServers": {
    "clara-verifica": {
      "command": "C:\\ruta\\a\\Clara\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "app.mcp_server"],
      "cwd": "C:\\ruta\\a\\Clara\\backend"
    }
  }
}
```

### Ejemplo: generar y verificar antes de entregar

1. Un agente genera una propuesta para Ciencias Naturales de 6° básico.
2. Consulta `buscar_objetivos("Ciencias Naturales", "6° básico", "cambios de estado")` para escoger OA disponibles.
3. Envía el borrador completo a `auditar_material_educativo`.
4. Si recibe un hallazgo `bloqueante` para `CN06 OA 999`, elimina o reemplaza ese código. Si recibe una observación de ausencia, la trata como evidencia que Clara no pudo encontrar en el material leído, no como una acusación.

## How Codex built this

El primer agente implementado es el **Planner**. Usa la Responses API con salida
estructurada validada por Pydantic y reintenta una vez ante una salida inválida o
un error transitorio. Después valida cada OA contra un proveedor de currículum
inyectable: el ejemplo local contiene una pequeña muestra oficial de Ciencias
Naturales y Matemática; un OA no incluido nunca se acepta. Las instrucciones
compartidas y la referencia curricular se colocan antes de la solicitud variable
para favorecer prompt caching. Cada agente admite su propio modelo mediante
variables de entorno: Terra para la planificación y generación principal, y Luna
por defecto para la revisión de consistencia de menor costo.

El **Designer** consume el LessonPlan validado y solicita una salida estructurada
con GPT-5.6 Terra (configurable mediante `DESIGNER_MODEL`). Verifica que cada
actividad use una etapa existente, que cada etapa tenga al menos una actividad,
que no excedan el presupuesto de tiempo y que se limiten a objetivos ya presentes
en el plan. Esta separación evita que los agentes se reescriban entre sí: el
**Planner** define el arco pedagógico, objetivos y presupuestos de tiempo, mientras
el **Designer** crea la coreografía de aula (pasos, agrupamiento, productos y
diferenciación). El resumen de materiales se deriva determinísticamente de las
actividades para evitar inconsistencias.

El **Assessment** crea el instrumento final, sus respuestas esperadas y una rúbrica
observable. Valida cobertura total de objetivos, puntajes y correspondencia entre
ítems y rúbrica; la tabla de especificaciones agregada se deriva de los ítems.
En selección múltiple, la alternativa correcta vive en un campo estructurado
(`correct_option_label`) separado del criterio explicativo; los reintentos reciben
el error específico de validación para corregirlo.

La corrección del Reviewer tiene una prueba determinística sin llamadas al modelo:

```powershell
cd backend
python -m unittest tests.test_review_correction
```
