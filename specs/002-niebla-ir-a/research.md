# Investigación (fase 0): Mapa conocido, memoria de puertas y antorcha

**Feature**: `002-niebla-ir-a` (parte del integrante 2: FR-201 a FR-225, NFR-201 a NFR-205, SC-201 a SC-207) ·
**Plan**: [plan.md](plan.md) · **Modelo**: [data-model.md](data-model.md) ·
**Contrato**: [contracts/contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md)

La parte de «ir a» (FR-250 a FR-264) es del integrante 3 y no se diseña aquí. Este documento solo fija lo que el
mapa conocido le ofrece (R5).

Notación: S = salas del esqueleto (`len(Mazmorra.salas)`, ids de 0 a S − 1, la posición 0 puede estar vacía);
X = salas exploradas; c = índice de una cara = `sala * 4 + dirección` (0 = N, 1 = S, 2 = E, 3 = O, como en
`DTO/Direcciones.py` y en la 003); g = grado de una sala (salidas que tiene, a lo sumo 4).

---

## R0. Revisión de las estructuras ya implementadas (Principio II)

Se revisó cada estructura y módulo que el mapa conocido podría usar, contra lo que pide la Parte II (§3.3, §5.3).

| Estructura / módulo | Limitación frente a la Parte II | Decisión |
|---|---|---|
| `Logic/HistorialRetroceso` | Guarda funciones de reversión por intervalo; registrar es O(1) y deshacer O(cambios del intervalo); tope de 5 | **Se usa tal cual** para el pergamino (R3). No se modifica |
| `Logic/Mazmorra` | Tiene el esqueleto completo y el estado **real** de las puertas; un solo `observador_puertas`, ya ocupado por `RutasHaciaJugador` (001, FR-114) | Se usa **solo para leer** (nombres, salidas, costo igualado, emparejamiento de caras con `_salida_inversa`). No se modifica. El aviso se reparte (R2) |
| `Logic/GrafoEsqueleto` (001) | «Utilizable» = abierta **ahora**; no sabe del conocimiento | No se reutiliza: el grafo de «ir a» es otro (R5). Se copia su idea de adyacencia inversa armada una vez |
| `Logic/BusquedaCostoMinimo` (001) | Ninguna: recibe el grafo como parámetro | La usa «ir a» (integrante 3) sobre el grafo del mapa (R5) |
| `Logic/RutasHaciaJugador` (001) | Escucha el aviso de puertas | No se toca; convive con el mapa por medio del repartidor (R2) |
| `Logic/PartidaGuardada` | Copia todo el estado a DTO a mano, sin `copy`; no conoce el mapa | Se **extiende** con dos líneas (R4) |
| `Data/GuardadoBinario` | Versión 1; un bloque global, bloques de sala e índice directo | Versión 2 con un bloque propio del mapa, junto con el de la línea de T003 de la 004 (R4) |
| `Estructuras/Cola`, `ListaDoble`, `BufferCircular`, `MonticuloMinimo`, `BusquedaBinaria`, `Ordenador` | Ninguna ofrece acceso directo por id; los ids ya son enteros seguidos | **No se usan**: el acceso directo por posición en un arreglo ya es O(1) y no hace falta ordenar (R1, R5) |

No se agrega nada a `Estructuras/`.

---

## R1. Dónde vive el mapa conocido y cómo se representa (decisión 1)

- **Problema**: FR-201 (tres estados por sala), FR-208 (estado recordado **por cara**, FR-207), FR-212 («sin
  observar»), FR-218 (separado del esqueleto) y NFR-201 / §5.3 (consultas de sala y de cara con costo que no depende
  del tamaño), sin `dict` ni `set` (Principio II).

- **Decisión**: una clase nueva de Logic, `Logic/MapaConocido.py`, que es **estado de la partida** y vive en el
  motor (`motor.mapa`, igual que `motor.rastro`). Guarda dos arreglos de enteros:

  | Arreglo | Largo | Índice | Valores |
  |---|---|---|---|
  | `estado` | S | id de sala | `DESCONOCIDA = 0`, `AVISTADA = 1`, `EXPLORADA = 2` |
  | `caras` | 4·S | c = `sala * 4 + dirección` | `SIN_OBSERVAR = 0`, `ABIERTA = 1`, `CERRADA = 2` |

  Los dos arreglos empiezan en 0 (todo desconocido y sin observar). Las constantes viven en
  `DTO/MapaConocidoDTO.py` para que Data y la vista lean los mismos valores sin importar Logic.

  Lo que el jugador sabe de una sala **explorada** (nombre, salidas, costo igualado) no se copia: se lee del esqueleto
  de la `Mazmorra`, que no cambia durante la partida, **solo cuando `estado[sala] == EXPLORADA`**. Del esqueleto
  nunca se lee el estado real de una puerta para mostrarlo: eso sale siempre de `caras` (FR-208). Así el mapa queda
  separado del esqueleto (FR-218): el esqueleto es infraestructura y el mapa es lo único que decide qué se muestra.

- **Consultas** (NFR-201): `estado_sala(id)` y `estado_cara(sala, dirección)` son un acceso por posición: **O(1)**,
  sin depender de S ni de X. Memoria: 5 casillas por sala, **O(S)**.

- **Cómo se mantiene «avistada» (FR-204)**: una sala está avistada si no está explorada y es destino de una salida de
  una sala explorada. Cuando una sala u pasa a explorada, cada destino v de sus salidas que esté `DESCONOCIDA` pasa a
  `AVISTADA` (O(g)). No hacen falta contadores de «cuántas exploradas apuntan a v»: entre dos pergaminos el conjunto
  de exploradas solo crece, así que la sala explorada que dejó avistada a v sigue explorada y v sigue avistada hasta
  que se explora. Una sala que solo tiene una salida sin vuelta **hacia** una explorada nunca se toca, porque solo se
  recorren las salidas **de** la sala explorada (FR-204, escenario H2-4). Una sala vecina de sí misma o vecina por
  varias salidas se marca una sola vez: la segunda vez ya no está `DESCONOCIDA` (casos borde).

- **Por qué una explorada no vuelve atrás (FR-203)**: el código del mapa solo tiene dos escrituras de `estado`:
  `DESCONOCIDA → AVISTADA` y `(DESCONOCIDA | AVISTADA) → EXPLORADA`. No existe ninguna operación que baje un estado.
  La única forma de volver atrás es la función de reversión que esas mismas escrituras dejan en el historial (R3), y
  esa solo corre al leer un pergamino. Cargar una partida reemplaza el mapa entero por el guardado (FR-221), no lo
  baja casilla por casilla (hallazgo H-8).

- **Alternativas descartadas**:

  | Alternativa | Complejidad de la consulta | Por qué se descarta |
  |---|---|---|
  | `set` / `dict` de salas exploradas o de caras | O(1) promedio | Prohibido (Principio II, §6.2) |
  | Lista de ids explorados recorrida en cada consulta | O(X) | Viola NFR-201 y SC-203; se **mide** en el bench (B3) para mostrarlo |
  | Atributos nuevos en `SalaViva` / `SalidaViva` (`explorada`, `cara_recordada`) | O(1) | Mezcla esqueleto y conocimiento (FR-218), modifica código P1 de la `Mazmorra` (integrante 1) y obliga a recorrer la `Mazmorra` para copiar el mapa en cada punto de control |
  | Un grafo propio con copia de las salas conocidas y sus salidas | O(1) con un índice aparte | Duplica el esqueleto (memoria y copia en cada punto de control más grandes) sin ganar nada: lo que se sabe de una explorada es exactamente lo que trae el esqueleto |
  | `bytearray` en lugar de `list[int]` | O(1) | Menos memoria, pero no está en la lista de bibliotecas y tipos acordados; a las escalas del proyecto (≤ 10 000 salas) la lista basta |

---

## R2. Cuándo y cómo se actualiza (decisión 2)

- **Problema**: FR-202, FR-203, FR-207 a FR-216, NFR-202 (costo proporcional a lo revelado), NFR-205 (ciclo < 20 ms)
  y FR-218 (precarga, esqueleto y cazador no tocan el mapa).

- **Decisión**: el mapa tiene **tres puntos de entrada**, y nada más lo escribe:

  | Punto | Quién lo llama | Qué hace | Requisitos |
  |---|---|---|---|
  | `iniciar(sala_inicial)` | `Motor.iniciar()` | Explora la sala inicial (y avista sus destinos) y observa sus puertas | FR-202, FR-207 |
  | `entrar(sala, antorcha)` | `Motor.mover_jugador()`, justo después de `jugador.Sala_Actual = destino` | Explora la sala; si `antorcha`, explora además cada vecina (destino de **cualquier** salida, abierta o cerrada) y avista los destinos de las salidas de cada vecina, sin ir más allá; observa las puertas de la sala | FR-203, FR-207, FR-209, FR-210, FR-212, FR-213, FR-214 |
  | `puerta_cambio(a, b)` | El aviso de puertas de la `Mazmorra` (001 FR-114) | Vuelve a observar las puertas de la sala donde está el jugador | FR-207, FR-209 |

  Más `restaurar(dto)` al cargar (R4), que no es una regla del juego sino reconstrucción del estado.

- **Antorcha**: el motor le pasa a `entrar` un booleano, `self.efectos.tiene(self.jugador, "antorcha")`, leído en el
  instante de la entrada. El mapa no conoce los efectos. Esto resuelve el escenario H3-8 sin código especial: si el
  evento de fin de la antorcha se programó antes que la acción del jugador en el mismo instante, la cola lo atiende
  primero (001 FR-108), `Antorcha.activar` quita el efecto y `tiene` da `False`; si se programó después, sigue en la
  cola y `tiene` da `True`. Encender la antorcha (`Motor.usar`) no llama al mapa (FR-215). La exploración con antorcha
  no lee ni carga contenido, no toca enemigos ni trampas (FR-211) y no programa eventos ni consume tiempo: el costo
  de la acción lo sigue fijando `terminar_accion_jugador(salida.costo)`. Tampoco necesita el contenido de las vecinas
  («pendiente»), porque solo usa el esqueleto.

- **Observar las puertas de la sala x** (FR-207): para cada dirección d con salida s de x hacia una sala que existe,
  se escribe en `caras[x*4 + d]` el estado real de s; si la puerta tiene vuelta, también el de su otra cara. La otra
  cara se busca con la **misma regla de emparejamiento de la `Mazmorra`** (`_salida_inversa(x, s.destino)`: la primera
  salida del destino que vuelve a x) y su dirección por identidad entre las 4 salidas del destino, como ya hace
  `PartidaGuardada._cargar_evento`. Así el mapa empareja las caras igual que `abrir_puerta` y `CierrePuerta`, sin
  duplicar la regla. Una salida sin vuelta solo tiene cara en la sala de la que sale, así que solo se observa desde
  ella; la salida sin vuelta de otra sala **hacia** x no es una salida de x y no se observa (FR-207, escenario H2-4).
  Toda puerta con cara en x es una salida de x, así que recorrer las 4 salidas de x basta. Costo: O(g · 4) = O(1).

- **Cambios de puerta mientras el jugador sigue en la sala**: se **reutiliza el aviso de la 001** (`abrir_puerta` y
  `CierrePuerta.activar` llaman a `observador_puertas.puerta_cambio(a, b)` después de cambiar las caras). El aviso no
  identifica la puerta cuando no tiene vuelta (pasa su destino dos veces, sin el origen), así que el mapa no intenta
  adivinarla: **vuelve a observar todas las puertas de la sala del jugador**, O(1). Invariante que lo hace correcto:
  *mientras el jugador está en x, el estado recordado de cada cara de cada puerta con cara en x es igual al real*. Se
  establece al llegar (observación) y se mantiene porque todo cambio de puerta pasa por uno de esos dos puntos y avisa.
  Si el cambio no tocó una puerta de x, la nueva observación escribe los mismos valores y no registra nada (R3).

  La `Mazmorra` tiene **un solo** `observador_puertas`, que hoy es `RutasHaciaJugador`. Para que escuchen los dos sin
  modificar la `Mazmorra`, se agrega una clase nueva y mínima de Logic, `RepartidorAvisosPuertas`, que reenvía cada
  `puerta_cambio(a, b)` a una lista de observadores en orden fijo (primero las rutas del cazador, después el mapa). El
  motor la asigna en lugar de `self.rutas`. Es una **modificación de `Logic/motorJuego.py`** (integrante 1): ver la
  tabla de cambios del plan. El orden no cambia ningún resultado, porque el mapa no cambia puertas y las rutas no leen
  el mapa.

- **FR-218, cómo se garantiza**: (1) solo esos tres puntos escriben el mapa, y los llaman `iniciar` y `mover_jugador`
  (el jugador) y el aviso de puertas, que solo re-observa la sala **del jugador**; (2) la precarga y el esqueleto son
  de Data y Service (`GestorContenido`, `GestorEsqueleto`) y no tienen referencia al mapa; `Mazmorra.cargar_contenido`
  y `cargar_esqueleto` no lo llaman; (3) el cazador mueve enemigos con `Mazmorra.mover_enemigo` y calcula sobre
  `GrafoEsqueleto`, que no conocen el mapa; (4) el reporte de resolubilidad se calcula antes de que exista el motor.
  Pruebas: H1-5 (A3), H1-7 (A41) y H5-7 (A40).

- **Costo** (NFR-202): `iniciar` y `entrar` sin antorcha: O(g) para explorar y avistar + O(1) para observar. Con
  antorcha: O(1 + Σ g(v)) sobre las vecinas v que **pasan** a exploradas (una vecina ya explorada se salta sin recorrer
  sus salidas), es decir, a lo sumo 1 + 4 salas y 4 + 16 salidas: proporcional a lo revelado, nunca a S ni a X.
  `puerta_cambio`: O(1) por aviso. Con 30 cazadores el ciclo suma un `puerta_cambio` por cada puerta que cambia y una
  `entrar` por movimiento del jugador: se mide en B8 contra el límite de 20 ms (NFR-205, SC-206).

- **Alternativas descartadas**:

  | Alternativa | Complejidad | Por qué se descarta |
  |---|---|---|
  | Actualizar el mapa en Service después de cada `mover_jugador` que devuelve `"ok"` | Igual | Las reglas del mapa quedarían en Service (Principio I); la re-simulación de la 004 (`DespachoAcciones`) y el replay tendrían que repetirlo y podrían divergir; los cierres automáticos ocurren dentro de `avanzar_hasta_jugador`, fuera del alcance de Service |
  | Re-observar la sala del jugador al final de **cada evento** en `avanzar_hasta_jugador` | O(1) por evento, en todos los eventos | Modifica el bucle de eventos de P1 y cuesta en cada evento aunque no cambie ninguna puerta |
  | Recalcular «avistadas» recorriendo todo el mapa conocido después de cada entrada | O(X · g) por entrada | Viola NFR-202 y SC-204; se **mide** en B5 |
  | Segundo atributo `observador_mapa` en la `Mazmorra` con su propio aviso | Igual | Modifica la `Mazmorra` (dos puntos de P1 más) para lo mismo que hace un repartidor sin tocarla |
  | Que el mapa reenvíe el aviso a las rutas (cadena) | Igual | Acopla el mapa al cazador; el repartidor deja a cada uno con una sola responsabilidad |

---

## R3. Pergamino: registro e inversión de los cambios del mapa (decisión 3)

- **Problema**: FR-222 (volver exactamente al mapa anterior a la acción revertida, incluidas las salas de la
  antorcha y las puertas observadas) y NFR-203 (registrar e invertir proporcional a lo que cambió, sin copiar el
  mapa).

- **Decisión**: todas las escrituras pasan por dos métodos privados, `_poner_estado(sala, valor)` y
  `_poner_cara(c, valor)`. Si el valor nuevo es **igual** al actual, no hacen nada (ni escriben ni registran). Si es
  distinto, registran en el historial que ya existe una función de reversión **de esa casilla**, con el índice y el
  valor anterior ligados (`historial.registrar_cambio(...)`, O(1)), y después escriben. `registrar_atributo` no sirve
  porque restaura atributos, no casillas de un arreglo. Si el historial es `None` (bench sin motor), no se registra.

  El registro cae en el intervalo abierto del motor: la entrada y las observaciones ocurren durante la acción del
  jugador, y los avisos de puerta durante los eventos que le siguen, antes de que `_cerrar_intervalo` lo cierre en la
  siguiente decisión. Deshacer recorre el intervalo de atrás hacia adelante, así que cada casilla vuelve al valor que
  tenía antes de la acción, aunque haya cambiado varias veces en el mismo intervalo, y en el orden correcto respecto
  de las puertas reales (`registrar_atributo(salida, "cerrada", …)` de la `Mazmorra`). Lo que el motor hace al
  preparar la partida (`iniciar`) se descarta con `descartar_intervalo_abierto`, como el resto de la preparación: el
  conocimiento inicial no se deshace.

- **Costo**: registrar O(1) por casilla cambiada; deshacer O(casillas cambiadas en ese intervalo); una entrada con
  antorcha cambia a lo sumo 5 estados de exploración, 16 de avistamiento y 8 caras. Memoria del historial: O(cambios
  de los últimos 5 intervalos). **No depende de S ni de X** (SC-207, medido en B6). Re-observar sin cambios no deja
  nada en el historial.

- **Alternativas descartadas**:

  | Alternativa | Complejidad | Por qué se descarta |
  |---|---|---|
  | Copiar el mapa entero al empezar cada acción y restaurarlo | O(S) por acción y O(S) de memoria por intervalo | Viola NFR-203 y §5.3 («barato registrar e invertir»); se **mide** en B7 |
  | Una sola función de reversión por entrada con la lista de casillas cambiadas | O(cambios) | Igual complejidad, pero una función más compleja de explicar; con cambios repetidos en el mismo intervalo hay que guardar el **primer** valor anterior, que el registro por casilla ya resuelve por el orden inverso |
  | Inversas también para la línea de tiempo | — | No hace falta: la 004 reconstruye hacia adelante (FR-223, Sesión 2026-11-13); las inversas son solo para el pergamino |

---

## R4. Guardado y línea de tiempo (decisión 4)

- **Problema**: FR-221 (guardar y cargar idéntico), FR-223 (el resumen de `historia` muestra el mapa de ese instante),
  FR-224, NFR-203 (copia proporcional al tamaño del mapa, una vez por punto de control), T004 de la 004 (el mapa es un
  campo de `PartidaGuardadaDTO` que actualiza el motor y se copia con `PartidaGuardada.guardar`, sin `copy`), T002 y
  T003 de la 004 (campo `linea` y formato versión 2).

- **Decisión (DTO)**: un DTO nuevo de solo datos, `MapaConocidoGuardadoDTO(estado_salas: list[int], caras: list[int])`,
  en `DTO/MapaConocidoDTO.py`, con `a_diccionario` / `desde_diccionario` (comparación JSON contra binario, §4.10).
  `PartidaGuardadaDTO` gana el campo **`mapa: MapaConocidoGuardadoDTO | None = None`**, al final y con valor por
  defecto.

- **Orden respecto de `linea` (T002)**: **`mapa` va antes que `linea`**: `…, ruta_log, acciones_en_log, mapa=None,
  linea=None`. Razones: (1) el contrato de la 004 dice que `linea` es el **último** campo, y así sigue siéndolo;
  (2) `mapa` es estado de la partida, como `rastro`, mientras que `linea` es la historia que contiene copias de ese
  estado (y en cada punto de control va en `None`); (3) todos los que construyen el DTO (`PartidaGuardada.guardar`,
  `GuardadoBinario._leer_partida`, `desde_diccionario`) usan nombres de campo, así que insertar `mapa` antes de
  `linea` no rompe nada aunque T002 se haga primero.

- **Imports**: `DTO/MapaConocidoDTO.py` no importa nada del proyecto; `PartidaGuardadaDTO` lo importa;
  `LineaTiempoDTO` importa `PartidaGuardadaDTO`. **El mapa no forma ningún ciclo.** Aviso para T002: si
  `PartidaGuardadaDTO` importara `LineaTiempoDTO` arriba del módulo para anotar `linea`, sí se formaría un ciclo
  (`LineaTiempoDTO` → `PartidaGuardadaDTO` → `LineaTiempoDTO`). Se evita anotando `linea` con texto
  (`"LineaTiempoGuardadaDTO | None"`, que `dataclasses` no evalúa) e importando `LineaTiempoGuardadaDTO` **dentro** de
  `desde_diccionario`, como ya hace `BenchLogica.medir` con `BenchRutas`.

- **Decisión (Logic)**: `MapaConocido.a_guardado()` devuelve un `MapaConocidoGuardadoDTO` con **copias** de los dos
  arreglos hechas con `list(...)` (O(S)), y `MapaConocido.restaurar(dto)` vuelve a copiar los arreglos del DTO
  (O(S)) después de comprobar que los largos corresponden a la `Mazmorra` (si no, `ValueError` con el motivo). Las dos
  copias son necesarias: la línea de tiempo arma **varios** motores aparte desde el mismo punto de control, y si
  `restaurar` no copiara, la re-simulación escribiría dentro del punto de control.
  `PartidaGuardada.guardar` agrega `mapa=motor.mapa.a_guardado()` y `PartidaGuardada.cargar` llama a
  `motor.mapa.restaurar(partida.mapa)` antes de vaciar el historial. Si `partida.mapa` es `None`, `cargar` lanza
  `ValueError` («la partida guardada no trae el mapa conocido»): nunca se inventa un mapa (FR-221). Los archivos de la
  primera parte no llegan aquí: `GuardadoBinario` los rechaza por versión (FR-421 de la 004).

- **Línea de tiempo**: como los puntos de control son `PartidaGuardada.guardar` y la re-simulación usa
  `PartidaGuardada.cargar` y el mismo motor, el mapa entra en cada punto de control (una copia O(S) por punto, NFR-203)
  y la re-simulación lo reproduce con las mismas reglas (FR-223, FR-224). El punto nuevo que la 004 toma después de un
  pergamino copia el mapa ya revertido, así que `historia` no muestra conocimiento de acciones revertidas. **La 004 no
  necesita nada más del mapa** salvo copiar la vista al resumen: `ResumenHistoriaDTO.mapa_conocido =
  motor.mapa.a_dto()` sobre el motor aparte (T023 de la 004, integrante 3).

- **Decisión (binario, versión 2)**: el mapa va en un **bloque propio**, igual que la línea de T003:

  ```text
  CABECERA (58 bytes)   4s "CRPT" · H versión = 2 · Q,I global · Q,I índice (offset, entradas) · I id mínimo
                        · Q,I mapa (offset, largo) · Q,I línea (offset, largo)
  BLOQUE GLOBAL         PartidaGuardadaDTO sin mapa ni línea (mismo formato que en la versión 1)
  BLOQUE DEL MAPA       I cantidad de salas S · S bytes de estado · S bytes de caras (2 bits por cara: N, S, E, O)
  BLOQUE DE LA LÍNEA    (T003 de la 004) cada punto de control lleva, después de su bloque global, el bloque de su mapa
  BLOQUES DE SALAS      sin cambios
  ÍNDICE                sin cambios (sigue al final: la comprobación de tamaño de hoy no cambia)
  ```

  - Un byte por sala para el estado y un byte por sala para sus 4 caras (2 bits cada una), como el byte de las 4
    puertas del bloque de sala: 2 bytes por sala. Al leer, Data valida solo formato: estado ∈ {0, 1, 2}, cada par de
    bits ∈ {0, 1, 2}, largo exacto; si no, `ErrorGuardado`. Largo 0 = `mapa` es `None`.
  - Un **mismo** `_codificar_mapa` / `_leer_mapa` sirve para el bloque del mapa y para el mapa de cada punto de control
    dentro del bloque de la línea.
  - `cargar(ruta)` lee el bloque global, el del mapa y el de la línea. `cargar_sala(ruta, id)` sigue leyendo solo la
    cabecera, una entrada del índice y el bloque de esa sala: **no lee el mapa ni la línea**.
  - **Versión 1 rechazada**: `_leer_cabecera` ya compara la versión antes de interpretar el resto; con
    `VERSION_FORMATO = 2`, un archivo de la primera parte da `ErrorGuardado` con la versión leída y la esperada, sin
    cargar nada.
  - **Coordinación con T003**: como T003 también es del integrante 2, la versión 2 se define **una sola vez** con los
    dos bloques. Si T003 se implementa antes que el mapa, su cabecera ya reserva el offset y el largo del mapa (con
    largo 0). Así el formato no pasa a una versión 3 cuando llegue el mapa.

- **Costo**: copiar para un punto de control o para guardar: O(S) tiempo y memoria (5 casillas por sala en memoria,
  2 bytes por sala en el archivo), una vez por punto de control (B9). Cargar: O(S).

- **Alternativas descartadas**:

  | Alternativa | Complejidad | Por qué se descarta |
  |---|---|---|
  | Guardar el mapa dentro del bloque global | O(S) | Cambia el formato del bloque global, que la línea reutiliza en cada punto de control; un bloque propio deja el bloque global igual que en la versión 1 |
  | Guardar solo las salas exploradas y las caras observadas (lista de pares) | O(X + caras observadas) | Menos bytes con mapas chicos, pero más código de lectura y validación; con el mapa completo (lo que mide la 004 y lo que pide NFR-250) ocupa más que 2 bytes por sala |
  | Copia por casilla dentro del bloque de cada sala | O(S) | Mezcla conocimiento con estado real de la sala (FR-218) y obliga a `cargar_sala` a leer conocimiento |
  | Reconstruir el mapa al cargar re-simulando las acciones | O(acciones) | Depende de la línea y del catálogo; FR-221 pide el mapa idéntico, no re-calculado |

---

## R5. Lo que el mapa conocido ofrece al integrante 3 (decisión 5)

El detalle (firmas, reglas, ejemplos y lo que no se ofrece) está en
[contracts/contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md). Resumen de las decisiones:

- **(a) Grafo para «ir a»**: clase nueva `Logic/GrafoMapaConocido.py` con la interfaz **exacta** de
  `specs/001-terreno-cazador/contracts/busqueda-rutas.md`: `cantidad_salas()`, `salidas(u)` y `entradas(x)`, con
  pares `(sala, costo)`. «Utilizable» (FR-225, FR-252): salida u→v con `u` y `v` exploradas y la cara de u
  (`caras[u*4 + d]`) recordada `ABIERTA`; «sin observar» y «cerrada» no cuentan; el costo es `SalidaViva.costo`, el
  igualado por Logic (001 FR-101); los ids son los reales del esqueleto (`cantidad_salas() = len(Mazmorra.salas)`), así
  que el desempate por menor id de `BusquedaCostoMinimo` da lo mismo que FR-253. Lee el mapa **en vivo** en cada
  llamada (regla 2 del contrato de la 001). `salidas(u)`: O(4). `entradas(x)`: O(grado de entrada de x), con una
  adyacencia inversa del esqueleto armada una vez en O(S + E), como `GrafoEsqueleto`; solo devuelve orígenes
  explorados, de los que el jugador conoce todas sus salidas (FR-205), así que no filtra nada del esqueleto.
  **Aviso**: el mapa tiene un atributo `observador_rutas = None`. Si alguien lo asigna, cada vez que cambia una salida
  utilizable le avisa `puerta_cambio(a, b)` con los **destinos** de lo que cambió, según la regla de la 001 (cuando una
  cara observada pasa de abierta a no abierta o al revés entre exploradas: los destinos de esa cara; cuando una sala x
  pasa a explorada: `(x, w)` por cada salida x→w utilizable y `(x, x)` por las que entran a x). Recomendación: como el
  viaje recalcula **antes de cada paso** (FR-255) y el conocimiento solo cambia entre pasos, empezar una búsqueda
  nueva por paso (`paso_desde_cero` o `reiniciar`) no necesita el aviso y cumple NFR-250 con holgura en la cripta de
  referencia; el aviso queda disponible si el integrante 3 decide reutilizar la búsqueda entre pasos.
  *Alternativa descartada*: una segunda búsqueda propia de «ir a» (§5.3 pide justificarlo): la 001 ya decidió
  compartir la búsqueda (R5 de la 001) y el grafo como parámetro lo permite sin duplicar el desempate.
- **(b) DTO de solo lectura para la vista, el comando y el resumen**: `MapaConocido.a_dto() -> MapaConocidoDTO`, armado
  en Logic (que es quien sabe qué conoce el jugador, FR-217) y solo copiado por Service. Lista las salas exploradas
  en orden de id, cada una con id, nombre y sus 4 salidas; cada salida con costo igualado, estado recordado de su cara
  (`ABIERTA`, `CERRADA` o `SIN_OBSERVAR`) y `destino` = id si el destino está explorado o `None` si está avistado («sala
  sin explorar detrás de esta salida», una entrada por salida, sin identificador). Nunca aparece una sala desconocida
  (toda salida de una explorada lleva a una explorada o a una avistada). Costo O(S + 4·S) por llamada: recorre los ids
  en orden, sin ordenar. *Alternativa descartada*: mantener una lista de exploradas para armar el DTO en O(X): agrega
  estado que hay que revertir y guardar, y el orden de exploración cambiaría al cargar; se mide en B10 para respaldar
  la decisión.
- **(c) Búsqueda por nombre (FR-251)**: `MapaConocido.buscar_exploradas(nombre) -> list[int]` devuelve los ids de las
  salas **exploradas** cuyo nombre coincide (regla de comparación en el hallazgo H-3). 0 resultados → la orden se
  rechaza con el mensaje único de FR-251; 2 o más → ambigua; 1 → ese es el destino. Solo mira exploradas, así que no
  revela si existe una avistada o desconocida con ese nombre. Costo O(S) por orden (una vez por orden, no por paso).
  *Alternativa descartada*: índice ordenado por nombre con búsqueda binaria (O(log S)): hay que mantenerlo con cada
  exploración y cada pergamino; la búsqueda ocurre una vez por orden.
- **(d) Lo que no ofrece**: el reporte de resolubilidad de la 003 (FR-217), el estado real de las puertas, el
  contenido de ninguna sala, la identidad de las avistadas, cualquier dato de una desconocida y las inversas para la
  línea de tiempo.

---

## R6. Determinismo (decisión 6)

- **Decisión**: el mapa es una función de la secuencia de llamadas `iniciar`, `entrar` y `puerta_cambio`, que hace el
  motor en el orden determinista de la cola (001 FR-108). No usa azar, ni reloj real, ni iteración sobre `dict` o
  `set`; recorre siempre las direcciones en el orden N, S, E, O. `--replay` y `--replay … --hasta` ejecutan las mismas
  acciones por el mismo motor, así que llegan al mismo mapa (FR-224). La 004 lo reproduce desde los puntos de control
  con las mismas reglas.
- **Comentarios «# ir a»**: `BitacoraReplayIO.leer` los ignora (T071 de la 004, hecho) y `continuar_desde` no los
  copia; no son acciones, así que no llegan al motor ni al mapa. Prueba A10 con un log que trae comentarios.
- **Prueba**: dos ejecuciones de la misma partida (y su `--replay`) comparan los dos arreglos casilla por casilla en
  cada acción (SC-205).

---

## R7. `--bench` (decisión 7)

- **Dónde**: `Logic/BenchMapaConocido.py` (nuevo, integrante 2), en Logic porque mide Logic. Reutiliza sin
  modificarlos `_cronometrar`, `_mejor_y_mediana` y `SEMILLA` de `Logic/BenchLogica.py`, y `_cuadricula_con_costos`,
  `_motor_con_cazadores`, `_centro` y `_peor` de `Logic/BenchRutas.py` (integrante 1), como hace la 003. Sin import
  circular: `BenchMapaConocido` importa esos dos módulos y ninguno de ellos lo importa. Se engancha en
  `Service/ServicioBench.py` (integrante 2), agregando `BenchMapaConocido.medir` a la lista por defecto después de
  `BenchLogica.medir` (y de `BenchResolubilidad.medir` si ya está). `Logic/BenchLogica.py` no se modifica.
- **Criptas**: cuadrículas con costos de `random.Random(SEMILLA)` entre 1 y 300, de lado 10, 32 y 100 (100, 1 024 y
  10 000 salas): la mayor es 100 veces la menor (SC-203, SC-204, SC-207 piden al menos 10). Ids y estados
  preparados por semilla, así que cada corrida mide lo mismo.

| # | Qué mide | Tamaños | Qué se compara / criterio | Requisito |
|---|---|---|---|---|
| B1 | Consulta de estado de sala (100 000 consultas sobre ids sacados por semilla, mapa con un tercio de salas en cada estado) | 100 / 1 024 / 10 000 | Tiempo medio por consulta; 10 000 contra 100: menos de ×2 | NFR-201, SC-203 |
| B2 | Consulta de cara recordada (igual que B1, sobre caras) | ídem | ídem | NFR-201, SC-203 |
| B3 | **Alternativa descartada de R1**: lista de ids explorados recorrida | ídem | Crece con X; la nota dice cuántas veces más que B1 | Principio VIII |
| B4 | Entrada con antorcha que revela la misma cantidad de salas (la sala y sus 4 vecinas sin explorar), con el resto del mapa ya explorado | mapa conocido de ~100, ~1 000 y ~10 000 salas | Tiempo por entrada; el mayor contra el menor: menos de ×2. El estado se repone fuera del cronómetro con el pergamino (`preparar`) | NFR-202, SC-204 |
| B5 | **Alternativa descartada de R2**: después de cada entrada, recalcular «avistadas» recorriendo todo el mapa conocido | ídem | Crece con X | Principio VIII |
| B6 | Registrar e invertir con el pergamino los cambios de una entrada con antorcha (misma cantidad de casillas): entrar, cerrar el intervalo y deshacer | ídem | El mayor contra el menor: menos de ×2 | NFR-203, SC-207 |
| B7 | **Alternativa descartada de R3**: copiar el mapa entero antes de la acción y restaurarlo | ídem | Crece con S | Principio VIII |
| B8 | Ciclo de eventos con la antorcha encendida: 1 024 salas (32 × 32), 30 cazadores y 20 errantes y rastreadores (`_motor_con_cazadores` de la 001), el jugador se mueve en cada ciclo; variante con una puerta de la sala del jugador que cambia en cada ciclo (camino del aviso). Antes, sin cronometrar, se comprueba que el mapa coincide con el de un motor de control | 1 024 | Peor ciclo frente a 20 ms; la nota dice si cumple | NFR-205, SC-206 |
| B9 | Copia del mapa para un punto de control: `a_guardado` + `restaurar` | 100 / 1 024 / 10 000 | Crece con S (lineal), una vez por punto | NFR-203 (última oración) |
| B10 | Armar `MapaConocidoDTO` y `buscar_exploradas` con el mapa completo | ídem | O(S); respalda R5 (b) y (c) | Principio VIII |

- **No se mide aquí**: el cálculo de un paso de «ir a» (NFR-250, NFR-251, SC-252): es del integrante 3, que usa
  `GrafoMapaConocido`; su bench puede reutilizar las cuadrículas de B1 con el mapa completo.
- **DECISIONES.md**: la sección del integrante 2 gana «Mapa conocido» con problema, alternativas, decisión,
  complejidad, los números de B1 a B10 y si la decisión final coincide con este plan (Principio VIII, NFR-204).

---

## R8. Pruebas (decisión 8)

- Un archivo por grupo, `unittest`, corridas por `tests/correr_pruebas.py`. Cada prueba cita escenario y FR en el nombre
  (por ejemplo `test_h3_1_apendiceB_caso4_fr210_fr211_antorcha_no_despierta`).
- Ayudante nuevo `tests/ayudas_mapa.py`: criptas pequeñas con la notación de la spec (A, B, C…, salidas con y sin
  vuelta, caras con estados distintos, costo en una sola cara), sobre `salida`, `salida_sin_vuelta`,
  `mazmorra_con_costos` y `motor_con` de `tests/ayudas_terreno.py`; y `estados(motor)`, que devuelve los dos arreglos
  para comparar.

| Archivo (nuevo) | Cubre |
|---|---|
| `tests/test_mapa_conocido_estados.py` | Historia 1: H1-1 (A1), H1-2 y H1-6 (A2), H1-3 (A13), H1-4 (A14), H1-5 (A3), H1-7 (A41); casos borde (vecina de sí misma, varias salidas, sala de origen) y que ninguna operación baja un estado (FR-203) |
| `tests/test_mapa_conocido_puertas.py` | Historia 2: H2-1 (**caso 2a**), H2-2 (A4), H2-3 (A15), H2-4 (A16), H2-5 (A38), H2-6 (A42); invariante «en la sala del jugador, recordado = real» tras abrir y cerrar |
| `tests/test_mapa_conocido_antorcha.py` | Historia 3: H3-1 (**caso 4**), H3-2 (A5), H3-3 (A6), H3-4 (A17), H3-5 (A18), H3-6 (A19), H3-7 (A20), H3-8 (A43, las dos variantes de orden) |
| `tests/test_mapa_conocido_partida.py` | Historia 4: H4-1 (**caso 5**), H4-2 (A8), H4-3 (A7: `PartidaGuardada` y `GuardadoBinario` versión 2), H4-4 (A9: con `ArmadorResumen` de la 004; `skip` con motivo hasta que exista T023), H4-5 (A10: `--replay` y `--replay … --hasta` con un log con «# ir a»); pergaminos seguidos; pergamino sin cambios del mapa |
| `tests/test_mapa_conocido_vista.py` | Historia 5 en Logic: H5-1 (A11), H5-2 (A21), H5-3 (A22), H5-4 (A12: `a_dto` no cambia reloj, historial ni estado), H5-5 (A23), H5-6 (A39), H5-7 (A40); SC-202: partida de 200 acciones con y sin antorcha que revisa en cada acción el `MapaConocidoDTO`, el `ResumenHistoriaDTO` (si existe) y el `EstadoJuegoDTO` (ver hallazgo H-2) |
| `tests/test_grafo_mapa_conocido.py` | Contrato (a), (c) y (d): interfaz de la 001, «utilizable», igualdad con `paso_desde_cero` sobre un grafo filtrado a mano, aviso `puerta_cambio`, `buscar_exploradas` (0, 1 y 2 coincidencias) |
| `tests/test_guardado_mapa.py` | `MapaConocidoGuardadoDTO` y `PartidaGuardadaDTO` ida y vuelta por diccionario; binario versión 2: ida y vuelta con mapa, mapa `None` (largo 0), `cargar_sala` sin leer el mapa, versión 1 rechazada, bytes inválidos → `ErrorGuardado`; `restaurar` con largos distintos → `ValueError` |
| `tests/test_bench_mapa.py` | B1 a B10 con tamaños chicos, sin vista; las alternativas dan el mismo mapa que la decisión |

La prueba de la vista en pantalla y del comando (FR-219, FR-220 con `partida.log`) es del integrante 3 (ver
contrato).

---

## Hallazgos

Ninguno bloquea el plan. No se cambió la spec.

- **H-1 (coordinación, integrante 1)**: la `Mazmorra` tiene un solo `observador_puertas`, ocupado por las rutas del
  cazador. Hace falta que el motor asigne el repartidor (R2). Además, `Logic/BenchRutas.py` reasigna
  `observador_puertas` en dos mediciones (líneas 452 y 675): en esas dos el mapa deja de escuchar, lo que no afecta lo
  que miden. El data-model de la 001 dice que el motor asigna `observador_puertas = self.rutas`; queda desactualizado
  y el integrante 1 decide si lo anota.
- **H-2 (SC-202 y FR-204, integrante 3)**: hoy `EstadoJuegoDTO.sala` es el `SalaDTO` del esqueleto con las puertas
  actuales, y sus `SalidaDTO.sala_destino` traen el **id real** de los destinos, también de los avistados. La vista los
  usa (`View/EscenaJuego.py`, líneas 59, 112 y 318). Con eso la interfaz recibe la identidad de salas avistadas y podría
  saber que dos salidas llevan a la misma (FR-204, H5-5), y la prueba automática de SC-202 fallaría. Lo decide el
  integrante 3 en `ArmadorEstado` (por ejemplo, `sala_destino = None` para destinos no explorados y un dato aparte para
  la puerta final y la de llegada). Las puertas de la sala actual sí pueden seguir mostrando el estado real, porque es
  igual al recordado (invariante de R2).
- **H-3 (FR-251, ambigüedad)**: la spec no dice si el nombre de «ir a <sala>» se compara distinguiendo mayúsculas o
  espacios. Propuesta del plan: comparar `nombre.strip().casefold()` con el nombre de la sala tratado igual; se
  confirma con el integrante 3 antes de `tasks.md`.
- **H-4 (salidas repetidas)**: si una sala tiene dos salidas hacia la misma vecina, el mapa empareja caras con la misma
  regla de la `Mazmorra` (la primera salida que vuelve). Con salidas repetidas, una de las caras de la vecina no queda
  emparejada desde el otro lado y no se observa desde allí. Las criptas publicadas no tienen salidas repetidas (H-1 de
  la 001); es un límite conocido que se documenta en `DECISIONES.md`.
- **H-5 (escenario H2-5, ambigüedad)**: dice «lo que el mapa ofrece a "ir a" **desde A**» con la puerta A–C «sin
  observar». Si el jugador estuviera **en** A, esa puerta tendría cara en A y ya estaría observada (FR-207), así que el
  escenario no puede leerse como «el jugador está en A». El plan lo lee como «las salidas de A que se ofrecen», con el
  jugador en otra sala (A y C exploradas por la antorcha); la prueba se arma así.
- **H-6 (SC-206, tamaño)**: dice «1 000 salas»; el bench de la 001 usa 1 024 (32 × 32), «al menos 1 000». Se usa la
  misma cuadrícula de 1 024 para medir en la misma cripta que la 001.
- **H-7 (dependencia de la 001)**: el mapa usa `Mazmorra._salida_inversa` (privada) para emparejar caras, como ya
  hace `PartidaGuardada`. Si el integrante 1 cambia esa regla o su nombre, avisa antes (las pruebas H2-6 y A16 lo
  detectan).
- **H-8 (informativo, FR-203)**: cargar una partida guardada reemplaza el mapa por el guardado, que puede tener menos
  salas exploradas que el mapa vivo. No contradice FR-203 (no es una sala que «vuelve» dentro de la misma partida,
  sino otra partida cargada, FR-221), pero conviene que la spec lo diga si se vuelve a editar.
