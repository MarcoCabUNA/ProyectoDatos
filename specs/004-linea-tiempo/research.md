# Investigación: Línea de tiempo de la partida

**Feature**: `004-linea-tiempo` · **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Cada decisión lleva: problema, alternativas, decisión, complejidad, medición prevista y límites. Las
secciones de `DECISIONES.md` (§5.5 y §5.6 de la Parte II) salen de aquí. Las mediciones son
**previstas**: ninguna cifra de este archivo es un resultado.

## R0. Revisión de las estructuras ya implementadas (Principio II)

Revisadas contra lo que pide la Parte II §3.6 y §5.5. «No se toca» significa que no se modifica
ninguna línea (Abierto/Cerrado).

| Estructura | Qué hace hoy | Limitación frente a la línea de tiempo | Conclusión |
|---|---|---|---|
| `Logic/HistorialRetroceso.py` | Buffer circular de 5 intervalos; cada intervalo es un arreglo de funciones que invierten un cambio. | (1) Tope de 5, que es correcto para el pergamino (P1 §2.11). (2) Guarda **funciones**: no se pueden escribir en disco ni llevan tiempo. (3) El pergamino se lee, se suelta y se descuenta **fuera** del historial (`Inventario.py:227`, `Mazmorra.soltar_objeto/recoger_objeto(reversible=False)`, `Motor._usar_pergamino`), así que no se puede reconstruir hacia atrás. (4) Mientras se deshace ignora los registros nuevos. | **No se toca y no sirve** como línea. Esta feature no registra nada nuevo en él (decisión 9). |
| `Logic/PartidaGuardada.py` | `guardar(motor, …)` pasa el estado vivo a DTOs (copia hecha a mano: `list(...)`, un DTO por cosa); `cargar(partida, salas, cripta, salas_esqueleto, fn_ficha, fn_mensaje)` arma un `Motor` nuevo. Guarda el estado del azar, los eventos **válidos** en orden, los efectos, el rastro y todas las salas. | No guarda: historial, mensajes, caché de rutas. El mapa conocido (spec 002, FR-223) será un campo de `PartidaGuardadaDTO` que actualiza el motor; lo agrega Derek. Cada copia recorre todas las salas, los eventos y el inventario: O(S + E + V + I). | **Se reutiliza tal cual** como mecanismo de punto de control y de reconstrucción. No se toca. Coincide con lo que exige la Parte II: el punto de control incluye el estado de `random.Random`. |
| `Estructuras/BufferCircular.py` | Capacidad fija; al llenarse pisa el más antiguo. | Pierde lo más antiguo; la línea debe conservar **todo** desde el inicio. | **No sirve.** |
| `Estructuras/Cola.py` | Cola enlazada FIFO (encolar, desencolar, ver frente). | Sin acceso por posición ni búsqueda por tiempo: ubicar un punto de control sería O(n). | **No sirve.** |
| `Estructuras/ListaDoble.py` | Lista doblemente enlazada. | Acceso por posición O(n): imposible la búsqueda binaria. | **No sirve.** |
| `Estructuras/Ordenador.py` | Ordenamiento híbrido (inserción / mezcla) con comparador. | La línea nace ordenada por tiempo (se agrega siempre al final), así que no hay nada que ordenar. | **No se usa** (se menciona para dejar constancia de que no hace falta). |
| `Estructuras/MonticuloMinimo.py` | Montículo binario (feature 001). | No ayuda a ubicar por tiempo. | No se usa. |
| `Logic/ColaEventos.py` | Montículo de eventos con secuencia de desempate; descarta inválidos al llegar a la raíz. | `ver_siguiente()` permite mirar sin extraer; no hace falta tocarla para `avanzar_hasta(t)`. | No se toca. |
| `list` como arreglo | Almacenamiento contiguo (permitido). | `append` y `pop()` del final son O(1) amortizado; sirven para acciones, marcadores y puntos de control. | **Se usa** para los cuatro arreglos de la línea. |

Conclusión de la revisión: lo único nuevo en `Estructuras/` es una **búsqueda binaria propia** sobre
un arreglo ordenado (R5). Sin `bisect`.

## R1. Reconstruir hacia adelante o hacia atrás (decisión 1)

- **Problema**: obtener el estado en un instante pasado cumpliendo que ninguna consulta aplique o
  deshaga cambios de más de K acciones del jugador (FR-416).
- **Alternativas**:
  1. *Hacia atrás*: partir del estado actual e invertir cambios (como el pergamino).
  2. *Hacia adelante*: partir del punto de control más cercano **anterior** al instante y
     re-simular las acciones vigentes.
  3. *Sin puntos de control*: re-simular desde el inicio (la alternativa que pide medir §6.3).
- **Decisión**: **hacia adelante** (2).
- **Razones**:
  - Hacia atrás exigiría registrar la inversión de **todos** los cambios de toda la partida. El
    historial actual guarda funciones (no se pueden escribir en disco ni llevan tiempo), así que
    habría que crear un segundo historial completo, con su propio formato guardable.
  - El pergamino queda fuera del historial: se lee, se suelta y se descuenta sin registrar. Esos
    cambios no se pueden invertir hacia atrás.
  - Hacia adelante reutiliza `PartidaGuardada` (ya guarda y restaura el azar, la cola y los
    efectos) y las mismas reglas del motor, así que lo que se ve es lo que la partida vivió (FR-419).
  - Lo único que se guarda entre puntos de control son las **acciones vigentes** (tipo y
    parámetros): memoria proporcional al número de acciones, no al tamaño del estado (NFR-402).
- **Complejidad**: consulta = O(log P) para ubicar el punto de control + O(copia) para armar el
  `Motor` + O(K · ciclo de eventos) para re-simular. Memoria = O(A) acciones + O(A/K · copia).
  P = puntos de control, A = acciones vigentes.
- **Medición prevista**: M1 y M2 (ver plan). La comparación con la alternativa hacia atrás es
  **teórica** (no se implementa un segundo mecanismo solo para medirlo); la evidencia empírica es
  la comparación contra «sin puntos de control».
- **Límites**: el costo de re-simular crece con K y con la densidad de eventos entre decisiones.
  Un cambio de reglas del motor que rompa el determinismo (Principio IV) rompería también la línea.

## R2. Reconstrucción sin efectos (decisión 2)

- **Problema**: reconstruir no debe escribir `partida.log`, ni tocar la caché del catálogo vivo, ni
  gastar solicitudes (Principio VII), ni mostrar mensajes.
- **Alternativas**:
  1. Cargar con `ServicioGuardado.cargar` y ejecutar con `ServicioAccionJugador.ejecutar`: crearía
     un log nuevo, tocaría la caché y podría gastar solicitudes. **Descartada.**
  2. Guardar en memoria con `PartidaGuardada.guardar`/`cargar` directamente y despachar las
     acciones con un despacho propio que llama a los métodos del `Motor`.
- **Decisión**: (2). Piezas nuevas en `Service/`:
  - `ReconstructorEstado`: arma el `Motor` aparte con `PartidaGuardada.cargar(...)`, con
    `fn_mensaje=None` (el motor ya ignora los mensajes si no hay función), y re-simula.
  - `DespachoAcciones`: traduce un `AccionDTO` a la llamada del `Motor` (mover, abrir, atacar,
    esperar, recoger, soltar, equipar, usar). Nunca recibe `retroceder`. Es la tabla de
    `ServicioAccionJugador._ejecutar_en_el_motor` pero **sin** Data: no carga contenido, no anexa a la
    bitácora y no sincroniza usos de la caché.
  - La carga de salas durante la re-simulación sale de la propia línea (R3), nunca de Data.
- **Ubicación (Principio I)**: Service llama a Logic (`Motor`, `PartidaGuardada`) y **no** llama a
  Data. Logic no llama a Service ni a Data.
- **Duplicación consciente**: el despacho repite la correspondencia acción → método del motor. Se
  acepta (no se refactoriza `ServicioAccionJugador`, Principio III); una prueba compara, para una
  partida con todas las acciones, el estado del despacho propio contra el del servicio de acciones.
- **Complejidad**: construir un `Motor` es O(S + E + V + I) (lo mismo que `guardar`).
- **Límites**: si el motor cambia la firma de un método, hay que actualizar el despacho (la prueba
  de comparación lo detecta).

## R3. Autocontención de la línea: contenido y fichas (decisión 3)

- **Problema**: al re-simular una acción `mover` a una sala sin contenido, el servicio normal pide el
  contenido a Data y las fichas a la caché. Reconstruir no puede consultar a Data.
- **Alternativas**:
  1. *Cierre al cargar la sala*: al cargar una sala, pedir al catálogo las fichas de todo lo que la
     sala pueda necesitar (enemigos, trampas, objetos, objetos que sueltan los enemigos). **Descartada**:
     las fichas de objetos hoy se piden al recogerlos; pedirlas antes gasta solicitudes que la
     partida viva no gastaba (Principio VII).
  2. *Registro al primer uso* (elegida): dos adaptadores delgados en Service, que envuelven los
     objetos de Data que la partida ya usa, y registran en la línea lo que **la partida viva ya
     pidió**, una sola vez por id:
     - `ContenidoGrabador` envuelve `contexto.contenido`: en `asegurar_sala(id)` guarda el `SalaDTO`
       devuelto (contenido inicial de la sala) como **registro de carga**.
     - `ResolvedorGrabador` envuelve `contexto.resolvedor`: en `ficha(id)` guarda la ficha devuelta.
       Delega todo lo demás al resolvedor real.
     - **Ambos delegan TODO lo que no es `ficha()` o `asegurar_sala()`** al objeto original, incluidos
       `rechazo()` y `resolver_contenido()`. Si el objeto original lanza `ErrorDatos`, el error propaga
       y **no se registra nada**.
  3. *Guardar el catálogo completo en la línea*: tamaño proporcional al catálogo entero. **Descartada.**
- **Decisión**: (2). Sin solicitudes nuevas, sin tocar Data, sin tocar `ServicioAccionJugador`.
  Los adaptadores se instalan en los dos únicos puntos donde se arma un `ContextoPartida`
  (`ServicioPartida.iniciar_partida` y `ServicioGuardado.cargar`).
- **Costo en tamaño**: registros de carga ≤ una vez por sala (≤ S entradas, cada una con el
  contenido inicial: enemigos, objetos y trampas); fichas ≤ una por id distinto usado (≤ tamaño del
  catálogo). Ambos son **independientes de K y del número de acciones**: no crecen con la partida
  una vez vista cada sala. Se mide en M3.
- **Límite**: la línea depende de que Data devuelva fichas inmutables (DTO de solo datos): se guarda
  la referencia, no una copia. Si una ficha cambiara de versión durante la partida,
  `comprobar_compatibilidad` (versión de catálogo) ya lo impide.

### Hallazgo H-1 — el orden de carga de salas cambia la numeración de enemigos

`Mazmorra.cargar_contenido` numera a los enemigos con un contador por tipo (`contadores_tipo`,
«Rata #3»), y **cargar una sala no se deshace** con el pergamino (no se registra en el historial).
Si el jugador entró a una sala nueva en una acción que luego se revirtió, la sala **sigue cargada** y
el contador siguió avanzando. Re-simular solo las acciones vigentes cargaría las salas en otro
orden y numeraría distinto (rompe FR-419 en el nombre visible).

- **Solución sin reglas nuevas**: cada registro de carga guarda su **ordinal** (cuántas acciones
  vigentes llevaba la partida cuando se cargó). Los registros se guardan en el **orden real** de
  carga y **no se recortan** al usar un pergamino (siguen siendo hechos que ocurrieron). Al
  re-simular hasta un objetivo con `n` acciones completadas, se aplican, en orden, todos los
  registros **hasta el último cuyo ordinal sea ≤ n** (un prefijo del arreglo), saltando los que el
  punto de control ya trae cargados. Un prefijo conserva el orden real de numeración.
- **Efecto secundario aceptado**: una sala puede aparecer cargada un poco antes de que la partida viva
  la cargara; no es visible en el resumen (solo muestra los enemigos de la sala del jugador, que
  siempre está cargada).
- **Prueba prevista**: entrar a una sala nueva, revertirla con un pergamino, entrar a otra sala nueva
  y comprobar que `historia` muestra los mismos números que la partida viva.

## R4. Pergamino y recorte (decisión 4)

- **Problema**: las acciones revertidas deben dejar de existir (FR-413) sin recorrer toda la historia
  (NFR-403), y el pergamino se descuenta fuera del historial.
- **Alternativas**:
  1. Guardar todas las acciones, incluida `retroceder`, y re-ejecutarla al reconstruir. **Descartada**:
     la re-ejecución dependería del historial de 5 (que el motor aparte no tiene en el mismo estado)
     y violaría la decisión de no re-ejecutar `retroceder`.
  2. Guardar **solo las acciones vigentes** más un **marcador** de pergamino (elegida).
  3. Marcar las acciones como «revertida» sin borrarlas. **Descartada**: la numeración (FR-413)
     obligaría a saltarlas en cada consulta.
- **Decisión**: (2).
  - **Acciones vigentes**: arreglo de (tiempo de la decisión, `AccionDTO`). La acción número k es la
    posición k del arreglo: se cuentan **separadas de las líneas de `partida.log`** (que sí incluye
    la lectura del pergamino).
  - **Marcador de pergamino**: (posición p, `quitados`, `agregados`). `quitados` son los ids de
    pergaminos que salen del inventario y `agregados` los pergaminos que quedan en el inventario aunque
    la acción que los trajo se revirtió (regla de P1 §2.11, FR-424). Significa «cuando la partida
    llevaba p acciones vigentes, estos pergaminos salieron y estos otros quedaron». El descuento del
    pergamino usado para revertir es un «quitado». Al re-simular, al llegar a p acciones completadas
    se quitan los `quitados` del inventario (mismo `ubicar` + `soltar_actual` que el motor) y se
    agregan los `agregados` (con la ficha que la línea ya tiene). **Nunca** se re-ejecuta `retroceder`.
  - **Al usar un pergamino** (el jugador pasa de `c+1` a `c` acciones): se quita la última acción
    (`pop`), se quitan los puntos de control con más de `c` acciones (siempre los últimos del arreglo:
    a lo sumo uno si la acción revertida lo tenía) y los marcadores con posición mayor que `c` se
    **mueven a la posición `c`** (lo que ya persistía en la partida viva sigue persistiendo en el
    estado actual, pero no en los pasados). Después se calcula el marcador nuevo: se reconstruye el
    estado de `c` acciones (a lo sumo K acciones, no la historia) y se comparan sus pergaminos con los
    del inventario vivo: los que están en el reconstruido y no en el vivo son `quitados` (incluye el
    pergamino usado) y los que están en el vivo y no en el reconstruido son `agregados`. Si alguna
    de las dos listas no está vacía, se agrega el marcador en `c`. El recorte ocurre en el **final**
    de los arreglos: O(1 + r), con r los elementos quitados; no recorre la historia (NFR-403). La
    reconstrucción de `c` acciones cuesta lo de una consulta (acotada por K), no depende de la historia.
  - Los **registros de carga** y las **fichas** no se recortan (R3).
- **Detección de que una acción se hizo** (sin tocar `ServicioAccionJugador`): el registrador compara
  `jugador.acciones` antes y después de ejecutar: **+1** → acción nueva (se agrega); **−1** →
  pergamino leído (se recorta); **sin cambio** → rechazada (no se registra), igual que la bitácora.
- **Complejidad**: registrar acción O(1) amortizado (+ O(copia) cada K acciones); recortar O(1 + r).

### Hallazgo H-2 — recoger o soltar un pergamino dentro de la acción revertida

`Inventario` no registra los pergaminos en el historial (`Inventario.py:227`) y `Mazmorra`
marca como no reversible soltar y recoger un pergamino. Si la acción **revertida** era recoger o
soltar un pergamino, ese efecto **persiste** en la partida viva aunque la acción deje de existir. Un
marcador que solo dice «se descontó un pergamino» no lo reproduce.

- **Resuelto: es una regla de P1 §2.11**, que la spec fija como FR-424 (escenario H3-5): la reversión
  no deshace los pergaminos recogidos o soltados durante el intervalo revertido. La línea debe reflejar
  la cantidad de pergaminos igual que la partida viva (FR-419).
- **Decisión**: el marcador se generaliza a (posición, `quitados`, `agregados`) y se calcula al usar el
  pergamino como se describe en R4. No es una decisión pendiente ni un límite conocido.
- **Prueba**: H3-5 sin `skip` (el jugador recoge un pergamino en la acción 4 y usa otro para
  revertirla: el inventario del instante actual conserva el recogido y no tiene el consumido). Cita
  FR-413, FR-419 y FR-424.

## R5. Ubicar el punto de control más cercano (decisión 5)

- **Problema**: operación frecuente (§5.5): dado un instante o una acción, hallar el último punto de
  control anterior.
- **Alternativas**: (1) recorrido lineal: O(P). (2) búsqueda binaria propia sobre un arreglo
  ordenado: O(log P). (3) índice directo `k // K`: solo vale si los puntos de control están en
  posiciones regulares, pero el recorte por pergamino y un posible cambio de K lo vuelven frágil.
- **Decisión**: (2) en `Estructuras/BusquedaBinaria.py` (código nuevo, sin `bisect`): función
  `ultimo_menor_o_igual(arreglo, clave, extraer_clave)` que devuelve la posición del último elemento
  con clave ≤ la pedida, o −1. Se usa para los **puntos de control** (clave: acciones completadas) y
  para las **acciones vigentes** (clave: tiempo de la decisión), que también están ordenadas.
- **Complejidad**: O(log n) en tiempo, O(1) en espacio; el arreglo nace ordenado (se agrega siempre
  al final, y el recorte quita solo del final), así que no hay ordenamiento.
- **Medición prevista**: M4, con 100, 1 000 y 10 000 puntos de control, contra el recorrido lineal.
- **Límite**: dos decisiones nunca tienen el mismo tiempo (todo costo es ≥ 25), así que la clave
  de las acciones es estrictamente creciente.

## R6. `Motor.avanzar_hasta(t)` (decisión 6)

- **Problema**: la consulta de un instante entre dos decisiones del jugador necesita avanzar el reloj
  hasta t **sin** pasar de la siguiente decisión. `avanzar_hasta_jugador` no sirve: avanza hasta el
  jugador sin importar el tiempo.
- **Decisión**: método **nuevo** en `Logic/motorJuego.py`, sin tocar `avanzar_hasta_jugador`. Mientras
  no haya terminado la partida: mira el siguiente evento válido (`cola.ver_siguiente()`); si no hay,
  o su tiempo es mayor que t, se detiene; si no, lo extrae, adelanta el reloj y: si es el del jugador
  (una decisión), se detiene **justo antes** de tomarla; si no, lo ejecuta. Si la partida terminó en
  t, se detiene en cuanto `terminado` es verdadero: los demás eventos de t no se ejecutan (FR-402
  clarificado). Los eventos cancelados no cuentan: la cola los descarta al mirar.
- **FR que atiende**: FR-401, FR-402, FR-411, FR-412. **Revisión**: Marco (propietario del motor).
- **Qué reloj muestra el resumen**: lo fija FR-405 de la spec: el instante pedido; para `historia #k`,
  el instante de la decisión k; si la partida terminó antes de ese instante, el reloj del final de la
  partida. El reloj interno del motor aparte puede quedar en el último evento ≤ t; `ArmadorResumen`
  muestra el valor de FR-405 y no el interno.
- **Complejidad**: O(e log n), con e los eventos con tiempo ≤ t desde la última decisión.
- **Prueba prevista**: los escenarios H1-2, H1-9 y H1-12 de la spec, y la coincidencia entre
  `historia <t>` e `historia #k`.

## R7. Contenido de la línea en el archivo de partida (decisión 7)

- **Problema**: guardar y cargar conserva la línea completa (FR-420) y un archivo de la primera parte
  se detecta (FR-421).
- **Alternativas**: (1) guardar solo las acciones y re-simular todo al cargar (lento y depende del
  catálogo). (2) guardar acciones, marcadores, puntos de control, registros de carga, fichas y K
  (elegida). (3) archivo aparte. **Descartada**: dos archivos pueden desincronizarse.
- **Decisión**: (2). Campos nuevos **al final** de `PartidaGuardadaDTO` (`linea`, con valor por
  defecto) y un **bloque propio** en el binario con `VERSION_FORMATO = 2`. El detalle está en
  [contracts/contrato-linea-tiempo.md](contracts/contrato-linea-tiempo.md).
- **Archivo de la primera parte (versión 1)**: se **reporta como incompatible** con contexto
  (versión leída y versión esperada), sin migrar. Ya es lo que hace `GuardadoBinario` al comparar la
  versión antes de interpretar el resto; solo cambia la constante. Migrar exigiría inventar una línea
  que no existe (la primera parte no guardaba acciones con tiempo), y FR-421 lo permite.
- **Tamaño previsto**: acciones (pocos bytes cada una) + A/K copias completas + registros de carga +
  fichas. Se mide en M3 (bytes del archivo).
- **Límite**: guardar con K = 1 en una partida larga produce un archivo grande; es el costo medido.
- **K al cargar**: se conserva el K con el que se guardó la línea, aunque se indique otro
  `--checkpoint-cada` (Suposiciones de la spec). Así no se rompe FR-416 con puntos de control ya
  guardados.

## R8. Valor por defecto de K (decisión 8)

- **Provisional**: **K = 20**, **a confirmar con `--bench`**. Razón de partida: en una partida de
  5 000 acciones da 250 puntos de control (la búsqueda binaria hace ~8 pasos) y una consulta re-simula
  como máximo 20 acciones.
- **Criterio de decisión** (no se fija aquí): el K más grande (menos memoria) tal que la consulta
  `historia` tarde < 50 ms con 5 000 acciones (§6.1), con margen.
- **Medición**: M1 y M2 con K ∈ {1, 5, 20, 100} y la alternativa sin puntos de control. El resultado
  y la decisión final van a `DECISIONES.md` indicando si coincide con este valor provisional.
- **Validación de la bandera**: entero ≥ 1 (FR-415), con el mismo estilo de `--cache-size`.

## R9. Qué registra la feature en el historial de retroceso (decisión 9)

**Nada nuevo.** Consultar no cambia ningún estado (FR-407) y la línea vive fuera de `Motor`. El motor
aparte tiene su **propio** historial vacío (lo crea `Motor`) que se descarta con él. Marco registra
«descartar caché» en el historial solo como aviso (feature 001); esta feature no lo usa.

## R10. Qué se copia en cada punto de control

Un punto de control es el par `(PartidaGuardadaDTO, [SalaGuardadaDTO])` que devuelve
`PartidaGuardada.guardar` justo cuando el jugador tiene el control (después de
`avanzar_hasta_jugador`), más el número de acciones completadas. Se hace **a mano** (listas nuevas y
DTOs nuevos): sin `copy` ni `deepcopy` (Principio II).

| Se copia | Cómo |
|---|---|
| Reloj, secuencia siguiente de la cola, derrotados, terminado, victoria, salida abierta | valores simples |
| Estado de `random.Random` (versión, 625 enteros, gauss) | `list(estado)`: **exigencia de la Parte II para re-simular** |
| Jugador (vida, estadísticas, sala, acciones) | un DTO |
| Inventario (ids en orden real, cursor, posiciones de arma y armadura) | lista de ids |
| Rastro de salas | `list(...)` de S posiciones |
| Contadores por tipo | lista de pares |
| Efectos activos | un DTO por efecto |
| Eventos **válidos**, en el orden en que saldrían | un DTO por evento (los cancelados no se copian) |
| Cada sala: contenido cargado, puertas cerradas, objetos, trampas, enemigos | un `SalaGuardadaDTO` por sala |

**No se copia**: historial de retroceso (el motor aparte empieza con uno vacío), mensajes (FR-406),
caché de rutas de los cazadores (se reconstruye sola con el mismo resultado: FR-113), caché del
catálogo. **Mapa conocido** (spec 002, FR-223): será un campo de `PartidaGuardadaDTO` que actualiza el
motor, así que entra en la copia con `PartidaGuardada.guardar` y la re-simulación lo reproduce sin
invertirlo (NFR-203 de la 002 habla de invertirlo; la 004 reconstruye hacia adelante). Mientras ese campo
no exista, se omite (Suposiciones).

El costo de cada copia es O(S + E + V + I) (todas las salas, enemigos, eventos válidos e
inventario): es el riesgo R-1 del plan.
