# Plan de implementación: Verificación de resolubilidad

**Rama**: `derek` (spec-kit la reporta como `003-resolubilidad`) | **Fecha**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación de `specs/003-resolubilidad/spec.md` (FR-301 a FR-323, NFR-301 a NFR-304, SC-301 a SC-308)

**Constitución**: v1.2.0 · **Responsable**: integrante 2

## Resumen

Antes de iniciar una partida nueva, el programa decide si la cripta puede ganarse usando solo el esqueleto y la
ubicación de las llaves. Si es resoluble, entrega un orden determinista de obtención de llaves; si no, un reporte con
las llaves no obtenibles y sus ubicaciones, la frontera bloqueada y los ciclos con sus llaves dependientes. Sin
`--forzar`, una cripta no resoluble no inicia. `--verificar <cripta>` hace solo la verificación, sin vista, también con
`--offline`, y termina con 0, 3 o 1.

Enfoque técnico ([research.md](research.md)):

- **Datos de las llaves** (R1): `UbicacionLlaveDTO`, `FuenteDatos.obtener_llaves` (una solicitud, cuenta en el
  presupuesto), `llaves.json` en el paquete, persistencia por versión en `cache/llaves/` y validación de FR-321 en Data.
  El almacén de llaves se elige en el mismo `if` donde `ServicioPartida.fuente()` elige `FuenteOffline` o `FuenteRed`
  (offline → sin almacén; red → `AlmacenLlaves`); `ServicioResolubilidad` lo recibe ya decidido.
- **Índice propio de llaves** (R3): ordenar las menciones con el `Ordenador` y compactar; sin `dict` ni búsquedas.
- **Recorrido incremental por oleadas** (R4): la frontera se guarda **agrupada por llave** (`esperando[k]`, un array
  de listas indexado por el índice de la llave); al obtener una llave se reabren solo sus puertas. Cola de
  `Estructuras/`. Las caras se combinan con la misma `Mazmorra` de la primera parte.
- **Salida** (R4): es resoluble solo si `llave_salida` es obtenible y se llega a `sala_salida` por una cara cerrada
  que pide `llave_salida` desde la sala desde la que se entra (FR-304); si no existe ninguna cara así, el motivo de
  FR-322. El cierre automático no se lee: no es por cara y no bloquea (FR-302).
- **Orden** (R5): por oleada y, dentro de cada oleada, por id; todo ordenado con el `Ordenador`.
- **Ciclos** (R6): una fase hacia afuera del mismo recorrido asigna a cada sala la puerta que la bloquea, con la regla
  de FR-310 (menor nivel; desempate por sala de origen y dirección); cada llave no obtenible apunta a una sola llave y
  los ciclos de ese grafo y sus dependientes se hallan en O(K), sin repetir y **sin recursión**.
- **Bench** (R7): `Logic/BenchResolubilidad.py`, que `Service/ServicioBench.py` agrega a su lista por defecto después
  de `BenchLogica.medir`; reutiliza el cronómetro de `BenchLogica` sin modificarlo. Cuadrículas sintéticas por semilla con llaves encadenadas (100, 1 000 y 10 000 salas) contra la alternativa de
  repetir el recorrido por llave, y las alternativas descartadas de R3 (búsqueda lineal de ids) y R4 (frontera en una
  sola lista). Además, `Service/ServicioBench.py` mide la cripta con más salas del paquete local, leída sin red, para
  el límite de 200 ms de §6.1 sobre «la cripta publicada más grande» (NFR-301, SC-306).
- **Sin historial ni línea de tiempo** (R9): la verificación ocurre antes de que exista el motor.

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior.

**Dependencias principales**: ninguna nueva. Se usan `dataclasses`, `typing`, `json`, `os`, `random.Random` (solo en el
bench), `time` (vía `Service/Cronometro.py`), `argparse` y `unittest`. Nada de `dict` ni `set` como índice,
`collections`, `heapq`, `bisect`, bibliotecas de grafos, `sorted()`/`list.sort()` ni `copy`.

**Almacenamiento**: `cache/llaves/<id_cripta>.json` (respuesta del API más su versión); `paquete/<id>/llaves.json`.
En memoria, arreglos planos indexados por sala, por cara (`sala*4 + dirección`) y por índice de llave.

**Pruebas**: `unittest` en `tests/`, con `tests/correr_pruebas.py`. Cada prueba cita su FR (R10).

**Plataforma**: escritorio con `pygame-ce`; `--verificar` no importa pygame.

**Tipo de proyecto**: juego de escritorio por eventos, MVC en n capas (Principio I).

**Metas de rendimiento**: < 200 ms con la cripta con más salas del paquete local, leída sin red, o, mientras el
paquete no traiga criptas con `llaves.json`, con la cuadrícula sintética de 1 000 salas y 100 llaves (NFR-301, SC-306);
crecimiento ≤ ×20 por cada ×10 de tamaño (SC-307).

**Restricciones**: determinismo (Principio IV): el resultado no depende del orden del JSON; Abierto/Cerrado
(Principio III): lo nuevo en módulos nuevos, los cambios a lo existente en la tabla de abajo.

**Escala**: criptas publicadas de hasta 50 salas (paquete actual); sintéticas de hasta 10 000 salas y 1 000 llaves.
La prueba de que los dependientes se hallan sin recursión usa una cripta de 6 000 salas (2 × 3 000) con unas
1 500 dependientes, por encima de la escala de las mediciones (research R6 y R7).

## Verificación de la constitución

*Compuerta: antes de la fase 0, y otra vez después de la fase 1.*

| Principio | Cómo lo cumple este plan | Antes | Después |
|---|---|---|---|
| I. MVC en n capas | Data entrega y valida (llaves, almacén, FR-321). Logic decide (recorrido, orden, ciclos, reporte) y **no importa Data**: recibe `CriptaDTO`, `SalaDTO` y `UbicacionLlaveDTO`. Service orquesta y no valida: solo convierte los errores del paso de llaves en un reporte «no concluyó». La interfaz habla con Service por `ControladorBackend`. `--offline` cambia la fuente sin `if` dispersos: la única condición es el `if` de `ServicioPartida.fuente()`, que elige a la vez la fuente y el almacén de llaves; `ServicioResolubilidad` no mira `config.offline` | ✅ | ✅ |
| II. Bibliotecas y estructuras | `Cola` y `Ordenador` del equipo; arreglos indexados por entero; índice de llaves por ordenamiento y compactación (R3). Revisión de estructuras existentes: R0 | ✅ | ✅ |
| III. KISS, YAGNI, Abierto/Cerrado | Módulos nuevos con type hints y docstring. Cambios a la primera entrega en la tabla siguiente, cada uno con su FR. `obtener_llaves` no es abstracto para no romper fuentes falsas | ✅ | ✅ |
| IV. Determinismo | Reglas de orden y desempate definidas por los datos (R5, R6); una prueba permuta la entrada y compara (FR-306); 10 ejecuciones en procesos separados (SC-303). No consume el generador aleatorio (FR-301) | ✅ | ✅ |
| V. Modos sin vista | `--verificar` va por `main.py` → `ControladorBackend` → Service, no importa pygame y escribe el resultado en la salida estándar; es el único modo sin vista que muestra el resultado de la verificación (`--replay` no verifica y `--bench` solo mide cuánto tarda la verificación, sin mostrar veredictos ni iniciar partidas; FR-301, FR-313) | ✅ | ✅ |
| VI. Sin datos de una cripta concreta | Nada de ids, salas ni versiones en el código; el bench genera criptas por semilla | ✅ | ✅ |
| VII. Red y presupuesto | Una solicitud de llaves, que cuenta en el presupuesto (`ClienteHttp`); persistida por versión, no se repite; 429 y red → mensaje con contexto, sin caerse (FR-320) | ✅ | ✅ |
| VIII. Rendimiento con evidencia | B1 a B6 en `--bench`, con las alternativas descartadas de R3, R4 y §5.4 que se pueden medir con sentido (R7); resultados a `DECISIONES.md` | ✅ | ✅ |
| IX. Spec antes del código | La spec está confirmada (commits `a4782fe`, `f9ecaec` y `45e959e`, la segunda revisión del integrante 1). El plan se realineó con `45e959e` (FR-301, FR-302, FR-304, FR-313, FR-314, FR-322 y la Sesión 2026-11-13) y después con la revisión del plan del integrante 1 («Sesión 2026-11-13 (revisión del plan por el integrante 1)»: FR-309, FR-310, FR-312, FR-314, H1-12, H2-13 y Suposiciones), que se confirma en la spec en un commit anterior al de este plan. Este plan no agrega reglas: los hallazgos H-1 a H-4 no cambian la spec | ✅ | ✅ |
| X. Trazabilidad | Una prueba por escenario y por caso del Apéndice B, citando su FR (R10) | ✅ | ✅ |
| XI. Bitácora de LLM | El prompt de este `/speckit-plan` se registra en `PROMPTS_LLM.md` (en el commit del plan) | ✅ | ✅ |

**Resultado**: pasa. Sin violaciones que justificar (la tabla de complejidad queda vacía).

### Hallazgos

Ninguno bloquea; detalle en [research.md, Hallazgos](research.md#hallazgos).

- **H-1** (decidido en la Sesión 2026-11-13 de la spec): el motor de P1 gana con `salida_abierta`, que se activa al
  abrir cualquier puerta que pida `llave_salida`; la verificación exige una cara cerrada hacia `sala_salida` que pida
  `llave_salida` (FR-304, FR-322). Donde difieren, la verificación dice «no resoluble» y el motor dejaría ganar: **en
  esta regla** va hacia el lado seguro (si la verificación dice «resoluble», el motor también deja ganar; para el caso
  contrario está `--forzar`). **El integrante 1 mantiene el motor como está y registra la diferencia en
  `DECISIONES.md`.** Este plan no toca el motor y prueba el caso (research, R10). **Límite conocido en la otra
  dirección** (spec, Suposiciones y Sesión 2026-11-13 de la revisión del plan): en una puerta con cierre automático y
  llaves distintas por cara, la verificación supone que la puerta sigue abierta (§3.5), pero el motor la cierra en sus
  dos caras y volver pide la llave de la otra cara; ahí la verificación puede decir «resoluble» y el jugador quedar
  encerrado. Es una decisión del grupo; la prueba del caso borde comprueba que la verificación no lo trata como
  bloqueo.
- **H-2** (informativo): la solicitud de llaves gasta 1 del presupuesto en vivo y no en el replay (FR-317).
- **H-3** (datos): el paquete actual es de la primera parte, sin `llaves.json`, `costo` ni `rango`; hay que
  regenerarlo. Hasta entonces `--verificar --offline` da código 1, que es lo correcto.
- **H-4** (contrato HTTP): confirmar `GET /criptas/{id}/llaves` con Swagger al implementar.

## Revisión de estructuras existentes (Principio II)

Detalle en [research.md, R0](research.md#r0-revisión-de-las-estructuras-ya-implementadas-principio-ii).

| Estructura | Limitación frente a la Parte II | Decisión |
|---|---|---|
| `Cola` | Ninguna para un recorrido por anchura | Se usa (recorrido y fase hacia afuera) |
| `Ordenador` | Solo ordena; no deduplica | Se usa (índice de llaves, oleadas, frontera, ubicaciones, niveles) |
| `MonticuloMinimo` | El costo no afecta (FR-302): no hay prioridad | No se usa |
| `ListaDoble` | No hace falta borrar en el medio | No se usa |
| `BufferCircular` | Pisa lo antiguo | No se usa |
| `GestorEsqueleto` (Data) | Ninguna: `existe_sala` O(1) | Se usa para FR-321 |
| `Mazmorra` (Logic) | Es estado vivo: se usa una instancia aparte | Se usa solo para combinar caras |
| `GrafoEsqueleto` (001) | Estado vivo y solo salidas abiertas | No se usa |
| `BusquedaBinaria` (004, pendiente) | Claves enteras; no hace falta (R3) | No se usa |

No se agrega nada a `Estructuras/`.

## Estructura del proyecto

### Documentación de esta feature

```text
specs/003-resolubilidad/
├── plan.md                                  # este archivo
├── research.md                              # fase 0: R0 a R10 y hallazgos
├── data-model.md                            # fase 1: DTO, arreglos y estados
├── quickstart.md                            # fase 1: cómo validar de punta a punta
├── contracts/
│   ├── contrato-llaves.md                   # fase 1: API, DTO, paquete, persistencia, FR-321
│   └── contrato-reporte-resolubilidad.md    # fase 1: DTO del reporte (integrante 3), texto y CLI
└── tasks.md                                 # fase 2 (/speckit-tasks, NO lo crea este plan)
```

### Código fuente

```text
DTO/
├── UbicacionLlaveDTO.py          # NUEVO: id, sala, enemigo                              (FR-316)
├── ReporteResolubilidadDTO.py    # NUEVO: reporte y sus partes                           (FR-305..FR-310, FR-322)
└── ConfiguracionDTO.py           # MODIFICADO: verificar, forzar (después de los de la 004)   (FR-312, FR-314)

Data/
├── FuenteDatos.py                # MODIFICADO: obtener_llaves (no abstracto)             (FR-317)
├── FuenteJson.py                 # MODIFICADO: obtener_llaves + ubicaciones_desde_diccionario (formato)
├── FuenteOffline.py              # MODIFICADO: ruta criptas/{id}/llaves -> llaves.json   (FR-318, FR-320)
├── DescargadorPaquete.py         # MODIFICADO: descarga y escribe llaves.json            (FR-318)
├── ValidacionDatos.py            # MODIFICADO: validar_ubicaciones (ErrorDatos)          (FR-321)
├── AlmacenLlaves.py              # NUEVO: cache/llaves/<id>.json por versión             (FR-317, FR-319)
└── GestorLlaves.py               # NUEVO: almacén -> fuente -> validación                (FR-317, FR-320, FR-321)

Logic/
├── GrafoLlaves.py                # NUEVO: preparación (caras combinadas, índice de llaves, ubicaciones sin repetir)
├── RecorridoLlaves.py            # NUEVO: oleadas incrementales, frontera, fase hacia afuera   (FR-302..FR-305, FR-308)
├── CiclosLlaves.py               # NUEVO: ciclos y dependientes, iterativo               (FR-310)
├── VerificadorResolubilidad.py   # NUEVO: veredicto y armado del DTO                     (FR-301..FR-310, FR-322)
└── BenchResolubilidad.py         # NUEVO: B1 a B6, criptas sintéticas por semilla, alternativas descartadas   (NFR-301..NFR-304)

Service/
├── ServicioBench.py              # MODIFICADO (integrante 2): agrega BenchResolubilidad.medir a la lista por defecto, después de BenchLogica.medir
├── ServicioResolubilidad.py      # NUEVO: verificar(id), iniciar_partida_nueva(...) y ErrorPartidaNoIniciada   (FR-301, FR-311..FR-315, FR-320)
├── ServicioPartida.py            # MODIFICADO (integrante 3): iniciar_partida(..., datos=None); fuente() elige también el almacén de llaves
├── ContextoPartida.py            # MODIFICADO (integrante 3): campo final resolubilidad = None
└── ErroresServicio.py            # MODIFICADO (integrante 3): importa ErrorPartidaNoIniciada y lo agrega a ERRORES_ESPERADOS

UIController/
├── LectorArgumentos.py           # MODIFICADO: --verificar (grupo excluyente) y --forzar  (FR-314)
├── TextoResolubilidad.py         # NUEVO: líneas de texto del reporte (consola y, si quiere, la vista)
└── ControladorBackend.py         # MODIFICADO (integrante 3): iniciar con verificación, verificar(), resolubilidad()

View/                              # MODIFICADO (integrante 3): mostrar el reporte al iniciar   (FR-313)
main.py                            # MODIFICADO: rama --verificar con códigos 0/3/1   (FR-314)

tests/
├── ayudas_resolubilidad.py           # criptas a mano con la notación de la spec
├── test_resolubilidad_logica.py      # H1, SC-304, FR-306
├── test_resolubilidad_reporte.py     # H2, SC-305 (Apéndice B caso 1)
├── test_resolubilidad_datos.py       # contrato de llaves, H2-7, H2-8, H3-4..H3-7
├── test_resolubilidad_servicio.py    # H4, H1-8, H1-9, R9 (Apéndice B caso 4)
├── test_resolubilidad_cli.py         # H3-1..H3-3, H3-8, H3-9, cripta inexistente, --forzar sin efecto, SC-303, SC-308
└── test_resolubilidad_bench.py       # generadores por semilla, incremental = ingenua, alternativas = decisión (NFR-304)
```

**Decisión de estructura**: se mantiene MVC en n capas. El recorrido y el reporte son de Logic porque son reglas del
juego (FR-302 a FR-310); obtener y validar las llaves es de Data; decidir si se inicia la partida es un caso de uso de
Service. La combinación de caras se toma de `Mazmorra` para que la verificación y el juego no diverjan.

## Cambios a código de la primera entrega y de otros integrantes (Principio III)

Todo lo demás es código nuevo. Si un cambio modifica una decisión de la primera parte, se documenta el antes y el
después en `DECISIONES.md`.

| Archivo | Cambio | Por qué es indispensable | FR | Dueño |
|---|---|---|---|---|
| `Data/FuenteDatos.py` | Método `obtener_llaves` con implementación por defecto | La interfaz común debe ofrecer la consulta nueva para red y offline | FR-317, FR-318 | Integrante 2 |
| `Data/FuenteJson.py` | `obtener_llaves` y `ubicaciones_desde_diccionario` | Traducción y formato compartidos por red y offline | FR-316, FR-317 | Integrante 2 |
| `Data/FuenteOffline.py` | Ruta `criptas/{id}/llaves` | Leer las llaves del paquete | FR-318, FR-320 | Integrante 2 |
| `Data/DescargadorPaquete.py` | Descargar y escribir `llaves.json` | El paquete debe traer las llaves | FR-318 | Integrante 2 |
| `Data/ValidacionDatos.py` | `validar_ubicaciones` | FR-321 con `ErrorDatos` | FR-321 | Integrante 2 |
| `Service/ServicioBench.py` | Importar `BenchResolubilidad` desde `Logic` (como ya importa `BenchLogica`) y agregar `BenchResolubilidad.medir` a la lista por defecto, después de `BenchLogica.medir`. Sin import circular: `BenchResolubilidad` importa de `Logic/BenchLogica.py` solo `_cronometrar`, `_mejor_y_mediana` y `SEMILLA`, y ni `BenchLogica` ni `BenchRutas` importan `BenchResolubilidad` ni `ServicioBench`. Además, si el paquete local trae criptas con `llaves.json`, una fila que mide la verificación de la cripta con más salas del paquete (elegida por cantidad de salas, sin nombrar ids), leída sin red: Service orquesta `FuenteOffline`, `GestorEsqueleto`, `GestorLlaves` sin almacén y `VerificadorResolubilidad`; `Logic/BenchResolubilidad` no lee Data. Si no hay `llaves.json`, la fila no se agrega y la nota lo dice | Exponer las mediciones nuevas en `--bench` y medir «la cripta publicada más grande» de §6.1. `Logic/BenchLogica.py` no se modifica (feature 001 cerrada) | NFR-301, NFR-304, SC-306 | Integrante 2 |
| `DTO/ConfiguracionDTO.py`, `UIController/LectorArgumentos.py` | `verificar` y `forzar`, **después** de `hasta` (ya están `checkpoint_cada` y `hasta`, commit `1b53bc9`) | Banderas pedidas por la spec | FR-312, FR-314 | Integrante 2 |
| `main.py` | Rama `--verificar`: escribe las líneas de `TextoResolubilidad` en la salida estándar y devuelve 0, 3 o 1 | Pedido por la spec | FR-314 | Integrante 2, sobre la versión con la rama `--hasta` del integrante 3 |
| `Service/ServicioPartida.py` | (a) Parámetro final `datos=None` en `iniciar_partida`: si viene, no llama a `abrir_datos`. (b) El `if` de `fuente()` elige también el almacén de llaves: offline → `FuenteOffline()` y sin almacén; red → `FuenteRed()` y `AlmacenLlaves()`. Método nuevo `almacen_llaves() -> AlmacenLlaves \| None` (llama antes a `fuente()`) y parámetro final `almacen_llaves=None` en el constructor para las pruebas que inyectan la fuente | (a) No pedir dos veces los datos generales y el esqueleto (presupuesto). (b) Una sola condición para `--offline` (Principio I): `ServicioResolubilidad` no vuelve a mirar `config.offline` | FR-311, FR-317, FR-318 | Integrante 3; lo escribe el integrante 2 y ella lo revisa antes del merge (acuerdo del 14/11) |
| `Service/ContextoPartida.py` | Campo final `resolubilidad = None` (después de `linea` de la 004) | Dónde queda el reporte para mostrarlo | FR-313 | Integrante 3; lo escribe el integrante 2 y ella lo revisa antes del merge (acuerdo del 14/11) |
| `Service/ErroresServicio.py` | Importar `ErrorPartidaNoIniciada` de `Service/ServicioResolubilidad.py` y agregarlo a `ERRORES_ESPERADOS`, como ya se hace con `ErrorCarga` (`ServicioGuardado`) y `ErrorReplay` (`ServicioReplay`). Sin import circular: `ServicioResolubilidad` no importa `ErroresServicio` (solo lo importa `ControladorBackend`) | Que el controlador lo muestre sin caerse | FR-311, FR-320 | Integrante 3; lo escribe el integrante 2 y ella lo revisa antes del merge (acuerdo del 14/11) |
| `UIController/ControladorBackend.py` | `iniciar` llama a `ServicioResolubilidad.iniciar_partida_nueva(..., config.forzar)` y guarda el reporte (también el de `ErrorPartidaNoIniciada`); métodos nuevos `verificar(id)` y `resolubilidad()`, al final de la clase | La interfaz solo habla con Service por el controlador | FR-311 a FR-315 | Integrante 3; lo escribe el integrante 2 y ella lo revisa antes del merge (acuerdo del 14/11) |
| `View/…`, `UIController/ControladorPygame.py` | Mostrar el reporte antes de la primera acción, como advertencia con `--forzar`, y completo si no inicia | §7.3 | FR-311 a FR-313 | Integrante 3 |
| `README.md` | Comandos `--verificar` y `--forzar` (§7.2) | Pedido por el enunciado | FR-314 | Quien actualice el README (acordar) |
| `paquete/` | Regenerar con `DescargadorPaquete` cuando el API publique la Parte II | Hoy no trae `llaves.json`, `costo` ni `rango` (H-3) | FR-318 | Integrante 2, avisando antes |

**No se tocan**: `Logic/Mazmorra.py` (solo se usa), `Logic/HistorialRetroceso.py`, `Logic/motorJuego.py`,
`Service/ServicioReplay.py`, `Service/ServicioGuardado.py`, `Service/ServicioAccionJugador.py`, `Data/GestorEsqueleto.py`,
`Data/ClienteHttp.py`, `Data/AlmacenCatalogo.py`, ningún archivo de `Estructuras/`.

## Coordinación

**Con el integrante 3**:

1. **Hecho**: [contrato-reporte-resolubilidad.md](contracts/contrato-reporte-resolubilidad.md) quedó confirmado por el
   integrante 3 el 14/11, sin cambios (T002).
2. **Orden de `ConfiguracionDTO` y `LectorArgumentos`**: **ya está hecho** lo suyo (commit `1b53bc9`):
   `checkpoint_cada` (por defecto 20) y después `hasta` en `ConfiguracionDTO`; `--checkpoint-cada` y `--hasta` en
   `LectorArgumentos`. `verificar` y `forzar` van **detrás de `hasta`**. `--verificar` va en el grupo excluyente de
   `--replay` y `--bench`.
3. **`main.py`**: la rama `--verificar` se agrega sobre su versión con `--hasta`.
4. Los cambios de su código de la tabla de arriba (`ServicioPartida`, `ContextoPartida`, `ErroresServicio`,
   `ControladorBackend`, vista). El parámetro `datos` y el campo `resolubilidad` van al final, con valor por defecto.
   **Acuerdo del 14/11**: los cambios a `ServicioPartida`, `ContextoPartida`, `ErroresServicio` y `ControladorBackend`
   **los escribe el integrante 2**, con sus pruebas, sobre la versión de su rama (`origin/kris`, que se mergea antes
   de empezar), y **ella los revisa antes del merge**. Condiciones: `ContextoPartida.resolubilidad` va después de
   `linea`; los métodos nuevos de `ControladorBackend` van al final de la clase; quien suba segundo hace el merge.
   **La vista sigue siendo suya.**
5. **Línea de tiempo**: la verificación no registra nada en la línea ni en el historial (R9). Su `iniciar_partida`
   con la línea y los grabadores no cambia; solo recibe `datos`.

**Con el integrante 1**:

1. `GrafoLlaves` usa `Mazmorra.cargar_esqueleto` y `Mazmorra.salida` para combinar las caras como en la primera
   parte. Si cambia la regla de `_igualar_caras`, la verificación cambia con ella: avisar antes (las pruebas H1-10 y
   H2-9 lo detectan).
2. **Diferencia con el motor (H-1)**: el integrante 1 decidió mantener `Logic/motorJuego.py` como está y registra en
   `DECISIONES.md` la diferencia conocida entre la verificación y el motor (Sesión 2026-11-13 de la spec). Este plan
   no toca el motor; la prueba del caso queda en `tests/test_resolubilidad_logica.py`.
3. Revisión cruzada del plan, como en las specs.
4. **Dependencia de la 001 en el bench**: `Logic/BenchResolubilidad.py` reutiliza `_cronometrar`, `_mejor_y_mediana`
   y `SEMILLA`, que son privadas de `Logic/BenchLogica.py` (integrante 1, feature 001). El integrante 1 confirmó el
   14/11 que no les cambia el nombre ni la firma sin avisar: si cambian, el integrante 1 avisa antes.

**Con los tres**: regenerar `paquete/` (H-3) cambia archivos que usan pruebas de todos; se avisa y se hace en un
commit propio.

## Mediciones previstas (`--bench`, §6.3)

Criptas sintéticas deterministas por semilla (Principio VIII); detalle en
[research.md, R7](research.md#r7---bench-nfr-304-sc-306-sc-307).

| # | Qué mide | Tamaños | Para qué |
|---|---|---|---|
| B1 | Verificación completa, cripta resoluble | 100 / 1 000 / 10 000 salas (10, 100, 1 000 llaves) | SC-306 (< 200 ms en 1 000), SC-307 (≤ ×20) |
| B2 | Alternativa: repetir el recorrido completo por cada llave | los mismos (10 000: una sola repetición, con nota) | SC-307 (crece al menos el doble que B1) |
| B3 | Verificación completa, no resoluble (un ciclo de una llave + cadena de unas K/2 dependientes) | los mismos | NFR-303 |
| B4 | Desglose: preparación, recorrido, ciclos y armado | 1 000 salas | Dónde se va el tiempo |
| B5 | Índice de llaves (R3): ordenar y compactar frente a la búsqueda lineal de ids (descartada) | las cuadrículas de B1 (10 000: la lineal con una sola repetición, con nota) | Respaldar R3: O(M log M) frente a O(M·K) |
| B6 | Recorrido (R4): frontera agrupada por llave frente a una sola lista revisada entera al obtener cada llave (descartada) | «peine» de 100 / 1 000 / 3 000 dientes (3 000: la lista única con una sola repetición, con nota) | Respaldar R4: O(S + E + U) frente a O(K·F) |

B1 a B6 usan criptas sintéticas. Además, `Service/ServicioBench.py` agrega la fila de la **cripta con más salas del
paquete local**, leída sin red, cuando el paquete trae criptas con `llaves.json` (NFR-301, SC-306: «la cripta
publicada más grande» de §6.1); si no, la fila no se agrega, la nota lo dice y vale B1 a 1 000 salas.

Las alternativas descartadas que no se miden (con su motivo) están en research, R7. Además, `DECISIONES.md` gana la
sección «Resolubilidad» con problema, alternativas, decisión, complejidad y los números de B1 a B6.

## Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R-1 | **Registrar algo en el historial o en la línea de tiempo** (riesgo principal del plan de trabajo) | La verificación ocurre antes de crear el motor, la línea y el log (R9); prueba de que quedan vacíos e igual estado inicial que sin verificar (H1-8) |
| R-2 | **Romper el replay o la carga** si se verifica en `iniciar_partida` | Se verifica solo en `ServicioResolubilidad.iniciar_partida_nueva`; pruebas H4-4 (FR-301) |
| R-3 | **Pedir dos veces los datos** (presupuesto) | `iniciar_partida(..., datos=…)`; prueba que cuenta las solicitudes |
| R-4 | **La combinación de caras diverge del juego** | Se reutiliza `Mazmorra`; pruebas H1-10, H2-9, H2-10 |
| R-5 | **Paquete viejo** (H-3) | Pruebas con paquetes temporales; código 1 con mensaje mientras tanto |
| R-6 | **Ordenar las menciones domina el tiempo** | B4 lo muestra; si pasa, se ordenan solo las caras con llave (son pocas) |
| R-7 | **Entrega atrasada del contrato de llaves** | Este plan lo fija; es la primera tarea de `tasks.md` |
| R-8 | **Decidir por `alcanzable[sala_salida]`** en lugar de por la cara que pide `llave_salida` | El veredicto usa `caras_de_salida` (research R4); pruebas de los casos borde de la salida y de la diferencia con el motor (FR-304, FR-322) |
| R-9 | **Recursión en una cadena larga de dependientes** (límite de Python: 1 000 llamadas por defecto) | `CiclosLlaves` es iterativo (research R6); prueba con una cadena de más de 1 000 llaves (research R7) |

## Mapa de requisitos a componentes

| Requisito | Componente principal |
|---|---|
| FR-301 | `ServicioResolubilidad.iniciar_partida_nueva` (solo partida nueva; ni carga, ni `--replay`, ni `--bench`); `GrafoLlaves` sin contenido ni azar |
| FR-302 | `GrafoLlaves` (llave y estado cerrado por cara vía `Mazmorra`; cierre automático y costo no se leen), `RecorridoLlaves` (llaves no se consumen) |
| FR-303, FR-316 | `UbicacionLlaveDTO`; `GrafoLlaves.llaves_en_sala` (todas las copias) |
| FR-304, FR-322 | `GrafoLlaves` (`es_cara_de_salida`, `hay_puerta_de_salida`), `RecorridoLlaves` (`caras_de_salida`), `VerificadorResolubilidad` (veredicto y texto del motivo) |
| FR-305, FR-306 | `RecorridoLlaves` (oleadas) + `Ordenador` (R5) |
| FR-307, FR-309 | `VerificadorResolubilidad` (no obtenibles con ubicaciones o «sin ubicación»); `GrafoLlaves` (ubicaciones idénticas una sola vez) |
| FR-308 | `RecorridoLlaves` (`esperando` y `sin_llave` → frontera) |
| FR-310 | `RecorridoLlaves` (fase hacia afuera: puerta que bloquea según la regla de FR-310) + `CiclosLlaves` (iterativo) |
| FR-311, FR-312, FR-313 | `ServicioResolubilidad`, `ControladorBackend`, vista (antes de la primera acción del jugador); `--forzar` sin efecto con `--replay`, `--bench` y la carga (no pasan por `ServicioResolubilidad`) |
| FR-314, FR-315 | `LectorArgumentos`, `main.py` (salida estándar), `ServicioResolubilidad.verificar` (cripta inexistente → `no_concluyo`, código 1), `TextoResolubilidad` |
| FR-317 | `GestorLlaves`, `AlmacenLlaves`; `ServicioPartida.fuente()` elige el almacén (red) o ninguno (offline) |
| FR-319 | `AlmacenLlaves` (`validar_version`) y `GestorLlaves` para las llaves; `AlmacenCatalogo` para los datos que ya persistía la primera parte (sin cambios: su carpeta por versión del catálogo ya los invalida) |
| FR-318 | `LectorPaquete`, `DescargadorPaquete` |
| FR-320 | `GestorLlaves` → `ErrorRed` → reporte `no_concluyo` en `ServicioResolubilidad` |
| FR-321 | `validar_ubicaciones` (Data); «sin ubicación» en Logic |
| FR-323 | `GestorEsqueleto.cargar` (ya existe); `ServicioResolubilidad` lo propaga al iniciar |
| NFR-301 a NFR-304 | `Logic/BenchResolubilidad` (B1 a B6), enganchado en la lista por defecto de `Service/ServicioBench.py`, y `DECISIONES.md` |
