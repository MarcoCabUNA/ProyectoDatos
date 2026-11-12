# Modelo de datos: Línea de tiempo

**Feature**: `004-linea-tiempo` · **Plan**: [plan.md](plan.md) · **Investigación**: [research.md](research.md)

Todos los arreglos son `list` usadas como almacenamiento contiguo. Todo se agrega **al final** y todo
recorte quita **del final**; por eso nacen ordenados y no hace falta ordenar.

## LineaTiempo (Logic)

Es la historia de la partida tal como quedó. Una por partida; vive en `ContextoPartida.linea`. No
hace I/O ni conoce `Data`.

| Campo | Tipo | Descripción |
|---|---|---|
| `k` | `int ≥ 1` | Cada cuántas acciones del jugador se guarda un punto de control (FR-415). Fijo para la línea. |
| `acciones` | arreglo de `AccionVigente` | La acción número k es la posición k (empezando en 1). Solo las vigentes. |
| `marcadores` | arreglo de `MarcadorPergamino` | Ordenado por posición. |
| `puntos` | arreglo de `PuntoControl` | Ordenado por acciones completadas (el primero, con 0, se toma al empezar). |
| `cargas` | arreglo de `RegistroCarga` | En el orden **real** de carga. No se recorta (H-1). |
| `fichas` | arreglo de fichas del catálogo | Una por id distinto visto. Búsqueda lineal por id (son pocas; no se usa `dict`). |

### AccionVigente

| Campo | Tipo | Descripción |
|---|---|---|
| `tiempo` | `int ≥ 0` | Reloj en que el jugador tomó la decisión (el estado «justo antes» de la acción). Estrictamente creciente. |
| `accion` | `AccionDTO` | Tipo y parámetros. **Nunca** `retroceder` ni la lectura de un pergamino. |

### MarcadorPergamino

| Campo | Tipo | Descripción |
|---|---|---|
| `posicion` | `int ≥ 0` | Acciones vigentes completadas cuando se descontó el pergamino. |
| `id_objeto` | `str` | Id del pergamino descontado. |
| `efecto_externo` | opcional | **Reservado** (H-2): lo que la acción revertida hizo con un pergamino fuera del historial. No se implementa hasta que Marco confirme. |

Regla de recorte: al pasar de `c+1` a `c` acciones, los marcadores con posición mayor que `c` se
mueven a `c` y se agrega el nuevo en `c`.

### PuntoControl

| Campo | Tipo | Descripción |
|---|---|---|
| `acciones_completadas` | `int ≥ 0` | Acciones del jugador hechas cuando se tomó (clave de la búsqueda binaria). |
| `partida` | `PartidaGuardadaDTO` | Estado global, **con** el estado del azar. |
| `salas` | `[SalaGuardadaDTO]` | Un bloque por sala del esqueleto. |
| `mapa_conocido` | opcional | Copia del mapa conocido (spec 002). Ausente hasta que exista. |

Se toma justo cuando el jugador tiene el control, cada K acciones (no más de una cada K: FR-416).

### RegistroCarga

| Campo | Tipo | Descripción |
|---|---|---|
| `ordinal` | `int ≥ 0` | Acciones vigentes completadas cuando se cargó la sala (H-1). |
| `sala` | `SalaDTO` | El contenido inicial que Data entregó a Logic para esa sala. |

A lo sumo uno por sala.

## Operaciones de LineaTiempo

| Operación | Efecto | Costo |
|---|---|---|
| `agregar_accion(tiempo, accion)` | Anexa la acción vigente | O(1) amortizado |
| `necesita_punto(acciones_completadas)` | `True` si pasaron K acciones desde el último punto | O(1) |
| `agregar_punto(punto)` | Anexa un punto de control | O(1) amortizado |
| `retroceder_una(id_pergamino)` | Quita la última acción y los puntos con más de `c` acciones; mueve marcadores; agrega el marcador | O(1 + r) |
| `ubicar_punto(acciones)` | Último punto con `acciones_completadas ≤ acciones` | O(log P) |
| `ubicar_accion_por_tiempo(t)` | Última acción con `tiempo ≤ t` | O(log A) |
| `registrar_carga(ordinal, sala)` / `registrar_ficha(ficha)` | Anexa si no estaba | O(1) / O(F) |

## ResumenHistoriaDTO (DTO)

Vista de solo lectura del estado en un instante (FR-405). Solo transporta datos.

| Campo | Descripción |
|---|---|
| `reloj` | El reloj del resumen (ver H-3) |
| `sala` | Nombre e id de la sala del jugador |
| `jugador` | Vida, vida máxima, ataque, defensa y velocidad |
| `inventario` | Objetos en orden real, arma y armadura equipadas. **Sin cursor** (FR-406) |
| `efectos` | Efectos activos del jugador con su duración restante |
| `enemigos` | Los enemigos de esa sala con su vida |
| `mapa_conocido` | Opcional; ausente si la spec 002 no está |
| `terminada_antes` | `bool`: `--replay … --hasta` con t posterior al final (FR-412) |
| `instante_pedido` | t, o la acción k, según la consulta |

No hay campo de mensajes (FR-406).

## Estados y transiciones de la línea

```text
inicio ──(motor.iniciar + primera decisión)──► punto 0
   │
   ├─ acción aceptada (jugador.acciones +1) ──► agregar_accion  (+ punto si pasaron K)
   ├─ pergamino leído (jugador.acciones −1) ──► retroceder_una  (recorte por el final)
   ├─ acción rechazada (sin cambio) ──────────► nada
   └─ sala cargada / ficha pedida ────────────► registrar_carga / registrar_ficha
```

Una consulta **no** transiciona nada: lee la línea y trabaja sobre un `Motor` aparte.

## Reglas de validación (en Service, no en Logic ni en Data)

- `historia <t>`: t entero ≥ 0 y no posterior al reloj actual (FR-409).
- `historia #k`: k entero entre 1 y `jugador.acciones` (FR-409).
- La validación de estructura del comando (que sea un entero) es de la interfaz.
- `--hasta`: entero ≥ 0; `--hasta` sin `--replay` es error de uso (FR-410).
- `--checkpoint-cada`: entero ≥ 1 (FR-415).
