# Guía de validación: Terreno y cazador

**Feature**: `001-terreno-cazador` · Detalle en [plan.md](plan.md), [data-model.md](data-model.md) y [contracts/](contracts/)

## Requisitos previos

- Python 3.11 o superior, con las dependencias del proyecto (`uv sync`, o `pip install -r requirements.txt`).
- `SalidaDTO.costo` y `FichaEnemigoDTO.rango` incorporados según [contrato-datos.md](contracts/contrato-datos.md).

## 1. Todas las pruebas

```bash
python tests/correr_pruebas.py        # o: uv run python tests/correr_pruebas.py
```

Esperado: todo en verde, incluidas las pruebas nuevas de esta feature. Cada una cita su FR en el
nombre o en el docstring.

## 2. Los 7 casos del Apéndice B

```bash
python -m unittest tests.test_terreno_cazador -v
```

Esperado: un caso por fila de la tabla de trazabilidad de [spec.md](spec.md):

| Caso | Se comprueba |
|---|---|
| 1 | Sin ruta abierta: el cazador espera y su siguiente acción queda a 100 unidades (escalada por velocidad). |
| 2 | d = 700 > `rango` 600: espera con costo 100. |
| 3 | La ruta 1–2–3–4 (300) gana a 1–4 (500): va a la sala 2 y paga 100. |
| 4 | Empate entre las salas 7 y 4: va a la 4. |
| 5 | Se cierra 2–4 tras el primer paso: vuelve a la sala 1, y la decisión coincide con `paso_desde_cero`. |
| 6 | Velocidad 300 por una salida de costo 1: el intervalo es 1. |
| 7 | Velocidad 100 → 200 en t = 100 durante una salida de costo 400: la siguiente acción pasa a t = 250. |

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

Esperado: en la tabla aparecen los subsistemas `rutas del cazador`, `invalidación de rutas` y
`ciclo de eventos` con cazadores. La nota del ciclo dice «cumple» (< 20 ms) con decenas de
cazadores. Con `rango` fijo, la decisión de un cazador tarda aproximadamente lo mismo en
cuadrículas de 100, 1 000 y 10 000 salas.

## 6. Prueba manual en el juego

Hace falta una cripta con costos y un cazador:

```bash
python main.py --offline
```

Entrar a una sala con salidas de costos distintos y ver el costo de cada salida y al cazador
marcado. La interfaz es del integrante 3. Si todavía no está, esta parte queda pendiente.

## 7. Revisión de restricciones (Principio II)

```bash
grep -rnE "heapq|bisect|collections|import copy|networkx|\bdict\(|\bset\(" Logic Estructuras DTO
```

Esperado: ninguna coincidencia nueva en el código de esta feature.
