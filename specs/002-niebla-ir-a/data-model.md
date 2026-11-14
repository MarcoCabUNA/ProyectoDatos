# Modelo de datos (fase 1): Mapa conocido, memoria de puertas y antorcha

**Feature**: `002-niebla-ir-a` (parte del integrante 2) · **Plan**: [plan.md](plan.md) ·
**Decisiones**: [research.md](research.md) · **Contrato**: [contracts/contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md)

Notación: S = `len(Mazmorra.salas)` (ids de 0 a S − 1; la posición 0 puede estar vacía), c = `sala * 4 + dirección`
(0 = N, 1 = S, 2 = E, 3 = O), g = salidas de una sala (≤ 4).

## 1. Constantes (`DTO/MapaConocidoDTO.py`)

Viven en DTO porque las leen Logic, Data (al validar el binario) y la vista. Ningún otro módulo define estos valores.

| Constante | Valor | Significado |
|---|---|---|
| `DESCONOCIDA` | 0 | La sala no existe para el jugador (FR-206) |
| `AVISTADA` | 1 | No explorada y destino de una salida de una explorada (FR-204) |
| `EXPLORADA` | 2 | Entró, es la inicial o la exploró la antorcha (FR-202, FR-203, FR-210) |
| `SIN_OBSERVAR` | 0 | Cara nunca observada (FR-212); también toda cara de una dirección sin salida |
| `ABIERTA` | 1 | Cara abierta en su última observación (FR-208) |
| `CERRADA` | 2 | Cara cerrada en su última observación (FR-208) |

## 2. `MapaConocido` (Logic, nuevo, `Logic/MapaConocido.py`)

Estado de la partida. Lo crea el motor (`motor.mapa`); lo escriben solo `iniciar`, `entrar`, `puerta_cambio` y
`restaurar`.

| Atributo | Tipo | Notas |
|---|---|---|
| `estado` | `list[int]`, largo S | `DESCONOCIDA` / `AVISTADA` / `EXPLORADA` por id de sala |
| `caras` | `list[int]`, largo 4·S | `SIN_OBSERVAR` / `ABIERTA` / `CERRADA` por cara c |
| `mazmorra` | `Mazmorra` | Solo lectura: nombre, salidas, `SalidaViva.costo` y `cerrada` (para observar), `_salida_inversa` |
| `jugador` | `Jugador` | Solo lectura: `Sala_Actual`, para re-observar al recibir un aviso |
| `historial` | `HistorialRetroceso \| None` | Donde se registran las reversiones (R3); `None` en el bench sin motor |

| Método | Qué hace | Costo | Requisitos |
|---|---|---|---|
| `iniciar(sala: int) -> None` | `_explorar(sala)` y `_observar_puertas(sala)` | O(g) | FR-202, FR-207 |
| `entrar(sala: int, antorcha: bool) -> None` | `_explorar(sala)`; si `antorcha`, `_explorar(v)` para cada destino v de una salida de `sala` (abierta o cerrada); `_observar_puertas(sala)` | O(1 + Σ g de las que pasan a exploradas) | FR-203, FR-207, FR-210 a FR-214 |
| `puerta_cambio(a: int, b: int) -> None` | `_observar_puertas(jugador.Sala_Actual)`; `a` y `b` no se usan | O(1) | FR-207, FR-209 |
| `estado_sala(sala: int) -> int` | Lectura de `estado` | O(1) | NFR-201 |
| `estado_cara(sala: int, direccion: int) -> int` | Lectura de `caras` | O(1) | NFR-201 |
| `a_dto() -> MapaConocidoDTO` | Vista de solo lectura (§4) | O(S) | FR-217, FR-219, FR-220 |
| `buscar_exploradas(nombre: str) -> list[int]` | Ids de exploradas con ese nombre | O(S) | FR-251 |
| `a_guardado() -> MapaConocidoGuardadoDTO` | Copia de los dos arreglos con `list(...)` | O(S) | FR-221, FR-223, NFR-203 |
| `restaurar(dto: MapaConocidoGuardadoDTO \| None) -> None` | Con un DTO: valida largos (`ValueError`, riesgo R-8) y copia los arreglos, reemplazando el mapa en curso; no registra en el historial. Con `None`: pone todo en `DESCONOCIDA` / `SIN_OBSERVAR` y arma el mapa inicial desde `jugador.Sala_Actual`, como `iniciar` (esa sala explorada, los destinos de sus salidas avistados y sus puertas observadas, FR-202); lo que registre queda en el intervalo abierto, que `PartidaGuardada.cargar` descarta enseguida | O(S) | FR-202, FR-221, FR-223 |

Privados:

| Método | Qué hace |
|---|---|
| `_explorar(sala)` | Si ya está `EXPLORADA`, no hace nada. Si no, `_poner_estado(sala, EXPLORADA)` y, por cada salida de `sala` hacia una sala v que existe con `estado[v] == DESCONOCIDA`, `_poner_estado(v, AVISTADA)` |
| `_observar_puertas(sala)` | Por cada dirección d con salida s hacia una sala que existe: `_poner_cara(sala*4 + d, CERRADA si s.cerrada si no ABIERTA)`; si `_salida_inversa(sala, s.destino)` existe, su dirección d' (por identidad entre las 4 salidas del destino) y `_poner_cara(s.destino*4 + d', …)` con su estado real |
| `_poner_estado(sala, valor)` / `_poner_cara(c, valor)` | Si el valor es igual, nada. Si no: registra la reversión de esa casilla (índice y valor anterior ligados) con `historial.registrar_cambio` y escribe. No avisa a nadie (una búsqueda de «ir a» empieza de nuevo en cada paso, contrato (a)) |

**Invariantes** (se prueban):

1. Exactamente un estado por sala (FR-201): lo garantiza el arreglo.
2. Si `estado[u] == EXPLORADA`, todo destino v de una salida de u tiene `estado[v] != DESCONOCIDA` (FR-203, FR-204).
3. Si `estado[v] == AVISTADA`, existe una salida u→v con `estado[u] == EXPLORADA` (FR-204).
4. Ningún método baja un estado; solo la reversión del historial lo hace (FR-203, FR-222).
5. Mientras el jugador está en x, `caras[c]` es igual al estado real de cada cara de cada puerta con cara en x (FR-207).

### Transiciones de una sala

```text
DESCONOCIDA ──(una sala explorada tiene una salida hacia ella)──► AVISTADA
DESCONOCIDA ──(el jugador entra, es la inicial o la antorcha la explora)──► EXPLORADA
AVISTADA    ──(el jugador entra o la antorcha la explora)──► EXPLORADA
cualquiera  ◄──(pergamino: reversión registrada en el historial)── el estado que tenía antes de la acción
```

### Transiciones de una cara

```text
SIN_OBSERVAR ──(el jugador observa la puerta)──► ABIERTA | CERRADA (estado real)
ABIERTA ⇄ CERRADA ──(nueva observación con otro estado real)──
cualquiera ◄──(pergamino)── el estado que tenía antes de la acción
```

## 3. `GrafoMapaConocido` (Logic, nuevo, `Logic/GrafoMapaConocido.py`)

Grafo de búsqueda de «ir a» con la interfaz de `specs/001-terreno-cazador/contracts/busqueda-rutas.md`.

| Atributo | Tipo | Notas |
|---|---|---|
| `mapa` | `MapaConocido` | Se lee en vivo en cada llamada (`mapa.estado`, `mapa.caras`); no se guardan referencias a los arreglos, porque `restaurar` los reemplaza |
| `_inversa` | `list[list[tuple[int, int]]] \| None` | Por sala x, pares (origen, dirección) del esqueleto que llegan a x; se arma una vez en O(S + E), como en `GrafoEsqueleto` |

| Método | Devuelve | Costo |
|---|---|---|
| `cantidad_salas()` | `len(Mazmorra.salas)` | O(1) |
| `salidas(u)` | `[(v, costo)]` de las salidas utilizables de u (vacía si u no está explorada) | O(4) |
| `entradas(x)` | `[(u, costo)]` de las salidas utilizables que llegan a x (vacía si x no está explorada) | O(grado de entrada de x) |

«Utilizable»: `estado[u] == EXPLORADA`, `estado[v] == EXPLORADA` y `caras[u*4 + d] == ABIERTA`; costo =
`SalidaViva.costo` (igualado, 001 FR-101).

## 4. DTO de la vista (`DTO/MapaConocidoDTO.py`, nuevos, `frozen`)

Solo datos. Si en el futuro se agregan campos, van al final y con valor por defecto.

`MapaConocidoDTO`

| Campo | Tipo | Notas |
|---|---|---|
| `salas` | `list[SalaConocidaDTO]` | Solo exploradas, en orden creciente de id |

`SalaConocidaDTO`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `int` | Id real (solo de exploradas; lo necesita la vista para unir salidas con su destino explorado, H5-5) |
| `nombre` | `str` | FR-205 |
| `salidas` | `list[SalidaConocidaDTO \| None]` | 4 posiciones (N, S, E, O); `None` si no hay salida |

`SalidaConocidaDTO`

| Campo | Tipo | Notas |
|---|---|---|
| `costo` | `int` | Igualado (001 FR-101, FR-205); nunca el declarado por una sola cara |
| `estado_puerta` | `int` | `ABIERTA`, `CERRADA` o `SIN_OBSERVAR`: el **recordado** de la cara de esta sala (FR-208, FR-212) |
| `destino` | `int \| None` | Id si el destino está explorado; `None` si está avistado («sala sin explorar detrás de esta salida», FR-204, FR-219) |

No hay campos de contenido (enemigos, objetos, trampas) ni de estado real.

## 5. DTO guardado

`MapaConocidoGuardadoDTO` (`DTO/MapaConocidoDTO.py`, nuevo, `frozen`)

| Campo | Tipo | Notas |
|---|---|---|
| `estado_salas` | `list[int]` | Copia de `MapaConocido.estado` |
| `caras` | `list[int]` | Copia de `MapaConocido.caras` |

`a_diccionario()` → `{"estado_salas": [...], "caras": [...]}`; `desde_diccionario(d)` copia las dos listas.

`PartidaGuardadaDTO` (`DTO/PartidaGuardadaDTO.py`, modificado): campo nuevo al final, **antes de `linea`** (T002 de la
004):

| Campo | Tipo | Valor por defecto |
|---|---|---|
| `mapa` | `MapaConocidoGuardadoDTO \| None` | `None` |

`a_diccionario` agrega `"mapa": None` o el diccionario; `desde_diccionario` usa `d.get("mapa")`.

`PartidaGuardada` (`Logic/PartidaGuardada.py`, modificado; lo escribe el integrante 2 y lo revisa el integrante 1,
acuerdo del 14/11): `guardar` pasa `mapa=motor.mapa.a_guardado()`; `cargar` suma **una sola línea**, antes de
`motor.historial.descartar_intervalo_abierto()`: `motor.mapa.restaurar(partida.mapa)`, sin `if` ni `raise`. Si
`partida.mapa` es `None`, `restaurar(None)` arma el mapa inicial desde la sala actual del jugador (§2), como FR-202 con
la sala de inicio. Los guardados reales (versión 2) y los puntos de control siempre traen el mapa, así que `None` solo
aparece en un `PartidaGuardadaDTO` armado a mano (pruebas de otros integrantes que no conocen el mapa). `cargar` no
gana ningún comportamiento nuevo: nunca rechaza una partida por el mapa.

## 6. Bloque binario del mapa (`Data/GuardadoBinario.py`, versión 2)

| Parte | Formato |
|---|---|
| Cabecera | `<4sHQIQIIQIQI>` (58 bytes): magia, versión (= 2), offset y largo global, offset del índice, entradas, id mínimo, offset y largo del mapa, offset y largo de la línea (T003 de la 004) |
| Bloque del mapa | `I` cantidad S · `S` bytes de estado · `S` bytes de caras (bits 0-1 = N, 2-3 = S, 4-5 = E, 6-7 = O) |
| Largo 0 | `mapa` es `None` |
| Validación (solo formato) | estado ∈ {0, 1, 2}; cada par de bits ∈ {0, 1, 2}; largo exacto; offset y largo dentro de la zona anterior al índice. Si no, `ErrorGuardado` |
| Puntos de control (bloque de la línea, T003 de la 004) | Cada punto lleva, en este orden, su bloque global, sus salas y el bloque de su mapa con el mismo formato |

`cargar_sala` no lee este bloque. Un archivo de versión 1 se rechaza antes de leer la cabecera completa.

## 7. `RepartidorAvisosPuertas` (Logic, nuevo, `Logic/RepartidorAvisosPuertas.py`)

| Atributo / método | Notas |
|---|---|
| `observadores: list` | En orden fijo: `[motor.rutas, motor.mapa]` |
| `puerta_cambio(a, b) -> None` | Llama a `puerta_cambio(a, b)` de cada observador, en orden. O(cantidad de observadores) = O(1) |

## 8. Cambios en el motor (`Logic/motorJuego.py`; lo escribe el integrante 2 en T033 y lo revisa el integrante 1 antes del merge, acuerdo del 14/11)

| Lugar | Línea nueva o cambiada | FR |
|---|---|---|
| `__init__`, después de crear `self.rutas` | `self.mapa = MapaConocido(mazmorra, jugador, self.historial)` | FR-201 |
| `__init__`, reemplaza `self.mazmorra.observador_puertas = self.rutas` | `self.mazmorra.observador_puertas = RepartidorAvisosPuertas([self.rutas, self.mapa])` | FR-114 (001), FR-207 |
| `iniciar()`, después de `self.rastro.marcar(...)` | `self.mapa.iniciar(self.jugador.Sala_Actual)` | FR-202 |
| `mover_jugador()`, justo después de `self.jugador.Sala_Actual = destino` | `self.mapa.entrar(destino, self.efectos.tiene(self.jugador, "antorcha"))` | FR-203, FR-210, FR-214 |

## 9. Relaciones

```text
Motor ──tiene──► MapaConocido ──lee──► Mazmorra (esqueleto, estado real al observar)
  │                   ▲   └──lee──► Jugador.Sala_Actual
  │                   │ registra reversiones
  └──► HistorialRetroceso
Mazmorra.observador_puertas ──► RepartidorAvisosPuertas ──► RutasHaciaJugador (001)
                                                        └──► MapaConocido
GrafoMapaConocido ──lee──► MapaConocido + Mazmorra        (lo usa «ir a», integrante 3)
PartidaGuardada ──a_guardado / restaurar──► MapaConocidoGuardadoDTO ──► PartidaGuardadaDTO.mapa ──► GuardadoBinario
ArmadorEstado / ArmadorResumen / comando (integrante 3) ──► motor.mapa.a_dto() ──► MapaConocidoDTO
```
