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
| `marcadores` | arreglo de `MarcadorPergamino` | Ordenado por posición (no decreciente: puede haber varios en la misma). |
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
| `posicion` | `int ≥ 0` | Acciones vigentes completadas cuando ocurrió el cambio. |
| `quitados` | arreglo de `str` | Ids de pergaminos que salen del inventario. El pergamino usado para revertir es un quitado. |
| `agregados` | arreglo de `str` | Ids de pergaminos que quedan en el inventario aunque la acción que los trajo se revirtió (FR-424). |

Regla: al llegar a `posicion` acciones completadas, se quitan los `quitados` del inventario y se agregan
los `agregados`. Un marcador tiene al menos un elemento entre las dos listas, y un id no está en las
dos a la vez.

Regla de recorte: al pasar de `c+1` a `c` acciones, los marcadores con posición mayor que `c` se
mueven a `c`, y se agrega el nuevo en `c` con lo que resulte de comparar los pergaminos del inventario
vivo con los del estado reconstruido a `c` acciones (`quitados` los que sobran en el reconstruido,
`agregados` los que sobran en el vivo).

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
| `retroceder_una()` | Quita la última acción y los puntos con más de `c` acciones; mueve a `c` los marcadores con posición mayor | O(1 + r) |
| `agregar_marcador(posicion, quitados, agregados)` | Anexa el marcador de pergamino (FR-424) | O(1) amortizado |
| `validar_instante(t, reloj_actual)` | Lanza `ValueError` con el motivo y el rango válido si t no es un entero ≥ 0 o es posterior al reloj actual (FR-409) | O(1) |
| `validar_accion(k)` | Lanza `ValueError` con el motivo y el rango válido si k no es un entero entre 1 y las acciones vigentes (FR-409) | O(1) |
| `ubicar_punto(acciones)` | Último punto con `acciones_completadas ≤ acciones` | O(log P) |
| `ubicar_accion_por_tiempo(t)` | Última acción con `tiempo ≤ t` | O(log A) |
| `registrar_carga(ordinal, sala)` / `registrar_ficha(ficha)` | Anexa si no estaba | O(1) / O(F) |

## ResumenHistoriaDTO (DTO)

Vista de solo lectura del estado en un instante (FR-405). Solo transporta datos.

| Campo | Descripción |
|---|---|
| `reloj` | El reloj del resumen, según FR-405 de la spec |
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
   ├─ pergamino leído (jugador.acciones −1) ──► retroceder_una + agregar_marcador  (recorte por el final)
   ├─ acción rechazada (sin cambio) ──────────► nada
   └─ sala cargada / ficha pedida ────────────► registrar_carga / registrar_ficha
```

Una consulta **no** transiciona nada: lee la línea y trabaja sobre un `Motor` aparte.

## Reglas de validación

- En **Logic** (`LineaTiempo`; son reglas de negocio, y Service no valida): `historia <t>` con t entero
  ≥ 0 y no posterior al reloj actual; `historia #k` con k entero entre 1 y las acciones del jugador
  (FR-409). Fallan con `ValueError`, con el motivo y el rango válido. `ServicioLineaTiempo` solo
  propaga el error.
- La validación de estructura del comando (que sea un entero) es de la interfaz.
- `--hasta`: entero ≥ 0; `--hasta` sin `--replay` es error de uso (FR-410).
- `--checkpoint-cada`: entero ≥ 1 (FR-415).
