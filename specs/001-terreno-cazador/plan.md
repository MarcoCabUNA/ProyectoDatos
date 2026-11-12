# Plan de implementación: Terreno con costo por salida y enemigo cazador

**Rama**: `Marco` (spec-kit la reporta como `001-terreno-cazador`) | **Fecha**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación de `specs/001-terreno-cazador/spec.md` (FR-101 a FR-123, NFR-101 a NFR-103)

**Constitución**: v1.2.0 · **Responsable**: integrante 1

## Resumen

Cada salida tiene un costo (100 por defecto) que pagan todos los actores al moverse. Se agrega un
cuarto comportamiento, el cazador, que avanza un paso por la ruta más barata hacia el jugador si
su costo d no pasa su `rango`, con desempate por menor id.

Enfoque técnico ([research.md](research.md)):

- Una búsqueda de costo mínimo **desde el jugador**, **compartida** por todos los cazadores y
  **reanudable**, cortada en el `rango` de quien consulta.
- Un montículo binario propio en `Estructuras` como cola de prioridad.
- Invalidación precisa: la búsqueda se descarta solo si cambia la sala del jugador o una puerta
  que toca una sala ya resuelta (con distancia definitiva) en la búsqueda. El historial la descarta al deshacer.
- La búsqueda recibe el grafo como parámetro para que «ir a» (feature 002) la reutilice.

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior.

**Dependencias principales**: ninguna nueva. Solo las bibliotecas permitidas por el Principio II
(`dataclasses`, `typing`, `random.Random` para el bench, `time` para el cronómetro del bench,
`unittest` en las pruebas). Nada de `heapq`, `bisect`, `collections`, `copy` (fuera de `tests/`),
`networkx` ni bibliotecas de grafos. Nada de `dict` ni `set` como índice o caché. Nada de
`sorted()` ni `list.sort()` en ordenamientos evaluados (si hace falta ordenar, se usa `Ordenador`).

**Almacenamiento**: no aplica. La búsqueda guardada vive en memoria, no se guarda en la partida y
se reconstruye sola.

**Pruebas**: `unittest` en `tests/`, ejecutadas con `tests/correr_pruebas.py`. Cada prueba cita su FR.

**Plataforma**: escritorio (Windows, Linux) con `pygame-ce`. Los modos sin vista (`--bench`,
`--replay`, `--verificar`) no usan pygame.

**Tipo de proyecto**: juego de escritorio por eventos, MVC en n capas (Principio I).

**Metas de rendimiento**: ciclo de eventos < 20 ms con 30 cazadores en una cuadrícula sintética de
1 000 salas (NFR-101, SC-104). La decisión de un cazador con `rango` pequeño cuesta según la región
dentro del `rango` (NFR-102): al multiplicar por 10 el tamaño de la cripta, no tarda más del doble
(SC-105).

**Restricciones**: determinismo (Principio IV): la decisión del cazador no consume el azar
(FR-115). Abierto/Cerrado (Principio III): ver la tabla de cambios a código P1.

**Escala**: criptas publicadas de 6 a 50 salas, y cuadrículas sintéticas de hasta 10 000 salas en
el bench. Decenas de cazadores activos (pruebas del enunciado), hasta 100 en el bench.

## Verificación de la constitución

*Compuerta: antes de la fase 0, y otra vez después de la fase 1.*

| Principio | Cómo lo cumple este plan | Antes | Después |
|---|---|---|---|
| I. MVC en n capas | Búsqueda, cazador y caché en Lógica. Montículo en Estructuras (sin dependencias). Campos nuevos en DTO. Validación de FR-122 en Data (integrante 2, fuera de este plan). La vista recibe todo por DTO. Lógica no importa Data ni Servicios. | ✅ | ✅ |
| II. Bibliotecas y estructuras | Montículo propio y arrays como almacenamiento contiguo. Sin `heapq`, `dict`, `set` ni `copy`. Revisión de estructuras existentes: R0 de [research.md](research.md). | ✅ | ✅ |
| III. KISS, YAGNI, Abierto/Cerrado | Comportamiento nuevo como clase nueva. Cada cambio a P1 está en la tabla de abajo con su FR. El código nuevo lleva type hints y docstring. No hay refactor de P1. | ✅ | ✅ |
| IV. Determinismo | La búsqueda y el desempate no usan azar. `Errante.decidir_paso` repite la misma llamada a `randint`, así que la secuencia de azar de P1 no cambia. Sin `costo`, los replays de P1 dan la misma partida. | ✅ | ✅ |
| V. Modos sin vista | Todo lo nuevo está en Lógica y Estructuras. El bench corre sin vista. | ✅ | ✅ |
| VI. Sin datos de una cripta concreta | Las cargas del bench son sintéticas y deterministas por semilla. No hay ids ni costos fijos en el código. | ✅ | ✅ |
| VII. Red y presupuesto | Sin solicitudes nuevas: `costo` y `rango` llegan en las respuestas que ya se piden (Apéndice A). | ✅ | ✅ |
| VIII. Rendimiento con evidencia | Cada decisión (R1 a R6) tiene alternativas, complejidad y medición prevista. Las secciones §5.1, §5.2 y §5.6 de `DECISIONES.md` (raíz del repositorio) salen de aquí. | ✅ | ✅ |
| IX. Spec antes del código | Este plan no agrega reglas que no estén en `spec.md`. El hallazgo H-1 (abajo) ya se corrigió en la spec (FR-104). | ✅ | ✅ |
| X. Trazabilidad | Hay una prueba por escenario y una por caso del Apéndice B, y cada una cita su FR. | ✅ | ✅ |
| XI. Bitácora de LLM | Este prompt se registra en `PROMPTS_LLM.md`. | ✅ | ✅ |

**Resultado**: pasa. La única observación era H-1, resuelta en la spec antes de `/speckit.tasks`.

### Hallazgos para la spec

- **H-1 (Principio IX) — Resuelto**: la spec definía qué salida usan el cazador (FR-119) y el
  errante (FR-104) cuando dos salidas abiertas llevan a la misma vecina, pero **no el rastreador**,
  que escoge una sala (P1 §2.9), no una salida. Se resolvió en la spec, en su propio commit
  («spec(001): salida usada por el rastreador con destinos repetidos»): FR-104 y la pregunta 7 de
  «Clarificaciones» dicen que el rastreador, igual que el cazador, se mueve por la salida abierta **más barata** hacia la sala escogida y paga su costo; el
  errante sigue sorteando entre salidas. Las criptas publicadas no tienen salidas repetidas hacia
  la misma sala, así que hoy no cambia ninguna partida.
- **H-2 (Principio IX) — Resuelto**: `/speckit.analyze` encontró que el §4.1 del enunciado declara
  `costo` en un solo lado de la salida, igual que la llave, y la spec no decía qué pasaba entonces.
  Se resolvió en la spec, en su propio commit («spec(001): costo en ambos lados de la salida y
  criterios medibles»): si solo un lado declara costo, vale para
  los dos; si ninguno, 100; si los dos declaran valores distintos, es error de datos (FR-101,
  FR-122, escenario H1-8). En el plan: `SalidaDTO.costo` guarda lo declarado (`int | None`) y
  Lógica iguala los dos lados junto a `_igualar_caras`.

## Contrato de datos

**Confirmado con el integrante 2 el 11 de noviembre, tal como está.** Detalle en
[contracts/contrato-datos.md](contracts/contrato-datos.md).

| DTO | Campo | Propuesta | Dueño |
|---|---|---|---|
| `SalidaDTO` | `costo` | `int \| None = None`, el costo **declarado** en ese lado | Integrante 2 |
| `FichaEnemigoDTO` | `rango` | `int \| None = None`; a un cazador no se le inventa valor | Integrante 1 |
| `ActorDTO` | `comportamiento` | `str \| None = None`, para que la vista distinga cazadores | Por acordar con el integrante 3 |
| (`Service/ArmadorEstado.py`) | — | Copiar también `costo` (el igualado) al armar la sala para la vista | Por acordar con el integrante 3 |

La validación de FR-122 (costo entero ≥ 1, los dos lados de una salida sin costos distintos,
`rango` entero ≥ 0 en cazadores) va en **Data** y es
del integrante 2. **Este plan no incluye código de Data.** Lógica no repite la validación.

`rango` tiene que llevar valor por defecto en Python: es un `dataclass` inmutable cuyos campos
finales ya tienen valor por defecto, y los enemigos que no son cazadores no lo traen. «Sin valor
por defecto» (FR-122) se cumple en Data, que rechaza un cazador sin `rango` válido.

## Revisión de estructuras existentes (Principio II)

Detalle en [research.md, R0](research.md#r0-revisión-de-las-estructuras-existentes-principio-ii).
Resumen:

- **`Logic/ColaEventos.py`**: montículo atado a eventos y al historial. No sirve como cola de la
  búsqueda sin modificarlo, así que no se toca y se vuelve a medir (§5.6).
- **`Logic/Comportamientos.py`**: `decidir()` devuelve una sala, no una salida, así que no sabe qué
  costo pagar. Se **extiende** con `decidir_paso()`.
- **`Logic/Mazmorra.py`**: `salidas_abiertas()` no da costo y nadie se entera de los cambios de
  puerta. El costo puede venir en un solo lado, como la llave. Se agregan `SalidaViva.costo`,
  `_igualar_costos()` junto a `_igualar_caras()`, métodos con costo y un aviso de puerta.
- **`Logic/motorJuego.py`**: el movimiento cuesta 100 fijo, y se cambia en los dos puntos de
  movimiento. `cambiar_velocidad()` ya cumple FR-105.
- **`Estructuras/Cola.py`, `Ordenador`, `ListaDoble`, `BufferCircular`**: ninguna da extracción del
  mínimo. Se agrega `MonticuloMinimo`.

## Cambios a código de la primera entrega (Principio III, Abierto/Cerrado)

Todo lo demás es código nuevo. Si un cambio modifica una decisión de P1, se documenta el antes y
el después en `DECISIONES.md`.

| Archivo | Cambio | Tipo | Requisito | Por qué no basta con extender |
|---|---|---|---|---|
| `Logic/Mazmorra.py` · `SalidaViva.__init__` | Guardar `self.costo_declarado = salida_dto.costo` y `self.costo` (el declarado, o 100) | Modificación (2 líneas) | FR-101 | La salida viva es la única que conoce Lógica, y el costo tiene que estar en ella. |
| `Logic/Mazmorra.py` · `cargar_esqueleto()` | Llamar a `self._igualar_costos()` justo después de `self._igualar_caras()`. `_igualar_costos` es un método nuevo. | Modificación (1 línea) + extensión | FR-101 | Es el único punto donde están las dos caras de cada salida. `_igualar_caras` no se toca. |
| `Logic/Mazmorra.py` · `Mazmorra` | `salidas_abiertas_con_costo()`, `costo_paso()`, atributo `observador_puertas = None` | Extensión | FR-102, FR-104, FR-119 | Métodos nuevos. Los existentes no cambian. |
| `Logic/Mazmorra.py` · `abrir_puerta()` y `CierrePuerta.activar()` | Al final, si `observador_puertas` no es `None`, avisarle `puerta_cambio(a, b)` | Modificación (2 líneas cada uno) | FR-114 | Son los dos únicos puntos donde cambia una puerta. Sin aviso, la búsqueda guardada podría quedar desactualizada. |
| `Logic/Comportamientos.py` · `Comportamiento` | Método `decidir_paso()` por defecto (usa `decidir()` y `costo_paso()`) | Extensión | FR-102, FR-104 | `Guardian` y `Rastreador` lo heredan sin cambios. |
| `Logic/Comportamientos.py` · `Errante` | Método nuevo `decidir_paso()` con el mismo sorteo sobre salidas con costo. `decidir()` no cambia. | Extensión | FR-104 | Con solo un destino no se sabe qué salida se sorteó si hay dos hacia la misma sala. |
| `Logic/Comportamientos.py` · `COMPORTAMIENTOS` | Agregar `Cazador` | Modificación (1 línea) | FR-106 | La fábrica solo conoce lo que está en la lista. |
| `Logic/Comportamientos.py` · `Cazador` | Clase nueva. En la historia 2 decide con `paso_desde_cero`; en la historia 3 pasa a `motor.rutas.decidir` (una línea de código nuevo, no de P1). | Extensión | FR-106 a FR-115 | — |
| `Logic/motorJuego.py` · `__init__` | Crear `self.grafo` (historia 2), `self.rutas` y asignar `mazmorra.observador_puertas` (historia 3) | Modificación (3 líneas) | FR-112, FR-114 | Es el dueño del historial y de la mazmorra. |
| `Logic/motorJuego.py` · `mover_jugador()` | `terminar_accion_jugador(salida.costo)` en lugar de `COSTO_MOVER` | Modificación (1 línea) | FR-102 | La regla de costo cambió. |
| `Logic/motorJuego.py` · `turno_enemigo()` | Usar `decidir_paso()` y programar con su costo (100 si espera o ataca) | Modificación (unas 5 líneas) | FR-102, FR-103, FR-110, FR-121 | Hoy programa 100 fijo después de moverse. |
| `Logic/Enemigo.py` | Redefinir `a_dto()` para incluir `comportamiento` (si se confirma con el integrante 3) | Extensión | FR-117 | — |
| `Logic/BenchLogica.py` · `medir()` | Agregar `BenchRutas.medir()` a lo que devuelve | Modificación (1 línea) | NFR-103 | `ServicioBench` (del integrante 2) ya llama a `BenchLogica.medir`. Así no se edita su archivo. |
| `DTO/FichaEnemigoDTO.py` | Campo `rango`, `"rango"` en `_CAMPOS`, lectura y escritura | Extensión del DTO | FR-106 | Contrato de datos. Es del integrante 1. |
| `DTO/SalaDTO.py` · `SalidaDTO` | Campo `costo` (declarado) | Extensión del DTO | FR-101 | Contrato de datos. **Lo hace el integrante 2.** |
| `Service/ArmadorEstado.py` · `_sala_con_estado_actual` | Copiar `costo=viva.salidas[d].costo` junto a `cerrada` | Modificación (1 palabra) | FR-101, FR-116 | La vista debe ver el costo igualado, no el declarado. **Por acordar con el integrante 3.** |
| `DTO/ActorDTO.py` | Campo `comportamiento` | Extensión del DTO | FR-117 | **Por acordar con el integrante 3.** |

No se tocan: `ColaEventos`, `HistorialRetroceso`, `cambiar_velocidad`, `Rastreador.decidir`,
`Errante.decidir`, `Mazmorra._igualar_caras`, la capa Data ni la Vista.

## Decisiones de diseño (resumen de [research.md](research.md))

| # | Decisión | Elegida | Alternativas medidas | Complejidad |
|---|---|---|---|---|
| R1 | Cola de prioridad | Montículo binario mínimo propio con borrado perezoso (`Estructuras/MonticuloMinimo.py`) | Recorrer un array (O(S²)); generalizar `ColaEventos`; índice de posiciones; cubetas | O((S_r + E_r) log E_r) por búsqueda |
| R2 | Por cazador o compartido | Compartido, desde el jugador (el costo es simétrico), reanudable | Una búsqueda por cazador desde el jugador; una desde el cazador (descartada) | Una búsqueda por invalidación, más O(g) por decisión |
| R3 | Corte en el `rango` | Se extiende hasta resolver la sala del cazador o hasta que la frontera pase su `rango`. Arrays con generación para no reiniciar en O(S). | Búsqueda completa | Proporcional a la región dentro del `rango` |
| R4 | Invalidación | Cambio de sala del jugador; puerta que toca una sala resuelta; pergamino (reversión registrada en el historial) | Recalcular siempre; descartar ante cualquier puerta | Comprobación O(1) por aviso |
| R5 | «Ir a» | Misma búsqueda y mismo desempate, con el grafo como parámetro ([contrato](contracts/busqueda-rutas.md)) | Dos búsquedas separadas | — |
| R6 | §5.6 | Repetir la agenda y el ciclo con cazadores y costos variables | — | — |

Por qué el desempate es correcto con una búsqueda cortada: toda vecina que cumple la igualdad
tiene distancia < d y ya está resuelta. Ver R3.

## Mediciones planificadas para `--bench` (§6.3, NFR-103)

Todo vive en `Logic/BenchRutas.py` (Lógica, con el mismo cronómetro de `BenchLogica`). Las
cuadrículas son sintéticas, con costos por salida sacados de `random.Random(SEMILLA)` entre 1 y
300. Mismo formato `ResultadoBenchDTO`.

| Subsistema | Caso | Tamaños | Qué se compara | Requisito |
|---|---|---|---|---|
| rutas del cazador | cola de prioridad | 100, 1 000, 10 000 salas | Montículo frente a recorrer un array (R1) | NFR-102 |
| rutas del cazador | un cazador frente a muchos | 1, 10, 30, 100 cazadores | Búsqueda individual por cazador frente a compartida (R2) | NFR-101 |
| rutas del cazador | `rango` pequeño frente a grande | `rango` 200, 600, 5 000 × 100, 1 000, 10 000 salas | Tiempo por decisión. Con `rango` 200, cada multiplicación por 10 del tamaño tarda como mucho el doble (SC-105). | NFR-102, SC-105 |
| invalidación de rutas | puertas estables | 30 cazadores, 1 000 salas | Recalcular siempre / descartar ante cualquier puerta / descarte preciso (R4). Se cuentan las búsquedas reales por ciclo. | NFR-101 |
| invalidación de rutas | puertas inestables | Ídem, con cierres automáticos frecuentes cerca y lejos del jugador | Ídem | NFR-101 |
| ciclo de eventos | con cazadores | Cuadrícula de 1 000 salas con **30** cazadores (y 10 y 100 como comparación), más errantes y rastreadores, costos variables | Peor ciclo frente al límite de 20 ms; la nota dice si cumple | NFR-101, SC-104 |
| agenda de eventos (§5.6) | repetición con la carga nueva | `medir_agenda_con_costos`: tiempos generados con costos entre 1 y 300 y velocidades distintas | Montículo frente a array ordenado, otra vez (Principio VIII) | §5.6 |
| agenda de eventos (§5.6) | muchos eventos con el mismo tiempo | `medir_agenda_con_costos`: 100, 1 000, 10 000 eventos en un solo tiempo y en 10 tiempos | Montículo frente a array ordenado cuando el orden lo decide el desempate por secuencia (límite conocido del montículo con invalidación perezosa) | §5.6 |
| agenda de eventos (§5.6) | muchas cancelaciones | `medir_agenda_con_costos`: 100, 1 000, 10 000 eventos con el 50 % y el 90 % cancelados | Montículo frente a array ordenado; la nota dice cuántas entradas canceladas se descartaron y el tamaño del arreglo antes y después (límite conocido de la invalidación perezosa) | §5.6 |
| historial (§5.6) | registros por intervalo | 30 cazadores | Registros por intervalo con y sin la búsqueda guardada | §5.6 |

## Pruebas planificadas (Principio X)

| Archivo (nuevo) | Cubre |
|---|---|
| `tests/ayudas_terreno.py` | Ayudantes: criptas con costos (en uno o en los dos lados), fichas, motor y una fuente de datos de prueba con un cazador. |
| `tests/test_mazmorra_costos.py` | Costo en `SalidaViva`, igualación de los dos lados, `salidas_abiertas_con_costo` y `costo_paso` (FR-101, FR-104, FR-119). |
| `tests/test_monticulo_minimo.py` | El montículo: orden, desempate por valor, entradas repetidas, `vaciar`. |
| `tests/test_busqueda_costo_minimo.py` | Búsqueda reanudable, corte en el límite, generación, salidas sin vuelta, salidas repetidas (FR-108, FR-111, FR-119). |
| `tests/test_terreno_cazador.py` | Escenarios H1-1 a H1-8, H2-1 a H2-8 y H3-6, y los casos 1, 2, 3, 4, 6 y 7 del Apéndice B. Bordes del cazador, incluido el cierre automático en el mismo instante (FR-108). |
| `tests/test_rutas_equivalencia.py` | Escenarios H3-1 a H3-5 (H3-1 es el **caso 5** del Apéndice B). FR-114 / SC-102: partidas sintéticas con semilla (puertas, movimientos, muertes, pergaminos), comparando cada decisión con `paso_desde_cero`. Historial. |
| `tests/test_dto_terreno.py` | `FichaEnemigoDTO.rango` (ida y vuelta, `_CAMPOS`, ausencia). Datos para la vista de H4-1 y H4-2 (costo igualado y `comportamiento`). |
| `tests/test_modos_sin_vista_terreno.py` | FR-118: `--replay`, `--replay … --hasta` y `--verificar` con una cripta de prueba con costos y un cazador, sin vista. |
| `tests/test_bench_rutas.py` | Las mediciones nuevas con tamaños chicos, sin vista. |
| Pruebas de la vista (integrante 3) | H4-1 y H4-2 en pantalla (FR-116, FR-117, SC-106). Se coordinan en la tarea T041. |

## Estructura del proyecto

### Documentación (esta feature)

```text
specs/001-terreno-cazador/
├── spec.md
├── plan.md              # este archivo
├── research.md          # fase 0
├── data-model.md        # fase 1
├── quickstart.md        # fase 1
├── contracts/
│   ├── contrato-datos.md     # DTO (confirmado con integrante 2 el 11 nov)
│   └── busqueda-rutas.md     # búsqueda compartida con «ir a»
├── checklists/requirements.md
└── tasks.md             # fase 2 (/speckit.tasks)
```

### Código fuente (raíz del repositorio)

```text
DTO/
├── FichaEnemigoDTO.py        # + rango                     (integrante 1)
├── SalaDTO.py                # + SalidaDTO.costo           (integrante 2, fuera de este plan)
└── ActorDTO.py               # + comportamiento            (por acordar con el integrante 3)
Estructuras/
└── MonticuloMinimo.py        # NUEVO: cola de prioridad propia
Logic/
├── BusquedaCostoMinimo.py    # NUEVO: búsqueda reanudable + paso_desde_cero
├── GrafoEsqueleto.py         # NUEVO: grafo sobre la Mazmorra (puertas en vivo)
├── RutasHaciaJugador.py      # NUEVO: búsqueda compartida, invalidación, historial
├── BenchRutas.py             # NUEVO: mediciones §6.3
├── Comportamientos.py        # + decidir_paso, + Cazador
├── Mazmorra.py               # + costo, _igualar_costos, métodos con costo, aviso de puertas
├── motorJuego.py             # costo de movimiento, self.rutas
├── Enemigo.py                # + a_dto con comportamiento
└── BenchLogica.py            # medir() incluye BenchRutas
Service/
└── ArmadorEstado.py          # + copiar el costo igualado   (por acordar con el integrante 3)
tests/
├── ayudas_terreno.py
├── test_mazmorra_costos.py
├── test_monticulo_minimo.py
├── test_busqueda_costo_minimo.py
├── test_terreno_cazador.py
├── test_rutas_equivalencia.py
├── test_dto_terreno.py
├── test_modos_sin_vista_terreno.py
└── test_bench_rutas.py
DECISIONES.md                 # NUEVO en la raíz: §5.1, §5.2 y §5.6 (Principio VIII)
```

**Decisión de estructura**: se usan las carpetas de capas que ya existen (Principio I). No se crea
ninguna carpeta nueva.

## Dependencias con otros integrantes

| Qué | De | Para | Bloquea |
|---|---|---|---|
| `SalidaDTO.costo` (declarado) | Integrante 2 | Integrante 1 | Todo desde la fase 2 de `tasks.md` (T001). |
| La validación de FR-122 en Data, incluidos los dos lados con costos distintos | Integrante 2 | Integrante 1 | Las pruebas de FR-122 (T002, T050). No bloquea a Lógica. |
| `FichaEnemigoDTO.rango` | Integrante 1 | Integrante 2 | La validación de Data. |
| `ActorDTO.comportamiento` y su uso en la vista | Integrante 3 | — | FR-116 y FR-117 (la interfaz es del integrante 3, §7.3). |
| `ArmadorEstado` copia el costo igualado, y pruebas de la vista para H4 | Integrante 3 | — | FR-116, SC-106 y el Principio X para H4-1 y H4-2 (T038, T041). |
| El grafo del mapa conocido | Integrante 2 | Integrante 3 («ir a») | Nada de esta feature. |

## Seguimiento de complejidad

Sin violaciones de la constitución que justificar. Los cambios a código P1 están en su tabla, con
su requisito.
