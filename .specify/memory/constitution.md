# Constitución de Cripta II

Proyecto de Estructuras de Datos II, UNA, II ciclo 2026. Cripta II es un juego de exploración
por eventos en Python, con reloj virtual, que obtiene criptas de un servicio web o de un paquete
local (`--offline`). Esta es la segunda entrega y continúa el código funcional de la primera.

## Principios fundamentales

### I. Arquitectura MVC en n-capas, estricta

- El proyecto MUST seguir MVC con arquitectura en n-capas. No se admite ningún otro estilo de
  organización.
- Las capas son: Data (red y disco), Logic (reglas del juego y estructuras de datos), Service
  (casos de uso), UIController + View (interfaz) y DTO (transversal). Security (validación de
  acceso y de versión/integridad) acompaña a la interfaz y a los datos. Se mantienen los nombres
  de carpetas que ya existen en el repositorio.
- El flujo de llamadas es UIController -> Service -> Logic -> Data. Cada capa MUST llamar solo a
  la capa inmediatamente adyacente. La interfaz MUST NOT llamar a Data, y Data MUST NOT conocer
  reglas del juego.
- El paquete Estructuras es un paquete de apoyo sin dependencias hacia ninguna otra capa;
  cualquier capa puede importarlo.
- Logic (el modelo) MUST NOT conocer HTTP, archivos ni la interfaz concreta. El acceso a red y a
  disco se hace detrás de una interfaz común (FuenteDatos) para que `--offline` sustituya la
  fuente sin `if` dispersos.
- Los DTO son clases simples de datos, sin reglas de negocio, y son el único formato en que
  fluye información entre capas.
- Cada capa valida lo suyo: Data solo conexión y formato; Logic reglas de negocio; Service no
  valida; la interfaz valida la estructura de lo que el usuario ingresa.

### II. Lenguaje, bibliotecas y estructuras de datos

- El proyecto MUST escribirse únicamente en Python 3.11 o superior.
- Siguen vigentes todas las restricciones del enunciado de la primera parte (Primer Proyecto,
  §7) y se suman las de Cripta - Parte II (§6.2). La única excepción es cuando Cripta - Parte II
  mencione expresamente un cambio a alguna de ellas.
- Restricciones de la primera parte: las estructuras de datos de los problemas evaluados MUST
  implementarse a mano y MUST NOT sustituirse por equivalentes de bibliotecas; `dict` MUST NOT
  usarse como índice, caché, tabla de búsqueda o estructura propia (los `dict` que entrega
  `respuesta.json()` solo se leen); `list` MAY usarse solo como almacenamiento contiguo de bajo
  nivel; `list.sort()` y `sorted()` MUST NOT usarse en los ordenamientos evaluados (se usa el
  Ordenador del equipo).
- Restricciones que suma la segunda parte: MUST NOT usarse `heapq`, `bisect`, `collections`
  (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` ni ninguna biblioteca de grafos
  o de búsqueda de rutas; `set` queda prohibido en las mismas condiciones que `dict`.
- Bibliotecas permitidas: `requests` (con tiempo de espera explícito) y `pygame-ce`, que ya
  están establecidas en el proyecto; `json`, `struct`, `uuid` y `random.Random`; y las de la
  biblioteca estándar `os`, `pathlib`, `argparse`, `time`, `subprocess` y `unittest`, ya
  consultadas con el profesor para la primera entrega. Agregar cualquier otra dependencia MUST
  requerir acuerdo de los tres integrantes y quedar registrada en `requirements.txt` y
  `pyproject.toml`.
- Se MUST mantener las bibliotecas y las estructuras de datos que ya están implementadas en el
  proyecto. Antes de comenzar cualquier implementación, el grupo MUST revisar las limitaciones
  de cada estructura ya implementada contra lo que solicita Cripta - Parte II, y dejar el
  resultado de esa revisión en el `plan.md` correspondiente.
- spec-kit y el agente de programación son solo herramientas de proceso: MUST NOT introducir
  dependencias ni estructuras prohibidas. Las dependencias que proponga un plan generado se
  revisan antes de aceptarlo.

### III. Simplicidad: KISS, YAGNI, responsabilidad única y Abierto/Cerrado

- KISS: se MUST elegir la solución más simple que cumpla la especificación. El código lo deben
  poder leer y defender los tres integrantes, incluso los que son principiantes en Python.
- YAGNI: MUST NOT implementarse clases, capas, parámetros ni opciones que ningún requisito
  numerado pida.
- Responsabilidad única: cada clase y cada módulo hace una sola cosa; las funciones son cortas;
  los nombres son claros, con type hints y un docstring breve.
- Abierto/Cerrado: el código de la primera entrega que ya funciona está cerrado a modificación y
  abierto a extensión. Las capacidades nuevas MUST agregarse con clases o módulos nuevos, o
  extendiendo lo existente, sin reescribir implementaciones funcionales. Solo se modifica código
  existente cuando es indispensable para cumplir un requisito de la segunda parte o para
  corregir un defecto; en ese caso el cambio MUST justificarse en `plan.md` y, si cambia una
  decisión de la primera parte, mostrarse el antes y el después en `DECISIONES.md`.

### IV. Determinismo

- Misma cripta, misma semilla y mismas acciones MUST producir la misma partida.
- El tiempo real de red MUST NOT avanzar el reloj virtual. Las respuestas pendientes o
  concurrentes MUST incorporarse en un orden determinista.

### V. Modos sin interfaz

- `--replay` y `--bench` MUST ejecutarse sin instanciar la vista. Si el modelo necesita una
  ventana o el teclado para funcionar, la separación de capas está mal.

### VI. Sin datos de una cripta concreta en el código

- MUST NOT escribirse en el código números de salas, ids de entidades, páginas, presupuestos ni
  estadísticas de una cripta específica. El programa MUST funcionar con una cripta que el grupo
  no haya visto.

### VII. Red y presupuesto de solicitudes

- El programa MUST respetar `presupuesto_solicitudes`. Un reintento cuenta dentro del
  presupuesto.
- El `X-Cripta-Client-Id` MUST generarse una sola vez por ejecución y enviarse en todas las
  solicitudes.
- Un HTTP 429 o un error de red MUST manejarse con un mensaje con contexto, sin que el programa
  se caiga.

### VIII. Rendimiento con evidencia

- Toda afirmación de rendimiento MUST respaldarse con mediciones propias de `--bench`. Las
  mediciones de la primera parte se repiten con la carga nueva.
- Cada decisión de estructura de datos MUST documentarse en `DECISIONES.md` con: problema,
  alternativas consideradas, decisión, complejidad, evidencia empírica y límites conocidos,
  enlazando a la spec y al plan de donde proviene e indicando si la decisión final coincide con
  la del `plan.md` original.
- Las criptas sintéticas de `--bench` MUST ser deterministas por semilla.

### IX. Especificación antes del código

- Una especificación MUST confirmarse (commit) antes que cualquier código que la implemente. Si
  la especificación estaba mal, se corrige primero la especificación y luego el código, en
  commits separados.
- `spec.md` contiene reglas del juego, historias de usuario, escenarios de aceptación y
  requisitos numerados, y MUST NOT nombrar estructuras de datos, clases ni módulos. `plan.md`
  contiene las estructuras elegidas, alternativas, complejidad y mediciones previstas.
  `tasks.md` contiene tareas pequeñas y verificables, cada una con el requisito que atiende.
- Specs: `001-terreno-cazador`, `002-niebla-ir-a`, `003-resolubilidad` y `004-linea-tiempo`.
  Los requisitos usan el prefijo FR-1xx, FR-2xx, FR-3xx y FR-4xx respectivamente, para que los
  identificadores no choquen.

### X. Trazabilidad y pruebas

- Cada requisito tiene un identificador estable. Cada escenario de aceptación MUST tener al
  menos una prueba automatizada (con las herramientas que ya usa el repo: `unittest` y
  `tests/correr_pruebas.py`) o un `partida.log` de reproducción, y la prueba cita el
  identificador del requisito.

### XI. Bitácora de uso de LLM

- Cada prompt enviado a un LLM, incluidos los comandos de spec-kit con texto propio, MUST
  registrarse en `PROMPTS_LLM.md` con fecha, herramienta, prompt textual y para qué se usó la
  respuesta. No se incluyen credenciales ni datos personales.
- El código generado con ayuda de un LLM es responsabilidad del grupo, y cada integrante MUST
  poder explicarlo y modificarlo.

## Gobernanza

- Esta constitución solo se cambia con acuerdo de los tres integrantes, en un commit propio.
- Si un plan o una tarea contradice la constitución, el plan o la tarea se corrige.

**Versión**: 1.0.1 | **Ratificada**: 2026-11-08 | **Última enmienda**: 2026-11-08
