# Guía rápida de validación: Mapa conocido, memoria de puertas y antorcha

**Feature**: `002-niebla-ir-a` (parte del integrante 2) · **Plan**: [plan.md](plan.md)

Cómo comprobar de punta a punta que el mapa conocido funciona. Las estructuras están en
[data-model.md](data-model.md); lo que se ofrece al integrante 3, en
[contrato-mapa-conocido.md](contracts/contrato-mapa-conocido.md). La validación de «ir a» la agrega el integrante 3 en
su sección del plan.

## Requisitos previos

- Python 3.11 o superior con las dependencias del proyecto (`uv sync`), desde la raíz del repositorio.
- El cambio de `Logic/motorJuego.py` y de `Logic/PartidaGuardada.py` (tabla de cambios del plan; T033 y T040) ya
  integrado: lo escribe el integrante 2 y lo revisa el integrante 1 antes del merge (acuerdo del 14/11). Sin él, el
  motor no crea `motor.mapa`.
- Para H4-4 (`historia`): `Service/ArmadorResumen.py` (T023 de la 004). Mientras no exista, esa prueba queda en `skip`
  con su motivo.

## 1. Pruebas automatizadas

```powershell
uv run python -m unittest tests.test_mapa_conocido_estados tests.test_mapa_conocido_puertas -v
uv run python -m unittest tests.test_mapa_conocido_antorcha tests.test_mapa_conocido_partida -v
uv run python -m unittest tests.test_mapa_conocido_vista tests.test_grafo_mapa_conocido -v
uv run python -m unittest tests.test_guardado_mapa tests.test_bench_mapa -v
$env:PYTHONIOENCODING = "utf-8"; uv run python tests/correr_pruebas.py
```

Resultado esperado: todo en verde. Cada nombre de prueba cita su escenario y su FR; los tres casos del Apéndice B de
esta parte se reconocen por `apendiceB_caso2a`, `apendiceB_caso4` y `apendiceB_caso5` (SC-201). Las pruebas que ya
existían (`tests/TestGuardadoBinario.py`, `tests/TestPartidaGuardadaDTO.py`, `tests/test_partida_guardada.py`,
`tests/test_terreno_cazador.py`, `tests/test_rutas_equivalencia.py`) siguen en verde.

## 2. Comprobaciones manuales en el juego

```powershell
uv run python main.py --offline
```

| Paso | Qué hacer | Qué se espera | Requisitos |
|---|---|---|---|
| 1 | Empezar una partida y abrir el mapa conocido (comando del integrante 3) | Solo la sala inicial con nombre, salidas, costos y puertas; sus vecinas como «sala sin explorar»; nada más | FR-201, FR-202, FR-219 |
| 2 | Moverse a una vecina y volver a abrir el mapa | La vecina aparece explorada; sus destinos, como «sala sin explorar» | FR-203 |
| 3 | Abrir una puerta con cierre automático, alejarse dos salas y esperar a que se cierre; abrir el mapa | La puerta sigue figurando abierta | FR-208 |
| 4 | Volver a una de las dos salas de esa puerta | El mapa la muestra cerrada | FR-207, FR-209 |
| 5 | Encender la antorcha y entrar a una sala | Sus vecinas quedan exploradas, sin contenido; sus puertas nunca vistas figuran «sin observar»; el reloj avanza lo mismo que sin antorcha | FR-210 a FR-213 |
| 6 | Leer un pergamino | El mapa vuelve a como estaba antes de esa entrada | FR-222 |
| 7 | Guardar, salir y cargar | El mapa es idéntico | FR-221 |
| 8 | Consultar `historia #k` de una acción anterior | El resumen muestra el mapa de ese momento | FR-223 |

Abrir el mapa no cambia el reloj, no agrega nada a `partida.log` y no cambia lo que deshace el pergamino (FR-220).

## 3. Determinismo con `--replay`

```powershell
uv run python main.py --replay logs/partida_001.log --offline
uv run python main.py --replay logs/partida_001.log --hasta 300 --offline
```

El mapa final (y el del resumen en t = 300) es igual al de la partida original, también si el log trae comentarios
`# ir a …` (FR-224, T071 de la 004). La prueba automática equivalente es la de H4-5 en
`tests/test_mapa_conocido_partida.py`.

## 4. Archivo de partida

- Guardar una partida y comprobar con `tests/test_guardado_mapa.py` que el archivo es de la versión 2 y que
  `cargar_sala` devuelve una sala sin leer el bloque del mapa.
- Cargar un archivo de la primera parte (versión 1): se rechaza con la versión leída y la esperada, sin cargar nada
  (FR-421 de la 004).

## 5. `--bench`

```powershell
uv run python main.py --bench | Out-File -Encoding utf8 bench.txt
```

En la tabla, el subsistema «mapa conocido» trae las filas B1 a B11 ([research.md, R7](research.md)). Qué mirar:

| Fila | Criterio | Requisito |
|---|---|---|
| B1, B2 | Tiempo por consulta con 10 000 salas menor que el doble que con 100 | SC-203 |
| B3 | La alternativa con lista crece con el tamaño | Principio VIII |
| B4 | Entrada con antorcha con el mapa mayor, menos del doble que con el menor | SC-204 |
| B6 | Registrar e invertir con el pergamino, menos del doble entre el mapa menor y el mayor | SC-207 |
| B5, B7 | Las alternativas descartadas crecen con el tamaño | Principio VIII |
| B8 | La nota dice «cumple»: peor ciclo < 20 ms con 30 cazadores y la antorcha encendida | NFR-205, SC-206 |
| B9, B10 | Crecen en forma lineal con S | NFR-203, R5 |
| B11 | Armar el grafo más un paso con 1 024 salas: la nota dice si queda por debajo de 5 ms (lo que se lee, sin suponerlo antes) | R5 (a); referencia para NFR-250 |

Los números y la decisión final van a `DECISIONES.md`, sección del integrante 2, «Mapa conocido» (NFR-204).

## 6. «ir a» y `mapa` a mano en la ventana (integrante 3, T126)

Pasos para seguir en la ventana. Los textos entre comillas son los que muestra el programa. Los números de vida, daño y bytes
cambian de una partida a otra porque la semilla se sortea; el reloj de los pasos, no: cada salida de la cripta tiene su costo.

```powershell
uv run python main.py --offline
```

Se usa la cripta **«Catacumbas menores - 20 salas»** (`cripta-02`, paquete de la Parte II, que ya trae `llaves.json`: es resoluble y
no hace falta `--forzar`). Las salas se llaman «Sala 1», «Sala 2», … y de la 1 a la 8 forman un pasillo hacia el norte (`W`). La
Sala 1 tiene una antorcha en el suelo, la Sala 7 una rata gigante y la Sala 8 un pergamino de retroceso. El costo de cada paso, en
reloj, es el de la salida: 1↔2 cuesta 60, 2↔3 100, 3↔4 150, 4↔5 100, 5↔6 80, 6↔7 250 y 7↔8 100. De la Sala 1 a la 6 hay 490 de
reloj, y de la 6 a la 1, 490 también (80 + 100 + 150 + 100 + 60). Recoger un objeto cuesta 25 y usarlo 50.

| Paso | Qué hacer | Qué se espera | Requisitos |
|---|---|---|---|
| 1 | En el menú: `Enter` (Comenzar juego), flecha abajo y `Enter` (Catacumbas menores), escribe un nombre y `Enter` | Un panel «Verificación de resolubilidad» con «Cripta cripta-02 (versión …): RESOLUBLE» y «Orden de obtención de llaves: itm_llave_bronce, itm_llave_negra» y, arriba a la derecha, «Se oculta con tu primera acción». No es rojo ni dice «Advertencia». Reloj 0 y, en el panel de mensajes, «Comienzas en Sala 1» | 003 FR-313 |
| 2 | Pulsa `W` cinco veces | El panel del reporte desaparece con la primera `W`. Entras a las salas 2 a 6 («Entras a Sala 2», …, con los relojes 60, 160, 310, 410 y 490) y el reloj marca 490 | 003 FR-313 |
| 3 | `Enter`, escribe `mapa`, `Enter` | Un panel «Mapa conocido: 6 salas exploradas» con las salas 1 a 6 en fila, la tuya en dorado y «Estás en: Sala 6», una celda hueca al norte de la 6 (la Sala 7, «sala sin explorar»: sin nombre ni número) unida con una línea verde (puerta abierta) y otra celda hueca al este de la Sala 5 unida con una línea roja (la puerta cerrada hacia otra sala). El reloj sigue en 490 y no se agrega nada al log | FR-219, FR-220 |
| 4 | Cierra el mapa con `Esc` (o escribe `mapa` otra vez, o haz cualquier acción) | El panel se cierra y **no** se abre la pausa; el juego sigue igual | FR-219 |
| 5 | `Enter`, `ir a Sala 1`, `Enter` | La orden no mueve nada por sí sola (reloj 490). Luego, cada 0.35 s, cambias de sala: 5, 4, 3, 2, 1, con el reloj en 570, 670, 820, 920 y 980. Al final, en el panel de mensajes, «Llegaste a Sala 1.» | FR-250, FR-254, FR-258, FR-260 |
| 6 | Estando en la Sala 1, prueba cuatro órdenes: `ir a Sala 20`, `ir a Sala 7`, `ir a Sala 1` e `ir a` | Aviso rojo: «No conoces ninguna sala explorada con ese nombre.» (la misma para la 20, que no conoces, y la 7, que solo viste desde la 6), «Ya estás en esa sala.» y «Uso: ir a <sala> (una sala que ya hayas explorado).». El reloj sigue en 980 y el aviso se borra con la tecla siguiente | FR-251, FR-260 |
| 7 | `ir a Sala 6` y, cuando ya hayas cambiado de sala una o dos veces, pulsa `Tab` | El viaje se corta donde estés (por ejemplo, en la Sala 3, reloj 1140), aparece «Viaje interrumpido.» en el panel de mensajes y ya no te mueves aunque esperes. `Tab` hizo lo suyo (recorrer el inventario) | FR-262 (corte; la tecla es un supuesto, `DECISIONES.md`) |
| 8 | Haz otro `ir a Sala 1` y pulsa `Esc` a mitad | Se corta con «Viaje interrumpido.» y **no** se abre la pausa. Un segundo `Esc` sí la abre (y otro la cierra) | supuesto (`DECISIONES.md`) |
| 9 | Ve a la Sala 1 (`ir a Sala 1`), haz clic sobre la antorcha del suelo (al pasar el ratón se lee su nombre) y pulsa `U` | «Recoges Antorcha» (el reloj sube 25) y «Usas Antorcha» (sube 50), y la antorcha en el panel de efectos | 002 FR-210 |
| 10 | `W` cinco veces hasta la Sala 6 (490 de reloj), luego `mapa` | «Mapa conocido: 8 salas exploradas»: las 1 a 6, la Sala 7 (la antorcha la exploró sin despertar a la rata) y la Sala 19, que está tras la puerta cerrada de la Sala 5 (la antorcha explora a través de puertas cerradas), sin contenido. Quedan dos celdas huecas, al norte de la 7 y al norte de la 19, unidas con una línea gris (puerta sin observar) | FR-210, FR-211, FR-219 |
| 11 | `ir a Sala 7` | Das un solo paso (cuesta 250 de reloj) y el viaje para con tres mensajes juntos: «Llegaste a Sala 7.», «Viaje detenido: hay enemigos.» y «Viaje detenido: recibiste daño.», precedidos por «Rata gigante #1 ataca a Jugador: N de daño», que aparece dos veces durante ese paso. La vida baja unos 5 puntos | FR-258, FR-260 |
| 12 | Mata a la rata con `Espacio` hasta ver «Rata gigante #1 muere» (suele bastar un golpe), pulsa `W` a la Sala 8 y haz clic sobre el pergamino del suelo | «Entras a Sala 8» (el paso cuesta 100) y «Recoges Pergamino de retroceso» | |
| 13 | `ir a Sala 1` desde la Sala 8, espera a que haya dado dos pasos (ya estás en la Sala 6: pasaste por la 7) y pulsa `Retroceso` | Aparecen «Viaje interrumpido.» y «Lees el pergamino: el tiempo retrocede». Vuelves a la Sala 7 (solo se revirtió el último paso, el de la 7 a la 6; el reloj baja 250), el viaje **no** continúa y el pergamino se gasta | FR-222, FR-262 |
| 14 | `ir a Sala 1` hasta llegar, abre el `mapa` y anota las salas; `Ctrl + S` | Aviso «Partida guardada (N bytes).». El mapa muestra 10 salas (las 1 a 9 y la 19) y tres celdas huecas (al norte y al este de la 9 y al norte de la 19) | FR-221 |
| 15 | Da dos pasos a mano (`W`, `W`) y pulsa `Ctrl + L` | Aviso «Partida cargada.» y mensaje «Partida cargada: estás en Sala 1». El reloj y la sala vuelven a los del guardado (los dos pasos suman 160 de reloj) y el `mapa` muestra las mismas 10 salas | FR-221 |
| 16 | `ir a Sala 6` | Funciona igual que antes de cargar: un paso cada 0.35 s (relojes +60, +160, +310, +410 y +490 sobre el de la carga) hasta «Llegaste a Sala 6.» (el viaje usa el mapa de la partida cargada) | 002 plan, D-4 |
| 17 | Sal al menú (`Esc`, «Salir al menú») o cierra la ventana. En PowerShell: `uv run python main.py --replay logs/partida_002.log --offline` (el número es el del log más reciente: tras cargar, la partida sigue en un archivo nuevo que incluye las acciones anteriores) | Una línea por acción (`mover`, `atacar`, `recoger`, `retroceder`, …) con su `t=` y la sala, y al final «Acciones reproducidas: K» y «Resultado: la partida no terminó (reloj R)», con R igual al reloj que tenía la partida al salir | FR-261, SC-253 |
| 18 | Busca los comentarios: `Select-String "# ir a" logs/partida_00*.log` | `# ir a Sala 1`, `# ir a Sala 6`, … una vez por orden, justo después de su primer paso. En el log que empieza al cargar solo está el de las órdenes dadas desde entonces (aquí, `# ir a Sala 6`; los anteriores quedan en el log anterior). `--replay` los ignora y repite los pasos | FR-261 |

Con esto el viaje se comprueba parado por **llegada**, **enemigos** y **daño** (paso 11), cortado por una **tecla**, por **Esc** y por un
**pergamino**, y rechazado por destino inválido o por estar ya allí. La parada por **«sin ruta conocida»** (una puerta de la ruta que se
cierra a escondidas y no hay otra) no tiene un recorrido corto en esta cripta; la cubren `test_h7_2_apendiceB_caso2b_fr256_fr259_fr260_sin_ruta_se_detiene_en_b_sin_tiempo`
y `test_sin_ruta_conocida_el_viaje_se_detiene_y_lo_dice`. Los pasos 1 a 18 se ensayaron con el controlador y la vista reales sin ventana
(`tests/test_ir_a_interfaz.py` y un guion con la cripta-02 del paquete de la Parte II, sin `--forzar`); lo que sí hay que mirar a mano
es cómo se ve y el ritmo del paso 5.
