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

## Viaje automático «ir a» (integrante 3)

**Responsable**: integrante 3 · **Cubre**: FR-250 a FR-264, NFR-250, NFR-251, SC-250 a SC-253, historias 6 y 7 y los
casos 1, 2b, 3 y 6 y A24 a A37 del Apéndice B. **Usa** el [contrato del mapa conocido](contracts/contrato-mapa-conocido.md)
(a) y (c), la búsqueda de la 001 ([busqueda-rutas.md](../001-terreno-cazador/contracts/busqueda-rutas.md)) y la
línea de tiempo de la 004. **Sin código ni tasks**: este texto fija el diseño; las tareas llegan con `/speckit-tasks`.

### Resumen

«ir a <sala>» no es un modo nuevo del juego: es una **orden que se descompone en movimientos ordinarios**. Cada paso
entra por el mismo camino que un movimiento hecho a mano (`ServicioLineaTiempo.ejecutar` → `ServicioAccionJugador` →
`Motor.mover_jugador`), así que FR-254, FR-263 y FR-264 se cumplen por construcción: el tiempo, los eventos del reloj,
la exploración, la antorcha, los enemigos, las trampas, `partida.log` y la línea de tiempo no se reimplementan. Lo único
nuevo es **decidir** cada paso y **cuándo parar**.

Decisiones de fondo:

1. **La decisión de cada paso se calcula desde cero** con `paso_desde_cero` de Marco sobre `GrafoMapaConocido`
   (FR-255, SC-251). No se guarda ninguna búsqueda entre pasos y el mapa no necesita avisar a nadie (recomendación del
   contrato (a)). Se descarta reutilizar `BusquedaCostoMinimo` con `observador_rutas`: ahorraría tiempo que nadie
   necesita (los 5 ms de NFR-250 se miden en R-I3-3) y obligaría a registrar el descarte con el pergamino.
2. **El servicio no guarda el estado del viaje**: el viaje es un `ViajeDTO` pequeño (destino, pasos dados, acciones
   esperadas) que viaja de una llamada a la siguiente. Así el pergamino (FR-262) y cargar una partida no pueden dejar un
   viaje «a medias» dentro del servicio, y la interfaz puede dar un paso por cuadro para animarlo.
3. **Toda regla vive en Logic** (`Logic/ViajeAutomatico.py`, sin I/O): resolver el destino, decidir el paso y
   decidir los motivos de parada. Service solo coordina: arma los datos, llama a Logic, ejecuta el paso y escribe el
   comentario.

**Decisiones confirmadas por el integrante 3** (resuelven los hallazgos I3-1, I3-4, I3-5, I3-7 y el H-2; la
spec no cambia):

| Hallazgo | Decisión |
|---|---|
| I3-4 | «ir a» desde una sala con enemigos vivos **permite el primer paso**. El viaje solo se detiene al **entrar** a una sala con enemigos, activos o dormidos (§3.4, FR-258 b). La sala de partida nunca cuenta |
| I3-5 | El comentario `# ir a <sala>` se escribe **justo después del primer paso aceptado**: queda entre el primer y el segundo paso y `--replay` lo ignora |
| I3-7 | `INTERRUMPIDO`, `TERMINADA` y `PASO_RECHAZADO` son **motivos internos**, no mensajes nuevos de la spec (FR-260 sigue con sus cinco motivos) |
| H-2 | **Opción A**: `ArmadorEstado` enmascara los destinos y la sala de salida no explorados; la vista no cambia (ver la sección del H-2) |
| D-1 (I3-1) | **No se pide `direccion_hacia`**: la dirección del paso se obtiene con `Mazmorra.salida` sobre las salas exploradas |
| M-2 (I3-3) | Riesgo anotado: la detección de daño se decide con la respuesta de Marco (ver I3-3 y R-I3-7) |

### Verificación de la constitución (v1.2.0)

| Principio | Cómo lo cumple esta sección | Antes | Después |
|---|---|---|---|
| I. MVC en n capas | Reglas en Logic (`ViajeAutomatico`); orquestación en Service (`ServicioIrA`); el Controlador solo valida la forma (texto no vacío) y traduce los motivos a mensajes; la vista no llama a Logic. DTO nuevos solo con datos | ✅ | ✅ |
| II. Estructuras | Listas y enteros; el grafo del mapa es el de Derek y la búsqueda es la de Marco; sin `dict`, `set`, `copy`, `sorted`, `heapq` ni `collections`. Nada nuevo en `Estructuras/` | ✅ | ✅ |
| III. KISS y Abierto/Cerrado | Dos clases nuevas (una de Logic, una de Service) y tres DTO; no se modifica `Motor`, `ServicioAccionJugador`, `ServicioLineaTiempo`, `BusquedaCostoMinimo` ni `MapaConocido`. Se descarta guardar el estado del viaje en el servicio (YAGNI) | ✅ | ✅ |
| IV. Determinismo | El paso depende solo del mapa y de la sala; sin azar ni reloj real; mismas acciones, mismo log, mismo viaje (FR-255, SC-253) | ✅ | ✅ |
| V. Modos sin vista | `ServicioIrA` no importa pygame ni `View/`; las pruebas lo usan sin ventana | ✅ | ✅ |
| VI. Sin datos de una cripta | Ningún nombre ni id en el código; las pruebas arman criptas a mano con la notación de la spec | ✅ | ✅ |
| VII. Red | Sin solicitudes propias: el contenido de la sala destino de cada paso lo pide `ServicioAccionJugador` como en cualquier movimiento | ✅ | ✅ |
| VIII. Evidencia | NFR-250 y NFR-251: `BenchViaje` con tres tamaños, enganchado en `--bench`; resultados a `DECISIONES.md` | ✅ | ✅ |
| IX. Spec antes del código | La spec ya fija FR-250 a FR-264; esta sección no agrega reglas: las ambigüedades quedan como hallazgos I3-n y la spec no se toca | ✅ | ✅ |
| X. Trazabilidad | Una prueba por escenario H6-1 a H6-10 y H7-1 a H7-9 y por caso A24 a A37, citando escenario y FR | ✅ | ✅ |
| XI. Bitácora de LLM | El prompt de esta sección se registra en `PROMPTS_LLM.md` | ✅ | ✅ |

### Componentes

```text
DTO/
└── ViajeDTO.py                  NUEVO: constantes de motivo; ViajeDTO, InicioViajeDTO, PasoViajeDTO     (FR-258, FR-260)

Logic/
└── ViajeAutomatico.py           NUEVO: resolver_destino, decidir_paso, motivos_de_parada                  (FR-251 a FR-253, FR-255 a FR-259)

Service/
└── ServicioIrA.py               NUEVO: iniciar(contexto, nombre), dar_paso(contexto, viaje)             (FR-250, FR-254, FR-261 a FR-264)

UIController/
└── ControladorBackend.py        AL FINAL DE LA CLASE: ir_a(nombre) y dar_paso_viaje(); sin tocar lo de otras features
```

- **`Logic/ViajeAutomatico.py`** (funciones puras; recibe el mapa, el grafo y datos simples; no importa Data ni Service):
  - `resolver_destino(mapa, nombre, sala_actual) -> (codigo, id | None)`. Códigos: `OK`, `DESTINO_INVALIDO`, `YA_AQUI`,
    `AMBIGUO`. Usa `mapa.buscar_exploradas(nombre)` (contrato (c)): `[]` → `DESTINO_INVALIDO` (**un solo código**
    para avistada, desconocida e inexistente: no hay forma de distinguirlas, FR-251); `[id]` igual a la sala actual →
    `YA_AQUI`; `[id]` → `OK`; dos o más → `AMBIGUO`. Un `nombre` que no es `str` es un error de programación
    (`ValueError`); uno vacío o de solo espacios es `DESTINO_INVALIDO`.
  - `decidir_paso(grafo, sala_actual, destino) -> (direccion, vecina, costo) | None`: llama a
    `paso_desde_cero(grafo, destino, sala_actual, None)` y devuelve `None` si no hay ruta (FR-259). La **dirección**
    se obtiene recorriendo las cuatro de la sala actual con `Mazmorra.salida(sala_actual, d)` (solo lectura) y tomando
    la primera, por número de dirección, cuyo destino es la vecina y cuyo costo es el del paso. Solo se mira una sala
    **explorada** (la actual) y una vecina que el grafo ya eligió, así que no se usa nada que el jugador no conozca
    (FR-252); la elección de la ruta sigue saliendo solo del mapa. Decisión D-1: no se pide nada a Derek.
  - `motivos_de_parada(sala_actual, destino, hay_enemigos, recibio_dano, terminada) -> list[str]`: los que apliquen,
    siempre en el mismo orden (`LLEGO`, `ENEMIGOS`, `DANO`, `TERMINADA`); lista vacía si el viaje sigue (FR-258, FR-260).
- **`Service/ServicioIrA.py`** (no guarda estado; recibe el contexto en cada llamada):
  - `iniciar(contexto, nombre) -> InicioViajeDTO`: aplica `resolver_destino`. Si no es `OK` devuelve el motivo y
    **no toca nada** (ni reloj, ni log, ni línea, ni mapa). Si es `OK` devuelve un `ViajeDTO` nuevo.
  - `dar_paso(contexto, viaje) -> PasoViajeDTO`: un paso o la parada. Detalle abajo.
- **DTO**: `ViajeDTO(destino, nombre_destino, pasos_dados, acciones_esperadas)`; `InicioViajeDTO(viaje | None,
  motivos)`; `PasoViajeDTO(viaje | None, motivos, estado)` (`viaje` es `None` cuando se detuvo; `estado` es el
  `EstadoJuegoDTO` posterior al paso, o el vigente si no se dio ninguno). Los motivos son constantes de texto de
  `DTO/ViajeDTO.py`; el texto para el jugador lo arma el Controlador, con **un solo mensaje** para `DESTINO_INVALIDO`.
  `INTERRUMPIDO`, `TERMINADA` y `PASO_RECHAZADO` son **motivos internos** (I3-7): no son mensajes nuevos de la spec y
  la interfaz no está obligada a mostrarlos.
- **Controlador**: `ir_a(nombre)` valida solo la forma (texto no vacío tras `strip()`, sin saltos de línea) y llama
  a `iniciar`; `dar_paso_viaje()` guarda el `ViajeDTO` vigente de la sesión y llama a `dar_paso`; cualquier otra orden
  que cambie la partida (un pergamino, por ejemplo) descarta ese viaje. La interfaz muestra los motivos (FR-260).

### Flujo de un paso (`dar_paso`)

```text
1. Si contexto.jugador.acciones != viaje.acciones_esperadas        → parar con INTERRUMPIDO (un pergamino u otra orden
                                                                     tocó la partida: el viaje no continúa, FR-262)
2. Si la partida terminó                                            → parar con TERMINADA
3. grafo = GrafoMapaConocido(contexto.motor.mapa)                   (se arma en cada paso: es barato y no se guarda)
   paso  = ViajeAutomatico.decidir_paso(grafo, sala_actual, viaje.destino)
   si paso es None                                                  → parar con SIN_RUTA, sin tiempo (FR-256, FR-259)
4. vida_antes = jugador.vida
   estado = ServicioLineaTiempo.ejecutar(contexto, AccionDTO("mover", direccion))      (FR-254, FR-263, FR-264)
   si la acción no se hizo (jugador.acciones no subió 1)            → parar con PASO_RECHAZADO (ver I3-6)
5. Si viaje.pasos_dados == 0: contexto.bitacora.anexar_comentario("ir a <nombre de la sala destino>")   (FR-261)
6. motivos = ViajeAutomatico.motivos_de_parada(sala_actual, destino,
                 hay_enemigos = hay enemigos vivos en la sala a la que llegó,
                 recibio_dano = jugador.vida < vida_antes,
                 terminada = motor.terminado)
   si motivos no está vacío → parar con esos motivos; si no → devolver el viaje con pasos_dados + 1 y
   acciones_esperadas = jugador.acciones
```

- **No hay recálculo aparte**: el paso 3 de la **siguiente** llamada ya es el recálculo con el conocimiento vigente
  (FR-255) y no consume tiempo (FR-256): consultar el mapa y buscar no llaman al motor.
- **Daño de cualquier origen** (enemigo, trampa, veneno): se mide como baja de `jugador.vida` entre antes del paso y
  después de que `ServicioAccionJugador` dejó correr los eventos hasta la siguiente decisión, que es donde caen los
  daños sostenidos. El viaje se detiene **antes de dar el paso siguiente** porque la comprobación es del paso actual
  (FR-258 c). **Riesgo conocido** (I3-3, R-I3-7): comparar la vida antes y después puede no detectar un daño que una
  regeneración o una curación compense **en el mismo paso**; la señal fiable se decide con la respuesta de Marco (M-2).
- **Enemigos**: se cuentan los vivos de la sala de llegada **después** del paso. Los dormidos ya fueron activados por
  `Motor.mover_jugador` (P1 §2.4) y los activos ya estaban: los dos cuentan (FR-258 b, H7-3 y H7-4). Si la sala de
  llegada es el destino salen los dos motivos, `LLEGO` y `ENEMIGOS` (FR-260, H7-4). **No se mira la sala de
  partida** (decisión I3-4): quien pide «ir a» desde una sala con enemigos vivos da el primer paso; el viaje solo se
  detiene al **entrar** a una sala con enemigos, como dice §3.4.

### Puerta recordada abierta que está cerrada (FR-256)

El caso no necesita lógica propia. Al llegar a B, `Motor.mover_jugador` observa las puertas de B (FR-207, parte de
Derek) y el mapa deja de recordar la salida como abierta. El `dar_paso` siguiente arma el grafo con el mapa **ya
actualizado**: `salidas(B)` no ofrece esa salida y `paso_desde_cero` busca otra ruta o devuelve `None`. Con otra ruta
(H7-1) el viaje continúa; sin ella (H7-2) se detiene con `SIN_RUTA`, el reloj queda donde lo dejó el último paso y el
jugador sigue en B. Lo mismo vale para una puerta de la sala actual que se cierra sola entre dos pasos: `puerta_cambio`
actualiza el mapa en su instante (FR-207) y el recálculo la evita. **El viaje nunca abre puertas ni usa llaves**
(FR-257): `ServicioIrA` solo genera acciones `mover`; el grafo no ofrece una salida recordada cerrada, aunque el
jugador tenga la llave (H6-4).

Una puerta recordada abierta en una sala **lejana** que ya está cerrada en realidad no se descubre hasta llegar: el
viaje la usa en el cálculo y se corrige al llegar. Así lo exige FR-252 (solo el conocimiento del jugador).

### Pergamino durante el viaje (FR-262)

El pergamino ya es el caso −1 de `ServicioLineaTiempo.ejecutar` (004, T030) y cada paso es una acción ordinaria sin
marcador, así que **no hace falta código nuevo para revertir**: el pergamino quita el último paso, el historial devuelve
la posición, el reloj y el mapa (FR-222, lo hace Derek) y la línea toma su punto de control nuevo. Lo que sí hace
`ServicioIrA` es **no continuar**: `acciones_esperadas` ya no coincide (bajó 1) y `dar_paso` para con `INTERRUMPIDO`; el
Controlador además descarta el `ViajeDTO`. Los pasos anteriores no se tocan (H7-7: de cuatro pasos y un pergamino tras
el tercero quedan dos).

Como el viaje no guarda estado, no hay nada que «reanudar» tras el pergamino ni tras cargar una partida.

### Registro: `partida.log` y línea de tiempo (FR-261, FR-263)

- **Pasos**: salen solos. `ServicioAccionJugador` anexa cada `mover` aceptado a `partida.log` y `ServicioLineaTiempo`
  lo agrega a la línea con su número; `--replay` repite los movimientos tal cual (H7-8, H7-9, SC-253).
- **La orden**: el comentario `# ir a <sala>` se escribe con `BitacoraReplayIO.anexar_comentario` (T071, hecho)
  **solo si la orden dio al menos un paso**, es decir, **justo después del primer paso aceptado** (paso 5). Por eso no
  se escribe nada en un rechazo (`DESTINO_INVALIDO`, `YA_AQUI`, `AMBIGUO`) ni cuando no hay ruta (FR-261). El texto
  usa el **nombre real de la sala destino** (ya explorada), no lo que escribió el jugador: no puede traer saltos de
  línea, que `anexar_comentario` rechaza. **Queda entre el primer y el segundo paso** (decisión I3-5).
  `BitacoraReplayIO.leer` lo ignora y no cuenta como acción (T071), así que el resultado de `--replay` no cambia.
  Si `contexto.bitacora` es `None` no se escribe nada.
- **La orden no cuenta como acción ni recibe número** (FR-263): no pasa por la línea; solo los pasos.
- `--replay` **no pasa por `ServicioIrA`**: reproduce los movimientos del log. Nunca se vuelve a decidir un viaje al
  reproducir, así que el replay no depende de la búsqueda.

### Validación y nombres (H-3)

- La validación del destino (explorado, único, distinto de la sala actual) es **regla de negocio y vive en Logic**
  (`resolver_destino` más `mapa.buscar_exploradas`). El Controlador valida solo la **forma** del texto, como
  `LectorArgumentos`; Service solo propaga el código.
- **H-3 (confirmación)**: se acepta la propuesta de `strip().casefold()` en los dos lados. El Controlador pasa el
  texto crudo (sin normalizarlo él) y `buscar_exploradas` normaliza ambos lados, para que la regla viva en un solo
  lugar. Límites asumidos, que deben anotarse en `DECISIONES.md`: no se quitan tildes (`sotano` no encuentra
  `Sótano`) ni se colapsan espacios internos. Si el grupo los quiere, el cambio es de una línea en
  `buscar_exploradas` (Derek) y no toca esta sección.
- El mensaje de `DESTINO_INVALIDO` es único (FR-251, H6-1) y no distingue «avistada», «desconocida» e «inexistente».
  `AMBIGUO` y `YA_AQUI` sí tienen mensaje propio, porque solo hablan de salas ya exploradas.

### Rendimiento (NFR-250, NFR-251, SC-252)

Un paso cuesta un `paso_desde_cero`: una búsqueda de costo mínimo desde el destino sobre las salas **exploradas** (a lo
sumo las de la cripta, 50 en las publicadas) más `GrafoMapaConocido` en vivo (`salidas` O(4), `entradas` O(grado)). No
depende de cuánto dure el viaje ni de la longitud de `partida.log`.

`Logic/BenchViaje.py` (dueño: integrante 3, mismo patrón que `BenchMapaConocido`) mide, con cuadrículas sintéticas por
semilla de 100, 1 024 y 10 000 salas, **un paso completo** (`decidir_paso`) con el mapa conocido completo, y reutiliza
`_cronometrar` y `_mejor_y_mediana` de `BenchLogica` sin modificarlos. El criterio de NFR-250 se comprueba con la
cripta de referencia (< 5 ms); los tamaños grandes quedan como evidencia y no son criterio. Se engancha en
`Service/ServicioBench.py` después de `BenchMapaConocido` (lo toca también Derek: pregunta D-5). La alternativa
descartada, reutilizar la búsqueda con `observador_rutas`, **se mide solo si** la medición de arriba no cabe en 5 ms;
mientras quepa no se implementa (YAGNI, Principio VIII).

### H-2: qué usa la vista de `sala_destino` (análisis, sin implementar)

`EstadoJuegoDTO.sala.salidas[d].sala_destino` trae hoy el id real de cada destino, también de los **avistados**. Hay
**tres usos** en `View/EscenaJuego.py` y uno más en `ArmadorEstado`:

| Uso | Dónde | Qué hace con el id | ¿Necesita el id de una sala no explorada? |
|---|---|---|---|
| 1 | `puertas_a_dibujar` (línea 59) | Compara `salida.sala_destino` con `estado.sala_salida` para dibujar `PUERTA_FINAL` en lugar de `PUERTA_CERRADA` en las puertas cerradas | **No, pero filtra**: si la sala de salida está solo avistada, la puerta final delata cuál es |
| 2 | `posicion_del_protagonista` (línea 112) | Busca la salida cuyo destino es la **sala anterior** para poner al protagonista frente a la puerta por la que entró | No: la sala anterior siempre está explorada |
| 3 | `_instantanea` (línea 318) → `EfectosEscena._contiguas` | Junta los destinos de la sala y mira si alguno es la sala del cuadro anterior, para saber si fue un paso por una puerta | No: solo compara con la sala anterior, que está explorada |
| 4 | `ArmadorEstado` (líneas 41 y 42) | `EstadoJuegoDTO.sala_salida` y `sala_inicial` van con el id real de la cripta | `sala_salida` filtra la identidad de la sala de salida aunque nunca se explore |

Conclusión: la vista **solo compara** el destino con la sala anterior (siempre explorada) y con `sala_salida`; **nadie
necesita saber a qué sala lleva una salida no explorada**. Los usos 2 y 3 funcionan con cualquier valor que no coincida
con un id real; el 1 y el 4 son los que filtran.

**Decisión: opción A.** Las demás se dejan como alternativas descartadas (no se implementa nada en este plan):

| Opción | Cambio | A favor | En contra |
|---|---|---|---|
| **A (elegida)** | `ArmadorEstado` enmascara: `sala_destino = SIN_EXPLORAR` (constante `-1`) para destinos no explorados, y `sala_salida = None` mientras la sala de salida no esté explorada. La vista no cambia | Cambia una sola función; los tipos (`int`) y el formato de `SalaDTO` no cambian; los tres usos siguen funcionando (`-1` nunca iguala un id real ni a `sala_salida`); dos salidas hacia la misma avistada quedan indistinguibles, como pide FR-204 | Un valor centinela; la puerta final no se distingue hasta explorar la sala de salida (es lo que pide FR-217) |
| B | `SalidaDTO.sala_destino: int \| None` (`None` si no explorada) | Más explícito que el centinela | Toca `SalaDTO` y `SalidaDTO` (Derek), el análisis de Data y `a_diccionario`; la `Mazmorra` y las pruebas usan el campo como `int` |
| C | Campo nuevo `EstadoJuegoDTO.destinos_conocidos` (por dirección: id o `None`) y cambiar la vista (tres lugares) para usarlo; `sala_destino` queda en `-1` para los no explorados | Separa «lo que ve el jugador» de «lo que trae el esqueleto» | Toca la vista (el cambio más grande) y duplica información |
| D | `ArmadorEstado` calcula los tres hechos que la vista usa (¿es la puerta final?, ¿cuál es la puerta por la que entró?, ¿son contiguas?) y la vista deja de comparar ids | La vista deja de manejar ids de salas | Cambia la vista y su contrato; más campos nuevos |

**Cómo queda la opción A**:

- `ArmadorEstado` (Service, integrante 3) pone `sala_destino = SIN_EXPLORAR` en cada salida de `EstadoJuegoDTO.sala` cuyo
  destino **no está explorado**, y deja `EstadoJuegoDTO.sala_salida = None` mientras la sala de salida no esté
  explorada. Las salidas hacia salas exploradas, `sala_inicial` y el resto del estado no cambian.
- **La constante** `SIN_EXPLORAR = -1` se define en `DTO/MapaConocidoDTO.py`, archivo de Derek: **queda pendiente de su
  visto bueno** (pregunta D-6). Si no la acepta, va a `DTO/EstadoJuegoDTO.py` (mío) sin otro cambio.
- `ArmadorEstado` consulta `mapa.es_explorada(sala)`, O(1) por salida, y no usa `a_dto()` (O(S)) en cada
  `armar_estado`. El plan de Derek no nombra esa consulta (hoy existe `mapa.estado[sala]` por R1): pregunta D-2.
- **La vista no cambia**: `-1` nunca iguala un id real ni a `sala_salida` (`None`), así que los usos 2 y 3 siguen
  funcionando y el uso 1 deja de delatar la puerta final hasta explorar esa sala (FR-217).

**Cómo se prueba**: la prueba de SC-202 de Derek **revisa también `EstadoJuegoDTO`** (R-6); además,
`tests/test_estado_sin_filtrar.py` recorre 200 acciones, con y sin antorcha, y comprueba que ningún `sala_destino` ni
`sala_salida` del estado sea el id de una sala no explorada.

### Pruebas previstas (una por escenario y caso)

| Archivo | Cubre |
|---|---|
| `tests/test_viaje_logica.py` | `resolver_destino` (H6-1, H6-8, ambiguo, H-3 con mayúsculas y espacios), `decidir_paso` (H6-2, H6-3, H6-4, H6-5, H6-6, H2-6) y `motivos_de_parada` (H7-3 a H7-6) en Logic pura, con criptas a mano (`ayudas_mapa`) |
| `tests/test_servicio_ir_a.py` | H6-1 a H6-9 y H7-1 a H7-6 por el servicio y el motor reales: tiempo por paso (A24, H6-2), eventos entre pasos (A29, H6-7), antorcha y enemigos (A31, H6-9), recálculo y parada (H7-1, H7-2), daño por veneno (H7-5) |
| `tests/test_ir_a_pergamino.py` | H7-7 (caso 6): viaje de 4 pasos, pergamino tras el 3.º; quedan 2, el mapa vuelve, `dar_paso` para con `INTERRUMPIDO` |
| `tests/test_ir_a_registro.py` | H7-8 (A36): `partida.log` con 3 movimientos y un comentario; `--replay` da la partida y el mapa iguales, y el comentario no cambia nada (SC-253); orden sin pasos: **sin** comentario. H7-9 (A37): 3 acciones en la línea; `historia #k` de cada una; la orden no cuenta |
| `tests/test_bench_viaje.py` | NFR-251 con tamaños chicos; A32 (SC-252) con la cripta de referencia en `--bench` |
| `tests/test_estado_sin_filtrar.py` | H-2 (opción elegida): 200 acciones sin ver ids de salas no exploradas en `EstadoJuegoDTO` |

SC-251 se comprueba con un viaje de cada tipo, comparando cada decisión con `paso_desde_cero` aplicado aparte al mismo
mapa (mismo desempate por id).

### Hallazgos de esta sección

Ninguno bloquea; la spec no se modifica.

- **I3-1** (dirección del paso) — **resuelto, sin pedido a Derek**: `paso_desde_cero` devuelve `(vecina, costo)` y
  `GrafoMapaConocido.salidas(u)` devuelve `(destino, costo)` sin la dirección. La dirección se obtiene con
  `Mazmorra.salida` sobre la sala actual, que está explorada (ver `decidir_paso`). Con salidas repetidas hacia la
  misma vecina (H-4, fuera de las criptas publicadas) se toma la de menor número de dirección con ese costo.
- **I3-2** (consulta del estado de una sala): `ArmadorEstado` necesita `mapa.es_explorada(sala)`, O(1), para la opción A
  del H-2 (pregunta D-2).
- **I3-3** (daño) — **riesgo abierto**: se mide por `jugador.vida` antes y después del paso. Si P1 tiene regeneración
  o curación que ocurra dentro del mismo paso, un daño pequeño podría quedar compensado y no detener el viaje
  (FR-258 c). La señal fiable (comparar la vida u otra) se decide con la respuesta de Marco (M-2); hasta entonces el
  plan usa la comparación de la vida.
- **I3-4** (sala de partida con enemigos) — **decidido**: «ir a» desde una sala con enemigos vivos permite el primer
  paso; el viaje solo se detiene al **entrar** a una sala con enemigos, activos o dormidos (FR-258 b, §3.4).
- **I3-5** (momento del comentario) — **decidido**: se escribe justo después del primer paso aceptado, para cumplir
  «solo si la orden da al menos un paso» aun cuando el primer movimiento falle por la red (`ErrorRed`). Queda entre el
  primer y el segundo paso; el replay lo ignora y no cambia el resultado.
- **I3-6** (paso rechazado): con el recálculo antes de cada paso, `mover` no debería devolver `cerrada` ni `sin_salida`.
  Si aun así se rechaza, el viaje se detiene con `PASO_RECHAZADO` sin tiempo y sin comentario; es una defensa, no un caso
  esperado. Una excepción de red (`ErrorRed`) se propaga como en cualquier acción y deja el viaje interrumpido: los
  pasos ya dados quedan hechos, igual que si el jugador los hubiera movido a mano.
- **I3-7** (motivos internos) — **decidido**: `INTERRUMPIDO`, `TERMINADA` y `PASO_RECHAZADO` no están en FR-258 ni
  FR-260 y **no son mensajes nuevos de la spec**: son motivos internos del servicio. La interfaz puede no mostrar nada
  para `INTERRUMPIDO`. Si el jugador muere o gana durante el paso, `TERMINADA` acompaña a `DANO` o a `LLEGO`.
- **I3-8** (identidad del grafo): se arma un `GrafoMapaConocido` por paso. No se guarda entre pasos porque el
  pergamino, `restaurar` y cargar una partida cambian el mapa; armarlo es O(1).
- **I3-9** (H-3): sin tildes ni espacios internos; anotarlo en `DECISIONES.md` (sección del integrante 3).

### Preguntas

**Para Derek (integrante 2)**

- ~~**D-1**~~ (cerrada: no se pide `direccion_hacia`; se usa `Mazmorra.salida` sobre las salas exploradas).
- **D-2**: `ArmadorEstado` usará `mapa.es_explorada(sala)`; ¿existe como método público y O(1)? Si hoy solo está
  `mapa.estado[sala]`, ¿lo agregas?
- **D-3**: `buscar_exploradas(nombre)`: confirma que normaliza **ambos** lados con `strip().casefold()`, que una cadena
  vacía devuelve `[]` y que un valor que no es `str` lanza `ValueError`.
- **D-4**: `MapaConocido.restaurar` ¿actualiza el mismo objeto `motor.mapa` (referencias vigentes) o lo reemplaza? Mi
  servicio no guarda referencias entre pasos (I3-8), pero las pruebas sí leen `motor.mapa` entre acciones.
- **D-5**: orden de los cambios en `Service/ServicioBench.py` (tu `BenchMapaConocido` y mi `BenchViaje`): quien suba
  segundo hace el `merge`, como en la 003.
- **D-6** (pendiente de tu visto bueno): la constante `SIN_EXPLORAR = -1` de la opción A del H-2 se define en
  `DTO/MapaConocidoDTO.py`, que es tuyo. ¿La aceptas ahí? Si no, va a `DTO/EstadoJuegoDTO.py` sin otro cambio.

**Para Marco (integrante 1)**

- **M-1**: `paso_desde_cero(grafo, origen, u, limite)` con `limite=None` y un grafo cuyo `entradas(x)` cambia entre
  llamadas: confirma que no guarda nada entre llamadas (es la referencia «sin reutilización») y que el desempate es el
  de menor id entre **todas** las rutas de costo mínimo (FR-253). Mi servicio la llama con `origen = destino` del viaje
  y `u = sala actual`.
- **M-2** (decide la detección de daño): ¿existe en P1 algo que cure al jugador dentro de un mismo paso (regeneración,
  efecto sostenido positivo)? Si existe, ¿cuál es la señal fiable de «recibió daño»: comparar la vida antes y después, o
  un contador de daño recibido en el motor? No pido el cambio; solo cuál es la señal (I3-3, R-I3-7).
- **M-3**: `Mazmorra.enemigos_vivos(sala)` después de `mover_jugador` incluye a los dormidos recién activados,
  ¿correcto? El plan cuenta los vivos de la sala de llegada con esa función.

### Riesgos de esta sección

| # | Riesgo | Mitigación |
|---|---|---|
| R-I3-1 | **La dirección del paso** no sale del grafo (I3-1) | Se obtiene con `Mazmorra.salida` sobre la sala actual, explorada; prueba con dos rutas de igual costo (H6-3) |
| R-I3-2 | **Filtrar el id de salas no exploradas por `EstadoJuegoDTO`** (H-2) | Opción A y prueba de 200 acciones; SC-202 de Derek |
| R-I3-3 | **El paso no cabe en 5 ms** con la cripta de referencia | `BenchViaje` lo mide antes de cerrar; si falla, se mide la búsqueda reutilizada con `observador_rutas` |
| R-I3-4 | **El pergamino deja un viaje activo** en el Controlador | `acciones_esperadas` en el `ViajeDTO`: el servicio para aunque el Controlador no descarte el viaje |
| R-I3-5 | **Un viaje que abre puertas o usa llaves** | `ServicioIrA` solo construye acciones `mover`; prueba H6-4 con llave en el inventario |
| R-I3-6 | **Se revela información al rechazar** | Un solo código y un solo mensaje para destino no explorado o inexistente; la prueba H6-1 compara los tres textos |
| R-I3-7 | **El daño no se detecta** si la vida del jugador baja y sube en el mismo paso (regeneración o curación): comparar `jugador.vida` antes y después no ve el daño compensado (FR-258 c) | Se anota; la señal fiable la decide la respuesta de Marco (M-2). Mientras tanto, prueba H7-5 con veneno sin curación y una prueba que documenta el límite si P1 tiene curación |

### Mapa de requisitos a componentes

| Requisito | Componente |
|---|---|
| FR-250 | `ServicioIrA` solo genera `mover`; `ViajeAutomatico.decidir_paso` |
| FR-251 | `ViajeAutomatico.resolver_destino` (+ `MapaConocido.buscar_exploradas`); un solo mensaje en el Controlador |
| FR-252, FR-253 | `GrafoMapaConocido` + `paso_desde_cero` (Marco) vía `decidir_paso` |
| FR-254 | `ServicioLineaTiempo.ejecutar` → `Motor.mover_jugador`; nada propio |
| FR-255, FR-256 | `dar_paso` recalcula desde cero antes de cada paso; el mapa se actualiza al llegar (FR-207) |
| FR-257 | Solo acciones `mover`; el grafo no ofrece salidas recordadas cerradas |
| FR-258, FR-259 | `ViajeAutomatico.motivos_de_parada` y `SIN_RUTA` en `dar_paso` |
| FR-260 | Motivos en `PasoViajeDTO`; mensajes del Controlador y la vista |
| FR-261 | `ServicioAccionJugador` (pasos) y `ServicioIrA` (`anexar_comentario` tras el primer paso) |
| FR-262 | Caso −1 de `ServicioLineaTiempo.ejecutar` + `acciones_esperadas` |
| FR-263 | Los pasos pasan por la línea; la orden no |
| FR-264 | `Motor.mover_jugador` |
| NFR-250, NFR-251, SC-252 | `Logic/BenchViaje.py` + `ServicioBench` + `DECISIONES.md` |
| SC-250, SC-251, SC-253 | `tests/test_servicio_ir_a.py`, `test_viaje_logica.py`, `test_ir_a_registro.py` |
