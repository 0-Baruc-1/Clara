# Clara

Clara es un copiloto de enseñanza para docentes de Chile. Su diferencia no es solo generar material: verifica las afirmaciones curriculares contra una fuente de Objetivos de Aprendizaje (OA), revisa la coherencia entre los artefactos y declara con honestidad lo que no pudo comprobar.

Una docente puede generar un pack, editarlo, pedir una nueva revisión, crear hojas imprimibles bajo demanda, auditar material creado fuera de Clara y observar cobertura curricular acumulada en su sesión local.

La sección de estudiantes convierte material **publicado y atestado por la docente** en práctica. No diagnostica dominio: conserva respuestas ligadas a los ítems y OA que la docente aprobó para que ella interprete la evidencia.

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

## Procedencia del catálogo curricular

El PDF oficial de MINEDUC se mantiene fuera de Git en `backend/data/source/` por su tamaño. Para volver a ejecutar la extracción, colócalo como `backend/data/source/bases-curriculares-1-a-6-basico.pdf` y ejecuta:

```powershell
python backend/scripts/extract_mineduc_bases.py
```

El proceso no adivina prefijos de código. Su evidencia versionada queda en [mineduc_extraction_report.json](backend/app/curriculum/mineduc_extraction_report.json). El PDF conserva asignatura, nivel, número y páginas, pero no declara los códigos completos. Para completar una cobertura, consulta cada ficha oficial, con caché local y límite de ritmo:

```powershell
python backend/scripts/complete_mineduc_codes.py
```

La pasada inicial verificó Ciencias Naturales y Matemática de 6° básico: el [catálogo activo](backend/app/curriculum/mineduc_objectives.json) contiene 42 OA, cada uno con su URL oficial individual como fuente. El informe conserva ambos textos y marca cualquier diferencia entre PDF y web para revisión manual; una ficha inexistente o una redacción no identificable nunca genera código. Las demás asignaturas y niveles siguen fuera de cobertura hasta completar el mismo proceso.

## Flujos adicionales

- **Auditar material existente**: importa planificación o evaluación en prosa, la interpreta de forma conservadora y utiliza el mismo Reviewer. Las conclusiones que dependen de una ausencia se muestran solo con suficiente confianza de lectura; un OA inexistente sigue siendo un hallazgo bloqueante porque es verificable por presencia.
- **Revisar mis cambios**: después de editar el pack en el navegador, la docente puede solicitar una auditoría de esa versión. Mantiene el mismo criterio de precisión que el material importado.
- **Cobertura curricular**: SQLite local registra solo asignatura, nivel, OA declarado, estado de verificación y evidencia de actividad. Un OA cuenta como cubierto únicamente si fue verificado y las actividades lo trabajaron. La vista declara de forma visible que solo representa los packs que Clara ha visto, no toda la planificación anual.
- **Sección de estudiantes**: una docente publica explícitamente un snapshot inmutable y atestigua los OA verificados de sus ítems. La evidencia muestra conteos como “Sofía respondió 1 de 3 ítems que etiquetaste CN06 OA 15”; no hay porcentajes de dominio, barras de progreso ni afirmaciones de maestría. Menos de tres ítems distintos respondidos por estudiante/OA queda gris como “evidencia insuficiente” (umbral configurable por curso). Los ítems sin OA verificable pueden publicarse solo como práctica y nunca generan evidencia curricular.
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

### Sección de estudiantes con Supabase

Aplica, en orden, [202607180001_student_evidence.sql](backend/supabase/migrations/202607180001_student_evidence.sql), [202607180002_student_material_list_and_roles.sql](backend/supabase/migrations/202607180002_student_material_list_and_roles.sql) y [202607180003_profiles_for_student_evidence.sql](backend/supabase/migrations/202607180003_profiles_for_student_evidence.sql) en tu proyecto Supabase y agrega estas variables solo al entorno del backend:

```dotenv
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_SERVICE_ROLE_KEY=solo_backend_nunca_frontend
```

La migración espera que el alta institucional asigne `teacher` o `student` en `public.clara_user_roles`; una cuenta sin ese rol no puede publicar como docente. La segunda migración permite que una persona autenticada lea **solo su propia** fila de rol para que la interfaz muestre la experiencia correcta. No usa roles como claims del JWT.

La migración aplica RLS y crea un camino RPC para el estudiante que recalcula el hash de la versión y de cada ítem antes de entregarlo. Una versión publicada, sus ítems y sus atestaciones no se pueden actualizar ni eliminar en la base de datos; detener una actividad se hace desde una entidad de disponibilidad separada. Una receta SymPy se valida una sola vez al publicar mediante `parse_expr(..., evaluate=False)`, un allow-list de operaciones y límites de complejidad. Nunca se ejecuta `sympify`, `eval` ni texto LLM en el momento de responder.

**Estado de verificación de la migración:** los triggers de inmutabilidad y la recomputación de hashes están definidos y revisados en la migración, pero aún no se han ejecutado contra un proyecto Supabase real (`supabase start` + intentos reales de `UPDATE`/`DELETE`). No se presentan como pruebas ejecutadas hasta completar esa comprobación de integración.

El API nuevo requiere un JWT Supabase real en `Authorization: Bearer …`:

- `POST /student-materials/publish`: crea el snapshot, registra la atestación docente y publica los ítems.
- `GET /student-materials`: lista solo releases activos de clases donde la estudiante tiene una matrícula activa; RLS decide el acceso, no un `class_id` entregado por el navegador.
- `GET /student-materials/{release_id}`: devuelve solo material de la estudiante autenticada tras verificar integridad.
- `POST /student-items/{item_id}/responses`: entrega feedback únicamente para una receta determinista ya congelada; las respuestas de juicio quedan en cola docente.
- `GET /classes/{class_id}/student-evidence`: devuelve conteos de evidencia, nunca mastery/maestría.

La regla de lenguaje es parte del contrato: ninguna vista o endpoint puede convertir “respuestas a ítems que la docente etiquetó OA X” en “evidencia de dominio de OA X”. La etiqueta es una atestación de la docente y el salto hacia una inferencia pedagógica sigue siendo su juicio profesional.

### Runbook de la sección de estudiantes

En `frontend/.env`, configura las variables públicas del cliente Supabase y el único curso de la demostración:

```dotenv
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu_anon_key_publica
VITE_DEMO_CLASS_ID=uuid-del-curso-demo
```

El frontend usa `@supabase/supabase-js` para iniciar sesión y persistir una sesión real; cada petición de estudiantes al backend incluye el JWT vigente en `Authorization: Bearer …`. El rol se lee desde `clara_user_roles` con la política RLS anterior. La clave `service_role` nunca se entrega al navegador.

Al ejecutar la demo, verifica exactamente lo siguiente:

1. Aplicaste ambas migraciones y existen una fila de `clara_user_roles` para cada cuenta demo y el `VITE_DEMO_CLASS_ID` correcto.
2. Existe una fila **activa** de `class_enrollments` que vincula a la estudiante demo con ese curso. Sin ella, `GET /student-materials` devolverá una lista vacía por diseño y en cámara parecerá que no hay material.
3. Inicia sesión como docente, publica un pack y confirma que la respuesta incluye `release_id`; la publicación debe aparecer en la lista de la estudiante matriculada.
4. Inicia sesión como estudiante, responde un ítem determinista y confirma el feedback inmediato. En un ítem `teacher_judgment`, confirma que solo aparece “Respuesta enviada. Tu profesora la revisará.”
5. Vuelve a iniciar sesión como docente y comprueba que la tabla separa `Declarado`, `Atestado` y `Evidencia de respuestas`, manteniendo gris “evidencia insuficiente” bajo el umbral.
6. Aplica también [202607180003_profiles_for_student_evidence.sql](backend/supabase/migrations/202607180003_profiles_for_student_evidence.sql) y siembra una fila `profiles` por cada cuenta demo (docente y estudiantes), con `user_id` igual al UUID de `auth.users` y `full_name` definido. La cobertura mostrará ese nombre real para estudiantes matriculados. Si falta una fila de perfil, no falla la evidencia: por diseño se muestra `Estudiante · <id corto>` como respaldo.

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
