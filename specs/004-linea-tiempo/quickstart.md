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
2. Escribir `historia #4`: el resumen muestra la sala, la vida y las estadísticas, el inventario, el arma y la
   armadura, los efectos activos y los enemigos de esa sala con su vida. **No** muestra el cursor del
   inventario ni mensajes (H1-4, H1-10). El `ResumenHistoriaDTO` lleva además el mapa conocido de ese
   momento (spec 002, FR-223; `tests/test_historia_con_mapa.py`) y el panel de la ventana lo dibuja en el panel central,
   con el título «Mapa conocido: N salas exploradas» y «Historia: el mapa de ese instante» (`tests/test_historia_mapa_vista.py`);
   la salida de `--hasta` imprime una línea con el mismo recuento. Para ver el mapa actual se usa el comando `mapa`.
3. Escribir `historia 800` con el reloj en 500: se rechaza con el límite (H1-1): «El instante 800 es posterior al
   reloj actual: debe estar entre 0 y 500». Escribir `historia #9`: se rechaza con el rango (H1-5): «La acción 9 no
   existe: debe estar entre 1 y 5». `historia #0`, `historia`, `historia abc` y `historia -3` ni siquiera llegan al
   backend: la interfaz responde «Uso: historia <t> (instante, entero >= 0) o historia #k (acción, entero >= 1).».
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
- Con T dentro de la partida imprime «Estado en t=T», la sala, el jugador, el inventario, el arma y la armadura,
  los efectos, los enemigos de la sala y una última línea «Mapa conocido: N salas exploradas» (o «1 sala explorada»;
  FR-223, `tests/test_main_hasta.py`).
- Con T posterior al final de una partida que **terminó** (el jugador murió o llegó a la salida), imprime el estado
  final y «La partida terminó antes de t=T: este es el estado final (reloj R).» (H2-2; la cubre
  `test_h2_2_apendiceB_caso5_fr412_t_posterior_al_final`, porque con un log a mano es difícil terminar la partida).
  Con una partida que **no** terminó, un T posterior al reloj es un error, no un estado final: «El instante 1500 es
  posterior al reloj actual: debe estar entre 0 y 700» y código de salida 1.
- Sin `--hasta` reproduce la partida completa: una línea por acción y, al final, «Acciones reproducidas: K» y «Resultado: ...» (H2-6).
- `--hasta` sin valor, con `abc` o `-3`, o sin `--replay`: error de uso y código de salida 2 (H2-3): «Error en las
  opciones: argument --hasta: debe ser un número entero mayor o igual a 0 (se recibió 'abc')» y «Error en las
  opciones: --hasta solo se puede usar junto con --replay».
- Un log que no existe: error con contexto y código de salida 1 (H2-4): «no existe el log 'nada.log'».
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
- `--checkpoint-cada 0`, `-2` o `abc`: error y no se inicia (H5-3), con código de salida 2: «Error en las opciones: argument
  --checkpoint-cada: debe ser mayor o igual a 1 (se recibió '0')».

## 6. Mediciones

```text
python main.py --bench
```

Debe incluir el grupo de la línea de tiempo (M1 a M6 del plan): tiempo de `historia` y memoria para
al menos tres valores de K y para la alternativa sin puntos de control, el costo de una copia y el
costo de ubicar el punto de control. Con 5 000 acciones del jugador y el K por defecto, `historia`
tarda menos de 50 ms (SC-405). Los resultados y el valor final de K se anotan en `DECISIONES.md`.

## 7. A mano en la ventana (integrante 3, T068)

Pasos para seguir en la ventana, con la cripta **«Catacumbas menores - 20 salas»** (`cripta-02`): de la Sala 1 a la 8
hay un pasillo hacia el norte (`W`); la Sala 7 tiene una rata gigante dormida y la Sala 8 un pergamino de retroceso. Cada
paso entre salas cuesta lo que dice su puerta (con el paquete de la Parte II ya no es siempre 100; el `Z` cuesta 100). Los textos entre comillas son los que muestra el programa; los números de
vida y estadísticas salen del personaje y pueden variar.

```powershell
uv run python main.py --offline
```

No hace falta `--forzar`: el paquete de la Parte II ya trae `llaves.json` y la cripta es resoluble (003, FR-311). En el menú:
`Enter` (Comenzar juego), flecha abajo y `Enter` (Catacumbas menores), un nombre y `Enter`. Verás el panel «Verificación de
resolubilidad» con «… RESOLUBLE» (no es rojo ni dice «Advertencia»); se oculta con tu primera acción.

| Paso | Qué hacer | Qué se espera | Requisitos |
|---|---|---|---|
| 1 | Pulsa `W` cinco veces y `Z` una vez | Reloj 590 (los pasos cuestan 60, 100, 150, 100 y 80, y el `Z`, 100), estás en la Sala 6 (seis acciones) | |
| 2 | `Enter`, escribe `historia #4`, `Enter` | Un panel «Historia: reloj 310» y, en el panel central, el mapa de ese instante con «Mapa conocido: 4 salas exploradas» (las salas 1 a 4) y «Historia: el mapa de ese instante»; el panel de texto trae «Sala: Sala 4 (#4)», una línea «Vida … Ataque … Defensa … Velocidad …», «Inventario: (vacío)», «Arma: ninguna  Armadura: ninguna», «Efectos: ninguno» y «Enemigos: ninguno». El reloj del juego sigue en 590 y no hay mensajes ni cursor del inventario en el panel | H1-4, H1-10, FR-406 |
| 3 | Pulsa `Esc` | El panel se cierra y **no** se abre la pausa; el juego sigue igual | |
| 4 | `historia 310` | El mismo panel que el del paso 2 (mismas seis líneas): `historia <t>` y `historia #k` coinciden cuando t es el instante de esa acción | H1-9 |
| 5 | Repite `historia #4` dos veces | El resumen es idéntico las dos veces | H1-8 |
| 5b | Con `historia #4` abierto, compara su mapa con el actual: cierra con `Esc`, escribe `mapa` y mira el título | El mapa de `historia #4` dice «Mapa conocido: 4 salas exploradas» (las salas 1 a 4) y el comando `mapa` dice «Mapa conocido: 6 salas exploradas»: la historia temprana tiene **menos** salas que el mapa actual y no muestra la 5 ni la 6, que se conocieron después. Cierra el mapa con `Esc` | FR-223 |
| 6 | `historia 800`, `historia #9`, `historia #0`, `historia` y `historia abc` (uno por uno) | Un aviso rojo cada vez: «El instante 800 es posterior al reloj actual: debe estar entre 0 y 590», «La acción 9 no existe: debe estar entre 1 y 6» y, para las otras tres, «Uso: historia <t> (instante, entero >= 0) o historia #k (acción, entero >= 1).». Si había un panel abierto, sigue abierto | H1-1, H1-5 |
| 7 | Mira el reloj y cuenta las líneas de `logs/partida_NNN.log` (el archivo más reciente; `(Get-Content logs/partida_NNN.log).Count`) antes y después de los pasos 2 a 6 | Reloj y número de líneas no cambian: consultar no es una acción | H1-3, FR-407, FR-408 |
| 8 | Pulsa `W` con un panel de `historia` abierto | El panel se cierra y la acción se ejecuta (el reloj sube a 840, Sala 7). Despierta o no a la rata: si te ataca, sigue al paso 9 igual | FR-406 |
| 9 | Mata a la rata con `Espacio` hasta ver «Rata gigante #1 muere», pulsa `W` a la Sala 8 y haz clic sobre el pergamino del suelo | «Entras a Sala 8» y «Recoges Pergamino de retroceso» | |
| 10 | `historia #999` | Aviso «La acción 999 no existe: debe estar entre 1 y M». Anota M: son las acciones vigentes | H1-5 |
| 11 | Pulsa `Z` (acción M + 1) y luego `Retroceso` | «Lees el pergamino: el tiempo retrocede»; el reloj baja 100 y el pergamino se gasta | H3-1 |
| 12 | `historia #N`, con N = M + 1 | Aviso «La acción N no existe: debe estar entre 1 y M»: la acción revertida ya no existe | H3-1 |
| 13 | Pulsa `Z` de nuevo y repite `historia #N` | Un panel con el estado justo antes de la acción nueva: la Sala 8 y el reloj que tenías antes de esa `Z` | H3-2 |
| 14 | Con el panel de `historia #3` abierto, anota sus líneas, ciérralo, `Ctrl + S`, pulsa `Z` y `Ctrl + L` | Avisos «Partida guardada (N bytes).» y «Partida cargada.». Repite `historia #3` y `historia 200`: las mismas líneas que antes de guardar | H4-1, H4-2 |
| 15 | Sal al menú (`Esc`, «Salir al menú») y en PowerShell: `uv run python main.py --offline --replay logs/partida_NNN.log --hasta 310` (NNN: el número del log más reciente) | Se imprime «Estado en t=310», «Sala: Sala 4 (#4)» y las demás líneas con el mismo contenido que `historia 310` en la ventana (con «(ninguno)» y «(vacío)» entre paréntesis), y al final «Mapa conocido: 4 salas exploradas» y el código de salida es 0 (`$LASTEXITCODE`). No se abre ninguna ventana | H2-1 |
| 16 | Repite con `--hasta 99999`, `--hasta abc` y sin `--replay` (`uv run python main.py --offline --hasta 300`) | «El instante 99999 es posterior al reloj actual: debe estar entre 0 y R» con código 1 (la partida no terminó); «Error en las opciones: argument --hasta: debe ser un número entero mayor o igual a 0 (se recibió 'abc')» y «Error en las opciones: --hasta solo se puede usar junto con --replay», ambos con código 2 | H2-3, H2-2 |
| 17 | `uv run python main.py --offline --checkpoint-cada 1`, repite los pasos 1 y 2 (`historia #4`) y luego haz lo mismo con `--checkpoint-cada 50` | El mismo panel de `historia #4` con cualquier K | H5-1 |
| 18 | `uv run python main.py --offline --checkpoint-cada 0` (y con `-2` y `abc`) | «Error en las opciones: argument --checkpoint-cada: debe ser mayor o igual a 1 (se recibió '0')» (para `-2` y `abc`: «debe ser un número entero mayor o igual a 1 (se recibió …)»), código 2 y no se abre la ventana | H5-3 |

Lo que no se puede ver a mano en esta cripta tiene su prueba automática: la partida **terminada** antes de t (H2-2,
`test_h2_2_apendiceB_caso5_fr412_t_posterior_al_final`), el archivo de guardado de la primera parte (H4-3) y los
números de enemigos tras revertir una sala nueva (hallazgo H-1, paso 3 de la sección 3). Los pasos 1 a 14 se ensayaron
con el controlador y la vista reales sin ventana (cripta-02, sin `--forzar`) y los pasos 15 a 18 con `main.py`; lo que sí hay que mirar a
mano es cómo se ve el panel y que el juego se siente igual con las consultas.

## Criterio de salida

- Los 6 casos del Apéndice B pasan como pruebas automatizadas que citan su FR (SC-401).
- El 100 % de las consultas coincide con el estado vivo en una partida de 200 o más acciones (SC-402).
- Tras cualquier secuencia de consultas, reloj, `partida.log` y retroceso son idénticos a los de una
  partida sin consultas (SC-403).
