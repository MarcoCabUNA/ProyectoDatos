# Plan de implementación: Línea de tiempo de la partida

**Rama**: `kris` (spec-kit la reporta como `004-linea-tiempo`) | **Fecha**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación de `specs/004-linea-tiempo/spec.md` (FR-401 a FR-416, FR-418 a FR-423 y NFR-401 a NFR-403; FR-417 se integró en NFR-402)

**Constitución**: v1.2.0

## Resumen

La línea de tiempo permite ver el estado de la partida en cualquier instante pasado sin tocarla. Se
**reconstruye hacia adelante**: se parte del punto de control más cercano anterior al instante pedido,
se arma un `Motor` aparte con `PartidaGuardada` y se re-simulan las acciones vigentes del jugador
(a lo sumo K). Lo que la línea guarda es:

- las **acciones vigentes** del jugador con el tiempo de cada decisión (las revertidas por un
  pergamino desaparecen);
- **marcadores** de «se descontó un pergamino» (el pergamino queda fuera del historial);
- **puntos de control**: una copia completa del estado, hecha a mano, cada K acciones;
- los **registros de carga de sala** y las **fichas** que la partida ya pidió, para reconstruir sin
  consultar a Data;
- el valor de K.

Enfoque técnico ([research.md](research.md)):

- Reconstrucción en `Service/` con un despacho de acciones propio: sin `partida.log`, sin tocar la
  caché del catálogo viva, sin solicitudes (R1, R2).
- Método nuevo `Motor.avanzar_hasta(t)`, sin tocar `avanzar_hasta_jugador` (R6).
- Búsqueda binaria propia en `Estructuras/` para ubicar el punto de control (R5).
- Archivo de partida versión 2 con un bloque propio para la línea (R7).
- Valor de K por defecto **provisional**, a confirmar con `--bench` (R8).

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior.

**Dependencias principales**: ninguna nueva. Solo las permitidas por el Principio II (`dataclasses`,
`typing`, `struct`, `random.Random`, `time` para el bench, `argparse`, `unittest`). Nada de `copy`,
`bisect`, `heapq`, `collections`, `dict` ni `set` como índice, ni `sorted()`/`list.sort()`. Las
copias de estado son manuales. **`tracemalloc` no está permitido**: la memoria se mide con el tamaño
del archivo serializado y con un conteo de elementos guardados (M3).

**Almacenamiento**: la línea viaja dentro del archivo de partida (bloque propio, versión 2). En
memoria son cuatro arreglos (acciones, marcadores, puntos de control, registros de carga) más las
fichas vistas.

**Pruebas**: `unittest` en `tests/`, con `tests/correr_pruebas.py`. Cada prueba cita su FR.

**Plataforma**: escritorio con `pygame-ce`. `--replay … --hasta` no usa pygame.

**Tipo de proyecto**: juego de escritorio por eventos, MVC en n capas (Principio I).

**Metas de rendimiento**: `historia` en menos de 50 ms con al menos 5 000 acciones del jugador y el K
por defecto (§6.1, SC-405). Nunca más de K acciones por consulta (FR-416, SC-404).

**Restricciones**: determinismo (Principio IV); Abierto/Cerrado (Principio III): todo lo nuevo va en
módulos nuevos y los cambios mínimos a la primera entrega están en la tabla de abajo.

**Escala**: partidas de hasta 5 000 acciones en el bench, criptas de hasta 50 salas publicadas y
cuadrículas sintéticas de hasta 10 000 salas (para ver el costo de cada copia).

## Verificación de la constitución

*Compuerta: antes de la fase 0, y otra vez después de la fase 1.*

| Principio | Cómo lo cumple este plan | Antes | Después |
|---|---|---|---|
| I. MVC en n capas | La línea (datos, recorte, búsqueda) es de **Logic**, sin I/O. El reconstructor, el despacho y los adaptadores son de **Service**, que llama a Logic y **no** a Data. Data solo gana un bloque de formato (Derek). La interfaz llama a Service y recibe un DTO. Logic nunca llama a Data ni a Service. | ✅ | ✅ |
| II. Bibliotecas y estructuras | Arreglos como almacenamiento contiguo, búsqueda binaria propia, copias a mano (sin `copy`). Revisión de estructuras existentes: R0 de [research.md](research.md). | ✅ | ✅ |
| III. KISS, YAGNI, Abierto/Cerrado | Todo lo nuevo en módulos nuevos, con type hints y docstring. Los cambios a la primera entrega están en la tabla siguiente, cada uno con su FR. No se toca `HistorialRetroceso`, `PartidaGuardada` ni `ServicioAccionJugador`. | ✅ | ✅ |
| IV. Determinismo | El punto de control incluye el estado del azar; la re-simulación usa las mismas reglas. Una prueba compara el resumen con el estado vivo (FR-419, SC-402). | ✅ | ✅ |
| V. Modos sin vista | `--replay … --hasta` y la reconstrucción no instancian la vista. | ✅ | ✅ |
| VI. Sin datos de una cripta concreta | Nada de ids ni números de salas en el código; el bench usa criptas sintéticas deterministas por semilla. | ✅ | ✅ |
| VII. Red y presupuesto | Reconstruir y consultar **no** piden nada a Data: contenido y fichas salen de la línea. Los adaptadores solo registran lo que la partida viva ya pidió (R3). | ✅ | ✅ |
| VIII. Rendimiento con evidencia | Cada decisión (R1 a R9) tiene alternativas, complejidad y medición prevista (M1 a M6). El valor de K es **provisional** hasta medir. | ✅ | ✅ |
| IX. Spec antes del código | Este plan no agrega reglas. Las observaciones están como hallazgos H-1, H-2 y H-4. | ✅ | ✅ |
| X. Trazabilidad | Hay una prueba por escenario y por caso del Apéndice B, y cada una cita su FR. | ✅ | ✅ |
| XI. Bitácora de LLM | Este prompt se registra en `PROMPTS_LLM.md`. | ✅ | ✅ |

**Resultado**: pasa. Los hallazgos no bloquean el plan, pero H-2 lo decide el integrante 3 antes de
cerrar la tarea del pergamino.

### Hallazgos

Abiertos: H-1 (resuelto en el diseño, con prueba), H-2 (decisión pendiente) y H-4 (dependencia). El
reloj que muestra el resumen ya no es un hallazgo: lo fija FR-405 de la spec (el instante pedido; para
`historia #k`, el instante de la decisión k; si la partida terminó antes, el reloj del final).

- **H-1** (FR-419): cargar una sala no se deshace con el pergamino y numera a los enemigos por tipo.
  Re-simular solo las acciones vigentes cambiaría la numeración. Solución sin reglas nuevas:
  registros de carga con ordinal, guardados en el orden real y aplicados como prefijo
  ([research.md, R3](research.md#hallazgo-h-1--el-orden-de-carga-de-salas-cambia-la-numeración-de-enemigos)).
- **H-2** (FR-413, FR-419) — **decisión del integrante 3** (`Inventario` y `HistorialRetroceso` son
  suyos): recoger o soltar un **pergamino** dentro de una acción revertida persiste en la partida
  viva, porque el pergamino está fuera del historial. El marcador de pergamino **no** lleva campos
  nuevos: solo dice «se descontó este pergamino». El plan implementa solo ese descuento.
  - *Tarea pendiente* (se numerará en `tasks.md`): decidir qué hace la línea cuando la acción
    revertida recogió o soltó un pergamino (documentarlo como límite conocido o reproducirlo con otro
    mecanismo), y dejar la decisión en `DECISIONES.md`.
  - *Prueba pendiente*: escenario con un pergamino recogido en la acción revertida, marcada con
    `skip` hasta que se decida; cita FR-413 y FR-419.
  - Detalle en [research.md, R4](research.md#hallazgo-h-2--recoger-o-soltar-un-pergamino-dentro-de-la-acción-revertida).
- **H-4** (dependencia): la spec 002 todavía no existe en el repositorio. El mapa conocido se copia
  con un método de copia manual **que se pide a esa clase**; hasta entonces el resumen omite esa
  sección (Suposiciones de la spec).

## Revisión de estructuras existentes (Principio II)

Resultado de la revisión de limitaciones contra la Parte II §3.6 y §5.5. Detalle en
[research.md, R0](research.md#r0-revisión-de-las-estructuras-ya-implementadas-principio-ii).

| Estructura | Limitación frente a la Parte II | Decisión |
|---|---|---|
| `HistorialRetroceso` | Tope de 5 (correcto para el pergamino); guarda funciones que no se pueden escribir en disco ni llevan tiempo; el pergamino queda fuera de él | No se toca ni sirve como línea. Esta feature no registra nada nuevo en él |
| `BufferCircular` | Pisa lo más antiguo; la línea debe conservar todo desde el inicio | No sirve |
| `Cola` | Sin acceso por posición ni por tiempo: ubicar un punto de control sería O(n) | No sirve |
| `ListaDoble` | Acceso por posición O(n): impide la búsqueda binaria | No sirve |
| `Ordenador` | La línea nace ordenada por tiempo (se agrega al final); no hay nada que ordenar | No se usa |
| `MonticuloMinimo` | Da el mínimo, no ubica por tiempo | No se usa |
| `PartidaGuardada` | Guarda y restaura el azar, la cola, los efectos y todas las salas, pero cada copia recorre todo el estado (O(S + E + V + I)); no guarda historial, mensajes, caché de rutas ni mapa conocido | Se reutiliza tal cual como punto de control y para reconstruir. Su costo es el riesgo R-1 |

Lo único nuevo en `Estructuras/` es una búsqueda binaria propia sobre un arreglo (sin `bisect`).

## Estructura del proyecto

### Documentación de esta feature

```text
specs/004-linea-tiempo/
├── plan.md                              # este archivo
├── research.md                          # fase 0: R0 a R10 y hallazgos H-1 y H-2
├── data-model.md                        # fase 1: entidades de la línea
├── quickstart.md                        # fase 1: cómo validar de punta a punta
├── contracts/
│   └── contrato-linea-tiempo.md         # fase 1: DTO, bloque binario, comandos y banderas
└── tasks.md                             # fase 2 (/speckit-tasks, NO lo crea este plan)
```

### Código fuente

```text
Estructuras/
└── BusquedaBinaria.py            # NUEVO: último elemento con clave <= pedida (sin bisect)

Logic/
├── LineaTiempo.py                # NUEVO: acciones vigentes, marcadores, puntos de control, registros de carga, recorte
└── motorJuego.py                 # MODIFICADO: método nuevo avanzar_hasta(t)   (FR-401, FR-402)

DTO/
├── LineaTiempoDTO.py             # NUEVO: DTO de la línea para guardar (acciones, marcadores, puntos, cargas, fichas, K)
├── ResumenHistoriaDTO.py         # NUEVO: lo que muestra una consulta (FR-405)
├── PartidaGuardadaDTO.py         # MODIFICADO: campo nuevo AL FINAL (linea), con valor por defecto   (Derek)
└── ConfiguracionDTO.py           # MODIFICADO: campos nuevos al final (hasta, checkpoint_cada)

Data/
└── GuardadoBinario.py            # MODIFICADO: VERSION_FORMATO = 2 y bloque propio de la línea   (Derek)

Service/
├── ReconstructorEstado.py        # NUEVO: arma el Motor aparte y re-simula (sin Data, sin log)   (FR-401..FR-404, FR-407)
├── DespachoAcciones.py           # NUEVO: AccionDTO -> llamada al Motor; sin bitácora ni caché viva
├── ArmadorResumen.py             # NUEVO: Motor aparte -> ResumenHistoriaDTO (sin cursor ni mensajes)   (FR-405, FR-406)
├── ServicioLineaTiempo.py        # NUEVO: registrar, consultar por t / por #k, ejecutar con registro
├── GrabadoresLinea.py            # NUEVO: ContenidoGrabador y ResolvedorGrabador (registro al primer uso)
├── ServicioReplayHasta.py        # NUEVO: --replay ... --hasta t   (FR-410..FR-412)
├── ContextoPartida.py            # MODIFICADO: campo final linea (valor por defecto None)
├── ServicioPartida.py            # MODIFICADO: crear la línea e instalar los grabadores en iniciar_partida
└── ServicioGuardado.py           # MODIFICADO: guardar y cargar el bloque de la línea; instalar grabadores

UIController/
├── LectorArgumentos.py           # MODIFICADO: --hasta y --checkpoint-cada   (FR-410, FR-415)
├── ControladorBackend.py         # MODIFICADO: ejecutar con registro; consultar historia; replay hasta
└── ControlesJuego.py             # MODIFICADO: comando «historia <t>» / «historia #k»   (FR-423)

View/                              # MODIFICADO (integrante 3): mostrar el resumen   (FR-423)
main.py                            # MODIFICADO: rama --replay con --hasta y códigos 0/1/2

Service/ (bench)
└── BenchLineaTiempo.py           # NUEVO: grupo de mediciones de la línea de tiempo (M1 a M6)

tests/
├── test_linea_tiempo_logica.py       # recorte, marcadores, registros de carga, búsqueda binaria
├── test_linea_tiempo_consultas.py    # escenarios H1, H3 y casos borde
├── test_linea_tiempo_replay.py       # escenarios H2 y códigos de salida
├── test_linea_tiempo_guardado.py     # escenarios H4
└── test_linea_tiempo_puntos.py       # escenarios H5 (K)
```

**Decisión de estructura**: se mantiene MVC en n capas. La línea es un dato de Logic; quien la
alimenta y la consulta es Service. El reconstructor vive en Service porque necesita armar un `Motor`
(Logic) a partir de DTO y decidir qué acciones re-simular, y no debe llamar a Data (Principio I).

## Cambios a código de la primera entrega (Principio III, Abierto/Cerrado)

Todo lo demás es código nuevo. Si un cambio modifica una decisión de la primera parte, se documenta el
antes y el después en `DECISIONES.md`.

| Archivo | Cambio | Por qué es indispensable | FR | Dueño |
|---|---|---|---|---|
| `Logic/motorJuego.py` | Método **nuevo** `avanzar_hasta(t)`; `avanzar_hasta_jugador` no se toca | Sin él no se puede detener el reloj en t antes de la siguiente decisión | FR-401, FR-402 | Marco (revisa) |
| `DTO/PartidaGuardadaDTO.py` | Campo nuevo `linea` **al final**, con valor por defecto | Guardar y cargar conservan la línea | FR-420 | Derek |
| `Data/GuardadoBinario.py` | `VERSION_FORMATO = 2` y bloque propio | Distinguir archivos de la primera parte y guardar la línea | FR-420, FR-421 | Derek |
| `DTO/ConfiguracionDTO.py`, `UIController/LectorArgumentos.py` | Campos y banderas nuevos al final (`hasta`, `checkpoint_cada`) | Pedidos por la spec | FR-410, FR-415 | Integrante 3 |
| `main.py` | Rama `--replay` con `--hasta`; códigos 0, 1 y 2 como en el resto del programa | Pedido por la spec | FR-410, FR-411 | Integrante 3 |
| `Service/ContextoPartida.py` | Campo final `linea = None` | Dónde vive la línea de una partida | FR-401 | Integrante 3 |
| `Service/ServicioPartida.py`, `Service/ServicioGuardado.py` | Crear/cargar la línea e instalar los grabadores (los dos únicos puntos donde se arma un contexto) | Sin ellos la línea no se alimenta ni se conserva | FR-401, FR-420 | Integrante 3 |
| `UIController/ControladorBackend.py`, `ControlesJuego.py`, `View/…` | Ejecutar con registro, comando `historia` y mostrar el resumen | Pedido por la spec | FR-423 | Integrante 3 |

**No se tocan**: `Logic/HistorialRetroceso.py` (su tope de 5 es correcto; decisión 9),
`Logic/PartidaGuardada.py`, `Service/ServicioAccionJugador.py`, `Service/ServicioReplay.py`, `Data/` (salvo el
bloque de Derek), ninguna estructura de `Estructuras/`.

## Contrato de datos

Detalle en [contracts/contrato-linea-tiempo.md](contracts/contrato-linea-tiempo.md). Resumen para
Derek: `PartidaGuardadaDTO.linea` (valor por defecto `None`) con un `LineaTiempoGuardadaDTO` nuevo,
que contiene K, las acciones vigentes con su tiempo, los marcadores de pergamino, los puntos de
control (cada uno con su `PartidaGuardadaDTO` y su lista de `SalaGuardadaDTO`), los registros de carga
de sala (con ordinal) y las fichas vistas. En el binario es un **bloque propio** con su offset y largo
en la cabecera, y `VERSION_FORMATO` pasa a 2. Al cargar se conserva el K guardado en la línea, aunque se
indique otro `--checkpoint-cada` (Suposiciones de la spec).

## Mediciones previstas (`--bench`, §6.3)

Todas con criptas sintéticas deterministas por semilla (Principio VIII). Se agregan al grupo de
mediciones existente sin modificar las anteriores.

| # | Qué mide | Variables | Para qué decisión |
|---|---|---|---|
| M1 | Tiempo de `historia` (mejor y mediana de repeticiones) | K ∈ {1, 5, 20, 100} y **sin puntos de control**; 5 000 acciones | Valor por defecto de K; SC-405 (< 50 ms) |
| M2 | Tiempo de `historia` según la posición consultada (inicio, mitad, final) | mismo conjunto | Peor caso y variación |
| M3 | Memoria: bytes del archivo serializado y conteo de elementos guardados | los mismos K y 100, 1 000 y 5 000 acciones | NFR-402 (crece con los cambios, no con acciones × estado) |
| M4 | Ubicar el punto de control: búsqueda binaria contra recorrido lineal | 100, 1 000 y 10 000 puntos de control | R5 (operación frecuente, §5.5) |
| M5 | **Costo de una copia** (un punto de control) | 6, 50, 1 000 y 10 000 salas; con 0, 10 y 100 enemigos | Riesgo R-1; si crece mal, evaluar copias incrementales |
| M6 | Costo del recorte al usar un pergamino | historia de 100 a 5 000 acciones | NFR-403 (no debe crecer con la historia) |

Además, la repetición de las mediciones de la primera parte con la carga nueva (§5.6) incluye ahora
`avanzar_hasta`, la cola de eventos con muchos eventos válidos y el historial de retroceso con la
línea activa. Si alguna decisión de la primera parte deja de ser adecuada, se muestra el antes y el
después en `DECISIONES.md`.

## Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R-1 | **Costo de cada copia**: `PartidaGuardada.guardar` recorre todas las salas, los eventos y el inventario (O(S + E + V + I)). Con K pequeño y muchas salas, el tiempo por acción y la memoria suben. | Medirlo (M5). K por defecto elegido con M1 y M3. Si es inaceptable, alternativa para el plan siguiente: guardar solo las salas que cambiaron desde el punto anterior (no se adelanta, YAGNI). |
| R-2 | **Duplicación del despacho** de acciones respecto de `ServicioAccionJugador`. | Una prueba compara el estado del despacho propio contra el del servicio para todas las acciones; una firma cambiada del motor la rompe. |
| R-3 | **El motor no es perfectamente reproducible** si alguien introduce estado nuevo que `PartidaGuardada` no guarda. | La prueba de SC-402 (200+ acciones, 100 % de coincidencias) es la red de seguridad; cualquier estado nuevo del motor debe entrar en `PartidaGuardada` (aviso al equipo). |
| R-4 | **Orden de carga de salas** (H-1). | Registros con ordinal, sin recorte, aplicados como prefijo; prueba específica. |
| R-5 | **Pergamino recogido o soltado en la acción revertida** (H-2). | Decisión del integrante 3; mientras tanto solo se implementa el descuento; prueba pendiente con `skip`. |
| R-6 | **Memoria con K = 1**: una copia por acción. | Es la medición M3; el bench muestra el costo y justifica el valor por defecto. |
| R-7 | **Archivo grande** al guardar (copias + registros). | Se mide el tamaño (M3); formato binario con tamaños fijos y contadores. |
| R-8 | **Mapa conocido ausente** (spec 002). | Se omite en el resumen y en las copias hasta que exista el método de copia manual. |

## Mapa de requisitos a componentes

| Requisito | Componente principal |
|---|---|
| FR-401, FR-403, FR-404 | `ServicioLineaTiempo.consultar_por_instante` / `consultar_por_accion` → `ReconstructorEstado` |
| FR-402 | `Motor.avanzar_hasta(t)` y la elección de la acción en `ReconstructorEstado` |
| FR-405, FR-406 | `ArmadorResumen` y `ResumenHistoriaDTO`: el reloj es el instante pedido (para `historia #k`, el de la decisión k; el del final si la partida terminó antes); sin cursor del inventario ni mensajes |
| FR-407, FR-408 | La consulta solo usa el motor aparte; no toca `contexto.motor`, la bitácora ni el historial |
| FR-409 | Validación en `ServicioLineaTiempo` (instante ≤ reloj actual, k entre 1 y acciones) y de estructura en el controlador |
| FR-410 a FR-412 | `LectorArgumentos`, `main.py`, `ServicioReplayHasta` |
| FR-413, FR-414 | `LineaTiempo` (recorte en el final de los arreglos), independiente de `HistorialRetroceso` |
| FR-415, FR-416, FR-418 | `LectorArgumentos`; puntos de control cada K en `LineaTiempo`; el resultado no depende de K |
| FR-419 | Punto de control con azar; re-simulación con las mismas reglas; H-1 |
| FR-420, FR-421 | `LineaTiempoDTO`, `GuardadoBinario` versión 2 |
| FR-423 | `ControlesJuego` y la vista |
| NFR-401 | `BenchLineaTiempo` (M1 a M6) y `DECISIONES.md` |
| NFR-402 | Solo acciones vigentes entre puntos de control; M3 |
| NFR-403 | Recorte por el final de los arreglos; M6 |
