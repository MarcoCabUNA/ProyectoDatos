---
description: "Lista de tareas de la feature 002: niebla de guerra y mapa conocido (parte del integrante 2)"
---

# Tareas: Niebla de guerra, mapa conocido y viaje automático «ir a»

**Entrada**: documentos de diseño de `specs/002-niebla-ir-a/`

**Prerrequisitos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md),
[quickstart.md](quickstart.md). Versión del plan del commit `acd4196` (`plan(002)`).

**Alcance de este archivo**: la **parte del integrante 2**: mapa conocido, memoria de puertas y antorcha (FR-201 a
FR-225, NFR-201 a NFR-205, SC-201 a SC-207; historias 1 a 5). Las tareas de «ir a» (FR-250 a FR-264, NFR-250,
NFR-251, SC-250 a SC-253; historias 6 y 7) son del **integrante 3** y van en la sección reservada del final.

**Numeración**: las tareas del integrante 2 van de **T001 a T099** (se usan T001 a T061; T034 se eliminó el 14/11 y su número no se reutiliza). Las del integrante 3 van
**desde T100**, en la sección reservada. Los números de tareas de otras features siempre se escriben calificados
(«T002 de la 004», «T071 de la 004», «T055 de la 001», «T067 de la 003»): un «T0xx» sin calificar es de este archivo.

**Pruebas**: sí. La constitución (Principio X) pide una prueba por escenario y por caso del Apéndice B, y el plan pide
`unittest` en `tests/` (research R8). Cada prueba cita en el nombre del método su escenario, el adicional de la tabla
de trazabilidad de la spec (`aNN`) o el caso del Apéndice B (`apendiceB_casoN`) y sus FR
(`test_h3_1_apendiceB_caso4_fr210_fr211_antorcha_no_despierta`). Se escriben **antes** que el código y deben fallar
primero. Las que pasan por el motor (variantes con el motor de las historias 1 a 4, repartidor e inicio) se escriben en
T031, **antes** del cambio de `Logic/motorJuego.py` (T033), y fallan hasta que T033 lo hace; no llevan `skipTest`.
Solo las que dependen de una pieza de otro integrante (T023 de la 004, H-2, `ServicioResolubilidad` de la 003) tienen
una guarda con su motivo y una tarea para quitarla (T050).

**Organización**: en el orden del plan: DTO del mapa → `MapaConocido` en Logic con una `Mazmorra` y un jugador de
prueba (estados, caras, iniciar, entrar, antorcha, observación, `puerta_cambio`, pergamino) → contrato para el
integrante 3 (`GrafoMapaConocido` y `buscar_exploradas`) → `RepartidorAvisosPuertas` y el cambio del motor →
guardado (DTO, `PartidaGuardada` y binario versión 2) → vista (`a_dto`, SC-202) → bench → documentación. Cada
historia de la spec es una etiqueta (H1 → US1 … H5 → US5).

**Responsable**: integrante 2. Las tareas marcadas **(coordinar con el integrante 1)** o **(coordinar con el
integrante 3)** tocan archivos de otro integrante según la tabla «Cambios a código existente» y la sección
«Coordinación» del plan; cada una dice el cambio exacto y **no se implementa sin su visto bueno**. Las marcadas
**Aviso** son mensajes a otro integrante, sin código. **Acuerdo del 14/11 con el integrante 1**: las líneas de
`Logic/motorJuego.py` (T033: crear el mapa y el `RepartidorAvisosPuertas` como `observador_puertas`, la llamada en
`iniciar` y la llamada en `mover_jugador`) y las dos de `Logic/PartidaGuardada.py` (T040: guardar y cargar el mapa)
**las escribe el integrante 2**, con sus pruebas primero, y **el integrante 1 las revisa antes del merge**, como el
integrante 3 con las suyas en la 003. Le parece bien el repartidor y anota en su plan las funciones privadas que usan
la 002 y la 003 (`_salida_inversa`, `_cronometrar`, `_mejor_y_mediana`, `SEMILLA`, `_cuadricula_con_costos`,
`_motor_con_cazadores`, `_centro`, `_peor`) para avisar antes de tocarlas. La vista, el comando de ver el mapa,
`Service/ArmadorEstado.py`, `DTO/EstadoJuegoDTO.py` y `Service/ArmadorResumen.py` son del integrante 3.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas sin terminar).
- **[US1]…[US5]**: historia de la spec a la que pertenece la tarea.
- Las fases de preparación, base, bench y cierre no llevan etiqueta de historia.

## Reglas para todas las tareas (constitución v1.2.0)

- Python 3.11 o superior. Sin dependencias nuevas (`dataclasses`, `typing`, `struct` solo en `Data/GuardadoBinario.py`,
  `random.Random` y `time` solo en el bench, `unittest`).
- Prohibido en `Logic/`, `Estructuras/`, `DTO/` y `Service/`: `copy` (incluido `deepcopy`), `bisect`, `heapq`,
  `collections`, `dict` o `set` como índice o caché, bibliotecas de grafos, y `sorted()` / `list.sort()`. Las copias de
  los arreglos se hacen con `list(...)`. `copy` solo en `tests/`.
- `Logic/` no importa `Data/` ni `Service/`. `DTO/MapaConocidoDTO.py` no importa nada del proyecto. Data solo valida
  formato. Service no valida: copia `motor.mapa.a_dto()`.
- **Solo tres puntos de entrada escriben el mapa** (research R2): `iniciar`, `entrar` y `puerta_cambio`, más
  `restaurar` al cargar. Toda escritura pasa por `_poner_estado` / `_poner_cara`. Ninguna operación baja un estado
  (FR-203); solo lo hace la reversión del historial.
- Determinismo (Principio IV): el mapa no usa azar ni reloj real; las direcciones se recorren siempre en el orden
  N, S, E, O (0, 1, 2, 3).
- Sin ids, nombres ni versiones de una cripta concreta en el código (Principio VI): las pruebas arman criptas a mano
  con la notación de la spec y el bench las genera por semilla.
- Código nuevo con type hints y docstring breve. Comentarios y nombres en español. No se agregan type hints ni
  docstrings al código de la primera entrega.
- **No se tocan**: `Logic/Mazmorra.py` (solo lectura, incluido `_salida_inversa`), `Logic/HistorialRetroceso.py`,
  `Logic/Efectos.py`, `Logic/GestorEfectos.py`, `Logic/BenchLogica.py`, `Logic/BenchRutas.py`,
  `Service/ContextoPartida.py`, `Service/ServicioPartida.py`, `Service/ServicioGuardado.py`,
  `Service/ServicioReplay.py`, `Data/BitacoraReplayIO.py` (T071 de la 004 ya hecha), `DTO/ResumenHistoriaDTO.py` ni
  ningún archivo de `Estructuras/`.
- Campos nuevos de DTO: **al final y con valor por defecto**; en `PartidaGuardadaDTO`, `mapa` va **antes de `linea`**,
  que sigue siendo el último (T002 de la 004).
- Las pruebas usan `unittest` y corren con `python tests/correr_pruebas.py`. En Windows se corre con
  `PYTHONIOENCODING=utf-8` (`$env:PYTHONIOENCODING = "utf-8"; uv run python tests/correr_pruebas.py` en PowerShell).
- Vocabulario: una **cara** es una salida vista desde una sala (`c = sala*4 + dirección`, 0 N, 1 S, 2 E, 3 O); S =
  `len(Mazmorra.salas)` (ids de 0 a S − 1; la posición 0 puede estar vacía); las constantes `DESCONOCIDA = 0`,
  `AVISTADA = 1`, `EXPLORADA = 2`, `SIN_OBSERVAR = 0`, `ABIERTA = 1`, `CERRADA = 2` son las de `DTO/MapaConocidoDTO.py`.

---

## Fase 1: Preparación

**Propósito**: ayudantes de prueba y los acuerdos con los otros integrantes desde el inicio, para que las decisiones
del integrante 3 lleguen a tiempo. Los acuerdos con el integrante 1 (T002, T003) quedaron cerrados el 14/11.

- [ ] T001 [P] Crear `tests/ayudas_mapa.py` (con docstring) sobre `salida`, `salida_sin_vuelta`, `mazmorra_con_costos` y `motor_con` de `tests/ayudas_terreno.py`, sin modificar ese archivo: `cripta_mapa(cantidad, salidas)` que devuelve una `Mazmorra` armada con la notación de la spec (A = 1, B = 2…; salidas con y sin vuelta, costo en una sola cara o en ninguna); `cara_cerrada_sin_llave(mazmorra, a, b)` (deja cerrada solo la cara de `a` de la puerta a–b, para H2-6); `JugadorPrueba(sala)`, un objeto con `Sala_Actual`, para usar `MapaConocido` sin motor; `mapa_de_prueba(mazmorra, sala_jugador, historial=None)`, que devuelve `(MapaConocido, JugadorPrueba)`; `estados(mapa)`, que devuelve `(list(mapa.estado), list(mapa.caras))` para comparar casilla por casilla. Ninguna cripta de ejemplo usa datos de una cripta publicada (Principio VI). Todo el ayudante, incluidos `mapa_de_prueba` y `estados`, se escribe **antes de T010**: hasta T012, las pruebas que lo usan fallan al importar `Logic.MapaConocido`, que es el fallo esperado. `JugadorPrueba` y `mapa_de_prueba` dependen de T011 (constantes) solo a través de `MapaConocido`.
- [x] T002 **(coordinar con el integrante 1)** *Confirmado por el integrante 1 el 14/11: el cambio de `Logic/motorJuego.py` lo escribe el integrante 2, con sus pruebas (T031, T033), y él lo revisa antes del merge; le parece bien el repartidor.* (FR-201, FR-202, FR-203, FR-207, FR-210 a FR-214; 001 FR-114) Acordar con el integrante 1 el cambio en `Logic/motorJuego.py`, según la tabla «Cambios a código existente» del plan y [data-model.md](data-model.md) §8. Cambio exacto (lo implementa T033): (1) imports `from Logic.MapaConocido import MapaConocido` y `from Logic.RepartidorAvisosPuertas import RepartidorAvisosPuertas`; (2) en `__init__`, después de `self.rutas = RutasHaciaJugador(self.grafo, self.historial)`: `self.mapa = MapaConocido(mazmorra, jugador, self.historial)`; (3) **reemplazar** `self.mazmorra.observador_puertas = self.rutas` por `self.mazmorra.observador_puertas = RepartidorAvisosPuertas([self.rutas, self.mapa])`; (4) en `iniciar()`, después de `self.rastro.marcar(self.jugador.Sala_Actual, 0)`: `self.mapa.iniciar(self.jugador.Sala_Actual)`; (5) en `mover_jugador()`, justo después de `self.jugador.Sala_Actual = destino`: `self.mapa.entrar(destino, self.efectos.tiene(self.jugador, "antorcha"))`. Ya no bloquea nada.
- [x] T003 **(coordinar con el integrante 1)** *Confirmado por el integrante 1 el 14/11: las dos líneas de `Logic/PartidaGuardada.py` las escribe el integrante 2, con sus pruebas (T040), y él las revisa antes del merge.* (FR-221, FR-223) Confirmar con el integrante 1 quién escribe las dos líneas de `Logic/PartidaGuardada.py` (código P1 suyo según `git log`; el plan de la 004 asignó la extensión al integrante 2). Ya no bloquea T040.
- [ ] T004 **(coordinar con el integrante 1)** *Confirmado por el integrante 1 el 14/11: anota en su plan la lista de funciones privadas que usan la 002 y la 003 (`_salida_inversa`, `_cronometrar`, `_mejor_y_mediana`, `SEMILLA`, `_cuadricula_con_costos`, `_motor_con_cazadores`, `_centro`, `_peor`) y avisará antes de tocarlas. Falta solo su revisión cruzada del plan de la 002, que llega hoy (14/11).* Confirmar con el integrante 1, sin pedirle cambios a su código (plan, «Coordinación», puntos 3 a 6): que el mapa usa sin copiar el aviso `puerta_cambio` de `abrir_puerta` y `CierrePuerta.activar` (001 FR-114), `SalidaViva.costo` igualado (001 FR-101) y `Mazmorra._salida_inversa` para emparejar caras (H-7); que el bench reutiliza `_cronometrar`, `_mejor_y_mediana`, `SEMILLA` (`Logic/BenchLogica.py`) y `_cuadricula_con_costos`, `_motor_con_cazadores`, `_centro`, `_peor` (`Logic/BenchRutas.py`) sin modificarlos; y que `BenchRutas` reasigna `observador_puertas` en dos mediciones sin efecto para ellas (H-1), y que el data-model de la 001 queda desactualizado en `observador_puertas = self.rutas` (lo anota él si quiere). Se marca cuando llegue la revisión cruzada; si pide cambios al plan, se corrigen en un commit `plan(002)` propio. No bloquea nada.
- [ ] T005 **(coordinar con el integrante 3)** *H-3 confirmado por el integrante 3 el 14/11: «ir a <sala>» compara con `strip().casefold()` en los dos lados (hecho; el contrato (c) ya no dice «propuesta»). Queda pendiente su confirmación del resto del contrato.* (FR-217, FR-225; FR-251) Revisar y confirmar con el integrante 3 [contracts/contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md): el grafo (a) con la interfaz exacta de la 001 y la regla de «utilizable», el DTO de solo lectura (b), la búsqueda por nombre (c) y lo que no se ofrece (d). Confirmar además **H-3**: `buscar_exploradas` compara `nombre.strip().casefold()` con el nombre de la sala tratado igual. Anotar la respuesta en esta línea. Si pide cambios, corregir primero el contrato (y el plan) en un commit `plan(002)` propio. Bloquea T026.
- [ ] T006 **(coordinar con el integrante 3)** *Respuesta del integrante 3 del 14/11: H-2 lo resuelve ella en `Service/ArmadorEstado.py` y en la vista cuando `MapaConocido` esté en `origin/derek`; esta tarea queda esperando eso (aviso en T030).* (FR-204, FR-217, SC-202) Acordar con el integrante 3 **H-2**: hoy `EstadoJuegoDTO.sala.salidas[d].sala_destino` lleva el id real de destinos avistados y `View/EscenaJuego.py` lo usa. Ella decide cómo deja de llegar a la vista (por ejemplo, `sala_destino = None` para destinos no explorados en `Service/ArmadorEstado.py`) y si agrega el campo final `mapa_conocido: MapaConocidoDTO | None = None` a `DTO/EstadoJuegoDTO.py`. La prueba de SC-202 (T045) revisa también ese DTO y queda en `skip` con el motivo «H-2 pendiente del integrante 3» hasta que lo resuelva. El integrante 2 no edita esos archivos.
- [ ] T007 **(coordinar con el integrante 3)** *Respuesta del integrante 3 del 14/11: el texto del §1 y del §2 de su contrato de la 004 lo actualiza ella hoy; se marca cuando esté en su commit.* (FR-221, FR-223; 004 FR-420, FR-421) Acordar con el integrante 3 el texto del **§1 y del §2 de [contrato-linea-tiempo.md](../004-linea-tiempo/contracts/contrato-linea-tiempo.md)**. **§1**: `PartidaGuardadaDTO` gana dos campos al final, con `None` por defecto, en este orden: `mapa: MapaConocidoGuardadoDTO | None` y después `linea: LineaTiempoGuardadaDTO | None`, que **sigue siendo el último** (T002 de la 004); los demás campos no cambian de orden. **§2**: la cabecera de la versión 2 tiene 58 bytes (`<4sHQIQIIQIQI>`: magia, versión, offset y largo global, offset del índice, entradas, id mínimo, **offset y largo del mapa**, offset y largo de la línea), y cada punto de control del bloque de la línea se escribe en este orden: su `acciones_completadas`, su **bloque global**, sus **salas** y el **bloque de su mapa**. Lo actualiza ella, o el integrante 2 con su visto bueno, en un commit `plan(004)` propio; el formato se implementa una sola vez en T039. Bloquea T039.
- [ ] T008 **(coordinar con el integrante 3)** *Respuesta del integrante 3 del 14/11: `Service/ArmadorResumen.py` ya acepta un mapa opcional; lo conecta a `motor.mapa.a_dto()` cuando exista `a_dto` (aviso en T049). También escribe su sección del plan de «ir a» al final de `plan.md`, en su propio commit.* (FR-223; 004 FR-405) Acordar con el integrante 3 que **T023 de la 004** (`Service/ArmadorResumen.py`) copie `mapa_conocido = motor.mapa.a_dto()` sobre el motor aparte (no el `MapaConocidoGuardadoDTO`, que no trae nombres). La prueba H4-4 (T042) queda en `skip` hasta que exista T023 de la 004. No bloquea nada.

---

## Fase 2: Base — DTO del mapa y núcleo de `MapaConocido` (bloquea todas las historias)

**Propósito**: las constantes y los DTO que leen Logic, Data y la vista, y el estado del mapa con sus dos únicas
escrituras, que registran su reversión en el historial (research R1 y R3).

**⚠️ Ninguna historia empieza antes de terminar esta fase.**

### Pruebas de la base ⚠️ (deben fallar primero)

- [ ] T009 [P] Escribir `tests/test_guardado_mapa.py` con las pruebas de `DTO/MapaConocidoDTO.py`: `test_fr201_fr208_constantes_del_mapa` (`DESCONOCIDA = 0`, `AVISTADA = 1`, `EXPLORADA = 2`, `SIN_OBSERVAR = 0`, `ABIERTA = 1`, `CERRADA = 2`), `test_fr219_dto_de_vista_inmutables_y_orden_de_campos` (`MapaConocidoDTO(salas)`, `SalaConocidaDTO(id, nombre, salidas)`, `SalidaConocidaDTO(costo, estado_puerta, destino)`, `MapaConocidoGuardadoDTO(estado_salas, caras)`, todas `@dataclass(frozen=True)`, en ese orden de campos), `test_fr221_guardado_a_diccionario_y_vuelta` (`{"estado_salas": [...], "caras": [...]}` y de vuelta, igual) y `test_fr221_desde_diccionario_copia_las_listas` (cambiar la lista del diccionario después no cambia el DTO).
- [ ] T010 [P] Escribir `tests/test_mapa_conocido_estados.py` con las pruebas del núcleo, usando `mapa_de_prueba` y `estados` de `tests/ayudas_mapa.py` (T001, ya escrito; fallan al importar `MapaConocido` hasta T012): `test_fr201_fr206_mapa_nuevo_todo_desconocido` (`estado` de largo S con todo `DESCONOCIDA`; `caras` de largo 4·S con todo `SIN_OBSERVAR`), `test_nfr201_consultas_estado_sala_y_cara` (`estado_sala(s)` y `estado_cara(s, d)` leen la casilla), `test_fr222_poner_igual_no_registra` (escribir el mismo valor no deja nada en el historial: `deshacer` después de cerrar el intervalo no cambia nada), `test_fr222_poner_distinto_registra_su_reversion` (con un `HistorialRetroceso` real: cambiar una casilla, `cerrar_intervalo`, `deshacer` → vuelve al valor anterior), `test_fr222_cambios_repetidos_vuelven_al_primer_valor` (la misma casilla cambia dos veces en un intervalo; `deshacer` la deja como antes de la acción), `test_nfr203_historial_none_no_registra` (con `historial=None` se escribe igual y no falla).

### Implementación de la base

- [ ] T011 [P] (FR-201, FR-204, FR-205, FR-208, FR-212, FR-219, FR-221) Crear `DTO/MapaConocidoDTO.py`, sin importar nada del proyecto, según [data-model.md](data-model.md) §1, §4 y §5: las seis constantes; `@dataclass(frozen=True) MapaConocidoDTO(salas: list[SalaConocidaDTO])` («Solo exploradas, en orden creciente de id»); `SalaConocidaDTO(id: int, nombre: str, salidas: list[SalidaConocidaDTO | None])` («Id real (solo de exploradas…)»; salidas: «4 posiciones (N, S, E, O); `None` si no hay salida»); `SalidaConocidaDTO(costo: int, estado_puerta: int, destino: int | None)` (costo: «Igualado (001 FR-101, FR-205); nunca el declarado por una sola cara»; `estado_puerta`: «`ABIERTA`, `CERRADA` o `SIN_OBSERVAR`: el **recordado** de la cara de esta sala»; `destino`: «Id si el destino está explorado; `None` si está avistado»); `MapaConocidoGuardadoDTO(estado_salas: list[int], caras: list[int])` con `a_diccionario()` y `desde_diccionario(d)`, que copian las listas con `list(...)`. Sin campos de contenido ni de estado real. Regla: «si en el futuro se agregan campos, van al final y con valor por defecto». Con type hints y docstring. Hace pasar T009.
- [ ] T012 (FR-201, FR-206, FR-218, FR-222, NFR-201, NFR-203) Crear `Logic/MapaConocido.py` con el núcleo, según [data-model.md](data-model.md) §2 y research R1 y R3: `MapaConocido(mazmorra: Mazmorra, jugador, historial: HistorialRetroceso | None)`; `estado = [DESCONOCIDA] * S` y `caras = [SIN_OBSERVAR] * (4 * S)` con S = `len(mazmorra.salas)`; `estado_sala(sala) -> int` y `estado_cara(sala, direccion) -> int` (O(1)); privados `_poner_estado(sala, valor)` y `_poner_cara(c, valor)`: si el valor es igual, nada; si no, `historial.registrar_cambio(deshacer)` con una función que tiene **ligados** el índice y el valor anterior (no una `lambda` que lea variables del bucle) y después escribe; si `historial` es `None`, solo escribe. Importa las constantes de `DTO/MapaConocidoDTO.py`; no importa Data ni Service. Con type hints y docstring. Hace pasar T010.
- [ ] T013 Correr `python tests/correr_pruebas.py`: todo en verde, incluidas las pruebas de las features 001, 003 y 004.

**Punto de control**: el estado del mapa existe y cada escritura se puede deshacer con el pergamino.

---

## Fase 3: Historia 1 — El jugador solo ve lo que ha explorado (P1) 🎯 MVP

**Objetivo**: `iniciar` y `entrar` (sin antorcha) mantienen los tres estados de cada sala (FR-201 a FR-206) y nada
más escribe el mapa (FR-218).

**Prueba independiente**: con criptas pequeñas armadas a mano, una `Mazmorra` y un jugador de prueba, comparar el
estado de cada sala después de cada entrada con el esperado.

### Pruebas de la historia 1 ⚠️ (deben fallar primero)

- [ ] T014 [US1] Agregar a `tests/test_mapa_conocido_estados.py` los escenarios de la historia 1, con `mapa_de_prueba` de T001: `test_h1_1_a1_fr201_fr202_fr204_fr205_fr206_sala_inicial_explorada` (después de `iniciar(A)`: A explorada y sus caras observadas con el estado real; B y C avistadas; todas las demás desconocidas), `test_h1_2_a2_fr203_entrar_explora_y_avista` (entrar a B: B explorada, D y E avistadas), `test_h1_3_a13_fr204_salida_sin_vuelta_avista_su_destino` (A → F sin vuelta: F avistada), `test_h1_5_a3_fr217_fr218_precarga_y_esqueleto_no_cambian_el_mapa` (con el esqueleto ya cargado una sola vez al armar la `Mazmorra`, simular la precarga con lo que de verdad hace: cargar en la `Mazmorra` el contenido de la sala desconocida G con `cargar_contenido`, **sin volver a cargar el esqueleto**: `estados(mapa)` no cambió y G sigue desconocida), `test_h1_6_a2_fr203_volver_no_baja_el_estado` (explorar B, volver a A: B sigue explorada). H1-7 (A41) pasa por el motor y se escribe en T031. Casos borde y invariantes: `test_fr203_vecina_de_si_misma_y_varias_salidas_una_sola_vez` (cada casilla cambia una sola vez: el historial tiene un cambio por casilla), `test_fr203_sala_de_origen_no_cambia`, `test_fr203_fr204_invariantes_del_mapa` (después de cada entrada de un recorrido: toda salida de una explorada lleva a una no desconocida; toda avistada es destino de una salida de una explorada; ningún estado bajó) y `test_fr204_origen_de_salida_sin_vuelta_hacia_explorada_sigue_desconocida`.

### Implementación de la historia 1

- [ ] T015 [US1] (FR-202, FR-203, FR-204, FR-205, FR-207, NFR-202) En `Logic/MapaConocido.py`, según [data-model.md](data-model.md) §2 y research R2: privado `_explorar(sala)` («Si ya está `EXPLORADA`, no hace nada. Si no, `_poner_estado(sala, EXPLORADA)` y, por cada salida de `sala` hacia una sala v que existe con `estado[v] == DESCONOCIDA`, `_poner_estado(v, AVISTADA)`»); privado `_observar_puertas(sala)` (por cada dirección d con salida s hacia una sala que existe: `_poner_cara(sala*4 + d, CERRADA si s.cerrada si no ABIERTA)`; si `mazmorra._salida_inversa(sala, s.destino)` existe, su dirección d′ por **identidad** entre las 4 salidas del destino, como `PartidaGuardada._cargar_evento`, y `_poner_cara(s.destino*4 + d′, …)` con su estado real; una salida sin vuelta de otra sala **hacia** `sala` no se observa); `iniciar(sala)` = `_explorar` + `_observar_puertas`; `entrar(sala, antorcha: bool)` = `_explorar(sala)` + `_observar_puertas(sala)` (la rama de la antorcha llega en T021). Direcciones en orden 0 a 3. O(g). Hace pasar T014.
- [ ] T016 [US1] Correr `python tests/correr_pruebas.py`. **Parar y validar**: los escenarios H1-1, H1-2, H1-3, H1-5 y H1-6 pasan (H1-7 llega con T031 y T033).

---

## Fase 4: Historia 2 — El mapa recuerda las puertas como las vio por última vez (P1)

**Objetivo**: el estado recordado por cara (FR-207 a FR-209) y la re-observación cuando cambia una puerta de la sala
del jugador (`puerta_cambio`). Lo que se ofrece a «ir a» (H2-5 y la mitad de H2-6) está en la fase 7.

**Prueba independiente**: cambiar una puerta con el jugador lejos y con el jugador en una de sus salas, y comprobar
el estado recordado de cada cara.

### Pruebas de la historia 2 ⚠️ (deben fallar primero)

- [ ] T017 [US2] Escribir `tests/test_mapa_conocido_puertas.py`: `test_h2_1_apendiceB_caso2a_fr207_fr209_puerta_recordada_abierta_se_actualiza` (el mapa recuerda abierta B–C, en realidad está cerrada; el jugador llega a B → recordada cerrada; y lo mismo llegando a C), `test_h2_2_a4_fr208_cierre_automatico_lejos_sigue_abierta` (con el jugador de prueba en D: cerrar las dos caras de A–B en la `Mazmorra` y llamar a `mapa.puerta_cambio(a, b)` como haría el aviso → el mapa la sigue recordando abierta), `test_h2_3_a15_fr207_cambio_con_el_jugador_en_la_sala` (jugador en B; se cierra una puerta de B y llega `puerta_cambio` → recordada cerrada desde ese momento), `test_h2_4_a16_fr204_fr207_salida_sin_vuelta_solo_desde_su_origen` (A → F sin vuelta: desde A se observa y queda cerrada; desde F no se observa y se conserva lo visto desde A; la sala X con salida sin vuelta hacia A sigue desconocida y esa cara no se observa), `test_h2_6_a42_fr207_fr208_caras_distintas_se_recuerdan_por_separado` (con `cara_cerrada_sin_llave(A, B)`: desde A o desde B, `estado_cara` de A hacia B es `CERRADA` y de B hacia A es `ABIERTA`), `test_fr207_en_la_sala_del_jugador_recordado_igual_a_real` (invariante 5 del data-model después de abrir y cerrar varias veces) y `test_fr207_puerta_cambio_sin_cambios_no_registra` (un aviso de una puerta lejana no deja nada en el historial). Las variantes de H2-2 y H2-3 con el motor se escriben en T031.

### Implementación de la historia 2

- [ ] T018 [US2] (FR-207, FR-209) En `Logic/MapaConocido.py`: `puerta_cambio(a: int, b: int) -> None` = `_observar_puertas(jugador.Sala_Actual)`; `a` y `b` no se usan (el aviso no identifica la puerta sin vuelta, research R2). O(1). Docstring con la invariante «mientras el jugador está en x, el recordado de cada cara con cara en x es el real». Hace pasar T017.
- [ ] T019 [US2] Correr `python tests/correr_pruebas.py`. **Parar y validar**: el caso 2a del Apéndice B pasa.

---

## Fase 5: Historia 3 — La antorcha explora las vecinas (P2)

**Objetivo**: con la antorcha encendida, entrar explora las vecinas sin ir más allá, sin contenido, sin despertar
nada y sin tiempo extra (FR-210 a FR-216).

**Prueba independiente**: entrar a la misma sala con la antorcha encendida y apagada y comparar el mapa; con el
motor, comparar enemigos, trampas y reloj.

### Pruebas de la historia 3 ⚠️ (deben fallar primero)

- [ ] T020 [US3] Escribir `tests/test_mapa_conocido_antorcha.py`: `test_h3_1_apendiceB_caso4_fr210_fr211_antorcha_explora_vecinas` (`entrar(B, True)`: B, C y D exploradas), `test_h3_2_a5_fr210_explora_a_traves_de_una_puerta_cerrada` (B → E con puerta cerrada con llave: E explorada), `test_h3_3_a6_fr214_antorcha_apagada_solo_avista`, `test_h3_4_a17_fr213_no_explora_mas_alla_de_las_vecinas` (H e I, destinos de C, avistadas y no exploradas), `test_h3_6_a19_fr205_fr207_fr212_puertas_de_la_vecina_sin_observar` (la cara B→C con el estado observado desde B; la cara C→J `SIN_OBSERVAR`), `test_h3_8_a43_fr210_fr214_entrar_con_y_sin_antorcha_en_el_mismo_instante` (en Logic, lo que decide H3-8 es el booleano que recibe `entrar`: desde el mismo mapa, `entrar(B, False)` deja las vecinas de B solo avistadas y `entrar(B, True)` las deja exploradas). La variante de H3-1 con el motor y H3-5 (A18), H3-7 (A20) y las dos variantes de H3-8 (A43) con el motor se escriben en T031. Casos borde: `test_fr210_vecina_ya_explorada_no_cambia_ni_registra`, `test_nfr202_cambios_proporcionales_a_lo_revelado` (una entrada con antorcha registra a lo sumo 5 cambios de exploración, 16 de avistamiento y 8 de caras, con un mapa chico y con uno de 1 024 salas casi todo explorado: la misma cantidad).

### Implementación de la historia 3

- [ ] T021 [US3] (FR-210, FR-211, FR-212, FR-213, FR-214, FR-215, NFR-202) En `Logic/MapaConocido.py`, rama de la antorcha de `entrar(sala, antorcha)`: después de `_explorar(sala)`, si `antorcha`, `_explorar(v)` para cada destino v de **cualquier** salida de `sala` (abierta o cerrada) que exista, en orden de dirección; después `_observar_puertas(sala)` (que observa también la cara de cada vecina hacia `sala`). No lee ni carga contenido, no toca enemigos ni trampas, no programa eventos ni consume tiempo; el mapa no conoce los efectos (el booleano lo pasa el motor, T002). Una vecina ya explorada se salta sin recorrer sus salidas. Costo O(1 + Σ g de las que pasan a exploradas). Hace pasar T020.
- [ ] T022 [US3] Correr `python tests/correr_pruebas.py`. **Parar y validar**: el caso 4 del Apéndice B pasa en Logic (su variante con el motor llega con T031 y T033).

---

## Fase 6: Historia 4 (parte 1) — El pergamino revierte el mapa (P2)

**Objetivo**: con el `HistorialRetroceso` real, revertir una acción deja el mapa exactamente como antes (FR-222,
NFR-203), sin copiar el mapa.

**Prueba independiente**: explorar con y sin antorcha, cerrar el intervalo y deshacer; comparar `estados(mapa)` con
el de antes de la acción.

### Pruebas del pergamino ⚠️ (deben fallar primero)

- [ ] T023 [US4] Escribir `tests/test_mapa_conocido_partida.py` con los escenarios del pergamino, con un `HistorialRetroceso` real y `mapa_de_prueba`: `test_h4_1_apendiceB_caso5_fr222_pergamino_revierte_entrada_con_antorcha` (antes: B avistada, C desconocida, D avistada; `entrar(B, True)`, `cerrar_intervalo`, `deshacer` → B avistada, C desconocida, D avistada y el resto de `estados(mapa)` igual que antes de la entrada; la variante con el motor se escribe en T031), `test_h4_2_a8_fr222_pergamino_revierte_la_observacion` (el mapa recordaba abierta B→C; entrar a B la observa cerrada; deshacer → vuelve a recordarla abierta), `test_fr222_pergaminos_seguidos` (dos entradas y dos `deshacer`: cada uno devuelve el mapa al estado anterior a su acción), `test_fr222_pergamino_sin_cambios_del_mapa` (una acción que no cambió el mapa: deshacer no lo cambia) y `test_fr222_iniciar_no_se_deshace` (el conocimiento inicial se descarta con `descartar_intervalo_abierto`, como la preparación del motor: deshacer no vuelve la sala inicial a desconocida). **Excepción documentada al «falla primero»** (Principio X): estas pruebas cubren escenarios cuyo código ya llegó en T012 (la reversión por casilla, probada en T010), T015 y T021, así que pueden pasar desde que se escriben; si pasan, se deja constancia en el commit y T024 no cambia nada.

### Implementación del pergamino

- [ ] T024 [US4] (FR-222, NFR-203) Si alguna prueba de T023 falla, corregir **solo** `_poner_estado` / `_poner_cara` en `Logic/MapaConocido.py` (por ejemplo, una función de reversión que no tenía ligados el índice y el valor anterior). No se modifica `Logic/HistorialRetroceso.py` ni se agrega una copia del mapa. Hace pasar T023.
- [ ] T025 [US4] Correr `python tests/correr_pruebas.py`. **Parar y validar**: el caso 5 del Apéndice B pasa en Logic. `MapaConocido` está completo en Logic salvo `a_dto`, `buscar_exploradas`, `a_guardado` y `restaurar`.

---

## Fase 7: Contrato para el integrante 3 — `GrafoMapaConocido` y `buscar_exploradas` (historia 2)

**Objetivo**: lo que el mapa ofrece a «ir a» (FR-225, contrato (a), (c) y (d)), lo antes posible, para que el
integrante 3 empiece sus tareas desde T100.

**Prueba independiente**: con salas exploradas por entrada y por la antorcha, comparar `salidas`, `entradas` y la
búsqueda de la 001 sobre el grafo con un grafo filtrado a mano.

### Pruebas del contrato ⚠️ (deben fallar primero)

- [ ] T026 [US2] Escribir `tests/test_grafo_mapa_conocido.py` (depende de T005): `test_h2_5_a38_fr205_fr212_fr225_ofrece_solo_utilizables_con_costo_igualado` (lectura del hallazgo H-5: A, B y C exploradas con el jugador en otra sala; A–B recordada abierta y solo su cara en B declara costo 150; A–C `SIN_OBSERVAR`; A → D con D avistada: `salidas(A) == [(B, 150)]`, `salidas(B)` incluye `(A, 150)`, ni A→C ni A→D aparecen, y los ids son los reales), `test_h2_6_a42_fr208_fr225_solo_la_cara_de_origen_abierta_se_ofrece` (con `cara_cerrada_sin_llave(A, B)`: `salidas(A)` no tiene B; `salidas(B)` tiene A; `entradas(A)` tiene B y `entradas(B)` no tiene A), `test_fr225_interfaz_de_la_001` (`cantidad_salas() == len(Mazmorra.salas)`; pares `(sala, costo)`; listas vacías para salas no exploradas), `test_fr225_misma_ruta_que_paso_desde_cero_sobre_grafo_filtrado` (la búsqueda de la 001, `BusquedaCostoMinimo` / `paso_desde_cero`, sobre `GrafoMapaConocido` da el mismo paso, costo y desempate por menor id que sobre un grafo armado a mano con las salidas utilizables, en varias criptas con empates), `test_fr225_lee_el_mapa_en_vivo` (después de una observación nueva o de un `deshacer`, `salidas` cambia sin crear otro grafo, así que una búsqueda nueva por paso ve el conocimiento vigente), `test_fr217_grafo_no_lee_el_estado_real` (cambiar una puerta en la `Mazmorra` sin aviso no cambia `salidas`), y las de la búsqueda por nombre: `test_fr251_buscar_exploradas_cero_uno_y_dos` (`[]`, `[id]` y dos ids en orden creciente), `test_fr206_fr251_avistada_o_desconocida_con_el_mismo_nombre_no_cuenta`, `test_fr251_comparacion_strip_casefold` (H-3 confirmado en T005) y `test_fr220_buscar_exploradas_no_cambia_el_estado`.

### Implementación del contrato

- [ ] T027 [US2] (FR-205, FR-217, FR-225) Crear `Logic/GrafoMapaConocido.py`, según [data-model.md](data-model.md) §3 y el contrato (a): `GrafoMapaConocido(mapa: MapaConocido)`; `cantidad_salas()` = `len(mazmorra.salas)` (O(1)); `salidas(u)` = `[(v, costo)]` de las salidas **utilizables** de u (O(4)); `entradas(x)` = `[(u, costo)]` de las salidas utilizables que llegan a x (O(grado de entrada)), con una adyacencia inversa `_inversa` de pares (origen, dirección) del esqueleto armada una vez en O(S + E), como `GrafoEsqueleto`. «Utilizable»: «`estado[u] == EXPLORADA`, `estado[v] == EXPLORADA` y `caras[u*4 + d] == ABIERTA`; costo = `SalidaViva.costo` (igualado, 001 FR-101)». Lee `mapa.estado` y `mapa.caras` **en cada llamada** (no guarda referencias a los arreglos, porque `restaurar` los reemplaza). No consulta el estado real de ninguna puerta ni el contenido. Con type hints y docstring.
- [ ] T028 [US2] (FR-225, FR-251) En `Logic/MapaConocido.py`: `buscar_exploradas(nombre: str) -> list[int]`, ids de las salas **exploradas** cuyo nombre coincide con la comparación confirmada en T005 (`strip().casefold()` en los dos lados), en orden creciente de id, O(S), sin cambiar nada. El mapa **no** avisa a una búsqueda guardada (contrato (a); YAGNI, research R5): «ir a» empieza una búsqueda nueva por paso. Hace pasar T026.
- [ ] T029 [US2] Correr `python tests/correr_pruebas.py`.
- [ ] T030 **Aviso** al integrante 3: `GrafoMapaConocido` y `buscar_exploradas` están listos (sin aviso a una búsqueda guardada: una búsqueda nueva por paso, contrato (a)) y fijados por `tests/test_grafo_mapa_conocido.py`, según el contrato confirmado en T005. Puede empezar sus tareas de «ir a» (desde T100) con `GrafoMapaConocido(mapa)` y `MapaConocido` + `JugadorPrueba` de `tests/ayudas_mapa.py`, sin esperar al motor; el acceso por `contexto.motor.mapa` llega con T033. El aviso también le dice que **`MapaConocido` ya está en `origin/derek`** (subirlo antes de avisar), así que puede resolver **H-2** en `ArmadorEstado` y en la vista (T006).

---

## Fase 8: `RepartidorAvisosPuertas` y el cambio del motor (historia 2)

**Objetivo**: que el aviso de puertas de la 001 llegue a las rutas del cazador y al mapa sin modificar la `Mazmorra`
(FR-207; 001 FR-114), y conectar el mapa al motor (lo escribe el integrante 2; lo revisa el integrante 1, acuerdo del
14/11).

**Prueba independiente**: un repartidor con dos observadores falsos reenvía cada aviso en orden; con el motor,
`mazmorra.observador_puertas` es el repartidor, los escenarios con el motor de las historias 1 a 4 pasan y las pruebas
del cazador siguen en verde.

### Pruebas del repartidor y del motor ⚠️ (deben fallar primero)

- [ ] T031 [US2] Lleva la etiqueta [US2] por el repartidor, pero **también tiene pruebas de H1, H3 y H4** (las variantes con el motor; ver la tabla de cobertura). Escribir, **antes** de T032 y T033, las pruebas del repartidor y todas las que pasan por el motor (con `motor_con`, `poner_enemigo` y las fichas de `tests/ayudas_terreno.py`), sin `skipTest`; las del motor fallan hasta T033. En `tests/test_mapa_conocido_puertas.py`: `test_fr207_repartidor_reenvia_en_orden` (dos observadores falsos reciben `puerta_cambio(a, b)` en el orden de la lista), `test_fr207_repartidor_lista_vacia_no_falla`, `test_fr207_fr114_motor_asigna_el_repartidor` (`motor.mazmorra.observador_puertas` es un `RepartidorAvisosPuertas` cuyos observadores son `[motor.rutas, motor.mapa]`), `test_fr202_motor_iniciar_explora_la_sala_inicial` (después de `motor.iniciar()`, la sala inicial está explorada y el historial no puede deshacerla), `test_h2_2_a4_fr208_motor_cierre_automatico` (con el `CierrePuerta` real, la puerta A–B se cierra sola con el jugador en D: el mapa la sigue recordando abierta) y `test_h2_3_a15_fr207_motor_aviso_por_el_repartidor` (`abrir_puerta` / `CierrePuerta` de una puerta de la sala del jugador llegan al mapa por el repartidor). En `tests/test_mapa_conocido_estados.py` **(historia 1)**: `test_h1_7_a41_fr218_cazador_no_cambia_el_mapa` (un cazador de `ficha_cazador` que se mueve por salas desconocidas y pasa por puertas nunca observadas: `estados(motor.mapa)` igual antes y después). En `tests/test_mapa_conocido_antorcha.py` **(historia 3)**: `test_h3_1_apendiceB_caso4_fr210_fr211_motor_antorcha_no_despierta` (la antorcha encendida, un enemigo dormido en C y una trampa en D: el enemigo sigue dormido, la trampa no se activa, el contenido de C y D no se cargó para el jugador y el reloj avanza lo mismo que la misma entrada sin antorcha), `test_h3_5_a18_fr216_entrar_despues_revela_y_aplica_p1` (C explorada por la antorcha con un enemigo dormido; al entrar a C se revela su contenido y el enemigo se comporta según P1 §2.4), `test_h3_7_a20_fr210_fr215_encender_sin_moverse_no_cambia` (`usar` la antorcha estando en B no cambia `estados(motor.mapa)` ni el historial; la entrada siguiente sí explora), `test_h3_8_a43_fr210_fr214_fin_programado_antes_que_la_entrada` y `test_h3_8_a43_fr210_fr214_fin_programado_despues_de_la_entrada` (el fin de la antorcha y la entrada a B en el mismo instante t; 001 FR-108). **Receta**, según `Logic/EventoPorg.py` (`EventoProgramado.__lt__` ordena por `tiempo` y, con el mismo tiempo, por `secuencia`) y `Logic/ColaEventos.py` (`programar` da secuencias crecientes en el orden en que se programa): **antes**: con el jugador en A y una antorcha en el inventario cuya `duracion` es `motor.jugador.Calcu_de_Intervalo(Motor.COSTO_USAR)` (50 con velocidad 100), `motor.usar(antorcha)`: `GestorEfectos.aplicar` programa el fin en `t = reloj + duracion` y después `terminar_accion_jugador` programa la acción del jugador en el mismo `t`, con secuencia mayor; `avanzar_hasta_jugador` atiende primero el fin (`Antorcha.activar` quita el efecto) y luego devuelve el turno; `mover_jugador` hacia B entra con `efectos.tiene(jugador, "antorcha")` falso → las vecinas de B solo quedan avistadas. Es el flujo normal del juego. **Después**: con `motor.usar` no se puede, porque el efecto siempre se programa antes que la acción siguiente del jugador; la prueba lo arma así: `motor.esperar()` (programa la acción del jugador en `t = jugador.Evento_pendiente.tiempo`) y enseguida `motor.efectos.aplicar(Antorcha(motor.jugador, t - motor.reloj))`, que programa el fin en el mismo `t` con secuencia **mayor**; `avanzar_hasta_jugador` devuelve el turno antes de atender el fin, y `mover_jugador` hacia B entra con la antorcha encendida → las vecinas de B quedan exploradas. Las dos variantes se pueden armar con certeza; la decisión en Logic se prueba además con `MapaConocido.entrar(sala, antorcha)` en T020. En `tests/test_mapa_conocido_partida.py` **(historia 4)**: `test_h4_1_apendiceB_caso5_fr222_motor_leer_pergamino` (leer un pergamino en el motor revierte la entrada con antorcha, junto con la posición y el reloj).

### Implementación y coordinación

- [ ] T032 [US2] (FR-207; 001 FR-114) Crear `Logic/RepartidorAvisosPuertas.py`, según [data-model.md](data-model.md) §7: `RepartidorAvisosPuertas(observadores: list)` que guarda una copia `list(observadores)` en orden fijo y `puerta_cambio(a, b) -> None` que llama a `puerta_cambio(a, b)` de cada observador, en orden. O(cantidad de observadores). No importa `MapaConocido` ni `RutasHaciaJugador`. Con type hints y docstring. Hace pasar las dos primeras pruebas de T031.
- [ ] T033 **(coordinar con el integrante 1)** (FR-201, FR-202, FR-203, FR-207, FR-210 a FR-214; 001 FR-114) Escribir en `Logic/motorJuego.py` (acordado con el integrante 1 el 14/11; él lo revisa antes del merge) el cambio exacto de T002 y de la tabla «Cambios a código existente» del plan, y nada más: (1) imports `from Logic.MapaConocido import MapaConocido` y `from Logic.RepartidorAvisosPuertas import RepartidorAvisosPuertas`; (2) en `__init__`, después de `self.rutas = RutasHaciaJugador(self.grafo, self.historial)`: `self.mapa = MapaConocido(mazmorra, jugador, self.historial)`; (3) **reemplazar** `self.mazmorra.observador_puertas = self.rutas` por `self.mazmorra.observador_puertas = RepartidorAvisosPuertas([self.rutas, self.mapa])`; (4) en `iniciar()`, después de `self.rastro.marcar(self.jugador.Sala_Actual, 0)`: `self.mapa.iniciar(self.jugador.Sala_Actual)`; (5) en `mover_jugador()`, justo después de `self.jugador.Sala_Actual = destino`: `self.mapa.entrar(destino, self.efectos.tiene(self.jugador, "antorcha"))`. Sin type hints ni docstrings nuevos en el código de la primera entrega. Depende de las fases 3 a 7 y de T032. Hace pasar las pruebas del motor de T031; comprobar que `tests/test_terreno_cazador.py`, `tests/test_rutas_equivalencia.py` y las pruebas de la 003 y la 004 siguen en verde. Commit propio, revisado por el integrante 1 antes del merge.
- T034 *Eliminada el 14/11*: era quitar los `skipTest` de las pruebas del motor mientras se esperaba el cambio del integrante 1; con el acuerdo de T002 ya no hay esa espera. El número no se reutiliza.

**Punto de control**: el motor de la partida tiene `motor.mapa`; las historias 1, 2 y 3 pasan de punta a punta,
también con el motor.

---

## Fase 9: Historia 4 (parte 2) — El mapa se guarda y forma parte de la línea de tiempo (P2)

**Objetivo**: guardar y cargar el mapa idéntico (FR-221), en los puntos de control (FR-223) y en el binario versión 2
definido **una sola vez** con los bloques del mapa y de la línea (T002, T003 y T047 de la 004, que son del integrante
2); `--replay` da el mismo mapa (FR-224).

**Prueba independiente**: explorar, guardar, cargar y reproducir, y comparar `estados(motor.mapa)` casilla por
casilla.

### Pruebas del guardado ⚠️ (deben fallar primero)

- [ ] T035 [US4] *Se hace en dos momentos (orden de implementación, «Estrategia»): las cuatro primeras pruebas (DTO y `linea`) se escriben al adelantar el guardado, justo después de la fase 2, antes de T036; las de `a_guardado` y `restaurar` se agregan después de la fase 3, justo antes de T037, porque `restaurar(None)` usa `_explorar` y `_observar_puertas` (T015).* Agregar a `tests/test_guardado_mapa.py`: `test_fr221_partida_guardada_mapa_antes_de_linea` (`dataclasses.fields(PartidaGuardadaDTO)` termina en `mapa`, `linea`; los dos valen `None` por defecto), `test_fr221_partida_guardada_a_diccionario_y_vuelta_con_mapa` (con mapa y sin mapa; un diccionario sin la clave `"mapa"` da `None`), `test_t002_de_la_004_linea_ida_y_vuelta_por_diccionario` (con una `LineaTiempoGuardadaDTO` chica y con `None`), `test_t002_de_la_004_sin_ciclo_de_imports` (en un proceso aparte, `import DTO.PartidaGuardadaDTO` solo y `import DTO.LineaTiempoDTO` solo funcionan), `test_fr221_a_guardado_copia_los_arreglos` (cambiar el mapa después no cambia el DTO), `test_fr223_restaurar_dos_veces_del_mismo_dto` (restaurar, explorar, restaurar otra vez del mismo DTO: el mismo mapa, y el DTO no cambió, riesgo R-4), `test_fr221_restaurar_con_largos_distintos_es_value_error` (con el motivo), `test_fr221_restaurar_no_registra_en_el_historial`, `test_fr221_restaurar_reemplaza_el_mapa_en_curso` (un mapa con más salas exploradas que el DTO queda igual al DTO, FR-221) y `test_fr202_fr221_restaurar_none_arma_el_mapa_inicial_desde_la_sala_del_jugador` (con el jugador de prueba en X y un mapa con salas exploradas: `restaurar(None)` deja X explorada, los destinos de sus salidas avistados, sus caras observadas con el estado real y todo lo demás desconocido o sin observar, igual que `iniciar(X)` sobre un mapa nuevo).

### Implementación del DTO y de `MapaConocido`

- [ ] T036 [US4] (FR-221; **T002 de la 004**) En `DTO/PartidaGuardadaDTO.py` (integrante 2), en la misma tarea: campo `mapa: MapaConocidoGuardadoDTO | None = None` al final y **antes de `linea`**, y campo `linea: "LineaTiempoGuardadaDTO | None" = None` como **último** campo (anotado con texto, que `dataclasses` no evalúa); `a_diccionario` agrega `"mapa"` (`None` o el diccionario) y `"linea"`; `desde_diccionario` usa `d.get("mapa")` y `d.get("linea")`, e importa `LineaTiempoGuardadaDTO` **dentro** de `desde_diccionario` para no formar el ciclo `LineaTiempoDTO` → `PartidaGuardadaDTO` → `LineaTiempoDTO` (research R4). Los demás campos no cambian de orden. Comprobar que `tests/TestPartidaGuardadaDTO.py` sigue en verde. Hace pasar las cuatro primeras pruebas de T035.
- [ ] T037 [US4] (FR-221, FR-223, NFR-203) En `Logic/MapaConocido.py`: `a_guardado() -> MapaConocidoGuardadoDTO` con copias `list(self.estado)` y `list(self.caras)` (O(S)); `restaurar(dto: MapaConocidoGuardadoDTO | None) -> None`: con un DTO, comprueba `len(dto.estado_salas) == S` y `len(dto.caras) == 4 * S` (si no, `ValueError` con el motivo, riesgo R-8) y copia los dos arreglos con `list(...)`, reemplazando el mapa en curso, **sin registrar en el historial**; con `None`, pone todo en `DESCONOCIDA` / `SIN_OBSERVAR` y arma el mapa inicial desde `jugador.Sala_Actual` con lo mismo que `iniciar` (`_explorar` + `_observar_puertas`; FR-202). Así `PartidaGuardada.cargar` no necesita `if` (T040). Depende de T015. Hace pasar el resto de T035.

### Pruebas e implementación del binario versión 2

- [ ] T038 [US4] Agregar a `tests/test_guardado_mapa.py` las pruebas del binario (también son las de **T003 y T047 de la 004**): `test_fr221_binario_v2_ida_y_vuelta_con_mapa`, `test_fr221_binario_v2_mapa_none_largo_cero`, `test_t003_de_la_004_binario_v2_ida_y_vuelta_con_linea` (cada punto de control con su mapa), `test_t003_de_la_004_binario_v2_linea_none_largo_cero`, `test_t047_de_la_004_cargar_sala_no_lee_mapa_ni_linea` (con bytes inválidos en los bloques del mapa y de la línea, `cargar_sala` igual devuelve la sala), `test_t047_de_la_004_archivo_v1_rechazado` (`ErrorGuardado` con la versión leída y la esperada, sin cargar nada; FR-421 de la 004), `test_t047_de_la_004_archivo_v1_deja_intacta_la_partida_actual` (con una partida en curso, intentar cargar un archivo de la versión 1 por `ServicioGuardado` falla y la partida actual queda igual: mismo motor, reloj, `estados(motor.mapa)` y historial; contrato de la 004 §2), `test_t003_de_la_004_linea_con_formato_invalido_es_error_guardado` (cada restricción al leer del §1 del contrato de la 004: `k` < 1, acciones fuera de orden de `tiempo`, puntos que no crecen estrictamente en `acciones_completadas` o fuera de rango, más de `k` acciones entre dos puntos sin pergamino de por medio, punto con `partida.linea` distinto de `None` → `ErrorGuardado`), `test_fr221_binario_cabecera_de_58_bytes` y `test_fr221_bytes_del_mapa_invalidos_son_error_guardado` (estado fuera de {0, 1, 2}, un par de bits de cara fuera de {0, 1, 2}, largo que no coincide, offset fuera de la zona anterior al índice). En `tests/TestGuardadoBinario.py` (archivo del integrante 2 según `git log`), cambiar **solo** la aserción de la línea 253, `(b"CRPT", 1)` → `(b"CRPT", 2)`.
- [ ] T039 [US4] (FR-221; **T003 de la 004**; 004 FR-420, FR-421) En `Data/GuardadoBinario.py`, según [data-model.md](data-model.md) §6 y el §2 acordado en T007 (que la versión 2 se defina **una sola vez**): `VERSION_FORMATO = 2`; `_CABECERA = struct.Struct("<4sHQIQIIQIQI")` (58 bytes: «magia, versión (= 2), offset y largo global, offset del índice, entradas, id mínimo, offset y largo del mapa, offset y largo de la línea»); el bloque global sin mapa ni línea (mismo formato que en la versión 1); `_codificar_mapa` / `_leer_mapa`: «`I` cantidad S · `S` bytes de estado · `S` bytes de caras (bits 0-1 = N, 2-3 = S, 4-5 = E, 6-7 = O)», «Largo 0 = `mapa` es `None`»; el bloque de la línea con los escritores y lectores primitivos de hoy, y cada punto de control en este orden: su `acciones_completadas`, su bloque global, sus salas y el bloque de su mapa con el **mismo** `_codificar_mapa` / `_leer_mapa` (§2 acordado en T007); validación solo de formato del mapa («estado ∈ {0, 1, 2}; cada par de bits ∈ {0, 1, 2}; largo exacto; offset y largo dentro de la zona anterior al índice. Si no, `ErrorGuardado`») y, al leer la línea, las restricciones al leer del §1 del contrato de la 004 para `LineaTiempoGuardadaDTO` (`k ≥ 1`; `acciones` en orden creciente de `tiempo`; `puntos` en orden estrictamente creciente de `acciones_completadas`, cada una entre 0 y la cantidad de acciones, y a lo sumo `k` acciones entre dos puntos consecutivos salvo después de un pergamino; el `partida.linea` de cada punto es `None`): un formato inválido es `ErrorGuardado`; `cargar` lee el global, el mapa y la línea; `cargar_sala` sigue leyendo solo la cabecera, una entrada del índice y el bloque de esa sala. La versión 1 se rechaza en `_leer_cabecera` antes de interpretar el resto. Hace pasar T038; `tests/TestGuardadoBinario.py` sigue en verde.

### Pruebas e implementación de `PartidaGuardada`

- [ ] T040 [US4] **(coordinar con el integrante 1)** (FR-221, FR-223) Escribir en `Logic/PartidaGuardada.py` (acordado con el integrante 1 el 14/11, T003; él lo revisa antes del merge). Primero las pruebas, que fallan, en `tests/test_mapa_conocido_partida.py`: `test_h4_3_a7_fr221_guardar_y_cargar_conserva_el_mapa` (salas exploradas por entrada y por la antorcha, puertas recordadas distintas del real; `PartidaGuardada.guardar` → `GuardadoBinario` → `cargar`: `estados(motor.mapa)` idéntico), `test_fr221_cargar_con_mapa_none_deja_el_mapa_inicial_desde_la_sala_del_jugador` (un `PartidaGuardadaDTO` armado a mano con `mapa = None` y el jugador en la sala X: `cargar` no lanza error; X queda explorada, los destinos de sus salidas avistados, todo lo demás desconocido y sus caras observadas, como FR-202 con la sala de inicio; `deshacer` no lo revierte) y `test_fr223_punto_de_control_lleva_el_mapa`. Cambio exacto: (1) en `guardar`, argumento nuevo `mapa=motor.mapa.a_guardado()` en el `PartidaGuardadaDTO(...)`; (2) en `cargar`, **una sola línea** antes de `motor.historial.descartar_intervalo_abierto()`: `motor.mapa.restaurar(partida.mapa)`, **sin `if` ni `raise`**. El caso `None` lo resuelve `restaurar(None)` (T037); `cargar` no gana comportamiento nuevo, porque nunca rechaza una partida por el mapa (los guardados reales de la versión 2 y los puntos de control siempre traen el mapa; `None` solo aparece en DTOs armados a mano por pruebas de otros integrantes, riesgo R-9). Nada más en ese archivo. Depende de T033, T037 y T039. Comprobar que `tests/test_partida_guardada.py`, `tests/test_servicio_guardado.py`, `tests/test_controlador_backend.py`, `tests/TestGuardadoBinario.py` y las pruebas de la 004 siguen en verde sin cambiarlas. Commit propio, revisado por el integrante 1 antes del merge.
- [ ] T041 [US4] Agregar a `tests/test_mapa_conocido_partida.py`: `test_h4_5_a10_fr224_replay_da_el_mismo_mapa` (una partida con entradas con y sin antorcha y un pergamino; su `partida.log` **con líneas `# ir a <sala>`** (T071 de la 004) reproducido con `ServicioReplay` y con `--replay … --hasta t`: `estados(motor.mapa)` idéntico al de la partida original en ese instante) y `test_sc205_misma_partida_mismo_mapa_en_cada_accion` (dos ejecuciones con la misma cripta, semilla y acciones comparan los dos arreglos casilla por casilla en cada acción). Dependen de T033 y T040. No necesitan código nuevo: pasan por el mismo motor (research R6). **Excepción documentada al «falla primero»** (Principio X): cubren escenarios cuyo código ya llegó en T033 y T040, así que pueden pasar desde que se escriben.
- [ ] T042 [US4] Agregar a `tests/test_mapa_conocido_partida.py` `test_h4_4_a9_fr223_historia_muestra_el_mapa_de_ese_instante` (en la acción 4 el jugador está en A con B avistada; en la acción 6 explora B; `historia #4` → el `ResumenHistoriaDTO.mapa_conocido` es un `MapaConocidoDTO` sin B entre las exploradas y con la salida hacia B con `destino = None`; y nada de acciones revertidas). Guarda propia: `self.skipTest("pendiente: T023 de la 004 (Service/ArmadorResumen.py, integrante 3)")` si no existe `Service/ArmadorResumen.py`; T050 la quita.
- [ ] T043 **Aviso** al integrante 3, **adelantado**: se manda justo después de T039, que se hace después de la fase 2 y antes de las fases 3 a 7, con su commit propio («Estrategia»). `PartidaGuardadaDTO.mapa` y `linea` (T036, **T002 de la 004**) y `GuardadoBinario` versión 2 con los bloques del mapa y de la línea (T039, **T003 de la 004**) están listos, con sus pruebas. Avisarle que **las pruebas de T003 y T047 de la 004 están en `tests/test_guardado_mapa.py`** (no en `tests/TestGuardadoBinario.py`, como decía T003 de la 004); en `tests/TestGuardadoBinario.py` solo cambió la aserción de la versión (1 → 2). Puede marcar como hechas T002, T003 y T047 de la 004 y seguir con sus tareas que dependen del guardado (T043 a T048 de la 004); y, si no lo hizo, actualizar el §1 y el §2 de su contrato con el texto de T007.
- [ ] T044 [US4] Correr `python tests/correr_pruebas.py`. **Parar y validar**: H4-3 y H4-5 pasan; H4-4 figura como `skip` de T023 de la 004.

---

## Fase 10: Historia 5 — La vista del mapa conocido (P3)

**Objetivo**: `MapaConocido.a_dto()`, el único DTO que la interfaz y el resumen usan para el mapa (FR-217, FR-219,
FR-220), y la comprobación automática de SC-202. El comando y el dibujo son del integrante 3.

**Prueba independiente**: después de explorar, comparar el `MapaConocidoDTO` con las salas, salidas, costos y
puertas esperados, y comprobar que no aparece nada de una sala desconocida ni la identidad de una avistada.

### Pruebas de la historia 5 ⚠️ (deben fallar primero)

- [ ] T045 [US5] Escribir `tests/test_mapa_conocido_vista.py`: `test_h5_1_a11_fr219_muestra_exploradas_y_avistadas_sin_desconocidas` (A y B con sus salidas, costos y estado recordado; C, D y E solo como `destino = None`; ningún id de sala desconocida en el DTO), `test_h5_2_a21_fr208_fr219_muestra_el_recordado_no_el_real`, `test_h5_3_a22_fr211_fr212_fr219_explorada_por_antorcha_sin_contenido_y_sin_observar` (nombre y salidas sí; `estado_puerta = SIN_OBSERVAR` en sus puertas nunca observadas; el DTO no tiene campos de contenido; cubre también «el mapa muestra el nombre y las salidas de C y D, pero no su contenido» de H3-1), `test_h5_4_a12_fr220_ver_el_mapa_no_altera_la_partida` (`a_dto()` no cambia `estados(mapa)` ni el historial), `test_h5_4_a12_fr220_motor_reloj_sin_cambios` (con el motor en t = 300: el reloj sigue en 300 y el historial igual; lo de `partida.log` es del comando del integrante 3), `test_h5_5_a23_fr204_fr219_dos_salidas_a_la_misma_avistada` (dos `destino = None` independientes; al explorar C, los dos tienen el id de C), `test_h5_6_a39_fr205_fr219_costo_igualado` (A→B 150, B→A 150, A→C 100), `test_h5_7_a40_fr202_fr217_reporte_con_forzar_no_cambia_el_mapa` (iniciar con `ServicioResolubilidad.iniciar_partida_nueva(..., forzar=True)` de la 003 una cripta no resoluble: el mapa tiene solo la sala inicial explorada y sus vecinas avistadas, con las caras iguales que sin reporte; guarda propia si `Service/ServicioResolubilidad.py` de la 003 no existe todavía, con ese motivo, que se quita cuando exista) y `test_sc202_doscientas_acciones_sin_datos_de_desconocidas` (partida de al menos 200 acciones con y sin antorcha, con `motor_con`: en cada acción, el `MapaConocidoDTO` no contiene ids, nombres ni salidas de salas desconocidas ni ids de avistadas; también el `ResumenHistoriaDTO` si existe `Service/ArmadorResumen.py` y el `EstadoJuegoDTO` de `ArmadorEstado` (H-2); para la parte del `EstadoJuegoDTO`, `self.skipTest("pendiente: H-2 del integrante 3 (sala_destino de destinos no explorados en EstadoJuegoDTO)")` hasta T050). Agregar a `tests/test_mapa_conocido_estados.py` `test_h1_4_a14_fr204_fr217_avistada_solo_muestra_su_existencia` (B avistada: en el DTO solo aparece como `destino = None` en la salida de A; no aparecen su nombre, sus salidas, sus costos, sus puertas ni su contenido).

### Implementación de la historia 5

- [ ] T046 [US5] (FR-204, FR-205, FR-211, FR-212, FR-217, FR-219, FR-220) En `Logic/MapaConocido.py`: `a_dto() -> MapaConocidoDTO`, según [data-model.md](data-model.md) §4 y el contrato (b): recorre los ids en orden creciente (sin ordenar) y, por cada sala **explorada**, arma `SalaConocidaDTO(id, nombre, salidas)` con 4 posiciones; cada salida que existe es `SalidaConocidaDTO(costo=SalidaViva.costo (igualado), estado_puerta=caras[sala*4 + d], destino=id si el destino está explorado, si no None)`; `None` si no hay salida en esa dirección. Nunca lee el estado real de una puerta ni el contenido. No consume tiempo, no registra nada ni cambia estado. O(S). Hace pasar T045 (salvo las que tienen guarda).
- [ ] T047 [US5] Correr `python tests/correr_pruebas.py`.

### Coordinación de la historia 5

- [ ] T048 [US5] **(coordinar con el integrante 3)** **Aviso** y pedido al integrante 3: `MapaConocido.a_dto()` está listo y fijado por `tests/test_mapa_conocido_vista.py` (contrato (b)). Pedirle, en sus archivos (`UIController/…`, `View/…`, `Service/ArmadorEstado.py`, `DTO/EstadoJuegoDTO.py`): (1) el **comando de ver el mapa** con `contexto.motor.mapa.a_dto()`, que no consume tiempo, no cuenta como acción, **no se registra en `partida.log`** y no pasa por el historial (FR-219, FR-220), disponible también con la partida terminada; (2) el **dibujo** del mapa con el `MapaConocidoDTO` (cada `destino = None` como «sala sin explorar detrás de esta salida», «sin observar» como tal; §3.3, §7.3); (3) resolver **H-2** según lo acordado en T006, y, si lo decide, el campo final `mapa_conocido: MapaConocidoDTO | None = None` en `EstadoJuegoDTO`; (4) **la prueba automática** de que el comando de ver el mapa **no se registra en `partida.log`**, no consume tiempo, no cuenta como acción y no cambia el historial ni ningún estado (FR-220, escenario H5-4), en sus archivos de prueba, con el nombre `test_h5_4_a12_fr220_…` para que figure en la cobertura. Comprobar juntos con [quickstart.md](quickstart.md) §2, pasos 1 a 8. El integrante 2 no edita esos archivos.
- [ ] T049 [US4] **(coordinar con el integrante 3)** **Aviso** al integrante 3: con `a_dto()` (T046) y `motor.mapa` (T033) listos, puede hacer **T023 de la 004** con `mapa_conocido = motor.mapa.a_dto()` sobre el motor aparte, según lo acordado en T008.
- [ ] T050 Cuando el integrante 3 termine T023 de la 004 y H-2: quitar la guarda de T023 de la 004 de `test_h4_4_a9_fr223_…` (T042) y la de H-2 de `test_sc202_…` (T045), y correr `python tests/correr_pruebas.py`: las dos pasan. Si `test_sc202_…` falla por el `EstadoJuegoDTO`, avisarle con el caso que falla (el integrante 2 no edita `ArmadorEstado`).

**Punto de control**: las historias 1 a 5 pasan de punta a punta, salvo lo que espera al integrante 3 (con su motivo).

---

## Fase 11: Bench B1 a B11 (NFR-201 a NFR-205, SC-203, SC-204, SC-206, SC-207)

**Propósito**: evidencia de rendimiento con cuadrículas sintéticas deterministas por semilla de 100, 1 024 y 10 000
salas (Principio VIII, research R7). `--bench` no inicia partidas ni instancia la vista.

- [ ] T051 Escribir `tests/test_bench_mapa.py` (tamaños chicos; los umbrales de tiempo se leen en la tabla, no en pruebas): `test_nfr204_cuadriculas_deterministas_por_semilla` (misma semilla → mismas salas, costos y estados preparados), `test_r1_lista_de_exploradas_da_el_mismo_estado` (B3 responde lo mismo que `estado_sala`), `test_r2_recalcular_avistadas_da_el_mismo_mapa` (B5), `test_r3_copiar_y_restaurar_da_el_mismo_mapa` (B7), `test_nfr203_b6_vuelve_al_mapa_de_antes` (después de entrar, cerrar y deshacer, el mapa es el de antes), `test_nfr205_b8_mapa_igual_al_de_un_motor_de_control` (también en la variante con puertas que cambian, avisadas por `motor.mazmorra.observador_puertas`), `test_r5_b11_paso_igual_al_de_un_grafo_filtrado_a_mano` (el paso de `paso_desde_cero` sobre el `GrafoMapaConocido` de B11 es el mismo que sobre un grafo armado a mano con las salidas utilizables), `test_nfr204_medir_devuelve_b1_a_b11` (`BenchMapaConocido.medir` con tamaños chicos devuelve `ResultadoBenchDTO` del subsistema «mapa conocido» con los casos B1 a B11) y `test_nfr204_servicio_bench_incluye_mapa_conocido` (la lista por defecto de `Service/ServicioBench.py` incluye `BenchMapaConocido.medir` **después** de `BenchLogica.medir`, y de `BenchResolubilidad.medir` si está).
- [ ] T052 (NFR-201, NFR-203, NFR-204, SC-203) Crear `Logic/BenchMapaConocido.py` con las cuadrículas (lado 10, 32 y 100, con `_cuadricula_con_costos` de `Logic/BenchRutas.py` y costos de `random.Random(SEMILLA)` entre 1 y 300) y las mediciones **B1** (100 000 consultas de `estado_sala` sobre ids sacados por semilla, con un tercio de salas en cada estado), **B2** (ídem con `estado_cara`), **B3** (alternativa descartada de R1: lista de ids explorados recorrida; vive solo en el bench), **B9** (`a_guardado` + `restaurar`), **B10** (`a_dto` y `buscar_exploradas` con el mapa completo) y **B11** (armar `GrafoMapaConocido` sobre el mapa completo, que arma el índice de entradas en O(S + E), y un `paso_desde_cero` sobre él desde una esquina hacia la opuesta; cronometrados por separado y juntos, en las tres cuadrículas; en la de 1 024 salas, la que importa para NFR-250, la nota dice si «armar el grafo + un paso» queda por debajo de 5 ms, sin suponerlo antes; research R5 y R7). Depende de T027 (`GrafoMapaConocido`). Reutiliza de `Logic/BenchLogica.py` solo `_cronometrar`, `_mejor_y_mediana` y `SEMILLA`, **sin modificarlo** (confirmado en T004). La columna `nota` informa el factor respecto del tamaño anterior. Sin `dict` ni `sorted` también en el bench. Con type hints y docstring.
- [ ] T053 (NFR-202, NFR-203, SC-204, SC-207) En `Logic/BenchMapaConocido.py`: **B4** (entrada con antorcha que revela la misma cantidad de salas, la sala y sus 4 vecinas sin explorar, con el resto del mapa ya explorado, en mapas de ~100, ~1 000 y ~10 000 salas; el estado se repone fuera del cronómetro con el pergamino), **B5** (alternativa descartada de R2: recalcular «avistadas» recorriendo todo el mapa después de cada entrada), **B6** (entrar con antorcha, cerrar el intervalo y deshacer, con la misma cantidad de casillas) y **B7** (alternativa descartada de R3: copiar el mapa entero antes de la acción y restaurarlo). Las alternativas en 10 000 salas con **una sola repetición** si tardan demasiado, con la nota «1 repetición».
- [ ] T054 (NFR-205, SC-206) En `Logic/BenchMapaConocido.py`: **B8**, ciclo de eventos con la antorcha encendida en la cuadrícula de 1 024 salas (32 × 32, hallazgo H-6), 30 cazadores y 20 errantes y rastreadores con `_motor_con_cazadores` de `Logic/BenchRutas.py`, el jugador se mueve en cada ciclo; variante con una puerta de la sala del jugador que cambia en cada ciclo, avisada por el **camino real**: después de cambiar la cara, `motor.mazmorra.observador_puertas.puerta_cambio(a, b)`, es decir, el `RepartidorAvisosPuertas` del motor, que llega a las rutas del cazador y al mapa. **No** usar `BenchRutas._cambiar_puerta`, que avisa solo a la estrategia que recibe por parámetro: con eso el mapa no se enteraría (research R7). Antes, sin cronometrar, comprobar que el mapa coincide con el de un motor de control. Nota «cumple» o «no cumple» frente a 20 ms con el peor ciclo. **Depende de T033** (el motor necesita `motor.mapa`). `medir()` junta B1 a B11. Hace pasar T051 (salvo la de `ServicioBench`).
- [ ] T055 (NFR-204) En `Service/ServicioBench.py` (integrante 2): `from Logic import BenchMapaConocido` y `BenchMapaConocido.medir` en la lista por defecto, **después de `BenchLogica.medir`** (y de `BenchResolubilidad.medir` si ya está). Sin import circular: ni `BenchLogica`, ni `BenchRutas`, ni `BenchResolubilidad` importan `BenchMapaConocido`. `Logic/BenchLogica.py` no se toca. Hace pasar `test_nfr204_servicio_bench_incluye_mapa_conocido`.
- [ ] T056 Correr `uv run python main.py --bench` (o `python -m Service.ServicioBench`) y guardar la tabla en `specs/002-niebla-ir-a/bench-<fecha>.txt`, con la máquina y la versión de Python, como en la 001 y la 003. Comprobar [quickstart.md](quickstart.md) §5: B1 y B2 con 10 000 salas, menos del doble que con 100 (SC-203); B4 con el mapa mayor, menos del doble que con el menor (SC-204); B6, menos del doble (SC-207); B3, B5 y B7 crecen con el tamaño; B8 «cumple», peor ciclo < 20 ms (NFR-205, SC-206); B9 y B10 crecen en forma lineal con S (NFR-203); B11 con 1 024 salas: anotar el tiempo de «armar el grafo + un paso» y si queda por debajo de 5 ms, y corregir la frase de research R5 y del contrato (a) con el número medido (si no queda por debajo, avisar al integrante 3 antes de cerrar, porque afecta a su NFR-250); dos corridas con la misma semilla miden lo mismo. Si un criterio no se cumple, revisar el diseño antes de tocar un umbral; si hace falta cambiar un umbral, corregir primero la spec (Principio IX).

---

## Fase 12: Documentación y cierre

- [ ] T057 (NFR-204, Principio VIII) En `DECISIONES.md` (raíz del repositorio), sección **«Integrante 2 — 002 y 003»** (hoy «(pendiente)»; las secciones de los integrantes 1 y 3 no se tocan; si ya existe el apartado «§5.4 Resolubilidad» de T064 de la 003, va a continuación), escribir el apartado **«Mapa conocido»** a partir de research R0 a R7 y de los números de T056: por cada decisión (representación con dos arreglos por sala y por cara, R1; tres puntos de entrada y el repartidor del aviso, R2; reversión por casilla en el historial, R3; copia por punto de control y bloque propio en el binario versión 2, R4; lo que se ofrece al integrante 3, R5), el **problema**, las **alternativas** con su complejidad, la **decisión**, la **complejidad**, la **evidencia** de B1 a B11 (enlace al archivo de T056; B11 para el grafo y la búsqueda nueva por paso) y **si la decisión final coincide con el plan**. Decir explícitamente qué decisiones se tomaron **por diseño, sin medición**, y por qué: el `RepartidorAvisosPuertas` (frente a un solo observador o a que la `Mazmorra` avise a dos observadores), porque es una cuestión de responsabilidades y de no modificar la `Mazmorra` (P1, integrante 1), no de rendimiento: las tres opciones cuestan O(1) por aviso; y el formato binario con un bloque propio del mapa (frente a meter el mapa en el bloque global), porque el bloque global lo reutiliza cada punto de control de la línea y `cargar_sala` no debe leer conocimiento: es formato y compatibilidad, con el mismo costo O(S). Incluir la revisión de estructuras existentes (R0), el límite conocido de las salidas repetidas (H-4), la dependencia de `_salida_inversa` (H-7), el cambio de `observador_puertas` en el motor (H-1), la lectura de H2-5 (H-5), la cuadrícula de 1 024 salas (H-6) y que cargar reemplaza el mapa (H-8). Si el cambio del binario a la versión 2 modifica una decisión de la primera parte, documentar el antes y el después.
- [ ] T058 [P] **(avisar al integrante 3)**, porque ella también edita ese archivo. En `specs/002-niebla-ir-a/spec.md`, tabla «Trazabilidad del Apéndice B», cambiar «Se define en `tasks.md`» por el nombre de la prueba **solo en las filas de esta parte**: caso 2a (`test_h2_1_apendiceB_caso2a_…`, T017), caso 4 (`test_h3_1_apendiceB_caso4_…`, T020), caso 5 (`test_h4_1_apendiceB_caso5_…`, T023) y los adicionales A1 a A23 y A38 a A43 (tabla de cobertura de abajo). Las filas 1, 2b, 3, 6 y A24 a A37 son del integrante 3 y no se tocan. En un **commit `spec(002)` aparte**, separado del código (Principio IX).
- [ ] T059 Revisión de restricciones (Principio II), como **T067 de la 003**: `grep -rnE "import copy|from copy|bisect|heapq|collections|networkx|\bsorted\(|\.sort\(" Logic Estructuras DTO Service` no debe mostrar coincidencias nuevas en el código de esta feature (`Logic/MapaConocido.py`, `Logic/GrafoMapaConocido.py`, `Logic/RepartidorAvisosPuertas.py`, `Logic/BenchMapaConocido.py`, `DTO/MapaConocidoDTO.py`); `grep -rnE "^(from|import) (Data|Service)" Logic` no debe mostrar nada nuevo; `grep -rnE "^(from|import) " DTO/MapaConocidoDTO.py` solo debe mostrar `dataclasses` y `typing`; `grep -rn "\.mapa\.\(iniciar\|entrar\|puerta_cambio\|restaurar\|_poner\)" --include=*.py Logic Service Data UIController View` solo debe mostrar `Logic/motorJuego.py` y `Logic/PartidaGuardada.py` (el repartidor recibe el mapa en su lista) (FR-218, riesgo R-2); `git diff` de la feature no toca los archivos de «No se tocan» (Reglas); y `git diff` de `Logic/motorJuego.py` y `Logic/PartidaGuardada.py` contiene solo las líneas de T033 y T040, revisadas por el integrante 1.
- [ ] T060 Correr `$env:PYTHONIOENCODING = "utf-8"; uv run python tests/correr_pruebas.py` (todo en verde, sin regresiones en las pruebas de la primera parte ni de las features 001, 003 y 004; los únicos `skip` que quedan son los que esperan al integrante 3, con su motivo; **SC-202 no se da por cumplido** hasta que la parte del `EstadoJuegoDTO` de `test_sc202_doscientas_acciones_sin_datos_de_desconocidas` (H-2) pase sin `skip`) y el replay de ejemplo `uv run python main.py --replay ejemplos/partida_ejemplo.log --offline`, comparando su salida y su código con los de antes de la feature. Seguir [quickstart.md](quickstart.md) de punta a punta (§1 pruebas, §2 en el juego con el integrante 3, §3 determinismo, §4 archivo de partida, §5 `--bench`) y comprobar la tabla de cobertura de abajo.
- [ ] T061 (Principio XI) Registrar en `PROMPTS_LLM.md` los prompts de esta parte de la feature. El archivo **no tiene secciones por integrante**: las entradas van **al final del archivo, en orden cronológico**, con el formato que ya usa (`**Fecha:**`, `**Herramienta:**`, el prompt textual, `**Uso de la respuesta:**` y la línea de guiones que separa las entradas), sin credenciales ni datos personales. Registra **los prompts usados durante la implementación** de esta parte, con la fecha y para qué tarea. Los de `/speckit-tasks`, del agregado por la respuesta del integrante 1, de `/speckit-analyze` y de sus correcciones **no** van aquí: los registra el integrante 2 en el commit de `tasks.md`.

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1 (preparación)**: T001 empieza ya y se termina entero (incluidos `mapa_de_prueba` y `estados`) antes de T010; hasta T012, lo que lo usa falla al importar `MapaConocido`, que es el fallo esperado. T002 y T003 están hechas
  (acuerdo del 14/11 con el integrante 1) y no bloquean nada; T004 solo espera su revisión cruzada del plan, que llega
  hoy, y no bloquea nada. T005 a T008 son acuerdos con el integrante 3 que se mandan **hoy**; T005 bloquea T026; T007
  bloquea T039.
- **Fase 2 (base)**: T009 no depende de T001; T010 depende de T001 (`mapa_de_prueba`, `estados`). Bloquea todas las
  historias.
- **Fase 3 (US1)**: depende de la fase 2. Es el MVP.
- **Fase 4 (US2)**: depende de la fase 3 (`_observar_puertas`).
- **Fase 5 (US3)**: depende de la fase 3 (`entrar`). Puede ir en paralelo con la fase 4 (otros archivos de prueba;
  el mismo `Logic/MapaConocido.py`, así que la implementación es en serie).
- **Fase 6 (US4, pergamino)**: depende de las fases 3 a 5 (revierte entradas con antorcha y observaciones).
- **Fase 7 (contrato)**: depende de las fases 2 a 4 y de T005. Se adelanta a la fase 6 si el integrante 3 lo
  necesita antes (no usa nada de la fase 6 salvo la prueba de lectura en vivo después de un `deshacer`). T030 (aviso)
  al terminar T029.
- **Fase 8 (repartidor y motor)**: T031 (pruebas, primero) depende de las fases 3 a 6; T032 depende de la fase 2;
  T033 (cambio del motor, lo escribe el integrante 2 y lo revisa el integrante 1) depende de T031, de T032 y de las
  fases 3 a 7. T034 está eliminada.
- **Fase 9 (US4, guardado)**: las cuatro primeras pruebas de T035, T036, T038 y T039 dependen solo de la fase 2
  (`MapaConocidoGuardadoDTO`, T011) y de T007 (formato), así que **se adelantan** y se hacen justo después de la fase 2,
  antes de las fases 3 a 7, con un commit y un aviso propios (T043): el integrante 3 los necesita para sus T043 a T048
  de la 004. Comprobado que nada de eso depende de `MapaConocido`: `GuardadoBinario` solo ve el DTO, y mientras no
  esté T040, `PartidaGuardada.guardar` deja `mapa = None` (bloque de largo 0) sin romper nada. El resto de T035 y T037
  dependen de T015 (`restaurar(None)`); T040 (lo escribe el integrante 2 y lo revisa el integrante 1) se queda donde
  está, porque depende de T033, T037 y T039; T041 depende de T033 y T040.
- **Fase 10 (US5)**: T045 y T046 dependen de las fases 3 a 5 y, las pruebas con el motor, de T033. T048 y T049
  (avisos) al terminar T046; T050 depende del integrante 3 (T023 de la 004 y H-2).
- **Fase 11 (bench)**: depende de las fases 2 a 10 (mide `a_dto`, `buscar_exploradas`, `a_guardado`, `restaurar`);
  T054 depende de T033.
- **Revisión del integrante 1**: T033 y T040 no se integran a `origin/derek` sin su revisión.
- **Fase 12 (cierre)**: depende de todo lo anterior. T057 usa los números de T056. T058 depende de que existan los
  nombres de las pruebas.

### Fuera de esta parte (no son tareas del integrante 2 de la 002)

- **Revisión de `Logic/motorJuego.py` y `Logic/PartidaGuardada.py`** (integrante 1): los escribe el integrante 2 en
  T033 y T040 (acuerdo del 14/11, T002 y T003); el integrante 1 los revisa antes del merge.
- **Lista de funciones privadas que usan la 002 y la 003** (integrante 1): la anota en su plan y avisa antes de
  tocarlas (T004).
- **T023 de la 004** (`Service/ArmadorResumen.py`, integrante 3): copia `motor.mapa.a_dto()`; acordado en T008,
  avisado en T049.
- **Vista, comando de ver el mapa, H-2** (integrante 3): acordados en T006, pedidos en T048.
- **T071 de la 004** (integrante 2, ya hecha): `BitacoraReplayIO.leer` ignora `# ir a`; la usa la prueba de H4-5
  (T041).
- **T002, T003 y T047 de la 004** (integrante 2): se cumplen dentro de esta feature (T036, T038, T039), para que la
  versión 2 del formato se defina una sola vez; avisadas en T043.
- **«ir a»** (integrante 3): sus tareas, desde T100, en la sección reservada.

### Dentro de cada historia

- Las pruebas primero, y deben fallar.
- DTO antes que Logic; Logic antes que Data y Service; el cambio del motor (T033) después de Logic y de sus pruebas
  (T031).
- Las tareas **(coordinar con el integrante 1)** que escribe el integrante 2 (T033, T040) llevan su prueba primero,
  como las demás, y pasan por la revisión del integrante 1 antes del merge. Las de **(coordinar con el integrante 3)**
  (T048 y lo que piden T006 y T008) se le piden a ella, que es la dueña de esos archivos.
- Correr todas las pruebas al final de cada fase.

### Grafo de dependencias

```text
T002 [x] (integ. 1: motor lo escribe el integ. 2, confirmado el 14/11) ─► (no bloquea; T033 lo implementa)
T003 [x] (integ. 1: PartidaGuardada la escribe el integ. 2, confirmado el 14/11) ─► (no bloquea; T040 lo implementa)
T004 (integ. 1: privadas que usan 002 y 003, confirmado; falta su revisión cruzada) ─► (no bloquea; T015, T052, T054 las usan)
T005 (integ. 3: contrato y H-3) ───────────────────────────────► T026
T006 (integ. 3: H-2) ──────────────────────────────────────────► T045 (parte del EstadoJuegoDTO), T048, T050
T007 (integ. 3: §2 del contrato de la 004) ────────────────────► T039
T008 (integ. 3: T023 de la 004) ───────────────────────────────► T042, T049

T001 ─┐
T009 ─► T011 ─┐
T010 ─────────┴► T012 ─► T013 (fase 2)
Fase 2 + T007 ─► (adelantado) T035 (4 pruebas del DTO) ─► T036 (T002 de la 004) ─► T038 ─► T039 (T003 de la 004) ─► T043 (aviso integ. 3: sus T043 a T048 de la 004)
Fase 2 ─► US1: T014 ─► T015 ─► T016
          US2: T017 ─► T018 ─► T019
          US3: T020 ─► T021 ─► T022
          US4: T023 ─► T024 ─► T025 (pergamino)
          Contrato: T026 ─► T027, T028 ─► T029 ─► T030 (aviso integ. 3 ─► sus tareas desde T100)
          Repartidor y motor: T031 (pruebas, también las del motor) ─► T032 ─► T033 (motorJuego.py, integ. 2, revisa integ. 1)   [T034 eliminada]
          Guardado (resto): T015 ─► T035 (pruebas de restaurar) ─► T037 ─┐
                            T033 + T039 ───────────────────────────────┴► T040 (PartidaGuardada.py, integ. 2, revisa integ. 1) ─► T041, T042 ─► T044
          US5: T045 ─► T046 ─► T047 ─► T048 (integ. 3: vista y comando), T049 (integ. 3: T023 de la 004) ─► T050
          Bench: T051 ─► T052 ─► T053 ─► T054 (necesita T033) ─► T055 ─► T056
          Cierre: T057 (usa T056) ─► T058 ─► T059 ─► T060 ─► T061
```

## Oportunidades de paralelismo

- **Fase 1**: T001 a la vez que los acuerdos T004 a T008 (mensajes, sin código); T002 y T003 ya están hechas.
- **Fase 2**: T009 y T010 a la vez (archivos de prueba distintos); T011 a la vez que T010.
- **Fases 4 y 5**: las pruebas T017 y T020 a la vez (archivos distintos); las implementaciones T018 y T021 en serie
  (mismo archivo).
- **Fase 8**: T032 (repartidor) puede adelantarse a la fase 3 (solo depende de la fase 2); T031 espera a las fases
  3 a 6 porque escribe en sus archivos de prueba.
- **Fase 9**: T035, T036, T038 y T039 (sin la parte de `restaurar`) se adelantan a la fase 3 y pueden ir en paralelo
  con las fases 3 a 7 (otros archivos, salvo `tests/test_guardado_mapa.py`); T035 y T038 son del mismo archivo (en
  serie); T036 y T037 a la vez (archivos distintos).
- **Fase 11**: puede empezar con B1 a B3 apenas esté la fase 2, en paralelo con las fases 3 a 10.
- **Fase 12**: T057 y T058 a la vez.
- **No** son paralelas entre sí las tareas que escriben el mismo archivo: `Logic/MapaConocido.py` (T012, T015, T018,
  T021, T024, T028, T037, T046), `tests/test_mapa_conocido_estados.py` (T010, T014, T031, T045),
  `tests/test_mapa_conocido_puertas.py` (T017, T031), `tests/test_mapa_conocido_antorcha.py` (T020, T031),
  `tests/test_mapa_conocido_partida.py` (T023, T031, T040, T041, T042),
  `tests/test_guardado_mapa.py` (T009, T035, T038), `tests/test_mapa_conocido_vista.py` (T045) y
  `Logic/BenchMapaConocido.py` (T052, T053, T054).

### Ejemplo de paralelismo: base

```text
Tarea: "Pruebas de DTO/MapaConocidoDTO.py en tests/test_guardado_mapa.py"           (T009)
Tarea: "Pruebas del núcleo en tests/test_mapa_conocido_estados.py"                   (T010)
Tarea: "Crear DTO/MapaConocidoDTO.py"                                                (T011)
```

### Ejemplo de paralelismo: historias 2 y 3

```text
Tarea: "Escenarios de la historia 2 en tests/test_mapa_conocido_puertas.py"          (T017)
Tarea: "Escenarios de la historia 3 en tests/test_mapa_conocido_antorcha.py"         (T020)
Tarea: "Crear Logic/RepartidorAvisosPuertas.py"                                      (T032)
```

---

## Estrategia de implementación

### Primero el MVP (historia 1)

1. Fase 1: ayudantes y acuerdos (con el integrante 1 ya cerrados el 14/11: el integrante 2 escribe el motor y
   `PartidaGuardada` y él los revisa; con el integrante 3: contrato, H-2, §2 de la 004 y T023 de la 004).
2. Fase 2: `DTO/MapaConocidoDTO.py` y el núcleo de `MapaConocido`.
3. **Guardado adelantado** (el integrante 3 depende de él para sus T043 a T048 de la 004): las cuatro primeras pruebas
   de T035, T036 (`PartidaGuardadaDTO` con `mapa` y `linea`, T002 de la 004), T038 y T039 (`GuardadoBinario` versión 2,
   T003 y T047 de la 004), que solo necesitan el DTO; un commit propio y el aviso de T043.
4. Fase 3: `iniciar` y `entrar` sin antorcha.
5. **Parar y validar**: `python tests/correr_pruebas.py` y los escenarios de la historia 1 en Logic.

### Entrega incremental

0. (Ya hecho después de la fase 2, ver MVP paso 3) Guardado adelantado: `PartidaGuardadaDTO` y `GuardadoBinario`
   versión 2, con su commit y el aviso de T043.
1. + Historia 2: memoria de puertas y `puerta_cambio` (caso 2a).
2. + Historia 3: antorcha (caso 4 en Logic).
3. + Pergamino en Logic (caso 5 en Logic).
4. + Contrato para el integrante 3: `GrafoMapaConocido` y `buscar_exploradas`; subir `MapaConocido` a `origin/derek`
   y avisarle (T030), para «ir a» y para H-2.
5. + Pruebas con el motor (T031), repartidor y cambio de `Logic/motorJuego.py` (T033, lo revisa el integrante 1):
   las historias 1 a 4 pasan también con el motor.
6. + Resto del guardado: `a_guardado` y `restaurar` (T035, T037) y `Logic/PartidaGuardada.py` (T040, lo revisa el
   integrante 1), que necesita `MapaConocido` y el motor.
7. + Historia 5: `a_dto` y SC-202; pedir la vista, el comando, H-2 y T023 de la 004 (T048, T049).
8. + Bench B1 a B11, `DECISIONES.md` «Mapa conocido» y trazabilidad.

Cada paso deja todas las pruebas en verde (las que esperan a otro integrante, en `skip` con su motivo).

### Commits sugeridos (los hace el integrante 2)

Uno por fase o por grupo lógico, por ejemplo: `feat(002): DTO y núcleo del mapa conocido`, enseguida el del guardado
adelantado `feat(002): PartidaGuardadaDTO con mapa y linea y binario versión 2 (T002, T003 y T047 de la 004)` (T035 a
T039 sin `restaurar`, con el aviso de T043), `feat(002): estados de
sala (iniciar y entrar)`, `feat(002): memoria de puertas`, `feat(002): antorcha`, `feat(002): pergamino y mapa
conocido`, `feat(002): GrafoMapaConocido y buscar_exploradas (contrato del integrante 3)`, `feat(002):
RepartidorAvisosPuertas y pruebas con el motor`, `feat(002): a_guardado y restaurar del mapa conocido`, `feat(002): vista del mapa conocido (a_dto)`, `bench(002): B1 a
B11`, `spec(002): nombres de las pruebas en la trazabilidad` (T058, siempre aparte del código) y `docs(002):
DECISIONES.md, mapa conocido`. Los cambios a `Logic/motorJuego.py` (T033) y a `Logic/PartidaGuardada.py` (T040)
**los commitea el integrante 2** en commits propios, solo con esas líneas y sus pruebas (por ejemplo `feat(002):
motorJuego crea el mapa y el repartidor` y `feat(002): PartidaGuardada guarda y carga el mapa`), y **los revisa el
integrante 1 antes del merge**, como el integrante 3 con los suyos en la 003.

---

## Cobertura: escenarios, casos del Apéndice B y decisiones sin escenario

| Escenario / caso | Adicional | Prueba | Tarea | FR |
|---|---|---|---|---|
| H1-1 | A1 | `test_h1_1_a1_fr201_fr202_fr204_fr205_fr206_sala_inicial_explorada` | T014 | FR-201, FR-202, FR-204, FR-205, FR-206 |
| H1-2 | A2 | `test_h1_2_a2_fr203_entrar_explora_y_avista` | T014 | FR-203 |
| H1-3 | A13 | `test_h1_3_a13_fr204_salida_sin_vuelta_avista_su_destino` | T014 | FR-204 |
| H1-4 | A14 | `test_h1_4_a14_fr204_fr217_avistada_solo_muestra_su_existencia` | T045 | FR-204, FR-217 |
| H1-5 | A3 | `test_h1_5_a3_fr217_fr218_precarga_y_esqueleto_no_cambian_el_mapa` | T014 | FR-217, FR-218 |
| H1-6 | A2 | `test_h1_6_a2_fr203_volver_no_baja_el_estado` | T014 | FR-203 |
| H1-7 | A41 | `test_h1_7_a41_fr218_cazador_no_cambia_el_mapa` | T031 | FR-218 |
| H2-1 (Apéndice B, caso 2a) | — | `test_h2_1_apendiceB_caso2a_fr207_fr209_puerta_recordada_abierta_se_actualiza` | T017 | FR-207, FR-209 |
| H2-2 | A4 | `test_h2_2_a4_fr208_cierre_automatico_lejos_sigue_abierta` y `test_h2_2_a4_fr208_motor_cierre_automatico` | T017, T031 | FR-208 |
| H2-3 | A15 | `test_h2_3_a15_fr207_cambio_con_el_jugador_en_la_sala` y `test_h2_3_a15_fr207_motor_aviso_por_el_repartidor` | T017, T031 | FR-207 |
| H2-4 | A16 | `test_h2_4_a16_fr204_fr207_salida_sin_vuelta_solo_desde_su_origen` | T017 | FR-204, FR-207 |
| H2-5 | A38 | `test_h2_5_a38_fr205_fr212_fr225_ofrece_solo_utilizables_con_costo_igualado` | T026 | FR-205, FR-212, FR-225 |
| H2-6 | A42 | Repartida en dos: `test_h2_6_a42_fr207_fr208_caras_distintas_se_recuerdan_por_separado` (cubre FR-207 y FR-208: la observación y la memoria por cara) y `test_h2_6_a42_fr208_fr225_solo_la_cara_de_origen_abierta_se_ofrece` (cubre FR-208 y FR-225: lo que se ofrece a «ir a») | T017, T026 | FR-207, FR-208, FR-225 (entre las dos) |
| H3-1 (Apéndice B, caso 4) | — | `test_h3_1_apendiceB_caso4_fr210_fr211_antorcha_explora_vecinas`, `test_h3_1_apendiceB_caso4_fr210_fr211_motor_antorcha_no_despierta` y `test_h5_3_a22_…` (sin contenido) | T020, T031, T045 | FR-210, FR-211 |
| H3-2 | A5 | `test_h3_2_a5_fr210_explora_a_traves_de_una_puerta_cerrada` | T020 | FR-210 |
| H3-3 | A6 | `test_h3_3_a6_fr214_antorcha_apagada_solo_avista` | T020 | FR-214 |
| H3-4 | A17 | `test_h3_4_a17_fr213_no_explora_mas_alla_de_las_vecinas` | T020 | FR-213 |
| H3-5 | A18 | `test_h3_5_a18_fr216_entrar_despues_revela_y_aplica_p1` | T031 | FR-216 |
| H3-6 | A19 | `test_h3_6_a19_fr205_fr207_fr212_puertas_de_la_vecina_sin_observar` | T020 | FR-205, FR-207, FR-212 |
| H3-7 | A20 | `test_h3_7_a20_fr210_fr215_encender_sin_moverse_no_cambia` | T031 | FR-210, FR-215 |
| H3-8 | A43 | `test_h3_8_a43_fr210_fr214_entrar_con_y_sin_antorcha_en_el_mismo_instante` (Logic), `test_h3_8_a43_fr210_fr214_fin_programado_antes_que_la_entrada` y `…_despues_de_la_entrada` (motor) | T020, T031 | FR-210, FR-214 |
| H4-1 (Apéndice B, caso 5) | — | `test_h4_1_apendiceB_caso5_fr222_pergamino_revierte_entrada_con_antorcha` y `test_h4_1_apendiceB_caso5_fr222_motor_leer_pergamino` | T023, T031 | FR-222 |
| H4-2 | A8 | `test_h4_2_a8_fr222_pergamino_revierte_la_observacion` | T023 | FR-222 |
| H4-3 | A7 | `test_h4_3_a7_fr221_guardar_y_cargar_conserva_el_mapa` (y las de binario de T038) | T040, T038 | FR-221 |
| H4-4 | A9 | `test_h4_4_a9_fr223_historia_muestra_el_mapa_de_ese_instante` | T042 (sin `skip` desde T050) | FR-223 |
| H4-5 | A10 | `test_h4_5_a10_fr224_replay_da_el_mismo_mapa` | T041 | FR-224 |
| H5-1 | A11 | `test_h5_1_a11_fr219_muestra_exploradas_y_avistadas_sin_desconocidas` | T045 | FR-219 |
| H5-2 | A21 | `test_h5_2_a21_fr208_fr219_muestra_el_recordado_no_el_real` | T045 | FR-208, FR-219 |
| H5-3 | A22 | `test_h5_3_a22_fr211_fr212_fr219_explorada_por_antorcha_sin_contenido_y_sin_observar` | T045 | FR-211, FR-212, FR-219 |
| H5-4 | A12 | `test_h5_4_a12_fr220_ver_el_mapa_no_altera_la_partida` y `test_h5_4_a12_fr220_motor_reloj_sin_cambios`; y, del integrante 3, `test_h5_4_a12_fr220_…` del comando de ver el mapa (no se registra en `partida.log` ni cambia nada), pedida en T048 | T045, T048 | FR-220 |
| H5-5 | A23 | `test_h5_5_a23_fr204_fr219_dos_salidas_a_la_misma_avistada` | T045 | FR-204, FR-219 |
| H5-6 | A39 | `test_h5_6_a39_fr205_fr219_costo_igualado` | T045 | FR-205, FR-219 |
| H5-7 | A40 | `test_h5_7_a40_fr202_fr217_reporte_con_forzar_no_cambia_el_mapa` | T045 | FR-202, FR-217 |

| Decisión sin escenario propio | Prueba | Tarea | FR |
|---|---|---|---|
| Vecina de sí misma o por varias salidas, sala de origen | `test_fr203_vecina_de_si_misma_y_varias_salidas_una_sola_vez`, `test_fr203_sala_de_origen_no_cambia` | T014 | FR-203 |
| Invariantes del mapa (ningún estado baja; avistadas bien formadas) | `test_fr203_fr204_invariantes_del_mapa` | T014 | FR-203, FR-204 |
| En la sala del jugador, recordado = real | `test_fr207_en_la_sala_del_jugador_recordado_igual_a_real` | T017 | FR-207 |
| Vecina ya explorada con la antorcha | `test_fr210_vecina_ya_explorada_no_cambia_ni_registra` | T020 | FR-210, FR-222 |
| Pergaminos seguidos y pergamino sin cambios del mapa | `test_fr222_pergaminos_seguidos`, `test_fr222_pergamino_sin_cambios_del_mapa` | T023 | FR-222 |
| El conocimiento inicial no se deshace | `test_fr222_iniciar_no_se_deshace`, `test_fr202_motor_iniciar_explora_la_sala_inicial` | T023, T031 | FR-202, FR-222 |
| Búsqueda por nombre (H-3) | `test_fr251_buscar_exploradas_cero_uno_y_dos`, `test_fr251_comparacion_strip_casefold`, `test_fr206_fr251_…` | T026 | FR-206, FR-225 (FR-251 es del integrante 3) |
| Igualdad con la búsqueda de la 001 | `test_fr225_misma_ruta_que_paso_desde_cero_sobre_grafo_filtrado` | T026 | FR-225 |
| Costo de armar el grafo y dar un paso (búsqueda nueva por paso; referencia para NFR-250 del integrante 3) | B11 en la tabla de T056; `test_r5_b11_paso_igual_al_de_un_grafo_filtrado_a_mano` | T051, T052, T056 | FR-225 (Principio VIII) |
| Restaurar con `None` y reemplazar el mapa en curso | `test_fr202_fr221_restaurar_none_arma_el_mapa_inicial_desde_la_sala_del_jugador`, `test_fr221_restaurar_reemplaza_el_mapa_en_curso` | T035 | FR-202, FR-221 |
| Repartidor del aviso | `test_fr207_repartidor_reenvia_en_orden`, `test_fr207_fr114_motor_asigna_el_repartidor` | T031 | FR-207; 001 FR-114 |
| Cargar un DTO sin mapa (riesgo R-9); restaurar con otra cripta; restaurar dos veces | `test_fr221_cargar_con_mapa_none_deja_el_mapa_inicial_desde_la_sala_del_jugador`, `test_fr221_restaurar_con_largos_distintos_es_value_error`, `test_fr223_restaurar_dos_veces_del_mismo_dto` | T040, T035 | FR-221, FR-223 |
| Archivo de la primera parte (versión 1) | `test_t047_de_la_004_archivo_v1_rechazado`, `test_t047_de_la_004_archivo_v1_deja_intacta_la_partida_actual` | T038 | FR-221; 004 FR-421 |
| Línea guardada con formato inválido | `test_t003_de_la_004_linea_con_formato_invalido_es_error_guardado` | T038 | 004 FR-420 |

| Criterio | Dónde se verifica |
|---|---|
| SC-201 | Los tres casos del Apéndice B de esta parte: caso 2a (T017), caso 4 (T020; con el motor, T031 y T033) y caso 5 (T023; con el motor, T031 y T033) |
| SC-202 | `test_sc202_doscientas_acciones_sin_datos_de_desconocidas` (T045; la parte del `EstadoJuegoDTO` sin `skip` desde T050, cuando el integrante 3 resuelva H-2). T060 no lo da por cumplido mientras esa parte siga en `skip` |
| SC-203 | B1 y B2 en la tabla de T056 |
| SC-204 | B4 en la tabla de T056; `test_nfr202_cambios_proporcionales_a_lo_revelado` (T020) |
| SC-205 | H4-1 a H4-5 (T023, T038, T040, T041) y `test_sc205_misma_partida_mismo_mapa_en_cada_accion` (T041) |
| SC-206 | B8 en la tabla de T056 (T054, depende de T033) |
| SC-207 | B6 en la tabla de T056 |

| NFR | Dónde se verifica |
|---|---|
| NFR-201 | `test_nfr201_consultas_estado_sala_y_cara` (T010); B1 y B2 (T052, T056) |
| NFR-202 | `test_nfr202_cambios_proporcionales_a_lo_revelado` (T020); B4 frente a B5 (T053, T056) |
| NFR-203 | B6 frente a B7 y B9 (T052, T053, T056); `test_nfr203_historial_none_no_registra` (T010) |
| NFR-204 | T051 a T056 y `DECISIONES.md` (T057) |
| NFR-205 | B8 (T054, T056), con la variante de puertas avisadas por `mazmorra.observador_puertas` |

---

## Viaje automático «ir a» (integrante 3) — sección reservada

*Esta sección la completa el integrante 3 en su propio commit, con las tareas de FR-250 a FR-264, NFR-250, NFR-251 y
SC-250 a SC-253 (historias 6 y 7; casos 1, 2b, 3 y 6 del Apéndice B y adicionales A24 a A37). Su numeración empieza
en **T100**, para no chocar con T001 a T099 del integrante 2. Usa
[contracts/contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md) (`GrafoMapaConocido`, `buscar_exploradas`,
`MapaConocidoDTO`; avisado en T030) y la búsqueda de la 001
([busqueda-rutas.md](../001-terreno-cazador/contracts/busqueda-rutas.md)). El integrante 2 no la edita.*
