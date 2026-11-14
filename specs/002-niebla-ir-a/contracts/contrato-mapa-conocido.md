# Contrato: lo que el mapa conocido ofrece

**Dueño**: integrante 2 · **Usuarios**: «ir a» (FR-250 a FR-264), la vista, el comando de ver el mapa y el resumen de
`historia` (integrante 3) · **Capa**: Logic (grafo, búsqueda por nombre) y DTO (vista, guardado) ·
Ver [research.md](../research.md), R5 · Modelo: [data-model.md](../data-model.md)

Este contrato cumple FR-225 y FR-217: todo lo que «ir a» y la interfaz usen del mapa sale de aquí, y nada más.
Aquí van nombres y reglas; el código llega en `tasks.md`.

Acceso: el mapa vive en el motor de la partida, `contexto.motor.mapa` (`MapaConocido`). En la línea de tiempo, el motor
aparte que arma la 004 tiene el suyo, ya restaurado desde el punto de control y re-simulado.

## (a) Grafo para «ir a»

```text
GrafoMapaConocido(mapa)                      # Logic/GrafoMapaConocido.py
  cantidad_salas() -> int                    # len(Mazmorra.salas): ids reales, 0 .. cantidad_salas() - 1
  salidas(u: int)  -> list[(destino, costo)] # salidas UTILIZABLES de u
  entradas(x: int) -> list[(origen, costo)]  # salidas UTILIZABLES que llegan a x
```

Es la interfaz **exacta** de [busqueda-rutas.md](../../001-terreno-cazador/contracts/busqueda-rutas.md) de la 001, así
que se le pasa tal cual a `BusquedaCostoMinimo` o a `paso_desde_cero`:

```text
grafo = GrafoMapaConocido(contexto.motor.mapa)       # una vez por partida (o por viaje)
paso = paso_desde_cero(grafo, destino, sala_jugador, None)   # (vecina, costo) | None
```

**«Utilizable»** (FR-225, FR-252): una salida u→v en la dirección d es utilizable si y solo si

1. u está **explorada**,
2. v está **explorada**,
3. la cara de u (`sala u, dirección d`) se recuerda **abierta**. Una cara «sin observar» o recordada cerrada no
   cuenta, aunque la cara de v se recuerde abierta (escenario H2-6).

Garantías:

- `costo` es el **igualado** por Logic (`SalidaViva.costo`, 001 FR-101): el mismo en los dos sentidos aunque solo una
  cara lo declare, y 100 si ninguna lo declara.
- Los ids son los **reales** del esqueleto: el desempate por menor id de la búsqueda de la 001 da el mismo resultado
  que FR-253 (escenario H2-5).
- `salidas` y `entradas` leen el mapa **en vivo** en cada llamada: reflejan las observaciones hechas hasta ese momento
  (regla 2 de la 001). Una salida hacia una sala avistada o desconocida nunca aparece.
- No consultan el estado real de ninguna puerta, ni el contenido, ni el reporte de resolubilidad.
- Costo: `salidas(u)` O(4); `entradas(x)` O(grado de entrada de x); `cantidad_salas()` O(1).

**Aviso cuando cambia una salida utilizable** (regla 3 de la 001). `MapaConocido.observador_rutas` vale `None`. Si se
le asigna un objeto con `puerta_cambio(a, b)` (por ejemplo, quien guarde una `BusquedaCostoMinimo` entre pasos), el
mapa le avisa con los **destinos** de lo que cambió:

| Qué cambió en el mapa | Aviso |
|---|---|
| Una observación cambia la cara de u (dirección d, destino v) entre «abierta» y «no abierta», con u y v exploradas | `puerta_cambio(v, v)` por esa cara |
| Una sala x pasa a explorada | `puerta_cambio(x, w)` por cada salida utilizable x→w, y `puerta_cambio(x, x)` si alguna salida utilizable llega a x |

El aviso llega dentro del mismo intervalo en que cambió el mapa. **El pergamino no avisa** (igual que con las
puertas reales): quien guarde una búsqueda debe registrar en el historial su descarte, como hace
`RutasHaciaJugador._registrar_descarte`, o empezar una búsqueda nueva.

**Recomendación**: como el viaje recalcula antes de cada paso (FR-255) y el conocimiento solo cambia entre un paso y el
siguiente, una búsqueda nueva por paso (`paso_desde_cero`) no necesita el aviso, da por construcción el mismo paso que
«calcular desde cero» (FR-255, SC-251) y cabe en los 5 ms de NFR-250 con la cripta de referencia. El aviso queda
disponible si la medición de NFR-251 pide reutilizar la búsqueda.

## (b) DTO de solo lectura para la vista, el comando y el resumen

```text
contexto.motor.mapa.a_dto() -> MapaConocidoDTO       # Logic arma el DTO; Service solo lo copia
```

```text
MapaConocidoDTO(salas: list[SalaConocidaDTO])                       # solo exploradas, por id creciente
SalaConocidaDTO(id: int, nombre: str, salidas: list[SalidaConocidaDTO | None])   # 4 posiciones: N, S, E, O
SalidaConocidaDTO(costo: int, estado_puerta: int, destino: int | None)
```

| Campo | Qué es | Requisitos |
|---|---|---|
| `SalaConocidaDTO.id` | Id real de una sala **explorada** (nunca de una avistada o desconocida) | FR-204, SC-202 |
| `SalaConocidaDTO.nombre` | Nombre de la sala explorada | FR-205 |
| `SalidaConocidaDTO.costo` | Costo igualado | FR-205, FR-219, 001 FR-101 |
| `SalidaConocidaDTO.estado_puerta` | `ABIERTA`, `CERRADA` o `SIN_OBSERVAR` (constantes de `DTO/MapaConocidoDTO.py`): el **recordado** de la cara de esta sala, nunca el real | FR-208, FR-212, FR-219 |
| `SalidaConocidaDTO.destino` | Id si el destino está explorado; `None` si está avistado: «sala sin explorar detrás de esta salida», una por salida, sin identificador | FR-204, FR-219 |

Garantías:

- Nunca aparece una sala desconocida: toda salida de una sala explorada lleva a una explorada o a una avistada.
- Dos salidas hacia la misma sala avistada aparecen como dos `destino = None` independientes; cuando esa sala se
  explora, las dos pasan a tener el mismo id (escenario H5-5).
- No trae contenido (enemigos, objetos, trampas) de ninguna sala, ni siquiera de las exploradas por la antorcha
  (FR-211, FR-219).
- `a_dto()` no consume tiempo, no registra nada en el historial ni cambia ningún estado (FR-220). Costo O(S).
- Es el mismo DTO para la vista de la partida, el comando de ver el mapa y `ResumenHistoriaDTO.mapa_conocido` (que hoy
  es `object | None`; con la 002, `MapaConocidoDTO`). En el resumen se arma sobre el motor aparte de la 004
  (`motor.mapa.a_dto()`), así que muestra el mapa de ese instante y nada de acciones revertidas (FR-223).
- Si se agrega a `EstadoJuegoDTO`, va como campo nuevo al final con valor por defecto (`mapa_conocido:
  MapaConocidoDTO | None = None`). Decide el integrante 3.
- La partida terminada sigue teniendo su mapa: el comando funciona igual (caso borde).

## (c) Búsqueda de una sala explorada por nombre

```text
contexto.motor.mapa.buscar_exploradas(nombre: str) -> list[int]
```

| Resultado | Qué hace «ir a» (integrante 3) | FR |
|---|---|---|
| `[]` | Rechaza la orden con **el mismo mensaje** para avistada, desconocida o inexistente; sin pasos, sin tiempo, sin acción, sin `partida.log` | FR-251 |
| `[id]` y `id == jugador.Sala_Actual` | Informa que ya está allí; sin pasos ni tiempo | FR-251 |
| `[id]` | Destino del viaje | FR-250 |
| dos o más ids | Rechaza por ambiguo, sin tiempo | FR-251 |

- Solo compara nombres de salas **exploradas**: una sala avistada o desconocida con el mismo nombre no cuenta ni se
  revela.
- Comparación: propuesta del plan `nombre.strip().casefold()` contra el nombre de la sala tratado igual (hallazgo
  H-3); se confirma con el integrante 3 antes de `tasks.md`.
- Ids en orden creciente. Costo O(S) por orden (no por paso). No cambia ningún estado.

## (d) Lo que el mapa conocido NO ofrece

- El **reporte de resolubilidad** de la 003 (FR-313): se muestra al iniciar como excepción de FR-217, no forma parte del
  mapa, no lo modifica y «ir a» no lo usa.
- El **estado real** de ninguna puerta, salvo a través del recordado. (Las puertas de la sala actual que hoy muestra
  `EstadoJuegoDTO.sala` son reales, pero mientras el jugador está en una sala el recordado es igual al real: research,
  R2.)
- El **contenido** de ninguna sala.
- La **identidad** de las salas avistadas y cualquier dato de las desconocidas. Ver el hallazgo H-2 del plan:
  `EstadoJuegoDTO.sala.salidas[d].sala_destino` hoy trae el id real de destinos avistados.
- El esqueleto (`Mazmorra`, `GrafoEsqueleto`, `GestorEsqueleto`): «ir a» no debe usarlo para rutas (FR-252).
- **Inversas** para la línea de tiempo: la 004 reconstruye hacia adelante (FR-223).
- Escritura: ni «ir a» ni la interfaz escriben el mapa. Los pasos de «ir a» lo actualizan porque son movimientos
  ordinarios (`Motor.mover_jugador`, FR-264).

## Cómo se avisa a quien usa este contrato

Si cambia una firma o una regla de este contrato, el integrante 2 avisa antes al integrante 3. Las pruebas de
`tests/test_grafo_mapa_conocido.py` y `tests/test_mapa_conocido_vista.py` fijan el contrato.
