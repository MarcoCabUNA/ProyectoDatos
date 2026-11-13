# Especificación: Niebla de guerra, mapa conocido y viaje automático «ir a»

**Feature**: `002-niebla-ir-a`

**Creada**: 2026-11-12

**Estado**: Borrador (parte del integrante 2: mapa conocido y antorcha; parte del integrante 3: «ir a», FR-250 a FR-264, historias 6 y 7, ya escrita por el integrante 3)

**Fuente**: Cripta - Parte II §3.3, §3.4, §3.5, §3.6, §5.3, §6.1, §6.3, §7.3 y Apéndice B «Niebla de guerra e «ir a»»; Primer Proyecto (P1) §2.4 (enemigos dormidos), §2.7 (antorcha), §2.11 (pergamino de retroceso), §4.2 (precarga) y §5.2; feature `001-terreno-cazador` (FR-101, FR-108 y FR-122)

**Constitución**: v1.2.0 · Requisitos con prefijo FR-2xx (Principio IX)

**Reparto de la numeración**: esta spec la comparten dos integrantes. El mapa conocido y la antorcha usan
FR-201 a FR-249, NFR-201 a NFR-249 y SC-201 a SC-249. El rango 250 a 299 (FR, NFR y SC) queda reservado para
el viaje automático «ir a» (§3.4), que el integrante 3 ya escribió en su propio commit (FR-250 a FR-264,
historias 6 y 7).

**Fuera de alcance**: cómo se dibuja el mapa en la interfaz (integrante 3); el costo de las salidas y el
cazador (feature `001-terreno-cazador`); la línea de tiempo en sí (feature `004-linea-tiempo`, que usa el mapa
conocido en su FR-405 y lo conserva al guardar por su FR-420); la verificación de resolubilidad (feature
`003-resolubilidad`), que usa el esqueleto completo y no el mapa conocido, y cuyo reporte se muestra según la
excepción de FR-217.

**Entrada**: Descripción del usuario: "Niebla de guerra y mapa conocido de Cripta II (parte del integrante 2).
Tres estados por sala (explorada, avistada, desconocida); memoria de puertas según la última observación;
antorcha que explora las vecinas sin activar enemigos ni trampas; separación entre el esqueleto descargado y el
conocimiento del jugador; el conocimiento se guarda, se revierte con el pergamino y forma parte de la línea de
tiempo; comando para ver el mapa conocido; determinismo con --replay; consultas frecuentes de costo
independiente del tamaño; --bench. Requisitos FR-201 a FR-249. No nombrar estructuras de datos, clases ni
módulos."

> Este archivo contiene reglas del juego, historias, escenarios y requisitos. No nombra estructuras
> de datos, clases ni módulos: eso va en `plan.md` (Principio IX). Se confirma con un commit antes
> de cualquier código de esta feature.

## Convenciones de los ejemplos

- **Salida**: conexión dirigida de una sala a otra, con un costo (feature 001). Toda salida tiene una puerta,
  abierta o cerrada (P1); en una salida con vuelta, la puerta tiene una cara en cada sala (ver «Puerta»).
  Una «salida sin vuelta» es una salida de A a B sin una salida de B a A.
- **Vecina** de una sala S: sala destino de alguna salida de S, abierta o cerrada.
- **Puerta**: la de una salida. La puerta de una salida con vuelta tiene dos caras, una en cada una de las dos
  salas que conecta. Normalmente las dos caras tienen el mismo estado real, pero pueden diferir según la
  primera parte: si ninguna declara llave y solo una está cerrada, o si las dos declaran llave (la misma o
  distintas) con distinto estado, cada cara se rige por lo suyo (003 FR-302). Una salida sin vuelta solo existe como salida de la sala de la que
  sale, así que su puerta solo tiene cara en esa sala. El estado real de cada cara lo fija P1 (por ejemplo,
  abierta o cerrada; algunas se cierran solas).
- **Observar una puerta**: ver el estado real de cada una de sus caras en un momento, desde una sala donde la
  puerta tiene una cara (FR-207).
- **Salida recordada abierta**: salida cuya cara en la sala de la que sale el mapa recuerda abierta (FR-208);
  el estado recordado de la otra cara no cuenta. Es lo que usa FR-225.
- **Puerta «sin observar»**: puerta de una sala explorada que el jugador nunca ha observado; su estado es
  desconocido para el jugador (FR-212).
- **Mapa conocido**: todo lo que el jugador sabe del mapa: el estado de cada sala para el jugador y el estado
  recordado de cada cara de cada puerta observada.
- **Entrar a una sala**: llegar a ella mediante un movimiento del jugador. La sala inicial cuenta como
  explorada desde el instante 0 sin necesidad de entrar.
- Los nombres de salas (A, B, C…) y los instantes (t) de los ejemplos son ilustrativos; no corresponden a
  ninguna cripta concreta (Principio VI).

## Clarificaciones

### Sesión 2026-11-12

- P: Al explorar una vecina con la antorcha, si el jugador nunca estuvo en ella, ¿conoce el estado de sus
  puertas? → R: No. Las puertas de esa vecina que el jugador nunca observó figuran «sin observar» (estado
  desconocido) hasta que esté en una sala donde esa puerta tenga una cara; la puerta de la salida por la que es
  vecina sí se observa, porque el jugador está en la otra sala (FR-207). Una puerta «sin observar» no es una
  puerta recordada abierta (dato que usará «ir a», FR-252) (FR-205, FR-212, FR-219).
- P: Encender la antorcha estando ya en una sala, ¿explora las vecinas de esa sala o solo tiene efecto al
  entrar a la siguiente? → R: Solo tiene efecto al entrar a una sala (§3.3: «al entrar a una sala»); encenderla
  estando ya en una sala no cambia el mapa conocido (FR-215).
- P: Una sala X que no es destino de ninguna salida de una sala explorada, pero tiene una salida sin vuelta
  hacia una sala explorada A, ¿queda avistada, y el jugador observa la puerta de esa salida desde A? → R: No a
  ambas: X sigue desconocida. En la primera parte, una puerta con vuelta tiene una cara en cada una de las dos
  salas que conecta y es la misma puerta; una salida sin vuelta solo existe como salida de la sala de la que
  sale. El jugador observa las puertas que tienen una cara en la sala donde está: una puerta con vuelta se
  observa desde cualquiera de sus dos salas (§3.3) y una salida sin vuelta solo desde la sala de la que sale.
  Si se observara desde la otra sala, el jugador sabría que existe una sala desconocida, lo que contradice
  FR-206 *(decisión del grupo: observar la salida sin vuelta solo desde la sala de la que sale, para no
  contradecir FR-206)* (FR-204, FR-207).
- P: ¿Ver el mapa conocido consume tiempo o cuenta como acción? → R: No; es una consulta, como `historia` en la
  feature 004: no consume tiempo, no es acción, no se registra en `partida.log` y no modifica el historial de
  retroceso (FR-220).
- P: Si dos salidas de salas exploradas llevan a la misma sala avistada, ¿sabe el jugador que es la misma sala?
  → R: No. Cada salida hacia una sala avistada se muestra por separado, como «sala sin explorar detrás de esta
  salida», sin identificador; que dos salidas llevan a la misma sala solo se sabe al explorarla *(decisión del
  grupo)* (FR-204, FR-219).

### Sesión 2026-11-13

- P: ¿Qué debe ofrecer exactamente el mapa conocido a «ir a» para que la ruta coincida con FR-252 y FR-253?
  *(revisión cruzada del integrante 1)* → R: Para cada sala explorada, sus salidas hacia otras salas exploradas
  cuya puerta el mapa recuerda abierta, cada una con su costo igualado según 001 FR-101; una puerta «sin
  observar» (FR-212) no cuenta y una salida hacia una sala avistada o desconocida tampoco. Cada sala se
  identifica por su identificador real, para que el desempate por menor identificador de FR-253 dé el mismo
  resultado que la búsqueda del cazador aplicada a ese mismo conjunto de salas y salidas. Cómo se ofrece lo
  decide el plan (FR-225).
- P: ¿Qué costo conoce y ve el jugador en una salida cuya puerta declara el costo en una sola cara o en
  ninguna? *(revisión cruzada del integrante 1)* → R: El costo igualado según 001 FR-101: el mismo en los dos
  sentidos aunque solo una cara lo declare, y 100 si ninguna lo declara; nunca el declarado por una sola cara
  cuando difiere del igualado. Si las dos caras declaran costos distintos, la partida no inicia (001 FR-122)
  (FR-205, FR-219).
- P: El reporte de resolubilidad (003 FR-313) puede nombrar salas, puertas o ubicaciones de llaves que el
  jugador no conoce; ¿contradice FR-217? *(acuerdo con el integrante 3, dueña de la interfaz)* → R: Es una
  excepción explícita a FR-217. §3.3 dice que la vista solo muestra el conocimiento del jugador, pero §7.3 exige
  ver el reporte al iniciar, y el reporte de §3.5 nombra salas y llaves; el choque solo aparece cuando la cripta
  no es resoluble y se inicia con `--forzar`. El reporte se muestra completo al iniciar, no es parte del mapa
  conocido, no lo modifica (no explora ni avista ninguna sala ni cambia el estado recordado de ninguna puerta) y
  «ir a» no lo usa (FR-217).
- P: ¿Las inversas de los cambios del mapa conocido sirven también para la línea de tiempo (feature 004)?
  *(acuerdo con el integrante 3)* → R: No; son solo para el pergamino. Registrar un cambio e invertirlo con el
  pergamino cuesta proporcionalmente a lo que cambió (§5.3). Para la línea de tiempo, el mapa conocido se
  reconstruye hacia adelante: forma parte del estado de la partida que se copia en cada punto de control y que
  la re-simulación reproduce (FR-221, FR-223, FR-224); esa copia cuesta proporcionalmente al tamaño del mapa
  conocido y se hace una vez por punto de control (NFR-203).
- P: Las dos caras de la puerta de una salida con vuelta, ¿tienen siempre el mismo estado? *(revisión cruzada
  del integrante 1; es la regla de la primera parte)* → R: No necesariamente. Normalmente sí, pero en la primera
  parte pueden diferir: si ninguna declara llave y solo una está cerrada, o si las dos declaran llave (la
  misma o distintas) con distinto estado, cada cara se rige por lo suyo, porque la primera parte no iguala
  dos caras que declaran llave (003 FR-302). Por eso el estado recordado se guarda por cara: al
  observar una puerta (FR-207), el mapa registra el estado real de cada una de sus caras, y una salida cuenta
  como recordada abierta solo si se recuerda abierta la cara de la sala de la que sale; eso es lo que se ofrece
  a «ir a» (FR-208, FR-225).

---

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — El jugador solo ve lo que ha explorado (Prioridad: P1)

Como jugador, quiero ver solo la parte de la cripta que he recorrido y saber dónde hay salas que todavía no
he visitado, para que explorar tenga sentido y no conozca de antemano el mapa completo.

**Por qué esta prioridad**: es la regla central de la niebla de guerra; todo lo demás (puertas, antorcha,
comando de mapa, «ir a») se apoya en los tres estados de una sala.

**Prueba independiente**: iniciar una partida, moverse por unas salas y comprobar, sala por sala, que el
estado para el jugador (explorada, avistada o desconocida) y lo que se muestra de ella coinciden con las reglas,
aunque el programa haya descargado o precargado salas que el jugador no conoce.

**Escenarios de aceptación**:

1. **Dada** una partida nueva cuya sala inicial A tiene salidas hacia B y C, **cuando** el reloj está en
   t = 0, **entonces** A está explorada (el jugador conoce su nombre, sus salidas, el costo de cada salida y el
   estado de sus puertas), B y C están avistadas (el jugador solo sabe que hay una sala detrás de cada salida)
   y todas las demás salas de la cripta están desconocidas. *(FR-201, FR-202, FR-204, FR-205, FR-206)*
2. **Dado** que B está avistada y tiene salidas hacia D y E, que están desconocidas, **cuando** el jugador
   entra a B, **entonces** B queda explorada y D y E quedan avistadas. *(FR-203)*
3. **Dado** que el jugador está en A con una salida sin vuelta de A hacia F (F no tiene salida hacia A) y F
   no está explorada, **cuando** se consulta el estado de F, **entonces** F está avistada, porque es destino
   de una salida de una sala explorada. *(FR-204)*
4. **Dada** una sala avistada B, **cuando** la interfaz muestra cualquier información del mapa, **entonces**
   de B solo indica que existe una sala detrás de esa salida: no muestra su nombre, sus salidas, sus costos,
   sus puertas ni su contenido. *(FR-204, FR-217)*
5. **Dado** que el programa ya descargó el esqueleto completo y precargó el contenido de la sala desconocida
   G, **cuando** el jugador mira la vista o el mapa conocido, **entonces** G sigue desconocida y no aparece
   ningún dato suyo; y la precarga no cambió el estado de ninguna sala para el jugador. *(FR-217, FR-218)*
6. **Dado** que el jugador exploró B y luego volvió a A, **cuando** se consulta el estado de B, **entonces**
   B sigue explorada: una sala explorada no vuelve a avistada ni a desconocida salvo por un pergamino.
   *(FR-203, FR-222)*
7. **Dado** que un cazador (feature 001) se mueve por salas desconocidas para el jugador, calculando su camino
   con el esqueleto completo y pasando por salidas cuyas puertas el jugador nunca observó, **cuando** se
   consulta el mapa conocido después de esos movimientos, **entonces** ninguna sala cambió de estado para el
   jugador y el estado recordado de ninguna puerta cambió. *(FR-218)*

---

### Historia 2 — El mapa recuerda las puertas como las vio por última vez (Prioridad: P1)

Como jugador, quiero que mi mapa recuerde el estado de cada puerta tal como la vi la última vez, aunque haya
cambiado sin que yo lo viera, para que mi información sea realista y pueda equivocarse.

**Por qué esta prioridad**: el estado recordado de las puertas es la base de las rutas de «ir a» (§3.4) y la
diferencia entre lo que el jugador cree y la realidad es parte de la regla.

**Prueba independiente**: hacer que una puerta cambie mientras el jugador está lejos y comprobar que el mapa
conserva el estado viejo hasta que el jugador vuelve a estar en una de las dos salas que conecta.

**Escenarios de aceptación**:

1. *(Apéndice B, caso «puerta recordada abierta», parte del mapa)* **Dado** que el mapa del jugador recuerda
   abierta la puerta de la salida con vuelta entre B y C y en realidad esa puerta está cerrada, **cuando** el
   jugador llega a B (o a C), **entonces** observa la puerta y el mapa pasa a recordarla cerrada. *(FR-207, FR-209)*
   La parte «la ruta se recalcula; si no queda ruta, el viaje se detiene sin consumir tiempo adicional» es de
   «ir a» (escenarios H7-1 y H7-2; FR-255, FR-256, FR-259).
2. **Dado** que el jugador cruza de A a B por una puerta abierta con cierre automático y sigue hacia D, que no
   está conectada con A ni con B, **cuando** la puerta se cierra sola mientras el jugador está en D,
   **entonces** el mapa sigue mostrando esa puerta abierta, aunque en realidad está cerrada. *(FR-208)*
3. **Dado** que el jugador está en B y una puerta de una salida de B está abierta, **cuando** esa puerta se
   cierra mientras el jugador sigue en B, **entonces** el mapa la recuerda cerrada desde ese momento.
   *(FR-207)*
4. **Dada** una salida sin vuelta de A hacia F cuya puerta el mapa recuerda abierta y que en realidad está
   cerrada, **cuando** el jugador está en A, **entonces** observa esa puerta y el mapa la recuerda cerrada; y
   **cuando** el jugador está en F, **entonces** no observa esa puerta (no tiene cara en F) y el mapa conserva
   el último estado observado desde A. Además, **dada** una sala X que no es destino de ninguna salida de una
   sala explorada y tiene una salida sin vuelta hacia A, **cuando** el jugador está en A, **entonces** X sigue
   desconocida y la puerta de esa salida no se observa. *(FR-204, FR-207)*
5. **Dado** que A, B y C están exploradas; que la puerta de la salida con vuelta A–B está recordada abierta y
   solo su cara en B declara costo 150; que la puerta de la salida A–C figura «sin observar»; y que A tiene una
   salida hacia D, que está avistada, **cuando** se consulta lo que el mapa conocido ofrece a «ir a» desde A,
   **entonces** ofrece la salida A→B con costo 150 (y B→A también con costo 150) y no ofrece A→C ni A→D; cada
   sala ofrecida va con su identificador real, de modo que la búsqueda del cazador aplicada a ese conjunto de
   salas y salidas da la misma ruta y el mismo desempate que FR-253. *(FR-205, FR-212, FR-225)*
6. **Dado** que A y B están exploradas y que, según la primera parte, la puerta de la salida con vuelta A–B
   tiene la cara de A cerrada sin llave y la cara de B abierta, **cuando** el jugador observa esa puerta (desde
   A o desde B), **entonces** el mapa recuerda A→B cerrada y B→A abierta, y a «ir a» solo se le ofrece B→A.
   *(FR-207, FR-208, FR-225)*

---

### Historia 3 — La antorcha explora las vecinas (Prioridad: P2)

Como jugador, quiero que la antorcha encendida me revele las salas vecinas al entrar a una sala, sin despertar
lo que haya en ellas, para planificar mejor mi recorrido.

**Por qué esta prioridad**: da efecto a un objeto de la primera parte (P1 §2.7); es la fuente principal de
cambios grandes en el mapa conocido de una sola vez.

**Prueba independiente**: entrar a la misma sala con la antorcha encendida y apagada, y comparar qué salas
quedan exploradas y qué ocurrió con los enemigos y trampas de las vecinas.

**Escenarios de aceptación**:

1. *(Apéndice B, caso «antorcha»)* **Dado** que la antorcha está encendida y la sala B tiene salidas hacia C
   (con un enemigo dormido) y hacia D (con una trampa), **cuando** el jugador entra a B, **entonces** B, C y D
   quedan exploradas; el enemigo de C sigue dormido; la trampa de D no se activa; el mapa muestra el nombre y
   las salidas de C y D, pero no su contenido; y la entrada no consume más tiempo que una entrada sin antorcha.
   *(FR-210, FR-211)*
2. **Dado** que la antorcha está encendida y la salida de B hacia E tiene una puerta cerrada (incluso con llave
   que el jugador no tiene), **cuando** el jugador entra a B, **entonces** E queda explorada igual que las
   vecinas detrás de salidas abiertas. *(FR-210)*
3. **Dado** que la antorcha está apagada y B tiene salidas hacia C y D, que están desconocidas, **cuando** el
   jugador entra a B, **entonces** solo B queda explorada; C y D quedan avistadas. *(FR-214)*
4. **Dado** que la antorcha está encendida y C, vecina de B, tiene salidas hacia H e I, que están
   desconocidas, **cuando** el jugador entra a B, **entonces** C queda explorada y H e I quedan avistadas (no
   exploradas). *(FR-213)*
5. **Dado** que C fue explorada por la antorcha y tiene un enemigo dormido, **cuando** el jugador entra a C,
   **entonces** se revela su contenido y el enemigo se comporta según P1 §2.4, como en cualquier entrada.
   *(FR-216)*
6. **Dado** que la antorcha está encendida, B tiene una salida hacia C y C tiene además una salida hacia J cuya
   puerta el jugador nunca observó, **cuando** el jugador entra a B, **entonces** el mapa muestra la puerta de
   la salida de B a C con el estado observado desde B, y la puerta de la salida de C a J como «sin observar»
   (ni abierta ni cerrada) hasta que el jugador esté en una sala donde esa puerta tenga una cara.
   *(FR-205, FR-207, FR-212)*
7. **Dado** que el jugador está en B con la antorcha apagada y C, vecina de B, está avistada, **cuando**
   enciende la antorcha sin moverse, **entonces** el mapa conocido no cambia y C sigue avistada; y **cuando**
   después entra a otra sala con la antorcha encendida, **entonces** se exploran las vecinas de esa sala.
   *(FR-210, FR-215)*
8. **Dado** que la antorcha encendida se apaga en el instante t y que el jugador entra a B en ese mismo
   instante t, **cuando** el fin de la antorcha se programó antes que la acción del jugador, **entonces** la
   entrada ocurre con la antorcha apagada y las vecinas de B solo quedan avistadas; y **cuando** se programó
   después, **entonces** la entrada ocurre con la antorcha encendida y las vecinas de B quedan exploradas. Los
   eventos con el mismo tiempo se atienden en el orden en que se programaron, la misma regla de 001 FR-108.
   *(FR-210, FR-214)*

---

### Historia 4 — El mapa se guarda, se revierte y se consulta en la línea de tiempo (Prioridad: P2)

Como jugador, quiero que lo que sé del mapa forme parte de mi partida: que se conserve al guardar, que el
pergamino lo deshaga y que la historia me muestre lo que sabía en cada momento.

**Por qué esta prioridad**: el conocimiento del jugador es estado del juego (§3.3); si no se guardara o no
se revirtiera, la partida quedaría inconsistente.

**Prueba independiente**: explorar con y sin antorcha, usar un pergamino, guardar, cargar, consultar
`historia` y reproducir con `--replay`, comparando el mapa conocido en cada paso.

**Escenarios de aceptación**:

1. *(Apéndice B, caso «pergamino y antorcha»)* **Dado** que, con la antorcha encendida, el jugador entró a B
   desde A y eso exploró B y sus vecinas C y D (antes, B estaba avistada, C desconocida y D avistada),
   **cuando** usa un pergamino que revierte esa entrada, **entonces** B vuelve a avistada, C a desconocida y
   D a avistada, y el resto del mapa conocido queda como estaba antes de esa entrada. *(FR-222)*
2. **Dado** que el mapa recordaba abierta la puerta de la salida de B a C, el jugador entró a B y la observó
   cerrada, **cuando** usa un pergamino que revierte esa entrada, **entonces** el mapa vuelve a recordar esa
   puerta abierta. *(FR-222)*
3. **Dada** una partida con salas exploradas por entrada y por antorcha y puertas recordadas con un estado
   distinto al real, **cuando** se guarda y se carga, **entonces** el mapa conocido es idéntico al guardado:
   mismos estados de sala y mismo estado recordado de cada puerta. *(FR-221)*
4. **Dado** que en la acción 4 el jugador estaba en A con B avistada y en la acción 6 exploró B, **cuando**
   consulta `historia #4`, **entonces** el resumen muestra el mapa conocido de ese momento, con B avistada.
   *(FR-223)*
5. **Dada** la misma cripta, la misma semilla y el mismo `partida.log`, **cuando** se reproduce con
   `--replay` (y con `--replay … --hasta t`), **entonces** el mapa conocido resultante es idéntico al de la
   partida original en ese instante. *(FR-224)*

---

### Historia 5 — El jugador consulta su mapa con un comando (Prioridad: P3)

Como jugador, quiero un comando que me muestre mi mapa conocido, para orientarme y decidir hacia dónde ir.

**Por qué esta prioridad**: lo exige §3.3, pero depende de que las historias 1 a 3 ya definan qué se sabe;
cómo se dibuja es de la interfaz (integrante 3).

**Prueba independiente**: después de explorar una parte de la cripta, ejecutar el comando y comparar lo que
lista con los estados de sala y puertas esperados.

**Escenarios de aceptación**:

1. **Dado** que el jugador exploró A y B y avistó C, D y E, **cuando** ejecuta el comando de ver el mapa,
   **entonces** se muestran A y B con sus salidas, el costo de cada salida y el estado recordado de cada
   puerta, y C, D y E como salas avistadas detrás de sus salidas; ninguna sala desconocida aparece.
   *(FR-219)*
2. **Dada** una puerta recordada abierta que en realidad está cerrada, **cuando** el jugador ejecuta el
   comando, **entonces** la puerta figura abierta (el estado recordado, no el real). *(FR-208, FR-219)*
3. **Dada** una sala explorada solo por la antorcha, **cuando** el jugador ejecuta el comando, **entonces**
   aparece con su nombre y sus salidas, sin su contenido, y sus puertas nunca observadas figuran «sin observar».
   *(FR-211, FR-212, FR-219)*
4. **Dada** una partida con el reloj en t = 300, **cuando** el jugador ejecuta el comando de ver el mapa,
   **entonces** el reloj sigue en 300, no cuenta como acción, no se registra en `partida.log` y no cambia el
   historial de retroceso. *(FR-220)*
5. **Dado** que A y B están exploradas y cada una tiene una salida hacia la misma sala C, que está avistada,
   **cuando** el jugador ejecuta el comando de ver el mapa, **entonces** se muestran dos salidas hacia «sala
   sin explorar», cada una por separado y sin identificador, sin indicar que llevan a la misma sala; y
   **cuando** el jugador entra a C, **entonces** el mapa muestra que ambas salidas llevan a C. *(FR-204,
   FR-219)*
6. **Dado** que A y B están exploradas, que solo la cara en B de la puerta de la salida con vuelta A–B declara
   costo 150 y que ninguna cara de la puerta de la salida de A hacia C declara costo, **cuando** el jugador
   ejecuta el comando de ver el mapa, **entonces** la salida A→B figura con costo 150, la salida B→A también con
   150 y la salida A→C con 100 (costos igualados según 001 FR-101). *(FR-205, FR-219)*
7. **Dada** una cripta no resoluble cuya partida se inicia con `--forzar`, **cuando** se muestra el reporte de
   resolubilidad (003 FR-313), **entonces** el reporte se muestra completo aunque nombre salas, puertas o
   ubicaciones de llaves desconocidas para el jugador; y **después** de mostrarlo, el mapa conocido sigue
   teniendo solo la sala inicial explorada y sus vecinas avistadas, con el estado recordado de las puertas
   igual que antes del reporte. *(FR-202, FR-217)*

---

### Historia 6 — Viajar a una sala explorada con «ir a» (Prioridad: P2)

Como jugador, quiero indicar a qué sala que ya exploré quiero ir y que el viaje se haga solo, paso a paso,
para no repetir a mano un recorrido que ya conozco.

**Por qué esta prioridad**: se apoya en el mapa conocido (historias 1 y 2) y en las salidas recordadas abiertas; sin
ella el jugador igual puede moverse a mano, pero deja sin uso lo que el mapa recuerda (§3.4).

**Prueba independiente**: explorar varias salas, ejecutar «ir a» hacia una de ellas y comprobar la ruta que se
sigue, el tiempo que consume cada paso y que nunca se usan salas no exploradas ni puertas que el mapa no
recuerda abiertas.

**Escenarios de aceptación**:

1. *(Apéndice B, caso «ir a hacia una sala no explorada»)* **Dado** que el jugador está en A, que B está
   avistada y que G está desconocida, **cuando** ejecuta «ir a» hacia B, hacia G o hacia un nombre que no
   corresponde a ninguna sala que conoce, **entonces** las tres órdenes se rechazan con el mismo mensaje, que no
   revela si la sala existe ni nada de ella; el reloj no avanza, no se da ningún paso, no se cuenta ninguna
   acción, no se escribe nada en `partida.log` y el mapa conocido no cambia. *(FR-251)*
2. **Dado** que A, B, C y D están exploradas, que el jugador está en A, que las salidas de A a B y de B a D
   están recordadas abiertas y cuestan 100 cada una, y que las salidas de A a C y de C a D también están
   recordadas abiertas y cuestan 100 y 300, **cuando** ejecuta «ir a» hacia D, **entonces** el viaje pasa por B
   (costo total 200 frente a 400), da dos pasos y cada uno consume el tiempo de su salida según §3.1.
   *(FR-253, FR-254)*
3. **Dado** que desde A hay dos rutas de igual costo mínimo hacia D, una por B y otra por C, y que B tiene menor
   identificador que C, **cuando** ejecuta «ir a» hacia D, **entonces** el primer paso va hacia B. *(FR-253)*
4. **Dado** que la ruta más corta hacia D pasa por una puerta que el mapa recuerda cerrada y que el jugador
   tiene la llave de esa puerta, **cuando** ejecuta «ir a» hacia D, **entonces** el viaje no abre la puerta: toma
   otra ruta con salidas recordadas abiertas, aunque sea más larga; y si no hay otra, no se da ningún paso, se
   informa que no hay ruta conocida y el reloj no avanza. *(FR-252, FR-257, FR-259)*
5. **Dado** que una sala explorada solo por la antorcha tiene una puerta «sin observar» en la única ruta hacia el
   destino, **cuando** el jugador ejecuta «ir a», **entonces** esa salida no cuenta como recordada abierta y el
   viaje no la usa. *(FR-212, FR-252)*
6. **Dado** que la ruta más corta imaginable hacia D atraviesa una sala avistada o desconocida, **cuando** el
   jugador ejecuta «ir a» hacia D, **entonces** el viaje no la usa: solo recorre salas exploradas, aunque el
   esqueleto de la cripta ya esté descargado. *(FR-217, FR-252)*
7. **Dado** que durante un viaje de varios pasos una puerta de otra parte de la cripta se cierra sola en un
   instante que cae entre dos pasos, **cuando** el viaje continúa, **entonces** ese evento ocurre en su instante,
   como en cualquier otro momento de la partida, y el viaje no lo omite ni lo adelanta. *(FR-254)*
8. **Dado** que el jugador está en A, **cuando** ejecuta «ir a» hacia A, **entonces** se informa que ya está allí,
   no se da ningún paso y el reloj no avanza. *(FR-251)*
9. **Dado** que la antorcha está encendida, **cuando** un paso del viaje entra a una sala, **entonces** se aplican
   todas las reglas de una entrada ordinaria: la sala y sus vecinas se exploran según FR-203 y FR-210, y los
   enemigos y trampas se comportan según P1. *(FR-264)*
10. **Dado** el mapa conocido completo de la cripta de referencia, **cuando** se calcula un paso de «ir a»,
    **entonces** el cálculo tarda menos de 5 ms (medido con `--bench`). *(NFR-250)*

---

### Historia 7 — El viaje se detiene, se recalcula y se puede deshacer (Prioridad: P2)

Como jugador, quiero que el viaje automático se detenga cuando algo cambia o me amenaza, que corrija su ruta
con lo que voy viendo y que el pergamino pueda deshacer un paso, para no perder el control de la partida.

**Por qué esta prioridad**: sin estas paradas el viaje automático sería peligroso; son la otra mitad de la regla
de §3.4.

**Prueba independiente**: provocar cada causa de detención (llegada, enemigos, daño, falta de ruta), comprobar
el motivo que muestra la interfaz y usar un pergamino en mitad de un viaje.

**Escenarios de aceptación**:

1. *(Apéndice B, caso «puerta recordada abierta», parte de «ir a»)* **Dado** que el mapa recuerda abierta la
   puerta de la salida entre B y C, que en realidad está cerrada, y que la ruta hacia el destino pasa por ella
   y existe otra ruta recordada abierta, **cuando** el jugador llega a B durante el viaje, **entonces** observa
   la puerta cerrada, el mapa se actualiza (H2-1), la ruta se recalcula evitándola y el viaje continúa por la
   otra ruta. *(FR-255, FR-256)*
2. *(Apéndice B, caso «puerta recordada abierta», parte de «ir a»)* **Dado** el mismo caso pero sin otra ruta
   recordada abierta, **cuando** el jugador llega a B, **entonces** el viaje se detiene porque ya no hay ruta
   conocida; la interfaz muestra ese motivo; el reloj queda en el instante en que el jugador llegó a B, sin
   tiempo adicional, y el jugador sigue en B. *(FR-256, FR-259, FR-260)*
3. *(Apéndice B, caso «enemigos dormidos»)* **Dado** que una sala de la ruta contiene un enemigo dormido,
   **cuando** el jugador entra a ella durante el viaje, **entonces** el enemigo se activa según P1 §2.4, como en
   cualquier entrada, y el viaje se detiene; la interfaz muestra que se detuvo por enemigos. *(FR-258, FR-260)*
4. **Dado** que una sala de la ruta contiene un enemigo ya activo, **cuando** el jugador entra a ella durante el
   viaje, **entonces** el viaje se detiene por enemigos; y si esa sala es el destino, la interfaz muestra los dos
   motivos: llegada y enemigos. *(FR-258, FR-260)*
5. **Dado** que durante un viaje el jugador recibe daño (por un enemigo, una trampa o un efecto sostenido como
   el veneno), **cuando** ocurre el daño, **entonces** el viaje se detiene antes de dar el siguiente paso y la
   interfaz muestra que se detuvo por daño. *(FR-258, FR-260)*
6. **Dado** que el jugador llega al destino, **cuando** termina el último paso, **entonces** el viaje se detiene y
   la interfaz indica que llegó. *(FR-258, FR-260)*
7. *(Apéndice B, caso «pergamino durante un viaje»)* **Dado** un viaje de cuatro pasos y que el jugador tiene un
   pergamino, **cuando** lo lee después del tercer paso, **entonces** se revierte únicamente el tercer paso (la
   posición, el reloj y el mapa conocido vuelven a como estaban antes de ese paso), los pasos primero y segundo
   permanecen, y el viaje no continúa. *(FR-222, FR-262)*
8. **Dado** un viaje de tres pasos, **cuando** se revisa `partida.log`, **entonces** contiene tres movimientos
   individuales, iguales a los de movimientos hechos a mano, y la orden «ir a» como comentario; y **cuando** se
   reproduce con `--replay`, **entonces** la partida llega al mismo estado y al mismo mapa conocido, sin que el
   comentario cambie nada. *(FR-261)*
9. **Dado** un viaje de tres pasos, **cuando** el jugador consulta la línea de tiempo (feature 004), **entonces**
   hay tres acciones consecutivas del jugador, `historia #k` de cada una describe el estado justo antes de ese
   paso, y la orden «ir a» en sí no cuenta como una acción ni recibe número. *(FR-263)*

---

### Casos borde

- **Vecina ya explorada**: con la antorcha encendida, una vecina que ya estaba explorada no cambia; revertir la
  entrada no la vuelve avistada (FR-222: el mapa vuelve exactamente al estado anterior).
- **Sala vecina de sí misma o vecina por varias salidas**: se explora una sola vez; la exploración no se
  duplica.
- **Sala de la que se viene**: con la antorcha, la sala de origen ya está explorada y no cambia.
- **La antorcha se apaga en el mismo instante en que el jugador entra**: los eventos con el mismo tiempo se
  atienden en el orden en que se programaron (la misma regla de 001 FR-108). Si el fin de la antorcha se
  programó antes que la acción del jugador, la entrada ocurre con la antorcha apagada y no explora las
  vecinas; si se programó después, las explora (escenario H3-8).
- **Caras de una puerta con estados distintos**: el mapa recuerda cada cara por separado; una salida solo se
  ofrece a «ir a» si se recuerda abierta la cara de la sala de la que sale (FR-208, FR-225, escenario H2-6).
- **Salida sin vuelta hacia una sala explorada**: la sala de la que sale sigue desconocida si no es destino de
  ninguna salida de una sala explorada (FR-204, escenario H2-4).
- **Varias salidas hacia la misma sala avistada**: el jugador no sabe que es la misma sala hasta explorarla
  (FR-204, escenario H5-5).
- **Puerta en una salida sin vuelta**: solo tiene cara en la sala de la que sale, así que solo se observa desde
  esa sala, no desde la sala destino (FR-207, escenario H2-4).
- **Pergamino que revierte una acción en la que no cambió el mapa**: el mapa conocido queda igual.
- **Pergaminos seguidos**: cada uno devuelve el mapa al estado anterior a la acción que revierte (P1 §2.11).
- **Archivo de partida de la primera parte**: no trae mapa conocido; se trata según FR-421 de la feature 004
  (incompatible o migrado con aviso; nunca se carga en silencio).
- **Partida terminada**: el comando de ver el mapa sigue disponible y muestra el mapa del final.
- **Cazador en una sala desconocida**: el cazador conoce el esqueleto completo (feature 001), pero su recorrido
  no cambia el mapa conocido del jugador (FR-218).
- **Costo declarado en una sola cara de una puerta**: el jugador conoce y ve el costo igualado (001 FR-101), el
  mismo en los dos sentidos, aunque la cara que lo declara esté en una sala avistada; si ninguna cara lo
  declara, 100. Si las dos caras declaran costos distintos, la partida no inicia (001 FR-122) (FR-205,
  escenario H5-6).
- **Salida de una sala explorada hacia una sala avistada**: no se ofrece a «ir a», aunque su puerta se
  recuerde abierta (FR-225, escenario H2-5).
- **Reporte de resolubilidad con `--forzar`**: puede nombrar salas, puertas y ubicaciones de llaves que el
  jugador no conoce; se muestra completo, pero no cambia el mapa conocido y «ir a» no lo usa (FR-217,
  escenario H5-7). Al cargar o reproducir con `--replay` no se muestra (003 H4-4).
- **«ir a» con el destino en la sala actual**: se informa que ya está allí; sin pasos y sin tiempo (FR-251).
- **«ir a» con un nombre que designa más de una sala explorada**: se rechaza por ambiguo, sin tiempo (FR-251).
- **Destino sin ruta conocida desde el inicio**: no se da ningún paso, se informa el motivo y el reloj no avanza
  (FR-259).
- **Varios motivos de detención a la vez** (por ejemplo, llegar a un destino con enemigos): la interfaz los muestra
  todos (FR-260).
- **Pergamino sin que haya viaje en curso**: se comporta como siempre (P1 §2.11); FR-262 solo añade que, si hay un
  viaje en curso, este no continúa.
- **Partida terminada durante un viaje** (por ejemplo, el jugador muere): el viaje se detiene por daño y no hay
  más pasos (FR-258).

---

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Estados de una sala para el jugador**

- **FR-201**: En todo momento, cada sala de la cripta DEBE estar, para el jugador, en exactamente uno de tres
  estados: explorada, avistada o desconocida.
- **FR-202**: La sala inicial DEBE estar explorada desde el instante 0, y los destinos de sus salidas DEBEN
  estar avistados desde ese instante (salvo que sean la misma sala inicial).
- **FR-203**: Al entrar a una sala, esta DEBE quedar explorada, y los destinos de sus salidas que no estén
  explorados DEBEN quedar avistados. Una sala explorada NO DEBE volver a avistada ni a desconocida, salvo al
  revertir con un pergamino la acción que la exploró (FR-222).
- **FR-204**: Una sala DEBE estar avistada si no está explorada y es destino de al menos una salida de una
  sala explorada, aunque esa salida no tenga vuelta. De una sala avistada el jugador solo conoce que existe una
  sala detrás de esa salida: NO su nombre, sus salidas, sus costos, sus puertas, su contenido ni su identidad.
  Si varias salidas llevan a la misma sala avistada, el jugador NO DEBE poder saber que es la misma sala hasta
  explorarla. Una sala que no es destino de ninguna salida de una sala explorada DEBE seguir desconocida
  aunque tenga una salida sin vuelta hacia una sala explorada; la puerta de esa salida no se observa desde la
  sala explorada (FR-207).
- **FR-205**: De una sala explorada el jugador DEBE conocer su nombre, sus salidas, el costo de cada salida y
  el estado de cada una de sus puertas según la última observación (FR-208), o «sin observar» si nunca se
  observó (FR-212). El costo que el jugador conoce de cada salida DEBE ser el costo igualado según 001 FR-101:
  el mismo en los dos sentidos aunque solo una cara de la puerta lo declare, y 100 si ninguna lo declara; NO
  el declarado por una sola cara.
- **FR-206**: De una sala desconocida el jugador NO DEBE conocer nada, ni siquiera que existe.

**Memoria de puertas**

- **FR-207**: El jugador DEBE observar las puertas que tienen una cara en la sala donde está: al llegar a la
  sala y cada vez que una de esas puertas cambia mientras él sigue allí. Así, la puerta de una salida con
  vuelta se observa desde cualquiera de las dos salas que conecta (§3.3), y la de una salida sin vuelta solo
  desde la sala de la que sale *(decisión del grupo: observarla desde la sala destino revelaría que existe una
  sala desconocida y contradiría FR-206)*. Observar una puerta DEBE dejar en el mapa el estado real de cada
  una de sus caras en ese momento; las dos caras de una puerta con vuelta pueden tener estados distintos según
  la primera parte (ver «Puerta» en Convenciones).
- **FR-208**: El mapa DEBE recordar, por cara, el estado de cada puerta tal como estaba en su última
  observación, aunque después haya cambiado. Todo lo que el jugador ve del estado de una puerta DEBE ser el
  estado recordado de cada cara, no el real. Una salida cuenta como recordada abierta solo si el mapa recuerda
  abierta la cara de la sala de la que sale.
- **FR-209**: Al volver a observar una puerta, el mapa DEBE actualizarse con su estado real de ese momento.

**Antorcha**

- **FR-210**: Mientras la antorcha esté encendida, al entrar a una sala también DEBEN quedar exploradas todas
  sus vecinas, a través de cualquier salida, abierta o cerrada.
- **FR-211**: Explorar una vecina con la antorcha DEBE revelar su nombre, sus salidas y el costo de cada
  salida, y NO DEBE revelar su contenido (enemigos, objetos, trampas). NO DEBE activar sus enemigos ni sus
  trampas, NO DEBE consumir tiempo virtual adicional y NO DEBE contar como una acción aparte de la entrada.
- **FR-212**: Para una vecina explorada con la antorcha, la puerta de la salida por la que es vecina se observa
  según FR-207, porque el jugador está en la otra sala, donde esa puerta tiene una cara. Las demás puertas de
  esa vecina que el jugador nunca observó DEBEN figurar «sin observar» (estado desconocido) hasta que el
  jugador esté en una sala donde esa puerta tenga una cara. Una puerta «sin observar» NO es una puerta
  recordada abierta (dato que usará «ir a», FR-252).
- **FR-213**: Los destinos de las salidas de una vecina explorada con la antorcha que no estén explorados
  DEBEN quedar avistados; la antorcha NO DEBE explorar más allá de las vecinas de la sala a la que se entra.
- **FR-214**: Con la antorcha apagada, entrar a una sala NO DEBE explorar sus vecinas (solo las deja avistadas
  según FR-203).
- **FR-215**: La antorcha DEBE tener efecto solo al entrar a una sala (§3.3: «al entrar a una sala»).
  Encenderla estando ya en una sala NO DEBE cambiar el mapa conocido.
- **FR-216**: Entrar más tarde a una sala que fue explorada con la antorcha DEBE revelar su contenido y aplicar
  sus enemigos y trampas como en cualquier entrada (P1).

**Separación entre el mapa descargado y el conocimiento del jugador**

- **FR-217**: Todo lo que la interfaz muestre sobre el mapa (la vista de la partida, el comando de ver el mapa
  y el mapa del resumen de `historia`) y todo lo que use «ir a» DEBE derivarse exclusivamente del mapa conocido
  del jugador. NO DEBE mostrarse ningún dato de una sala desconocida ni más que la existencia de una sala
  avistada. **Excepción**: el reporte de resolubilidad (spec 003, FR-313) DEBE mostrarse completo al iniciar la
  partida, como exige §7.3, aunque mencione salas, puertas o ubicaciones de llaves que el jugador no conoce
  (solo ocurre con una cripta no resoluble iniciada con `--forzar`). Ese reporte no es parte del mapa
  conocido, NO DEBE modificarlo (no explora ni avista ninguna sala ni cambia el estado recordado de ninguna
  puerta) y «ir a» NO DEBE usarlo.
- **FR-218**: El programa PUEDE seguir descargando el esqueleto completo, y la precarga (P1 §4.2) y el cazador
  (feature 001) PUEDEN usarlo, pero descargar, precargar o cualquier cálculo del cazador NO DEBE cambiar el
  estado de ninguna sala para el jugador ni el estado recordado de ninguna puerta.

**Comando para ver el mapa conocido**

- **FR-219**: La interfaz DEBE ofrecer un comando para ver el mapa conocido que muestre las salas exploradas
  (con su nombre, sus salidas, el costo igualado de cada salida según FR-205 y 001 FR-101, y el estado
  recordado de sus puertas, o «sin observar» para las puertas que nunca se observaron, mostradas como
  tales) y las salas avistadas (cada salida hacia una sala avistada por separado, como «sala sin explorar
  detrás de esta salida», sin identificador). NUNCA DEBE mostrar salas desconocidas ni información
  que el jugador no conoce, como el contenido de una sala explorada con la antorcha o el estado real de una
  puerta distinto del recordado.
- **FR-220**: Ver el mapa conocido NO DEBE consumir tiempo virtual, NO DEBE contar como acción del jugador,
  NO DEBE registrarse en `partida.log` y NO DEBE modificar el historial de retroceso ni ningún estado del juego.

**El conocimiento del jugador es estado del juego**

- **FR-221**: Guardar la partida DEBE incluir el mapa conocido; al cargar, el mapa conocido DEBE ser idéntico
  al guardado (estado de cada sala y estado recordado de cada puerta).
- **FR-222**: Al revertir una acción con un pergamino, el mapa conocido DEBE volver exactamente al estado que
  tenía antes de esa acción, incluidas las salas exploradas o avistadas por la antorcha y las puertas observadas
  durante la acción revertida.
- **FR-223**: El mapa conocido DEBE formar parte de la línea de tiempo (feature 004): el resumen de cualquier
  instante DEBE mostrar el mapa conocido que el jugador tenía en ese instante, y NO DEBE mostrar conocimiento
  obtenido en acciones revertidas. El mapa conocido de un instante se reconstruye hacia adelante, como el
  resto del estado de la partida: forma parte de lo que se copia en cada punto de control y la re-simulación
  lo reproduce (FR-221, FR-224); la línea de tiempo NO necesita invertir cambios del mapa conocido (NFR-203).
- **FR-224**: La misma partida (misma cripta, misma semilla y mismas acciones) DEBE producir el mismo mapa
  conocido en cada instante, también al reproducirla con `--replay` y con `--replay … --hasta`
  (Principio IV).

**Lo que el mapa conocido ofrece a «ir a»**

- **FR-225**: El mapa conocido DEBE ofrecer a «ir a» exactamente lo que necesitan FR-252 y FR-253: para cada
  sala explorada, sus salidas hacia otras salas exploradas que el mapa recuerda abiertas (la cara de la puerta
  en esa sala se recuerda abierta, FR-208), cada una con su costo igualado según 001 FR-101 (FR-205). Una
  salida cuya cara en la sala de la que sale figura «sin observar» (FR-212) o se recuerda cerrada NO DEBE
  ofrecerse, aunque la otra cara se recuerde abierta, ni tampoco una salida hacia una sala avistada o
  desconocida. Cada sala DEBE ir identificada por su identificador real, para que el desempate por menor
  identificador de FR-253 dé el mismo resultado que la búsqueda del cazador (feature 001) aplicada a ese
  mismo conjunto de salas y salidas. NO DEBE ofrecerse nada más (FR-217).

### Viaje automático «ir a» (§3.4) — FR-250 a FR-299 (integrante 3)

Esta sección usa los rangos FR-250 a FR-299, NFR-250 a NFR-299 y SC-250 a SC-299. Sus historias son la 6 y
la 7. Cuando se dice «el mapa» se entiende el mapa conocido del jugador (FR-217).

**El comando y su destino**

- **FR-250**: El programa DEBE ofrecer el comando «ir a <sala>», que lleva al jugador a una sala explorada
  mediante una secuencia de movimientos ordinarios del jugador. «ir a» NO DEBE mover al jugador de ninguna otra
  forma.
- **FR-251**: El destino DEBE ser una sala explorada. Una orden cuyo destino no sea una sala explorada
  (avistada, desconocida o inexistente) o cuyo nombre designe más de una sala explorada DEBE rechazarse con un
  mensaje, sin dar ningún paso, sin consumir tiempo virtual, sin contar como acción, sin registrarse en
  `partida.log` y sin cambiar la partida. El mensaje NO DEBE revelar si la sala existe ni nada de ella (FR-206,
  FR-217). Si el destino es la sala donde está el jugador, DEBE informar que ya está allí, sin pasos y sin
  consumir tiempo.

**La ruta**

- **FR-252**: La ruta DEBE calcularse solo con el conocimiento del jugador: únicamente por salas exploradas y
  únicamente por **salidas recordadas abiertas**: el mapa recuerda cada cara de una puerta por separado, y una
  salida cuenta como recordada abierta solo si se recuerda abierta la cara de la sala de la que sale (FR-208,
  FR-225; escenario H2-6). Una salida cuya cara se recuerda cerrada, o figura «sin observar» (FR-212), NO DEBE
  usarse. NO DEBE usar salas avistadas ni desconocidas, ni el estado real
  de las puertas, ni nada del esqueleto de la cripta que el jugador no conozca (FR-217).
- **FR-253**: Entre las rutas permitidas, la ruta DEBE minimizar la suma de los costos de las salidas (§3.1). Si
  hay varias de igual costo mínimo, el primer paso DEBE ir hacia la vecina de menor identificador entre las que
  están en alguna ruta de costo mínimo, igual que el cazador (§3.2). El identificador es interno: el jugador no
  necesita verlo.
- **FR-254**: Cada paso DEBE ser un movimiento ordinario del jugador y una acción completa: DEBE consumir el
  tiempo que le corresponde según §3.1 (el costo de la salida y la velocidad del jugador) y, entre un paso y el
  siguiente, los eventos del reloj (enemigos, puertas que se cierran solas, efectos) DEBEN ocurrir con
  normalidad. El viaje NO DEBE detener, adelantar ni omitir eventos.
- **FR-255**: La ruta DEBE recalcularse antes de cada paso con el conocimiento vigente en ese momento. La
  decisión de cada paso DEBE ser idéntica a la que se obtendría calculando la ruta desde cero con ese
  conocimiento, y la misma partida (misma cripta, misma semilla y mismas acciones) DEBE producir siempre el mismo
  viaje (Principio IV).
- **FR-256**: Si al llegar a una sala el jugador observa que una puerta de su ruta está cerrada (FR-207, FR-209),
  el cálculo siguiente DEBE evitarla. Recalcular la ruta NO DEBE consumir tiempo virtual.
- **FR-257**: El viaje NO DEBE abrir puertas, aunque el jugador tenga la llave.

**Cuándo se detiene el viaje**

- **FR-258**: El viaje DEBE detenerse cuando ocurra cualquiera de estos casos: (a) el jugador llega al destino;
  (b) el jugador entra a una sala que contiene enemigos, activos o dormidos (los dormidos se activan según P1
  §2.4, como en cualquier entrada); (c) el jugador recibe daño, de cualquier origen, y en ese caso el viaje NO
  DEBE dar el paso siguiente; (d) deja de existir una ruta conocida hasta el destino.
- **FR-259**: Si no existe una ruta conocida, ya sea al ejecutar la orden o tras recalcular, el viaje DEBE
  detenerse sin dar ningún paso adicional y sin consumir tiempo virtual adicional.
- **FR-260**: La interfaz DEBE mostrar el motivo por el que se detuvo el viaje o se rechazó la orden (§7.3): llegó
  al destino, entró a una sala con enemigos, recibió daño, no hay ruta conocida o el destino no es válido. Si
  coinciden varios motivos, DEBE mostrarlos todos.

**Registro, pergamino y línea de tiempo**

- **FR-261**: En `partida.log`, cada paso DEBE registrarse como un movimiento individual, igual que un movimiento
  hecho a mano, y la orden «ir a» DEBE registrarse además como comentario para fines de depuración. Reproducir con
  `--replay` DEBE repetir los pasos, y el comentario NO DEBE cambiar el resultado. Una orden rechazada o que no da
  ningún paso NO DEBE registrarse.
- **FR-262**: Si el jugador lee un pergamino durante un viaje, el pergamino DEBE revertir únicamente el último
  paso (P1 §2.11; el mapa conocido vuelve al estado anterior a ese paso, FR-222) y el viaje NO DEBE continuar. Los
  pasos anteriores NO DEBEN revertirse.
- **FR-263**: En la línea de tiempo (feature 004), cada paso DEBE contar como una acción del jugador, con su
  número de acción. La orden «ir a» en sí NO DEBE contar como acción ni recibir número, y una orden rechazada no
  agrega ninguna.
- **FR-264**: Cada paso DEBE aplicar todas las reglas de una entrada ordinaria a la sala a la que llega:
  exploración (FR-203), antorcha (FR-210 a FR-215), enemigos y trampas (P1).

### Requisitos de rendimiento y de recursos

- **NFR-201**: Consultar si una sala está explorada, avistada o desconocida, y consultar el estado recordado
  de una puerta, son operaciones frecuentes (en cada vista, en cada paso de «ir a» y en cada actualización por
  antorcha): su costo NO DEBE depender del tamaño del mapa conocido ni del tamaño de la cripta (§5.3).
- **NFR-202**: Explorar nuevas salas (al entrar o con la antorcha) DEBE costar proporcionalmente a lo que se
  revela (las salas que cambian de estado y sus salidas), no al tamaño del mapa conocido (§5.3).
- **NFR-203**: Registrar un cambio del mapa conocido e invertirlo con el pergamino (FR-222) DEBE costar
  proporcionalmente a lo que cambió, no al tamaño del mapa conocido (§5.3). Las inversas son solo para el
  pergamino: para la línea de tiempo (feature 004) el mapa conocido NO necesita inversas, porque se
  reconstruye hacia adelante como parte del estado de la partida que se copia en cada punto de control y que
  la re-simulación reproduce (FR-221, FR-223, FR-224). Esa copia DEBE costar proporcionalmente al tamaño del
  mapa conocido y hacerse una sola vez por punto de control.
- **NFR-204**: `--bench` DEBE medir las consultas al mapa conocido y la exploración con antorcha en criptas
  sintéticas deterministas por semilla de al menos tres tamaños *(decisión del grupo)*, y las decisiones que
  se tomen con esas mediciones DEBEN documentarse en `DECISIONES.md` (§6.3, Principio VIII).
- **NFR-205**: Las actualizaciones del mapa conocido NO DEBEN hacer que el ciclo de eventos entre dos
  decisiones del jugador supere el límite de 20 ms (P1 §5.2 y §6.1 de la Parte II).
- **NFR-250**: El cálculo de un paso de «ir a» DEBE tardar menos de 5 ms con el mapa conocido completo de la
  cripta de referencia, medido en el equipo local, sin red ni renderizado. El «5 ms» sale de la tabla de §6.1
  del enunciado.
- **NFR-251**: `--bench` DEBE medir el cálculo de un paso de «ir a» en criptas sintéticas deterministas por
  semilla de al menos tres tamaños, incluido el mapa conocido completo *(decisión del grupo)*, y las decisiones
  que se tomen con esas mediciones DEBEN documentarse en `DECISIONES.md` (§6.3, Principio VIII).

### Entidades clave

- **Mapa conocido**: lo que el jugador sabe de la cripta en un instante; forma parte del estado de la partida.
- **Estado de una sala para el jugador**: explorada, avistada o desconocida (FR-201).
- **Estado recordado de una puerta**: por cada cara, el estado real que tenía en la última observación de la
  puerta (FR-208), o «sin observar» si el jugador nunca la observó (FR-212). Las dos caras de una puerta con
  vuelta pueden recordarse con estados distintos; una salida cuenta como recordada abierta solo si se recuerda
  abierta la cara de la sala de la que sale.
- **Observación**: momento en que el jugador ve el estado real de una puerta (FR-207).
- **Antorcha**: objeto de P1 §2.7; mientras está encendida, cada entrada explora también las vecinas
  (FR-210).
- **Esqueleto de la cripta**: todas las salas y salidas descargadas por el programa; es infraestructura y no
  es conocimiento del jugador (FR-218).
- **Viaje («ir a»)**: secuencia de pasos que lleva al jugador a una sala explorada (FR-250).
- **Paso**: un movimiento ordinario del viaje; es una acción completa del jugador (FR-254, FR-263).
- **Motivo de detención**: la causa por la que termina un viaje o se rechaza la orden (FR-258, FR-260).

---

## Trazabilidad del Apéndice B «Niebla de guerra e «ir a»» (Principio X)

| # | Caso del Apéndice B | Escenario | Requisitos | Prueba |
|---|---|---|---|---|
| 1 | `ir a` hacia una sala no explorada: se rechaza y no consume tiempo | H6-1 | FR-251 | Se define en `tasks.md` |
| 2a | El mapa recuerda abierta una puerta que en realidad está cerrada: al observarla, el mapa se actualiza… | H2-1 (parte del mapa) | FR-207, FR-209 | Se define en `tasks.md` |
| 2b | …y la ruta se recalcula; si no queda ruta, el viaje se detiene sin consumir tiempo adicional | H7-1, H7-2 | FR-255, FR-256, FR-259, FR-260 | Se define en `tasks.md` |
| 3 | `ir a` entra a una sala con enemigos dormidos: se activan según P1 §2.4 y el viaje se detiene | H7-3 | FR-258, FR-260 | Se define en `tasks.md` |
| 4 | Con la antorcha encendida, entrar a una sala explora sus vecinas sin activar sus enemigos ni sus trampas | H3-1 | FR-210, FR-211 | Se define en `tasks.md` |
| 5 | Un pergamino revierte una entrada con antorcha encendida: las salas exploradas por la antorcha vuelven a su estado anterior | H4-1 | FR-222 | Se define en `tasks.md` |
| 6 | Un pergamino durante un viaje: revierte solo el último paso y el viaje no continúa | H7-7 | FR-222, FR-262 | Se define en `tasks.md` |

Escenarios adicionales (no provienen del Apéndice B):

| Adicional | Comportamiento | Escenario | Requisitos | Prueba |
|---|---|---|---|---|
| A1 | Sala inicial explorada en el instante 0 y sus vecinas avistadas | H1-1 | FR-201, FR-202, FR-204, FR-205, FR-206 | Se define en `tasks.md` |
| A2 | Entrar a una sala la explora y deja avistados los destinos de sus salidas | H1-2, H1-6 | FR-203 | Se define en `tasks.md` |
| A3 | Precarga y esqueleto no cambian el conocimiento | H1-5 | FR-217, FR-218 | Se define en `tasks.md` |
| A4 | Puerta con cierre automático figura abierta y está cerrada | H2-2 | FR-208 | Se define en `tasks.md` |
| A5 | La antorcha explora a través de una salida cerrada | H3-2 | FR-210 | Se define en `tasks.md` |
| A6 | Con la antorcha apagada no se exploran las vecinas | H3-3 | FR-214 | Se define en `tasks.md` |
| A7 | Guardar y cargar conserva el mapa | H4-3 | FR-221 | Se define en `tasks.md` |
| A8 | El pergamino revierte la observación de una puerta | H4-2 | FR-222 | Se define en `tasks.md` |
| A9 | `historia` muestra el mapa conocido de ese instante | H4-4 | FR-223 | Se define en `tasks.md` |
| A10 | `--replay` produce el mismo mapa | H4-5 | FR-224 | Se define en `tasks.md` |
| A11 | El comando de ver el mapa no muestra salas desconocidas | H5-1 | FR-219 | Se define en `tasks.md` |
| A12 | Ver el mapa no altera la partida | H5-4 | FR-220 | Se define en `tasks.md` |
| A13 | Una salida sin vuelta que sale de una sala explorada deja avistado su destino | H1-3 | FR-204 | Se define en `tasks.md` |
| A14 | Una sala avistada solo muestra su existencia | H1-4 | FR-204, FR-217 | Se define en `tasks.md` |
| A15 | Una puerta que cambia mientras el jugador está en su sala se observa en ese momento | H2-3 | FR-207 | Se define en `tasks.md` |
| A16 | La puerta de una salida sin vuelta se observa solo desde la sala de la que sale; la sala de origen de una salida sin vuelta hacia una sala explorada sigue desconocida | H2-4 | FR-204, FR-207 | Se define en `tasks.md` |
| A17 | La antorcha deja avistados, sin explorarlos, los destinos de las salidas de las vecinas | H3-4 | FR-213 | Se define en `tasks.md` |
| A18 | Entrar después a una sala explorada con la antorcha revela su contenido y aplica P1 | H3-5 | FR-216 | Se define en `tasks.md` |
| A19 | Las puertas nunca observadas de una vecina explorada con la antorcha figuran «sin observar» | H3-6 | FR-205, FR-207, FR-212 | Se define en `tasks.md` |
| A20 | Encender la antorcha estando ya en una sala no cambia el mapa | H3-7 | FR-210, FR-215 | Se define en `tasks.md` |
| A21 | El comando de ver el mapa muestra el estado recordado, no el real | H5-2 | FR-208, FR-219 | Se define en `tasks.md` |
| A22 | El comando muestra una sala explorada con la antorcha sin contenido y con sus puertas «sin observar» | H5-3 | FR-211, FR-212, FR-219 | Se define en `tasks.md` |
| A23 | Dos salidas hacia la misma sala avistada se muestran por separado, sin identificador, hasta explorarla | H5-5 | FR-204, FR-219 | Se define en `tasks.md` |
| A24 | El viaje toma la ruta de menor costo y cada paso consume el tiempo de su salida | H6-2 | FR-253, FR-254 | Se define en `tasks.md` |
| A25 | Con rutas de igual costo, el primer paso va a la vecina de menor identificador | H6-3 | FR-253 | Se define en `tasks.md` |
| A26 | El viaje no abre puertas aunque el jugador tenga la llave | H6-4 | FR-252, FR-257, FR-259 | Se define en `tasks.md` |
| A27 | Una salida con puerta «sin observar» no cuenta como recordada abierta | H6-5 | FR-212, FR-252 | Se define en `tasks.md` |
| A28 | El viaje solo usa salas exploradas | H6-6 | FR-217, FR-252 | Se define en `tasks.md` |
| A29 | Entre los pasos ocurren los eventos del reloj | H6-7 | FR-254 | Se define en `tasks.md` |
| A30 | Destino en la sala actual: sin pasos y sin tiempo | H6-8 | FR-251 | Se define en `tasks.md` |
| A31 | Cada paso aplica las reglas de una entrada ordinaria (antorcha, enemigos, trampas) | H6-9 | FR-264 | Se define en `tasks.md` |
| A32 | El cálculo de un paso tarda menos de 5 ms | H6-10 | NFR-250, NFR-251 | Se define en `tasks.md` |
| A33 | El viaje se detiene si entra a una sala con enemigos activos | H7-4 | FR-258, FR-260 | Se define en `tasks.md` |
| A34 | El viaje se detiene al recibir daño | H7-5 | FR-258, FR-260 | Se define en `tasks.md` |
| A35 | El viaje se detiene al llegar y la interfaz lo indica | H7-6 | FR-258, FR-260 | Se define en `tasks.md` |
| A36 | `partida.log` registra cada paso como movimiento y la orden como comentario; `--replay` da el mismo resultado | H7-8 | FR-261 | Se define en `tasks.md` |
| A37 | Cada paso cuenta como acción en la línea de tiempo; la orden no | H7-9 | FR-263 | Se define en `tasks.md` |
| A38 | El mapa conocido ofrece a «ir a» solo las salidas entre salas exploradas con puerta recordada abierta, con costo igualado e identificador real | H2-5 | FR-205, FR-212, FR-225 | Se define en `tasks.md` |
| A39 | El costo de cada salida que se conoce y se muestra es el igualado según 001 FR-101 | H5-6 | FR-205, FR-219 | Se define en `tasks.md` |
| A40 | El reporte de resolubilidad se muestra completo con `--forzar` y no cambia el mapa conocido | H5-7 | FR-202, FR-217 | Se define en `tasks.md` |
| A41 | Un cazador que se mueve por salas desconocidas no cambia el mapa conocido | H1-7 | FR-218 | Se define en `tasks.md` |
| A42 | Las caras de una puerta con estados distintos se recuerdan por separado; a «ir a» solo se ofrece la salida cuya cara de origen se recuerda abierta | H2-6 | FR-207, FR-208, FR-225 | Se define en `tasks.md` |
| A43 | Si la antorcha se apaga en el mismo instante de la entrada, decide el orden en que se programaron los eventos | H3-8 | FR-210, FR-214 | Se define en `tasks.md` |

Cada prueba citará el identificador del requisito que verifica (Principio X).

---

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-201**: Los casos del Apéndice B que son de esta parte (antorcha, pergamino con antorcha y la parte del
  mapa de la puerta recordada abierta) pasan como pruebas automatizadas, y cada una cita su requisito.
- **SC-202**: En cada acción de una partida de prueba de al menos 200 acciones *(decisión del grupo)*, con y
  sin antorcha, lo que la interfaz recibe para dibujar el mapa (vista, comando de ver el mapa y resumen de
  `historia`) no contiene el identificador, el nombre, las salidas ni el contenido de ninguna sala
  desconocida, ni más que la existencia de las salas avistadas; se comprueba automáticamente. El reporte de
  resolubilidad al iniciar no cuenta: es la excepción de FR-217.
- **SC-203**: Con `--bench`, el tiempo medio de una consulta de estado de sala o de puerta recordada varía
  menos de un factor 2 entre la cripta sintética más pequeña y la más grande, siendo la más grande al menos
  10 veces mayor *(decisión del grupo)*.
- **SC-204**: Con `--bench`, explorar con la antorcha la misma cantidad de vecinas cuesta un tiempo que varía
  menos de un factor 2 entre un mapa conocido pequeño y uno al menos 10 veces mayor *(decisión del grupo)*.
- **SC-205**: En el 100 % de los casos probados, guardar y cargar, revertir con un pergamino y reproducir con
  `--replay` dejan el mapa conocido idéntico al esperado (estado de cada sala y de cada puerta recordada).
- **SC-206**: El ciclo de eventos entre dos decisiones del jugador se mantiene por debajo de 20 ms, medido con
  `--bench` en la misma cripta que usa la feature 001 (NFR-101 y SC-104: una cripta sintética de 1 000 salas
  en cuadrícula con 30 cazadores activos), con la antorcha encendida *(decisión del grupo)*.
- **SC-207**: Con `--bench`, registrar e invertir con el pergamino la misma cantidad de cambios del mapa
  conocido varía menos de un factor 2 entre un mapa conocido pequeño y uno al menos 10 veces mayor
  *(decisión del grupo)*.
- **SC-250**: Los 4 casos del Apéndice B de «ir a» (destino no explorado, puerta recordada abierta que está
  cerrada, enemigos dormidos y pergamino durante un viaje) pasan como pruebas automatizadas, y cada una cita su
  requisito.
- **SC-251**: En el 100 % de los viajes probados, la ruta usa solo salas exploradas y salidas recordadas abiertas,
  no abre ninguna puerta, y cada paso coincide con el que resulta de calcular la ruta desde cero con el
  conocimiento de ese momento, con el desempate por menor identificador.
- **SC-252**: Con `--bench`, el cálculo de un paso de «ir a» con el mapa conocido completo de la cripta de
  referencia (o de una sintética de tamaño equivalente) tarda menos de 5 ms (el «5 ms» sale de la tabla de §6.1
  del enunciado).
- **SC-253**: En el 100 % de los viajes probados, reproducir `partida.log` con `--replay` deja la partida y el
  mapa conocido idénticos a los originales, y la línea de tiempo cuenta exactamente un paso por acción.

---

## Suposiciones

- Las puertas y sus estados son los de P1; esta feature no agrega estados de puerta, solo los recuerda.
- «Mientras está en una sala» (FR-207) se interpreta literalmente: un cambio de una puerta que tiene una cara
  en la sala actual se observa en el momento en que ocurre.
- Las vecinas de una sala son los destinos de sus salidas; una sala que solo tiene una salida hacia la sala
  actual no es vecina de ella (y sigue desconocida si no es destino de ninguna salida de una sala explorada,
  FR-204).
- El nombre del comando para ver el mapa y la forma en que se dibuja los define la interfaz (integrante 3);
  esta spec solo fija qué información muestra y qué no.
- El estado inicial de la antorcha y su duración no cambian respecto de P1 §2.7.
- Leer un pergamino no es una acción del jugador (P1 §2.11); revertir no genera conocimiento nuevo.
- Un archivo de partida de la primera parte no contiene mapa conocido y se trata con FR-421 de la feature 004.
