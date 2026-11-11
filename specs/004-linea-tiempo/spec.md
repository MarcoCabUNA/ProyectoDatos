# Especificación: Línea de tiempo de la partida

**Feature**: `004-linea-tiempo`

**Creada**: 2026-11-10

**Estado**: Borrador

**Fuente**: Cripta - Parte II §3.6, §7.3 y Apéndice B «Línea de tiempo»; Primer Proyecto (P1) §2.11 (pergamino de retroceso) y §4.10 (versión del archivo de partida)

**Constitución**: v1.2.0 · Requisitos con prefijo FR-4xx (Principio IX)

**Fuera de alcance**: el comando «ir a» y el mapa conocido son de la feature `002-niebla-ir-a`; esta spec solo exige que el resumen incluya el mapa conocido cuando exista. La verificación de resolubilidad es de la feature `003-resolubilidad`.

**Entrada**: Descripción del usuario: "Línea de tiempo de Cripta II. Consultar, sin modificar la partida, el estado en cualquier instante pasado desde el inicio, de forma independiente del pergamino de retroceso (limitado a 5 acciones). Comandos «historia <t>» e «historia #k»; modo sin interacción «--replay partida.log --hasta <t>»; las acciones revertidas con un pergamino dejan de existir en la línea; «--checkpoint-cada K»; guardar y cargar conserva la línea completa; un archivo de la primera parte se reporta incompatible o se migra explícitamente. Requisitos FR-401 en adelante. No nombrar estructuras de datos, clases ni módulos."

> Este archivo contiene reglas del juego, historias, escenarios y requisitos. No nombra estructuras
> de datos, clases ni módulos: eso va en `plan.md` (Principio IX). Se confirma con un commit antes
> de cualquier código de esta feature.

## Convenciones de los ejemplos

- «t» es el reloj virtual, un entero ≥ 0. El reloj actual es el instante de la partida en curso.
- «Acción número k» es la k-ésima acción del jugador, contada desde 1 en el orden en que quedó la
  historia de la partida (FR-413). Las consultas no cuentan como acciones.
- «Resumen» es la información que muestra una consulta (FR-405).
- «Evento» es cualquier cosa que ocurre en un instante: una acción del jugador o de un enemigo, un cambio
  de puerta, el vencimiento de un efecto, etc.

## Clarificaciones

### Sesión 2026-11-11

- P: Cuando en el instante t hay eventos con el mismo tiempo y también una decisión del jugador, las dos frases
  del enunciado (§3.6) dan estados distintos. ¿Cuál prevalece? → R: Si a t le corresponde una decisión del
  jugador, `historia <t>` muestra el estado justo antes de esa decisión, incluyendo los eventos con tiempo t que
  ya se habían ejecutado antes de pedírsela al jugador (el orden de eventos con el mismo tiempo es
  determinista), de modo que `historia <t>` e `historia #k` coinciden para ese instante. Si en t no hay
  decisión del jugador, se muestra el estado después de todos los eventos con tiempo ≤ t (FR-402).

---

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Consultar un instante pasado durante la partida (Prioridad: P1)

Como jugador, quiero preguntar cómo estaba la partida en un instante pasado, o justo antes de una de mis
acciones, sin que eso afecte mi partida, para entender qué decisiones me trajeron hasta aquí.

**Por qué esta prioridad**: es la capacidad central de la feature; las demás historias la protegen o la
extienden.

**Prueba independiente**: jugar varias acciones, consultar instantes y acciones anteriores, y comprobar que el
resumen coincide con lo vivido y que la partida sigue exactamente igual después de consultar.

**Escenarios de aceptación**:

1. *(Apéndice B, caso 1)* **Dada** una partida con el reloj en t = 500, **cuando** el jugador escribe
   `historia 800`, **entonces** la consulta se rechaza con un mensaje que indica que el instante es posterior
   al reloj actual (500), no se muestra ningún resumen y el estado de la partida no cambia. *(FR-409)*
2. *(Apéndice B, caso 3)* **Dado** que en t = 300 ocurren varios eventos (por ejemplo, un enemigo ataca, una
   puerta se cierra sola y expira un efecto) y a t = 300 no le corresponde ninguna decisión del jugador,
   **cuando** el jugador escribe `historia 300`, **entonces** el resumen muestra el estado después de
   ejecutar todos esos eventos. *(FR-402)*
3. *(Apéndice B, caso 4)* **Dada** una partida con el reloj en t = 500 y 5 acciones realizadas, todas
   revertibles, **cuando** el jugador escribe `historia 200` o `historia #3`, **entonces** el reloj
   sigue en 500, no se programa ni se ejecuta ningún evento, el archivo `partida.log` no gana ninguna línea
   y el historial de retroceso conserva, antes y después de la consulta, esas mismas 5 acciones
   revertibles. *(FR-407, FR-408)*
4. **Dado** que el jugador ya realizó 6 acciones, **cuando** escribe `historia #4`, **entonces** el resumen
   describe el estado justo antes de que el jugador tomara su cuarta acción: su sala, vida, estadísticas,
   inventario, efectos activos, los enemigos de esa sala con su vida y el mapa conocido en ese momento.
   *(FR-404, FR-405)*
5. **Dado** que el jugador realizó 6 acciones, **cuando** escribe `historia #9` o `historia #0`, **entonces**
   la consulta se rechaza indicando el rango válido de acciones, sin cambiar la partida. *(FR-409)*
6. **Dada** una partida donde el jugador lleva 20 acciones y el pergamino solo permite revertir las últimas 5,
   **cuando** consulta `historia #2`, **entonces** obtiene el resumen de esa acción aunque ya no sea
   revertible. *(FR-401, FR-414)*
7. **Dada** una partida con el reloj en t = 500, **cuando** el jugador escribe `historia 500`, **entonces**
   la consulta se acepta (t no es posterior al reloj actual) y muestra el estado que corresponde a ese
   instante según FR-402. *(FR-409)*
8. **Dada** la misma consulta repetida dos veces seguidas, **cuando** se comparan los dos resúmenes,
   **entonces** son idénticos. *(FR-419)*

---

### Historia 2 — Consultar sin interacción con `--replay … --hasta` (Prioridad: P1)

Como evaluador o jugador, quiero reproducir una partida guardada en `partida.log` hasta un instante y ver el
resumen sin abrir ninguna ventana, para verificar partidas de forma automática.

**Por qué esta prioridad**: es el modo con el que se prueban de forma automatizada los demás escenarios
(Principios V y X).

**Prueba independiente**: ejecutar `--replay partida.log --hasta t` sobre un registro conocido y comparar el
resumen con el esperado, sin interfaz gráfica.

**Escenarios de aceptación**:

1. **Dado** un `partida.log` de una partida de 10 acciones, **cuando** se ejecuta
   `--replay partida.log --hasta t` con t dentro de la partida, **entonces** se imprime el mismo resumen que
   mostraría `historia t` en esa partida, sin crear ninguna ventana. *(FR-410, FR-411)*
2. *(Apéndice B, caso 5)* **Dado** un `partida.log` cuya partida terminó en t = 900, **cuando** se ejecuta
   `--replay partida.log --hasta 1500`, **entonces** se imprime el resumen del estado final e indica de forma
   explícita que la partida terminó antes de t = 1500. *(FR-412)*
3. **Dado** un `partida.log` y `--hasta` con un valor no entero, negativo o ausente, **cuando** se ejecuta
   el comando, **entonces** se informa el error de uso y no se reproduce nada. *(FR-410)*
4. **Dado** un `partida.log` inexistente o ilegible, **cuando** se ejecuta el comando, **entonces** se informa
   con contexto y el programa termina sin caerse. *(FR-410)*
5. **Dado** un `partida.log` y `--hasta 0`, **cuando** se ejecuta el comando, **entonces** se imprime el
   resumen del estado inicial de la partida. *(FR-402, FR-410)*

---

### Historia 3 — La línea se mantiene correcta con el pergamino (Prioridad: P2)

Como jugador, quiero que lo que deshice con un pergamino ya no aparezca en la línea de tiempo, para que la
historia que consulto sea la de la partida tal como quedó.

**Por qué esta prioridad**: sin esto la línea mostraría acciones que dejaron de existir y las consultas serían
engañosas.

**Prueba independiente**: realizar acciones, usar un pergamino, volver a actuar y consultar instantes y
acciones; ninguna consulta debe mostrar lo revertido.

**Escenarios de aceptación**:

1. *(Apéndice B, caso 2)* **Dado** que el jugador realizó las acciones 1 a 5 (la acción 4 lo dejó en la sala 7
   y la acción 5 lo llevó a la sala 9) y luego usó un pergamino que revirtió la acción 5, **cuando** consulta
   `historia #5`, **entonces** la consulta se rechaza por estar fuera de rango (solo existen 4 acciones);
   y **cuando** consulta el instante actual, **entonces** el resumen muestra al jugador en la sala 7, no en la
   9, como si la acción 5 nunca hubiera ocurrido. *(FR-404, FR-409, FR-413)*
2. **Dado** el mismo caso anterior, **cuando** el jugador realiza una acción nueva y consulta `historia #5`,
   **entonces** el resumen describe el estado justo antes de esa acción nueva, que ahora es la número 5.
   *(FR-413)*
3. **Dado** que se revirtió una acción con un pergamino y el reloj retrocedió, **cuando** se consulta un
   instante anterior al reloj previo a la reversión pero posterior al reloj actual, **entonces** se rechaza
   según FR-409 (el límite es el reloj actual). *(FR-409, FR-413)*
4. **Dado** que se usaron pergaminos varias veces seguidas, **cuando** se consultan instantes de cualquier
   parte de la partida, **entonces** ningún resumen incluye eventos de acciones revertidas. *(FR-413)*

---

### Historia 4 — La línea sobrevive a guardar y cargar (Prioridad: P2)

Como jugador, quiero guardar la partida y retomarla después con todo mi historial consultable, y que un archivo
de la versión anterior no se cargue por error.

**Por qué esta prioridad**: la persistencia es requisito de §3.6, y cargar en silencio un archivo antiguo
corrompería la línea.

**Prueba independiente**: consultar varios instantes, guardar, cargar y repetir las consultas; después intentar
cargar un archivo de la primera parte.

**Escenarios de aceptación**:

1. **Dada** una partida con 20 acciones, **cuando** se guarda y se carga, **entonces** cualquier
   `historia <t>` o `historia #k` devuelve el mismo resumen que antes de guardar. *(FR-420)*
2. **Dada** una partida cargada, **cuando** el jugador sigue jugando y consulta un instante anterior al guardado,
   **entonces** el resumen es correcto. *(FR-420)*
3. *(Apéndice B, caso 6)* **Dado** un archivo de partida generado por la primera parte, **cuando** se intenta
   cargar, **entonces** se reporta la incompatibilidad de formato (o se migra con un aviso explícito que indica
   qué parte de la línea no puede reconstruirse), la partida actual no se modifica y el archivo nunca se carga
   en silencio. *(FR-421)*

---

### Historia 5 — Configurar los puntos de control con `--checkpoint-cada K` (Prioridad: P3)

Como integrante del grupo, quiero decidir cada cuántas acciones del jugador se guarda una copia completa, para
equilibrar memoria y velocidad de consulta.

**Por qué esta prioridad**: es una restricción de recursos (§3.6) que no cambia lo que ve el jugador.

**Prueba independiente**: jugar la misma partida con distintos K y comprobar que los resúmenes son idénticos y
que ninguna consulta exige procesar más de K acciones.

**Escenarios de aceptación**:

1. **Dada** la misma partida jugada con K = 1, K = 5 y K = 50, **cuando** se hacen las mismas consultas,
   **entonces** los resúmenes son idénticos. *(FR-418)*
2. **Dada** una partida con K = 10, **cuando** se consulta cualquier instante, **entonces** la reconstrucción
   no requiere aplicar ni deshacer cambios de más de 10 acciones del jugador. *(FR-416)*
3. **Dado** `--checkpoint-cada 0`, un valor negativo o no entero, **cuando** se inicia el programa,
   **entonces** se informa el error y no se inicia con ese valor. *(FR-415)*
4. **Dado** que no se indica `--checkpoint-cada`, **cuando** se inicia el programa, **entonces** se usa el valor
   por defecto que fije el plan. *(FR-415)*

---

### Casos borde

- **t = 0**: devuelve el estado inicial de la partida (escenario H2-5).
- **t igual al reloj actual**: se acepta (escenario H1-7).
- **Acción número k igual a la siguiente por tomar**: `historia #k` solo acepta acciones ya realizadas; la que
  se va a tomar aún no existe y se rechaza (escenario H1-5).
- **Partida terminada** (el jugador murió o ganó): las consultas siguen disponibles sobre toda la historia.
- **Sin acciones realizadas**: `historia 0` se acepta; `historia #1` se rechaza.
- **Instante sin ningún evento**: el estado es el del último evento anterior.
- **Reloj retrocedido por un pergamino**: el límite de FR-409 se mide contra el reloj actual, no contra el
  mayor reloj alcanzado antes de la reversión (escenario H3-3).
- **Consultas encadenadas**: consultar muchas veces seguidas no cambia nada de la partida (FR-407).
- **Consulta tras un viaje de «ir a»** (spec 002): el viaje es una secuencia de acciones ordinarias; la
  línea las cuenta como acciones del jugador.
- **Argumentos inválidos**: `historia`, `historia abc`, `historia -3` y `historia #x` se rechazan con un mensaje
  de uso, sin cambiar la partida (FR-409).

---

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Estado en un instante**

- **FR-401**: El programa DEBE permitir consultar el estado de la partida en cualquier instante pasado desde
  el inicio, sin modificar la partida.
- **FR-402**: El estado en el instante t DEBE ser el estado después de ejecutar todos los eventos con tiempo
  menor o igual que t. Si a t le corresponde una decisión del jugador, DEBE ser el estado justo antes de
  tomarla, incluyendo los eventos con tiempo t que ya se habían ejecutado antes de pedírsela al jugador (el
  orden de eventos con el mismo tiempo es determinista); así `historia <t>` e `historia #k` coinciden para ese
  instante. Si en t no hay decisión del jugador, DEBE ser el estado después de todos los eventos con tiempo
  menor o igual que t.
- **FR-403**: El comando `historia <t>` DEBE mostrar el resumen del estado en el instante t, con t un entero ≥ 0.
- **FR-404**: El comando `historia #k` DEBE mostrar el resumen del estado justo antes de la acción número k
  del jugador, con k entre 1 y el número de acciones del jugador realizadas.
- **FR-405**: Cada resumen DEBE mostrar como mínimo: el reloj, la sala del jugador, su vida y estadísticas, su
  inventario, sus efectos activos, los enemigos de esa sala con su vida, y el mapa conocido en ese momento
  (cuando la feature 002 esté disponible).
- **FR-406**: El cursor del inventario y los mensajes del juego NO forman parte del estado consultable y NO
  DEBEN aparecer en el resumen.
- **FR-419**: El resumen de un instante DEBE ser exactamente el estado que la partida tuvo al vivirlo,
  incluidos los resultados que dependen de azar, y DEBE ser idéntico en cada consulta repetida.

**La consulta no altera la partida**

- **FR-407**: Una consulta NO DEBE consumir tiempo virtual, NO DEBE contar como acción del jugador, NO DEBE
  programar ni ejecutar eventos y NO DEBE modificar ningún estado del juego ni el historial de retroceso.
- **FR-408**: Una consulta NO DEBE registrarse en `partida.log`.
- **FR-409**: Una consulta con un instante posterior al reloj actual, con un número de acción fuera del rango
  válido (FR-404), o con argumentos mal formados DEBE rechazarse con un mensaje que explique el motivo y el
  rango válido, sin mostrar resumen y sin modificar la partida.
- **FR-423**: La interfaz DEBE ofrecer los comandos `historia <t>` e `historia #k` y mostrar el resumen
  (§7.3).

**Consulta sin interacción**

- **FR-410**: El programa DEBE aceptar `--replay partida.log --hasta <t>`, reproducir la partida hasta el
  instante t e imprimir el resumen. Si `--hasta` falta, no es un entero ≥ 0, o el archivo no existe o no se
  puede leer, DEBE informar el error con contexto y terminar sin caerse.
- **FR-411**: El resumen de `--replay … --hasta` DEBE ser el mismo que mostraría `historia <t>` en esa
  partida, y el modo DEBE ejecutarse sin instanciar la interfaz gráfica (Principio V).
- **FR-412**: Si t es posterior al final de la partida, `--replay … --hasta` DEBE mostrar el resumen del
  estado final e indicar de forma explícita que la partida terminó antes de t.

**Interacción con el pergamino de retroceso**

- **FR-413**: Las acciones revertidas con un pergamino DEBEN dejar de existir en la línea de tiempo: ninguna
  consulta puede mostrar sus efectos, y la numeración de acciones y el reloj DEBEN reflejar la historia de la
  partida tal como quedó.
- **FR-414**: La línea de tiempo DEBE ser independiente del límite de 5 acciones del pergamino: puede
  consultarse cualquier instante desde el inicio, aunque la acción ya no se pueda revertir.

**Puntos de control**

- **FR-415**: El programa DEBE aceptar `--checkpoint-cada K` con K un entero ≥ 1. Un valor inválido DEBE
  rechazarse con un mensaje y no iniciar el programa con ese valor. Si no se indica, DEBE usarse el valor por
  defecto que el plan justifique con mediciones (§3.6, Principio VIII); esta spec no lo fija.
- **FR-416**: El programa NO DEBE guardar copias completas del estado con una frecuencia mayor a una cada K
  acciones del jugador, y NINGUNA consulta DEBE requerir aplicar o deshacer cambios de más de K acciones del
  jugador.
- **FR-417**: Fuera de las copias completas, el programa SOLO DEBE almacenar la información necesaria para
  reconstruir los cambios del estado.
- **FR-418**: El resultado de una consulta NO DEBE depender del valor de K.

**Guardar y cargar**

- **FR-420**: Guardar y cargar la partida DEBE conservar la línea de tiempo completa: tras cargar, cualquier
  consulta DEBE devolver el mismo resumen que antes de guardar.
- **FR-421**: Un archivo de partida de la primera parte, o de cualquier versión distinta a la actual, DEBE
  detectarse y reportarse como incompatible con contexto, o migrarse de forma explícita avisando al usuario
  de lo que se conserva y lo que no. NUNCA DEBE cargarse en silencio, el programa NO DEBE caerse, y si no se
  carga, la partida actual NO DEBE modificarse.

### Requisitos de rendimiento y de recursos

- **NFR-401**: Las decisiones de diseño de la línea de tiempo (valor por defecto de K, estrategia de
  reconstrucción) DEBEN respaldarse con mediciones de `--bench` que cubran al menos tres valores de K
  y la alternativa sin puntos de control, DEBEN justificar el valor por defecto de K y DEBEN documentarse en
  `DECISIONES.md` (§3.6, §5.5, §6.3, Principio VIII).
- **NFR-402**: La memoria total de la línea de tiempo DEBE crecer con la cantidad de cambios ocurridos más
  una copia completa cada K acciones del jugador, y NO con el producto de las acciones por el tamaño del
  estado (§5.5).
- **NFR-403**: Al usar un pergamino, la línea de tiempo DEBE recortarse sin recorrer toda la historia
  (§5.5).

### Entidades clave

- **Línea de tiempo**: la historia de la partida tal como quedó (sin acciones revertidas), consultable en
  cualquier instante desde el inicio hasta el reloj actual.
- **Instante**: valor del reloj virtual (entero ≥ 0).
- **Acción número k**: la k-ésima acción del jugador en la historia vigente.
- **Resumen**: vista de solo lectura del estado en un instante (FR-405).
- **Punto de control**: copia completa del estado, guardada como máximo una cada K acciones del jugador.
- **Partida registrada (`partida.log`)**: registro de las acciones de la partida con el que se reproduce sin
  interacción.

---

## Trazabilidad del Apéndice B «Línea de tiempo» (Principio X)

| # | Caso del Apéndice B | Escenario | Requisitos | Prueba |
|---|---|---|---|---|
| 1 | `historia <t>` con t mayor que el reloj actual: se rechaza | H1-1 | FR-409 | Se define en `tasks.md` |
| 2 | `historia` después de usar un pergamino: no muestra las acciones revertidas | H3-1 | FR-404, FR-409, FR-413 | Se define en `tasks.md` |
| 3 | Varios eventos en el mismo instante t: `historia <t>` muestra el estado después de todos ellos | H1-2 | FR-402 | Se define en `tasks.md` |
| 4 | `historia` no consume tiempo virtual, no se registra en `partida.log` y no modifica el historial de retroceso | H1-3 | FR-407, FR-408 | Se define en `tasks.md` |
| 5 | `--replay … --hasta t` con t posterior al final: muestra el estado final e indica que la partida terminó antes | H2-2 | FR-412 | Se define en `tasks.md` |
| 6 | Se carga un archivo de la primera parte: incompatibilidad reportada o migración explícita; nunca en silencio | H4-3 | FR-421 | Se define en `tasks.md` |

Cada prueba citará el identificador del requisito que verifica (Principio X).

---

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-401**: Los 6 casos del Apéndice B «Línea de tiempo» pasan como pruebas automatizadas, y cada una cita
  su requisito.
- **SC-402**: En una partida de al menos 200 acciones del jugador, el 100 % de las consultas `historia <t>` e
  `historia #k` coinciden con el estado que la partida tuvo al vivirlo.
- **SC-403**: Tras cualquier secuencia de consultas, el reloj, `partida.log` y el historial de retroceso son
  idénticos a los de una partida donde no se consultó nada.
- **SC-404**: La misma partida jugada con K = 1, K = 5 y K = 50 produce resúmenes idénticos en el 100 % de las
  consultas.
- **SC-405**: Una consulta `historia` se contesta en menos de 50 ms en una partida de al menos 5 000 acciones
  del jugador, con el valor de K por defecto, medido con --bench (§6.1 y §6.3 de la Parte II).
- **SC-406**: Guardar, cargar y repetir las consultas devuelve resúmenes idénticos en el 100 % de los casos
  probados, y los archivos de la primera parte se rechazan o migran con aviso en el 100 % de los casos.

---

## Suposiciones

- Los instantes son enteros del reloj virtual; no hay instantes fraccionarios.
- Los eventos con igual tiempo se ordenan de forma determinista (Principio IV), de modo que el estado en un
  instante está bien definido (FR-402).
- El pergamino de retroceso (P1 §2.11) y su límite de 5 acciones no cambian.
- `partida.log` ya existe como registro de las acciones de la partida; esta feature solo exige que permita
  reproducirla hasta un instante.
- El mapa conocido es el de la feature 002; mientras no exista, el resumen omite esa sección.
- El valor por defecto de K se define en `plan.md` con mediciones, no aquí.
- Se asume que cada paso de «ir a» es una acción ordinaria del jugador; se confirmará en la spec 002.
- Leer un pergamino no cuenta como acción del jugador (P1 §2.11): no recibe número de acción, y por eso las
  acciones revertidas dejan de existir en la línea (FR-413).
