# Contrato de datos de la feature 001

> **Propuesto — pendiente de confirmar con integrante 2** (y con el integrante 3 en la parte de
> `ActorDTO` y `ArmadorEstado`).
> Fecha límite acordada en el plan de trabajo: 9 de noviembre.
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
| `ActorDTO` | `comportamiento` | `str \| None` | `None` (jugador) | Por acordar con el integrante 3 | FR-117 |

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
| `rango` de una ficha con `comportamiento == "cazador"` | falta, es `null`, no es entero (incluido `bool`) o es negativo | id de la ficha, valor recibido |

Efecto: un error de formato con contexto (como los `ErrorRed` de formato que ya existen). La
partida no inicia y el programa no se cae. Lógica no repite la validación: si dos lados declaran
costos distintos, supone que Data ya lo rechazó.

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
