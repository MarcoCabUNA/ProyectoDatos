# Decisiones de diseño — Cripta, segunda parte

Este archivo reúne las decisiones de diseño de la segunda parte (Principio VIII de la constitución). Cada
decisión de estructura de datos indica el problema, las alternativas consideradas, la decisión, su
complejidad, la evidencia empírica (mediciones propias de `--bench`) y los límites conocidos, con enlaces a
la spec y al plan de donde proviene, e indica si la decisión final coincide con la del `plan.md` original.

**El «antes»**: las decisiones de la primera entrega están en
[docs/Documento_Decisiones.pdf](docs/Documento_Decisiones.pdf). Cuando una decisión de la segunda parte
cambia una de la primera (Principio III), se muestra el antes y el después: el antes se cita como
«Documento de Decisiones de la primera entrega, §x» y el después se escribe aquí.

Cada integrante escribe su sección.

---

## Integrante 1 — 001 terreno y cazador (§5.1, §5.2, §5.6)

Spec: [specs/001-terreno-cazador/spec.md](specs/001-terreno-cazador/spec.md) ·
Plan: [specs/001-terreno-cazador/plan.md](specs/001-terreno-cazador/plan.md) ·
Investigación: [specs/001-terreno-cazador/research.md](specs/001-terreno-cazador/research.md)

### §5.1 La ruta más barata del cazador

**Problema.** Cada cazador debe dar un paso por una ruta de costo mínimo hacia el jugador si ese
costo no pasa su `rango` (FR-106 a FR-111), con decenas de cazadores a la vez y sin que la decisión
cueste según el tamaño de la cripta (NFR-101, NFR-102). Detalle en [research.md](specs/001-terreno-cazador/research.md) R1 a R3.

**Antes (primera entrega).** No había búsqueda de rutas: los errantes y los rastreadores deciden mirando
solo sus g ≤ 4 vecinas (Documento de Decisiones de la primera entrega, §4.7), y moverse costaba siempre
100 (`Motor.COSTO_MOVER`; `turno_enemigo` programaba 100). El único recorrido de grafo era el BFS de la
precarga (§4.2), que cuenta salas y no costos.

**Después.**

- **Costo por salida** (FR-101 a FR-105): `SalidaViva.costo`, igual en los dos sentidos al cargar el
  esqueleto (`_igualar_costos`, junto a `_igualar_caras` y sin modificarlo). El jugador y los enemigos
  pagan el costo de la salida que cruzan; esperar y atacar siguen costando 100.
- **Cola de prioridad** (R1): montículo binario mínimo propio (`Estructuras/MonticuloMinimo.py`) con
  entradas repetidas y borrado perezoso. Alternativas: recorrer un array (O(S²)), generalizar
  `ColaEventos` (tocaría código de la primera entrega), índice de posiciones, cubetas por distancia.
- **Una búsqueda compartida desde el jugador** (R2): como el costo es el mismo en los dos sentidos,
  dist(cazador, jugador) = dist(jugador, cazador), y una sola búsqueda sirve a todos los cazadores. Es
  reanudable: cada cazador la extiende solo hasta resolver su sala o pasar su `rango`.
- **Corte en el `rango` y desempate** (R3): toda vecina que cumple costo + dist = d ya está resuelta, así
  que el paso se elige mirando solo las salidas del cazador (FR-111). Los arrays se reservan una vez y una
  búsqueda nueva solo cambia la generación: empezar cuesta O(1).

**Complejidad.** Una búsqueda: O((S_r + E_r) log E_r), con S_r y E_r las salas y salidas a costo ≤ r del
jugador. Cada decisión que reutiliza la búsqueda: O(g). Memoria: O(S) una sola vez, más la frontera.

**Evidencia.**

| Medición | Resultado |
|---|---|
| Montículo frente a array (esquina a esquina) | 100 salas: 0,48 frente a 0,62 ms; 1 024 salas: 4,2 frente a 31,6 ms (7,5 veces) |
| 1 / 10 / 30 / 100 cazadores, 20 ciclos | una búsqueda por cazador: 32 / 268 / 611 / 1 617 ms; compartida: 32 / 63 / 67 / 64 ms (hasta 25 veces menos) |
| `rango` 200, 100 → 1 024 → 10 000 salas | 19,6 → 32,9 → 35,9 µs por decisión: 1,68 y 1,09 veces, **SC-105 se cumple** |
| `rango` 5 000, las mismas cuadrículas | 0,23 → 3,2 → 19,8 ms: crece con la región dentro del `rango`, como se esperaba |
| Ciclo de eventos, 1 024 salas, 30 cazadores | peor ciclo de 7,9 ms (jugador quieto) y 5,4 ms (jugador moviéndose): **NFR-101 y SC-104 se cumplen** |

En todas las mediciones con cazadores, cada decisión se compara con `paso_desde_cero`, y son iguales
(escenario H3-8).

**Límites.** Con un solo cazador, la búsqueda compartida no ahorra nada (empata). Con `rango` grande en
una cripta grande, la búsqueda recorre casi toda la cripta (19,8 ms con 10 000 salas y `rango` 5 000).
Con 100 cazadores el peor ciclo llega a 18,0 ms: cumple, pero con poco margen.

**¿Coincide con el plan?** Sí. Lo que cambió fue la medición de R3: con el jugador siempre en el centro
de cada cuadrícula, la de 10 000 salas dio 2,78 veces. Se debía a que los costos alrededor del centro
eran distintos (12 salas resueltas en lugar de 4), no a la búsqueda. Ahora se promedian 400 posiciones
del jugador. El array de R1 no se mide con 10 000 salas (O(S²)). Las dos mediciones de cada cambio de
método, con su causa y su evidencia, están en [research.md](specs/001-terreno-cazador/research.md) R3 y R6.

Mediciones: `python -m Service.ServicioBench` (`Logic/BenchRutas.py`), tabla completa en [bench-2026-11-13.txt](specs/001-terreno-cazador/bench-2026-11-13.txt). Máquina: AMD Ryzen 5 3600X, 32 GB, Windows 11 Pro, Python 3.12.10. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la máquina.

### §5.2 Rutas que dejan de ser válidas

**Problema.** La búsqueda guardada deja de valer cuando cambia algo de lo que depende: la sala del
jugador o el estado de una puerta (FR-112, FR-120). Además, un pergamino puede devolver puertas y salas a
un estado anterior sin avisar. La decisión debe ser siempre la de un cálculo desde cero (FR-114). Detalle
en [research.md](specs/001-terreno-cazador/research.md) R4.

**Antes (primera entrega).** No había nada guardado que se pudiera invalidar. El historial de retroceso
registra una función inversa por cambio, agrupadas por intervalo (Documento de Decisiones de la primera
entrega, §4.6).

**Después.**

- Si el jugador cambió de sala, la siguiente consulta empieza una búsqueda nueva (se compara el origen).
- La `Mazmorra` avisa en los dos lugares donde cambia una puerta (`abrir_puerta` y `CierrePuerta.activar`)
  con los destinos de las caras. La búsqueda se descarta solo si alguno ya está resuelto: una salida u → v
  solo se lee al resolver v, así que si ninguno lo está, la salida se leerá después con su estado nuevo.
- Moverse, morir, cambiar de velocidad o cargar el contenido de una sala no invalidan nada.
- Pergamino: cada vez que la búsqueda se crea, se extiende o recibe un aviso, registra en el historial
  una función que la descarta. Deshacer un intervalo en el que no cambió nada de eso la conserva. No se
  copia nada.

**Alternativas.** A, recalcular siempre (k búsquedas por ciclo); B, descartar ante cualquier puerta;
C, el descarte preciso (elegida).

**Complejidad.** Cada aviso cuesta O(1). Cada registro en el historial cuesta O(1) y hay uno como mucho
por creación, extensión o aviso.

**Evidencia.** 30 cazadores en 1 024 salas, 60 ciclos; búsquedas por ciclo y tiempo por ciclo:

| Escenario | A, recalcular siempre | B, cualquier puerta | C, descarte preciso |
|---|---|---|---|
| Puertas estables | 21,8 · 15,8 ms | 0,20 · 0,55 ms | 0,20 · 0,64 ms |
| Una puerta al azar por ciclo | 20,6 · 14,1 ms | 0,98 · 2,23 ms | 0,67 · 1,60 ms |
| Al azar y una de la sala del jugador | 19,4 · 10,9 ms | 1,00 · 1,76 ms | 1,00 · 1,77 ms |

Las tres deciden lo mismo en cada turno. FR-114 tiene además su evidencia en pruebas: 12 partidas
aleatorias (`TestEquivalenciaAleatoria`, con puertas, cierres automáticos, muertes, velocidades y
pergaminos), unas 11 000 decisiones de cazador, todas iguales a `paso_desde_cero`, con la búsqueda
reutilizada en más del 90 % de ellas. Pruebas de mutación: sin los avisos de puerta fallan 6 o 7 de
las 12 partidas. Sin el descarte registrado para el pergamino, el error solo lo detecta la prueba fija
`test_pergamino_despues_de_abrir_una_puerta_sin_moverse`; en las partidas aleatorias lo detecta, a lo
sumo, 1 de 12.

**Límites.** Una puerta que toca la región resuelta (por ejemplo, una de la sala del jugador) descarta la
búsqueda igual que B. Un jugador que cambia de sala en cada decisión obliga a una búsqueda nueva por
decisión, pero sigue siendo una sola para todos los cazadores.

**¿Coincide con el plan?** Sí. La medición separa las puertas inestables en dos escenarios, porque con
una puerta junto al jugador en cada ciclo B y C empatan.

Mediciones: `python -m Service.ServicioBench` (`Logic/BenchRutas.py`), tabla completa en [bench-2026-11-13.txt](specs/001-terreno-cazador/bench-2026-11-13.txt). Máquina: AMD Ryzen 5 3600X, 32 GB, Windows 11 Pro, Python 3.12.10. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la máquina.

### §5.6 Revisión de decisiones de la primera parte

Las decisiones de la primera entrega que esta feature toca se volvieron a medir con la carga nueva
(Principio VIII; [research.md](specs/001-terreno-cazador/research.md) R6).

**Movimiento y turnos enemigos (cambia).**

- *Antes*: moverse costaba 100 fijo (`Motor.COSTO_MOVER`) y `turno_enemigo` programaba siempre la
  siguiente acción a 100 (P1 §2.3).
- *Después*: el jugador paga `salida.costo`, y `turno_enemigo` programa con el costo que devuelve
  `decidir_paso()` (el de la salida cruzada), o 100 si espera o ataca (FR-102 a FR-104). El errante sortea
  entre las salidas con su costo y hace la misma llamada a `randint` que antes (Principio IV). El
  rastreador paga la salida abierta más barata hacia la sala que elige.

**Agenda de eventos (no cambia).**

- *Antes* (Documento de Decisiones de la primera entrega, §4.1): montículo binario frente a array
  ordenado. Con 10 000 eventos, programar y sacar sumaban 6,36 µs frente a 781,92 µs (unas 120 veces
  menos), y el ciclo con 500 enemigos tenía su peor caso en 16,92 ms.
- *Después*: con tiempos de costos entre 1 y 300 y velocidades distintas, con 10 000 eventos el
  montículo programa en 0,81 µs y saca en 5,4 µs, y el array tarda 1 241 µs en programar: unas 200 veces
  menos. Los dos límites conocidos del montículo con invalidación perezosa, con 10 000 eventos:
  - *Mismo tiempo*: el montículo no cambia (0,69 µs para programar y 5,5 µs para sacar). El array
    empeora, a 1 821 µs por evento programado.
  - *Cancelaciones*: con el 50 % cancelado, sacar cuesta 10,2 µs por evento válido. Con el 90 %, cuesta
    60,6 µs y descarta 917 entradas por cada 100 válidas. En el juego no hay tantas cancelaciones juntas:
    salen de muertes, antídotos y cambios de velocidad.
- Con 30 cazadores en 1 024 salas, el peor ciclo es de 7,9 ms.

**Historial de retroceso (no cambia).**

- *Antes* (§4.6): una función inversa por cambio, unos 12 registros por intervalo en partidas reales.
- *Después*: la búsqueda del cazador registra su descarte. Con 30 cazadores agrega 0,02 registros por
  intervalo con el jugador quieto y 1,60 con el jugador moviéndose (sobre 249 y 106 de la partida
  sintética: menos del 1,5 %).

**¿Coincide con el plan?** Sí: el plan esperaba que el montículo siguiera siendo adecuado y que el
historial no cambiara.

**La fila de la primera entrega con 500 enemigos ya fallaba antes de esta feature.** `medir_ciclo`
con 500 errantes y rastreadores, sin cazadores ni costos. Se midió el 13 de noviembre en esta máquina,
en el último commit anterior a la 001 (`83d15c5`, en un `git worktree` aparte) y en la rama actual:

| Cómo se midió | Antes de la 001 (`83d15c5`) | Rama actual |
|---|---|---|
| Sola, 10 corridas alternadas | peor 11,7 a 16,2 ms; mediana 5,37 a 5,67 ms | peor 12,3 a 17,0 ms; mediana 5,37 a 5,68 ms |
| Dentro de `--bench` completo, 3 corridas | peor 17,4 / **20,7** / 16,5 ms | peor **24,3** / **25,0** / **24,0** ms |
| Con el mismo `BenchDatos` actual antes, 4 corridas | peor 18,7 / **21,3** / 17,3 / 17,1 ms | peor 16,8 / 17,8 / 19,6 / 16,9 ms |

En negrita, las que no cumplen. Los dos árboles procesan los mismos ~521 eventos por ciclo y hacen las
mismas 21 pasadas completas del recolector de basura de Python (generación 2) durante la medición.
Cada pasada recorre unos 103 000 objetos y tarda de 10 a 20 ms. El peor ciclo es un ciclo normal
(5 a 8 ms) más una de esas pasadas: con el recolector desactivado, el peor ciclo baja a 7 a 12 ms en
los dos árboles. Por eso la fila queda en el límite y a veces no cumple, con o sin la 001. Ya fallaba
antes: una de las tres corridas del `--bench` completo en `83d15c5` dio 20,7 ms. El Documento de la
primera entrega ya decía que el peor ciclo varía entre corridas (§4.1, límites: un pico de 119 ms).

En el `--bench` completo, la rama actual da un peor ciclo más alto (24 ms frente a 16 a 21 ms). Esa
diferencia no viene del código de la 001. Con lo mismo corriendo antes en el proceso (el `BenchDatos`
actual), el `Logic` de antes y el de ahora dan lo mismo (tercera fila). La diferencia aparece según lo
que corre antes en el mismo proceso, cuyo código (Servicios y Datos) también cambió desde `83d15c5`; no
se aisló qué parte. Queda para revisarla con el equipo; esta feature no cambia nada por eso.

Mediciones: `python -m Service.ServicioBench` (`Logic/BenchRutas.py`), tabla completa en [bench-2026-11-13.txt](specs/001-terreno-cazador/bench-2026-11-13.txt). Máquina: AMD Ryzen 5 3600X, 32 GB, Windows 11 Pro, Python 3.12.10. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la máquina.

### Diferencia conocida entre la verificación y el motor de P1

- **Qué pasa**: la verificación de resolubilidad (003 FR-304) sigue al pie de la letra §3.5 y P1 §2.12:
  la cripta es resoluble si el jugador puede obtener `llave_salida` y llegar a `sala_salida` a través de
  una puerta que requiere `llave_salida`. El motor de la primera parte es más permisivo:
  `Mazmorra.abrir_puerta` activa `salida_abierta` al abrir **cualquier** puerta que pida `llave_salida`,
  aunque esa puerta no dé a `sala_salida`, y después basta con entrar a `sala_salida` por cualquier camino.
- **Decisión**: el motor no se cambia, porque ningún FR lo pide (Principio III: el código de la primera
  entrega que funciona queda cerrado a modificación).
- **Por qué es aceptable**: en esta regla, la diferencia va hacia el lado seguro. Si la verificación dice
  «resoluble», en el motor también se gana: abrir la puerta que requiere `llave_salida` y da a
  `sala_salida` activa `salida_abierta`. Lo contrario sí puede pasar: una cripta que solo se gana abriendo
  otra puerta con `llave_salida` es no resoluble para la verificación, y en ese caso la partida igual se
  puede jugar con `--forzar`.
- **Acuerdo**: con el integrante 2 (dueño de la 003), el 13 de noviembre.

---

## Integrante 2 — 002 y 003

(pendiente)

---

## Integrante 3 — 004

Spec: [specs/004-linea-tiempo/spec.md](specs/004-linea-tiempo/spec.md) ·
Plan: [specs/004-linea-tiempo/plan.md](specs/004-linea-tiempo/plan.md) ·
Investigación: [specs/004-linea-tiempo/research.md](specs/004-linea-tiempo/research.md)

### §5.3 Banco de pruebas de la línea de tiempo (`--bench`)

`Service/BenchLineaTiempo.py` (con `Service/Cronometro.py` y `ResultadoBenchDTO`, igual que
`Service/BenchInventario.py`) corre sin ventana y con cargas **sintéticas** (Principio VI): una cripta en
cuadrícula de 4 × 4 salas, dos enemigos errantes inofensivos y un jugador que no puede morir, que juega una
secuencia fija (esperar y dar la vuelta a una manzana de salas) con la semilla 2026. Cada partida de 5 000 acciones se
juega una vez por K y la comparten M1, M2 y M3: como la partida es determinista, la historia de las primeras n
acciones es la de una partida de n. `BenchInventario.medir()` devuelve también este grupo (una línea), y así `--bench`
lo muestra sin tocar `Service/ServicioBench.py` (cambio registrado en el plan, NFR-401).

Tabla completa: [bench-tabla.txt](specs/004-linea-tiempo/bench-tabla.txt) (`python -m Service.ServicioBench`, 74 s,
Windows 11 Pro). Los tiempos son medianas y dependen de la máquina; los conteos son reproducibles.

### §5.5 Línea de tiempo y puntos de control

Cada decisión sigue [research.md](specs/004-linea-tiempo/research.md) R1 a R10. «¿Coincide con el plan?» compara
con el `plan.md` original.

**1. Hacia adelante o hacia atrás (R1, diseño A).**

- *Problema*: obtener el estado de un instante pasado sin que una consulta re-simule más de K acciones del jugador
  (FR-416, SC-404).
- *Alternativas*: hacia atrás (invertir cambios desde el estado vivo, como el pergamino); hacia adelante desde el
  punto de control anterior; sin puntos de control (re-simular desde el inicio).
- *Decisión*: **hacia adelante**. `ReconstructorEstado` ubica el punto más cercano anterior, arma con él un **Motor
  aparte** (`PartidaGuardada.cargar`, sin función de mensajes) y re-simula las acciones vigentes. Hacia atrás exigiría
  un segundo historial completo y guardable (el actual guarda funciones, tiene tope de 5 y el pergamino actúa fuera
  de él). La comparación con hacia atrás es teórica: no se implementó un segundo mecanismo solo para medirlo.
- *Complejidad*: O(log P) para ubicar + O(S + E + V + I) para armar el Motor + O(K · ciclo de eventos). Memoria
  O(A) acciones + O(A/K) copias.
- *Evidencia*: M1 y M2 (decisión 10). *Límites*: un cambio de reglas del motor que rompa el determinismo
  (Principio IV) rompe también la línea.
- *¿Coincide con el plan?* Sí.

**2. Reconstrucción sin efectos y `DespachoAcciones` propio (R2).** Reconstruir no escribe `partida.log`, no toca la
caché del catálogo ni gasta solicitudes (Principio VII). Se descartó cargar con `ServicioGuardado.cargar` y ejecutar con
`ServicioAccionJugador`. `Service/DespachoAcciones.py` traduce un `AccionDTO` a la llamada del Motor (mover, abrir,
atacar, esperar, recoger, soltar, equipar, usar; nunca `retroceder`) **sin Data**. Repite la correspondencia de
`ServicioAccionJugador` a propósito, para no modificar la primera entrega (Principio III), y una prueba compara los dos
caminos. *Límite*: si el Motor cambia la firma de un método, hay que actualizar el despacho; esa prueba lo detecta.
*¿Coincide con el plan?* Sí.

**3. Línea autocontenida: grabadores con registros de carga y ordinal (R3, hallazgo H-1).**

- `ContenidoGrabador` y `ResolvedorGrabador` envuelven `contexto.contenido` y `contexto.resolvedor` y guardan en la línea
  lo que **la partida viva ya pidió**: el `SalaDTO` de cada sala cargada (registro de carga) y cada ficha, una vez por
  id. Delegan todo lo demás (incluidos `rechazo()` y `resolver_contenido()`) y, si el original lanza `ErrorDatos`, no
  registran nada. No hacen solicitudes nuevas.
- Se descartó pedir al catálogo las fichas de todo lo que una sala pueda necesitar (gastaría solicitudes que la partida
  viva no gastaba) y guardar el catálogo completo.
- **Ordinal**: cada registro de carga guarda cuántas acciones vigentes llevaba la partida. Los registros se guardan en
  el orden real y no se recortan con el pergamino, porque cargar una sala no se deshace y el contador por tipo de
  `Mazmorra.cargar_contenido` numera los enemigos según el orden de carga («Rata #3»).
- *Tamaño*: ≤ una entrada por sala y una ficha por id usado; no depende de K ni de las acciones (4 cargas en las
  partidas medidas).
- *¿Coincide con el plan?* Sí en el diseño. **T032 (regla del prefijo por ordinal al reconstruir) no fue necesaria**: el
  punto nuevo en c (decisión 4) copia el estado vivo, ya con las salas cargadas y sus contadores. Se verificó con
  `FuenteConRatas` en T034 (dos salas nuevas con el mismo tipo de enemigo, una cargada dentro de una acción revertida).
  El ordinal queda registrado, pero el reconstructor solo toma de la línea las salas que el punto no trae.

**4. Pergamino sin marcador: punto de control nuevo en c (R4, FR-413, FR-424, NFR-403).**

- *Problema*: las acciones revertidas dejan de existir sin recorrer la historia, y el pergamino actúa fuera del
  historial (los pergaminos recogidos o soltados en la acción revertida persisten, hallazgo H-2).
- *Alternativas*: guardar `retroceder` y re-ejecutarla; marcar acciones como revertidas; **marcadores de pergamino**
  (`quitados`/`agregados`) comparando el inventario vivo con el reconstruido.
- *Decisión*: acciones vigentes + **un punto de control nuevo en c** tras el pergamino. `ServicioLineaTiempo.ejecutar`
  compara `jugador.acciones` antes y después: +1 acción nueva, −1 pergamino (llama a `LineaTiempo.retroceder_una` con
  `PartidaGuardada.guardar` del estado vivo ya revertido), sin cambio rechazada. `retroceder_una` quita la última
  acción, quita los puntos con c acciones o más y agrega el de c.
- *Por qué es más simple y exacta que los marcadores*: desaparecen el DTO, el bloque binario, el recorte y la regla de
  aplicación del marcador; y la copia describe **todo** el estado vivo (inventario, suelo, azar, cola), no solo lo
  que alguien previó comparar. Las consultas de instantes anteriores a c usan los puntos anteriores, que reflejan lo
  vivido en ese momento. Consecuencia: tras un pergamino los puntos pueden quedar más cerca que K, nunca más lejos.
- *Complejidad*: O(1 + r) más una copia O(S + E + V + I), sin depender de la historia.
- *Evidencia*: M6: 0,034 ms con 100 acciones de historia y 0,055 ms con 5 000.
- *¿Coincide con el plan?* Sí: es la versión del plan tras `plan(004): punto de control tras el pergamino`.

**5. Búsqueda binaria propia (R5).** Los puntos de control y las acciones nacen ordenados (todo se agrega al final y todo
recorte quita del final), así que `Estructuras/BusquedaBinaria.ultimo_menor_o_igual` (sin `bisect`) basta: O(log n),
sin ordenar. Se descartaron el recorrido lineal y un índice directo `k // K` (frágil con el pergamino y con otro K).
Evidencia (M4, 200 consultas por tanda): con 10 000 puntos, 0,285 ms contra 20,673 ms; con 1 000, 0,281 contra
1,782 ms; con 100 puntos casi empatan (0,199 contra 0,282 ms). *¿Coincide con el plan?* Sí.

**6. `Motor.avanzar_hasta(t)` y la regla de consulta de un instante (R6, FR-402).**

- Método nuevo en `Logic/motorJuego.py`, sin tocar `avanzar_hasta_jugador`: mira el siguiente evento válido, y si es
  posterior a t o es una decisión del jugador, se detiene **justo antes**; si la partida terminó, no ejecuta los demás
  eventos de ese instante. Una corrección posterior (`fix(004): avanzar_hasta usa el evento extraído y cierra el
  intervalo`) hizo que usara el evento ya extraído de la cola.
- **Regla de la consulta**: `j` es la última acción con tiempo **estrictamente menor** que t. Si en t hay una decisión
  del jugador, esa acción no se hace: `historia <t>` coincide con `historia #k`. Si el último punto con
  `acciones_completadas == j` ya tiene reloj igual a t, **ese punto es** el estado pedido y no se llama a
  `avanzar_hasta`; si no, se parte del último punto con `<= j − 1`, se re-simula hasta `j − 1`, se ejecuta la `j` y se
  llama a `avanzar_hasta(t)`. Excepción: si la partida terminó y t es el reloj del final, la acción de t sí se aplica.
- **El error que se corrigió** (commit `d3ddf90`, T021): la primera versión usaba el punto de control directamente
  cuando su reloj era **mayor o igual** que t. Con un instante a mitad de un intervalo, el punto siguiente ya incluía
  eventos posteriores a t y el resumen salía distinto según K. Lo detectó la prueba H5-1 (K = 1 daba otro resumen que
  K = 50). Ahora solo se usa directo si el reloj del punto es **igual** a t. Quedó la prueba de regresión
  `test_instante_entre_decisiones_no_usa_el_punto_posterior_fr402` (`tests/test_reconstructor_estado.py`): compara los
  resúmenes de todos los instantes pares de una partida con K = 1 y con K = 1000 (solo existe el punto 0).
- *¿Coincide con el plan?* No del todo: la regla de consulta se precisó en `spec(004): retraso de efectos y regla de
  consulta de un instante` y el error de arriba obligó a cambiar la condición de «mayor o igual» a «igual».

**7. Validación de t y k en Logic (FR-409).** `LineaTiempo.validar_instante` y `validar_accion` lanzan `ValueError` con
el motivo y el rango válido (t entre 0 y el reloj actual; k entre 1 y las acciones vigentes); es regla de negocio.
`ServicioLineaTiempo` solo la propaga y `ControladorBackend` la devuelve como `ErrorOperacion`. El Controlador valida
**solo la estructura** (`historia <t>` con entero ≥ 0; `historia #k` con entero ≥ 1). Una consulta no consume tiempo, no
cuenta como acción, no se anexa a `partida.log` y no toca el historial de retroceso (FR-407; R9: la feature no registra
nada nuevo ahí). *¿Coincide con el plan?* Sí.

**8. Interfaz: línea de comandos con Enter y Esc (FR-423, T056).** `Enter` abre la línea como un campo de texto durante la
partida; `Enter` acepta y ejecuta, y `Esc` la cierra **sin pausar**. Con la línea abierta las teclas del juego se
escriben y no actúan. El panel de `historia` es de solo lectura y no calcula nada: solo formatea el
`ResumenHistoriaDTO`; `Esc` lo cierra primero (el juego sigue tal cual estaba) y recién el siguiente `Esc` pausa. Una
acción nueva también cierra el panel, porque describe un estado pasado. La misma línea la usará «ir a» (spec 002).
*¿Coincide con el plan?* Sí.

**9. Contenido de la línea en el archivo y K al cargar (R7).** Decisión de diseño: campos nuevos al final de
`PartidaGuardadaDTO`, un bloque propio en el binario con `VERSION_FORMATO = 2`, y los archivos de la primera parte se
rechazan como incompatibles (no se migran). **Todavía no implementado**: depende de T002 y T003 (integrante 2) y de
T044 a T048; por eso M3 mide los bytes con el escritor de la versión 1 (ver «Memoria»).

**10. K por defecto: 20, confirmado (R8, T062).**

- *Problema*: elegir el K más grande (menos memoria) con el que `historia` tarde menos de 50 ms con 5 000 acciones (SC-405).
- *Alternativas medidas (M1)*: K = 1, 5, 20, 100 y **sin puntos de control** (solo el punto 0). Peor caso del bloque
  (la acción que obliga a re-simular K − 1 acciones), mediana:

| K | `historia #k` | `historia <t>` | Puntos | Bytes (5 000 acciones) |
|---|---|---|---|---|
| 1 | 0,090 ms | 0,079 ms | 5 001 | 16 600 279 |
| 5 | 0,186 ms | 0,186 ms | 1 001 | 3 380 623 |
| **20** | **0,620 ms** | **0,617 ms** | 251 | 901 877 |
| 100 | 3,587 ms | 2,978 ms | 51 | 240 877 |
| sin puntos | **147,382 ms** | **149,102 ms** | 1 | 75 627 |

- *Decisión*: **K = 20**, con 0,62 ms: unas 80 veces menos que el límite de 50 ms. Sin puntos de control, `historia`
  tarda 147 ms y **no cumple**: los puntos de control son necesarios. K = 100 también cumpliría (3 ms), pero K = 20 deja
  margen para estados más grandes, donde cada acción re-simulada y cada copia cuestan más (M5). La posición consultada
  importa poco con K = 20 (M2): inicio 0,068 ms, mitad 0,612 ms, final 0,590 ms; sin puntos crece con la posición
  (0,066, 73,5 y 147,4 ms).
- **¿Coincide con el plan?** Sí: coincide con el valor provisional (K = 20). No se cambió `CHECKPOINT_POR_DEFECTO`.
- *Límite*: la medición es con una partida sintética de 16 salas; con muchas salas cada copia cuesta más (M5).

**Costo de una copia (M5, riesgo R-1).** Un punto de control es una copia completa, O(S + E + V + I):

| Salas | 0 enemigos | 10 enemigos | 100 enemigos |
|---|---|---|---|
| 6 | 0,024 ms | 0,046 ms | 0,242 ms |
| 50 | 0,079 ms | 0,126 ms | 0,464 ms |
| 1 000 | 1,268 ms | 1,414 ms | 1,518 ms |
| 10 000 | 14,835 ms | 15,904 ms | 16,811 ms |

Crece con las salas y poco con los enemigos. Para las criptas publicadas (hasta 50 salas) una copia cuesta menos de
0,5 ms; solo con miles de salas llega a unos 15 ms, y se paga una vez cada K acciones. Si eso llegara a ser un
problema, la alternativa que el plan deja anotada (guardar solo las salas que cambiaron desde el punto anterior) no se
adelanta (YAGNI).

**Memoria (M3, NFR-402).** La memoria crece con el número de puntos, no con acciones × estado: con 5 000 acciones, K = 20
guarda 0,90 MB y K = 1 guarda 16,6 MB (unas 18 veces más). Las acciones pesan unos 14,5 bytes cada una (72 500 bytes en
5 000). *Límite*: el formato versión 2 con la línea no existe todavía (T003, integrante 2), así que los bytes son los que
escribe `GuardadoBinario` (versión 1) por cada punto (un archivo por punto, con su cabecera de unos 34 bytes) más las
acciones; las cargas y las fichas se cuentan, pero no se pesan.

### §5.6 Revisión de decisiones de la primera parte

Las decisiones de la primera entrega que esta feature toca se volvieron a medir con la carga nueva (Principio VIII).

**Historial de retroceso (no cambia).** *Antes* (Documento de Decisiones de la primera entrega, §4.6): una función
inversa por cambio, con tope de 5 intervalos. *Después*: la 004 **no registra nada nuevo** en él (R9): consultar no
cambia el estado y la línea vive fuera de `Motor`; el Motor aparte tiene su propio historial, que se descarta con él.
El pergamino sigue funcionando igual; lo único nuevo es que, al leerlo, `ServicioLineaTiempo` toma una copia del estado
vivo (decisión 4), que cuesta entre 0,034 y 0,055 ms y no crece con la historia.

**Ciclo de eventos y agenda (no cambian).** `Motor.avanzar_hasta(t)` es un método nuevo que usa `cola.ver_siguiente()`
y no modifica `ColaEventos` ni `avanzar_hasta_jugador`. La re-simulación ejecuta el mismo ciclo de eventos que la
partida viva, y su costo ya está contenido en M1: con K = 20 re-simula 19 acciones en 0,62 ms, unos 30 µs por acción.
Las mediciones de la agenda y del ciclo de la primera entrega siguen siendo las de §5.6 del integrante 1; esta feature
no las modifica.

**Costo por acción con la línea activa (NFR-401).** `ServicioLineaTiempo.ejecutar` con K = 20 tarda **69,7 µs por acción**
(mediana de 200 acciones) y sin línea, 72,3 µs: la línea no agrega un costo medible, porque registrar una acción es un
`append` (O(1)) y la copia se paga una vez cada 20 acciones (unos 0,07 ms con 16 salas). El «antes» y el «después» son
iguales dentro del ruido de la medición; la decisión de la primera parte sigue siendo adecuada.

**Estructuras de la primera parte.** No se modificó ninguna (R0): `HistorialRetroceso`, `BufferCircular`, `Cola` y
`ListaDoble` no sirven como línea (tope fijo, funciones en lugar de datos, sin acceso por posición), y
`PartidaGuardada` se reutiliza tal cual.

**Pendiente de la sección.** Cuando exista el guardado con línea (T044 a T048), se agregará el tamaño real del archivo
versión 2 y se revisará si ese valor cambia la elección de K.
