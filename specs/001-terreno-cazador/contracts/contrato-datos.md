# Contrato de datos de la feature 001

> **Confirmado con el integrante 2 el 11 de noviembre, tal como está.** `ActorDTO` ya está hecho
> (T039). Pendiente de confirmar con el integrante 3 la parte de `ArmadorEstado`.
> Este plan **no** incluye código de la capa Data. La validación es del integrante 2.

## Entrada desde el API o el paquete (Apéndice A)

Esqueleto (`GET /criptas/<id>/salas`), por salida. El costo puede venir en un lado, en los dos o en
ninguno (FR-101):

```json
"E": { "sala": 7, "costo": 250, "cerrada": true, "llave": "itm_llave_bronce", "cierre_automatico": 500 }
```

Catálogo (`GET /catalogo?ids=...`), ficha de un cazador:

```json
{ "id": "ent_sabueso_oseo", "clase": "enemigo", "nombre": "Sabueso óseo", "vida_max": 18,
  "ataque": 6, "defensa": 2, "velocidad": 120, "comportamiento": "cazador", "rango": 600, "suelta": [] }
```

## Campos de los DTO

| DTO | Campo | Tipo | Ausente en el JSON | Dueño | Requisito |
|---|---|---|---|---|---|
| `SalidaDTO` | `costo` | `int \| None` | `None`: este lado no declara costo. Va como **último** campo. | Integrante 2 | FR-101 |
| `FichaEnemigoDTO` | `rango` | `int \| None` | `None`. Solo es válido si `comportamiento != "cazador"`. | Integrante 1 | FR-106, FR-122 |
| `FichaEnemigoDTO` | `comportamiento` | `str` | (obligatorio, como en P1). Acepta `"cazador"`. | Integrante 1 | FR-106 |
| `ActorDTO` | `comportamiento` | `str \| None` | `None` (jugador) | Integrante 3 (hecho: T039) | FR-117 |

`SalidaDTO.costo` guarda lo **declarado**, no el costo final. Así Lógica distingue «no declarado» de
«declarado 100». Lógica iguala el costo de los dos lados al cargar el esqueleto
(`Mazmorra._igualar_costos`, junto a `_igualar_caras`): el lado que lo declara manda; si ninguno lo
declara, vale 100. Ver [data-model.md](../data-model.md).

Sobre `rango` con valor por defecto en Python: `FichaEnemigoDTO` es un `dataclass` inmutable cuyos
últimos campos (`efectos`, `extras`) ya tienen valor por defecto. Un campo nuevo sin valor por
defecto tendría que ir antes que ellos y rompería los constructores posicionales que ya existen
(por ejemplo, `Logic/BenchLogica.py`). Además, los guardianes, errantes y rastreadores no traen
`rango`. Por eso el campo es `int | None = None`, y «sin valor por defecto» (FR-122) se cumple en
Data: a un cazador no se le inventa un `rango`.

## Validación (FR-122) — en Data, integrante 2

| Dato | Inválido si | Contexto mínimo del mensaje |
|---|---|---|
| `costo` de una salida | no es entero (incluido `bool`), o es menor que 1 | sala, dirección, valor recibido |
| `costo` de los dos lados de una salida | los dos lo declaran y son distintos (se comprueba con el esqueleto completo) | las dos salas, las dos direcciones, los dos valores |
| `rango` de una ficha con `comportamiento == "cazador"` | falta, es `null`, no es entero (incluido `bool`) o es negativo | id de la ficha, campo (`rango`), valor recibido |
| `cierre_automatico` de una salida (`SalidaDTO`), si viene | no es entero (incluido `bool`), o es menor que 1 | sala, dirección, campo (`cierre_automatico`), valor recibido |
| `duracion` de la ficha de un objeto (`ObjetoDTO`), si la trae | no es entero (incluido `bool`), o es menor que 1 | id de la ficha, campo (`duracion`), valor recibido |

Las dos últimas filas las pidió el integrante 2 (T055, escenarios H2-20 y H2-21): los dos campos
programan eventos en la agenda, y la feature 004 supone que ningún efecto se programa con retraso 0.
`null` o ausente sigue siendo válido en los dos, como en P1. La `duracion` de `EfectoFichaDTO` queda
**fuera**: P1 ya convierte las duraciones ≤ 0 en `None`, así que no programa eventos con retraso 0, y
ese comportamiento no cambia.

Efecto: un error de datos con contexto, que se pueda distinguir de un error de red (hoy
`FuenteDatos` usa `ErrorRed` para los dos; ver T052). El mensaje sigue el mismo formato en todos
los casos: sala y dirección si el dato es del esqueleto, o id de la ficha y campo si es de una
ficha, más el valor recibido. El programa no se cae en ningún caso. Según de dónde venga el dato:

- **Esqueleto** (costos y `cierre_automatico`): la partida no inicia, tampoco con `--forzar`
  (003 FR-323).
- **Ficha de la sala inicial** (cazador con `rango` inválido u objeto con `duracion` inválida): se
  rechaza la ficha y la partida no inicia.
- **Ficha de cualquier otra sala**, llegue antes o durante la partida: no se vuelve a pedir (Data
  recuerda el rechazo por sala) y solo esa sala queda como contenido no disponible; un cazador de
  esa sala no se activa (FR-123). Si el jugador intenta entrar, el movimiento se rechaza con ese mensaje, sin
  consumir tiempo ni registrarse en `partida.log`, y la partida sigue. Mostrar el mensaje es de
  Service (integrante 3, T053). No cambian el formato de `partida.log` ni el replay.

Lógica no repite la validación: si dos lados declaran costos distintos, supone que Data ya lo
rechazó.

## Hacia la vista (integrante 3)

`Service/ArmadorEstado.py` copia el `SalidaDTO` del esqueleto y hoy solo reemplaza `cerrada` con
el estado vivo. Como el esqueleto trae el costo **declarado** (puede ser `None` en un lado), debe
reemplazar también `costo` con el costo igualado de Lógica (`SalidaViva.costo`). Es un cambio de
una palabra en un archivo del integrante 3 (FR-116).

## Compatibilidad

- Sin `costo`, una salida vale 100 y el juego se comporta como en P1. Los replays de P1 siguen
  dando la misma partida.
- `SalidaDTO.a_diccionario()` escribe `costo` solo si no es `None`, y
  `FichaEnemigoDTO.a_diccionario()` escribe `rango` solo si no es `None`. Así, las cachés y los
  guardados en disco de P1 se leen igual.
