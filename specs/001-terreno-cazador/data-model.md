# Modelo de datos (fase 1): Terreno y cazador

**Feature**: `001-terreno-cazador` · **Plan**: [plan.md](plan.md) · **Investigación**: [research.md](research.md)

Las clases nuevas llevan type hints y un docstring breve (Principio III). La columna «Capa» sigue
el Principio I.

## DTO (transversal)

### `SalidaDTO` · `DTO/SalaDTO.py` · integrante 2 · **Propuesto — pendiente de confirmar con integrante 2**

| Campo | Tipo | Regla | Requisito |
|---|---|---|---|
| `costo` (nuevo) | `int` | 100 si el JSON no lo trae. `desde_diccionario` lee `d.get("costo", 100)`. `a_diccionario` lo escribe solo si es distinto de 100, para que las cachés en disco de P1 sigan iguales. | FR-101 |

Data valida que sea un entero ≥ 1 (FR-122). Si no lo es, informa con contexto y la partida no inicia.

### `FichaEnemigoDTO` · `DTO/FichaEnemigoDTO.py` · integrante 1 · **Propuesto — pendiente de confirmar con integrante 2**

| Campo | Tipo | Regla | Requisito |
|---|---|---|---|
| `rango` (nuevo) | `int \| None = None` | Se lee con `d.get("rango")` y se escribe en `a_diccionario` si no es `None`. Se agrega `"rango"` a `_CAMPOS` para que no quede también en `extras`. | FR-106 |
| `comportamiento` | `str` | Acepta `"cazador"`. | FR-106 |

`None` solo es válido si el enemigo no es un cazador. Data rechaza un cazador con `rango` `None`,
negativo o que no sea entero (FR-122). Lógica no repite esa validación.

### `ActorDTO` · `DTO/ActorDTO.py` · **Propuesto — pendiente de confirmar con integrante 3**

| Campo | Tipo | Regla | Requisito |
|---|---|---|---|
| `comportamiento` (nuevo) | `str \| None = None` | El comportamiento del enemigo, o `None` para el jugador. Con él, la vista distingue a los cazadores. | FR-117 |

El costo de las salidas ya llega a la vista: `ArmadorEstado` copia el `SalidaDTO` del esqueleto
y solo reemplaza `cerrada`, así que `costo` viaja sin cambios (FR-116).

## Lógica

### `SalidaViva` · `Logic/Mazmorra.py` (modificación)

| Atributo | Tipo | Origen | Requisito |
|---|---|---|---|
| `costo` (nuevo) | `int` | `salida_dto.costo`. Es fijo: no se registra en el historial porque nunca cambia. | FR-101 |

### `Mazmorra` · `Logic/Mazmorra.py` (extensión)

| Elemento | Qué hace | Requisito |
|---|---|---|
| `salidas_abiertas_con_costo(id_sala) -> list[tuple[int, int]]` | Igual que `salidas_abiertas`, en el **mismo orden**, pero con pares (destino, costo). | FR-102, FR-104 |
| `costo_paso(origen, destino) -> int` | El menor costo entre las salidas **abiertas** de `origen` hacia `destino`. | FR-119 |
| `observador_puertas` (atributo, `None` por defecto) | Si no es `None`, `abrir_puerta` y `CierrePuerta.activar` le avisan con `puerta_cambio(sala_a, sala_b)` después de cambiar las dos caras. | FR-114 |

### `MonticuloMinimo` · `Estructuras/MonticuloMinimo.py` (nuevo, sin dependencias)

| Operación | Costo | Notas |
|---|---|---|
| `insertar(clave: int, valor: int)` | O(log n) | Entradas (clave, valor). Se comparan por clave y luego por valor. |
| `extraer_minimo() -> tuple[int, int]` | O(log n) | |
| `ver_minimo() -> tuple[int, int] \| None` | O(1) | |
| `esta_vacio()`, `tamano()` | O(1) | |

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
| `marca_cerrada` | `list[int]` de tamaño S | La sala está cerrada (distancia definitiva) si es igual a `generacion`. |
| `frontera` | `MonticuloMinimo` | Pares (distancia tentativa, sala). |
| `generacion` | `int` | Crece en cada `reiniciar(origen)`. Reiniciar cuesta O(1). |
| `cerradas` | `int` | Cuántas salas se cerraron (para el bench). |

| Operación | Qué hace | Costo |
|---|---|---|
| `reiniciar(origen)` | Nueva generación, frontera con (0, origen). | O(1), más vaciar la frontera |
| `distancia_hasta(sala, limite) -> int \| None` | Extiende la búsqueda hasta cerrar `sala` o hasta que el mínimo de la frontera pase `limite`. Devuelve d o `None`. | Amortizado: cada sala se cierra una vez por generación |
| `esta_cerrada(sala) -> bool`, `distancia_cerrada(sala) -> int` | Consultas O(1). | O(1) |
| `paso_hacia_origen(u, d) -> tuple[int, int]` | La vecina v de menor id con costo(u, v) + dist(v) = d, y ese costo (la salida abierta más barata hacia v, FR-119). | O(g) |

Función de referencia: `paso_desde_cero(grafo, origen, u, limite)`. Crea una búsqueda nueva
y devuelve el mismo resultado que el cazador **sin reutilizar nada**. La usan las pruebas de
FR-114 y el bench (alternativas A de R2 y R4).

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
| `puerta_cambio(a, b)` | Si a o b están cerradas, descarta. Registra «descartar» en el historial en todos los casos. | FR-114 |
| `descartar()` | `valida = False`. | — |

Transiciones de `valida`:

```text
(inicio) --decidir--> válida --puerta que toca una sala cerrada / deshacer--> descartada
descartada --decidir--> válida (búsqueda nueva)
válida --decidir con otra sala de jugador--> válida (búsqueda nueva)
```

### `Comportamiento` · `Logic/Comportamientos.py` (extensión)

| Elemento | Qué hace | Requisito |
|---|---|---|
| `Comportamiento.decidir_paso(enemigo, motor) -> tuple[int, int] \| None` (nuevo, por defecto) | Llama a `decidir()`. Si devuelve un destino, el costo es `mazmorra.costo_paso(origen, destino)`. Lo usan `Guardian` y `Rastreador` sin cambios. | FR-102, FR-104 |
| `Errante.decidir_paso` (nuevo) | El mismo sorteo que `decidir()`, con la **misma** llamada a `motor.azar.randint`, pero sobre `salidas_abiertas_con_costo`. Devuelve la salida sorteada con su costo. `decidir()` no cambia. | FR-104 |
| `Cazador` (nueva, `NOMBRE = "cazador"`) | `decidir_paso` llama a `motor.rutas.decidir(...)` con `enemigo.ficha.rango`. No usa `motor.azar`. Se agrega a `COMPORTAMIENTOS`. | FR-106 a FR-115, FR-119 a FR-121 |

### `Motor` · `Logic/motorJuego.py` (modificación)

| Cambio | Requisito |
|---|---|
| `__init__`: crea `self.rutas = RutasHaciaJugador(GrafoEsqueleto(mazmorra), historial)` y asigna `mazmorra.observador_puertas = self.rutas`. | FR-114 |
| `mover_jugador`: `terminar_accion_jugador(salida.costo)` en lugar de `COSTO_MOVER`. | FR-102 |
| `turno_enemigo`: usa `decidir_paso()`. Programa con el costo devuelto si se movió, o con 100 si espera o ataca. | FR-102, FR-103, FR-110, FR-121 |

### `Enemigo` · `Logic/Enemigo.py` (extensión)

| Cambio | Requisito |
|---|---|
| `a_dto()` redefinido: el `ActorDTO` de la base más `comportamiento` (si se confirma el campo con el integrante 3). | FR-117 |
