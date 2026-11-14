# Plan de implementación: Niebla de guerra, mapa conocido y viaje automático «ir a»

**Rama**: `derek` (spec-kit la reporta como `002-niebla-ir-a`) | **Fecha**: 2026-11-14 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación de `specs/002-niebla-ir-a/spec.md`. Este plan cubre la **parte del integrante 2**: mapa
conocido, memoria de puertas y antorcha (FR-201 a FR-225, NFR-201 a NFR-205, SC-201 a SC-207). La parte de «ir a»
(FR-250 a FR-264, NFR-250, NFR-251, SC-250 a SC-253, historias 6 y 7) es del **integrante 3**, que agrega su plan en
la sección reservada al final, en su propio commit. Aquí solo se fija el contrato que el mapa le ofrece (FR-225).

**Constitución**: v1.2.0 · **Responsable**: integrante 2

## Resumen

El jugador deja de ver el mapa completo. Cada sala está, para él, desconocida, avistada o explorada; el mapa recuerda
cada cara de cada puerta como la vio por última vez, o «sin observar»; la antorcha encendida explora las vecinas al
entrar, sin despertar nada y sin tiempo extra. Ese conocimiento es estado del juego: se guarda, se revierte con el
pergamino, entra en la línea de tiempo y se reproduce igual con `--replay`.

Enfoque técnico ([research.md](research.md)):

- **Representación** (R1): `Logic/MapaConocido.py`, estado de la partida en el motor (`motor.mapa`), con dos arreglos
  de enteros: `estado[sala]` y `caras[sala*4 + dirección]`. Consultas O(1) sin `dict` ni `set`. Lo que se sabe de una
  sala explorada (nombre, salidas, costo igualado) se lee del esqueleto solo si está explorada; el estado de una puerta
  sale siempre de `caras`, nunca del real.
- **Actualización** (R2): tres puntos de entrada y nada más: `iniciar` (sala inicial), `entrar(sala, antorcha)` desde
  `Motor.mover_jugador` y `puerta_cambio`, que reutiliza el aviso de puertas de la 001 por medio de un
  `RepartidorAvisosPuertas` (la `Mazmorra` tiene un solo observador, ocupado por el cazador). Costo proporcional a lo
  revelado.
- **Pergamino** (R3): cada casilla que cambia registra su propia reversión en el `HistorialRetroceso` que ya existe;
  O(1) por casilla, sin copiar el mapa.
- **Guardado y línea de tiempo** (R4): `PartidaGuardadaDTO.mapa` (antes de `linea`), copiado a mano por
  `PartidaGuardada.guardar` y `cargar` en O(S), una vez por punto de control; bloque propio en el binario versión 2,
  definido junto con el de la línea (T003 de la 004).
- **Contrato para el integrante 3** (R5): `GrafoMapaConocido` con la interfaz exacta de la búsqueda de la 001,
  `MapaConocidoDTO` de solo lectura y `buscar_exploradas(nombre)`.
- **Bench** (R7): `Logic/BenchMapaConocido.py` (B1 a B10), enganchado en `Service/ServicioBench.py`.

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior.

**Dependencias principales**: ninguna nueva. Se usan `dataclasses`, `typing`, `struct` (solo en `GuardadoBinario`),
`random.Random` y `time` (solo en el bench, con el cronómetro de `BenchLogica`) y `unittest`. Nada de `dict` ni `set`
como índice, `collections`, `heapq`, `bisect`, bibliotecas de grafos, `sorted()`/`list.sort()` ni `copy`.

**Almacenamiento**: en memoria, dos `list[int]` (5 casillas por sala). En el archivo de partida, un bloque propio de
2 bytes por sala en la versión 2 del formato, y el mismo bloque dentro de cada punto de control de la línea.

**Pruebas**: `unittest` en `tests/`, con `tests/correr_pruebas.py`. Cada prueba cita escenario y FR (R8).

**Plataforma**: escritorio con `pygame-ce`; `--replay`, `--replay … --hasta` y `--bench` no instancian la vista.

**Tipo de proyecto**: juego de escritorio por eventos, MVC en n capas (Principio I).

**Metas de rendimiento**: consultas de sala y de cara sin depender del tamaño (SC-203: < ×2 entre 100 y 10 000 salas);
exploración con antorcha y registro/inversión con el pergamino sin depender del tamaño del mapa conocido (SC-204,
SC-207); ciclo de eventos < 20 ms con 30 cazadores y la antorcha encendida en la cuadrícula de 1 024 salas de la 001
(NFR-205, SC-206).

**Restricciones**: determinismo (Principio IV): el mapa sale solo de las acciones; Abierto/Cerrado (Principio III): lo
nuevo en módulos nuevos, los cambios a lo existente en la tabla de abajo.

**Escala**: criptas publicadas de hasta 50 salas; cuadrículas sintéticas de hasta 10 000 salas en el bench.

No quedan puntos «NEEDS CLARIFICATION»: las dos ambigüedades de la spec están como hallazgos H-3 y H-5, con la lectura
que adopta el plan.

## Verificación de la constitución

*Compuerta: antes de la fase 0, y otra vez después de la fase 1.*

| Principio | Cómo lo cumple este plan | Antes | Después |
|---|---|---|---|
| I. MVC en n capas | El mapa, sus reglas, el grafo de «ir a» y la vista del mapa (`a_dto`) son de **Logic**, que no importa Data ni Service. Los DTO nuevos solo transportan datos. Data solo gana el bloque binario y valida su formato. Service no valida: copia `motor.mapa.a_dto()` y engancha el bench. La interfaz no llama a Logic: recibe el DTO por Service (integrante 3) | ✅ | ✅ |
| II. Bibliotecas y estructuras | Arreglos indexados por entero (sala y cara); sin `dict`, `set`, `copy` ni ordenamientos; copias con `list(...)`. Revisión de estructuras existentes: R0 | ✅ | ✅ |
| III. KISS, YAGNI, Abierto/Cerrado | Tres clases nuevas pequeñas (mapa, grafo, repartidor) con type hints y docstring. Los cambios a código existente (4 líneas del motor, 2 de `PartidaGuardada`, un campo del DTO, el formato binario y una línea del bench) están en la tabla, cada uno con su FR. No se modifican `Mazmorra`, `HistorialRetroceso` ni `Efectos`. El aviso a «ir a» es opcional y no se usa si el integrante 3 recalcula por paso | ✅ | ✅ |
| IV. Determinismo | El mapa no usa azar ni reloj real; recorre las direcciones en orden fijo; lo llaman el motor y la cola en su orden determinista. `--replay` y la 004 pasan por el mismo motor; los comentarios `# ir a` no son acciones (R6) | ✅ | ✅ |
| V. Modos sin vista | Todo lo nuevo está en Logic y DTO; el bench y el replay no tocan la vista | ✅ | ✅ |
| VI. Sin datos de una cripta concreta | Nada de ids ni nombres en el código; cuadrículas sintéticas por semilla en el bench | ✅ | ✅ |
| VII. Red y presupuesto | Sin solicitudes nuevas: la antorcha usa solo el esqueleto ya descargado y no pide contenido | ✅ | ✅ |
| VIII. Rendimiento con evidencia | B1 a B10 con las alternativas descartadas de R1, R2 y R3 medidas; resultados a `DECISIONES.md` (NFR-204) | ✅ | ✅ |
| IX. Spec antes del código | La spec está confirmada en su commit (con la parte del integrante 3). Este plan no agrega reglas: las ambigüedades quedan como hallazgos y la spec no se toca | ✅ | ✅ |
| X. Trazabilidad | Una prueba por escenario de las historias 1 a 5 y por caso del Apéndice B de esta parte (2a, 4, 5, A1 a A23, A38 a A43), citando escenario y FR (R8) | ✅ | ✅ |
| XI. Bitácora de LLM | El prompt de este `/speckit-plan` se registra en `PROMPTS_LLM.md` en el commit del plan | ✅ | ✅ |

**Resultado**: pasa. Sin violaciones que justificar (la tabla de complejidad queda vacía).

### Hallazgos

Ninguno bloquea; detalle en [research.md, Hallazgos](research.md#hallazgos). La spec no se modificó.

- **H-1** (coordinación con el integrante 1): la `Mazmorra` tiene un solo `observador_puertas`; el motor debe asignar el
  repartidor. `BenchRutas` lo reasigna en dos mediciones propias, sin efecto sobre lo que miden.
- **H-2** (SC-202, FR-204; integrante 3): `EstadoJuegoDTO.sala.salidas[d].sala_destino` lleva hoy el id real de
  destinos **avistados** y la vista lo usa (`View/EscenaJuego.py`). Con eso la prueba automática de SC-202 falla y la
  interfaz podría saber que dos salidas llevan a la misma sala avistada. Lo resuelve el integrante 3 en
  `ArmadorEstado`; la prueba de SC-202 de este plan revisa también el `EstadoJuegoDTO`.
- **H-3** (FR-251, ambigua): la spec no dice cómo se comparan los nombres de «ir a <sala>». Propuesta:
  `strip().casefold()` en los dos lados; a confirmar con el integrante 3.
- **H-4** (límite conocido): con salidas repetidas hacia la misma vecina, el emparejamiento de caras es el de la
  `Mazmorra` y una cara de la vecina no se observa desde el otro lado. Las criptas publicadas no las tienen.
- **H-5** (escenario H2-5, ambiguo): «desde A» con la puerta A–C «sin observar» no puede significar que el jugador
  está en A (la habría observado). Se lee como «las salidas de A que se ofrecen», con el jugador en otra sala.
- **H-6** (SC-206): «1 000 salas» se mide con la cuadrícula de 1 024 de la 001, para usar la misma cripta.
- **H-7** (dependencia de la 001): se usa `Mazmorra._salida_inversa` para emparejar caras, como `PartidaGuardada`.
- **H-8** (informativo, FR-203): cargar una partida reemplaza el mapa por el guardado; no es una sala que «vuelve»
  dentro de la misma partida.

## Revisión de estructuras existentes (Principio II)

Detalle en [research.md, R0](research.md#r0-revisión-de-las-estructuras-ya-implementadas-principio-ii).

| Estructura | Limitación frente a la Parte II | Decisión |
|---|---|---|
| `HistorialRetroceso` | Ninguna: registrar O(1), deshacer O(cambios del intervalo) | Se usa para el pergamino (R3), sin modificarlo |
| `Mazmorra` | Mezcla esqueleto y estado real; un solo observador de puertas | Solo lectura; aviso repartido (R2) |
| `GrafoEsqueleto` | «Utilizable» = abierta ahora | No se usa; el grafo del mapa es otro (R5) |
| `BusquedaCostoMinimo` | Ninguna (grafo como parámetro) | La usa «ir a» sobre `GrafoMapaConocido` |
| `RutasHaciaJugador` | Es el observador de puertas actual | No se toca; convive por el repartidor |
| `PartidaGuardada` | No conoce el mapa | Se extiende (2 líneas) |
| `GuardadoBinario` | Versión 1 | Versión 2 con bloque del mapa y de la línea |
| `Cola`, `ListaDoble`, `BufferCircular`, `MonticuloMinimo`, `BusquedaBinaria`, `Ordenador` | No dan acceso directo por id; no hace falta ordenar | No se usan |

No se agrega nada a `Estructuras/`.

## Estructura del proyecto

### Documentación de esta feature

```text
specs/002-niebla-ir-a/
├── spec.md                              # (sin cambios)
├── plan.md                              # este archivo (+ sección reservada del integrante 3)
├── research.md                          # fase 0: R0 a R8 y hallazgos
├── data-model.md                        # fase 1: mapa, grafo, DTO, bloque binario, cambios del motor
├── quickstart.md                        # fase 1: cómo validar de punta a punta
├── contracts/
│   └── contrato-mapa-conocido.md        # fase 1: grafo, DTO de vista, búsqueda por nombre y lo que no se ofrece
├── checklists/requirements.md
└── tasks.md                             # fase 2 (/speckit-tasks, NO lo crea este plan)
```

### Código fuente

```text
DTO/
├── MapaConocidoDTO.py            # NUEVO: constantes; MapaConocidoDTO, SalaConocidaDTO, SalidaConocidaDTO; MapaConocidoGuardadoDTO
└── PartidaGuardadaDTO.py         # MODIFICADO: campo mapa al final, antes de linea (T002 de la 004)   (FR-221)

Logic/
├── MapaConocido.py               # NUEVO: estado de salas y caras, iniciar/entrar/puerta_cambio, a_dto, buscar_exploradas, a_guardado/restaurar   (FR-201..FR-222)
├── GrafoMapaConocido.py          # NUEVO: cantidad_salas/salidas/entradas para «ir a»   (FR-225)
├── RepartidorAvisosPuertas.py    # NUEVO: reenvía puerta_cambio a las rutas del cazador y al mapa   (FR-207; 001 FR-114)
├── BenchMapaConocido.py          # NUEVO: B1 a B10   (NFR-204, SC-203, SC-204, SC-206, SC-207)
├── motorJuego.py                 # MODIFICADO (integrante 1): crea el mapa y el repartidor; iniciar y mover_jugador lo llaman
└── PartidaGuardada.py            # MODIFICADO: guardar/cargar copian el mapa   (FR-221, FR-223)

Data/
└── GuardadoBinario.py            # MODIFICADO: VERSION_FORMATO = 2 con bloque del mapa (y de la línea, T003 de la 004)

Service/
└── ServicioBench.py              # MODIFICADO: agrega BenchMapaConocido.medir a la lista por defecto

tests/
├── ayudas_mapa.py                    # criptas a mano con la notación de la spec
├── test_mapa_conocido_estados.py     # historia 1 (A1, A2, A3, A13, A14, A41)
├── test_mapa_conocido_puertas.py     # historia 2 (caso 2a, A4, A15, A16, A38, A42)
├── test_mapa_conocido_antorcha.py    # historia 3 (caso 4, A5, A6, A17..A20, A43)
├── test_mapa_conocido_partida.py     # historia 4 (caso 5, A7..A10)
├── test_mapa_conocido_vista.py       # historia 5 (A11, A12, A21..A23, A39, A40) y SC-202
├── test_grafo_mapa_conocido.py       # contrato (a), (c), (d)
├── test_guardado_mapa.py             # DTO y binario versión 2
└── test_bench_mapa.py                # B1 a B10 con tamaños chicos
```

**Decisión de estructura**: se mantiene MVC en n capas. El mapa es estado y reglas del juego, así que vive en Logic y
lo mantiene el motor; la vista del mapa también la arma Logic, porque es Logic quien decide qué conoce el jugador
(FR-217). Data solo serializa. No se crea ninguna carpeta.

## Cambios a código existente y de otros integrantes (Principio III)

Todo lo demás es código nuevo. Si un cambio modifica una decisión de la primera parte, se documenta el antes y el
después en `DECISIONES.md`. Dueños verificados con `git log` y con los `plan.md` de las otras features.

| Archivo | Cambio exacto | Por qué es indispensable | FR | Dueño |
|---|---|---|---|---|
| `Logic/motorJuego.py` · imports | `from Logic.MapaConocido import MapaConocido` y `from Logic.RepartidorAvisosPuertas import RepartidorAvisosPuertas` | Para lo de abajo | — | **Integrante 1** (código P1 y de la 001 suyo). **Se le pide el cambio; no lo hace el integrante 2** |
| `Logic/motorJuego.py` · `__init__` | Después de `self.rutas = …`: `self.mapa = MapaConocido(mazmorra, jugador, self.historial)`. **Reemplaza** `self.mazmorra.observador_puertas = self.rutas` por `self.mazmorra.observador_puertas = RepartidorAvisosPuertas([self.rutas, self.mapa])` | El motor es dueño del historial, el jugador y la mazmorra; la `Mazmorra` admite un solo observador y el cazador ya lo usa | FR-201, FR-207; 001 FR-114 | Integrante 1 (se le pide) |
| `Logic/motorJuego.py` · `iniciar()` | Después de `self.rastro.marcar(...)`: `self.mapa.iniciar(self.jugador.Sala_Actual)` | La sala inicial está explorada desde t = 0 | FR-202 | Integrante 1 (se le pide) |
| `Logic/motorJuego.py` · `mover_jugador()` | Justo después de `self.jugador.Sala_Actual = destino`: `self.mapa.entrar(destino, self.efectos.tiene(self.jugador, "antorcha"))` | Es el único punto donde el jugador entra a una sala; ahí se sabe si la antorcha está encendida en ese instante (H3-8) | FR-203, FR-207, FR-210 a FR-214 | Integrante 1 (se le pide) |
| `Logic/PartidaGuardada.py` · `guardar` | Argumento nuevo en el `PartidaGuardadaDTO(...)`: `mapa=motor.mapa.a_guardado()` | Los puntos de control y el guardado deben llevar el mapa (T004 de la 004) | FR-221, FR-223 | **Sin dueño claro**: es código P1 del integrante 1 (autor en `git log`), pero el plan de la 004 dice que «lo extiende Derek para el mapa conocido». Propuesta: lo escribe el integrante 2 y lo revisa el integrante 1; **confirmar con él antes de `tasks.md`** |
| `Logic/PartidaGuardada.py` · `cargar` | Antes de `motor.historial.descartar_intervalo_abierto()`: `motor.mapa.restaurar(partida.mapa)` (si `partida.mapa` es `None`, `restaurar` no se llama y `cargar` lanza `ValueError` con el motivo) | El mapa cargado debe ser idéntico (FR-221); la re-simulación de la 004 parte de él | FR-221, FR-223 | Ídem |
| `DTO/PartidaGuardadaDTO.py` | Campo `mapa: MapaConocidoGuardadoDTO \| None = None` al final, **antes de `linea`** (T002); `"mapa"` en `a_diccionario` y `d.get("mapa")` en `desde_diccionario` | El mapa es estado de la partida | FR-221 | Integrante 2 |
| `Data/GuardadoBinario.py` | `VERSION_FORMATO = 2`; cabecera de 58 bytes con offset y largo del mapa y de la línea; `_codificar_mapa` / `_leer_mapa` (también para cada punto de control de la línea); validación de formato; `cargar` lee el mapa; `cargar_sala` no | Guardar el mapa y distinguir los archivos de la primera parte | FR-221; 004 FR-420, FR-421 | Integrante 2 (junto con T003) |
| `Service/ServicioBench.py` | `from Logic import BenchMapaConocido` y `BenchMapaConocido.medir` en la lista por defecto, después de `BenchLogica.medir` (y de `BenchResolubilidad.medir` si ya está). Sin import circular: ni `BenchLogica` ni `BenchRutas` importan `BenchMapaConocido` | Exponer las mediciones en `--bench`; `Logic/BenchLogica.py` no se modifica | NFR-204 | Integrante 2 |
| `Service/ArmadorEstado.py`, `DTO/EstadoJuegoDTO.py` | (Opcional) campo final `mapa_conocido: MapaConocidoDTO \| None = None` con `motor.mapa.a_dto()`. Y resolver H-2 (`sala_destino` de destinos no explorados) | Que la vista muestre solo el conocimiento (FR-217, SC-202) | FR-217, FR-219 | **Integrante 3** (decide ella) |
| `Service/ArmadorResumen.py` (004, T023) | `mapa_conocido=motor.mapa.a_dto()` sobre el motor aparte | El resumen muestra el mapa de ese instante | FR-223; 004 FR-405 | Integrante 3 |
| `UIController/…`, `View/…` | Comando de ver el mapa y dibujo, con `MapaConocidoDTO`; no se registra en `partida.log` ni pasa por el historial | §3.3, §7.3 | FR-219, FR-220 | Integrante 3 |
| `DECISIONES.md` | Sección del integrante 2: «Mapa conocido» (R1 a R4) con los números de B1 a B10 | Principio VIII | NFR-204 | Integrante 2 |

**No se tocan**: `Logic/Mazmorra.py` (solo lectura, incluido `_salida_inversa`), `Logic/HistorialRetroceso.py`,
`Logic/Efectos.py` y `Logic/GestorEfectos.py` (la antorcha se consulta con `efectos.tiene`), `Logic/BenchLogica.py`,
`Logic/BenchRutas.py`, `Service/ContextoPartida.py` (el mapa vive en `contexto.motor`), `Service/ServicioPartida.py`,
`Service/ServicioGuardado.py` (el mapa viaja dentro del DTO), `Service/ServicioReplay.py`,
`Data/BitacoraReplayIO.py` (T071 ya hecho), `DTO/ResumenHistoriaDTO.py` (su `mapa_conocido: object | None` ya admite
el DTO), ningún archivo de `Estructuras/`.

## Coordinación

**Con el integrante 1**:

1. **Pedido de cambio en `Logic/motorJuego.py`**: las cuatro líneas de la tabla (más dos imports). El integrante 2 no
   las escribe. Hasta que estén, las pruebas que pasan por el motor quedan en `skip` con el motivo; las de
   `MapaConocido` y `GrafoMapaConocido` con una `Mazmorra` y un jugador de prueba no dependen de ellas.
2. **`Logic/PartidaGuardada.py`**: confirmar quién escribe las dos líneas (propuesta: el integrante 2, con su revisión),
   porque el archivo es suyo y la 004 asignó la extensión al integrante 2.
3. **Reglas de la 001 que el mapa usa sin copiarlas**: el aviso `puerta_cambio` (FR-114), `SalidaViva.costo` igualado
   (FR-101) y `_salida_inversa` (emparejamiento de caras). Si cambian, avisa antes (H-7).
4. **`observador_puertas`** (H-1): el data-model de la 001 queda desactualizado; `BenchRutas` lo reasigna en dos
   mediciones sin efecto para ellas.
5. Reutilización en el bench de `_cronometrar`, `_mejor_y_mediana`, `SEMILLA` (`BenchLogica`) y
   `_cuadricula_con_costos`, `_motor_con_cazadores`, `_centro`, `_peor` (`BenchRutas`), sin modificarlas; confirmar que no
   les cambia el nombre ni la firma sin avisar (como en la 003).
6. Revisión cruzada del plan, como en las specs.

**Con el integrante 3**:

1. Revisar y confirmar [contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md): grafo, DTO, búsqueda por nombre
   (H-3) y lo que no se ofrece.
2. **H-2**: decidir cómo deja de llegar a la vista el id de los destinos avistados en `EstadoJuegoDTO`.
3. **004**: T023 copia `motor.mapa.a_dto()` al resumen; el contrato binario de la 004 (§2) debe decir que la cabecera
   también lleva el bloque del mapa y que cada punto de control lleva su mapa (ver «Cambios que piden la 004 y la 001»).
4. «ir a» llama a `BitacoraReplayIO.anexar_comentario` (T071, hecho) y pasa por `ServicioLineaTiempo.ejecutar`; sus pasos
   actualizan el mapa por ser movimientos ordinarios (FR-264). El mapa no necesita nada de su parte para eso.
5. Su sección del plan va al final de este archivo, en su propio commit.

### Cambios que piden la 004 y la 001

| Feature | Qué | Cambio | Quién |
|---|---|---|---|
| 004 · T002 | Orden de campos de `PartidaGuardadaDTO` | `mapa` va **antes** de `linea` (que sigue siendo el último). Anotar `linea` con texto e importar `LineaTiempoGuardadaDTO` dentro de `desde_diccionario` para no formar un ciclo de imports | Integrante 2 (las dos tareas son suyas) |
| 004 · T003 y contrato §2 | Cabecera de la versión 2 | Lleva offset y largo **del mapa y de la línea** (58 bytes); cada punto de control de la línea lleva también el bloque de su mapa. Si T003 va antes que el mapa, reserva el lugar con largo 0 para no pasar a versión 3 | Integrante 2 implementa; el texto del contrato de la 004 lo actualiza el integrante 3 (o el integrante 2 con su visto bueno) |
| 004 · T004 | Mapa en `PartidaGuardadaDTO` | Se cumple con este plan (R4); no cambia | — |
| 004 · T023 | Resumen | `mapa_conocido = motor.mapa.a_dto()` (no el DTO guardado, que no trae nombres) | Integrante 3 |
| 001 | Specs | Ninguno. El contrato `busqueda-rutas.md` se cumple tal cual; solo queda desactualizada la mención del data-model a `observador_puertas = self.rutas` (H-1) | Integrante 1, si quiere anotarlo |
| 001 | Código | Las cuatro líneas de `Logic/motorJuego.py` | Integrante 1 |

## Mediciones previstas (`--bench`, §6.3)

Cuadrículas sintéticas por semilla de 100, 1 024 y 10 000 salas (Principio VIII); detalle en
[research.md, R7](research.md#r7---bench-decisión-7).

| # | Qué mide | Tamaños | Para qué |
|---|---|---|---|
| B1 | Consulta de estado de sala | 100 / 1 024 / 10 000 | SC-203 (< ×2) |
| B2 | Consulta de cara recordada | ídem | SC-203 (< ×2) |
| B3 | Alternativa descartada: lista de exploradas recorrida | ídem | Respaldar R1 |
| B4 | Entrada con antorcha que revela la misma cantidad de salas | mapa conocido de ~100 / ~1 000 / ~10 000 | SC-204 (< ×2) |
| B5 | Alternativa descartada: recalcular avistadas recorriendo el mapa | ídem | Respaldar R2 |
| B6 | Registrar e invertir con el pergamino los cambios de una entrada con antorcha | ídem | SC-207 (< ×2) |
| B7 | Alternativa descartada: copiar y restaurar el mapa entero por acción | ídem | Respaldar R3 |
| B8 | Ciclo de eventos con antorcha, 30 cazadores, jugador que se mueve (y variante con puerta de su sala que cambia) | 1 024 | NFR-205, SC-206 (< 20 ms) |
| B9 | Copia del mapa para un punto de control | 100 / 1 024 / 10 000 | NFR-203 (lineal, una vez por punto) |
| B10 | `a_dto` y `buscar_exploradas` con el mapa completo | ídem | Respaldar R5 (b) y (c) |

`DECISIONES.md`, sección del integrante 2, gana «Mapa conocido» con problema, alternativas, decisión, complejidad, los
números de B1 a B10 y si la decisión final coincide con este plan.

## Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R-1 | **El cambio del motor no llega** (es del integrante 1) | Pedido exacto en la tabla; las pruebas de Logic pura avanzan sin él y las del motor quedan en `skip` con motivo |
| R-2 | **Algo distinto del jugador escribe el mapa** (FR-218) | Tres puntos de entrada; pruebas H1-5, H1-7 y H5-7; nadie más tiene referencia al mapa salvo el motor y el repartidor |
| R-3 | **El emparejamiento de caras diverge de la `Mazmorra`** | Se usa `_salida_inversa` en lugar de copiar la regla (H-7); pruebas H2-6 y A16 |
| R-4 | **La re-simulación de la 004 escribe dentro de un punto de control** | `a_guardado` y `restaurar` copian los arreglos (R4); prueba que restaura dos veces del mismo DTO y compara |
| R-5 | **Cambio de formato binario dos veces** (T003 antes que el mapa) | La versión 2 se define una sola vez con los dos bloques (R4) |
| R-6 | **Filtrar identidad de avistadas por `EstadoJuegoDTO`** (H-2) | La prueba de SC-202 revisa también ese DTO; lo resuelve el integrante 3 |
| R-7 | **Ciclo de eventos más lento con muchos avisos de puerta** | `puerta_cambio` es O(1) y no registra nada si no hay cambios; B8 con puertas que cambian en cada ciclo |
| R-8 | **Mapa de otra versión de la cripta al cargar** | `restaurar` compara largos con la `Mazmorra` y lanza `ValueError`; antes, `comprobar_compatibilidad` ya rechaza otra versión |

## Mapa de requisitos a componentes

| Requisito | Componente principal |
|---|---|
| FR-201, FR-206 | `MapaConocido.estado` (un valor por sala; 0 = desconocida) |
| FR-202 | `MapaConocido.iniciar`, llamado por `Motor.iniciar` |
| FR-203 | `MapaConocido.entrar` / `_explorar`, llamado por `Motor.mover_jugador`; ninguna operación baja un estado |
| FR-204 | `_explorar` (avista los destinos de las salidas de la explorada); `a_dto` (`destino = None`) |
| FR-205 | `a_dto` (nombre, salidas, `SalidaViva.costo` igualado, `caras`) |
| FR-207, FR-209 | `_observar_puertas` al entrar y en `puerta_cambio` (vía `RepartidorAvisosPuertas`) |
| FR-208 | `MapaConocido.caras`, por cara; `a_dto` y `GrafoMapaConocido` leen solo el recordado |
| FR-210 a FR-215 | `entrar(sala, antorcha)` con `efectos.tiene(jugador, "antorcha")` en el motor; `usar` no llama al mapa |
| FR-216 | Sin cambios: la entrada ordinaria del motor activa enemigos y trampas |
| FR-217 | `a_dto`, `GrafoMapaConocido`, `buscar_exploradas`: lo único que ve la interfaz y «ir a» |
| FR-218 | Tres puntos de entrada; ni Data, ni la precarga, ni el cazador tienen referencia al mapa |
| FR-219, FR-220 | `MapaConocidoDTO` (Logic) + comando y vista (integrante 3) |
| FR-221 | `a_guardado` / `restaurar`, `PartidaGuardada`, `PartidaGuardadaDTO.mapa`, `GuardadoBinario` versión 2 |
| FR-222 | `_poner_estado` / `_poner_cara` + `HistorialRetroceso.registrar_cambio` |
| FR-223 | Puntos de control (`PartidaGuardada.guardar`) y re-simulación de la 004; `ArmadorResumen` copia `a_dto` |
| FR-224 | Mapa determinista (R6); `BitacoraReplayIO.leer` ignora `# ir a` |
| FR-225 | `GrafoMapaConocido` ([contrato](contracts/contrato-mapa-conocido.md), (a)) |
| NFR-201 | Acceso directo a `estado` y `caras`; B1, B2 |
| NFR-202 | `_explorar` salta las ya exploradas; B4 |
| NFR-203 | Reversión por casilla (B6); copia O(S) por punto de control (B9) |
| NFR-204 | `Logic/BenchMapaConocido.py` + `Service/ServicioBench.py` + `DECISIONES.md` |
| NFR-205 | B8 |

## Seguimiento de complejidad

Sin violaciones de la constitución que justificar.

---

## Viaje automático «ir a» (integrante 3) — sección reservada

*Esta sección la completa el integrante 3 en su propio commit, con el plan de FR-250 a FR-264, NFR-250, NFR-251 y
SC-250 a SC-253 (historias 6 y 7). Usa [contracts/contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md) y la
búsqueda de la 001 ([busqueda-rutas.md](../001-terreno-cazador/contracts/busqueda-rutas.md)). El integrante 2 no la
edita.*
