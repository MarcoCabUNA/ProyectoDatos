# Contrato: búsqueda de costo mínimo compartida (cazador e «ir a»)

**Dueño**: integrante 1 · **Usuarios**: el cazador (esta feature) y «ir a» (feature 002, integrantes 2 y 3)
**Capa**: Lógica · Ver [research.md](../research.md), R3 y R5

## Grafo de búsqueda

Cualquier objeto con estos tres métodos sirve como grafo:

```text
cantidad_salas() -> int                      # ids de sala válidos: 0 .. cantidad_salas() - 1
entradas(x: int) -> list[(origen, costo)]    # salidas UTILIZABLES que llegan a x
salidas(u: int)  -> list[(destino, costo)]   # salidas UTILIZABLES de u
```

Reglas que el grafo debe cumplir:

1. `costo` es un entero ≥ 1.
2. `entradas` y `salidas` describen las mismas salidas vistas desde cada extremo, y en cada
   llamada reflejan el estado **actual** («utilizable» lo define quien implementa el grafo).
3. Si cambia cuándo una salida es utilizable y la búsqueda ya está en curso, quien implementa el
   grafo avisa con `puerta_cambio(a, b)` a quien guarda la búsqueda, o empieza una búsqueda nueva.

| Grafo | «Utilizable» | Implementa |
|---|---|---|
| `GrafoEsqueleto` | abierta ahora, en el esqueleto completo | Integrante 1 |
| Grafo del mapa conocido | entre salas exploradas, con la puerta **recordada** abierta | Integrante 2 (feature 002) |

## Operaciones

```text
BusquedaCostoMinimo(grafo)
  .reiniciar(origen)                           # O(1)
  .distancia_hasta(sala, limite) -> int|None   # extiende solo lo necesario; None si d > limite o sin ruta
  .paso_hacia_origen(u, d) -> (destino, costo) # vecina de menor id con costo(u,v) + dist(v) = d

paso_desde_cero(grafo, origen, u, limite) -> (destino, costo) | None   # referencia sin reutilización
```

`paso_hacia_origen` aplica siempre el desempate de §3.2 y FR-111: la vecina de **menor id**. El
costo es el de la salida utilizable más barata hacia esa vecina (FR-119). Si `limite` es `None`,
la búsqueda no tiene tope.

## Uso esperado

- **Cazador**: `origen` = la sala del jugador, `u` = la sala del cazador, `limite` = `rango`.
  Lo hace `RutasHaciaJugador`, que comparte la búsqueda entre todos los cazadores.
- **«Ir a»**: `origen` = la sala destino, `u` = la sala del jugador, `limite` = `None`. Antes de
  cada paso, el bucle de Servicios vuelve a pedir el paso (feature 002), igual que el cazador.

## Garantías

- La respuesta no depende de cuánto se reutilizó: es igual a `paso_desde_cero` (FR-114).
- No usa `heapq`, `dict`, `set` ni ninguna biblioteca de grafos (Principio II).
- No consume el generador aleatorio (FR-115).
