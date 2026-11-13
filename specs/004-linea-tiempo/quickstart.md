# Guía de validación: Línea de tiempo

**Feature**: `004-linea-tiempo` · **Plan**: [plan.md](plan.md) · **Contrato**: [contracts/contrato-linea-tiempo.md](contracts/contrato-linea-tiempo.md)

Cómo comprobar de punta a punta que la feature funciona, una vez implementada. Cada paso cita los
escenarios de la [spec](spec.md). No hay código aquí; los comandos son los de la interfaz.

## Requisitos previos

- Python 3.11 o superior y las dependencias del proyecto instaladas.
- Una cripta disponible en modo sin red: `python main.py --offline`.
- Todo el conjunto de pruebas existente en verde: `python tests/correr_pruebas.py`.

## 1. Consultar sin alterar la partida (Historia 1)

1. Iniciar una partida y hacer unas 6 acciones.
2. Escribir `historia #4`: el resumen muestra la sala, la vida, el inventario, los efectos activos,
   los enemigos de esa sala con su vida y, si existe, el mapa conocido. **No** muestra el cursor del
   inventario ni mensajes (H1-4, H1-10).
3. Escribir `historia 800` con el reloj en 500: se rechaza con el límite (H1-1). Escribir
   `historia #9` y `historia #0`: se rechazan con el rango (H1-5).
4. Repetir una consulta: el resumen es idéntico (H1-8).
5. Comprobar que el reloj no cambió, que `partida.log` no ganó ninguna línea y que el retroceso sigue
   con las mismas acciones (H1-3, FR-407, FR-408).
6. Con una decisión del jugador en el instante pedido, comprobar que `historia <t>` coincide con
   `historia #k` (H1-9).

## 2. Consultar sin ventana (Historia 2)

```text
python main.py --offline --replay logs/partida.log --hasta 300
python main.py --offline --replay logs/partida.log --hasta 1500
python main.py --offline --replay logs/partida.log
```

- Con T dentro de la partida imprime el mismo resumen que `historia T` (H2-1).
- Con T posterior al final, imprime el estado final e indica que la partida terminó antes (H2-2).
- Sin `--hasta` reproduce la partida completa (H2-6).
- `--hasta` sin valor, con `abc` o `-3`, o sin `--replay`: error de uso y código de salida 2 (H2-3).
- Un log que no existe: error con contexto y código de salida 1 (H2-4).
- Ninguno de estos modos abre una ventana.

## 3. Pergamino (Historia 3)

1. Hacer 5 acciones, leer un pergamino (revierte la 5) y consultar `historia #5`: se rechaza (H3-1).
2. Hacer una acción nueva y consultar `historia #5`: describe el estado justo antes de esa acción (H3-2).
3. Entrar a una sala nueva, revertirla con un pergamino, entrar a otra sala nueva y comprobar que los
   números de los enemigos son los mismos que vio la partida viva (hallazgo H-1).
4. (H3-5) Recoger un pergamino en la acción 4 y usar otro para revertir esa acción: `historia` del instante
   actual conserva el pergamino recogido y no tiene el consumido, igual que el inventario vivo.
5. (H3-6) Soltar un pergamino en la acción 4, usar otro para revertirla y recoger después el que sigue en
   el suelo de la sala: `historia` del instante actual y de los instantes posteriores coincide con la
   partida viva; el pergamino soltado quedó fuera de la reversión, en el inventario y en el suelo.

## 4. Guardar y cargar (Historia 4)

1. Con 20 acciones, hacer varias consultas, guardar, cargar y repetirlas: mismos resúmenes (H4-1, H4-2).
2. Intentar cargar un archivo de la primera parte: se reporta incompatible, la partida actual no
   cambia (H4-3).

## 5. Puntos de control (Historia 5)

- Jugar la misma partida con `--checkpoint-cada 1`, `5` y `50`: las mismas consultas dan resúmenes
  idénticos (H5-1).
- `--checkpoint-cada 0`, `-2` o `abc`: error y no se inicia (H5-3).

## 6. Mediciones

```text
python main.py --bench
```

Debe incluir el grupo de la línea de tiempo (M1 a M6 del plan): tiempo de `historia` y memoria para
al menos tres valores de K y para la alternativa sin puntos de control, el costo de una copia y el
costo de ubicar el punto de control. Con 5 000 acciones del jugador y el K por defecto, `historia`
tarda menos de 50 ms (SC-405). Los resultados y el valor final de K se anotan en `DECISIONES.md`.

## Criterio de salida

- Los 6 casos del Apéndice B pasan como pruebas automatizadas que citan su FR (SC-401).
- El 100 % de las consultas coincide con el estado vivo en una partida de 200 o más acciones (SC-402).
- Tras cualquier secuencia de consultas, reloj, `partida.log` y retroceso son idénticos a los de una
  partida sin consultas (SC-403).
