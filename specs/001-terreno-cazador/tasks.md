---
description: "Lista de tareas de la feature 001: terreno con costo por salida y enemigo cazador"
---

# Tareas: Terreno con costo por salida y enemigo cazador

**Entrada**: documentos de diseño de `specs/001-terreno-cazador/`

**Prerrequisitos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Pruebas**: sí. La constitución (Principio X) pide una prueba por escenario y por caso del
Apéndice B, y el plan pide `unittest` en `tests/`. Cada prueba cita su FR en el nombre del método o
en el docstring. Se escriben **antes** que el código y deben fallar primero.

**Organización**: una fase por historia de la spec (H1 → US1, H2 → US2, H3 → US3, H4 → US4).

**Responsable**: integrante 1. Las tareas marcadas **(integrante 2)** o **(integrante 3)** no las
hace el integrante 1: solo se comprueba que estén y se coordinan.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas sin terminar).
- **[US1]…[US4]**: historia de la spec a la que pertenece la tarea.

## Reglas para todas las tareas (constitución v1.2.0)

- Python 3.11. Sin dependencias nuevas.
- Prohibido en `Logic/`, `Estructuras/` y `DTO/`: `dict` o `set` como índice o caché, `heapq`,
  `bisect`, `collections`, `copy`, bibliotecas de grafos o rutas, y `sorted()` / `list.sort()`
  (si hace falta ordenar, `Estructuras/Ordenador.py`). `copy` solo en `tests/`.
- `Logic/` no importa `Data/` ni `Service/`. `Estructuras/` no importa ninguna capa.
- Código nuevo con type hints y docstring breve. Comentarios y nombres en español, como el resto
  del proyecto.
- Toda caché que sea estado del juego se registra en `HistorialRetroceso`.
- Las pruebas usan `unittest` y corren con `python tests/correr_pruebas.py`.
- Vocabulario: una **puerta** está abierta o cerrada; una **sala** de la búsqueda está **resuelta**
  cuando su distancia ya es definitiva.

---

## Fase 1: Preparación

**Propósito**: los datos de los que depende todo y los ayudantes de prueba.

- [X] T001 **(integrante 2)** Confirmar que `SalidaDTO` en `DTO/SalaDTO.py` ya tiene `costo: int | None = None` como **último** campo (después de `cierre_automatico`, para que `SalidaDTO(1, True, "llave")` siga funcionando). `None` significa «este lado no declara costo». `desde_diccionario` lee `d.get("costo")` y `a_diccionario` escribe `"costo"` solo si no es `None`, según [contracts/contrato-datos.md](contracts/contrato-datos.md). El integrante 1 **no** escribe este código. Si aún no está, esperar: bloquea T004 en adelante.
- [X] T002 **(integrante 2)** Coordinar la validación de FR-122 en Data, según [contracts/contrato-datos.md](contracts/contrato-datos.md): costo que no es entero (incluido `bool`) o es menor que 1; salida cuyos **dos lados** declaran costos distintos (se comprueba con el esqueleto completo); ficha con `comportamiento == "cazador"` cuyo `rango` falta, es `null`, no es entero (incluido `bool`) o es negativo. Efecto, según de dónde venga el dato: (a) **esqueleto** (costos): error de formato con contexto y la partida no inicia; (b) **ficha de un cazador de la sala inicial**: la partida no inicia; (c) **ficha de cualquier otra sala**, llegue antes o durante la partida: se rechaza con un error de datos (T052) y esa sala queda como contenido no disponible; intentar entrar se rechaza con ese mensaje y la partida sigue (T053, escenario H2-9). En todos los casos el programa no se cae. No bloquea las fases siguientes: Lógica supone datos válidos. La prueba se verifica en T050 y en T054.
- [X] T052 **(integrante 2)** Coordinar en Data (FR-122): rechazar la ficha de cazador con `rango` ausente o inválido con un **error de datos** con contexto (ficha y campo), que se pueda distinguir del error de red (hoy `FuenteDatos` usa `ErrorRed` para los dos; por ejemplo, una subclase propia de `ErrorRed`, para no romper los `except` de P1); **recordar el rechazo por sala** sin gastar otra solicitud (`asegurar_sala` vuelve a lanzar el mismo error al intentar entrar); y que **solo esa sala** quede sin contenido: las demás salas del mismo lote se cargan normalmente (hoy `resolver_pendientes` marca el lote como cargado antes de resolver el catálogo). No bloquea a Lógica; bloquea T053 y quitar el `skip` de T054.
- [X] T053 **(integrante 3)** Coordinar en Service (FR-122, escenario H2-9): en `ServicioAccionJugador.ejecutar`, cuando llega el error de datos de T052 al intentar entrar a una sala, mostrar **ese** mensaje (ficha y campo) al rechazar el movimiento, en lugar de «Sin conexión con el servicio». El movimiento ya no se ejecuta ni se anexa al log, como hoy con `ErrorRed`. Depende de T052. Al terminar, quitar el `skip` de T054.
- [X] T003 [P] Crear `tests/ayudas_terreno.py` con ayudantes de prueba (con docstring): `salidas_con_costos(cantidad, salidas)`, que arma una lista de `SalaDTO` donde `salidas` es una lista de tuplas `(sala_a, direccion_a, sala_b, costo_a, costo_b, cerrada)` y genera **las dos caras** (dirección opuesta en `sala_b`, usando `DTO/Direcciones.py`); `costo_a` y `costo_b` pueden ser `None` (lado sin costo declarado); `salida(sala_a, direccion_a, sala_b, costo=None, cerrada=False)`, atajo que devuelve la tupla con el mismo costo en los dos lados; `salida_sin_vuelta(...)` para una sola cara; `cuadricula_con_costos(n, azar)`, que devuelve la lista de `SalaDTO` de una cuadrícula de n × n salas, con los mismos ids y vecinas que `salas_cuadricula(n)` de `tests/Utilidades.py`, y en cada salida un costo entre 1 y 300 sacado de `azar` (un `random.Random` que recibe la prueba), **el mismo en los dos lados**; `mazmorra_con_costos(cantidad, salidas)`, que arma la `Mazmorra` con todo el contenido marcado como cargado; `ficha_cazador(rango, velocidad=100, **cambios)`, `ficha_errante(...)` y `ficha_rastreador(...)` sobre `FichaEnemigoDTO`; `motor_con(mazmorra, sala_jugador, semilla=1)`, que devuelve `(motor, mensajes)` como `crear_motor` de `tests/test_logica.py`; y `poner_enemigo(...)`, que lo coloca y lo activa con `motor.activar_enemigos`.

---

## Fase 2: Base (bloquea todas las historias)

**Propósito**: que Lógica conozca el costo de cada salida, igual en los dos sentidos.

**⚠️ Ninguna historia empieza antes de terminar esta fase.**

- [X] T004 Escribir `tests/test_mazmorra_costos.py` (debe fallar), citando FR-101, FR-104 y FR-119: los dos lados declaran el mismo costo → ese costo; solo un lado lo declara → los **dos** lados valen ese costo; ninguno lo declara → 100; salida sin vuelta sin costo → 100; si el esqueleto se carga en dos llamadas a `cargar_esqueleto` (una sala primero y su vecina después), el costo se iguala al llegar la segunda; `salidas_abiertas_con_costo(id_sala)` devuelve pares `(destino, costo)` en el **mismo orden** y con la **misma longitud** que `salidas_abiertas(id_sala)`, incluidas dos salidas hacia la misma sala; `costo_paso(origen, destino)` devuelve el **menor** costo entre las salidas **abiertas** de `origen` hacia `destino` e ignora las cerradas. Usar `tests/ayudas_terreno.py`.
- [X] T005 En `Logic/Mazmorra.py`, `SalidaViva.__init__`: agregar `self.costo_declarado = salida_dto.costo` y `self.costo = salida_dto.costo if salida_dto.costo is not None else 100` (dos líneas; fila de `SalidaViva` en la tabla de cambios a P1 del plan). No se registran en el historial: no cambian durante la partida (FR-101).
- [X] T006 En `Logic/Mazmorra.py`, clase `Mazmorra`: agregar el método privado `_igualar_costos(self) -> None`, con docstring, **junto a** `_igualar_caras` y sin modificarlo. Para cada cara: si `costo_declarado` no es `None`, `costo = costo_declarado`; si no, busca la inversa con `self._salida_inversa(...)` y usa su `costo_declarado` si existe y no es `None`, o 100. Recorre todas las salas en cada llamada, así que el resultado no depende del orden en que llegan las páginas. No valida costos distintos en los dos lados: eso es de Data (T002). En `cargar_esqueleto`, llamar a `self._igualar_costos()` justo después de `self._igualar_caras()` (una línea).
- [X] T007 En `Logic/Mazmorra.py`, clase `Mazmorra`: agregar `salidas_abiertas_con_costo(self, id_sala: int) -> list[tuple[int, int]]` (mismo recorrido y mismos filtros que `salidas_abiertas`: no `None`, no cerrada, `self._existe(destino)`) y `costo_paso(self, origen: int, destino: int) -> int` (mínimo entre las salidas abiertas de `origen` hacia `destino`), con docstring. No cambiar `salidas_abiertas`. Con T005 y T006, hace pasar T004.

**Punto de control**: `python -m unittest tests.test_mazmorra_costos -v` en verde y `python tests/correr_pruebas.py` sin regresiones.

---

## Fase 3: Historia 1 — El terreno cuesta distinto (Prioridad: P1) 🎯 MVP

**Objetivo**: moverse por una salida cuesta su costo, para el jugador y para todos los enemigos.

**Prueba independiente**: con dos salidas de costos distintos, mover al jugador por cada una y
comparar el instante de su siguiente acción. No hace falta ningún cazador.

### Pruebas de la historia 1 ⚠️ (escribirlas primero; deben fallar)

- [X] T008 [US1] En `tests/test_terreno_cazador.py` (archivo nuevo), clase `TestTerreno`, una prueba por escenario, con el FR en el nombre: `test_h1_1_fr102_salida_costo_250` (t = 250), `test_h1_2_fr101_salida_sin_costo_vale_100` (t = 100), `test_h1_3_fr101_mismo_costo_en_ambos_sentidos`, `test_h1_4_apendiceB_caso6_fr102_intervalo_minimo_1` (velocidad 300, costo 1 → t = 1, nunca 0), `test_h1_5_apendiceB_caso7_fr105_cambio_de_velocidad` (velocidad 100, costo 400, en t = 100 pasa a 200 con `motor.cambiar_velocidad` → siguiente acción en t = 250), `test_h1_6_fr103_otras_acciones_conservan_costo` (atacar 100, esperar 100, usar 50), `test_h1_7_fr104_errante_paga_la_salida_sorteada` (única salida de costo 300 → su siguiente acción a 300 unidades), `test_h1_8_fr101_costo_declarado_en_un_solo_lado` (solo el lado de la sala 1 declara 250; ir de 2 a 1 en t = 0 deja la siguiente acción en t = 250).
- [X] T009 [US1] En `tests/test_terreno_cazador.py`, clase `TestTerrenoComportamientos`: `test_fr104_errante_sortea_por_salida_igual_que_p1` (con la misma semilla, `Errante.decidir_paso` escoge el mismo índice y deja el generador en el **mismo estado** que `Errante.decidir`; con dos salidas hacia la misma sala de costos 100 y 300, paga el costo de la salida sorteada); `test_fr104_rastreador_usa_la_salida_mas_barata` (dos salidas hacia la sala con rastro fresco, costos 300 y 120 → paga 120); `test_fr104_guardian_no_se_mueve`; y `test_fr102_enemigo_programa_con_costo_de_salida` (`turno_enemigo` programa la siguiente acción con max(1, costo × 100 // velocidad)).

### Implementación de la historia 1

- [X] T010 [US1] En `Logic/motorJuego.py`, `mover_jugador`: cambiar `self.terminar_accion_jugador(self.COSTO_MOVER)` por `self.terminar_accion_jugador(salida.costo)` (FR-102). No borrar `COSTO_MOVER`.
- [X] T011 [US1] En `Logic/Comportamientos.py`, clase `Comportamiento`: agregar `decidir_paso(self, enemigo, motor) -> tuple[int, int] | None`, con docstring. Llama a `self.decidir(enemigo, motor)`; si devuelve `None`, devuelve `None`; si devuelve un destino, devuelve `(destino, motor.mazmorra.costo_paso(enemigo.Sala_Actual, destino))`. `Guardian` y `Rastreador` lo heredan sin cambios (FR-102, FR-104).
- [X] T012 [US1] En `Logic/Comportamientos.py`, clase `Errante`: agregar `decidir_paso` con el **mismo** sorteo que `decidir`: `opciones = motor.mazmorra.salidas_abiertas_con_costo(enemigo.Sala_Actual)`; si está vacía, `None`; si no, `opciones[motor.azar.randint(0, len(opciones) - 1)]`. **No** cambiar `decidir` (FR-104, Principio IV: misma secuencia del generador que P1).
- [X] T013 [US1] En `Logic/motorJuego.py`, `turno_enemigo`: en la rama sin ataque, usar `paso = enemigo.estrategia.decidir_paso(enemigo, self)`; si no es `None`, `destino, costo = paso`, mover con `self.mazmorra.mover_enemigo` y mantener el mensaje de «entra a la sala»; programar con `self.programar_accion(enemigo, costo)` si se movió, o con `100` si atacó o esperó (FR-102, FR-103, FR-121). No cambiar la rama de ataque.
- [X] T014 [US1] Correr `python tests/correr_pruebas.py`: T008 y T009 en verde y **ninguna** prueba de P1 rota (sin `costo`, todo vale 100 y las partidas de P1 dan lo mismo). Si alguna prueba de P1 cambia, detenerse y documentarlo antes de seguir. Equipar, recoger, soltar y abrir una puerta con llave (FR-103) no cambian de costo y quedan cubiertos por las pruebas de P1 que corren aquí; T008 solo agrega atacar, esperar y usar.

**Punto de control**: la historia 1 funciona sola. Se puede entregar sin cazadores.

---

## Fase 4: Historia 2 — El cazador persigue por la ruta más barata (Prioridad: P1)

**Objetivo**: el cuarto comportamiento, «cazador», correcto en cada turno. En esta fase cada
decisión se calcula **desde cero** (sin reutilizar nada); la reutilización llega en la historia 3.

**Prueba independiente**: con una cripta pequeña, un cazador y rutas de costos distintos,
comprobar en cada turno del cazador qué hace, a qué sala va y cuánto cuesta.

### Pruebas de la historia 2 ⚠️ (escribirlas primero; deben fallar)

- [X] T015 [P] [US2] Crear `tests/test_monticulo_minimo.py`: extrae en orden de clave; con claves iguales, en orden de valor; admite entradas repetidas de la misma sala (borrado perezoso); `ver_minimo()` devuelve `None` si está vacío; `tamano()`, `esta_vacio()` y `vaciar()`; 1 000 inserciones con `random.Random(7)` salen en el mismo orden que una referencia hecha **en la prueba** con `sorted` (en `tests/` está permitido como oráculo).
- [X] T016 [P] [US2] Crear `tests/test_dto_terreno.py`: `FichaEnemigoDTO.desde_diccionario` lee `rango` (600) y lo deja en `None` si falta; `a_diccionario` escribe `"rango"` solo si no es `None`; ida y vuelta igual; `"rango"` **no** aparece también en `extras`; una ficha de P1 sin `rango` se lee y se escribe exactamente igual que antes (FR-106).
- [X] T017 [P] [US2] Crear `tests/test_busqueda_costo_minimo.py` sobre un grafo de prueba hecho en la propia prueba (clase con `cantidad_salas`, `entradas`, `salidas`, según [contracts/busqueda-rutas.md](contracts/busqueda-rutas.md)): distancias correctas con costos no uniformes (FR-108); `distancia_hasta` devuelve `None` si no hay ruta o si d > límite y devuelve d cuando d = límite (FR-109, FR-110); la búsqueda se **reanuda**: dos consultas seguidas con límites 100 y luego 500 dan lo mismo que una sola con 500, y `resueltas` no cuenta dos veces la misma sala; `reiniciar` cambia la generación sin recorrer los arrays (las distancias viejas no se filtran a la nueva búsqueda); salida sin vuelta (se recorre al revés: R3); `paso_hacia_origen` escoge la vecina de **menor id** sin importar el orden de las salidas (FR-111) y, con dos salidas hacia la misma vecina, usa el **menor** costo (FR-119); `paso_desde_cero` da lo mismo que una búsqueda nueva.
- [X] T018 [US2] En `tests/test_terreno_cazador.py`, clase `TestCazador`, un escenario por prueba: `test_h2_1_apendiceB_caso1_fr109_sin_ruta_abierta_espera` (espera, costo 100, no cambia de sala); `test_h2_2_apendiceB_caso2_fr109_d700_mayor_que_rango600_espera`; `test_h2_3_apendiceB_caso3_fr110_ruta_de_mas_salas_y_menor_costo` (va a la sala 2, costo 100); `test_h2_4_apendiceB_caso4_fr111_desempate_menor_id` (la salida hacia 7 aparece **antes** que la de 4 en la sala 1 → va a la 4); `test_h2_5_fr107_misma_sala_ataca_y_no_se_mueve`; `test_h2_6_fr110_d_igual_a_rango_se_mueve` (d = 600 → sala 2, costo 250); `test_h2_7_fr102_velocidad_120_costo_250_intervalo_208`; `test_h2_8_fr112_ignora_contenido_no_descargado` (la sala intermedia con `contenido_cargado = False` no cambia la decisión).
- [X] T019 [US2] En `tests/test_terreno_cazador.py`, clase `TestCazadorBordes`: `test_fr113_no_abre_puertas` (la llave en la sala del cazador no cambia nada); `test_fr119_dos_salidas_misma_vecina_paga_la_mas_barata`; `test_fr120_otros_actores_no_bloquean` (un guardián y otro cazador en la ruta); `test_fr121_entra_a_la_sala_y_no_ataca_en_ese_turno` (la vida del jugador no cambia en ese turno y sí en el siguiente); `test_fr123_dormido_no_actua_hasta_activarse`; `test_rango_0_solo_ataca_en_la_misma_sala`; `test_fr115_decidir_no_consume_el_generador` (el estado de `motor.azar.getstate()` es igual antes y después de un turno en el que el cazador se mueve o espera); `test_fr106_crear_comportamiento_cazador` (`crear_comportamiento("cazador")` devuelve un `Cazador`); y `test_fr108_cierre_automatico_en_el_mismo_instante`, con un cierre automático programado en el **mismo t** que el turno del cazador sobre la única puerta de su ruta: si en el orden de eventos de P1 §2.3 el cierre va primero, el cazador espera; si va después, se mueve. En los dos casos coincide con `paso_desde_cero` en el momento de decidir.
- [X] T054 [US2] En `tests/test_terreno_cazador.py`, clase `TestDatosInvalidos`, `test_h2_9_fr122_ficha_invalida_rechaza_entrar` (FR-122). A cargo del integrante 1. Agregar a `tests/ayudas_terreno.py` una fuente de prueba (por ejemplo `FuenteConFichaInvalida`, sobre `FuenteCuadricula` de `tests/Utilidades.py`) que devuelve el error de datos de T052 para una sala cuyo cazador no trae `rango`. Con `ServicioPartida(..., fuente=esa_fuente)`: (1) la precarga llega y la partida sigue: el jugador actúa en otras salas y el cazador no se activa; (2) intentar entrar a esa sala se rechaza con un mensaje que nombra la ficha y el campo `rango`, el jugador sigue en su sala y el reloj no avanza; (3) la partida sigue: el jugador puede hacer otra acción; (4) ese `mover` no queda en `partida.log`; (5) un segundo intento da el mismo mensaje sin una solicitud nueva. Marcarla con `unittest.skip("pendiente de T052 y T053")` hasta que estén hechas.

### Implementación de la historia 2

- [X] T020 [P] [US2] Crear `Estructuras/MonticuloMinimo.py` con la clase `MonticuloMinimo` (sin importar nada de otras capas): `insertar(clave: int, valor: int) -> None` O(log n), `extraer_minimo() -> tuple[int, int]` O(log n), `ver_minimo() -> tuple[int, int] | None` O(1), `esta_vacio() -> bool`, `tamano() -> int`, `vaciar() -> None`. Montículo binario en un `list` usado como array contiguo; compara por clave y luego por valor. Nada de `heapq` (R1). Hace pasar T015.
- [X] T021 [P] [US2] En `DTO/FichaEnemigoDTO.py`: agregar `rango: int | None = None` como **último** campo, después de `extras` (así no se rompe ningún constructor posicional: ni los de 8 argumentos de `Logic/BenchLogica.py` ni los 10 de `desde_diccionario`); agregar `"rango"` a `_CAMPOS`; leerlo con `d.get("rango")` en `desde_diccionario` y escribirlo en `a_diccionario` solo si no es `None`. **No** validar aquí: FR-122 es de Data (T002). Hace pasar T016.
- [X] T022 [US2] Crear `Logic/GrafoEsqueleto.py` con la clase `GrafoEsqueleto(mazmorra)`, que implementa el protocolo de [contracts/busqueda-rutas.md](contracts/busqueda-rutas.md): `cantidad_salas() -> int` (= `len(mazmorra.salas)`); `salidas(u) -> list[tuple[int, int]]` (= `mazmorra.salidas_abiertas_con_costo(u)`); `entradas(x) -> list[tuple[int, int]]` con pares `(origen, costo)` de las salidas **abiertas ahora** que llegan a `x`. La adyacencia inversa (por sala, lista de `(origen, direccion)`) es estática, se arma **una sola vez y de forma perezosa** en la primera llamada a `entradas`, en O(S + E), con arrays (no `dict`); el estado `cerrada` de la puerta se lee en vivo en cada llamada. Excluir destinos que no existen con `mazmorra._existe()`, el mismo filtro de `salidas_abiertas`: es un método privado de `Mazmorra`, pero se prefiere a agregar uno público, que sería otro cambio a código de P1 (Principio III).
- [X] T023 [US2] Crear `Logic/BusquedaCostoMinimo.py` con la clase `BusquedaCostoMinimo(grafo)` (estado y costos en [data-model.md](data-model.md)): arrays `distancia`, `marca_distancia` y `marca_resuelta` de tamaño `grafo.cantidad_salas()` creados una vez; `generacion`; `frontera: MonticuloMinimo`; `origen`; contador `resueltas`. Operaciones: `reiniciar(origen)` (nueva generación, `frontera.vaciar()`, inserta `(0, origen)`); `distancia_hasta(sala, limite: int | None) -> int | None` (extrae mientras la frontera no esté vacía, su mínimo sea ≤ `limite` y `sala` no esté resuelta; al resolver `x` relaja `grafo.entradas(x)`; descarta las entradas viejas del montículo; al final devuelve d si `sala` está resuelta y d ≤ `limite`, o `None`); `esta_resuelta(sala)`; `distancia_resuelta(sala)`; `paso_hacia_origen(u, d) -> tuple[int, int]` (recorre `grafo.salidas(u)`, se queda con la vecina **resuelta** de menor id que cumple `costo + dist(v) = d`, y con el menor costo hacia ella: FR-111, FR-119, R3). Agregar la función `paso_desde_cero(grafo, origen, u, limite) -> tuple[int, int] | None`, que crea una búsqueda nueva y no reutiliza nada (alternativa A de R2). Sin `random`. Hace pasar T017.
- [X] T024 [US2] En `Logic/Comportamientos.py`: agregar la clase `Cazador(Comportamiento)` con `NOMBRE = "cazador"`; `decidir` devuelve el destino de `decidir_paso` (o `None`); `decidir_paso(enemigo, motor)` devuelve `paso_desde_cero(motor.grafo, motor.jugador.Sala_Actual, enemigo.Sala_Actual, enemigo.ficha.rango)`. No usa `motor.azar` (FR-115). Agregar `Cazador` al final de `COMPORTAMIENTOS` (una línea, FR-106). Nota: agregar el caso cazador → 'cazador' a la prueba de T037.
- [X] T025 [US2] En `Logic/motorJuego.py`, `Motor.__init__`: crear `self.grafo = GrafoEsqueleto(mazmorra)` (una línea de las tres de la fila de `Motor.__init__` del plan; T022 lo hace perezoso, así que no importa si el esqueleto se carga después). Correr T018 y T019 hasta que pasen.
- [X] T026 [US2] Correr `python tests/correr_pruebas.py`: todo en verde, incluidas las pruebas de P1.

**Punto de control**: el cazador decide bien en cada turno. Funciona igual sin la historia 3,
solo que recalcula desde cero en cada decisión.

---

## Fase 5: Historia 3 — La decisión sigue siendo correcta cuando el mapa cambia (Prioridad: P2)

**Objetivo**: reutilizar una sola búsqueda para todos los cazadores (R2, R3) y descartarla solo
cuando haga falta (R4), sin que cambie ninguna decisión (FR-114).

**Prueba independiente**: en partidas con puertas que cambian, movimientos del jugador y
pergaminos, cada decisión de cada cazador es igual a la de `paso_desde_cero` en ese instante.

### Pruebas de la historia 3 ⚠️ (escribirlas primero; deben fallar)

- [ ] T027 [US3] Crear `tests/test_rutas_equivalencia.py`, clase `TestEscenariosH3`: `test_h3_1_apendiceB_caso5_fr114_puerta_se_cierra_entre_turnos` (el cazador va a la 2, se cierra 2–4 con `CierrePuerta.activar`, vuelve a la 1 con costo 100, y la decisión coincide con `paso_desde_cero`); `test_h3_2_fr114_jugador_cambia_de_sala`; `test_h3_3_fr114_se_abre_una_puerta_y_crea_ruta` (con `motor.abrir_puerta`); `test_h3_4_fr114_cierre_lejano_no_cambia_la_decision` (además, `rutas.recalculos` no aumenta: R4); `test_h3_5_fr114_muerte_movimiento_y_velocidad_no_invalidan`.
- [ ] T028 [US3] En `tests/test_rutas_equivalencia.py`, clase `TestEquivalenciaAleatoria` (FR-114, SC-102): con `random.Random(semilla)` para varias semillas, en cuadrículas hechas con `cuadricula_con_costos(n, azar)` de `tests/ayudas_terreno.py` (T003), de 5 a 20 cazadores con `rango` distintos, cientos de pasos que mezclan: mover al jugador, abrir y cerrar puertas, cierres automáticos, matar enemigos, cambiar velocidades y leer pergaminos. Antes de **cada** decisión de **cada** cazador, comparar `motor.rutas.decidir(...)` con `paso_desde_cero(...)`. Afirmar también que `rutas.reutilizaciones > 0` (sí se reutiliza).
- [ ] T029 [US3] En `tests/test_rutas_equivalencia.py`, clase `TestHistorial`: `test_pergamino_descarta_la_busqueda` (crear o extender la búsqueda en un intervalo, `historial.deshacer()`, y la siguiente decisión es correcta y empieza desde cero); `test_aviso_de_puerta_se_registra_en_el_historial`; `test_deshacer_un_intervalo_sin_cambios_de_ruta_la_conserva`.
- [ ] T030 [US3] En `tests/test_terreno_cazador.py`, clase `TestDeterminismo`: `test_h3_6_fr115_misma_semilla_misma_partida` (la misma secuencia de acciones con la misma semilla, jugada dos veces, da la misma bitácora y los mismos instantes); `test_sc103_cazadores_no_cambian_lo_que_eligen_los_errantes` (en una partida donde ningún cazador ataca, las salas que eligen los errantes son las mismas con y sin cazadores).

### Implementación de la historia 3

- [X] T031 [US3] En `Logic/Mazmorra.py`: agregar el atributo `self.observador_puertas = None` en `Mazmorra.__init__`. Al final de `abrir_puerta`, después de abrir las caras: `if self.observador_puertas is not None: self.observador_puertas.puerta_cambio(id_sala, salida.destino)`. Al final de `CierrePuerta.activar`, después de cerrar las caras: avisar a `motor.mazmorra.observador_puertas` (si no es `None`) con `puerta_cambio(self.caras[0].destino, self.caras[-1].destino)`. Dejar en un comentario por qué basta con los **destinos** de las caras: una salida u→v solo se lee al resolver v (la búsqueda va al revés, R3); con dos caras son los dos extremos, y con una sola cara es el único extremo que importa. Ver la nota sobre `puerta_cambio` en [contracts/busqueda-rutas.md](contracts/busqueda-rutas.md). Dos líneas en cada punto (FR-114).
- [X] T032 [US3] Crear `Logic/RutasHaciaJugador.py` con la clase `RutasHaciaJugador(grafo, historial)` ([data-model.md](data-model.md)): `busqueda: BusquedaCostoMinimo` creada una vez; `valida: bool`; contadores `reutilizaciones` y `recalculos` (no son estado del juego). `decidir(sala_cazador, sala_jugador, rango) -> tuple[int, int] | None`: si `not valida` o `busqueda.origen != sala_jugador`, `reiniciar(sala_jugador)` y `recalculos += 1`, si no `reutilizaciones += 1`; luego `distancia_hasta(sala_cazador, rango)` y `paso_hacia_origen` (R3). Si creó la búsqueda o resolvió alguna sala nueva, registrar `historial.registrar_cambio(self.descartar)`. `puerta_cambio(a, b)`: si la búsqueda es válida y `a` o `b` está resuelta, `descartar()`; registrar `self.descartar` en el historial **siempre**. `descartar()`: `valida = False`. Si `historial` es `None`, no registra. Sin `dict`, `set` ni `copy`. Nota: la búsqueda se crea en `Motor.__init__`, con el esqueleto ya cargado; sus arrays se reservan una sola vez (ver [data-model.md](data-model.md)).
- [ ] T033 [US3] En `Logic/motorJuego.py`, `Motor.__init__`, después de crear `self.grafo`: `self.rutas = RutasHaciaJugador(self.grafo, self.historial)` y `self.mazmorra.observador_puertas = self.rutas` (las otras dos líneas de la fila de `Motor.__init__` del plan).
- [ ] T034 [US3] En `Logic/Comportamientos.py`, `Cazador.decidir_paso`: cambiar la llamada a `paso_desde_cero(...)` por `motor.rutas.decidir(enemigo.Sala_Actual, motor.jugador.Sala_Actual, enemigo.ficha.rango)` (una línea). Correr T027 a T030 hasta que pasen.
- [ ] T035 [US3] Correr `python tests/correr_pruebas.py`: todo en verde, incluidas las pruebas de P1 y de la historia 2 (que ahora pasan por la búsqueda compartida).

**Punto de control**: las historias 1, 2 y 3 funcionan juntas y cada decisión coincide con un
cálculo desde cero.

---

## Fase 6: Historia 4 — Ver el terreno y reconocer al cazador (Prioridad: P3)

**Objetivo**: que la vista reciba por DTO el costo de cada salida y el comportamiento de cada
enemigo. **Dibujarlos es del integrante 3 (§7.3).**

**Prueba independiente**: el estado que recibe la vista trae los costos de las salidas de la sala
actual y el comportamiento de cada enemigo.

### Pruebas de la historia 4 ⚠️

- [X] T036 [US4] En `tests/test_dto_terreno.py`, `test_h4_1_fr116_el_costo_llega_a_la_vista`: armar el estado con `Service/ArmadorEstado.py` para una sala con salidas de costo 100, 250, una sin costo y una cuyo costo 300 solo lo declara el **otro** lado, y comprobar que los `SalidaDTO` que recibe la vista traen 100, 250, 100 y 300 (el costo ya igualado por Lógica, no el declarado). Corre sin `skip`: T038 ya está integrada. Incluye una salida cerrada (escenario H4-1).
- [X] T037 [US4] En `tests/test_dto_terreno.py`, `test_h4_2_fr117_actor_dto_trae_el_comportamiento` (FR-117), sin `skip`: el `ActorDTO` de un errante trae `comportamiento == "errante"`, el de un guardián `"guardián"`, el de un rastreador `"rastreador"` y el del jugador `None`. El caso del cazador se agrega con T024 (ver su nota).

### Implementación de la historia 4

- [X] T038 [US4] **(integrante 3)** Coordinar el cambio en `Service/ArmadorEstado.py`, `_sala_con_estado_actual`: el `replace(...)` que hoy copia `cerrada=viva.salidas[direccion].cerrada` debe copiar también `costo=viva.salidas[direccion].costo`, porque el esqueleto trae el costo **declarado** (puede ser `None` en un lado) y la vista debe mostrar el costo igualado (FR-101, FR-116). Al confirmarse, quitar el `skip` de T036.
- [X] T039 [US4] **(integrante 3)** Confirmar el campo `comportamiento: str | None = None` como **último** campo de `ActorDTO` en `DTO/ActorDTO.py`, con lectura `d.get("comportamiento")` y escritura en `a_diccionario`. Si el integrante 3 lo acepta y pide que lo haga el integrante 1, hacerlo así; si prefiere otro formato, actualizar [contracts/contrato-datos.md](contracts/contrato-datos.md) antes de tocar código.
- [X] T040 [US4] En `Logic/Enemigo.py`: redefinir `a_dto(self) -> ActorDTO`, que toma el `ActorDTO` de `ActorBase.a_dto()` y le agrega `comportamiento=self.ficha.comportamiento` con `dataclasses.replace` (FR-117). Depende de T039. Quitar el `skip` de T037 y correrla.
- [ ] T041 [US4] **(integrante 3)** Coordinar las pruebas de la interfaz que pide el Principio X para los escenarios H4-1 y H4-2 (FR-116, FR-117, SC-106), en los archivos de prueba de la vista que ya usa el integrante 3 (por ejemplo, `tests/test_vista_escena.py`): que muestre el costo de cada salida de la sala actual y que distinga a un cazador de un errante. Cada prueba cita su escenario y su FR. Anotar sus nombres en la fila de H4 del plan.

**Punto de control**: la vista tiene los datos de FR-116 y FR-117, y hay pruebas de interfaz acordadas para H4.

---

## Fase 7: Bench, documentación y cierre

**Propósito**: evidencia de rendimiento (NFR-101 a NFR-103, §5.1, §5.2, §5.6, §6.3) y trazabilidad.

- [ ] T042 [P] Crear `tests/test_bench_rutas.py`: cada función de `Logic/BenchRutas.py` corre sin vista con tamaños chicos (por ejemplo, 100 salas y 3 cazadores) y devuelve una lista de `ResultadoBenchDTO` con el subsistema y el caso esperados; `BenchLogica.medir()` incluye los subsistemas nuevos.
- [ ] T043 Crear `Logic/BenchRutas.py` (Lógica; mismo cronómetro y formato `ResultadoBenchDTO` que `Logic/BenchLogica.py`; reutilizar `_cuadricula` y `_cronometrar` de allí). Las cuadrículas sintéticas se arman con un helper privado nuevo, `_cuadricula_con_costos(lado: int, azar: random.Random) -> list[SalaDTO]`, en `Logic/BenchRutas.py`: toma el resultado de `_cuadricula(lado)` y le asigna a cada salida un costo entre 1 y 300 sacado de `azar` con `dataclasses.replace(salida, costo=...)`, **el mismo en los dos lados** (se sortea una vez por par de salas y se aplica a las dos caras). **No** modificar `_cuadricula` (Principio III). Cada medición crea su `azar` con `random.Random(SEMILLA)`, para que sea determinista (Principio VIII). Funciones: `medir_cola_prioridad` (montículo frente a recorrer un array, 100 / 1 000 / 10 000 salas: R1); `medir_compartida` (1 / 10 / 30 / 100 cazadores, `paso_desde_cero` por cazador frente a `RutasHaciaJugador`: R2); `medir_rango` (`rango` 200 / 600 / 5 000 × 100 / 1 000 / 10 000 salas, tiempo por decisión; la nota dice si con `rango` 200 cada multiplicación por 10 del tamaño tarda **como mucho el doble**: R3, SC-105); `medir_invalidacion` (recalcular siempre / descartar ante cualquier puerta / descarte preciso, con puertas estables e inestables, 30 cazadores, 1 000 salas, contando búsquedas reales por ciclo: R4); `medir_ciclo_cazadores` (cuadrícula de **1 000 salas** con **30 cazadores**, y además 10 y 100 como comparación, junto con errantes y rastreadores; peor ciclo frente a 20 ms, con la nota «cumple» o «no cumple»: NFR-101, SC-104); `medir_agenda_con_costos` (repite la comparación de `medir_agenda`, montículo frente a array ordenado, con los tiempos que generan costos variables entre 1 y 300 y velocidades distintas; además mide los dos límites conocidos del montículo con invalidación perezosa, con los mismos tamaños que `medir_agenda` (100 / 1 000 / 10 000 eventos): **(a) muchos eventos con el mismo tiempo**, con todos los eventos en un solo tiempo y repartidos en 10 tiempos, para que el orden lo decida el desempate por secuencia; y **(b) muchas cancelaciones**, cancelando con `cancelar()` el 50 % y el 90 % de los eventos ya programados antes de sacar el lote, para que `obtener_siguiente` tenga que descartar las entradas inválidas al llegar a la raíz. En (b) la nota dice cuántas entradas canceladas se descartaron y el tamaño del arreglo antes y después: R6, Principio VIII); y `medir_historial` (registros por intervalo con y sin la búsqueda guardada, 30 cazadores: R6). Y `medir()` que las junta.
- [ ] T044 En `Logic/BenchLogica.py`, `medir()`: devolver también `BenchRutas.medir()` (una línea; así no se toca `Service/ServicioBench.py`, que es del integrante 2). Hace pasar T042.
- [ ] T045 Correr `python -m Service.ServicioBench` y guardar la tabla. Comprobar lo que dice [quickstart.md](quickstart.md) §5: con 1 000 salas y 30 cazadores el ciclo «cumple» (< 20 ms), y con `rango` 200 cada multiplicación por 10 del tamaño de la cripta tarda como mucho el doble.
- [ ] T046 Crear `DECISIONES.md` en la **raíz del repositorio** (Principio VIII) y escribir las secciones §5.1, §5.2 y §5.6 a partir de [research.md](research.md) R1 a R6 y de los números de T045: problema, alternativas, decisión, complejidad, evidencia empírica y límites, con enlaces a la spec y al plan, y si la decisión final coincide con la de `research.md`. Incluir el antes y el después de las decisiones de P1 que cambian (Principio III): el movimiento ya no cuesta 100 fijo y `turno_enemigo` programa con el costo de la salida. Acordar el contenido con el equipo, porque los otros integrantes escriben sus secciones en el mismo archivo.
- [ ] T047 [P] En `specs/001-terreno-cazador/spec.md`, tabla «Trazabilidad del Apéndice B», cambiar «Se define en `tasks.md`» por el nombre de cada prueba: caso 1 `test_h2_1_apendiceB_caso1_…`, caso 2 `test_h2_2_…`, caso 3 `test_h2_3_…`, caso 4 `test_h2_4_…` (T018), caso 5 `test_h3_1_apendiceB_caso5_…` (T027), caso 6 `test_h1_4_…` y caso 7 `test_h1_5_…` (T008). Hacerlo en un commit de spec propio (Principio IX).
- [ ] T048 [P] Crear `tests/test_modos_sin_vista_terreno.py` para FR-118, con el mismo estilo que `tests/test_servicio_replay.py` (funciones `probar_*` y bloque `__main__`): una `FuenteDatos` de prueba en `tests/ayudas_terreno.py` (por ejemplo `FuenteCuadriculaConCazador`, sobre `FuenteCuadricula` de `tests/Utilidades.py`) que devuelve una cuadrícula de 4 × 4 armada con `cuadricula_con_costos(4, random.Random(semilla))` de T003 (costos entre 1 y 300, iguales en los dos lados), un cazador y un errante en el contenido, y sus fichas en el catálogo. Jugar una partida con `ServicioPartida(..., fuente=esa_fuente)`, leer su log y comprobar con `ServicioReplay` que `--replay`, `--replay … --hasta N` y `--verificar` reproducen los mismos estados, sin instanciar la vista.
- [ ] T049 Revisión de restricciones (Principio II), como en [quickstart.md](quickstart.md) §8: `grep -rnE "heapq|bisect|collections|import copy|networkx|\bdict\(|\bset\(|sorted\(|\.sort\(" Logic Estructuras DTO` no debe mostrar coincidencias nuevas en el código de esta feature; y `grep -rnE "^(from|import) (Data|Service)" Logic Estructuras` no debe mostrar nada nuevo.
- [X] T050 Cuando el integrante 2 entregue T002, comprobar que hay pruebas de FR-122 (en sus pruebas de Data o en `tests/test_dto_terreno.py`): costo 0, `"250"`, `true`; los dos lados de una salida con 100 y 250; cazador sin `rango`, con `rango` `null`, `-1` y `true`. Si el dato viene en el esqueleto o la ficha es de un cazador de la sala inicial, la partida no inicia; si es de cualquier otra sala, esa sala queda como contenido no disponible y entrar se rechaza (eso lo prueba T054). En todos los casos el mensaje dice qué sala y dirección o qué ficha y qué campo, y el programa no se cae.
- [ ] T051 Seguir [quickstart.md](quickstart.md) de punta a punta (pruebas, 7 casos, equivalencia, determinismo, bench, modos sin vista) y registrar en `PROMPTS_LLM.md` cada prompt usado durante la implementación (Principio XI).

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1 (preparación)**: T001 (hecho) era del integrante 2 y bloqueaba la fase 2. T002, T052 y T053 se coordinan en paralelo y no bloquean. T003 se puede hacer ya.
- **Fase 2 (base)**: depende de T001. Bloquea todas las historias.
- **Fase 3 (US1)**: depende de la fase 2.
- **Fase 4 (US2)**: depende de la fase 2. Usa `decidir_paso` de T011 y el cambio de `turno_enemigo` de T013, así que en la práctica va **después de US1**.
- **Fase 5 (US3)**: depende de US2 (cambia el cazador para que use la búsqueda compartida).
- **Fase 6 (US4)**: depende de la fase 2 y del integrante 3 (T038, T039, T041). Puede ir en paralelo con US2 y US3.
- **Fase 7 (cierre)**: depende de US3 (el bench compara la búsqueda compartida con la de desde cero). T050 depende de T002.
- **T054**: se escribe en la fase 4 con `skip`; el `skip` se quita cuando estén T052 (integrante 2) y T053 (integrante 3).

### Dentro de cada historia

- Las pruebas primero, y deben fallar.
- Estructuras y DTO antes que Lógica; Lógica antes que el cambio del motor.
- Correr todas las pruebas al final de cada fase.

### Grafo de dependencias

```text
T001 (integrante 2) ──► T004 ─► T005 ─► T006 ─► T007 ──► US1 (T008–T014) ──► US2 (T015–T026) ──► US3 (T027–T035) ──► Fase 7 (T042–T051)
T002 (integrante 2) ──────────────────────────────────────────────────────────────────────────────────────────────► T050
T052 (integrante 2) ──► T053 (integrante 3) ──► quitar el skip de T054
T003 ─────────────────► (todas las pruebas)                         └──► US4 (T036–T041) ◄── T038, T039, T041 (integrante 3)
```

## Oportunidades de paralelismo

- **Fase 1**: T003 mientras se espera T001; T002 se coordina a la vez.
- **US2**: T015, T016 y T017 (tres archivos de prueba distintos) a la vez; luego T020 y T021 a la vez.
- **US4**: T036 y T037 se pueden escribir en cualquier momento después de la fase 2.
- **Fase 7**: T042, T047 y T048 a la vez.
- Las pruebas que van en `tests/test_terreno_cazador.py` (T008, T009, T018, T019, T030, T054) **no** son paralelas entre sí: es el mismo archivo. Lo mismo con las de `tests/test_rutas_equivalencia.py` (T027 a T029) y las de `tests/test_dto_terreno.py` (T016, T036, T037).

### Ejemplo de paralelismo: historia 2

```text
Tarea: "Crear tests/test_monticulo_minimo.py"          (T015)
Tarea: "Crear tests/test_dto_terreno.py"               (T016)
Tarea: "Crear tests/test_busqueda_costo_minimo.py"     (T017)
# luego:
Tarea: "Crear Estructuras/MonticuloMinimo.py"          (T020)
Tarea: "Agregar rango a DTO/FichaEnemigoDTO.py"        (T021)
```

## Estrategia de implementación

### Primero el MVP (historia 1)

1. Fases 1 y 2: costo por salida en Lógica, igual en los dos sentidos.
2. Fase 3: el jugador y los enemigos pagan el costo de la salida.
3. **Parar y validar**: `python tests/correr_pruebas.py` y los casos 6 y 7 del Apéndice B. Ya se puede entregar sin cazadores.

### Entrega incremental

1. + Historia 2: el cazador correcto, calculando desde cero. Casos 1 a 4 del Apéndice B.
2. + Historia 3: búsqueda compartida e invalidación. Caso 5 y la equivalencia aleatoria.
3. + Historia 4: datos para la vista, cuando el integrante 3 confirme `ArmadorEstado` (`ActorDTO` ya está: T039).
4. + Fase 7: bench, `DECISIONES.md`, trazabilidad y modos sin vista.

Cada paso deja todas las pruebas en verde.

### Commits sugeridos (los hace el integrante 1)

Uno por fase o por grupo lógico, por ejemplo: `feat(001): costo por salida en Lógica`,
`feat(001): movimiento con costo de salida (H1)`, `feat(001): cazador (H2)`,
`feat(001): búsqueda compartida e invalidación (H3)`, `feat(001): comportamiento en ActorDTO (H4)`,
`bench(001): rutas del cazador`, `docs(001): DECISIONES.md`, `spec(001): pruebas en la tabla de trazabilidad`.

## Notas

- [P] = otro archivo y sin dependencias pendientes.
- Cada prueba cita su FR (Principio X).
- La validación de FR-122 es de Data, del integrante 2 (T002, T052), y se comprueba en T050. Mostrar ese error al rechazar el movimiento es de Service, del integrante 3 (T053), y se comprueba en T054.
- Si al implementar aparece una regla que la spec no define, se detiene la tarea y se corrige primero la spec en su propio commit (Principio IX), como se hizo con H-1 y con el costo declarado en un solo lado.
