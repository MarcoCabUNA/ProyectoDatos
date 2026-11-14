# Guía de validación: Terreno y cazador

**Feature**: `001-terreno-cazador` · Detalle en [plan.md](plan.md), [data-model.md](data-model.md) y [contracts/](contracts/)

## Requisitos previos

- Python 3.11 o superior, con las dependencias del proyecto (`uv sync`, o `pip install -r requirements.txt`).
- `SalidaDTO.costo` (el costo declarado, `int | None`) y `FichaEnemigoDTO.rango` incorporados según
  [contrato-datos.md](contracts/contrato-datos.md).

## 1. Todas las pruebas

```bash
python tests/correr_pruebas.py        # o: uv run python tests/correr_pruebas.py
```

Esperado: todo en verde, incluidas las pruebas nuevas de esta feature. Cada una cita su FR en el
nombre o en el docstring.

## 2. Los 7 casos del Apéndice B

```bash
python -m unittest tests.test_terreno_cazador tests.test_rutas_equivalencia -v
```

Los casos 1, 2, 3, 4, 6 y 7 están en `test_terreno_cazador`, y el caso 5 en `test_rutas_equivalencia`
(escenario H3-1). Esperado: un caso por fila de la tabla de trazabilidad de [spec.md](spec.md):

| Caso | Se comprueba |
|---|---|
| 1 | Sin ruta abierta: el cazador espera y su siguiente acción queda a 100 unidades (escalada por velocidad). |
| 2 | d = 700 > `rango` 600: espera con costo 100. |
| 3 | La ruta 1–2–3–4 (300) gana a 1–4 (500): va a la sala 2 y paga 100. |
| 4 | Empate entre las salas 7 y 4: va a la 4. |
| 5 | Se cierra 2–4 tras el primer paso: vuelve a la sala 1, y la decisión coincide con `paso_desde_cero`. |
| 6 | Velocidad 300 por una salida de costo 1: el intervalo es 1. |
| 7 | Velocidad 100 → 200 en t = 100 durante una salida de costo 400: la siguiente acción pasa a t = 250. |

### Datos inválidos (FR-122, escenario H2-9)

```bash
python -m unittest tests.test_terreno_cazador.TestDatosInvalidos -v
```

Esperado: con una ficha de cazador sin `rango` en una sala que no es la inicial, intentar entrar a esa
sala se rechaza con un mensaje que nombra la ficha y el campo, el reloj no avanza, ese movimiento no
queda en `partida.log` y la partida sigue. Mientras T052 (integrante 2) y T053 (integrante 3) no
estén hechas, la prueba aparece como omitida (`skip`).

## 3. Equivalencia con un cálculo desde cero (FR-114, SC-102)

```bash
python -m unittest tests.test_rutas_equivalencia -v
```

Esperado: en partidas sintéticas con puertas que se abren y cierran, movimientos del jugador y
pergaminos, **cada** decisión de **cada** cazador es igual a la de `paso_desde_cero`.

## 4. Determinismo (SC-103)

Se juega dos veces la misma secuencia con la misma semilla y se comparan las bitácoras: deben
ser idénticas. Si en esa partida ningún cazador ataca, agregar cazadores no cambia lo que eligen
los errantes.

## 5. Bench, sin vista (Principio V, §6.3)

```bash
python -m Service.ServicioBench
```

Esperado: en la tabla aparecen los subsistemas `rutas del cazador`, `invalidación de rutas`,
`ciclo de eventos` con cazadores y `agenda de eventos` con costos variables.

- **NFR-101, SC-104**: en la cuadrícula de 1 000 salas con 30 cazadores, la nota del ciclo dice
  «cumple» (< 20 ms).
- **SC-105**: con `rango` 200, la decisión de un cazador tarda como mucho el doble al pasar de 100 a
  1 000 salas, y otra vez como mucho el doble al pasar de 1 000 a 10 000.

## 6. Modos sin vista (FR-118)

```bash
python tests/test_modos_sin_vista_terreno.py
```

Esperado: una línea `OK: ...` al final. Con una cripta de prueba con costos y un cazador, `--replay`
reproduce los mismos estados sin instanciar la vista. Hoy solo se cubre `--replay`: `--replay … --hasta`
(spec 004) y `--verificar` (spec 003) todavía no existen; el script lo avisa con una línea `PENDIENTE`, y
sus pruebas se agregan cuando lleguen esas specs (T048 sigue abierta, y H3-7 con `skip`).

## 7. Prueba manual en el juego

Hace falta una cripta con costos y un cazador:

```bash
python main.py --offline
```

Entrar a una sala con salidas de costos distintos y ver el costo de cada salida y al cazador
marcado. La interfaz es del integrante 3 (tareas T038, T039 y T041). Si todavía no está, esta parte
queda pendiente. Hoy ninguna cripta de `paquete/` trae costos ni cazadores.

## 8. Revisión de restricciones (Principios I y II)

```bash
grep -rnE "heapq|bisect|collections|import copy|networkx|\bdict\(|\bset\(|sorted\(|\.sort\(" Logic Estructuras DTO
grep -rnE "^(from|import) (Data|Service)" Logic Estructuras
```

Esperado: ninguna coincidencia nueva en el código de esta feature.
