---
description: "Lista de tareas de la feature 004: línea de tiempo de la partida"
---

# Tareas: Línea de tiempo de la partida

**Entrada**: documentos de diseño de `specs/004-linea-tiempo/`

**Prerrequisitos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Pruebas**: sí. La constitución (Principio X) pide una prueba por escenario y por caso del
Apéndice B, y el plan pide `unittest` en `tests/`. Cada prueba cita su FR en el nombre del método
(`test_h1_4_fr404_fr405`). Se escriben **antes** que el código y deben fallar primero.

**Organización**: una fase por historia de la spec (H1 → US1, H2 → US2, H3 → US3, H4 → US4,
H5 → US5), en el orden de la ruta de desarrollo: base, H1, H3, H2, H4, H5, interfaz, bench,
documentación.

**Responsable**: integrante 3. Las tareas marcadas **(integrante 2)** (Derek: `DTO/PartidaGuardadaDTO.py`, `Data/GuardadoBinario.py`, mapa conocido) no las
hace el integrante 3: solo se **coordinan** y se comprueba que estén. Nada de esas tareas se
implementa por ellos. La excepción es T012 (**integrante 3, revisa Marco**): Marco pidió que el
integrante 3 agregue `avanzar_hasta(t)` en `Logic/motorJuego.py` como extensión, sin tocar
`avanzar_hasta_jugador`, y que él revise el cambio.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas sin terminar).
- **[US1]…[US5]**: historia de la spec a la que pertenece la tarea.
- Las fases de preparación, base, bench y cierre no llevan etiqueta de historia.

## Reglas para todas las tareas (constitución v1.2.0)

- Python 3.11. Sin dependencias nuevas.
- Prohibido en `Logic/`, `Estructuras/`, `DTO/` y `Service/`: `copy` (incluido `deepcopy`),
  `bisect`, `heapq`, `collections`, `dict` o `set` como índice o caché, bibliotecas de grafos, y
  `sorted()` / `list.sort()` (si hace falta ordenar, `Estructuras/Ordenador.py`). `copy` solo en `tests/`.
  Las copias de estado (puntos de control) se hacen a mano. `tracemalloc` tampoco está permitido: la
  memoria se mide con bytes serializados y conteo de elementos.
- `Logic/` no importa `Data/` ni `Service/`. `Service/` no llama a `Data/` al reconstruir ni al
  consultar. `Estructuras/` no importa ninguna capa.
- Código nuevo con type hints y docstring breve. Comentarios y nombres en español, como el resto
  del proyecto. No se agregan type hints ni docstrings al código de la primera entrega.
- No se tocan `Logic/HistorialRetroceso.py`, `Logic/PartidaGuardada.py`, `Service/ServicioAccionJugador.py`
  ni `Service/ServicioReplay.py`.
- Las pruebas usan `unittest` y corren con `python tests/correr_pruebas.py`.
- Vocabulario: una **consulta** no cambia la partida; un **punto de control** es una copia completa del
  estado cada K acciones; una **acción vigente** es una acción del jugador que no fue revertida.
- El **K por defecto = 20 es provisional**: se confirma en T062 con las mediciones del bench.

---

## Fase 1: Preparación

**Propósito**: ayudantes de prueba y lo que hay que coordinar con otros integrantes desde el inicio.

- [X] T001 [P] (FR-401, FR-419) Crear `tests/ayudas_linea_tiempo.py` con ayudantes de prueba (con docstring): `partida_de_prueba(carpeta, semilla, k)`, que reutiliza `_crear` y `_correr` de `tests/test_servicios.py` (paquete offline, carpetas temporales) y devuelve `(servicio_partida, contexto)`; `jugar(contexto, cantidad)`, que ejecuta `cantidad` acciones deterministas con `_elegir_accion` de ese mismo archivo y devuelve el `EstadoJuegoDTO` final; `resumen_vivo(contexto)`, que arma el resumen del estado vivo para compararlo con el de la línea (sin cursor del inventario ni mensajes). Para pruebas de Lógica pura reutiliza `motor_con` y `poner_enemigo` de `tests/ayudas_terreno.py`.
- [ ] T002 **(integrante 2)** Coordinar en `DTO/PartidaGuardadaDTO.py` (FR-420), según [contracts/contrato-linea-tiempo.md](contracts/contrato-linea-tiempo.md) §1: campo nuevo `linea: LineaTiempoGuardadaDTO | None = None` **como último campo** de `PartidaGuardadaDTO`, y extender `a_diccionario` / `desde_diccionario` con él. Los demás campos no cambian de orden. Bloquea T045 y T046.
- [ ] T003 **(integrante 2)** Coordinar en `Data/GuardadoBinario.py` (FR-420, FR-421), según el contrato §2: `VERSION_FORMATO = 2`, offset y largo del bloque de la línea en la cabecera, escritura y lectura del bloque con los escritores y lectores primitivos de hoy, bloque de largo 0 si `linea` es `None`, y `cargar_sala` sin leer ese bloque. Un archivo de versión 1 se rechaza como incompatible con la versión leída y la esperada, sin cargar nada. Pedirle además sus pruebas en `tests/TestGuardadoBinario.py` (ida y vuelta con línea, línea vacía, archivo de versión 1). Bloquea T046 y T047.
- [ ] T004 **(integrante 2)** Coordinar con FR-223 de la spec 002 (riesgo R-8, hallazgo H-4): el mapa conocido es un campo de `PartidaGuardadaDTO` que actualiza el motor y se copia con `PartidaGuardada.guardar`, sin `copy`. Así los puntos de control y la re-simulación lo reproducen; la 004 solo agrega `linea` y no invierte el mapa (reconstruye hacia adelante). Mientras ese campo no exista, el resumen y las copias omiten esa sección (Suposiciones de la spec). No bloquea nada. Además, **todo camino que ejecute acciones** (comando manual, «ir a» de la 002, replay) debe pasar por `ServicioLineaTiempo.ejecutar` (hallazgo E2 del plan, H-4).
- [ ] T071 **(integrante 2)** Coordinar en `Data/BitacoraReplayIO.py` (spec 002, FR-261; hallazgo H-4 del plan): «ir a» registra la orden como un comentario `# ir a <sala>` en `partida.log` (formato acordado con el integrante 2), además de cada paso como un movimiento individual. **`BitacoraReplayIO.leer` debe ignorar esas líneas** (las que empiezan por `# ir a`, sin confundirlas con el encabezado `#CRIPTA-REPLAY` ni con `#ACCIONES`) y reproducirlas sin cambiar el resultado. Pedirle su prueba en `tests/TestBitacoraReplayIO.py`. **`--replay … --hasta` (T039, T041) depende de ello**: sin esto un log con «ir a» no se puede leer. No bloquea las demás historias.

---

## Fase 2: Base (bloquea todas las historias)

**Propósito**: la búsqueda binaria, la línea de tiempo en Lógica y los DTOs que usan todas las historias.

**⚠️ Ninguna historia empieza antes de terminar esta fase.**

- [X] T005 [P] Escribir `tests/test_busqueda_binaria.py` (debe fallar), citando FR-416 y §5.5: `test_busqueda_ultimo_menor_o_igual_fr416` (clave exacta, clave entre dos elementos, clave mayor que todas), `test_busqueda_sin_menor_devuelve_menos_uno_fr416` (clave menor que todas y arreglo vacío), `test_busqueda_con_extractor_de_clave_fr416`.
- [X] T006 Crear `Estructuras/BusquedaBinaria.py` (sin `bisect`; no importa ninguna capa): función `ultimo_menor_o_igual(arreglo: list, clave: int, extraer_clave) -> int` que devuelve la posición del último elemento con clave ≤ la pedida, o −1, en O(log n) de tiempo y O(1) de espacio. Con type hints y docstring. Hace pasar T005.
- [X] T007 [P] Escribir `tests/test_linea_tiempo_logica.py` (debe fallar), citando FR-409, FR-413, FR-415 y FR-416, solo para lo que no es recorte: `test_linea_valida_instante_fr409` (t negativo, no entero o posterior al reloj actual → `ValueError` cuyo mensaje trae el motivo y el rango válido; t igual al reloj se acepta), `test_linea_valida_accion_fr409` (k = 0, k mayor que las acciones o no entero → `ValueError` con el rango; sin acciones, `#1` se rechaza), `test_linea_agrega_acciones_en_orden_fr413` (la acción número k es la posición k, desde 1), `test_linea_necesita_punto_cada_k_fr416` (con K = 3: puntos en 0, 3, 6…; **nunca hay más de K acciones entre dos puntos consecutivos**; los puntos tomados tras un pergamino pueden estar más cerca, T027), `test_linea_ubicar_punto_fr416`, `test_linea_ubicar_accion_por_tiempo_fr404`, `test_linea_k_invalido_fr415` (K < 1 → `ValueError`), `test_linea_registra_carga_y_ficha_una_sola_vez_fr419` (a lo sumo un registro por sala y una ficha por id).
- [X] T008 Crear `Logic/LineaTiempo.py` (Lógica; sin I/O, no importa `Data/` ni `Service/`), según [data-model.md](data-model.md): clase `LineaTiempo` con `k` y los arreglos `acciones`, `puntos` y `cargas` más las fichas vistas (búsqueda lineal por id, sin `dict`); clases pequeñas `AccionVigente`, `PuntoControl` y `RegistroCarga` con los campos de la tabla (no hay marcador de pergamino). Operaciones: `agregar_accion`, `necesita_punto` (a lo sumo K acciones entre dos puntos consecutivos), `agregar_punto`, `ubicar_punto` y `ubicar_accion_por_tiempo` (ambas con `BusquedaBinaria`), `registrar_carga` y `registrar_ficha`, y la **validación de rango** de las consultas (FR-409; es regla de negocio, por eso va aquí y no en Service): `validar_instante(t, reloj_actual)` y `validar_accion(k)`, que lanzan `ValueError` con el motivo y el rango válido. `k < 1` lanza `ValueError`. Todo se agrega al final. Con type hints y docstring. Hace pasar T007. (El recorte con el punto nuevo llega en T028.)
- [X] T009 [P] Crear `DTO/ResumenHistoriaDTO.py` (DTO inmutable, solo datos) con los campos de [data-model.md](data-model.md): `reloj`, `sala`, `jugador`, `inventario` (sin cursor), `efectos`, `enemigos`, `mapa_conocido` opcional, `terminada_antes`, `instante_pedido`; **sin campo de mensajes** (FR-406). Con su prueba en `tests/test_dto_linea_tiempo.py`: `test_resumen_no_tiene_cursor_ni_mensajes_fr406` (el DTO no define esos campos) y `test_resumen_mapa_conocido_es_opcional_fr405`.
- [X] T010 [P] Crear `DTO/LineaTiempoDTO.py` (DTO inmutable, solo datos) con `LineaTiempoGuardadaDTO` y sus partes (`AccionGuardadaDTO`, `PuntoControlGuardadoDTO`, `RegistroCargaGuardadoDTO`), según el contrato §1, con `a_diccionario` / `desde_diccionario`. **No hay DTO de marcador de pergamino**: la línea guardada lleva `k`, `acciones`, `puntos`, `cargas` y `fichas`. Restricciones a validar al leer (citar verbatim): «`k ≥ 1`; `acciones` en orden creciente de `tiempo`; `puntos` en orden estrictamente creciente de `acciones_completadas`, cada una entre 0 y la cantidad de `acciones`, y a lo sumo `k` acciones entre dos puntos consecutivos; el punto de `partida.linea` es siempre `None`». Con sus pruebas en `tests/test_dto_linea_tiempo.py`: `test_linea_guardada_ida_y_vuelta_fr420`, `test_linea_guardada_rechaza_orden_invalido_fr420`, `test_linea_guardada_rechaza_k_invalido_fr420`, `test_linea_guardada_rechaza_punto_invalido_fr420` (posición repetida o decreciente, fuera de rango, más de `k` acciones entre dos puntos consecutivos).
- [X] T069 (FR-415) *(confirmar con el integrante 2: `ConfiguracionDTO.py` es de Derek; el cambio son un campo y una constante nuevos al final)* En `DTO/ConfiguracionDTO.py` crear la constante `CHECKPOINT_POR_DEFECTO = 20` (**provisional**, se confirma en T062) y agregar al final el campo `checkpoint_cada: int = CHECKPOINT_POR_DEFECTO`. **Orden de campos**: `checkpoint_cada` primero; `hasta` después (T037); los de la 003 (`verificar` y `forzar`, del integrante 2) van detrás. Con su prueba en `tests/test_configuracion_checkpoint.py`: `test_configuracion_checkpoint_por_defecto_fr415` (una `ConfiguracionDTO` sin ese argumento trae `CHECKPOINT_POR_DEFECTO`) y `test_configuracion_checkpoint_acepta_otro_valor_fr415`. La bandera `--checkpoint-cada` llega en T050. No es paralela a T037 ni a T050 (mismo archivo). Bloquea T018.

**Punto de control**: `python tests/correr_pruebas.py` en verde.

---

## Fase 3: Historia 1 — Consultar un instante pasado durante la partida (P1) 🎯 MVP

**Objetivo**: `historia <t>` e `historia #k` muestran el estado pedido sin afectar la partida.

**Prueba independiente**: jugar varias acciones, consultar instantes y acciones anteriores y comprobar
que el resumen coincide con lo vivido y que la partida queda igual (SC-402, SC-403).

### Pruebas de la historia 1 ⚠️ (deben fallar primero)

- [X] T011 [US1] Escribir `tests/test_linea_tiempo_motor.py` con el motor sintético de `tests/ayudas_terreno.py` (programando eventos a mano en t = 300): `test_h1_2_apendiceB_caso3_fr402` (un enemigo ataca, una puerta se cierra sola y expira un efecto en t = 300, sin decisión del jugador: el estado es el posterior a todos), `test_h1_9_fr402_decision_del_jugador_en_t` (un enemigo ataca y luego le toca al jugador: `avanzar_hasta(300)` se detiene justo antes de la decisión, incluye el ataque), `test_h1_12_fr402_fr405_partida_terminada_en_t` (el veneno mata al jugador en t = 400: los demás eventos de t = 400 no se ejecutan), `test_fr402_eventos_cancelados_no_cuentan`, `test_fr402_avanzar_hasta_no_cambia_avanzar_hasta_jugador` (el comportamiento de `avanzar_hasta_jugador` es el mismo de siempre).
- [X] T013 [P] [US1] Escribir `tests/test_despacho_acciones.py` (con el paquete offline y `tests/ayudas_linea_tiempo.py`), citando FR-419 y FR-408: `test_despacho_igual_al_servicio_de_acciones_fr419` (para mover, abrir, atacar, esperar, recoger, soltar, equipar y usar, el estado del motor tras el despacho propio es igual al del `ServicioAccionJugador` sobre la misma partida), `test_despacho_no_escribe_log_fr408`, `test_despacho_no_pide_nada_a_data_fr407` (la cantidad de solicitudes de la fuente no cambia), `test_despacho_rechaza_retroceder_fr413` (lanza error: la línea nunca contiene esa acción).
- [X] T015 [P] [US1] Escribir `tests/test_grabadores_linea.py`, citando FR-419 y el Principio VII: `test_grabadores_registran_la_carga_de_sala_con_su_ordinal_fr419`, `test_grabadores_registran_cada_ficha_una_sola_vez_fr419`, `test_grabadores_no_piden_nada_nuevo_a_data` (la cantidad de solicitudes de la fuente es la misma con y sin grabadores), `test_grabadores_delegan_el_resto_al_resolvedor` (lo que no es `ficha()` funciona igual: `version_catalogo()`, etc.), `test_grabadores_delegan_rechazo_y_resolver_contenido_fr419` (lo que no es `ficha()` ni `asegurar_sala()` pasa tal cual al objeto original) y `test_grabadores_errordatos_propaga_sin_registrar_nada_fr419` (si el objeto original lanza `ErrorDatos`, el error sale igual y no queda ningún registro).
- [X] T017 [P] [US1] Escribir `tests/test_linea_tiempo_registro.py`, citando FR-401, FR-413, FR-416 y FR-407: `test_inicio_toma_el_punto_cero_fr401`, `test_accion_aceptada_se_agrega_con_su_tiempo_fr413` (`jugador.acciones` +1), `test_accion_rechazada_no_se_registra_fr407` (acción sin cambio en `jugador.acciones`, por ejemplo una dirección sin salida), `test_punto_de_control_cada_k_fr416` (K = 3).
- [ ] T020 [P] [US1] Escribir `tests/test_reconstructor_estado.py`, citando FR-401, FR-402, FR-407 y FR-419: `test_reconstruir_igual_al_vivo_fr419` (partida de 200 o más acciones: en cada decisión, el resumen reconstruido es igual al del estado vivo; SC-402), `test_reconstruir_conserva_el_azar_del_punto_fr419` (una acción con daño aleatorio da el mismo daño), `test_reconstruir_no_toca_log_historial_ni_reloj_fr407` (SC-403), `test_reconstruir_no_pide_nada_a_data_fr407`, `test_reconstruir_cuenta_las_acciones_reaplicadas_fr416` (el contador `acciones_reaplicadas` nunca pasa de K).
- [ ] T070 [P] [US1] Escribir `tests/test_linea_tiempo_cazador.py` (con el paquete offline y `tests/ayudas_linea_tiempo.py`), citando FR-419 y FR-114: `test_cazador_estado_reconstruido_igual_al_vivo_fr419_fr114` (escenario con un cazador que persigue al jugador durante varias acciones: en cada decisión, el resumen reconstruido por la línea —posición, vida y número de cada enemigo— coincide con el estado vivo) y `test_cazador_busqueda_compartida_del_motor_aparte_arranca_vacia_fr114` (la búsqueda compartida `motor.rutas` del `Motor` aparte arranca **vacía**, porque `PartidaGuardada` no la guarda, y la decisión del cazador es la misma que desde cero; coincide con la del motor vivo). Corre con T021; si falla, el defecto está en el reconstructor y no en la prueba.
- [ ] T022 [P] [US1] Escribir `tests/test_armador_resumen.py`, citando FR-405 y FR-406: `test_h1_4_fr404_fr405_contenido_del_resumen` (sala, vida, estadísticas, inventario, efectos, enemigos de esa sala con su vida), `test_h1_10_fr406_sin_cursor_ni_mensajes`, `test_resumen_reloj_es_el_instante_pedido_fr405`, `test_resumen_reloj_de_la_decision_k_fr405` (para `historia #k`), `test_resumen_reloj_del_final_si_la_partida_termino_antes_fr405`, `test_resumen_omite_mapa_conocido_si_no_existe_fr405`.
- [ ] T024 [P] [US1] Escribir `tests/test_linea_tiempo_consultas.py` (por el servicio, con `tests/ayudas_linea_tiempo.py`): `test_h1_1_apendiceB_caso1_fr409_instante_posterior` (reloj en 500, `historia 800`: rechazo con el límite 500, sin resumen, partida igual), `test_h1_3_apendiceB_caso4_fr407_fr408_no_altera_la_partida` (5 acciones revertibles, `historia 200` e `historia #3`: reloj igual, sin eventos nuevos, `partida.log` sin líneas nuevas, el historial de retroceso conserva las mismas 5 acciones antes y después), `test_h1_5_fr409_accion_fuera_de_rango` (`historia #9` e `historia #0` con 6 acciones: rechazo con el rango válido), `test_h1_6_fr401_fr414_accion_ya_no_revertible` (20 acciones, `historia #2` funciona), `test_h1_7_fr409_instante_igual_al_reloj` (`historia 500` se acepta), `test_h1_8_fr419_consulta_repetida` (dos consultas seguidas dan resúmenes idénticos), `test_h1_9_fr402_historia_t_igual_a_historia_k` (cuando a t le toca una decisión, `historia <t>` e `historia #k` coinciden), `test_casos_borde_sin_acciones_fr409` (`historia 0` se acepta, `historia #1` se rechaza), `test_partida_terminada_sigue_consultable_fr401`.

### Implementación de la historia 1

- [X] T012 [US1] **(integrante 3, revisa Marco)** En `Logic/motorJuego.py` agregar, como extensión y para que Marco lo revise, el método **nuevo** `avanzar_hasta(t: int) -> bool`, según [contracts/contrato-linea-tiempo.md](contracts/contrato-linea-tiempo.md) §3 (FR-401, FR-402, FR-411, FR-412). Mientras la partida no haya terminado: mira el siguiente evento válido sin extraerlo; si no hay o su tiempo es mayor que t, se detiene; si no, lo extrae, adelanta el reloj y, si es el del jugador (una decisión), se detiene **justo antes** de tomarla; si no, lo ejecuta. Si la partida terminó, los demás eventos de t no se ejecutan; los cancelados no cuentan. Devuelve `True` si se detuvo en una decisión del jugador. **`avanzar_hasta_jugador` no se toca.** Hace pasar T011. Bloquea T021.
- [X] T014 [US1] (FR-407, FR-408, FR-419) Crear `Service/DespachoAcciones.py`: clase `DespachoAcciones` con `ejecutar(motor, contexto_datos, accion: AccionDTO) -> str` que traduce el `AccionDTO` a la llamada correspondiente del `Motor` (mover, abrir, atacar, esperar, recoger, soltar, equipar, usar), con la misma tabla de `ServicioAccionJugador._ejecutar_en_el_motor` **pero**: sin anexar a la bitácora, sin sincronizar usos de la caché, sin pedir contenido a Data (la sala se carga con el registro de la línea) y sin aceptar `retroceder`. No cambia `ServicioAccionJugador`. Con type hints y docstring. Hace pasar T013.
- [X] T016 [US1] (FR-419, Principio VII) Crear `Service/GrabadoresLinea.py`: `ContenidoGrabador` (envuelve `contexto.contenido`; en `asegurar_sala(id)` guarda en la línea el `SalaDTO` devuelto como registro de carga, con el ordinal igual a `jugador.acciones` en ese momento) y `ResolvedorGrabador` (envuelve `contexto.resolvedor`; en `ficha(id)` guarda la ficha devuelta una sola vez). Los dos delegan **todo** lo que no es `ficha()` o `asegurar_sala()` al objeto original, incluidos `rechazo()` y `resolver_contenido()`; si el original lanza `ErrorDatos`, el error propaga y no se registra nada. Solo registran lo que la partida ya pidió, sin solicitudes nuevas (R3). Con type hints y docstring. Hace pasar T015.
- [X] T018 [US1] (FR-401, FR-416) Depende de T069. En `Service/ContextoPartida.py` agregar el campo final `linea: LineaTiempo | None = None` (**al final y con valor por defecto**: la 003 agrega `resolubilidad` después; quien suba primero, el otro hace `merge` antes). En `Service/ServicioPartida.py`, `iniciar_partida`: crear la `LineaTiempo` con el K de la configuración (`config.checkpoint_cada`, creado en T069 con el valor provisional), instalar los grabadores sobre `contenido` y `resolvedor` **antes** de cargar la sala inicial, y tomar el punto de control 0 al terminar la primera `avanzar_hasta_jugador` (copia manual con `PartidaGuardada.guardar`). Hace pasar `test_inicio_toma_el_punto_cero_fr401` de T017.
- [X] T019 [US1] (FR-407, FR-413, FR-416) Crear `Service/ServicioLineaTiempo.py` con `ejecutar(contexto, accion) -> EstadoJuegoDTO`: llama a `ServicioAccionJugador.ejecutar` y compara `jugador.acciones` antes y después: **+1** → `agregar_accion(tiempo de la decisión, accion)` y, si `necesita_punto`, toma un punto de control; **sin cambio** → no registra nada (acción rechazada); **−1** se trata en T030. Con type hints y docstring. Hace pasar el resto de T017.
- [ ] T021 [US1] (FR-401, FR-402, FR-419) Crear `Service/ReconstructorEstado.py`: clase `ReconstructorEstado` que, dada la línea y un objetivo (número de acciones completadas y, si hace falta, un instante), **ubica el punto de control** más cercano anterior (`ubicar_punto`), arma un `Motor` aparte con `PartidaGuardada.cargar(...)` (con `fn_mensaje=None`; `fn_ficha` y las salas del esqueleto salen de la línea, nunca de Data), re-simula las acciones vigentes con `DespachoAcciones` y `avanzar_hasta_jugador`, y para el instante pedido ejecuta la última acción y llama a `avanzar_hasta(t)`. Aplica los **registros de carga básicos** (cada sala que la re-simulación necesite y el punto de control no traiga, tomada de la línea; la regla del prefijo por ordinal llega en T032) y expone `acciones_reaplicadas`. Para un instante parte del último punto con `acciones_completadas ≤ j − 1` y re-simula la acción `j` (`j` = última acción con `tiempo ≤ t`); la regla de partir del punto tomado tras un pergamino llega en T034 Nunca toca `contexto.motor`, la bitácora, el historial ni la caché viva. Con type hints y docstring. Depende de T012, T014 y T016. Hace pasar T020.
- [ ] T023 [US1] (FR-405, FR-406) Crear `Service/ArmadorResumen.py`: `ArmadorResumen.armar(motor, esqueleto, instante_pedido, es_accion, terminada_antes) -> ResumenHistoriaDTO`. Sin cursor del inventario ni mensajes (FR-406). El `reloj` es el instante pedido; para `historia #k`, el instante de la decisión k; si la partida terminó antes de ese instante, el reloj del final (FR-405). **Si el estado trae el mapa conocido** (campo de `PartidaGuardadaDTO`, spec 002), el resumen lo **copia**; si no lo trae, omite `mapa_conocido`. Con type hints y docstring. Hace pasar T022.
- [ ] T025 [US1] En `Service/ServicioLineaTiempo.py` agregar `consultar_por_instante(contexto, t)` y `consultar_por_accion(contexto, k)` (FR-401, FR-403, FR-404, FR-409): **solo propagan** el error de `LineaTiempo.validar_instante(t, reloj_actual)` y `LineaTiempo.validar_accion(k)` (T008): la validación de rango (t entero ≥ 0 y no posterior al reloj actual; k entre 1 y las acciones del jugador) es regla de negocio y Service no valida. El `ValueError` trae el motivo y el rango válido, y la partida no se modifica. Usan `ReconstructorEstado` y `ArmadorResumen`. No consumen tiempo, no cuentan como acción y no se anexan a `partida.log` (FR-407, FR-408). Hace pasar T024.
- [ ] T026 [US1] Correr `python tests/correr_pruebas.py` y seguir [quickstart.md](quickstart.md) §1. **Parar y validar**: ya se puede entregar sin pergamino ni guardado.

---

## Fase 4: Historia 3 — La línea se mantiene correcta con el pergamino (P2)

**Objetivo**: lo revertido con un pergamino deja de existir en la línea (incluye el hallazgo H-1).

**Prueba independiente**: realizar acciones, usar un pergamino, volver a actuar y consultar; ninguna
consulta muestra lo revertido.

### Pruebas de la historia 3 ⚠️

- [ ] T027 [P] [US3] Agregar a `tests/test_linea_tiempo_logica.py`, citando FR-413, FR-416, FR-424 y NFR-403 (el estado guardado se arma con `PartidaGuardada.guardar` sobre un motor de `tests/ayudas_terreno.py`): `test_retroceder_una_quita_la_ultima_accion_fr413`, `test_retroceder_una_quita_los_puntos_con_mas_acciones_fr413`, `test_retroceder_una_agrega_el_punto_en_c_fr424` (no había punto en `c`: queda uno nuevo con el estado guardado), `test_retroceder_una_reemplaza_el_punto_en_c_fr424` (había uno en `c`: queda **uno solo**, el nuevo), `test_retroceder_una_no_deja_mas_de_k_entre_puntos_fr416`, `test_retroceder_una_no_recorre_la_historia_nfr403` (con 100 y con 5 000 acciones toca la misma cantidad de elementos), `test_retroceder_sin_acciones_falla_fr413`.
- [ ] T029 [P] [US3] Escribir `tests/test_linea_tiempo_pergamino.py` (con el paquete offline y un pergamino en el inventario, como `tests/test_servicios.py`): `test_h3_1_apendiceB_caso2_fr413_fr409` (acciones 1 a 5, el pergamino revierte la 5: `historia #5` se rechaza por rango y el instante actual muestra la sala 7, no la 9), `test_h3_2_fr413_accion_nueva_es_la_cinco` (tras una acción nueva, `historia #5` describe el estado justo antes de ella), `test_h3_3_fr409_fr413_limite_es_el_reloj_actual`, `test_h3_4_fr413_varios_pergaminos_seguidos` (ninguna consulta incluye eventos de acciones revertidas), `test_h3_el_pergamino_usado_no_esta_en_el_estado_actual_fr419` (la consulta del instante actual coincide con el estado vivo: no tiene el pergamino usado en el inventario), `test_h3_los_estados_pasados_conservan_el_pergamino_fr419` (los instantes anteriores a `c` usan los puntos anteriores y lo vivido en ese momento), `test_h3_la_linea_nunca_contiene_retroceder_fr413`, `test_hallazgo_h1_numeracion_de_enemigos_tras_el_pergamino_fr419` (entrar a una sala nueva, revertirlo, entrar a otra sala nueva: `historia` muestra los mismos números de enemigo que la partida viva).
- [ ] T033 [US3] Agregar a `tests/test_linea_tiempo_pergamino.py` las pruebas de los escenarios H3-5 y H3-6, **sin `skip`** (deben fallar primero): `test_h3_5_fr413_fr419_fr424_pergamino_recogido_en_la_accion_revertida` (el jugador recoge un pergamino en la acción 4 y usa otro pergamino para revertirla; la consulta del instante actual coincide con el estado vivo: el inventario conserva el pergamino recogido y no tiene el consumido) y `test_h3_6_fr413_fr419_fr424_pergamino_soltado_en_la_accion_revertida` (el jugador suelta un pergamino en la acción 4, usa otro para revertir esa acción y después recoge el que sigue en el suelo de la sala; al consultar el instante actual y los instantes posteriores, el resumen coincide con el de la partida viva: el pergamino soltado quedó fuera de la reversión, en el inventario y en el suelo). Citan FR-413, FR-419 y FR-424. Hacen pasar T034.

### Implementación de la historia 3

- [ ] T028 [US3] (FR-413, FR-424, NFR-403) En `Logic/LineaTiempo.py` agregar `retroceder_una(estado_guardado)`: quita la última acción (`pop`), quita los puntos de control con más de `c` acciones (siempre los últimos del arreglo) y **agrega o reemplaza** el punto de la posición `c` con `estado_guardado` (la copia del estado vivo que hizo `PartidaGuardada.guardar`; si ya había un punto en `c`, queda uno solo, el nuevo). Todo por el final de los arreglos: O(1 + r), sin recorrer la historia (NFR-403). **No** recorta `cargas` ni fichas. No hay marcadores. Hace pasar T027.
- [ ] T030 [US3] (FR-413, FR-424) En `Service/ServicioLineaTiempo.ejecutar` tratar el caso **−1** en `jugador.acciones` (pergamino leído): tomar el estado vivo con `PartidaGuardada.guardar` y llamar a `retroceder_una(estado_guardado)` (T028). `retroceder` nunca se agrega como acción. La numeración de acciones se cuenta separada de las líneas de `partida.log`. Depende de T028.
- ~~T031~~ **(eliminada)**: el reconstructor ya no aplica marcadores de pergamino (el pergamino deja un punto de control nuevo, R4). El número queda sin usar.
- [ ] T032 [US3] (FR-419) En `Service/ReconstructorEstado.py`: sobre los registros de carga básicos de T021, agregar la **regla del prefijo por ordinal** (hallazgo H-1). Para un objetivo con `n` acciones completadas se aplican, en el orden real, todos los registros hasta el último cuyo `ordinal` sea ≤ n, saltando las salas que el punto de control ya trae cargadas (incluido el punto tomado tras un pergamino, que trae las salas cargadas en la acción revertida). Así se conserva el orden real de la numeración de enemigos. Hace pasar `test_hallazgo_h1_…` de T029.
- [ ] T034 [US3] (FR-413, FR-419, FR-424; plan H-2, que es la regla de P1 §2.11) **Reemplazar el punto en `c` y verificar H3-5 y H3-6.** En `Service/ReconstructorEstado.py` aplicar la regla «Qué punto usa una consulta» de [data-model.md](data-model.md): para el instante `t`, si el último punto con `acciones_completadas ≤ j` (`j` = última acción con `tiempo ≤ t`) ya tiene reloj ≤ t, parte de él y solo llama a `avanzar_hasta(t)`; si no, parte del último punto con `acciones_completadas ≤ j − 1` y re-simula la acción `j` (así los instantes anteriores a `c` usan los puntos anteriores). Comprobar de punta a punta que el punto que reemplazó al de `c` (T028, T030) es el que usan el instante actual y los posteriores, y que el inventario **y el suelo** de la sala coinciden con la partida viva. Sin campos nuevos en las acciones ni en el historial de retroceso. Depende de T028 y T030. Hace pasar T033 y los `test_h3_…` de T029.
- [ ] T035 [US3] Correr todas las pruebas y seguir [quickstart.md](quickstart.md) §3.

---

## Fase 5: Historia 2 — Consultar sin interacción con `--replay … --hasta` (P1)

**Objetivo**: reproducir un `partida.log` hasta t e imprimir el mismo resumen, sin ventana.

**Prueba independiente**: ejecutar `--replay partida.log --hasta t` sobre un registro conocido y comparar el
resumen con el esperado.

### Pruebas de la historia 2 ⚠️

- [ ] T036 [P] [US2] Escribir `tests/test_lector_hasta.py` (no se edita `tests/TestLectorArgumentos.py`, que es del integrante 2), citando FR-410: `test_h2_3_fr410_hasta_sin_valor_es_error_de_uso`, `test_h2_3_fr410_hasta_no_entero_o_negativo_es_error_de_uso` (`abc`, `-3`, `2.5`), `test_h2_3_fr410_hasta_sin_replay_es_error_de_uso`, `test_fr410_replay_con_hasta_valido`, `test_h2_6_fr410_replay_sin_hasta_es_la_partida_completa`.
- [ ] T038 [P] [US2] Escribir `tests/test_servicio_replay_hasta.py` (con el paquete offline y los ayudantes de `tests/test_servicio_replay.py`): `test_h2_1_fr410_fr411_mismo_resumen_que_historia_t` (partida de 10 acciones), `test_h2_2_apendiceB_caso5_fr412_t_posterior_al_final` (partida terminada en 900, `--hasta 1500`: resumen del estado final, reloj 900, indica que la partida terminó antes), `test_h2_5_fr402_fr410_hasta_cero_es_el_estado_inicial`, `test_h2_6_fr410_sin_hasta_reproduce_todo`, `test_fr411_no_importa_la_vista` (no se importa `pygame` ni `View/`).
- [ ] T040 [P] [US2] Escribir `tests/test_main_hasta.py` (como `tests/test_main.py`): `test_h2_1_fr410_codigo_0`, `test_h2_3_fr410_codigo_2_hasta_invalido`, `test_h2_3_fr410_codigo_2_hasta_sin_replay`, `test_h2_4_fr410_codigo_1_archivo_inexistente` (error con contexto, sin caerse), `test_h2_4_fr410_codigo_1_archivo_ilegible`.

### Implementación de la historia 2

- [ ] T037 [US2] (FR-410) (confirmar con el integrante 2: `ConfiguracionDTO.py` y `LectorArgumentos.py` son de Derek; los cambios son campos y banderas nuevos al final) En `DTO/ConfiguracionDTO.py` agregar el campo `hasta: int | None = None` **después de `checkpoint_cada`** (T069; los campos de la 003, `verificar` y `forzar`, del integrante 2, van detrás), y en `UIController/LectorArgumentos.py` la bandera `--hasta` (entero ≥ 0, mismo estilo de `--cache-size`): sin valor, no entero o negativo → `ErrorArgumentos`; `--hasta` sin `--replay` → `ErrorArgumentos`. Actualizar el texto de ayuda. Hace pasar T036.
- [ ] T039 [US2] (FR-410, FR-411, FR-412) Crear `Service/ServicioReplayHasta.py`: `reproducir_hasta(ruta, t)` lee el log, reproduce la partida completa por `ServicioAccionJugador` mediante `ServicioLineaTiempo.ejecutar` (así la línea se alimenta igual que en vivo) y consulta t con `consultar_por_instante`, de modo que el resumen coincide con `historia t` por construcción (FR-411). Si t es posterior al final, devuelve el resumen del estado final con `terminada_antes` verdadero (FR-412). No instancia la vista. No toca `Service/ServicioReplay.py`. **No verifica la resolubilidad** (FR-301 de la 003: `--replay` y `--replay … --hasta` no la verifican). Depende de T071: `BitacoraReplayIO.leer` debe ignorar las líneas `# ir a <sala>` de «ir a». Hace pasar T038.
- [ ] T041 [US2] (FR-410, FR-411) En `UIController/ControladorBackend.py` agregar `reproducir_hasta(ruta, t)` **al final de la clase y sin tocar lo de la 003** (`verificar`, `resolubilidad`; quien suba primero, el otro hace `merge` antes) y en `main.py` la rama de `--replay` con `--hasta` que imprime el resumen; códigos de salida como en el resto del programa: 0 éxito, 1 error de operación (archivo inexistente o ilegible), 2 argumentos inválidos. Sin `--hasta`, `--replay` sigue como en la primera parte. Hace pasar T040.
- [ ] T042 [US2] Correr todas las pruebas y seguir [quickstart.md](quickstart.md) §2.

---

## Fase 6: Historia 4 — La línea sobrevive a guardar y cargar (P2)

**Objetivo**: guardar y cargar conserva la línea completa; un archivo de la primera parte se reporta incompatible.

**Prueba independiente**: consultar varios instantes, guardar, cargar y repetir; luego intentar cargar un
archivo de la primera parte.

### Pruebas de la historia 4 ⚠️

- [ ] T043 [P] [US4] Agregar a `tests/test_linea_tiempo_logica.py`, citando FR-420: `test_linea_a_guardada_y_desde_guardada_son_iguales_fr420` (acciones, puntos, cargas, fichas y K) y `test_linea_desde_guardada_conserva_el_orden_fr420`.
- [ ] T045 [P] [US4] Escribir `tests/test_linea_tiempo_guardado.py` (con el paquete offline, como `tests/test_servicio_guardado.py`): `test_h4_1_fr420_mismos_resumenes_tras_guardar_y_cargar` (20 acciones, varios `historia <t>` e `historia #k`), `test_h4_2_fr420_se_puede_seguir_jugando_tras_cargar` (consulta un instante anterior al guardado), `test_h4_3_apendiceB_caso6_fr421_archivo_de_la_primera_parte` (incompatibilidad reportada con contexto, partida actual sin modificar, nunca en silencio), `test_h4_k_guardado_se_conserva_al_cargar` (Suposiciones: se conserva el K guardado aunque se indique otro `--checkpoint-cada`), `test_h4_fr421_el_programa_no_se_cae`. Depende de T002 y T003 para correr.

### Implementación de la historia 4

- [ ] T044 [US4] (FR-420) En `Logic/LineaTiempo.py` agregar `a_guardada()` y `desde_guardada(dto)` (conversión a `LineaTiempoGuardadaDTO` y de vuelta), con copia manual (sin `copy`). Hace pasar T043.
- [ ] T046 [US4] (FR-420, FR-421) En `Service/ServicioGuardado.py`: `guardar` incluye `linea=contexto.linea.a_guardada()` (acciones, puntos, cargas, fichas y K; sin marcadores) en el `PartidaGuardadaDTO`; `cargar` reconstruye la línea con `desde_guardada`, **conserva el K guardado** aunque se indique otro `--checkpoint-cada`, e instala los grabadores con los registros y fichas que ya trae la línea. Depende de T002 y T003. Hace pasar T045.
- [ ] T047 [US4] (FR-420, FR-421) **(integrante 2)** Coordinar que existan las pruebas de `GuardadoBinario` versión 2 (T003): ida y vuelta de la línea, archivo de versión 1 rechazado, `cargar_sala` sin leer el bloque de la línea. Comprobar que `tests/TestGuardadoBinario.py` y `tests/TestPartidaGuardadaDTO.py` siguen en verde.
- [ ] T048 [US4] Correr todas las pruebas y seguir [quickstart.md](quickstart.md) §4.

---

## Fase 7: Historia 5 — Configurar los puntos de control con `--checkpoint-cada K` (P3)

**Objetivo**: decidir cada cuántas acciones se guarda una copia completa, sin cambiar lo que ve el jugador.

**Prueba independiente**: jugar la misma partida con distintos K y comprobar resúmenes idénticos y que
ninguna consulta reaplica más de K acciones.

### Pruebas de la historia 5 ⚠️

- [ ] T049 [P] [US5] Escribir `tests/test_checkpoint_cada.py`: `test_h5_1_fr418_mismos_resumenes_con_k_1_5_y_50`, `test_h5_2_fr416_ninguna_consulta_reaplica_mas_de_k_acciones` (K = 10, usando `acciones_reaplicadas` de `ReconstructorEstado`), `test_h5_3_fr415_valores_invalidos` (`0`, `-2`, `abc`, `2.5`: `ErrorArgumentos` y código de salida 2), `test_h5_4_fr415_valor_por_defecto` (sin la bandera se usa `CHECKPOINT_POR_DEFECTO`), `test_fr415_checkpoint_por_defecto_provisional_es_20` (se actualiza en T062 si el bench cambia el valor).

### Implementación de la historia 5

- [ ] T050 [US5] (FR-415) (confirmar con el integrante 2: `ConfiguracionDTO.py` y `LectorArgumentos.py` son de Derek; los cambios son campos y banderas nuevos al final) En `DTO/ConfiguracionDTO.py` el campo `checkpoint_cada` y la constante `CHECKPOINT_POR_DEFECTO = 20` (**provisional**, se confirma en T062) ya los creó T069; aquí queda la bandera: en `UIController/LectorArgumentos.py` la bandera `--checkpoint-cada` (entero ≥ 1; cualquier otro valor → `ErrorArgumentos`); en `Service/ServicioPartida.py` la línea ya usa `config.checkpoint_cada` desde T018, así que aquí solo se conecta la bandera. Hace pasar T049.
- [ ] T051 [US5] Correr todas las pruebas y seguir [quickstart.md](quickstart.md) §5.

---

## Fase 8: Interfaz — el comando `historia` (P1, historia 1)

**Objetivo**: el jugador escribe `historia <t>` o `historia #k` y ve el resumen (FR-423).

- [ ] T052 [P] [US1] Escribir `tests/test_controles_historia.py` (como `tests/test_controles_juego.py`): `test_h1_11_fr423_historia_t`, `test_h1_11_fr423_historia_k`, `test_fr409_historia_mal_formada_se_rechaza_con_uso` (`historia`, `historia abc`, `historia -3`, `historia #x`: mensaje de uso, partida sin cambios), `test_fr407_historia_no_cambia_el_estado_de_la_partida`.
- [ ] T053 [US1] (FR-423; es la tarea de la interfaz de la 004, distinta del T053 de la feature 001) En `UIController/ControladorBackend.py`: `historia_por_instante(t)` y `historia_por_accion(k)` que devuelven un `ResumenHistoriaDTO` por `ServicioLineaTiempo`; y que `_ejecutar` pase por `ServicioLineaTiempo.ejecutar` para que la línea se alimente (FR-423). **Todo camino que ejecute acciones** —el comando manual, el «ir a» de la spec 002 y el replay— usa `ServicioLineaTiempo.ejecutar`, nunca `ServicioAccionJugador` directo (hallazgo E2). Los métodos nuevos van **al final** de `ControladorBackend`, como los de la 003 (`verificar`, `resolubilidad`); quien suba primero, el otro hace `merge` antes. «ir a» registra la orden como comentario `# ir a <sala>` en `partida.log` (T071). La interfaz no llama a Lógica ni a Data.
- [ ] T054 [US1] (FR-409, FR-423) En `UIController/ControlesJuego.py` agregar `procesar_comando(texto)`: valida la **estructura** (`historia <t>` con entero ≥ 0, `historia #k` con entero ≥ 1; otra cosa → mensaje de uso, sin tocar la partida) y llama al backend. Hace pasar T052.
- [ ] T055 [P] [US1] Escribir `tests/test_vista_historia.py` (en el estilo de `tests/test_vista_hud.py`, con `SDL_VIDEODRIVER=dummy`): `test_h1_11_fr423_la_vista_muestra_el_resumen` (reloj, sala, vida, inventario sin cursor, efectos, enemigos) y `test_fr406_la_vista_no_muestra_mensajes_del_juego_en_el_resumen`.
- [ ] T056 [US1] (FR-423) En `View/…` (el archivo del panel o la pantalla que corresponda, por ejemplo `View/HudJuego.py`) y en la entrada de texto del controlador de pygame: línea de comandos para escribir `historia <t>` / `historia #k` y panel de solo lectura que muestra el `ResumenHistoriaDTO`. La tecla **Enter** abre la línea de comandos como un campo de texto (como el de la pantalla de nombre); Enter confirma y Esc la cierra sin pausar el juego. La misma línea la usará «ir a» (spec 002). Cerrar el panel devuelve el juego tal cual estaba. Hace pasar T055. Anotar la tecla (Enter) en el README (T065).
- [ ] T057 [US1] Correr todas las pruebas y seguir [quickstart.md](quickstart.md) §1 de punta a punta, con la interfaz.

---

## Fase 9: Bench M1 a M6 (NFR-401, §5.5, §6.1, §6.3)

**Propósito**: evidencia de rendimiento y de memoria. Todo con criptas sintéticas deterministas por semilla.

- [ ] T058 [P] Escribir `tests/test_bench_linea_tiempo.py`: cada función de `Service/BenchLineaTiempo.py` corre sin vista con tamaños chicos (por ejemplo, 50 acciones) y devuelve una lista de `ResultadoBenchDTO` con el subsistema y el caso esperados (`test_bench_m1_tiempo_de_historia_fr401_nfr401`, `test_bench_m3_memoria_nfr402`, `test_bench_m4_ubicar_punto_nfr401`, `test_bench_m5_costo_de_una_copia_nfr401`, `test_bench_m6_recorte_nfr403`); y `BenchInventario.medir()` incluye el subsistema «línea de tiempo».
- [ ] T059 Crear `Service/BenchLineaTiempo.py` (mismo cronómetro `Service/Cronometro.py` y formato `ResultadoBenchDTO` que `Service/BenchInventario.py`): **M1** tiempo de `historia` con K ∈ {1, 5, 20, 100} y la alternativa **sin puntos de control**, con 5 000 acciones; **M2** el mismo tiempo según la posición consultada (inicio, mitad, final); **M3** memoria como bytes del archivo serializado y conteo de elementos guardados, con 100, 1 000 y 5 000 acciones (sin `tracemalloc`); **M5** costo de una copia con 6, 50, 1 000 y 10 000 salas y con 0, 10 y 100 enemigos. Las cuadrículas sintéticas son deterministas por semilla (reutilizar `cuadricula_con_costos` de `tests/ayudas_terreno.py` como modelo; en `Logic/BenchLogica.py` se puede importar `_cuadricula`). Cita NFR-401 y NFR-402.
- [ ] T060 En `Service/BenchLineaTiempo.py`: **M4** ubicar el punto de control con búsqueda binaria contra recorrido lineal, con 100, 1 000 y 10 000 puntos; **M6** costo del **recorte más la copia del punto de control** (`PartidaGuardada.guardar` + `retroceder_una`) al usar un pergamino, con historias de 100 a 5 000 acciones (NFR-403: no debe crecer con la historia); y para el §5.6, el costo por acción de `ServicioLineaTiempo.ejecutar` **con y sin** línea activa. Cita NFR-401 y NFR-403.
- [ ] T061 (NFR-401) En `Service/BenchInventario.py`, `medir()`: devolver también `BenchLineaTiempo.medir()` (una línea; así no se toca `Service/ServicioBench.py`, que es del integrante 2). Es un cambio a código de la primera entrega, indispensable para exponer el bench nuevo y registrado en la tabla del plan. Hace pasar T058.
- [ ] T062 Correr `python -m Service.ServicioBench` y guardar la tabla. Comprobar el criterio de §6.1: con 5 000 acciones del jugador y el K por defecto, `historia` tarda menos de 50 ms (SC-405). **Confirmar o cambiar el K por defecto de 20**: elegir el K más grande (menos memoria) que cumpla con margen; si cambia, actualizar `CHECKPOINT_POR_DEFECTO` en `DTO/ConfiguracionDTO.py` y la prueba `test_fr415_checkpoint_por_defecto_provisional_es_20` de T049. Anotar si la decisión final coincide con el valor provisional del plan.

---

## Fase 10: `DECISIONES.md` — secciones §5.5 y §5.6 (Principio VIII)

- [ ] T063 (NFR-401) **Completar** la sección «Integrante 3 — 004» de `DECISIONES.md` (raíz del repositorio; ya la creó el integrante 1 con esa sección vacía, «(pendiente)») con el apartado **§5.5 Línea de tiempo y puntos de control**, a partir de [research.md](research.md) R1 a R10 y de los números de T062: por cada decisión (hacia adelante frente a hacia atrás, reconstrucción sin efectos, autocontención de la línea, pergamino y recorte, búsqueda binaria, `avanzar_hasta`, contenido en el archivo, K por defecto, historial de retroceso), problema, alternativas, decisión, complejidad, evidencia empírica y límites, con enlaces a la spec y al plan e indicando si la decisión final coincide con la del plan original. Incluir el pergamino como **punto de control nuevo en `c`** (R4, FR-424, T034) y por qué es más simple y exacta que los marcadores que se descartaron, y la revisión de estructuras existentes (R0).
- [ ] T064 (NFR-401) **Completar** en la misma sección «Integrante 3 — 004» de `DECISIONES.md` el apartado **§5.6 Revisión de decisiones de la primera parte**: repetir las mediciones de la primera parte con la carga nueva (la agenda de eventos con `avanzar_hasta`, el ciclo de eventos y el historial de retroceso con la línea activa, usando los resultados de T060) y mostrar el antes y el después, o los datos que muestran que la decisión sigue siendo adecuada. Si algún cambio modifica una decisión de la primera parte, mostrar el antes y el después.

---

## Fase 11: README y cierre

- [ ] T065 [P] En `README.md`, documentar los comandos nuevos: `historia <t>`, `historia #k`, `--replay partida.log --hasta T` (con sus códigos de salida 0, 1 y 2), `--replay` sin `--hasta` y `--checkpoint-cada K` (con el valor por defecto confirmado en T062), el archivo de partida versión 2 y que los archivos de la primera parte se rechazan como incompatibles.
- [ ] T066 [P] En `specs/004-linea-tiempo/spec.md`, tabla «Trazabilidad del Apéndice B» y la de escenarios adicionales, cambiar «Se define en `tasks.md`» por el nombre de cada prueba (ver «Cobertura» al final de este archivo). Se hace en un **commit `spec(004)` aparte**, separado del código (Principio IX).
- [ ] T067 Revisión de restricciones (Principio II): `grep -rnE "import copy|from copy|bisect|heapq|collections|\bsorted\(|\.sort\(|tracemalloc" Logic Estructuras DTO Service` no debe mostrar coincidencias nuevas en el código de esta feature; y que `grep -rnE "^(from|import) (Data|Service)" Logic` no muestre nada nuevo.
- [ ] T068 Seguir [quickstart.md](quickstart.md) de punta a punta (pruebas, 6 casos del Apéndice B, equivalencia, consultas sin alterar la partida, guardado, K, bench) y registrar en `PROMPTS_LLM.md` cada prompt usado durante la implementación (Principio XI).

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1 (preparación)**: T001 se puede hacer ya. T002, T003, T004 y T071 se coordinan en paralelo y **no bloquean** hasta la fase 6 (T002 y T003) o hasta que exista la spec 002 (T004).
- **Fase 2 (base)**: no depende de otras tareas (T069 toca `ConfiguracionDTO.py`, de Derek: se confirma con el integrante 2). Bloquea todas las historias.
- **Fase 3 (US1)**: depende de la fase 2. T012 (integrante 3, revisa Marco) bloquea T021. Es el MVP.
- **Fase 4 (US3)**: depende de la fase 3 (reutiliza el reconstructor y el registro). Orden dentro de la fase: T027 y T029/T033 (pruebas), T028, T030, T032 y T034 (T030 usa T028; T034 usa T028 y T030).
- **Fase 5 (US2)**: depende de la fase 3. Puede ir en paralelo con la fase 4 (archivos distintos), pero T039 usa `ServicioLineaTiempo.ejecutar`, que gana el caso del pergamino en T030, y depende de T071 (el log con «ir a» solo se lee si `BitacoraReplayIO.leer` ignora esas líneas).
- **Fase 6 (US4)**: depende de la fase 3, de T002 y T003 (integrante 2) y de T010. Mejor después de la fase 4, para guardar también el punto que deja el pergamino.
- **Fase 7 (US5)**: depende de la fase 3. Puede ir en paralelo con las fases 4 a 6.
- **Fase 8 (interfaz)**: depende de la fase 3 (consultas) y, para el comando completo, de la fase 4.
- **Fase 9 (bench)**: depende de las fases 3, 4 y 6 (mide consulta, recorte y serialización).
- **Fase 10 (DECISIONES.md)**: depende de la fase 9 (usa sus números) y de T034.
- **Fase 11 (cierre)**: depende de todo lo anterior. T066 depende de que existan los nombres de las pruebas (fases 3 a 8).
- **T018** depende de T069, que crea `checkpoint_cada` y la constante provisional en `DTO/ConfiguracionDTO.py`; T050 solo conecta la bandera `--checkpoint-cada`.

### Dentro de cada historia

- Las pruebas primero, y deben fallar.
- Estructuras y DTO antes que Lógica; Lógica antes que Service; Service antes que la interfaz.
- Correr todas las pruebas al final de cada fase.

### Grafo de dependencias

```text
T001 ─────────────────────────────────────────────────────────────► (todas las pruebas de Service)
T002, T003 (integrante 2) ────────────────────────────────────────────────────────────► T045, T046
T004 (integrante 2) ──► (no bloquea; cuando exista la spec 002)
T071 (integrante 2) ──► T039, T041   (BitacoraReplayIO.leer ignora «# ir a»)
T005 ─► T006 ──┐
T007 ─► T008 ──┼─► Fase 2 ──► US1: T011 ─► T012 (integ. 3, revisa Marco) ─┐
T009, T010 ────┘                     T013 ─► T014 ──────────────┼─► T021 ─► T023 ─► T025 ─► T026
T069 ──────────────────────────────► T015 ─► T016 ─► T018 ─► T019 ─┘   (T018 depende de T069)
                                                                  │
   US3 (T027–T035) ◄──────────────────────────────────────────────┤
   US2 (T036–T042) ◄──────────────────────────────────────────────┤  (US3 y US2 pueden ir en paralelo)
   US5 (T049–T051) ◄──────────────────────────────────────────────┤
   US4 (T043–T048) ◄── T002, T003, T010, T028 ────────────────────┘
   Interfaz (T052–T057) ◄── US1 (y US3)
   Bench (T058–T062) ◄── US1, US3, US4 ──► DECISIONES.md (T063, T064) ──► Cierre (T065–T068)
```

## Oportunidades de paralelismo

- **Fase 1**: T001 mientras se esperan T002, T003 y T004.
- **Fase 2**: T005, T007, T009 y T010 a la vez (archivos de prueba distintos); luego T006 y T008. T069 va aparte (archivo de Derek).
- **US1**: T013, T015, T017, T020, T022 y T024 se pueden escribir a la vez (archivos distintos); T011 es de otro archivo y también. Luego T014 y T016 a la vez.
- **US3, US2 y US5** pueden avanzar a la vez después de la fase 3.
- **Fase 8**: T052 y T055 a la vez.
- **Fase 9**: T058 con T059.
- **Fase 11**: T065 y T066 a la vez.
- Las pruebas de `tests/test_linea_tiempo_logica.py` (T007, T027, T043) **no** son paralelas entre sí: es el mismo archivo. Lo mismo con `tests/test_linea_tiempo_pergamino.py` (T029, T033), `tests/test_dto_linea_tiempo.py` (T009, T010) y `Service/ServicioLineaTiempo.py` (T019, T025, T030).

### Ejemplo de paralelismo: historia 1

```text
Tarea: "Escribir tests/test_despacho_acciones.py"      (T013)
Tarea: "Escribir tests/test_grabadores_linea.py"      (T015)
Tarea: "Escribir tests/test_armador_resumen.py"       (T022)
# luego:
Tarea: "Crear Service/DespachoAcciones.py"            (T014)
Tarea: "Crear Service/GrabadoresLinea.py"             (T016)
```

## Estrategia de implementación

### Primero el MVP (historia 1)

1. Fases 1 y 2: búsqueda binaria, línea en Lógica y DTOs.
2. Fase 3: `avanzar_hasta`, despacho, grabadores, registro, reconstructor, resumen y consultas.
3. **Parar y validar**: `python tests/correr_pruebas.py` y los casos 1, 3 y 4 del Apéndice B. Ya se puede consultar la partida en vivo.

### Entrega incremental

1. + Historia 3: el pergamino recorta la línea (caso 2 del Apéndice B) y la numeración de enemigos coincide (H-1).
2. + Historia 2: `--replay … --hasta` (caso 5).
3. + Historia 4: guardar y cargar con la línea (caso 6), cuando el integrante 2 entregue T002 y T003.
4. + Historia 5: `--checkpoint-cada`.
5. + Interfaz: el comando `historia`.
6. + Bench, `DECISIONES.md`, README y trazabilidad.

Cada paso deja todas las pruebas en verde.

### Commits sugeridos (los hace el integrante 3)

Uno por fase o por grupo lógico, por ejemplo: `feat(004): búsqueda binaria y línea de tiempo en Lógica`,
`feat(004): consultar historia (reconstructor, resumen, servicio)`, `feat(004): recorte con el pergamino`,
`feat(004): --replay --hasta`, `feat(004): guardar y cargar la línea`, `feat(004): --checkpoint-cada`,
`feat(004): comando historia en la interfaz`, `bench(004): mediciones de la línea de tiempo`,
`spec(004): nombres de las pruebas en la trazabilidad` (T066, siempre en un commit aparte del código), `docs(004): DECISIONES.md §5.5 y §5.6 y README`. El código de la tarea T012 lo commitea el integrante 3, después de la revisión de Marco.

---

## Cobertura: escenarios y casos del Apéndice B

| Escenario / caso | Prueba | FR |
|---|---|---|
| H1-1 (Apéndice B, caso 1) | `test_h1_1_apendiceB_caso1_fr409_instante_posterior` (T024) | FR-409 |
| H1-2 (Apéndice B, caso 3) | `test_h1_2_apendiceB_caso3_fr402` (T011) | FR-402 |
| H1-3 (Apéndice B, caso 4) | `test_h1_3_apendiceB_caso4_fr407_fr408_no_altera_la_partida` (T024) | FR-407, FR-408 |
| H1-4 | `test_h1_4_fr404_fr405_contenido_del_resumen` (T022) | FR-404, FR-405 |
| H1-5 | `test_h1_5_fr409_accion_fuera_de_rango` (T024) | FR-409 |
| H1-6 | `test_h1_6_fr401_fr414_accion_ya_no_revertible` (T024) | FR-401, FR-414 |
| H1-7 | `test_h1_7_fr409_instante_igual_al_reloj` (T024) | FR-409 |
| H1-8 | `test_h1_8_fr419_consulta_repetida` (T024) | FR-419 |
| H1-9 | `test_h1_9_fr402_decision_del_jugador_en_t` (T011) y `test_h1_9_fr402_historia_t_igual_a_historia_k` (T024) | FR-402 |
| H1-10 | `test_h1_10_fr406_sin_cursor_ni_mensajes` (T022) | FR-406 |
| H1-11 | `test_h1_11_fr423_historia_t` y `test_h1_11_fr423_historia_k` (T052) | FR-423 |
| H1-12 | `test_h1_12_fr402_fr405_partida_terminada_en_t` (T011) | FR-402, FR-405 |
| H2-1 | `test_h2_1_fr410_fr411_mismo_resumen_que_historia_t` (T038) | FR-410, FR-411 |
| H2-2 (Apéndice B, caso 5) | `test_h2_2_apendiceB_caso5_fr412_t_posterior_al_final` (T038) | FR-405, FR-412 |
| H2-3 | `test_h2_3_fr410_*` (T036) y `test_h2_3_fr410_codigo_2_*` (T040) | FR-410 |
| H2-4 | `test_h2_4_fr410_codigo_1_*` (T040) | FR-410 |
| H2-5 | `test_h2_5_fr402_fr410_hasta_cero_es_el_estado_inicial` (T038) | FR-402, FR-410 |
| H2-6 | `test_h2_6_fr410_sin_hasta_reproduce_todo` (T038) y `test_h2_6_fr410_replay_sin_hasta_es_la_partida_completa` (T036) | FR-410 |
| H3-1 (Apéndice B, caso 2) | `test_h3_1_apendiceB_caso2_fr413_fr409` (T029) | FR-404, FR-409, FR-413 |
| H3-2 | `test_h3_2_fr413_accion_nueva_es_la_cinco` (T029) | FR-413 |
| H3-3 | `test_h3_3_fr409_fr413_limite_es_el_reloj_actual` (T029) | FR-409, FR-413 |
| H3-4 | `test_h3_4_fr413_varios_pergaminos_seguidos` (T029) | FR-413 |
| H3-5 | `test_h3_5_fr413_fr419_fr424_pergamino_recogido_en_la_accion_revertida` (T033) | FR-413, FR-419, FR-424 |
| H3-6 | `test_h3_6_fr413_fr419_fr424_pergamino_soltado_en_la_accion_revertida` (T033) | FR-413, FR-419, FR-424 |
| H4-1 | `test_h4_1_fr420_mismos_resumenes_tras_guardar_y_cargar` (T045) | FR-420 |
| H4-2 | `test_h4_2_fr420_se_puede_seguir_jugando_tras_cargar` (T045) | FR-420 |
| H4-3 (Apéndice B, caso 6) | `test_h4_3_apendiceB_caso6_fr421_archivo_de_la_primera_parte` (T045) | FR-421 |
| H5-1 | `test_h5_1_fr418_mismos_resumenes_con_k_1_5_y_50` (T049) | FR-418 |
| H5-2 | `test_h5_2_fr416_ninguna_consulta_reaplica_mas_de_k_acciones` (T049) | FR-416 |
| H5-3 | `test_h5_3_fr415_valores_invalidos` (T049) | FR-415 |
| H5-4 | `test_h5_4_fr415_valor_por_defecto` (T049) | FR-415 |

| NFR | Dónde se verifica |
|---|---|
| NFR-401 | T058 a T062 (bench con al menos tres valores de K y la alternativa sin puntos de control) y T063 |
| NFR-402 | `test_bench_m3_memoria_nfr402` (T058) y M3 (T059) |
| NFR-403 | `test_retroceder_una_no_recorre_la_historia_nfr403` (T027) y M6 (T060) |
