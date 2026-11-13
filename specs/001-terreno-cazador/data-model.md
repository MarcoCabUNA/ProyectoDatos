# Modelo de datos (fase 1): Terreno y cazador

**Feature**: `001-terreno-cazador` · **Plan**: [plan.md](plan.md) · **Investigación**: [research.md](research.md)

Las clases nuevas llevan type hints y un docstring breve (Principio III). La columna «Capa» sigue
el Principio I.

Vocabulario: una **puerta** está abierta o cerrada; una **sala** de la búsqueda está **resuelta**
cuando su distancia ya es definitiva.

## DTO (transversal)

### `SalidaDTO` · `DTO/SalaDTO.py` · integrante 2 · **Confirmado con el integrante 2 el 11 de noviembre** (hecho: T001)

| Campo | Tipo | Regla | Requisito |
|---|---|---|---|
| `costo` (nuevo, último campo) | `int \| None = None` | El costo **declarado** en este lado, o `None` si este lado no lo declara. `desde_diccionario` lee `d.get("costo")`. `a_diccionario` lo escribe solo si no es `None`, para que las cachés en disco de P1 sigan iguales. Lógica calcula el costo final (ver `SalidaViva` y `Mazmorra._igualar_costos`). | FR-101 |

Data valida que sea un entero ≥ 1 y que los dos lados de una salida no declaren costos distintos
(FR-122). Si no se cumple, informa con contexto y la partida no inicia.

### `FichaEnemigoDTO` · `DTO/FichaEnemigoDTO.py` · integrante 1 · **Confirmado con el integrante 2 el 11 de noviembre**

| Campo | Tipo | Regla | Requisito |
|---|---|---|---|
| `rango` (nuevo) | `int \| None = None` | Se lee con `d.get("rango")` y se escribe en `a_diccionario` si no es `None`. Se agrega `"rango"` a `_CAMPOS` para que no quede también en `extras`. | FR-106 |
| `comportamiento` | `str` | Acepta `"cazador"`. | FR-106 |

`None` solo es válido si el enemigo no es un cazador. Data rechaza un cazador con `rango` `None`,
negativo o que no sea entero (FR-122). Lógica no repite esa validación.

### `ActorDTO` · `DTO/ActorDTO.py` · **Hecho (T039)**

| Campo | Tipo | Regla | Requisito |
|---|---|---|---|
| `comportamiento` (nuevo) | `str \| None = None` | El comportamiento del enemigo, o `None` para el jugador. Con él, la vista distingue a los cazadores. | FR-117 |

### `ArmadorEstado` · `Service/ArmadorEstado.py` · integrante 3 · **Por acordar con el integrante 3**

Copia el `SalidaDTO` del esqueleto y hoy solo reemplaza `cerrada` con el estado vivo. Como el
esqueleto trae el costo **declarado**, también debe reemplazar `costo` con `SalidaViva.costo`, el
costo igualado (FR-101, FR-116).

## Lógica

### `SalidaViva` · `Logic/Mazmorra.py` (modificación)

| Atributo | Tipo | Origen | Requisito |
|---|---|---|---|
| `costo_declarado` (nuevo) | `int \| None` | `salida_dto.costo`, tal como llegó. | FR-101 |
| `costo` (nuevo) | `int` | `costo_declarado`, o 100 si es `None`. `Mazmorra._igualar_costos` lo ajusta al cargar el esqueleto. No se registra en el historial: no cambia durante la partida. | FR-101 |

### `Mazmorra` · `Logic/Mazmorra.py` (extensión)

| Elemento | Qué hace | Requisito |
|---|---|---|
| `_igualar_costos()` (privado, nuevo; se llama en `cargar_esqueleto` justo después de `_igualar_caras()`) | Para cada cara: si declara costo, ese; si no, el que declara su cara inversa; si ninguna lo declara, 100. Recorre todas las salas en cada llamada, así que no depende del orden de las páginas. No valida costos distintos: eso es de Data. `_igualar_caras` no cambia. | FR-101 |
| `salidas_abiertas_con_costo(id_sala) -> list[tuple[int, int]]` | Igual que `salidas_abiertas`, en el **mismo orden**, pero con pares (destino, costo). | FR-102, FR-104 |
| `costo_paso(origen, destino) -> int` | El menor costo entre las salidas **abiertas** de `origen` hacia `destino`. Lanza `ValueError` si no hay ninguna. | FR-119 |
| `observador_puertas` (atributo, `None` por defecto) | Si no es `None`, `abrir_puerta` y `CierrePuerta.activar` le avisan con `puerta_cambio(a, b)` después de cambiar las caras. `a` y `b` son los **destinos** de las caras que cambiaron: con dos caras, los dos extremos; con una, su destino dos veces (ver [contrato](contracts/busqueda-rutas.md)). | FR-114 |

### `MonticuloMinimo` · `Estructuras/MonticuloMinimo.py` (nuevo, sin dependencias)

| Operación | Costo | Notas |
|---|---|---|
| `insertar(clave: int, valor: int)` | O(log n) | Entradas (clave, valor). Se comparan por clave y luego por valor. |
| `extraer_minimo() -> tuple[int, int]` | O(log n) | |
| `ver_minimo() -> tuple[int, int] \| None` | O(1) | |
| `esta_vacio()`, `tamano()` | O(1) | |
| `vaciar()` | O(1) | Lo usa `reiniciar` de la búsqueda. |

Las entradas se guardan en un array (`list` como almacenamiento contiguo). Nada de `heapq`.

### Protocolo «grafo de búsqueda» (ver [contrato](contracts/busqueda-rutas.md))

| Método | Devuelve |
|---|---|
| `cantidad_salas() -> int` | El límite superior de los ids de sala, más 1. |
| `entradas(x) -> list[tuple[int, int]]` | (origen, costo) de las salidas utilizables que llegan a x. |
| `salidas(u) -> list[tuple[int, int]]` | (destino, costo) de las salidas utilizables de u. |

### `GrafoEsqueleto` · `Logic/GrafoEsqueleto.py` (nuevo)

Implementa el protocolo sobre una `Mazmorra`. «Utilizable» = salida abierta **ahora**, hacia una
sala que existe. La adyacencia inversa (por sala, la lista de pares (origen, dirección)) es fija y
se arma una vez, en O(S + E). El estado de la puerta se lee en vivo en cada consulta.

### `BusquedaCostoMinimo` · `Logic/BusquedaCostoMinimo.py` (nuevo)

Búsqueda de costo mínimo **reanudable** desde un origen. No conoce cazadores ni jugadores.

| Estado | Tipo | Significado |
|---|---|---|
| `grafo` | protocolo | Sobre qué se busca. |
| `origen` | `int` | Sala desde la que se miden las distancias. |
| `distancia`, `marca_distancia` | `list[int]` de tamaño S | Distancia tentativa de cada sala. Vale solo si su marca es igual a `generacion`. |
| `marca_resuelta` | `list[int]` de tamaño S | La sala está resuelta (distancia definitiva) si es igual a `generacion`. |
| `frontera` | `MonticuloMinimo` | Pares (distancia tentativa, sala). |
| `generacion` | `int` | Crece en cada `reiniciar(origen)`. Reiniciar cuesta O(1). |
| `resueltas` | `int` | Cuántas salas se resolvieron (para el bench). |

| Operación | Qué hace | Costo |
|---|---|---|
| `reiniciar(origen)` | Nueva generación, frontera con (0, origen). | O(1), más vaciar la frontera |
| `distancia_hasta(sala, limite) -> int \| None` | Extiende la búsqueda hasta resolver `sala` o hasta que el mínimo de la frontera pase `limite`. Devuelve d o `None`. | Amortizado: cada sala se resuelve una vez por generación |
| `esta_resuelta(sala) -> bool`, `distancia_resuelta(sala) -> int` | Consultas O(1). | O(1) |
| `paso_hacia_origen(u, d) -> tuple[int, int]` | La vecina v de menor id con costo(u, v) + dist(v) = d, y ese costo (la salida abierta más barata hacia v, FR-119). | O(g) |

Función de referencia: `paso_desde_cero(grafo, origen, u, limite)`. Crea una búsqueda nueva
y devuelve el mismo resultado que el cazador **sin reutilizar nada**. La usan las pruebas de
FR-114 y el bench (alternativas A de R2 y R4).

Los arrays se crean una sola vez, en el constructor, con `grafo.cantidad_salas()` casillas, y no cambian
de tamaño. Por eso la búsqueda se crea con el esqueleto ya cargado: `Motor` se crea siempre después de
`Mazmorra.cargar_esqueleto` (`ServicioPartida`, `PartidaGuardada` y `BenchLogica`), y el esqueleto no
crece durante la partida.

Casos especiales: `paso_desde_cero` devuelve `None` también si `u == origen` (no hay paso que dar); `paso_hacia_origen` lanza `ValueError` si `u` no tiene una vecina en una ruta de costo d (no ocurre si d viene de `distancia_hasta`).

### `RutasHaciaJugador` · `Logic/RutasHaciaJugador.py` (nuevo)

La búsqueda compartida por todos los cazadores (decisiones R2 y R4).

| Estado | Tipo | Significado |
|---|---|---|
| `busqueda` | `BusquedaCostoMinimo` | Reutiliza los arrays entre generaciones. |
| `valida` | `bool` | `False` si se descartó. |
| `historial` | `HistorialRetroceso \| None` | Donde se registra la reversión «descartar». |
| `reutilizaciones`, `recalculos` | `int` | Contadores para el bench. No son estado del juego. |

| Operación | Qué hace | Requisito |
|---|---|---|
| `decidir(sala_cazador, sala_jugador, rango) -> tuple[int, int] \| None` | Si el origen difiere de `sala_jugador` o la búsqueda no es válida, reinicia. Luego aplica R3 y devuelve (destino, costo) o `None` (esperar). Registra «descartar» en el historial si creó o extendió la búsqueda. | FR-108 a FR-111, FR-114, FR-119 |
| `puerta_cambio(a, b)` | Si a o b están resueltas, descarta. Registra «descartar» en el historial en todos los casos. | FR-114 |
| `descartar()` | `valida = False`. | — |

Transiciones de `valida`:

```text
(inicio) --decidir--> válida --puerta que toca una sala resuelta / deshacer--> descartada
descartada --decidir--> válida (búsqueda nueva)
válida --decidir con otra sala de jugador--> válida (búsqueda nueva)
```

### `Comportamiento` · `Logic/Comportamientos.py` (extensión)

| Elemento | Qué hace | Requisito |
|---|---|---|
| `Comportamiento.decidir_paso(enemigo, motor) -> tuple[int, int] \| None` (nuevo, por defecto) | Llama a `decidir()`. Si devuelve un destino, el costo es `mazmorra.costo_paso(origen, destino)`. Lo usan `Guardian` y `Rastreador` sin cambios. | FR-102, FR-104 |
| `Errante.decidir_paso` (nuevo) | El mismo sorteo que `decidir()`, con la **misma** llamada a `motor.azar.randint`, pero sobre `salidas_abiertas_con_costo`. Devuelve la salida sorteada con su costo. `decidir()` no cambia. | FR-104 |
| `Cazador` (nueva, `NOMBRE = "cazador"`) | `decidir_paso` llama a `motor.rutas.decidir(...)` con `enemigo.ficha.rango`. En la historia 2 llama primero a `paso_desde_cero(motor.grafo, ...)` y en la historia 3 pasa a la búsqueda compartida (ver `tasks.md`). No usa `motor.azar`. Se agrega a `COMPORTAMIENTOS`. | FR-106 a FR-115, FR-119 a FR-121 |

### `Motor` · `Logic/motorJuego.py` (modificación)

| Cambio | Requisito |
|---|---|
| `__init__`: crea `self.grafo = GrafoEsqueleto(mazmorra)`, `self.rutas = RutasHaciaJugador(self.grafo, historial)` y asigna `mazmorra.observador_puertas = self.rutas` (tres líneas). | FR-112, FR-114 |
| `mover_jugador`: `terminar_accion_jugador(salida.costo)` en lugar de `COSTO_MOVER`. | FR-102 |
| `turno_enemigo`: usa `decidir_paso()`. Programa con el costo devuelto si se movió, o con 100 si espera o ataca. | FR-102, FR-103, FR-110, FR-121 |

### `Enemigo` · `Logic/Enemigo.py` (extensión)

| Cambio | Requisito |
|---|---|
| `a_dto()` redefinido: el `ActorDTO` de la base más `comportamiento` (si se confirma el campo con el integrante 3). | FR-117 |
