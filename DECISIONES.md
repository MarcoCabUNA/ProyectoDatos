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
- *Con el mapa conocido de la 002* (15 de noviembre): `observador_puertas` ya no es `self.rutas` sino un
  `RepartidorAvisosPuertas([rutas, mapa])` que el `Motor` asigna (002 FR-207), y `Logic/BenchRutas.py` arma el
  mismo repartidor en las dos mediciones que reemplazan las rutas (`medir_ciclo_cazadores`, `medir_historial`).
  En 3 corridas del `--bench` completo, con 30 cazadores el peor ciclo es de 5,5 a 17,6 ms: **NFR-101 y SC-104 se
  siguen cumpliendo**, pero con poco margen: el peor (17,6 ms, corrida 3, con el jugador esperando) queda a 2,4 ms
  del límite de 20 ms. Con 100 cazadores y el jugador moviéndose (fuera de NFR-101) dio 19,6 / **20,0** / **22,4** ms.
  Medido aparte, con la misma función del bench (`medir_ciclo_cazadores(cazadores=(30, 100))`, sola) y alternando el código de antes del merge (sin mapa) y el de ahora, el peor ciclo es de 7,2 a 9,4 ms
  en los dos y las medianas son iguales: el mapa no encarece el ciclo, y el pico depende de lo que corre antes en
  el mismo proceso, como la fila de 500 enemigos de abajo. Tabla en
  [bench-2026-11-15.txt](specs/001-terreno-cazador/bench-2026-11-15.txt).

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

Mediciones: `python -m Service.ServicioBench` (`Logic/BenchRutas.py`), tabla completa en [bench-2026-11-13.txt](specs/001-terreno-cazador/bench-2026-11-13.txt) y, con el mapa conocido conectado, en [bench-2026-11-15.txt](specs/001-terreno-cazador/bench-2026-11-15.txt). Máquina: AMD Ryzen 5 3600X, 32 GB, Windows 11 Pro, Python 3.12.10. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la máquina.

**Fichas con un dato inválido (cambia, T052, T055 y T057, FR-122).**

- *Antes* (P1, `Data/GestorContenido.resolver_pendientes`): un error de formato salía como el mismo `ErrorRed` que
  un fallo de red, y la precarga los trataba igual. El lote se integraba al esqueleto y quedaba cargado **antes**
  de resolver su catálogo, así que, si el catálogo fallaba, las salas del lote seguían como cargadas.
- *Después*: el dato inválido sale como `ErrorDatos` (`Data/ValidacionDatos.py`), subclase de `ErrorRed`, así
  que los `except ErrorRed` de P1 lo siguen atrapando sin cambios; quien necesita distinguirlo pregunta
  `isinstance(error, ErrorDatos)`. `ResolvedorCatalogo` no guarda la ficha inválida (ni en memoria ni en disco) y
  recuerda su error: no la vuelve a pedir (T052: `rango`; T055: `duracion` de un objeto; T057: un enemigo con una
  ficha de su `suelta` rechazada, también si viene de la caché en disco). `resolver_pendientes` resuelve el
  catálogo antes de integrar el lote y solo la sala que menciona la ficha rechazada (por sus enemigos o, desde
  T055, sus objetos del suelo) queda `RECHAZADA`, con el error guardado por sala: «contenido no disponible».
  `asegurar_sala` relanza ese error sin hacer otra solicitud. Las demás salas del lote se cargan normalmente y
  la precarga no se interrumpe.
- *Commits*: `c01dc93` (T052), `9eea7fa` (T055) y `38861c6` (T057), del integrante 2. Pruebas en
  `tests/TestValidacionDatos.py`.

**Contenido de una sala con una caché vieja en disco (cambia, T058, FR-122).**

- *Antes* (P1, `Data/GestorContenido.asegurar_sala`, con lo de T052): la sala se entregaba como cargada si ninguna
  de sus fichas estaba entre los rechazos **en memoria**. Con una caché escrita antes de T055/T057 (un enemigo
  guardado sin su `suelta`, o un objeto con `duracion` 0), la ficha inválida aparecía recién dentro de
  `Mazmorra.cargar_contenido`, cuando `ResolvedorCatalogo.ficha()` la volvía a validar al leerla del disco. La
  sala quedaba a medio cargar: los enemigos anteriores agregados, `contadores_tipo` avanzado (incluido el del
  rechazado) y la sala todavía cargada para Data. Con un `ErrorRed` a mitad, el reintento duplicaba los enemigos
  (en la prueba (c), `e-1` dos veces y los números en 2). Un objeto del suelo inválido ni siquiera se detectaba al
  entrar: el movimiento se hacía y el error salía después, sin atrapar, en `SincronizadorUsos`.
- *Después*: antes de devolver la sala, `asegurar_sala` pide `resolvedor.ficha(tipo, contar_acierto=False)` de
  cada enemigo, cada trampa y cada objeto del suelo. Con `ErrorDatos`, la sala queda rechazada (`_rechazar`) y el
  error sale; con `ErrorRed`, sale sin marcar nada y la sala se vuelve a validar en el próximo intento. Lógica
  recibe la sala solo si todas sus fichas son válidas; `Logic/Mazmorra.py` no cambia.
- *Costo*: O(enemigos + trampas + objetos) consultas a `ficha()` por sala que se entra. Las fichas ya están en
  memoria o en disco (las bajó `resolver_contenido`), así que no hay solicitudes nuevas: en una partida con el API
  falso, sin caché y con caché, las solicitudes (6 y 4) y los pedidos de catálogo (2 y 0) son los mismos antes y
  después, y el replay de ejemplo pide los mismos 2 lotes de contenido. Lo que cambia es el reporte de la caché:
  si una ficha se lee del disco aquí, la lectura de `cargar_contenido` que sigue cuenta como acierto (en la
  partida con caché, 3 aciertos en lugar de 1; los fallos y las lecturas de disco no cambian).
- *Acuerdo*: con el integrante 2, dueño del archivo; el cambio lo hizo el integrante 1. Pruebas en
  `tests/test_cache_vieja.py`.

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

Spec: [specs/002-niebla-ir-a/spec.md](specs/002-niebla-ir-a/spec.md) ·
Plan: [specs/002-niebla-ir-a/plan.md](specs/002-niebla-ir-a/plan.md) ·
Investigación: [specs/002-niebla-ir-a/research.md](specs/002-niebla-ir-a/research.md)

### §5.3 Mapa conocido

La parte de «ir a» de §5.3 (el viaje automático que usa este mapa) la escribe el integrante 3 en su sección. Aquí va
la parte del mapa conocido: los tres estados de cada sala, la memoria de puertas por cara, la antorcha, el pergamino,
el guardado y lo que el mapa le ofrece a «ir a» (FR-201 a FR-225, NFR-201 a NFR-205). Detalle en
[research.md](specs/002-niebla-ir-a/research.md) R0 a R7 y en
[contrato-mapa-conocido.md](specs/002-niebla-ir-a/contracts/contrato-mapa-conocido.md).

**Revisión de las estructuras existentes (R0).** Se usa tal cual `HistorialRetroceso` (registrar O(1), deshacer
O(cambios del intervalo)) para el pergamino. La `Mazmorra` se usa **solo para leer** (nombres, salidas, costo
igualado, emparejamiento de caras con `_salida_inversa`); tiene un solo `observador_puertas`, ocupado por las rutas
del cazador. `GrafoEsqueleto` no sirve para «ir a» (su «utilizable» es «abierta ahora», no «recordada abierta»), pero
se copia su idea de adyacencia inversa armada una vez. `BusquedaCostoMinimo` sirve sin cambios porque recibe el grafo
como parámetro. Ninguna estructura de `Estructuras/` ofrece acceso directo por id, y los ids ya son enteros seguidos,
así que no se usan ni se agrega nada a `Estructuras/`. `PartidaGuardada` y `GuardadoBinario` se extienden (decisión 4).

#### 1. Representación: dos arreglos, por sala y por cara (R1)

**Problema.** Tres estados por sala (desconocida, avistada, explorada; FR-201), el estado recordado de cada puerta
**por cara** (abierta, cerrada o sin observar; FR-207, FR-208, FR-212), separado del esqueleto (FR-218), con
consultas que no dependan del tamaño (NFR-201, SC-203) y sin `dict` ni `set`.

**Alternativas.** `set` o `dict` de exploradas (O(1) promedio, prohibido); una lista de ids explorados recorrida en
cada consulta (O(X)); atributos nuevos en `SalaViva` y `SalidaViva` (O(1), pero mezcla esqueleto y conocimiento y
modifica código P1 del integrante 1); un grafo propio con copia de las salas conocidas (duplica el esqueleto);
`bytearray` (O(1), fuera de los tipos acordados).

**Decisión.** `Logic/MapaConocido.py`, estado de la partida que vive en el motor (`motor.mapa`), con dos `list[int]`:
`estado[sala]` (largo S) y `caras[sala*4 + dirección]` (largo 4·S). Lo que se sabe de una explorada (nombre,
salidas, costo igualado) no se copia: se lee del esqueleto solo si está explorada. «Avistada» se mantiene al
explorar (cada destino desconocido de sus salidas pasa a avistado), sin contadores, porque entre dos pergaminos las
exploradas solo crecen. Ninguna operación baja un estado (FR-203).

**Complejidad.** `estado_sala` y `estado_cara`: O(1). Memoria: 5 casillas por sala, O(S).

**Evidencia** (B1 a B3, 100 / 1 024 / 10 000 salas, un tercio en cada estado):

| Medición | Resultado |
|---|---|
| B1 `estado_sala`, 100 000 consultas | 0,044 / 0,048 / 0,048 µs por consulta: 10 000 contra 100, 1,10 veces; **SC-203 se cumple** |
| B2 `estado_cara`, 100 000 consultas | 0,092 / 0,101 / 0,100 µs por consulta: 1,09 veces; **SC-203 se cumple** |
| B3 listas de ids recorridas (descartada) | 0,87 / 7,6 / 102,7 µs por consulta: 20, 158 y 2 138 veces B1 |

**¿Coincide con el plan?** Sí.

#### 2. Tres puntos de entrada y el repartidor del aviso de puertas (R2)

**Problema.** Explorar al entrar, con y sin antorcha (FR-202, FR-203, FR-210 a FR-216), volver a observar las
puertas de la sala del jugador cuando cambian (FR-207, FR-209), con costo proporcional a lo revelado (NFR-202,
SC-204), dentro del ciclo de 20 ms (NFR-205, SC-206) y sin que la precarga, el esqueleto o el cazador toquen el mapa
(FR-218).

**Alternativas.** Actualizar el mapa en Service después de cada movimiento (las reglas quedarían en Service y la
re-simulación de la 004 tendría que repetirlo); re-observar la sala del jugador al final de cada evento (O(1) por
evento, en todos, y toca el bucle de P1); recalcular «avistadas» recorriendo todo el mapa después de cada entrada
(O(S + X·g)); un segundo observador en la `Mazmorra`; que el mapa reenvíe el aviso a las rutas (cadena).

**Decisión.** Solo tres puntos escriben el mapa: `iniciar` (desde `Motor.iniciar`), `entrar(sala, antorcha)` (desde
`Motor.mover_jugador`, justo después de cambiar la sala; el booleano es `efectos.tiene(jugador, "antorcha")` en ese
instante, así que el mapa no conoce los efectos y H3-8 sale sin código especial) y `puerta_cambio` (el aviso de la
001, que re-observa todas las puertas de la sala del jugador, porque el aviso no identifica una puerta sin vuelta).
Más `restaurar` al cargar. Todo pasa por `_poner_estado` y `_poner_cara`. Para que el aviso llegue a las rutas del
cazador y al mapa sin modificar la `Mazmorra`, el motor asigna `RepartidorAvisosPuertas([rutas, mapa])` como
`observador_puertas` (hallazgo H-1; las líneas de `Logic/motorJuego.py` las escribió el integrante 2 y las revisó el
integrante 1). El cambio a `Logic/motorJuego.py` quedó en el commit `ed0da17` (revisado y aprobado por el integrante 1
el 15/11).

**Complejidad.** `iniciar` y `entrar` sin antorcha: O(g). Con antorcha: O(1 + Σ g de las vecinas que pasan a
exploradas), a lo sumo 5 salas y 20 salidas. `puerta_cambio`: O(g), g ≤ 4. El repartidor: O(observadores) por aviso.

**Evidencia** (B4, B5 y B8; la entrada al centro con la antorcha revela siempre 5 salas y 8 caras):

| Medición | Resultado |
|---|---|
| B4 entrada con antorcha, resto del mapa explorado | 13,1 / 13,3 / 13,5 µs: el mayor contra el menor, 1,03 veces; **SC-204 se cumple** |
| B5 entrada + recalcular «avistadas» (descartada) | 49 / 400 / 4 844 µs: crece con S |
| B8 ciclo con antorcha, 1 024 salas, 30 cazadores y 20 errantes y rastreadores, el jugador se mueve | peor ciclo 5,71 ms (mediana 0,43 ms): **NFR-205 y SC-206 se cumplen** |
| B8, además una puerta de la sala del jugador cambia en cada ciclo, avisada por `motor.mazmorra.observador_puertas` | peor ciclo 5,50 ms (mediana 0,47 ms): **se cumplen** |

Antes de cronometrar B8 se juegan 30 ciclos de cada variante comparando, casilla por casilla, el mapa del motor
medido (aviso por el repartidor) con el de un motor de control (aviso a las rutas y al mapa por separado), y en la
sala del jugador cada cara recordada con la real: son iguales.

**¿Coincide con el plan?** Sí.

#### 3. Pergamino: reversión por casilla en el historial (R3)

**Problema.** El pergamino debe dejar el mapa exactamente como antes de la acción, incluidas las salas de la
antorcha y las puertas observadas (FR-222), con registro e inversión proporcionales a lo que cambió (NFR-203,
SC-207).

**Alternativas.** Copiar el mapa entero al empezar cada acción y restaurarlo (O(S) por acción); una sola función de
reversión por entrada con la lista de casillas (misma complejidad, más difícil de explicar); inversas también para
la línea de tiempo (no hacen falta: la 004 reconstruye hacia adelante).

**Decisión.** `_poner_estado` y `_poner_cara` no hacen nada si el valor no cambia; si cambia, registran en el
`HistorialRetroceso` existente una función que devuelve **esa casilla** a su valor anterior (índice y valor ligados) y
después escriben. Como deshacer recorre el intervalo de atrás hacia adelante, una casilla que cambió dos veces en la
acción vuelve al primer valor. El conocimiento inicial se descarta con la preparación del motor y no se deshace.

**Complejidad.** Registrar: O(1) por casilla cambiada. Deshacer: O(casillas cambiadas en el intervalo); una entrada
con antorcha cambia a lo sumo 5 estados de exploración, 16 de avistamiento y 8 caras. No depende de S ni de X.

**Evidencia** (B6 y B7, las mismas 13 casillas en los tres tamaños):

| Medición | Resultado |
|---|---|
| B6 entrar con antorcha, cerrar el intervalo y deshacer | 15,9 / 25,8 / 15,7 µs (el mejor, 16 µs en los tres): el mayor contra el menor, 0,99 veces; **SC-207 se cumple** |
| B7 copiar el mapa entero y restaurarlo (descartada) | 10,7 / 24,9 / 159,9 µs: crece con S |

**¿Coincide con el plan?** Sí.

#### 4. Copia por punto de control y bloque propio en el binario versión 2 (R4)

**Problema.** Guardar y cargar el mapa idéntico (FR-221), que cada punto de control de la línea de tiempo lleve el
mapa de ese instante (FR-223) y que `--replay` dé el mismo mapa (FR-224), sin `copy` y con una copia proporcional al
tamaño del mapa una vez por punto (NFR-203).

**Alternativas.** Para el archivo: el mapa dentro del bloque global; solo las exploradas y las caras observadas
(lista de pares, O(X)); una copia por casilla dentro del bloque de cada sala; reconstruir el mapa al cargar
re-simulando. Para cargar un DTO sin mapa: lanzar `ValueError` (rompe unas 109 construcciones en 11 archivos de
prueba de otros integrantes sin proteger ningún archivo real) o un `if` en `PartidaGuardada.cargar`.

**Decisión.** `MapaConocidoGuardadoDTO(estado_salas, caras)` como campo `mapa` de `PartidaGuardadaDTO`, antes de
`linea`, que sigue siendo el último. `a_guardado` copia los dos arreglos con `list(...)` y `restaurar` los vuelve a
copiar (si no, la re-simulación de la 004 escribiría dentro del punto de control), comprueba los largos (si no
coinciden con la `Mazmorra`, `ValueError`) y **reemplaza** el mapa en curso sin registrar en el historial (H-8).
`restaurar(None)` arma el mapa inicial desde la sala del jugador, como FR-202, así `PartidaGuardada.cargar` suma una
sola línea, sin `if`. El cambio a `Logic/PartidaGuardada.py` quedó en el commit `4aac926`, junto con T041 a T044 (el
integrante 1 aceptó no rehacerlo como commit propio; aprobado el 15/11); el comentario se reordenó después en el
commit de los ajustes de su revisión. En el archivo, el mapa va en un **bloque propio**: 1 byte de estado y 1 byte con las 4 caras
(2 bits cada una) por sala; el mismo codificador sirve para el mapa de cada punto de control dentro del bloque de la
línea (T003 de la 004).

**Antes y después del formato binario** (cambia una decisión de la primera parte; el antes es el formato del archivo
de partida del Documento de Decisiones de la primera entrega y de P1 §4.10):

- *Antes*: versión 1; cabecera con magia `CRPT`, versión, offset y largo del bloque global, offset del índice,
  entradas e id mínimo; bloque global, bloques de sala e índice al final.
- *Después*: versión 2, definida una sola vez con los dos bloques nuevos (el del mapa de esta feature y el de la línea
  de T003 de la 004): la cabecera pasa a 58 bytes (`<4sHQIQIIQIQI>`) con offset y largo del mapa y de la línea; el
  bloque global, los bloques de sala y el índice no cambian, y `cargar_sala` sigue sin leer ni el mapa ni la línea.
  Un archivo de la versión 1 se rechaza con la versión leída y la esperada, sin cargar nada (FR-421 de la 004).

**Complejidad.** Copiar para guardar o para un punto de control: O(S) en tiempo y memoria (5 casillas por sala en
memoria, 2 bytes por sala en el archivo). Cargar: O(S).

**Evidencia** (B9, con el mapa completo):

| Medición | Resultado |
|---|---|
| B9 `a_guardado` + `restaurar` | 2,6 / 16,3 / 145,7 µs (26, 16 y 15 ns por sala): crece en forma lineal con S, una vez por punto de control |

**¿Coincide con el plan?** Sí. `restaurar(None)` en lugar de un error se decidió en el plan el 14/11 (riesgo R-9),
antes de implementar.

#### 5. Lo que el mapa le ofrece al integrante 3 (R5)

**Problema.** «Ir a» y la interfaz solo pueden usar lo que el jugador conoce (FR-217, FR-225), con el desempate de
la búsqueda de la 001 (FR-253).

**Alternativas.** Para el grafo: que el mapa avise a una búsqueda guardada entre pasos (nadie lo usaría: YAGNI); una
segunda búsqueda propia de «ir a» (la 001 ya decidió compartirla). Para la vista: mantener una lista de exploradas
para armar el DTO en O(X) (más estado que revertir y guardar). Para el nombre: un índice ordenado con búsqueda
binaria (O(log S), pero hay que mantenerlo con cada exploración y cada pergamino, y la búsqueda ocurre una vez por
orden).

**Decisión.** `GrafoMapaConocido(mapa)` con la interfaz exacta de la 001 (`cantidad_salas`, `salidas`, `entradas`):
una salida es utilizable si sus dos salas están exploradas y la cara de la sala de origen se recuerda abierta; costo
igualado; ids reales; lee el mapa en vivo. «Ir a» empieza una búsqueda nueva por paso. `MapaConocido.a_dto()` arma el
`MapaConocidoDTO` en Logic (solo exploradas, por id creciente; destino `None` para una avistada; nunca una
desconocida ni el contenido). `buscar_exploradas(nombre)` compara `strip().casefold()` solo contra exploradas
(H-3). `es_explorada(sala)` sirve al integrante 3 para el H-2.

**Complejidad.** `salidas(u)`: O(4); `entradas(x)`: O(grado de entrada), más O(S + E) la primera vez (índice inverso
del esqueleto); constructor O(1). `a_dto` y `buscar_exploradas`: O(S).

**Evidencia** (B10 y B11, con el mapa completo):

| Medición | Resultado |
|---|---|
| B10 `a_dto` | 0,28 / 3,04 / 39,7 ms (2,8, 3,0 y 4,0 µs por sala) |
| B10 `buscar_exploradas` | 11 / 194 / 1 247 µs (109, 190 y 125 ns por sala) |
| B11 armar el grafo (constructor + índice inverso) | 0,08 / 0,94 / 13,6 ms |
| B11 un `paso_desde_cero` de esquina a esquina con el grafo armado | 0,27 / 3,79 / 50,5 ms |
| B11 armar el grafo + un paso (búsqueda nueva por paso) | 0,56 / **4,52** / 65,0 ms: con 1 024 salas queda **por debajo de 5 ms** (NFR-250 del integrante 3) |

**¿Coincide con el plan?** Sí. El plan no afirmaba si «armar el grafo + un paso» entraba en 5 ms; ahora está medido,
y la frase de research R5 y del contrato (a) dice el número.

#### Decisiones tomadas por diseño, sin medición

- **El `RepartidorAvisosPuertas`**, frente a un solo observador o a que la `Mazmorra` avise a dos observadores: es una
  cuestión de responsabilidades y de no modificar la `Mazmorra` (código P1 del integrante 1), no de rendimiento. Las
  tres opciones cuestan O(1) por aviso; el repartidor deja a las rutas y al mapa con una sola responsabilidad cada
  uno, y el orden de la lista no cambia ningún resultado (el mapa no cambia puertas y las rutas no leen el mapa).
- **El bloque propio del mapa en el binario**, frente a meter el mapa en el bloque global: es formato y
  compatibilidad, con el mismo costo O(S). El bloque global lo reutiliza cada punto de control de la línea (que va con
  `linea = None`) y `cargar_sala` no debe leer conocimiento.

#### Límites conocidos y hallazgos

- **Dos salidas de una sala hacia la misma vecina** (H-4). El mapa empareja las caras con
  `Mazmorra._salida_inversa` (del integrante 1, solo lectura), que da solo la **primera** cara de vuelta. Con dos
  salidas de x hacia la misma vecina v, la segunda cara de v hacia x no queda emparejada y no se observa desde x. Es la
  misma regla que usan `abrir_puerta` y `CierrePuerta`, y queda fuera de las criptas publicadas, que no tienen salidas
  repetidas (H-1 de la 001).
- **Dependencia de `_salida_inversa`** (H-7), que es privada de la `Mazmorra`, como ya la usa `PartidaGuardada`. Si
  el integrante 1 cambia esa regla o su nombre, avisa antes (está en su lista de funciones privadas usadas por la 002
  y la 003); las pruebas H2-6 y A16 lo detectan.
- **`observador_puertas` del motor** (H-1): ahora es el repartidor, no `self.rutas`. `Logic/BenchRutas.py` lo reasigna
  en dos mediciones y, desde `c22202d` (integrante 1), también ahí a un `RepartidorAvisosPuertas([rutas, mapa])`: el
  mapa sigue escuchando. El data-model de la 001 ya dice que el `Motor` asigna el repartidor (integrante 1, 15/11).
- **Lectura de H2-5** (H-5): si el jugador estuviera en A, la puerta A–C no podría estar «sin observar»; el escenario
  se reescribió en la spec (el jugador está en B y A y C se exploraron con la antorcha) y la prueba se arma así.
- **Cuadrícula de 1 024 salas** (H-6): SC-206 dice «1 000 salas»; B8 usa la cuadrícula de 32 × 32 del bench de la 001,
  para medir en la misma cripta.
- **Cargar reemplaza el mapa** (H-8): una partida guardada puede tener menos salas exploradas que el mapa vivo; no
  contradice FR-203 (es otra partida), y FR-221 lo dice desde la Sesión 2026-11-14.
- **Margen de B11**: con 1 024 salas, «armar el grafo + un paso» tarda 4,52 ms de mediana: cumple, pero con poco
  margen (casi 3,8 ms son la búsqueda, que recorre toda la cripta de esquina a esquina). Lo usa el integrante 3 para
  NFR-250.
- **Alcance de B8**: el jugador va y viene entre dos salas, así que después del primer ciclo la antorcha casi no
  revela salas nuevas; el costo de una entrada que sí revela está en B4 (13 µs) y es despreciable frente a los 20 ms.
- **`a_dto` con 10 000 salas** cuesta 4,0 µs por sala frente a 2,8 y 3,0 con mapas menores (crea 5 objetos por sala);
  sigue siendo O(S) y se llama una vez por consulta del mapa, no por paso.

Mediciones: `python main.py --bench` (`Logic/BenchMapaConocido.py`), tabla completa en
[bench-2026-11-15.txt](specs/002-niebla-ir-a/bench-2026-11-15.txt). Máquina: AMD Ryzen 5 5500, 32 GB, Windows 11 Pro,
Python 3.14.7. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la
máquina.

### §5.4 Resolubilidad

Spec: [specs/003-resolubilidad/spec.md](specs/003-resolubilidad/spec.md) ·
Plan: [specs/003-resolubilidad/plan.md](specs/003-resolubilidad/plan.md) ·
Investigación: [specs/003-resolubilidad/research.md](specs/003-resolubilidad/research.md)

La verificación de resolubilidad (§3.5, §5.4; FR-301 a FR-323, NFR-301 a NFR-304) dice, antes de iniciar una partida
nueva o con `--verificar`, si se pueden obtener las llaves en algún orden hasta llegar a `sala_salida` por una puerta
que pide `llave_salida`; si no, informa qué llaves no se pueden obtener, la frontera y los ciclos. Detalle en
[research.md](specs/003-resolubilidad/research.md) R0 a R9 y en los contratos
[contrato-llaves.md](specs/003-resolubilidad/contracts/contrato-llaves.md) y
[contrato-reporte-resolubilidad.md](specs/003-resolubilidad/contracts/contrato-reporte-resolubilidad.md). Notación:
S salas, E caras (E ≤ 4S), U ubicaciones de llaves, K llaves distintas, M menciones de llaves (caras con llave +
ubicaciones + `llave_salida`), F puertas de la frontera.

**Revisión de las estructuras existentes (R0).** Se usan tal cual la `Cola` (FIFO con nodos, O(1)) para el recorrido
y la fase hacia afuera, y el `Ordenador` (estable, O(n log n)) para el índice de llaves, cada oleada, la frontera, las
ubicaciones y los niveles de puertas. `GestorEsqueleto.existe_sala` (O(1)) sirve para validar ubicaciones en Data. La
`Mazmorra` se usa en una instancia **aparte**, que se descarta, solo para leer las caras ya combinadas con la regla de
la primera parte. No sirven: `MonticuloMinimo` (el costo no afecta la verificación, FR-302: no hay prioridad),
`ListaDoble` (no hace falta borrar en el medio), `BufferCircular` (no se descarta nada), `GrafoEsqueleto` de la 001
(lee el estado vivo y no conoce llaves) ni `BusquedaBinaria` de la 004 (el índice se arma sin búsquedas; la 003 no
depende de la 004). Lo nuevo es código de Logic; **no se agrega nada a `Estructuras/`**.

#### 1. Contrato y persistencia de las llaves (R1)

**Problema.** Obtener la ubicación de las llaves (`GET /criptas/{id}/llaves`, §4.2) por el mismo camino que el resto
de los datos, también con `--offline`, sin pedirla dos veces (FR-317), sin que el almacén tape un `llaves.json`
ausente del paquete (FR-318, FR-320) y rechazando una llave en una sala que no existe (FR-321).

**Alternativas.** `obtener_llaves` abstracto en `FuenteDatos` (rompe las fuentes de prueba y del bench que no lo
necesitan); persistir en una carpeta por versión como el catálogo (la versión es por cripta: deja carpetas viejas,
mismo O(1) archivos por cripta); validar la sala en Logic (mismo O(U), pero Logic supone datos válidos); pedir
`GET /criptas/{id}/version` para validar lo persistido (+1 solicitud por verificación, y la versión ya llega en los
datos generales).

**Decisión.** `UbicacionLlaveDTO(id, sala, enemigo)` inmutable, entregado en el orden de la respuesta (Data no
ordena ni deduplica). `FuenteDatos.obtener_llaves` **no abstracto**, que por defecto lanza `ErrorRed`; `FuenteJson`
valida el formato y `LectorPaquete` lee `paquete/<id>/llaves.json` (si falta, el «falta el archivo» que ya existe es
FR-320). `Data/AlmacenLlaves.py` guarda un archivo por cripta en `cache/llaves/<id>.json` con su versión, que se
compara con `validar_version` contra la versión ya pedida de la cripta (no cuesta una solicitud); distinta versión,
archivo dañado o id distinto se tratan como ausentes. Con `--offline` no hay almacén, y eso se decide en **una sola
condición**, el mismo `if` donde `ServicioPartida.fuente()` elige la fuente. `Data/GestorLlaves.py` orquesta: almacén
vigente o una solicitud que se persiste, y después `validar_ubicaciones` (FR-321). Se persiste **antes** de validar:
volver a pedir no arregla un `ErrorDatos`, y así la segunda verificación da el mismo error sin gastar otra solicitud.

**Complejidad.** Una solicitud por cripta y versión; leer y validar: O(U).

**Evidencia.** No es un problema evaluado de §5: no se mide. Lo comprueban las pruebas de
`tests/test_resolubilidad_datos.py` (`test_fr317_obtener_llaves_es_una_solicitud_que_cuenta`,
`test_h3_5_fr317_no_repite_la_solicitud`, `test_fr317_se_persiste_antes_de_validar_fr321`) y
`test_fr317_red_con_almacen_de_llaves` de `tests/test_resolubilidad_servicio.py`. El Swagger confirmó el formato del
contrato el 15/11 (hallazgo H-4 de research, T008).

**¿Coincide con el plan?** Sí. El Swagger coincidió con el contrato y no hizo falta cambiarlo.

#### 2. Índice propio de llaves: ordenar y compactar (R3)

**Problema.** El recorrido necesita, por cada llave, una lista de espera y un estado, pero las llaves son textos y no
se puede usar `dict` como índice (Principio II).

**Alternativas.** `dict` id → índice (O(M) esperado, prohibido); búsqueda lineal en la lista de ids por cada mención
(O(M·K)); ids ordenados y búsqueda binaria por mención (O(M log M + M log K), y haría falta una búsqueda binaria de
textos que no existe).

**Decisión.** `Logic/GrafoLlaves.py` arma la lista de menciones `(id_llave, tipo, posición)`, la ordena con el
`Ordenador` por id (desempate por tipo y posición, así no depende del orden de entrada) y la recorre una vez: cada id
nuevo abre un índice `0, 1, 2…` que se escribe de vuelta en la cara o la ubicación mencionada. Los índices quedan en
orden de id, así que desempatar por índice es desempatar por id (decisión 4).

**Complejidad.** O(M log M) el ordenamiento + O(M) la compactación; espacio O(M + K).

**Evidencia** (B5, las tres cuadrículas de B1: 191, 2 081 y 20 981 menciones; 10, 100 y 1 000 llaves):

| Medición | Resultado |
|---|---|
| B5 ordenar y compactar (elegida) | 0,452 / 4,088 / 52,702 ms: ×9,0 y ×12,9 (con el mejor tiempo, ×12,4 y ×12,6), O(M log M) |
| B5 búsqueda lineal (descartada) | 0,136 / 6,823 / 688,5 ms (en 10 000 salas, 1 repetición): ×50,1 y ×100,9, O(M·K) |

Con 100 salas la lineal gana por constantes; con 1 000 ya gana ordenar y compactar, y de 1 000 a 10 000 la lineal
crece ×100,9 frente a ×12,9. El desglose B4 (decisión 3) muestra que la preparación, que incluye este índice, es el
86 % de la verificación con 1 000 salas.

**¿Coincide con el plan?** Sí. B5 se agregó al plan en la revisión del integrante 1 (13/11), antes de implementar. La
fila de B5 en research R7 decía que la lineal crece ~×100 en cada tramo; el 16/11 se corrigió con el factor medido
entre 100 y 1 000 (Principio IX). La decisión no cambia.

#### 3. Recorrido incremental por oleadas, con la frontera agrupada por llave (R4)

**Problema.** Decidir si la cripta es resoluble sin volver a recorrer lo ya alcanzado cada vez que se obtiene una
llave (§5.4, NFR-302), y dejar del mismo recorrido la frontera y lo que necesitan los ciclos (NFR-303).

**Alternativas.** Repetir el recorrido completo desde `sala_inicial` cada vez que se obtienen llaves (la ingenua de
§5.4, O(K · (S + E + U))); la misma por oleadas pero con la frontera en una sola lista revisada entera al obtener cada
llave (O(S + E + K·F), y con llaves encadenadas F crece con la cripta); recorrido en profundidad (O(S + E + U), pero
el orden depende del orden de visita y no deja oleadas para el desempate); `GrafoEsqueleto` (no resuelve el
problema).

**Decisión.** `GrafoLlaves` carga el esqueleto en una `Mazmorra` aparte, para combinar las caras igual que el juego
(FR-302), y lee arreglos planos por cara (`c = sala*4 + dirección`): tipo, destino y llave. El costo y el cierre
automático no se leen. `Logic/RecorridoLlaves.py` recorre por anchura con la `Cola`: una cara con llave no obtenida
se anota en `esperando[k]` y una cerrada sin llave en `sin_llave`. Al terminar cada oleada, las llaves vistas pasan a
obtenidas y **solo** se revisan sus listas `esperando[k]`. Es resoluble si se obtuvo `llave_salida` y alguna cara que
lleva a `sala_salida`, cerrada y que pide `llave_salida`, sale de una sala alcanzable (FR-304); si no existe ninguna
cara así en el esqueleto, el veredicto lleva el motivo de FR-322. La frontera son las caras que quedaron esperando
cuyo destino sigue afuera (FR-308).

**Complejidad.** O(S + E + U) el recorrido + O(K log K) ordenar las oleadas; con la preparación,
O(S + E + U + M log M), «aproximadamente lineal» (NFR-302). Espacio O(S + E + U + K).

**Evidencia** (B1 a B3 en cuadrículas de 100, 1 000 y 10 000 salas con 10, 100 y 1 000 llaves encadenadas; B6 en el
«peine» de 100, 1 000 y 3 000 dientes, donde la frontera empieza con una puerta por diente):

| Medición | Resultado |
|---|---|
| Cripta con más salas del paquete (`cripta-06`, 300 salas, resoluble) | mediana 1,371 ms: **SC-306 y NFR-301 se cumplen** (< 200 ms) |
| B1 verificación incremental, resoluble | 0,808 / 11,107 / 156,423 ms: ×13,8 y ×14,1; de 1 000 a 10 000, ≤ ×20: **SC-307 se cumple** |
| B2 repetir el recorrido por oleada (descartada) | 1,621 / 58,606 / 5 770,5 ms (en 10 000, 1 repetición): ×36,1 y ×98,5, 2,6 y 7,0 veces el de B1: **SC-307 se cumple** |
| B6 frontera agrupada por llave (elegida) | 0,253 / 3,185 / 9,136 ms: ×12,6 y ×2,9 |
| B6 frontera en una sola lista (descartada) | 0,507 / 28,033 / 236,7 ms (en 3 000, 1 repetición): ×55,3 y ×8,4 |
| B4 desglose con 1 000 salas (cripta de B3) | preparación 9,543 ms (86 %), recorrido 0,777 (7 %), frontera, fase hacia afuera y ciclos 0,650 (6 %), armado 0,098 (1 %) |

En B2, «por oleada» y «por llave» son lo mismo: en la cuadrícula encadenada, una oleada = una llave, así que la
alternativa hace K + 1 recorridos completos. En B6, con 100 dientes pesa la parte que no depende de la frontera (unos 0,25 ms en las dos variantes); sin ella, la
lista única crece unas ×98 entre 100 y 1 000. Con 2 001 salas la lista única tarda 8,8 veces la agrupada. El
recorrido es el 7 % de B4: el tiempo se va en la preparación (decisión 2 y la carga en la `Mazmorra` aparte).

**¿Coincide con el plan?** Sí. B6 y el peine se agregaron al plan en la revisión del integrante 1 (13/11), antes de
implementar. La fila de B6 en research R7 se corrigió el 16/11 con el factor medido de la lista única entre 100 y
1 000 (×55 en lugar de ~×100); la decisión no cambia.

#### 4. Orden determinista (R5)

**Problema.** Un orden válido de obtención de llaves (FR-305) que sea el mismo en cualquier ejecución y no dependa del
orden del JSON (FR-306), y un orden fijo para cada lista del reporte, sin `sorted` ni `list.sort`.

**Alternativas.** El orden de descubrimiento del recorrido (determinista con la misma entrada, pero depende del orden
de las ubicaciones o de las páginas, que no es una regla del juego); orden topológico global por id, siempre la menor
llave disponible (válido, pero necesita un montículo con claves de texto: O((K + E) log K)).

**Decisión.** El orden es la concatenación de las oleadas de la decisión 3 y, dentro de cada oleada, por id (que es
el índice de la decisión 2). Cada lista del reporte tiene su regla: no obtenibles por id; ubicaciones por sala, sin
enemigo antes que con enemigo y luego por enemigo, con las idénticas una sola vez (FR-309); frontera por sala y
dirección; ciclos por su llave de menor id; dependientes por id. Todo con el `Ordenador` y comparadores de enteros.

**Complejidad.** O(K log K + F log F + U log U) en total.

**Evidencia.** No es un problema de tiempo: el costo entra en el armado de B4 (0,098 ms, 1 % con 1 000 salas). El
determinismo lo comprueban `test_h1_5_apendiceB_caso3_fr305_fr306_mismo_orden_en_dos_ejecuciones`,
`test_fr306_entrada_permutada_mismo_resultado` y `test_sc303_diez_ejecuciones_en_procesos_separados`.

**¿Coincide con el plan?** Sí.

#### 5. La puerta que bloquea (FR-310) y ciclos sin recursión (R6)

**Problema.** Señalar los ciclos de dependencia entre llaves no obtenibles y las llaves que dependen de ellos
(FR-310), del mismo recorrido (NFR-303) y sin `RecursionError` con cadenas largas.

**Alternativas.** El grafo completo de dependencias con componentes fuertemente conexas (O(K + D), pero un ciclo
concreto igual necesita elegir una puerta por paso); un recorrido aparte por cada llave no obtenible (O(K · (S + E)),
viola NFR-303); enumerar todos los ciclos simples (exponencial); entre puertas del mismo nivel, preferir la que pide
la propia llave (solo arregla los ciclos de una llave); seguir las aristas con recursión (O(K), pero con una cadena de
1 000 llaves llega al límite de Python, y `setrecursionlimit` solo corre el problema).

**Decisión.** La regla de FR-310 (*decisión del grupo*, 13/11): la puerta que bloquea a una llave es una sola, la de
menor nivel desde la región alcanzable y, si empatan, la de menor sala de origen y luego menor dirección. La fase
hacia afuera continúa el recorrido por niveles con la `Cola` y asigna a cada zona su puerta. Así cada llave no
obtenible tiene a lo sumo una arista: los ciclos son disjuntos. `Logic/CiclosLlaves.py` los detecta con un `while` que
guarda el camino en un arreglo y asigna a cada llave la entrada a su ciclo volviendo por ese arreglo.

**Complejidad.** Fase hacia afuera O(S + E) más ordenar los niveles, O(E log E) en el peor caso; detección O(K) +
O(K log K) ordenar dependientes; espacio O(K).

**Evidencia** (B3, la variante no resoluble de B1: un ciclo de una llave y una cadena de 5, 50 y 500 dependientes):

| Medición | Resultado |
|---|---|
| B3 verificación incremental, no resoluble | 1,250 / 13,531 / 133,109 ms: ×10,8 y ×9,8 (con el mejor tiempo, ×13,4 y ×11,4), frente a ×13,8 y ×14,1 de B1: **NFR-303 se cumple** (el reporte no cambia el orden de crecimiento) |
| B4 frontera, fase hacia afuera y ciclos, 1 000 salas | 0,650 ms, 6 % de la verificación |

`test_fr310_cadena_de_mas_de_1000_dependientes_sin_recursion` (2 × 3 000 salas, unas 1 500 dependientes) termina
sin `RecursionError` y sin cambiar `sys.getrecursionlimit()`; `test_h2_13_fr306_fr307_fr308_fr310_puerta_que_bloquea`
comprueba el desempate.

**¿Coincide con el plan?** Sí. La regla de FR-310 y la detección iterativa salieron de la revisión del plan por el
integrante 1 (13/11), antes de implementar.

#### 6. Dónde vive cada parte y cómo se inicia la partida (R8)

**Problema.** Repartir la feature entre las capas (Principio I) y verificar al iniciar una partida nueva sin que el
replay, la carga ni `--bench` verifiquen (FR-301) y sin pedir dos veces los datos (FR-317).

**Alternativas.** Verificar dentro de `ServicioPartida.iniciar_partida` con una bandera (ese método lo usa el replay,
y una bandera olvidada rompería FR-301); verificar en el controlador con su propia carga de datos (pediría dos veces
los datos generales y el esqueleto).

**Decisión.** Data entrega y valida (`obtener_llaves`, `AlmacenLlaves`, `GestorLlaves`, `validar_ubicaciones`);
Logic decide (`GrafoLlaves`, `RecorridoLlaves`, `CiclosLlaves`, `VerificadorResolubilidad`) y no importa Data;
Service orquesta (`ServicioResolubilidad`); `main.py` y `LectorArgumentos` agregan `--verificar` y `--forzar`.
`iniciar_partida_nueva` abre los datos (un error ahí no inicia ni con `--forzar`), pide las llaves (un `ErrorRed` da
«no concluyó»), verifica y, si no es resoluble y no hay `--forzar`, lanza `ErrorPartidaNoIniciada` sin crear el motor
ni `partida.log`; si no, inicia con los mismos datos.

**Antes y después del inicio de una partida** (cambia una decisión de la primera parte, Principio III):

- *Antes* (P1): toda partida nueva iniciaba en cuanto se cargaban los datos de la cripta.
- *Después*: iniciar una partida nueva verifica la resolubilidad (`ControladorBackend.iniciar` →
  `_iniciar_verificando` → `ServicioResolubilidad.iniciar_partida_nueva`) y, sin `--forzar`, puede no iniciar: si la
  cripta no es resoluble o la verificación no concluye, `ErrorPartidaNoIniciada` llega como `ErrorOperacion`, el
  reporte queda en `resolubilidad()` y no se crean el motor ni `partida.log` (FR-311). Cargar una partida y `--replay`
  siguen igual que en P1 (FR-301).
- *`cripta-01` con `--offline`*: el paquete no trae su `llaves.json`, así que el paso de llaves da `ErrorRed` («falta
  el archivo … llaves.json») y el reporte es «no concluyó» (FR-320). Sin `--forzar` la partida **no inicia** («No se
  pudo verificar si la cripta cripta-01 es resoluble: la partida no se inició (use --forzar …)»); con `--forzar`
  inicia y el reporte «no concluyó» queda en `contexto.resolubilidad` para mostrarlo (FR-312, FR-313). Comprobado el
  17/11 con `ServicioResolubilidad` sobre el paquete del repositorio.
- *Pruebas del integrante 3*: las que inician por `ControladorBackend` con la `cripta-01` offline usan
  `ConfiguracionDTO(offline=True, forzar=True)`: `CONFIG_OFFLINE` de `tests/ayudas_controladores.py` y
  `tests/test_controlador_pygame.py` (commit `3940eac`, 16/11) y `tests/test_ir_a_interfaz.py`. Las que llaman
  directamente a `ServicioPartida.iniciar_partida` (por ejemplo `tests/ayudas_linea_tiempo.py`) no pasan por la
  verificación, igual que el replay.

**Interpretación del Principio I** («Data solo conexión y formato»). Comprobar que la sala de cada ubicación existe en
el esqueleto (FR-321) es **integridad de los datos**, no una regla del juego: no depende del estado de la partida ni
decide nada del juego, y una respuesta que nombra una sala inexistente está mal para esa versión, igual que un formato
inválido. Por eso va en Data (`validar_ubicaciones` en `Data/ValidacionDatos.py`, O(U)). El precedente es 001
FR-122: la validación de que una puerta tenga el mismo costo en sus dos caras ya vive en `GestorEsqueleto`, en Data
(research R1). La instancia de enemigo de una ubicación no se valida (FR-321, FR-301).

**Complejidad.** La de las decisiones 1 a 5; iniciar no pide dos veces los datos ni el esqueleto.

**Evidencia.** Es una decisión de responsabilidades, no de tiempo. Lo comprueban
`test_r3_fr317_no_pide_dos_veces_datos_ni_esqueleto`, `test_h4_1_apendiceB_caso4_fr311_no_resoluble_no_inicia` y
`test_h1_8_fr301_no_descarga_contenido_ni_consume_azar`; T067 confirmó que Logic no importa Data ni Service.

**¿Coincide con el plan?** Sí.

#### 7. Nada en el historial ni en la línea de tiempo (R9)

**Problema.** Que la verificación no cambie el estado de la partida ni lo que se reproduce o se revierte (FR-301).

**Alternativas.** Registrar la verificación como un evento en el instante 0 «para que se vea en el replay» (cambiaría
la cola de eventos, la numeración de la línea y el replay de las partidas de la primera parte).

**Decisión.** La verificación no registra nada en `HistorialRetroceso`, en la línea de tiempo de la 004 ni en
`partida.log`: ocurre antes de que existan el motor, el historial, la línea y la bitácora, y la `Mazmorra` auxiliar
no tiene motor. El reporte no es una acción; `contexto.resolubilidad` es solo lectura y `PartidaGuardada` no lo guarda.

**Complejidad.** Ninguna sobre la partida: O(1).

**Evidencia.** `test_r9_fr301_verificacion_no_registra_en_historial_linea_ni_log`: después de
`iniciar_partida_nueva`, el historial está vacío, la línea no tiene acciones y el log solo tiene el encabezado.

**¿Coincide con el plan?** Sí.

#### Paquete de la Parte II y veredictos (T057, T058)

**Paquete de la Parte II y excepción de `cripta-01` (T057, 15/11).** El API del 15/11 publica `cripta-02` a `cripta-06`
(catálogo `4b9e75a42be5`) y ya no `cripta-01` (responde 404). El paquete local conserva `cripta-01/` byte idéntica,
porque la usan las pruebas de los tres integrantes, y toma del API el catálogo y las demás criptas. Como el catálogo es
uno solo para todas las criptas, `cripta-01` usa las fichas nuevas: `ent_rata_gigante` (vida_max 12→8, ataque 5→3,
defensa 1→0, velocidad 150→110) y `ent_guardian_oseo` (vida_max 20→16, ataque 7→5, defensa 3→2). Su contenido trae
`"vida": 12` en las ratas y `Enemigo` toma esa vida tal cual, así que empiezan con 12 de vida y `vida_max` 8. Evitarlo
tocaría la primera parte sin un FR o inventaría datos; el integrante 1 lo aceptó el 15/11. Además, `cripta-01` es la
única cripta sin `llaves.json`: `--verificar cripta-01 --offline` termina con código 1 («falta el archivo …
llaves.json», FR-320). Reporte completo, con los veredictos de T058:
[paquete-2026-11-15.md](specs/003-resolubilidad/paquete-2026-11-15.md).

**Veredictos de T058** (`--verificar <id> --offline` con el paquete armado):

| Cripta | Veredicto | Código |
|---|---|---|
| `cripta-01` | no concluyó: falta `llaves.json` (ya no está publicada) | 1 |
| `cripta-02` | resoluble: bronce, negra | 0 |
| `cripta-03` | resoluble: bronce, hierro, negra | 0 |
| `cripta-04` | resoluble: bronce, hierro, negra | 0 |
| `cripta-05` | no resoluble: ciclo hierro ↔ negra (hierro en la sala 24, tras la 12–24, que pide negra; negra en la sala 23, tras la 7–22, que pide hierro) | 3 |
| `cripta-06` | resoluble: bronce, hierro, plata, negra | 0 |

#### Límites conocidos y hallazgos

- **Diferencia con el motor en la puerta de salida** (H-1 de research): la registra el integrante 1 en [«Diferencia
  conocida entre la verificación y el motor de P1»](#diferencia-conocida-entre-la-verificación-y-el-motor-de-p1); aquí
  no se repite. En esa regla la diferencia va hacia el lado seguro.
- **Límite conocido en la otra dirección** (spec, Suposiciones; *decisión del grupo*): el «lado seguro» no vale en
  general. En una puerta con cierre automático y llaves distintas por cara, la verificación supone que la puerta
  puede volver a abrirse (§3.5: «una puerta puede volver a abrirse con la misma llave») y no lee el cierre automático
  (decisión 3). El motor la cierra en sus dos caras y volver pide la llave de la otra cara, así que la verificación
  **puede decir «resoluble» y el jugador quedar encerrado**. Se acepta porque §3.5 pide verificar con llaves y
  puertas, sin simular el reloj ni los cierres; lo fija
  `test_fr302_cierre_automatico_con_llaves_distintas_por_cara_no_bloquea`.
- **Varias puertas de entrada del mismo nivel** (R6): el ciclo señalado usa la puerta de la regla de FR-310 y no las
  otras (H2-13); el reporte igual las lista todas en la frontera cuando salen de la región alcanzable.
- **H-2 (presupuesto)**: en una partida en vivo, la solicitud de llaves gasta 1 del presupuesto que el replay no
  gasta, porque el replay no verifica. Solo importaría si la partida agota el presupuesto; con las llaves persistidas
  (FR-317) no se gasta nada. Lo pide FR-317; queda escrito.
- **H-3 (paquete)**: el paquete de la primera parte (`cripta-01` a `cripta-04`, 6, 20, 40 y 50 salas) no traía
  `llaves.json`, `costo` ni `rango`, y `--verificar … --offline` terminaba con código 1 (FR-320). Resuelto el 15/11
  (T057, arriba); queda la excepción de `cripta-01`.
- **La fila del paquete no sirve para ver el crecimiento**: mide una sola cripta (300 salas); la base de B1 a B6 sigue
  siendo la generación sintética por semilla (R7).
- **Ruido en el tamaño menor**: con 100 salas algunas medianas salieron bastante por encima del mejor tiempo (B3:
  1,250 frente a 0,861 ms; B5 ordenar y compactar: 0,452 frente a 0,318 ms); por eso se dan también los factores con
  el mejor tiempo. No cambian ninguna conclusión.

Mediciones: `python main.py --bench` (`Logic/BenchResolubilidad.py` para B1 a B6 y `Service/ServicioBench.py` para
la fila del paquete), tabla completa y comprobaciones de quickstart §4 en
[bench-2026-11-16.txt](specs/003-resolubilidad/bench-2026-11-16.txt). Máquina: AMD Ryzen 5 5500, 31,8 GB, Windows
11 Pro, Python 3.14.7. Semilla `SEMILLA = 2026`: las criptas sintéticas son reproducibles (dos llamadas con la misma
semilla dan criptas iguales); los tiempos son medianas y dependen de la máquina.

---

## Integrante 3 — 004

Spec: [specs/004-linea-tiempo/spec.md](specs/004-linea-tiempo/spec.md) ·
Plan: [specs/004-linea-tiempo/plan.md](specs/004-linea-tiempo/plan.md) ·
Investigación: [specs/004-linea-tiempo/research.md](specs/004-linea-tiempo/research.md)

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
rechazan como incompatibles (no se migran). **Implementado**: T002 y T003 (integrante 2: campo `linea` al final de
`PartidaGuardadaDTO` y `VERSION_FORMATO = 2` en `Data/GuardadoBinario.py`) y T044 a T048 (integrante 3: `a_guardada()` y
`desde_guardada(dto)` en `LineaTiempo`, `ServicioGuardado` guarda la línea y al cargar conserva el K guardado). Lo cubren
`test_linea_a_guardada_y_desde_guardada_son_iguales_fr420` y `test_linea_desde_guardada_conserva_el_orden_fr420`
(`tests/test_linea_tiempo_logica.py`); `test_t002_de_la_004_linea_ida_y_vuelta_por_diccionario`,
`test_t003_de_la_004_binario_v2_ida_y_vuelta_con_linea`, `test_t003_de_la_004_binario_v2_linea_none_largo_cero`,
`test_t047_de_la_004_cargar_sala_no_lee_mapa_ni_linea`, `test_t047_de_la_004_archivo_v1_rechazado` y
`test_t047_de_la_004_archivo_v1_deja_intacta_la_partida_actual` (`tests/test_guardado_mapa.py`); y
`test_h4_1_fr420_mismos_resumenes_tras_guardar_y_cargar`, `test_h4_2_fr420_se_puede_seguir_jugando_tras_cargar`,
`test_h4_3_apendiceB_caso6_fr421_archivo_de_la_primera_parte`, `test_h4_k_guardado_se_conserva_al_cargar` y
`test_h4_fr421_el_programa_no_se_cae` (`tests/test_linea_tiempo_guardado.py`).

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
5 000). *Qué mide M3*: la memoria de la línea en ejecución, no el archivo guardado. Por cada punto de control
`medir_memoria` llama a `GuardadoBinario.guardar` con la partida y las salas de ese punto, en un archivo propio (cada
uno con su cabecera), y suma los bytes que devuelve; a eso le suma, por cada acción, su línea de texto del log, un
salto de línea y 4 bytes del tiempo. Las cargas y las fichas se cuentan, pero no se pesan. *Archivo versión 2 real*:
medición aparte con un guion no versionado (misma partida sintética de M3, K = 20, guardada con
`ServicioGuardado.guardar` y medida con `os.path.getsize`): 24 145 bytes con 100 acciones, 180 250 con 1 000 y
874 050 con 5 000 (la misma partida sin la línea ocupa 3 367 bytes). Es del mismo orden que M3 en el `--bench` del
17/11 (21 474, 186 039 y 917 439 bytes; la tabla de M1 trae 901 877 de una corrida anterior): con 5 000 acciones el
archivo pesa 43 389 bytes menos (5 %), y con 100 acciones, 2 671 más.
**Supuesto: `--replay` sin `--hasta`.** Es headless (sin ventana ni línea de comandos) y no alimenta la línea de tiempo,
porque `ServicioReplay` ejecuta las acciones con `ServicioAccionJugador` directo. Por eso `historia` no es alcanzable en ese
modo y no se agregó código para él (YAGNI). Si se llamara a pesar de todo, el contexto del replay tiene una línea con solo
el punto 0 y respondería un estado del instante 0, que engaña; la defensa mínima, que **no** se aplicó por ser inalcanzable,
es `contexto.linea = None` en `ServicioReplay.reproducir`, para que salga el mensaje claro «Esta partida no tiene línea de
tiempo que consultar». Anotado como supuesto en la spec de la 004 (Suposiciones).

**HUD con mensajes largos y vida mayor que vida_max.** Un mensaje de 342 px en un ancho útil de 334 no se arregla con más holgura (achicaría la letra de todos): `HudJuego._mensajes` ya lo recorta con `recortar_a_ancho` y «...», así que no cambió la vista; `barra_de_vida` ya limitaba la proporción a 1.0 y ahora lo cubren dos pruebas (ratas de cripta-01: vida 12, vida_max 8).

**Tamaño de letra del HUD.** Se mide con los nombres del catálogo de la Parte II (`MENSAJES_PARA_MEDIR` incluye Espectro acechador y Carcelero errante): con el catálogo nuevo el peor mensaje (342 px) ya no cabe en 334 a 17 px y el tamaño baja a 15, así que la vista no recorta mensajes reales; el recorte con «...» queda como protección. `test_vista_hud` pasa con el catálogo nuevo y con el viejo.

#### §5.5 (subsección) Banco de pruebas de la línea de tiempo (`--bench`)

`Service/BenchLineaTiempo.py` (con `Service/Cronometro.py` y `ResultadoBenchDTO`, igual que
`Service/BenchInventario.py`) corre sin ventana y con cargas **sintéticas** (Principio VI): una cripta en
cuadrícula de 4 × 4 salas, dos enemigos errantes inofensivos y un jugador que no puede morir, que juega una
secuencia fija (esperar y dar la vuelta a una manzana de salas) con la semilla 2026. Cada partida de 5 000 acciones se
juega una vez por K y la comparten M1, M2 y M3: como la partida es determinista, la historia de las primeras n
acciones es la de una partida de n. `BenchInventario.medir()` devuelve también este grupo (una línea), y así `--bench`
lo muestra sin tocar `Service/ServicioBench.py` (cambio registrado en el plan, NFR-401).

Tabla completa: [bench-tabla.txt](specs/004-linea-tiempo/bench-tabla.txt) (`python -m Service.ServicioBench`, 74 s,
Windows 11 Pro). Los tiempos son medianas y dependen de la máquina; los conteos son reproducibles.

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

**Tamaño real del archivo versión 2 (K = 20).** Con el guardado con línea ya implementado (T044 a T048), el archivo de
una partida de 5 000 acciones pesa 874 050 bytes (0,87 MB; medición aparte con un guion no versionado, ver «Memoria»),
contra los 917 439 bytes que estima M3 en el `--bench` del 17/11. La diferencia es de un 5 % (el archivo es más chico)
y no cambia la elección de
K = 20, que se hizo por el tiempo de `historia` (M1). Solo se midió el archivo con K = 20.

### Contador de daño recibido (`ActorBase.danio_recibido`, para «ir a» de la 002)

Cambio a la primera entrega (Principio III), propuesto por el integrante 3 y **revisado por el integrante 1 (Marco) y aprobado**, con los
ajustes que se aplicaron en el commit `06b1eff`: el campo y su explicación van como comentario de una línea y no como docstring
(`Logic/ActorBase.py`); una prueba con la Regeneración real dentro de un paso del motor (`test_la_regeneracion_real_dentro_de_un_paso_del_motor_no_lo_sube`);
los textos del plan y de `tasks.md` (T110A) corregidos; «tres sitios» que llaman a `Recibir_Dannio` (eran «cuatro» en el texto); una prueba de
guardar y cargar (`test_guardar_y_cargar_no_cambian_el_contador`); y, en `tests/test_linea_tiempo_guardado.py`, la comparación con el valor de antes
(`acciones_antes`).

**Problema.** «Ir a» debe detenerse cuando el jugador recibe daño (spec 002 FR-258 c, §3.4). Comparar `jugador.vida` antes y
después de un paso no basta: una Regeneración (`Logic/Efectos.py`, +vida por pulso) puede devolver la vida dentro del mismo
paso y ocultar el daño (R-I3-7).

**Alternativas.** (1) Comparar la vida y detenerse también si hay Regeneración activa, sin tocar Logic: no cambia la primera
entrega, pero detiene el viaje tras cada paso aunque no haya daño. (2) Contar los mensajes de daño del buffer: el buffer
guarda solo los últimos 20, no tiene contador total y el texto de la trampa no nombra a la víctima. (3) Un contador entero
en el único punto por el que pasa todo daño: **elegida**.

**Antes.**
```python
def Recibir_Dannio(self, Cant):
    if Cant <= 0:
        return
    self._registrar_vida()
    ...
```
**Después** (`Logic/ActorBase.py`: campo con un comentario de una línea en `__init__` y una línea en `Recibir_Dannio`):
```python
# daño recibido: suma de los daños finales > 0; no va al historial ni a PartidaGuardada
self.danio_recibido: int = 0                 # en __init__

def Recibir_Dannio(self, Cant):
    if Cant <= 0:
        return
    self.danio_recibido += Cant              # la línea nueva
    self._registrar_vida()
    ...
```

**Por qué es seguro.** `Cant` ya es el daño final en los tres sitios que llaman a `Recibir_Dannio`: el ataque
(`Logic/motorJuego.py:256`, `max(1, ataque + azar - defensa_efectiva)`), la trampa (`:289`, `dano_al_activarse()`) y el veneno
(`Logic/Efectos.py:33`, su valor por pulso); la defensa se resta antes de llamar, no dentro. La guarda `Cant <= 0` sigue
primero, así que un daño de 0 no sube el contador. El contador **no** va al historial (deshacer con un pergamino no lo baja,
así que el pergamino no parece daño en la comparación de un paso) ni a `PartidaGuardada` (solo importa la diferencia dentro
de un paso; cargar una partida interrumpe el viaje). Los enemigos también lo tienen porque comparten `ActorBase`; nadie lo
lee. Costo: O(1). Pruebas: `tests/test_danio_recibido.py`.

**Nota sobre las pruebas.** La mutación que quita `Evento_pendiente` del daño solo se nota contando los cambios del intervalo, y el
helper de la prueba lee atributos privados del historial (se rompe si cambia el buffer).

**Prueba con Regeneración real y mutación.** `test_h7_5_a34_fr258_dano_compensado_por_regeneracion_detiene` (`tests/test_servicio_ir_a.py`) pone una
`Regeneracion` real (+20, con su primer pulso a los 95) y un guardián que golpea a los 90 dentro de un paso: la vida queda igual
(el pulso la devuelve al máximo), `danio_recibido` sube y el viaje se detiene con `DANO`. Su contraparte,
`test_fr258_regeneracion_activa_sin_dano_el_viaje_sigue`, con Regeneración activa y sin daño, no lo detiene (el contador no sube
al curarse). Se comprobó con una mutación: si `ServicioIrA` compara `jugador.vida` en lugar de `danio_recibido`, la primera falla.
T110A sigue sin marcarse: falta la revisión del integrante 1.

### Viaje automático «ir a» (002, integrante 3)

Spec FR-250 a FR-264, NFR-250 y NFR-251; plan en `specs/002-niebla-ir-a/plan.md` («Viaje automático «ir a»»). Todo lo de abajo
existe en el código y lo cubren las pruebas que se nombran.

**1. Tres piezas, y el viaje viaja en un DTO.** *Problema:* decidir cada paso y cuándo parar sin reimplementar el movimiento.
*Decisión:* «ir a» es una orden que se descompone en movimientos ordinarios. `Logic/ViajeAutomatico.py` (funciones puras, sin I/O:
`resolver_destino`, `decidir_paso`, `motivos_de_parada`), `Service/ServicioIrA.py` (`iniciar(contexto, nombre)` y
`dar_paso(contexto, viaje)`; no guarda el viaje) y `DTO/ViajeDTO.py` (`ViajeDTO(destino, nombre_destino, pasos_dados,
acciones_esperadas)`, `InicioViajeDTO`, `PasoViajeDTO` y los motivos de parada). Cada paso es un `mover` que pasa por
`ServicioLineaTiempo.ejecutar`, así que gasta su tiempo, deja correr los eventos, se anota en `partida.log` y en la línea de
tiempo, y cuenta como acción (FR-254, FR-263, FR-264). *Alternativa descartada:* guardar el estado del viaje en el servicio;
con un `ViajeDTO` que viaja de una llamada a la siguiente, cargar una partida o leer un pergamino no pueden dejar un viaje
«a medias» dentro del servicio. *Pruebas:* `tests/test_servicio_ir_a.py`, `tests/test_viaje_logica.py`.

**2. `dar_paso(contexto, viaje)` y `acciones_esperadas`: así se detecta el pergamino.** El `ViajeDTO` guarda cuántas acciones
llevaba el jugador tras el último paso. Si `jugador.acciones` es otro valor (un pergamino la bajó en 1, o hubo otra orden), el
paso se detiene con `INTERRUMPIDO` sin tocar nada (FR-262). Con solo el destino no habría cómo saberlo. Después: partida
terminada → `TERMINADA`; sin ruta → `SIN_RUTA` sin tiempo; el `mover` rechazado → `PASO_RECHAZADO`; y, con el paso dado,
`motivos_de_parada`. *Pruebas:* `test_h7_7_apendiceB_caso6_fr222_fr262_pergamino_revierte_solo_el_ultimo_paso`
(`tests/test_ir_a_pergamino.py`), `test_dar_paso_con_la_partida_cambiada_por_fuera_para_con_interrumpido`.

**3. Búsqueda desde cero en cada paso.** *Problema:* la ruta debe usar solo lo que el jugador conoce y recalcularse antes de cada
paso (FR-252, FR-255). *Decisión:* `paso_desde_cero(grafo, destino, sala_actual, None)` sobre `GrafoMapaConocido`, sin guardar
ninguna búsqueda entre pasos (la decisión es idéntica a un cálculo desde cero, SC-251). *Alternativa descartada:* reutilizar
`BusquedaCostoMinimo` con `observador_rutas`; **no se implementó ni se midió**, porque el paso cabe en 5 ms (T122 la manda medir
solo si no cabe). *Pruebas:* `test_sc251_cada_paso_igual_a_paso_desde_cero`, `test_sc251_fr255_cada_decision_igual_a_paso_desde_cero`.

**4. El grafo se arma una vez por viaje y de nuevo tras cargar.** El plan lo armaba en cada paso. `ServicioIrA` guarda solo un
caché de un valor: el `GrafoMapaConocido` y el mapa del que salió. `iniciar` lo borra (un grafo por viaje) y `dar_paso` lo
rehace si `contexto.motor.mapa` es otro objeto, que es lo que pasa después de cargar una partida (hay un `Motor` nuevo).
El grafo lee el mapa en vivo, así que reutilizarlo entre pasos no cambia la decisión. *Pruebas:* `test_el_grafo_se_arma_una_vez_por_viaje`,
`test_viaje_tras_cargar_toma_el_mapa_del_motor_nuevo_y_arma_un_grafo_nuevo` (`tests/test_servicio_ir_a.py`).

**5. La dirección del paso sale de `Mazmorra.salida` (D-1) y de la cara recordada.** `paso_desde_cero` devuelve `(vecina,
costo)`, no la dirección. `decidir_paso` toma la primera dirección, por número, cuya salida lleva a la vecina, tiene ese costo y
cuya cara de origen se recuerda abierta (`mapa.estado_cara == ABIERTA`); así, con dos salidas a la misma vecina (H-4), no elige una
cara recordada cerrada. Solo mira la sala actual, que está explorada. *Pruebas:* `test_fr252_direccion_de_menor_numero_con_ese_costo`,
`test_fr252_h4_cara_recordada_cerrada_de_menor_direccion_no_se_elige`.

**6. Decisiones I3-4, I3-5 e I3-7.** *I3-4:* «ir a» desde una sala con enemigos vivos da el primer paso; solo se detiene al
**entrar** a una sala con enemigos (`test_i3_4_la_sala_de_partida_con_enemigos_permite_el_primer_paso`). *I3-5:* el comentario
`# ir a <sala>` se escribe justo después del primer paso aceptado, con el nombre real de la sala destino y solo si la bitácora
existe; una orden rechazada o sin pasos no escribe nada (`test_h7_8_a36_fr261_log_con_tres_movimientos_y_un_comentario`,
`test_fr261_orden_sin_pasos_no_se_registra`, `test_el_comentario_se_escribe_una_sola_vez_por_orden`). *I3-7:* `INTERRUMPIDO`,
`TERMINADA` y `PASO_RECHAZADO` son motivos internos, no mensajes de la spec; `TERMINADA` sale junto a `DANO` o `LLEGO`, en el
orden fijo `LLEGO`, `ENEMIGOS`, `DANO`, `TERMINADA` (`test_i3_7_fr258_terminada_junto_con_dano_o_llego`,
`test_i3_6_fr258_paso_rechazado_para_sin_tiempo_ni_comentario`).

**7. Límites de H-3 (I3-9).** El nombre se compara con `strip().casefold()` en los dos lados (`MapaConocido.buscar_exploradas`). No se
quitan tildes (`sotano` no encuentra `Sótano`; es el comportamiento de `casefold`, no hay una prueba que lo fije) ni se colapsan
espacios internos: el comando de la interfaz conserva los espacios internos del nombre (`test_solo_ir_a_con_un_destino_es_el_comando`).
Si el grupo quiere tildes o espacios, el cambio es de una línea en `buscar_exploradas` (integrante 2).

**8. Limitación conocida: los comentarios `# ir a` tras cargar una partida.** Al cargar, `BitacoraReplayIO.continuar_desde` copia al log nuevo solo las acciones, no los comentarios (`ServicioGuardado` lo llama con la cantidad de acciones). Por eso el log nuevo trae únicamente los `# ir a <sala>` de las órdenes dadas desde la carga; los anteriores quedan en el log previo. No afecta al replay: los comentarios son informativos y `--replay` usa solo las acciones.

**9. H-2, opción A: la interfaz no ve ids de salas no exploradas.** *Problema:* `EstadoJuegoDTO.sala.salidas[d].sala_destino` traía
el id real de las salas avistadas y `sala_salida` el de la salida de la cripta (FR-204, FR-217). *Decisión:* `ArmadorEstado` pone
`SIN_EXPLORAR = -1` (constante en `DTO/EstadoJuegoDTO.py`) en cada salida hacia una sala no explorada y deja `sala_salida = None`
mientras esa sala no esté explorada, con `mapa.es_explorada` (O(1) por salida; no usa `a_dto()`). La vista no cambia: `-1` no coincide con
ningún id ni con `sala_salida`. *Costo conocido:* la puerta final no se distingue hasta explorar la sala de salida. *Alternativas descartadas*
(plan, tabla del H-2): `sala_destino: int | None`, un campo nuevo con los destinos conocidos, o que `ArmadorEstado` calcule los hechos que
la vista compara. *Pruebas:* `tests/test_estado_sin_filtrar.py` (200 acciones con y sin antorcha), y se ajustaron tres pruebas viejas
que leían ids reales del estado (`test_servicios.py`, `test_grabadores_linea.py`, `test_dto_terreno.py`).

**10. Interfaz de «ir a»: supuestos míos (la spec no los fija).** La spec dice que el viaje es paso a paso y que se muestra el motivo
de parada (FR-260); el resto lo decidí yo, y se puede cambiar:
- *Ritmo:* un paso cada `PASO_VIAJE_MS` = 350 ms (`UIController/ControladorPygame.py`), medidos con el reloj del controlador,
  en `avanzar_viaje()`, que el bucle principal llama una vez por cuadro. El primer paso sale en el primer cuadro.
- *Corte:* cualquier tecla, clic o rueda corta el viaje y además se ejecuta como siempre (`Z` espera, `D` mueve); **Esc solo corta el
  viaje y no abre la pausa**. Sin viaje, Esc vuelve a pedir la pausa. El backend descarta el viaje (`cancelar_viaje`) y anota
  «Viaje interrumpido.».
- *Rechazos:* una orden rechazada (destino no válido, ambiguo, «ya estás aquí», comando vacío) sale como aviso, como los demás
  comandos, sin tiempo ni bitácora. Un destino inexistente, avistado o desconocido da el **mismo** mensaje (FR-251), y no se puede
  distinguir uno de otro; ambiguo y «ya estás aquí» tienen el suyo.
- *Motivos de parada:* `ControladorBackend.dar_paso_viaje` anota un mensaje por motivo («Llegaste a ...», «Viaje detenido: hay
  enemigos.», «...recibiste daño.», «...sin ruta conocida a ...», y «...no se pudo dar el paso.» para el `mover` rechazado) con
  `ServicioIrA.anotar`, que los agrega al buffer de mensajes de la partida viva (el panel de mensajes). No son parte del estado del
  motor, así que `--replay` no los reproduce. Son cortos a propósito y `test_vista_hud` los mide con los nombres de sala reales.
- *Pruebas de punta a punta:* `tests/test_ir_a_interfaz.py` (`ControladorPygame` y `VistaPygame` reales, partida real de 5 × 5 salas).
  Esas pruebas arrancan con `forzar=True` porque desde T054 `iniciar` verifica la resolubilidad y la fuente de la cuadrícula no trae llaves.

**11. Banco del paso (NFR-250, NFR-251, SC-252).** `Logic/BenchViaje.py` mide, con el mapa conocido completo y desde la esquina hacia la sala
opuesta, V1 armar el grafo, V2 un paso con el grafo armado y V3 un paso completo (grafo nuevo + `decidir_paso`), con cuadrículas de 100,
1 024 y 10 000 salas y una de 15 × 20 = 300 salas, el tamaño de cripta-06. **cripta-06 ya está en el paquete local** (la trajo el merge con el paquete de Derek, `ecb78e7`): `--bench` la mide sola
(`ServicioBench`), desde su sala inicial hacia su salida, y se midió además la sintética de 300 salas (commit `b995a97`: V1 0.160 ms, V2 0.002 ms y
V3 **0.164 ms** contra 5 ms con la cripta-06 real; cumple NFR-250 y SC-252). **cripta-06 no es representativa del peor caso:** de su entrada a su salida no hay
camino con puertas cerradas (el banco anota «decisión None» en V2, así que V3 mide casi solo armar el grafo); la sintética de 300 salas, con
camino largo y todas las salas conocidas, es la medida que sí exige el paso. Resultados de la sintética
(mediana): **300 salas, V3 = 1.001 ms contra 5 ms: cumple NFR-250 y SC-252** (V1 0.199 ms, V2 0.756 ms); 1 024 salas, V3 = 3.763 ms
(por debajo de 5 ms, con poco margen; evidencia, no criterio); 10 000 salas, 50.363 ms. La tabla completa está en
`specs/002-niebla-ir-a/bench-viaje-2026-11-17.txt`; se midió en otra máquina (Ryzen 4600G, 15 GB, Python 3.15.0) que la tabla del
integrante 2 del 15/11 (Ryzen 5 5500), así que los tiempos de las dos no son comparables fila por fila. Complejidad: V1 O(S + E) (la primera
`entradas` arma el índice inverso); un paso es una búsqueda de costo mínimo sobre las salas exploradas. *Pruebas:* `tests/test_bench_viaje.py`.

**12. Los mensajes de parada no van a `partida.log`.** «Llegaste a …», «Viaje detenido: hay enemigos.», «Viaje detenido: recibiste daño.»,
«Viaje detenido: sin ruta conocida a …» y «Viaje interrumpido.» los arma el backend (`ControladorBackend._textos_de_parada`, líneas 360 a 374,
y `cancelar_viaje`, línea 356) y los escribe en el panel de mensajes con `ServicioIrA.anotar` (`Service/ServicioIrA.py:28-29`:
`contexto.mensajes.agregar(...)`, con el reloj del momento). Lo único que `ServicioIrA` escribe en la bitácora es el comentario `# ir a <sala>`
(`Service/ServicioIrA.py:49`) y las acciones `mover` de cada paso. Por eso `--replay` no repite esos mensajes: el estado que reproduce
(reloj, sala, jugador, mapa) es el mismo, porque depende solo de las acciones (`test_el_log_trae_el_comentario_y_se_reproduce_igual`,
`test_h7_8_a36_fr261_sc253_replay_da_la_misma_partida_y_el_mismo_mapa`), pero el panel de mensajes de un replay no dice por qué se detuvo
un viaje.

### Comando `mapa` de la 002 (interfaz)

- *Nombre y alcance.* La spec pide «un comando para ver el mapa conocido» (FR-219) sin fijar el nombre: elegí `mapa` (sin argumentos), en la
  misma línea de comandos que `historia`. Repetirlo lo cierra; también lo cierran `Esc` (antes que la pausa) y cualquier acción.
- *Qué lee.* `ControladorBackend.ver_mapa()` devuelve `motor.mapa.a_dto()` y nada más: no pasa por servicios, no toca Data, no consume tiempo,
  no es una acción, no se anota en `partida.log` ni en la línea de tiempo, no toca el historial y no descarta un viaje en curso (FR-220).
  `PantallaDTO.mapa` (campo final con valor por defecto) lleva el `MapaConocidoDTO` a la vista, que solo dibuja.
- *Dibujo* (`View/MapaJuego.py`). El DTO no trae coordenadas: cada sala se pone junto a la que la nombra según N, S, E y O, a partir de la sala
  actual, y una sala que no cabe junto a su vecina se corre en la misma dirección. Una salida hacia una sala avistada es una celda hueca sin
  id ni nombre; cada conexión lleva el color de la puerta recordada. La celda va de 56 a 16 px; con 44 px o más se escriben nombres y costos.
  Si ni a 16 px cabe, se recorta alrededor de la sala actual y el panel lo dice (300 salas en cuadrícula caben enteras a unos 34 px).
- *Supuesto: con la partida terminada el comando no está disponible*, igual que `historia`. T048 punto 1 lo pide «también con la partida
  terminada», pero FR-219 y FR-220 no lo exigen. Al terminar, `ControladorPygame` pasa a la pantalla de victoria o derrota (o ignora todos los eventos
  durante la demora del fin) y esa pantalla no tiene línea de comandos. Habilitar `mapa` ahí obliga a darle teclas, un campo en `PantallaDTO`
  y un dibujo a las pantallas de fin, es decir, tocar la navegación de victoria y derrota. Si el grupo lo quiere, el cambio es de esas pantallas
  y no de `ver_mapa`, que no mira si la partida terminó (`test_con_la_partida_terminada_el_comando_no_esta_disponible_pero_ver_mapa_no_falla`).
- *Pruebas:* `tests/test_comando_mapa.py`, con dos pruebas que parchean `ver_mapa` para que anote en el log o gaste tiempo y comprueban que la
  comparación del reloj, las acciones, `partida.log`, la línea, el historial y el mapa lo detecta (la mutación de FR-220).

### Reporte de resolubilidad en la interfaz (003, T055)

El reporte llega a la vista como líneas de texto (`PantallaDTO.reporte_resolubilidad`, con el formato de `TextoResolubilidad.lineas_reporte`, FR-315) y un indicador de advertencia. `ControladorPygame` lo toma de `backend.resolubilidad()` justo después de iniciar: en una partida nueva se muestra en un panel hasta la primera acción que gasta tiempo (una acción rechazada no lo oculta), como advertencia si no es «resoluble» (`--forzar`, FR-312); si la partida no inicia (FR-311) el reporte completo se ve en la pantalla del nombre; al cargar o en `--replay` no hay reporte (FR-301). El aviso del menú no se toca: el mensaje de `ErrorPartidaNoIniciada` es corto y cabe en sus 2 líneas, pero no trae el ciclo, por eso el reporte va en un panel aparte. La fuente del juego no tiene la flecha «→» y la vista la dibuja como «->». Si un reporte no cabe en el panel (12 líneas en el menú, un ciclo con sus dependientes ocupa 12), se corta con «... y N líneas más» y se remite a `--verificar`, que escribe todo.

### La escena muestra el costo de cada salida y el comportamiento del enemigo (001, T041, integrante 3)

Cambia código de la primera entrega, así que va con su justificación (Principio III): `View/EscenaJuego.py` (y cuatro constantes de
`View/Componentes.py`: `COMPORTAMIENTO_CAZADOR`, `MARCADOR_CAZADOR`, `MARCADOR_SEPARACION`, `COSTO_DISTANCIA`). Fila en la tabla de cambios a P1
de `specs/001-terreno-cazador/plan.md`. Lo exigen FR-116 (el costo junto a cada salida, también las cerradas) y FR-117 (el comportamiento en
texto junto al nombre del enemigo y un marcador solo para el cazador); sin tocar la escena no hay dónde dibujarlos.

| | Antes | Después |
|---|---|---|
| Salidas | la escena dibujaba puertas y nada más | además, junto a cada puerta con salida, su costo (`SalidaDTO.costo`, ya igualado por Lógica; 100 si ninguna cara lo declara), también en las cerradas |
| Ficha del enemigo | `_ficha_de_actor` dibujaba solo el nombre | «Nombre (comportamiento)»; el cazador, un rombo rojo dibujado con `pygame.draw.polygon` a la izquierda del texto, ambos centrados juntos. Esa lógica vive en el método nuevo `_nombre_de_ficha` y en la función pura `rombo_del_marcador`, no en `_ficha_de_actor` |
| Reparto y medidas | `repartir_escena` y `c.SUELO`, `PASILLOS`, `HUD_PANELES` | iguales: no se movió ninguno |
| Código de P1 que cambia | — | `dibujar`: +1 línea (`self._costos(...)`). `_ficha_de_actor`: la llamada original a `texto_sombreado` del nombre se cambia por `self._nombre_de_ficha(...)` (−2 +1 líneas) |
| Código nuevo | — | `etiquetas_de_costo(estado, marcos, fuente)` (dirección, texto y `Rect`; el `Rect` es el del texto sin sombra, lo pintado ocupa `rect.inflate(2, 2)`), `posicion_de_costo`, `lleva_marcador`, `texto_de_ficha`, `rombo_del_marcador`, y los métodos `_costos` (dibuja en el `Rect` de `etiquetas_de_costo`) y `_nombre_de_ficha` |

- *El marcador sale del comportamiento* (`comportamiento == "cazador"`), nunca del id (`ent_sabueso_oseo`) ni del nombre (Principio VI).
- *Limitación del ancho de la ficha.* El texto se recorta dentro del ancho que ya reservaba el reparto; si no cabe, se recorta el nombre y se
  conserva el comportamiento (con 12 enemigos solo queda «(comportamiento)»). Ensanchar `ancho_ficha` movería el reparto, y no se hizo.
- *Limitación conocida (sin cambio de código).* `fondo_final` solo trae pintada la puerta norte (`MARCOS_OSCURECIBLES[2] = False` en `View/Componentes.py`), así que el costo de una salida S, E u O abierta en la sala de salida puede quedar sin puerta visible a su lado. El costo se dibuja igual junto al marco de esa dirección (FR-116).
- *Máximo de costo.* La spec no fija un máximo (FR-122 solo pide un entero ≥ 1). Las pruebas cubren hasta 5 dígitos (`DIGITOS_PROBADOS`, decisión nuestra, no de la spec) para pantalla, HUD y suelo, y 4 dígitos para el choque con el protagonista. Medido (sin cambiar código): con 6 o más dígitos las etiquetas E y O de `fondo_inicial` entran al suelo (`c.SUELO`); en `fondo_final`, desde 9 dígitos; `fondo_regular` aguanta 9.
- *Reserva del protagonista y lo que se pinta.* `JUGADOR_OCUPA` (120 × 130) es la reserva con la que `repartir_escena` coloca enemigos y objetos, más ancha que lo pintado (sprite 91 × 90, barra 96 × 14, nombre 60 × 19 en la medida). En `fondo_inicial`, cuando el protagonista entra por E u O, la etiqueta de esa misma puerta (inflada 2 px por la sombra) pisa la reserva 3 × 19 px (E) y 5 × 19 px (O) con 3 dígitos, 12 y 14 con 4, y 21 y 23 con 5. Lo pintado no se toca con 3 y 4 dígitos; con 5 la etiqueta pisa el sprite 7 × 19 px (E) y 8 × 19 px (O) (barra y nombre, nunca). N, S, `fondo_regular` y `fondo_final` no se tocan en ningún caso, con 0, 6 o 12 enemigos. Por eso la prueba de choques mide contra lo pintado (sprite, barra y nombre) con costos de 4 dígitos. **Limitación conocida, sin cambio de código:** con costos de 5 dígitos, en `fondo_inicial`, la etiqueta de la puerta por la que se entra tapa unos píxeles del borde del sprite (7 × 19 px en E, 8 × 19 px en O), y con 6 o más dígitos además entra al suelo en esas dos puertas. Como la spec no fija un máximo, es una limitación conocida y no un incumplimiento de FR-116 (el costo se muestra junto a cada salida en todos los casos).
- *Pruebas:* `tests/test_vista_terreno.py` (Vista real, `SDL_VIDEODRIVER=dummy`), con la lista de etiquetas probada por texto y `Rect`, no por píxeles.
