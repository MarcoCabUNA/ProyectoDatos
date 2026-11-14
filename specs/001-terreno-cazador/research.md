# Investigación (fase 0): Terreno y cazador

**Feature**: `001-terreno-cazador` · **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Este archivo resuelve las decisiones abiertas del plan. Cada una tiene problema, alternativas,
decisión, complejidad, medición prevista y límites conocidos, como pide el Principio VIII.
Las mediciones se completaron en la fase 7 (T045, [bench-2026-11-13.txt](bench-2026-11-13.txt)):
cada decisión tiene su «Medición» y su «¿Cambió respecto al plan?». La sección del integrante 1 de
`DECISIONES.md` (§5.1, §5.2, §5.6) se escribe a partir de aquí.

Notación: S = salas de la cripta, E = salidas, S_r y E_r = salas y salidas a costo ≤ r del
jugador, k = cazadores activos, g = grado de una sala (≤ 4).

Vocabulario: una **puerta** está abierta o cerrada; una **sala** de la búsqueda está **resuelta**
cuando su distancia ya es definitiva.

---

## R0. Revisión de las estructuras existentes (Principio II)

| Estructura (P1) | Qué hace hoy | Limitación frente a esta feature | Qué se hace |
|---|---|---|---|
| `Logic/ColaEventos.py` | Montículo binario de `EventoProgramado`, desempate por secuencia. Registra cada `programar` y cada extracción en `HistorialRetroceso`. | Está atado a eventos (`tiempo`, `secuencia`, `cancelar`) y al historial. Una búsqueda de rutas no es estado del juego y haría miles de registros inútiles por decisión. No sirve como cola de la búsqueda sin modificarla. | No se toca. La búsqueda usa un montículo nuevo en `Estructuras` (R1). Se vuelve a medir con la carga nueva (R6). |
| `Logic/Comportamientos.py` | `decidir()` devuelve una **sala destino** o `None`. | El costo del movimiento depende de la **salida**, no del destino. Con dos salidas hacia la misma sala, el destino no basta para saber qué costo pagar (FR-104, FR-119). | Se agrega `decidir_paso()` (destino y costo) en la clase base, con una implementación por defecto que usa `decidir()`. `Errante` la redefine para pagar la salida sorteada. `Cazador` es una clase nueva que se suma a `COMPORTAMIENTOS`. |
| `Logic/Mazmorra.py` | `salidas_abiertas()` devuelve destinos **sin costo**. `SalidaViva` no guarda costo. Las puertas cambian en `abrir_puerta()` y `CierrePuerta.activar()`. | No hay costo por salida ni forma de enterarse de que una puerta cambió (lo necesita la invalidación, R4). Además, el costo puede venir declarado en un solo lado (§4.1), igual que la llave, que ya iguala `_igualar_caras`. | `SalidaViva.costo` y `costo_declarado`, y `_igualar_costos()` junto a `_igualar_caras()` (sin modificarlo). Métodos nuevos que devuelven destino y costo, y un aviso de cambio de puerta en los dos puntos donde cambian. |
| `Logic/motorJuego.py` | `mover_jugador()` usa `COSTO_MOVER` (100). `turno_enemigo()` programa siempre 100. | Contradice FR-102 para el jugador y para los enemigos. | El jugador paga `salida.costo`. `turno_enemigo()` paga el costo que devuelve `decidir_paso()`, o 100 si espera o ataca. `cambiar_velocidad()` ya cumple FR-105 y no se toca. |
| `Logic/HistorialRetroceso.py` | Funciones de reversión por intervalo, 5 intervalos. | Ninguna. La caché de rutas se integra registrando en él (R4). | No se toca. |
| `Estructuras/Cola.py` | FIFO enlazada (BFS de `GestorContenido`). | Un BFS cuenta salas. Con costos no uniformes, contar salas no da la ruta más barata (§5.1, caso 3 del Apéndice B). | No sirve para la búsqueda. |
| `Estructuras/Ordenador.py` | Ordenamiento estable propio. | Ordenar toda la frontera en cada paso cuesta O(n log n) por extracción. | No sirve como cola de prioridad. |
| `Estructuras/ListaDoble.py`, `BufferCircular.py` | Inventario y bitácora. | No ofrecen extracción del mínimo. | No se usan. |
| `Logic/BenchLogica.py` | Agenda de eventos y ciclo < 20 ms con errantes y rastreadores. | No hay cazadores ni costos variables (§5.6). | Su `medir()` agrega las mediciones nuevas. Las funciones existentes no cambian. |

Hallazgo en los datos: las cuatro criptas de `paquete/` no tienen salidas sin vuelta, ni dos
salidas hacia la misma sala, ni el campo `costo`. Las pruebas de FR-101, FR-104 y FR-119 usan
criptas sintéticas.

---

## R1. Cola de prioridad de la búsqueda

**Problema**: la búsqueda de costo mínimo necesita extraer repetidamente la sala de menor
distancia tentativa (§5.1). `heapq` y `bisect` están prohibidos (Principio II).

| Alternativa | Extraer mínimo | Bajar una clave | Total búsqueda | Notas |
|---|---|---|---|---|
| A. Recorrer un array de salas sin resolver | O(S) | O(1) | O(S²) | La más simple. Cuesta según el tamaño de la cripta, no según la región: incumple NFR-102. |
| B. Generalizar `ColaEventos` | O(log n) | no tiene | — | Habría que separarla de los eventos y del historial: se modifica código P1 que funciona (Principio III). |
| **C. Montículo binario mínimo nuevo, con entradas repetidas («borrado perezoso»)** | O(log E) | se inserta otra entrada | O((S_r + E_r) log E_r) | Una entrada (distancia, sala). Si al extraerla la sala ya estaba resuelta, se descarta. No necesita índice de posiciones. |
| D. Montículo con índice de posiciones y `bajar_clave` | O(log S) | O(log S) | O((S_r + E_r) log S_r) | Un poco menos de memoria que C, pero necesita un array posición-por-sala que se mantiene en cada intercambio. Más código para el mismo orden de complejidad con g ≤ 4. |
| E. Cubetas por distancia (Dial) | O(1) amortizado | O(1) | O(E_r + r) | Barata si los costos son pequeños. Con costos de cientos y `rango` grande hay muchas cubetas vacías, y la memoria crece con el `rango`. |

**Decisión**: C, en `Estructuras/MonticuloMinimo.py`, sin dependencias de capas. Las entradas
se comparan por distancia y luego por id de sala, así el orden interno también es determinista.
El desempate de FR-111 no depende de este orden (ver R3).

**Por qué**: es la opción más simple que cumple NFR-102. Con g ≤ 4, E_r ≤ 4·S_r, y la
diferencia de C frente a D es una constante.

**Medición prevista**: búsqueda completa con C frente a A en cuadrículas de 100, 1 000 y
10 000 salas con costos aleatorios por semilla.

**Límites**: con muchas mejoras sucesivas de la misma sala, el montículo guarda entradas
viejas: hasta E_r entradas en lugar de S_r.

**Medición (T045, [bench-2026-11-13.txt](bench-2026-11-13.txt))**: búsqueda de esquina a esquina, sin límite (`medir_cola_prioridad`);
mediana de 7 repeticiones. Las dos alternativas dan la misma distancia.

| Salas | C, montículo (elegida) | A, recorrer un array | A / C |
|---|---|---|---|
| 100 | 0,48 ms | 0,62 ms | 1,3 |
| 1 024 | 4,2 ms | 31,6 ms | 7,5 |
| 10 000 | 50,2 ms | no se mide | — |

A es O(S²): con 10 000 salas serían unos 10⁸ pasos por búsqueda, demasiado para correr en cada
`--bench`. Con 100 y 1 024 salas ya se ve que la diferencia crece con el tamaño.

**¿Cambió respecto al plan?** La decisión no. La medición sí: A no se mide con 10 000 salas.

---

## R2. Un cálculo por cazador o uno compartido desde el jugador

**Problema**: hay decenas de cazadores y todos persiguen al mismo jugador (§5.1).

**Observación clave**: el costo es el mismo en ambos sentidos (FR-101). Por lo tanto,
dist(v, jugador) = dist(jugador, v), y una sola búsqueda **desde el jugador** da la distancia de
todas las salas al jugador. Además, el desempate de FR-111 pide justamente dist(v, jugador) para
las vecinas v del cazador. Una búsqueda desde el cazador daría dist(cazador, x), que no sirve para
desempatar sin otra búsqueda.

| Alternativa | Trabajo por ciclo con k cazadores | Notas |
|---|---|---|
| A. Una búsqueda por cazador, desde el jugador, que se detiene al resolver la sala del cazador o al pasar su `rango` | k · O((S_r + E_r) log E_r) | Cada cazador repite casi la misma búsqueda. Es la referencia «desde cero» de las pruebas (FR-114). |
| B. Una búsqueda por cazador, desde el cazador | k búsquedas, más otra para desempatar | Descartada: no da dist(v, jugador). |
| **C. Una búsqueda compartida desde el jugador, reanudable** | O((S_R + E_R) log E_R) una vez, con R = el mayor `rango` consultado, más O(g) por decisión | Se guarda el estado de la búsqueda (distancias, salas resueltas y frontera). Cada cazador la **extiende solo lo que necesita**: hasta resolver su sala o hasta que el mínimo de la frontera pase su `rango`. |

**Decisión**: C. Con un solo cazador hace el mismo trabajo que A, y con k cazadores reparte el
trabajo. La alternativa A se mantiene como función «desde cero» para las pruebas y para la
medición.

**Cuándo cambia la respuesta**: A solo podría ganar si el jugador cambiara de sala entre cada
par de decisiones de cazadores. En ese caso C también recalcula, así que empatan, con el costo
extra de guardar el estado. El bench lo mide.

**Medición prevista**: 1, 10, 30 y 100 cazadores, A frente a C, en la misma cripta y con la
misma secuencia de turnos.

**Medición (T045, [bench-2026-11-13.txt](bench-2026-11-13.txt))**: 1 024 salas, `rango` 3 000, 20 ciclos en los que el jugador da un paso y
después decide cada cazador (`medir_compartida`); mediana de 3 repeticiones de los 20 ciclos.

| Cazadores | A, una búsqueda por cazador | C, compartida (elegida) | Búsquedas A / C | A / C |
|---|---|---|---|---|
| 1 | 31,6 ms | 32,1 ms | 20 / 20 | 1,0 |
| 10 | 268 ms | 63 ms | 200 / 20 | 4,2 |
| 30 | 611 ms | 67 ms | 600 / 20 | 9,1 |
| 100 | 1 617 ms | 64 ms | 2 000 / 20 | 25,1 |

Las decisiones de C son iguales a las de A en todos los casos (el bench lo comprueba). Con un
solo cazador empatan, como se esperaba; con k cazadores, C hace una búsqueda por cada cambio de
sala del jugador y el resto de las decisiones reutiliza la búsqueda (1 950 de 2 000 con 100 cazadores).

**¿Cambió respecto al plan?** No.

---

## R3. Cortar la búsqueda en el `rango` y corrección del desempate

Consulta de un cazador en la sala u con `rango` r, sobre la búsqueda desde el jugador:

1. Si u ya está resuelta, d = dist(u).
2. Si no, se extraen salas mientras la frontera no esté vacía, su mínimo sea ≤ r y u siga sin resolver.
3. Si u no se resolvió, o d > r, no hay ruta dentro del `rango` y el cazador espera (FR-109).
4. Si se resolvió con d ≤ r, el paso es la vecina v de menor id con costo(u, v) + dist(v) = d. costo(u, v) es el de
   la salida abierta más barata entre u y v (FR-119).

**Por qué basta con lo ya calculado**: toda vecina v que cumple costo(u, v) + dist(v) = d tiene
dist(v) = d − costo(u, v) ≤ d − 1 < d, porque todo costo es ≥ 1 (FR-101). Por lo tanto v se resolvió
**antes** que u y su distancia es definitiva. Una vecina que no está resuelta tiene dist(v) ≥ d, así
que costo(u, v) + dist(v) > d y no puede cumplir la igualdad. El desempate se resuelve mirando solo
las g ≤ 4 salidas de u, y el resultado no depende del orden de la búsqueda (§3.2, FR-111).

**Corte en el `rango`**: con r pequeño, la búsqueda solo resuelve salas a distancia ≤ r del jugador.
El trabajo crece con la región dentro del `rango`, no con la cripta (NFR-102).

**Arrays sin reiniciar**: las distancias y las marcas de sala resuelta viven en arrays (`list`
usada como almacenamiento contiguo, Principio II) de tamaño S, que se crean **una sola vez**.
Cada búsqueda nueva incrementa un número de generación, y una casilla solo vale si su marca
coincide con la generación actual. Empezar una búsqueda nueva cuesta O(1), no O(S).

**Salidas sin vuelta**: la búsqueda desde el jugador recorre las salidas **al revés**: para resolver
x mira las salas que tienen una salida abierta hacia x. Esta adyacencia inversa es estática (no
depende de las puertas) y se arma una vez, en O(S + E). Con salidas siempre de ida y vuelta da lo
mismo que recorrerlas al derecho, y si una cripta trae una salida sin vuelta, sigue siendo correcta.

**Medición prevista**: `rango` 200, 600 y 5 000 sobre cuadrículas de 100, 1 000 y 10 000 salas.
Con `rango` fijo, el tiempo debe quedar aproximadamente constante al crecer la cripta (SC-105).

**Medición (T045, [bench-2026-11-13.txt](bench-2026-11-13.txt))**: un cazador en la sala 1 y una búsqueda nueva en cada decisión, con el
jugador en otra sala sorteada cada vez (`medir_rango`). Tiempo por decisión (mediana) y salas
resueltas por búsqueda; con `rango` 5 000 se hacen 40 decisiones en lugar de 400.

| `rango` | 100 salas | 1 024 salas | 10 000 salas |
|---|---|---|---|
| 200 | 19,6 µs (5,4 salas) | 32,9 µs (8,2) | 35,9 µs (8,2) |
| 600 | 112 µs (32,4) | 258 µs (64,3) | 314 µs (69,2) |
| 5 000 | 227 µs (65,9) | 3 151 µs (725) | 19 790 µs (3 743) |

Con `rango` 200, pasar de 100 a 1 024 salas tarda 1,68 veces, y de 1 024 a 10 000, 1,09 veces:
**SC-105 se cumple**. El tiempo sigue a las salas resueltas (la región dentro del `rango`), no al
tamaño de la cripta (NFR-102). Con 100 salas la región es más chica porque muchas posiciones del
jugador están cerca de un borde. Con `rango` 5 000 la región es casi toda la cripta y el tiempo crece
con ella, como se esperaba.

**¿Cambió respecto al plan?** La decisión no. El método de la medición sí cambió, y estas son
las dos mediciones con `rango` 200.

| Método | 100 salas | 1 024 salas | 10 000 salas | Razones | SC-105 |
|---|---|---|---|---|---|
| Primera corrida (`dfe4608`): el jugador alterna entre dos salas del centro, 200 decisiones | 20,2 µs (5 salas) | 15,4 µs (4) | 42,7 µs (12) | 0,76 y 2,78 | no cumple |
| Ahora (`5d01509`): el jugador en 400 salas sorteadas | 19,6 µs (5,4) | 32,9 µs (8,2) | 35,9 µs (8,2) | 1,68 y 1,09 | cumple |

*Causa.* Cada cuadrícula sortea sus costos con la misma semilla, pero tiene otro tamaño, así que las
salidas alrededor de su centro son otras. Con `rango` 200, en el centro de la de 10 000 salas había
salidas más baratas y la búsqueda resolvía 12 salas; en la de 1 024 resolvía 4. La razón 2,78 sale
de esas 12 salas contra 4, no del tamaño de la cripta.

*Evidencia.* El tiempo por sala resuelta es casi el mismo con los dos métodos y en los tres tamaños:
4,0, 3,9 y 3,6 µs en la primera corrida, y 3,6, 4,0 y 4,4 µs ahora. Con el método anterior, la
decisión en la cripta de 10 000 salas tardó más porque resolvió 3 veces más salas, no porque la
cripta fuera más grande: por sala resuelta tardó menos (3,6 µs frente a 3,9). Las salas resueltas se
cuentan en el bench y son reproducibles con la semilla.

*Por qué la versión nueva mide mejor lo que pide SC-105.* SC-105 compara la misma decisión, con
`rango` 200, en criptas de distinto tamaño. Una sola posición del jugador compara tres terrenos
distintos, y la razón mezcla el tamaño con los costos de ese lugar: en la primera corrida, con la
misma búsqueda, una razón dio 0,76 y la otra 2,78. Promediando 400 posiciones, la región dentro del
`rango` es la típica de cada cuadrícula: 8,2 salas en la de 1 024 y 8,2 en la de 10 000. El método
nuevo no favorece el resultado. La razón de 100 a 1 024 salas empeora (de 0,76 a 1,68) porque en la
cuadrícula de 10 × 10 muchas posiciones están junto a un borde y su región es más chica (5,4 salas).
El método nuevo deja eso a la vista.

---

## R4. Qué invalida la búsqueda guardada, y reutilizar frente a recalcular

Lo que entra en el cálculo es solo **la sala del jugador**, **la topología con costos** (fija) y
**el estado de las puertas** (FR-112, FR-120). Cada evento del §5.2:

| Evento entre dos turnos | ¿Afecta? | Regla |
|---|---|---|
| El jugador cambia de sala | Sí, cambia el origen | Al consultar se compara el origen guardado con la sala actual del jugador. Si difieren, se empieza una búsqueda nueva. No hace falta aviso. |
| Se abre o se cierra una puerta (llave o cierre automático) entre a y b | Solo si a o b ya están **resueltas** en la búsqueda | Una salida u→v solo se lee al resolver v (R3). Si ningún extremo está resuelto, la salida todavía no se leyó, y cuando se lea se leerá con su estado nuevo. Si alguno está resuelto, se descarta la búsqueda. Por eso el aviso puede llevar solo los destinos de las caras que cambiaron. |
| Un cazador u otro enemigo se mueve | No | El origen es el jugador y los actores no bloquean (FR-120). |
| Muere un actor | No | Ídem. |
| Cambia la velocidad de un actor | No | Solo cambia cuándo actúa (FR-105), no la ruta. |
| Se carga el contenido de una sala | No | FR-112. |
| Pergamino de retroceso | Sí | Ver «Historial». |
| Se carga una partida guardada o un replay | — | El motor nuevo empieza sin búsqueda guardada. |

**Historial (pedido del usuario: «toda caché que sea estado del juego se registra en
HistorialRetroceso»)**: la búsqueda guardada es un dato derivado, no estado del juego. Aun así,
**cada vez que se crea, se extiende o recibe un aviso de puerta**, registra en el historial una
reversión que la **descarta**. Si un pergamino deshace un intervalo en el que la búsqueda o una
puerta cambiaron, la búsqueda queda descartada y la siguiente consulta empieza desde cero. Si en
ese intervalo no cambió ninguna de las dos, la búsqueda sigue siendo válida para el estado
restaurado. Así no se copian estructuras (no se usa `copy`, Principio II) y deshacer sigue
costando O(cambios del intervalo).

**Garantía de FR-114**: con estas reglas, la búsqueda guardada siempre es la que habría producido
una búsqueda desde cero desde el mismo origen con las puertas actuales, extendida hasta el mismo
punto. Por R3, la decisión es idéntica. Las pruebas lo verifican comparando, en cada turno de cada
cazador, contra la alternativa A de R2.

| Alternativa | Trabajo con puertas estables | Con puertas inestables | Complejidad |
|---|---|---|---|
| A. Recalcular siempre | k búsquedas por ciclo | Igual | Mínima |
| B. Descartar ante **cualquier** cambio de puerta | 1 búsqueda por cambio de sala del jugador | 1 por cada cambio de puerta | Baja |
| **C. Descartar solo si la puerta toca una sala resuelta** | Igual que B | Solo los cambios cercanos al jugador descartan | Una comprobación O(1) por aviso |

**Decisión**: C. Una puerta que se cierra lejos de todos los cazadores no descarta nada (§8,
pregunta 2 del enunciado).

**Medición prevista**: A, B y C con puertas estables (sin cambios) y con puertas inestables
(cierres automáticos frecuentes, cerca y lejos del jugador), contando búsquedas reales por ciclo
y tiempo por ciclo (§5.2, §6.3).

**Límites**: un jugador que cambia de sala en cada decisión obliga a una búsqueda nueva por
decisión del jugador. Sigue siendo una sola búsqueda para todos los cazadores.

**Medición (T045, [bench-2026-11-13.txt](bench-2026-11-13.txt))**: 30 cazadores (`rango` 600, 1 500 y 3 000) en 1 024 salas, 60 ciclos; el
jugador da un paso cada 5 ciclos (`medir_invalidacion`). Las puertas cambian como en `abrir_puerta`
y `CierrePuerta`. Búsquedas reales por ciclo y tiempo por ciclo (mediana):

| Escenario | A, recalcular siempre | B, cualquier puerta | C, descarte preciso (elegida) |
|---|---|---|---|
| Puertas estables | 21,8 · 15,8 ms | 0,20 · 0,55 ms | 0,20 · 0,64 ms |
| Una puerta al azar por ciclo | 20,6 · 14,1 ms | 0,98 · 2,23 ms | 0,67 · 1,60 ms |
| Al azar y una de la sala del jugador | 19,4 · 10,9 ms | 1,00 · 1,76 ms | 1,00 · 1,77 ms |

Las tres estrategias deciden lo mismo en cada turno (el bench lo comprueba). C solo gana a B cuando
la puerta que cambia no toca la región ya resuelta. Una puerta de la sala del jugador siempre la
toca, porque el origen está resuelto, y entonces C hace lo mismo que B. Comprobar el aviso cuesta
O(1).

**Evidencia de FR-114** (T028, `TestEquivalenciaAleatoria`): 12 partidas aleatorias con puertas,
cierres automáticos, muertes, cambios de velocidad y pergaminos, con unas 11 000 decisiones de
cazador, todas iguales a `paso_desde_cero`. La búsqueda se reutilizó en más del 90 % de ellas.
Pruebas de mutación: sin los avisos de puerta fallan 6 o 7 de las 12 partidas. Sin el descarte
registrado para el pergamino, el error solo lo detecta la prueba fija
`test_pergamino_despues_de_abrir_una_puerta_sin_moverse`; en las partidas aleatorias lo detecta,
a lo sumo, 1 de 12.

**¿Cambió respecto al plan?** No. La medición separa «puertas inestables» en dos escenarios,
porque con una puerta junto al jugador en cada ciclo, B y C empatan.

---

## R5. La misma búsqueda para «ir a» (§5.3)

**Problema**: «ir a» (feature 002, integrantes 2 y 3) calcula la ruta del jugador sobre el
**mapa conocido**, con el mismo desempate. Lo pide el §5.3 del enunciado, no un requisito de la
spec 001.

**Decisión**: la búsqueda y la elección del paso reciben el **grafo como parámetro**. Un grafo
es cualquier objeto que responde:

- `cantidad_salas()`: el tamaño de los arrays;
- `entradas(x)`: pares (origen, costo) de las salidas **utilizables** que llegan a x;
- `salidas(u)`: pares (destino, costo) de las salidas utilizables de u.

Para el cazador, «utilizable» es «abierta ahora» sobre el esqueleto real. Para «ir a», el
integrante 2 da un grafo con las salas exploradas y las puertas como se recuerdan. «Ir a» busca
**desde la sala destino**, y el jugador da un paso con la misma regla de R3. El cazador es el caso
«origen = jugador».

**Por qué no es YAGNI (Principio III)**: el cazador ya necesita separar la búsqueda de la
`Mazmorra` para probarla con grafos pequeños (FR-111, FR-114), así que el parámetro no agrega
código. Lo que se agrega para «ir a» es solo el contrato.

**Alternativa descartada**: dos búsquedas separadas. Duplicaría el código y el desempate, y las
pruebas del Apéndice B solo cubrirían una.

**Límites**: el paso de «ir a» debe tardar menos de 5 ms (§6.1). Su medición es del integrante 3,
sobre el grafo del integrante 2. Ver el [contrato](contracts/busqueda-rutas.md).

---

## R6. Revisión de decisiones de la primera parte (§5.6)

- **Agenda de eventos** (Principio VIII: las mediciones de P1 se repiten con la carga nueva): se
  repite la comparación de `medir_agenda`, montículo frente a array ordenado, con los tiempos que
  generan costos entre 1 y 300 y velocidades distintas (`medir_agenda_con_costos`). También se mide
  el ciclo con 30 cazadores en una cuadrícula de 1 000 salas. Con costos variables, los tiempos de los eventos se dispersan más. Se espera
  que el montículo siga siendo adecuado frente al array ordenado. Si los datos dicen otra cosa,
  se documenta el antes y el después en `DECISIONES.md`.
- **Historial de retroceso**: la búsqueda guardada agrega a lo sumo un registro por cada
  creación, extensión o aviso de puerta. Se mide cuántos registros más hay por intervalo con 30
  cazadores (la medición base es del integrante 3).

**Medición (T045, [bench-2026-11-13.txt](bench-2026-11-13.txt))**:

- **Agenda, con la carga nueva** (`medir_agenda_con_costos`; reloj = 0, la acción pendiente de cada
  actor en un instante de su intervalo y el lote en reloj + intervalo completo). Costo por evento
  (mediana):

  | Eventos | Programar: montículo / array | Sacar: montículo / array |
  |---|---|---|
  | 100 | 0,76 / 15,2 µs | 2,1 / 0,13 µs |
  | 1 000 | 0,85 / 128 µs | 3,9 / 0,12 µs |
  | 10 000 | 0,81 / 1 241 µs | 5,4 / 0,13 µs |

  Programar y sacar suman 6,2 µs en el montículo y 1 241 µs en el array con 10 000 eventos: unas
  200 veces menos, contra unas 120 en la primera entrega. Con esta carga, cada evento nuevo va
  después del 69 % de los pendientes en promedio, y el array tiene que correrlos.

  *Cambio de método de esta medición.* La primera corrida (`dfe4608`) usaba otra carga: los n
  eventos en un instante al azar entre 0 y 10·n más un intervalo, y el lote entre 0 y 1 000 (10·100)
  más un intervalo. Las dos mediciones:

  | Eventos | Carga anterior: programar, montículo / array | Carga nueva: programar, montículo / array |
  |---|---|---|
  | 100 | 0,97 / 12,5 µs | 0,76 / 15,2 µs |
  | 1 000 | 1,41 / 16,5 µs | 0,85 / 128 µs |
  | 10 000 | 1,59 / 14,0 µs | 0,81 / 1 241 µs |

  Sacar no cambia (en el montículo, 2,1 a 5,5 µs con las dos cargas; en el array, 0,12 a 0,14 µs).
  *Causa*: con la carga anterior, el lote caía casi siempre antes que la agenda, porque sus instantes
  llegaban hasta unos 1 500 y los de la agenda hasta 100 000. *Evidencia* (conteo exacto con la
  misma semilla): con 10 000 eventos, cada evento del lote dejaba detrás, en promedio, a 46
  pendientes (0,5 %), y el array solo corría esos 46. Por eso su costo no crecía con n (12,5, 16,5 y
  14,0 µs), aunque la primera entrega había medido el mismo array creciendo en forma lineal (9,5,
  78 y 782 µs). Con la carga nueva, cada evento del lote deja detrás a 77 de 100, 726 de 1 000 y
  6 926 de 10 000 (del 69 % al 77 %).

  *Por qué la carga nueva mide mejor lo que pasa en el juego*: los eventos pendientes de una agenda
  real están entre el reloj y el reloj más un intervalo, y el actor que acaba de actuar programa su
  siguiente acción en el reloj más un intervalo completo, así que queda detrás de la mayoría. La
  carga anterior medía un caso que el juego no produce. El cambio no decide nada: con la carga
  anterior el montículo también sumaba menos (7,1 µs entre programar y sacar, contra 14,1 µs del
  array con 10 000 eventos). Las filas de cancelaciones usan la misma carga de la agenda y apenas se
  movieron (90 % cancelado, 10 000 eventos: 53,1 µs por evento válido antes y 60,6 µs ahora).
- **Muchos eventos con el mismo tiempo** (10 000): el montículo programa en 0,69 µs y saca en
  5,5 µs, igual que con tiempos distintos. El array tarda 1 821 µs en programar: con un solo
  tiempo, el desempate por secuencia pone cada evento nuevo detrás de todos los demás.
- **Muchas cancelaciones** (10 000): con el 50 % cancelado, sacar 100 eventos válidos descarta
  91 cancelados y cuesta 10,2 µs por evento válido. Con el 90 %, descarta 917 (el arreglo pasa de
  10 000 a 8 983 entradas) y cuesta 60,6 µs por evento válido, unas 11 veces más que sin
  cancelaciones. El array descarta igual de perezoso, pero cada descarte es un `pop()` O(1).
- **Ciclo con cazadores** (`medir_ciclo_cazadores`, 1 024 salas, 20 errantes y rastreadores):
  con 30 cazadores, el peor ciclo es de 7,9 ms con el jugador quieto y de 5,4 ms con el jugador
  moviéndose (una búsqueda nueva en cada ciclo): **NFR-101 y SC-104 se cumplen**. Con 100 cazadores
  es de 14,5 y 18,0 ms: todavía cumple, pero con poco margen.
- **Historial** (`medir_historial`, 30 cazadores): con el jugador quieto, la búsqueda agrega 0,02
  registros por intervalo sobre 249. Con el jugador moviéndose, agrega 1,60 sobre 106, un 1,5 %.

**¿Cambió respecto al plan?** No. El montículo sigue siendo la agenda y el historial no cambia.
El límite de las cancelaciones queda documentado: sacar se encarece en proporción a los
cancelados que hay en la raíz. En el juego, las cancelaciones vienen de muertes, antídotos y
cambios de velocidad: una por evento, no el 90 % de la agenda.

---

## R7. Contrato de datos

**Confirmado con el integrante 2 el 11 de noviembre, tal como está.** Ver
[contracts/contrato-datos.md](contracts/contrato-datos.md).

- `SalidaDTO.costo: int | None = None`: el costo **declarado** en ese lado, o `None` (FR-101). Es
  del integrante 2. Con `int = 100`, Lógica no podría distinguir «no declarado» de «declarado 100»,
  y no sabría qué lado manda cuando solo uno lo declara. Lógica iguala los dos lados al cargar el
  esqueleto.
- `FichaEnemigoDTO.rango: int | None = None`: es del integrante 1. Tiene que tener valor por
  defecto en Python porque los campos anteriores (`efectos`, `extras`) ya lo tienen, y porque los
  enemigos que no son cazadores no lo traen. «Sin valor por defecto» de FR-122 significa que
  **a un cazador no se le inventa un `rango`**: si un cazador llega con `None` o con un valor
  inválido, Data lo rechaza. `"rango"` se agrega a `_CAMPOS` para que no se duplique en `extras`.
- La validación de FR-122 (incluidos dos lados con costos distintos) vive en Data (Principio I: Data valida formato). Es código del
  integrante 2 y este plan no la incluye.
- Sin cambios en Lógica para validar: Lógica confía en el DTO.
