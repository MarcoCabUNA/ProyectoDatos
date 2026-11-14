---
description: "Lista de tareas de la feature 003: verificación de resolubilidad"
---

# Tareas: Verificación de resolubilidad

**Entrada**: documentos de diseño de `specs/003-resolubilidad/`

**Prerrequisitos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md). Versión de la spec del
commit `c2fb219` y del plan del commit `plan(003)` siguiente (`7e685f4`), con la revisión del integrante 1.

**Pruebas**: sí. La constitución (Principio X) pide una prueba por escenario y por caso del Apéndice B, y el plan
pide `unittest` en `tests/` (research R10). Cada prueba cita su escenario y su FR en el nombre del método
(`test_h2_13_fr306_fr307_fr308_fr310_puerta_que_bloquea`), con los FR que la tabla de cobertura de la spec asigna a
ese escenario, y, si es un caso del Apéndice B, también en el nombre
(`…_apendiceB_casoN_…`). Se escriben **antes** que el código y deben fallar primero.

**Organización**: en el orden de la ruta de desarrollo del plan: contrato de llaves (Data y DTO) → Logic
(historias 1 y 2) → `ServicioResolubilidad` (historias 1 y 4) → `--verificar` sin vista y `--forzar` (historia 3) →
interfaz al iniciar (historia 4) → paquete de la Parte II → bench → documentación. Cada historia de la spec es una
etiqueta (H1 → US1, H2 → US2, H3 → US3, H4 → US4).

**Responsable**: integrante 2. Las tareas marcadas **(coordinar con el integrante 3)** o **(coordinar con el
integrante 1)** tocan archivos de otro integrante según la tabla de cambios y la sección «Coordinación» del plan, y
cada una dice el cambio exacto. **Acuerdo del 14/11 con el integrante 3**: T037 (`ServicioPartida`), T038
(`ContextoPartida`), T040 (`ErroresServicio`), T049 y T054 (`ControladorBackend`) **los escribe el integrante 2**, con
sus pruebas, sobre la versión de la rama del integrante 3 (`origin/kris`), y **ella los revisa antes del merge**.
Condiciones: `ContextoPartida.resolubilidad` va después de `linea`, los métodos nuevos de `ControladorBackend` van al
final de la clase y quien suba segundo hace el merge. **T055 (vista) sigue siendo del integrante 3**: el integrante
2 no la implementa. Las marcadas **Aviso** son mensajes a otro integrante, sin código. `Logic/BenchLogica.py` **no se
modifica**: el bench se engancha en `Service/ServicioBench.py`, que es del integrante 2.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas sin terminar).
- **[US1]…[US4]**: historia de la spec a la que pertenece la tarea.
- Las fases de preparación, base, paquete, bench y cierre no llevan etiqueta de historia.

## Reglas para todas las tareas (constitución v1.2.0)

- Python 3.11 o superior. Sin dependencias nuevas.
- Prohibido en `Logic/`, `Estructuras/`, `DTO/` y `Service/`: `copy` (incluido `deepcopy`), `bisect`, `heapq`,
  `collections`, `dict` o `set` como índice o caché, bibliotecas de grafos, y `sorted()` / `list.sort()` (para
  ordenar, `Estructuras/Ordenador.py`). `copy` solo en `tests/`. Las colas son `Estructuras/Cola.py`.
- **Sin recursión** en `Logic/CiclosLlaves.py` ni en la fase hacia afuera de `Logic/RecorridoLlaves.py`: todo es
  `while` o `for` con arrays (research R6, riesgo R-9). Prohibido `sys.setrecursionlimit`.
- `Logic/` no importa `Data/` ni `Service/`: recibe `CriptaDTO`, `list[SalaDTO]` y `list[UbicacionLlaveDTO]`.
  `Service/` orquesta y no valida. `Estructuras/` no importa ninguna capa.
- **Una sola condición para `--offline`** (Principio I): el `if` de `ServicioPartida.fuente()`. Ni `GestorLlaves` ni
  `ServicioResolubilidad` leen `config.offline`.
- Sin ids, salas ni versiones de una cripta concreta en el código (Principio VI): las pruebas arman criptas a mano y
  el bench las genera por semilla.
- Código nuevo con type hints y docstring breve. Comentarios y nombres en español. No se agregan type hints ni
  docstrings al código de la primera entrega.
- **No se tocan**: `Logic/Mazmorra.py` (solo se usa), `Logic/HistorialRetroceso.py`, `Logic/motorJuego.py`,
  `Logic/BenchLogica.py`, `Service/ServicioReplay.py`, `Service/ServicioGuardado.py`,
  `Service/ServicioAccionJugador.py`, `Data/GestorEsqueleto.py`, `Data/ClienteHttp.py`, `Data/AlmacenCatalogo.py`
  ni ningún archivo de `Estructuras/`.
- Campos nuevos de DTO y de `ContextoPartida`: **al final y con valor por defecto**.
- `--checkpoint-cada` y `--hasta` del integrante 3 ya están (commit `1b53bc9`): `verificar` y `forzar` van
  **detrás de `hasta`**, sin tocar las banderas de la 004.
- Las pruebas usan `unittest` y corren con `python tests/correr_pruebas.py`. En Windows se corre con
  `PYTHONIOENCODING=utf-8`, como dice el README (`$env:PYTHONIOENCODING = "utf-8"; uv run python tests/correr_pruebas.py`
  en PowerShell); si no, el script se cae al imprimir un carácter que la consola no puede mostrar.
- Vocabulario: una **cara** es una salida vista desde una sala (`c = sala*4 + dirección`); una **puerta** es una
  salida cerrada; la **región alcanzable**, la **frontera bloqueada**, la **zona** y el **nivel** de una puerta son
  los de la spec (FR-308, FR-310); una **oleada** es el conjunto de llaves que se obtienen juntas (research R5).

---

## Fase 1: Preparación

**Propósito**: ayudantes de prueba y lo que hay que acordar con los otros integrantes desde el inicio.

- [ ] T001 [P] Crear `tests/ayudas_resolubilidad.py` con ayudantes de prueba (con docstring), en la notación de la spec (Convenciones): `cripta(cantidad_salas, salidas, ubicaciones, sala_inicial=1, sala_salida=9, llave_salida="S", version="v1", id_cripta="prueba")`, que devuelve `(CriptaDTO, list[SalaDTO], list[UbicacionLlaveDTO])`; `abierta(a, direccion, b)` (salida abierta, las dos caras), `puerta(a, direccion, b, llave)` («puerta a–b (llave)», las dos caras con la misma llave), `cara(a, direccion, b, cerrada=None, llave=None, cierre_automatico=None, costo=None)` (una sola cara, para H1-10, H2-9, H2-10, H2-11 y las salidas sin vuelta) y `ubic(id, sala, enemigo=None)`; `permutar(lista, semilla)` (copia barajada con `random.Random(semilla)`, para FR-306); `orden_es_valido(cripta, salas, ubicaciones, orden)` (comprueba FR-305 recorriendo el orden llave por llave, para SC-304); `FuenteConLlaves`, una `FuenteDatos` falsa sobre las de `tests/Utilidades.py` que entrega la cripta, el esqueleto y `obtener_llaves`, **cuenta las solicitudes por operación** (datos generales, esqueleto, contenido, catálogo, llaves) y puede lanzar en `obtener_llaves` un `PresupuestoAgotadoError`, un `ErrorRed` de 429 o de red, o un 404 en `obtener_datos_generales` (cripta inexistente); y `paquete_temporal(carpeta, cripta, salas, ubicaciones | None)`, que escribe un paquete offline con el mismo formato que `Data/DescargadorPaquete.py` y, si `ubicaciones` es `None`, **sin** `llaves.json`. Ninguna cripta de ejemplo usa datos de una cripta publicada (Principio VI). **Depende de T006**: `ubic` y `FuenteConLlaves` usan `UbicacionLlaveDTO`. `paquete_temporal` escribe `llaves.json` con el formato de [contracts/contrato-llaves.md](contracts/contrato-llaves.md) (la respuesta del API tal cual), así que **no espera a T013**. Las partes que no usan `UbicacionLlaveDTO` (`abierta`, `puerta`, `cara`, `permutar`) se pueden escribir antes.
- [x] T002 **(coordinar con el integrante 3)** *Confirmado por el integrante 3 el 14/11: el contrato del reporte de `7e685f4` queda tal cual.* Revisar y confirmar con el integrante 3, hoy (13/11), [contracts/contrato-reporte-resolubilidad.md](contracts/contrato-reporte-resolubilidad.md): las clases y campos de `DTO/ReporteResolubilidadDTO.py`, el formato de `UIController/TextoResolubilidad.py` (que la vista puede reutilizar, FR-315) y cómo llega el reporte a la interfaz (`ControladorBackend.verificar`, `iniciar`, `resolubilidad()`). Como no pidió cambios, ya no bloquea T007.
- [x] T003 **(coordinar con el integrante 1)** *Confirmado por el integrante 1 el 14/11: usar `Mazmorra.cargar_esqueleto` y `salida` sobre una instancia aparte, sin motor; avisará antes de cambiar `_igualar_caras` o lo que hace `cargar_esqueleto` al combinar caras.* Confirmar con el integrante 1 (plan, «Coordinación con el integrante 1», punto 1) que `Logic/GrafoLlaves.py` puede usar `Mazmorra.cargar_esqueleto(salas)` y `Mazmorra.salida(...)` sobre una instancia **aparte**, sin motor, para combinar las caras como en la primera parte (`_igualar_caras`). **No se le pide ningún cambio** a `Logic/Mazmorra.py`; se le pide que avise antes de cambiar la regla de `_igualar_caras` (las pruebas H1-10, H2-9 y H2-10 lo detectan). No bloquea nada.

---

## Fase 2: Base — contrato de llaves (Data y DTO; bloquea todas las historias)

**Propósito**: la entrega atrasada del 9/11 ([contracts/contrato-llaves.md](contracts/contrato-llaves.md), research R1)
y el DTO del reporte para el integrante 3 (research R2). Los escenarios de esta fase se prueban en Data; sus
versiones de punta a punta están en las fases 5 y 6.

**⚠️ Ninguna historia empieza antes de terminar esta fase.**

### Pruebas de la base ⚠️ (deben fallar primero)

- [ ] T004 [P] Escribir `tests/test_resolubilidad_datos.py` con las pruebas de `UbicacionLlaveDTO` (FR-316, FR-303): `test_fr316_ubicacion_desde_diccionario_con_y_sin_enemigo` (`{"id": "A", "sala": 4}` y `{"id": "B", "sala": 12, "enemigo": "e-1203"}`; `enemigo` ausente o `null` → `None`), `test_fr316_a_diccionario_omite_enemigo_none` (produce el mismo formato del API), `test_fr316_ubicacion_es_inmutable` (`@dataclass(frozen=True)`).
- [ ] T005 [P] Escribir en `tests/test_resolubilidad_reporte.py` las pruebas del DTO del reporte (contrato del reporte; FR-307 a FR-310, FR-322): `test_fr307_reporte_constantes_de_veredicto` (`RESOLUBLE = "resoluble"`, `NO_RESOLUBLE = "no_resoluble"`, `NO_CONCLUYO = "no_concluyo"`), `test_fr307_reporte_valores_por_defecto` (solo `id_cripta` y `veredicto` son obligatorios; `version_cripta`, `llave_salida`, `motivo` y `mensaje` valen `None`; las listas valen `[]` y **no se comparten** entre instancias, `field(default_factory=list)`), `test_fr307_reporte_orden_de_campos` (los 10 campos de `ReporteResolubilidadDTO` en el orden del contrato) y `test_fr310_clases_del_reporte_son_inmutables` (`PuertaLlaveDTO`, `LlaveNoObtenibleDTO`, `PasoCicloDTO`, `DependienteCicloDTO`, `CicloLlavesDTO`, `ReporteResolubilidadDTO`).

### Implementación de los DTO

- [ ] T006 [P] (FR-303, FR-316) Crear `DTO/UbicacionLlaveDTO.py`: `@dataclass(frozen=True) UbicacionLlaveDTO(id: str, sala: int, enemigo: str | None = None)`, con `desde_diccionario(d)` y `a_diccionario()` (omite `enemigo` si es `None`, igual que el API). Solo transporta datos: no valida, no ordena ni deduplica. Con type hints y docstring. Hace pasar T004.
- [ ] T007 [P] (FR-305 a FR-310, FR-322) Crear `DTO/ReporteResolubilidadDTO.py` según [contracts/contrato-reporte-resolubilidad.md](contracts/contrato-reporte-resolubilidad.md): constantes `RESOLUBLE`, `NO_RESOLUBLE`, `NO_CONCLUYO`; `PuertaLlaveDTO(sala_origen: int, direccion: int, sala_destino: int, llave: str | None)` («`llave = None` ⇒ "sin llave"»; `direccion` es el índice en `DTO/Direcciones.DIRECCIONES`, 0 N, 1 S, 2 E, 3 O); `LlaveNoObtenibleDTO(id, ubicaciones: list[UbicacionLlaveDTO])` («Lista vacía ⇒ "sin ubicación"»); `PasoCicloDTO(llave, ubicacion, puerta)` («`puerta.llave` = llave del paso siguiente»); `DependienteCicloDTO(llave, ubicacion, puerta, depende_de)` («`depende_de` es una llave del ciclo»); `CicloLlavesDTO(pasos, dependientes)` («Empieza por la llave de menor id»); `ReporteResolubilidadDTO(id_cripta, veredicto, version_cripta=None, llave_salida=None, orden_llaves=[], llaves_no_obtenibles=[], frontera=[], ciclos=[], motivo=None, mensaje=None)`, todas `@dataclass(frozen=True)` y las listas con `field(default_factory=list)`. Regla: «Campos nuevos al final, con valor por defecto». El contrato ya está confirmado (T002). Hace pasar T005.

### Pruebas de las fuentes, el almacén y el gestor ⚠️

- [ ] T008 Confirmar con el Swagger del servicio (hallazgo H-4) el formato de `GET /criptas/{id}/llaves` (raíz `llaves`, campos `id`, `sala`, `enemigo` opcional). Si difiere de [contracts/contrato-llaves.md](contracts/contrato-llaves.md), corregir primero el contrato (y la spec si cambia una regla) en un commit `plan(003)` propio, y solo después seguir con T009. Bloquea T011.
- [ ] T009 Agregar a `tests/test_resolubilidad_datos.py` las pruebas de las fuentes y el paquete (FR-316, FR-317, FR-318, FR-320): `test_fr317_fuente_por_defecto_lanza_error_red` (una `FuenteDatos` que no redefine `obtener_llaves` lanza `ErrorRed` «esta fuente no entrega la ubicación de las llaves»; `FuenteCuadricula` de `tests/Utilidades.py` y `_FuenteCuadricula` de `Service/BenchDatos.py` se siguen instanciando), `test_fr316_fuente_json_traduce_en_el_orden_de_la_respuesta` (sin ordenar ni deduplicar; una llave repetida llega repetida), `test_fr316_formato_invalido_es_error_red` (cada fila de la tabla «Validación de formato» del contrato: raíz sin `llaves` o que no es lista; `id` ausente, no texto o vacío; `sala` ausente, texto o `bool`; `enemigo` presente, no `null` y no texto no vacío → `ErrorRed` con la operación «ubicación de llaves de `<id>`»), `test_fr321_lista_vacia_es_valida`, `test_fr317_obtener_llaves_es_una_solicitud_que_cuenta` (`FuenteRed` con un proveedor de JSON falso, como las pruebas de Data de la primera parte: una sola solicitud a `criptas/{id}/llaves`, que cuenta en `presupuesto_solicitudes`), `test_fr318_lector_paquete_lee_llaves_json` (con `paquete_temporal` de T001; ninguna solicitud de red), `test_fr320_paquete_sin_llaves_json_es_error_red` (el «falta el archivo … en el paquete offline» que ya existe) y `test_fr318_descargador_escribe_llaves_json_tal_cual` (después de las páginas del esqueleto; si la solicitud de llaves falla, el paquete anterior queda intacto).

### Implementación de las fuentes

- [ ] T010 (FR-317, FR-318) En `Data/FuenteDatos.py` agregar `obtener_llaves(self, id_cripta: str) -> list[UbicacionLlaveDTO]`, **no abstracto**, cuya implementación por defecto lanza `ErrorRed(f"ubicación de llaves de {id_cripta}", "esta fuente no entrega la ubicación de las llaves")`. Así no se rompen las fuentes falsas que ya existen. Hace pasar la primera prueba de T009.
- [ ] T011 (FR-316, FR-317) En `Data/FuenteJson.py`: `obtener_llaves(id_cripta)` con `get_json(f"criptas/{id}/llaves", op)` y la traducción dentro de `_traducir`, y el estático público `ubicaciones_desde_diccionario(d: dict) -> list[UbicacionLlaveDTO]` (como `ficha_desde_diccionario`; lo usa también `AlmacenLlaves`), que valida el formato de la tabla del contrato con `es_entero` (un `bool` no cuenta). Formato inválido → `ErrorRed` de formato, no `ErrorDatos`. Entrega la lista en el orden de la respuesta. Depende de T008 y T010. Hace pasar las pruebas de formato de T009.
- [ ] T012 [P] (FR-318, FR-320) En `Data/FuenteOffline.py` (`LectorPaquete.get_json`) agregar la ruta `criptas/{id}/llaves` → `<carpeta>/<id>/llaves.json`; si falta, el `ErrorRed` «falta el archivo» que ya existe. Hace pasar `test_fr318_lector_paquete_lee_llaves_json` y `test_fr320_paquete_sin_llaves_json_es_error_red`.
- [ ] T013 [P] (FR-318) En `Data/DescargadorPaquete.py`, dentro de `descargar(id)`: pedir `criptas/{id}/llaves` después de las páginas del esqueleto y escribir `<id>/llaves.json` **tal cual**, junto con lo demás al final (si algo falla, el paquete anterior queda intacto). Los costos (`salas_p<N>.json`) y los `rango` (`catalogo.json`) no necesitan código nuevo. Hace pasar `test_fr318_descargador_escribe_llaves_json_tal_cual`.

### Pruebas del almacén y del gestor ⚠️

- [ ] T014 Agregar a `tests/test_resolubilidad_datos.py` las pruebas de `AlmacenLlaves` (FR-317, FR-319), con una carpeta temporal: `test_fr317_almacen_guarda_y_lee_la_misma_version` (archivo `cache/llaves/<id>.json` con `{"id", "version", "llaves"}` en el formato del API), `test_fr319_almacen_otra_version_es_ausente` (`leer` devuelve `None`; el siguiente `guardar` lo reemplaza, sin borrar nada a mano), `test_fr319_almacen_archivo_danado_se_borra` (`leer` lo borra y devuelve `None`), `test_fr319_almacen_id_distinto_es_ausente`, `test_fr317_almacen_id_inseguro_no_se_lee_ni_se_escribe` (`es_nombre_seguro`), `test_fr317_almacen_escribe_con_tmp_y_replace`.
- [ ] T015 (FR-317, FR-319) Crear `Data/AlmacenLlaves.py`: `AlmacenLlaves(carpeta: str = "cache/llaves")` con `leer(id_cripta, version) -> list[UbicacionLlaveDTO] | None` (solo si el archivo existe, se puede leer, su `id` coincide y `validar_version(guardada, version)` de Security es verdadero; dañado ⇒ se borra y `None`) y `guardar(id_cripta, version, ubicaciones) -> None` (`.tmp` + `os.replace`, como `AlmacenCatalogo`; ids que no pasan `es_nombre_seguro` no se leen ni se escriben). Traduce con `FuenteJson.ubicaciones_desde_diccionario`. La versión es `CriptaDTO.version`: no se pide `/version` aparte. Con type hints y docstring. Hace pasar T014.
- [ ] T016 Agregar a `tests/test_resolubilidad_datos.py` las pruebas de `validar_ubicaciones`, de `GestorLlaves` y de los escenarios de datos, con `FuenteConLlaves` de T001: `test_h2_7_fr321_fr320_sala_inexistente_es_error_de_datos` (`{ "id": A, "sala": 99 }` → `ErrorDatos` cuyo mensaje nombra la llave A y la sala 99, y el enemigo si lo trae; el programa no se cae), `test_h2_8_fr321_fr301_enemigo_inexistente_no_se_valida` (`{ "id": B, "sala": 12, "enemigo": "e-9999" }` con la sala 12 existente: no hay error y **no se pide contenido de ninguna sala**), `test_fr321_llave_sin_ubicacion_no_es_error_de_datos` (una puerta pide C y C no está en la lista: `GestorLlaves` no lanza nada), `test_h3_4_fr317_solicitud_de_llaves_cuenta_y_se_persiste` (una solicitud de llaves, dentro del presupuesto, y el archivo queda en el almacén), `test_h3_5_fr317_no_repite_la_solicitud` (segunda llamada con la misma versión: 0 solicitudes de llaves), `test_h3_6_fr319_datos_de_la_primera_parte_se_invalidan` (llaves persistidas con otra versión → se vuelven a pedir y se reemplazan; y los datos de la primera parte en `AlmacenCatalogo` con otra versión del catálogo se vuelven a obtener, sin cambiar `AlmacenCatalogo` y sin borrar archivos a mano), `test_h3_7_fr320_no_se_pudo_obtener_la_ubicacion` (presupuesto agotado, 429 repetido, error de red y paquete sin `llaves.json` → `ErrorRed` con contexto, sin caerse), `test_fr317_se_persiste_antes_de_validar_fr321` (con la sala 99: el archivo queda guardado y la segunda llamada da el mismo `ErrorDatos` sin otra solicitud), `test_fr318_sin_almacen_no_se_usa_cache` (`GestorLlaves(fuente, None)`: una respuesta persistida no tapa un `llaves.json` ausente del paquete, H3-7).

### Implementación del almacén y del gestor

- [ ] T017 (FR-321) En `Data/ValidacionDatos.py` agregar `validar_ubicaciones(operacion: str, ubicaciones: list[UbicacionLlaveDTO], existe_sala: Callable[[int], bool]) -> None`, O(U): lanza `ErrorDatos("ubicación de llaves de <id>", "la llave <llave> está en la sala <sala>, que no existe en el esqueleto")`, con «(enemigo <e>)» si lo trae, en la **primera** ubicación cuya sala no existe. Recibe la función `GestorEsqueleto.existe_sala`, no el gestor (evita el ciclo de importación). La instancia de enemigo **no** se valida. Hace pasar `test_h2_7_…` y `test_h2_8_…` de T016.
- [ ] T018 (FR-317, FR-319, FR-320, FR-321) Crear `Data/GestorLlaves.py`: `GestorLlaves(fuente: FuenteDatos, almacen: AlmacenLlaves | None)` con `obtener(cripta: CriptaDTO, esqueleto: GestorEsqueleto) -> list[UbicacionLlaveDTO]`: 1) si hay almacén y tiene la versión vigente, la usa; 2) si no, `fuente.obtener_llaves` y, si hay almacén, `guardar` (**antes** de validar); 3) `validar_ubicaciones(..., esqueleto.existe_sala)`. No mira `config.offline`: el almacén llega ya decidido. Los errores salen tal cual (`ErrorRed`, `ErrorDatos`). Con type hints y docstring. Hace pasar el resto de T016.
- [ ] T019 Correr `python tests/correr_pruebas.py`: todo en verde, incluidas las pruebas de Data de la primera parte (las fuentes falsas no se rompieron).

**Punto de control**: el contrato de llaves está entregado y el integrante 3 tiene el DTO del reporte.

---

## Fase 3: Historia 1 — Saber antes de jugar si la cripta es resoluble y en qué orden (P1) 🎯 MVP

**Objetivo**: `VerificadorResolubilidad.verificar(cripta, salas, ubicaciones)` decide el veredicto y entrega el
orden determinista de llaves (FR-301 a FR-306, FR-316, FR-322).

**Prueba independiente**: con criptas pequeñas armadas a mano, comparar el veredicto y el orden con el esperado.

### Pruebas de la historia 1 ⚠️ (deben fallar primero)

- [ ] T020 [US1] Escribir `tests/test_resolubilidad_logica.py` con los escenarios de la historia 1 que son de Logic, usando `tests/ayudas_resolubilidad.py`: `test_h1_1_fr301_fr304_fr305_unica_puerta_cerrada_es_la_de_salida` (orden `[llave_salida]`), `test_h1_2_fr304_fr322_sin_puertas_cerradas_no_resoluble_con_motivo` (no resoluble; `motivo` con el texto del contrato; `llave_salida` **no** está entre las no obtenibles y la frontera está vacía), `test_h1_3_fr304_fr305_cadena_a_b_llave_salida` (A antes que B, B antes que `llave_salida`), `test_h1_4_apendiceB_caso2_fr303_fr316_llave_de_enemigo_errante` (B obtenible en la sala 12, la del enemigo e-1203), `test_h1_5_apendiceB_caso3_fr305_fr306_mismo_orden_en_dos_ejecuciones` (dos verificaciones, también con las ubicaciones y las salas permutadas con `permutar`: siempre `[A, B, llave_salida]`; la versión en procesos separados es SC-303, T046), `test_h1_6_fr302_enemigo_trampa_cierre_y_costo_no_bloquean` (con costos distintos entre criptas iguales, el veredicto y el orden no cambian), `test_h1_7_fr302_las_llaves_no_se_consumen`, `test_h1_10_fr302_fr305_llave_declarada_en_una_sola_cara` (la puerta 1–3 se trata como cerrada con A desde sus dos salas), `test_h1_11_fr316_fr305_copia_alcanzable_de_la_llave` (A obtenible por su copia de la sala 4; ninguna ubicación es error).
- [ ] T021 [US1] Agregar a `tests/test_resolubilidad_logica.py` los casos borde y criterios sin escenario propio: `test_fr304_salida_alcanzable_por_salida_abierta_y_por_puerta_de_salida` (resoluble), `test_fr304_fr322_puerta_con_llave_salida_que_no_lleva_a_sala_salida` (no resoluble con el motivo de FR-322; es la diferencia conocida con el motor, hallazgo H-1), `test_fr304_solo_la_cara_de_sala_salida_pide_llave_salida` (la cara desde la que se entra pide otra llave: no cuenta), `test_fr304_llave_salida_en_la_sala_inicial` (obtenible en la oleada 0), `test_fr304_sala_inicial_es_sala_salida` (se aplica FR-304 sin excepciones), `test_fr305_llave_innecesaria_aparece_en_el_orden`, `test_fr302_cierre_automatico_con_llaves_distintas_por_cara_no_bloquea` (decisión del grupo, límite conocido: la verificación dice «resoluble»), `test_sc304_orden_valido_en_todas_las_criptas_resolubles` (con `orden_es_valido` de T001 sobre todas las criptas resolubles de este archivo) y `test_fr306_entrada_permutada_mismo_resultado` (el reporte completo es igual con 5 permutaciones de las ubicaciones y de las salas).

### Implementación de la historia 1

- [ ] T022 [US1] (FR-301, FR-302, FR-303, FR-304, FR-309, FR-316, FR-322) Crear `Logic/GrafoLlaves.py` (Logic; no importa Data ni Service), según [data-model.md](data-model.md) §3 y research R3, R4 y R5: crea una `Mazmorra` **aparte** con `cargar_esqueleto(salas)` y lee las caras ya combinadas en arreglos planos indexados por `c = sala*4 + dir`: `existe[s]`, `tipo_cara[c]` («0 sin salida · 1 abierta · 2 cerrada con llave · 3 cerrada sin llave»; una cara con llave pero no cerrada es abierta), `destino[c]` («sala destino, o −1»), `llave_cara[c]` («índice de llave, o −1»). **El costo y el cierre automático no se leen.** Índice de llaves (R3): menciones `(id_llave, tipo, posición)` (una por cara cerrada con llave, una por ubicación y una por `llave_salida`) → `Ordenador.ordenar` por id, tipo y posición → una pasada que asigna índices `0, 1, 2…` y los escribe en `llave_cara` y `llave_ubicacion`; `ids[k]` queda **ordenado** («índice menor = id menor»). Ubicaciones (R5, FR-309): ordenadas por (índice de llave, sala, sin enemigo antes que con enemigo, id de enemigo) con el `Ordenador` y una pasada O(U) que descarta cada una igual a la anterior («misma llave, sala y enemigo, o las dos sin enemigo»); `inicio_ubic[k]`, `fin_ubic[k]` («vacío ⇒ "sin ubicación"») y `llaves_en_sala[s]`. `llave_salida` («siempre existe: se menciona siempre»), `sala_inicial`, `sala_salida`, `es_cara_de_salida[c]` («`c` lleva a `sala_salida`, está cerrada y su propia llave (ya combinada) es `llave_salida`») y `hay_puerta_de_salida`. Sin `dict`, `set` ni `sorted`. O(S + E + U + M log M). La `Mazmorra` auxiliar se descarta: no toca el motor, el generador aleatorio ni el contenido (FR-301). Con type hints y docstring.
- [ ] T023 [US1] (FR-302, FR-305, FR-306, NFR-302) Crear `Logic/RecorridoLlaves.py` con el recorrido incremental por oleadas (research R4, pasos 1 a 3): arreglos `alcanzable[s]`, `estado_llave[k]` («0 sin ver · 1 vista en la oleada actual · 2 obtenida»), `oleada_llave[k]` («oleada en que se obtuvo, o −1»), `orden`, `esperando[k]` («caras cerradas con la llave `k` que salen de una sala alcanzable; se vacía al obtener `k`»), `sin_llave` y `caras_de_salida` (toda cara con `es_cara_de_salida[c]` que sale de una sala alcanzable, se haya obtenido o no la llave). Cola de `Estructuras/Cola.py`. Al terminar cada oleada, las llaves nuevas se ordenan por índice (= por id) con el `Ordenador`, pasan a 2 y se agregan al orden; luego **solo** se reabren sus `esperando[k]`. Nunca se repite el recorrido completo (NFR-302). O(S + E + U + K log K). Con type hints y docstring.
- [ ] T024 [US1] (FR-301, FR-304, FR-305, FR-322) Crear `Logic/VerificadorResolubilidad.py`: `verificar(cripta: CriptaDTO, salas: list[SalaDTO], ubicaciones: list[UbicacionLlaveDTO]) -> ReporteResolubilidadDTO`, sin estado entre llamadas. Arma `GrafoLlaves`, corre `RecorridoLlaves` y decide con la tabla de [data-model.md](data-model.md): `hay_puerta_de_salida` falso → `NO_RESOLUBLE` con `motivo` (texto literal del contrato del reporte: «Ninguna puerta cerrada por la que se entra a la sala de salida `<sala_salida>` pide `<llave_salida>` desde la sala de la que se entra (las puertas que piden `<llave_salida>` pero no llevan a la sala `<sala_salida>` no cuentan): la victoria es imposible (§3.5, P1 §2.12).»); `llave_salida` obtenida **y** `caras_de_salida` no vacía → `RESOLUBLE` con `orden_llaves` (ids en el orden de las oleadas); si no, `NO_RESOLUBLE` sin `motivo`. **No se usa `alcanzable[sala_salida]`** (riesgo R-8). Llena `id_cripta`, `version_cripta` y `llave_salida`. En esta fase el reporte no resoluble solo lleva el veredicto y el motivo (el resto llega en T033). Hace pasar T020 y T021.
- [ ] T025 [US1] Correr `python tests/correr_pruebas.py`. **Parar y validar**: los casos 2 y 3 del Apéndice B pasan.

---

## Fase 4: Historia 2 — Entender por qué una cripta no es resoluble (P1)

**Objetivo**: el reporte completo de una cripta no resoluble, del mismo recorrido: llaves no obtenibles con sus
ubicaciones, frontera bloqueada, ciclos y llaves dependientes (FR-307 a FR-310, NFR-303).

**Prueba independiente**: con criptas no resolubles armadas a mano, comparar cada parte del reporte con la esperada.

### Pruebas de la historia 2 ⚠️ (deben fallar primero)

- [ ] T026 [US2] Agregar a `tests/test_resolubilidad_reporte.py` los escenarios de llaves no obtenibles, ubicaciones y frontera: `test_h2_1_apendiceB_caso1_fr304_fr307_fr308_fr309_fr310_llave_salida_detras_de_su_puerta` (`sala_salida` 5: no obtenibles `[llave_salida]`; frontera la puerta 4–5 con `llave_salida`; ubicación sala 5; ciclo de un paso `llave_salida` → puerta 4–5), `test_h2_5_fr307_fr308_frontera_sin_repetir` (las puertas 2–6, 3–7 y 4–10, una vez cada una y con su llave; D no aparece entre las no obtenibles), `test_h2_6_fr307_fr308_fr309_fr321_llave_sin_ubicacion` (C con `ubicaciones` vacía, la puerta 4–5 en la frontera con C, sin error de datos), `test_h2_9_fr302_fr308_llaves_distintas_por_cara` (con A obtenible la sala 6 es alcanzable; si A no es obtenible, la puerta 2–6 está en la frontera con A, la de la cara de la sala alcanzable), `test_h2_10_fr302_fr308_cara_cerrada_sin_llave` (la frontera lista la puerta 3–7 con `llave = None`, «sin llave: no se puede abrir»; si la sala 7 se alcanza por otro camino, desde ella se llega a la 3), `test_h2_11_fr308_salida_sin_vuelta_hacia_la_region_no_es_frontera` y `test_h1_12_fr316_fr309_fr306_ubicaciones_identicas_una_sola_vez` (C con cuatro ubicaciones en la lista: el reporte lista tres, sala 10 una sola vez, sala 13 y sala 13 con e-1301, en ese orden, igual en varias verificaciones).
- [ ] T027 [US2] Agregar a `tests/test_resolubilidad_reporte.py` los escenarios de ciclos y dependientes: `test_h2_2_fr307_fr310_ciclo_de_dos_llaves` (A en sala 6 → puerta 2–6 requiere B → B en sala 7 → puerta 3–7 requiere A; `llave_salida` dependiente de A), `test_h2_3_fr306_fr310_reporte_identico_en_cada_ejecucion` (5 verificaciones con entradas permutadas: el mismo DTO, incluida la llave por la que empieza el ciclo y el orden de llaves y puertas), `test_h2_4_fr307_fr309_fr310_dependiente_del_ciclo` (C no está en un ciclo propio y se lista dentro del ciclo A–B con `depende_de = A`), `test_h2_12_fr307_fr310_fr306_dos_ciclos_independientes` (A–B y E–F una vez cada uno, por id de la llave inicial; `llave_salida` y G dependen de A, H de E), `test_h2_13_fr306_fr307_fr308_fr310_puerta_que_bloquea` (las puertas 2–6 y 3–6 son de nivel 1 y la que bloquea a A es la 2–6, por menor sala de origen; un solo ciclo {B}; A dependiente de B con la puerta 2–6; A no forma un ciclo propio; la frontera lista 2–6, 3–6, 4–7 y 4–8) y `test_sc305_reporte_completo_en_todas_las_no_resolubles` (en cada cripta no resoluble de este archivo: cada no obtenible con su id y todas sus ubicaciones o lista vacía; cada puerta de la frontera con sus dos salas y su llave o `None`; cada ciclo con la secuencia completa hasta volver a la primera llave: la `puerta.llave` del último paso es la llave del primero).
- [ ] T028 [P] [US2] Escribir `tests/test_resolubilidad_bench.py` con las pruebas del generador de cuadrícula (research R7; lo usa la prueba de recursión de T029): `test_nfr304_cuadricula_es_determinista_por_semilla` (misma semilla → mismas salas, ubicaciones y orden de la lista; otra semilla → otro orden de la lista y otras filas de las llaves), `test_nfr304_cuadricula_exige_dos_filas` (`filas < 2` → `ValueError`), `test_nfr304_cuadricula_resoluble` (la verificación dice resoluble y el orden tiene `columnas` llaves) y `test_nfr303_cuadricula_no_resoluble_un_ciclo_y_una_cadena` (solo se mueve la llave de la columna *m* = (`columnas` − 1) // 2: el reporte tiene **un** ciclo de un paso, *m* → *m*, y unas K/2 dependientes de *m*).
- [ ] T029 [US2] Agregar a `tests/test_resolubilidad_reporte.py` `test_fr310_cadena_de_mas_de_1000_dependientes_sin_recursion` (research R6 y R7, riesgo R-9): `cripta_en_cuadricula(filas=2, columnas=3000, semilla, resoluble=False)` (6 000 salas, unas 1 500 dependientes, por encima del límite de recursión de Python): la verificación termina sin `RecursionError`, con un solo ciclo y todas las dependientes listadas, y `sys.getrecursionlimit()` no cambió.

### Implementación de la historia 2

- [ ] T030 [US2] (NFR-304; adelanto del bench) Crear `Logic/BenchResolubilidad.py` **solo con el generador** `cripta_en_cuadricula(filas: int, columnas: int, semilla: int, resoluble: bool) -> tuple[CriptaDTO, list[SalaDTO], list[UbicacionLlaveDTO]]`, según research R7, con `random.Random(semilla)`: salidas abiertas entre vecinas de la misma columna; entre la columna *c* y *c + 1*, puertas que piden la llave *c*; la llave *c* en una fila elegida por la semilla dentro de la columna *c*; el orden de la lista de ubicaciones mezclado con la semilla; `filas ≥ 2` o `ValueError`; `sala_salida` en (fila 0, última columna), con su única entrada desde la fila 1 que pide `llave_salida`, ubicada en la última columna; variante no resoluble: se mueve **solo** la llave de la columna *m* a la columna *m + 1*. Sin datos de criptas publicadas. Las mediciones llegan en la fase 9. Hace pasar T028.
- [ ] T031 [US2] (FR-308, FR-310, NFR-303) En `Logic/RecorridoLlaves.py` agregar: (a) la **frontera** (research R4, paso 5): las caras que quedaron en `esperando[k]` de llaves no obtenidas y en `sin_llave` cuyo destino **sigue** fuera de la región, ordenadas por `c` con el `Ordenador` («caras de la frontera, ordenadas por `c`»); cada puerta una vez y con la llave de la cara de la sala alcanzable; (b) la **fase hacia afuera** (research R6), continuación del mismo recorrido, **sin recursión**: nivel 1 = las puertas de la frontera en orden; para cada una, si su destino no tiene puerta asignada, se le asigna y se inunda su zona con la `Cola` (caras abiertas o con llave obtenida); las caras cerradas con llave no obtenida o sin llave que salen de la zona se anotan para el nivel siguiente, que se ordena por (sala de origen, dirección) antes de procesarlo. Arreglos `puerta_que_encierra[s]` («la puerta que bloquea la zona de `s` según FR-310 […], o −1»; el docstring aclara que es **«la puerta que bloquea»** de FR-310, con otro nombre) y `nivel[s]` («0 dentro de la región, −1 si no se llega»). Cada sala y cada cara una vez: O(S + E) más ordenar cada nivel.
- [ ] T032 [US2] (FR-310) Crear `Logic/CiclosLlaves.py`, **iterativo** (research R6, data-model §3): `siguiente[k]` (la llave de la puerta que encierra la ubicación de menor nivel de `k`, desempate por el orden de FR-309; −1 si la puerta no tiene llave, si la llave no tiene ubicación o si su sala no se alcanza ni cruzando puertas), `ubic_usada[k]`, `marca[k]`, `pos_camino[k]`, `camino`, `ciclo_de[k]` y `entrada[k]`. Se recorren las no obtenibles por id; cada recorrido es un `while` que agrega a `camino`; al salir, un `for` sobre `camino` asigna `entrada`: ciclo nuevo desde `pos_camino[k]` (rotado para que empiece por su llave de menor id), la `entrada` de un recorrido anterior, o −1. Ciclos por id de su llave inicial; dependientes de cada ciclo por id. O(K) + O(K log K). Con type hints y docstring. Hace pasar T029.
- [ ] T033 [US2] (FR-307, FR-308, FR-309, FR-310, NFR-303) En `Logic/VerificadorResolubilidad.py`, si el veredicto es `NO_RESOLUBLE`: correr la fase hacia afuera y `CiclosLlaves` y traducir los índices a DTO: `llaves_no_obtenibles` (todas las no obtenidas, por id, con sus ubicaciones distintas en el orden de R5, o lista vacía), `frontera` (`PuertaLlaveDTO` por sala alcanzable y dirección, `llave = None` si es «sin llave»), `ciclos` (`PasoCicloDTO` con la ubicación usada y la puerta que la bloquea; `DependienteCicloDTO` con `depende_de`). Las no obtenibles con `entrada = −1` solo aparecen en `llaves_no_obtenibles`. Todo sale del mismo recorrido, sin recorridos por llave (NFR-303). Hace pasar T026, T027 y T029.
- [ ] T034 [US2] Correr `python tests/correr_pruebas.py`. **Parar y validar**: el caso 1 del Apéndice B pasa.

---

## Fase 5: Servicio — verificar e iniciar una partida nueva (historias 1 y 4)

**Objetivo**: `ServicioResolubilidad` (FR-301, FR-311, FR-312, FR-313, FR-315, FR-320, FR-323): verifica antes de
crear el motor, no inicia una cripta no resoluble sin `--forzar` y deja el reporte en el contexto.

**Prueba independiente**: iniciar partidas con criptas resolubles, no resolubles y con errores, con y sin `forzar`,
y comprobar si se crea el motor, `partida.log` y el guardado, y qué reporte queda.

**Paso previo, antes de T037 (sin número propio)**: hacer `git merge origin/kris` en la rama del integrante 2 para
trabajar sobre la versión del integrante 3 de `Service/ServicioPartida.py` (`iniciar_partida` con los grabadores y el
punto de control 0), `Service/ContextoPartida.py` (`linea` como último campo) y `UIController/ControladorBackend.py`,
y correr `python tests/correr_pruebas.py`: todo en verde antes de tocar esos archivos. Si hay conflictos, se resuelven
conservando lo del integrante 3 y se le avisa.

### Pruebas del servicio ⚠️ (deben fallar primero)

- [ ] T035 [US1] Escribir `tests/test_resolubilidad_servicio.py` (con `FuenteConLlaves` y `paquete_temporal` de T001, carpetas temporales como `tests/test_servicios.py`): `test_h1_8_fr301_no_descarga_contenido_ni_consume_azar` (antes de crear el motor no se pidió contenido de ninguna sala ni se consumió el generador; la partida iniciada con semilla S es idéntica a la de `ServicioPartida.iniciar_partida` con S, y a la de `--replay` de su `partida.log`), `test_h1_9_fr313_reporte_en_el_contexto_antes_de_la_primera_accion` (`contexto.resolubilidad` es el reporte resoluble con su orden apenas termina `iniciar_partida_nueva`, sin ninguna acción; mostrarlo en la ventana es de T055 (vista)), `test_r9_fr301_verificacion_no_registra_en_historial_linea_ni_log` (historial de retroceso vacío, línea de tiempo sin acciones y `partida.log` solo con el encabezado), `test_h2_8_fr301_fr303_fr321_iniciar_sin_descargar_contenido` (enemigo e-9999 inexistente: B obtenible en la sala 12, ninguna solicitud de contenido durante la verificación), `test_r3_fr317_no_pide_dos_veces_datos_ni_esqueleto` (una solicitud de datos generales y las del esqueleto una sola vez, gracias a `datos=`) y `test_fr315_verificar_e_iniciar_dan_el_mismo_reporte`.
- [ ] T036 [US4] Agregar a `tests/test_resolubilidad_servicio.py`: `test_h4_1_apendiceB_caso4_fr311_no_resoluble_no_inicia` (`ErrorPartidaNoIniciada` con `.reporte` no resoluble completo; no se creó `partida.log` ni guardado; el reloj no avanzó), `test_h4_2_fr312_fr313_forzar_inicia_con_advertencia` (inicia y `contexto.resolubilidad` es el reporte no resoluble), `test_h4_3_fr312_forzar_con_resoluble_no_cambia_nada` (el mismo contexto y el mismo reporte que sin `forzar`), `test_h4_4_fr301_fr313_cargar_y_replay_no_verifican` (partida iniciada con `forzar` sobre una cripta no resoluble, guardada y registrada: cargarla con `ServicioGuardado` y reproducirla con `ServicioReplay` funciona, no se pide la ubicación de llaves, `ServicioResolubilidad` no se llama y no queda ningún reporte para mostrar), `test_h4_5_fr323_costos_distintos_no_inicia_ni_con_forzar` (salida 3–4 con costos 150 y 200: el `ErrorDatos` de `GestorEsqueleto` se propaga con la salida y el campo; sin `partida.log` ni guardado), `test_fr323_cierre_automatico_invalido_no_inicia_ni_con_forzar` (una salida con `cierre_automatico` 0: el `ErrorDatos` se propaga con la sala, la dirección y el campo, sin `partida.log` ni guardado, con y sin `forzar`; depende de **T055 de la 001**, que se hace antes que esta feature), `test_h2_7_fr320_fr321_sala_inexistente_inicia_solo_con_forzar` (sin `forzar`: `ErrorPartidaNoIniciada` con un reporte `NO_CONCLUYO` cuyo `mensaje` nombra A y la sala 99; con `forzar`: inicia con ese reporte como advertencia), `test_fr320_llaves_no_disponibles_inicia_solo_con_forzar` (presupuesto agotado, 429, red), `test_fr312_forzar_al_cargar_sin_efecto` (cargar con la configuración `forzar=True` da el mismo resultado que sin ella), y dos pruebas de `verificar` que son de la **(historia 3)**: `test_fr314_verificar_cripta_inexistente_no_concluyo` (historia 3; 404 en línea y carpeta ausente del paquete en `--offline`: `verificar` devuelve `NO_CONCLUYO` con el mensaje, sin caerse) y `test_fr323_verificar_costo_invalido_no_concluyo` (historia 3; `verificar` devuelve `NO_CONCLUYO` sin veredicto: `orden_llaves`, `llaves_no_obtenibles`, `frontera`, `ciclos` y `motivo` vacíos).

### Coordinación e implementación del servicio

- [ ] T037 **(coordinar con el integrante 3)** (FR-311, FR-317, FR-318) Escribir en `Service/ServicioPartida.py` (acordado con el integrante 3 el 14/11; ella lo revisa antes del merge), sobre su versión de `origin/kris` (paso previo), según la tabla de cambios del plan. Primero la prueba, que falla, en `tests/test_resolubilidad_servicio.py`: `test_fr318_offline_sin_almacen_de_llaves` (con `--offline`, `fuente()` es `FuenteOffline` y `almacen_llaves()` es `None`), `test_fr317_red_con_almacen_de_llaves` (sin `--offline`, `FuenteRed` y un `AlmacenLlaves`) y `test_fr311_iniciar_partida_con_datos_no_los_vuelve_a_pedir`. Cambios: (a) parámetro **final** `datos=None` en `iniciar_partida`: si viene, no llama a `abrir_datos` (no pedir dos veces los datos generales y el esqueleto, riesgo R-3); (b) que el **mismo `if`** de `fuente()` elija también el almacén de llaves: offline → `FuenteOffline()` y sin almacén; red → `FuenteRed()` y `AlmacenLlaves()` (T015); método nuevo `almacen_llaves() -> AlmacenLlaves | None`, que llama antes a `fuente()`; y parámetro **final** `almacen_llaves=None` en el constructor, para las pruebas que inyectan la fuente. La línea de tiempo y los grabadores de su `iniciar_partida` no cambian. Comprobar que sus pruebas y las de la 004 siguen en verde. Bloquea T039.
- [ ] T038 **(coordinar con el integrante 3)** (FR-313) Escribir en `Service/ContextoPartida.py` (acordado con el integrante 3 el 14/11; ella lo revisa antes del merge), sobre su versión de `origin/kris`, primero con su prueba en `tests/test_resolubilidad_servicio.py`, `test_fr313_contexto_resolubilidad_ultimo_campo_y_none` (es el último campo, después de `linea`, y vale `None` si no se pasa), el campo **final** `resolubilidad: ReporteResolubilidadDTO | None = None`, **después de `linea`** de la 004. `PartidaGuardada` no lo guarda (al cargar no se verifica). Bloquea T039.
- [ ] T039 [US1] (FR-301, FR-311, FR-312, FR-313, FR-314, FR-315, FR-320, FR-323) Crear `Service/ServicioResolubilidad.py`, según research R8: `ErrorPartidaNoIniciada(ValueError)` con `reporte: ReporteResolubilidadDTO` y un mensaje corto para el jugador (mismo patrón que `ErrorCarga` y `ErrorReplay`; este módulo **no** importa `ErroresServicio`); `ServicioResolubilidad(partida: ServicioPartida)` con `verificar(id_cripta) -> ReporteResolubilidadDTO` (solo datos generales, esqueleto y llaves, sin el resolvedor del catálogo; cualquier `ErrorRed`, incluidos el 404 de una cripta inexistente, el «falta el archivo» del paquete, FR-321 y FR-323, da un reporte `NO_CONCLUYO` con `mensaje`) e `iniciar_partida_nueva(id_cripta, nombre, forzar, semilla=None) -> ContextoPartida`: 1) `datos = partida.abrir_datos(id)`; un error aquí, incluido FR-323 o la cripta inexistente, **se propaga** (no inicia ni con `forzar`); 2) `GestorLlaves(partida.fuente(), partida.almacen_llaves()).obtener(...)`; un `ErrorRed` o `ErrorDatos` aquí se convierte en `NO_CONCLUYO` (FR-320, FR-321); 3) `VerificadorResolubilidad.verificar(...)`; 4) si no es `RESOLUBLE` y no hay `forzar`, `ErrorPartidaNoIniciada(reporte)`, sin motor, log ni guardado; 5) si no, `partida.iniciar_partida(id, nombre, ..., datos=datos)` y `contexto.resolubilidad = reporte`. **No mira `config.offline`**; no registra nada en el historial, la línea ni el log (R9). Con type hints y docstring. Depende de T037 y T038. Hace pasar T035 y T036.
- [ ] T040 **(coordinar con el integrante 3)** (FR-311, FR-320) Escribir en `Service/ErroresServicio.py` (acordado con el integrante 3 el 14/11; ella lo revisa antes del merge), primero con su prueba en `tests/test_resolubilidad_servicio.py`, `test_fr311_error_partida_no_iniciada_es_esperado` (`ErrorPartidaNoIniciada` está en `ERRORES_ESPERADOS`), **solo** importar `ErrorPartidaNoIniciada` de `Service/ServicioResolubilidad.py` y agregarlo a `ERRORES_ESPERADOS`, como ya se hace con `ErrorCarga` y `ErrorReplay`. Sin import circular: `ServicioResolubilidad` no importa `ErroresServicio`. Depende de T039.
- [ ] T041 **Aviso** al integrante 3: `ServicioResolubilidad` (T039) y `DTO/ReporteResolubilidadDTO.py` (T007) están listos; puede empezar a mostrar el reporte **antes de la primera acción del jugador** (FR-313), como advertencia con `--forzar` (FR-312) y completo si la partida no inicia (FR-311), según el contrato del reporte. Ver T054 y T055 (vista).
- [ ] T042 Correr `python tests/correr_pruebas.py`. **Parar y validar**: el caso 4 del Apéndice B pasa; `--replay` de `ejemplos/partida_ejemplo.log` sigue igual.

---

## Fase 6: Historia 3 — Verificar una cripta sin jugar con `--verificar` (P2)

**Objetivo**: `--verificar <cripta>` escribe el resultado en la salida estándar, sin vista ni partida, también con
`--offline`, y termina con 0, 3 o 1; `--forzar` existe y no cambia nada con `--verificar` (FR-312, FR-314, FR-315).

**Prueba independiente**: ejecutar `--verificar` sobre criptas resolubles y no resolubles, en línea y con
`--offline`, y comprobar la salida, el código, que no se importa la vista y las solicitudes.

### Pruebas de la historia 3 ⚠️ (deben fallar primero)

- [ ] T043 [US3] Escribir `tests/test_resolubilidad_cli.py` con las pruebas de argumentos (no se edita `tests/TestLectorArgumentos.py`): `test_fr314_verificar_lee_el_id` (`config.verificar == "cripta-01"`), `test_fr314_verificar_sin_valor_o_vacio_codigo_2` (`--verificar` sin valor y `--verificar ""` → `ErrorArgumentos`, código 2), `test_fr314_verificar_con_replay_o_bench_codigo_2` (grupo excluyente), `test_fr312_forzar_por_defecto_falso_y_no_excluyente` (`--forzar` con `--replay`, con `--bench`, con `--verificar` y solo se acepta), `test_fr314_campos_de_configuracion_detras_de_hasta` (`dataclasses.fields(ConfiguracionDTO)` termina en `checkpoint_cada`, `hasta`, `verificar`, `forzar`; los valores por defecto son `None` y `False`) y `test_fr314_banderas_de_la_004_sin_cambios` (`--checkpoint-cada` y `--hasta` se comportan igual).
- [ ] T044 [US3] Agregar a `tests/test_resolubilidad_cli.py` las pruebas de `UIController/TextoResolubilidad.py`, con el formato del contrato del reporte: `test_fr314_texto_resoluble` (encabezado con id y versión, «RESOLUBLE» y el orden), `test_fr307_fr309_texto_no_resoluble` (llaves no obtenibles con «sala N», «sala N (enemigo e)» y «sin ubicación»; la frontera con «requiere X» o «sin llave: no se puede abrir»; los ciclos con «→» y sus dependientes debajo), `test_fr322_texto_con_motivo` y `test_fr323_texto_no_concluyo_sin_veredicto` (solo el encabezado «la verificación NO CONCLUYÓ» y el mensaje).
- [ ] T045 [US3] Agregar a `tests/test_resolubilidad_cli.py` los escenarios de `main` (como `tests/test_main.py`, con `FuenteConLlaves` y `paquete_temporal`): `test_h3_1_fr314_fr315_verificar_resoluble_codigo_0`, `test_h3_2_fr314_fr315_verificar_no_resoluble_codigo_3` (el texto es idéntico a `lineas_reporte` del reporte que deja `iniciar_partida_nueva` con la misma cripta), `test_h3_3_fr314_fr318_fr306_verificar_offline_igual_que_en_linea` (con `--offline`, 0 solicitudes de red y la misma salida), `test_h3_7_fr320_fr314_verificar_sin_llaves_codigo_1` (presupuesto agotado, 429, red y paquete sin `llaves.json`), `test_h3_8_fr323_fr314_costo_cero_codigo_1` (mensaje con la salida y el campo, sin veredicto, sin caerse), `test_h3_9_fr314_forzar_no_cambia_verificar` (las tres criptas: mismo texto y códigos 0, 3 y 1 con y sin `--forzar`), `test_h2_7_fr321_fr314_verificar_sala_inexistente_codigo_1` y `test_fr323_fr314_cierre_automatico_invalido_codigo_1` (un esqueleto con una salida con `cierre_automatico` 0: `--verificar` termina con código 1, muestra el error con contexto, con la sala, la dirección y el campo `cierre_automatico`, y no muestra ningún veredicto). Esta última depende de la validación en Data de **T055 de la 001** (integrante 2), que se hace antes que esta feature.
- [ ] T046 [US3] Agregar a `tests/test_resolubilidad_cli.py` las pruebas sin escenario propio: `test_fr314_verificar_cripta_inexistente_codigo_1` (en línea con 404 y con `--offline` sin la carpeta en el paquete, con y sin `--forzar`: «la verificación NO CONCLUYÓ» con contexto, código 1, sin caerse), `test_fr312_forzar_con_replay_sin_efecto` (`--replay L --forzar` da la misma salida y el mismo código que `--replay L`), `test_fr312_forzar_con_bench_sin_efecto` (con la lista de mediciones reemplazada por una medición chica: mismas filas y mismo código), `test_fr301_bench_no_llama_a_servicio_resolubilidad`, `test_sc308_verificar_sin_vista` (en un proceso aparte: `pygame` y `View` no quedan en `sys.modules`; no se crea `partida.log`), `test_sc308_verificar_offline_sin_solicitudes_de_red`, `test_sc303_diez_ejecuciones_en_procesos_separados` (cada cripta de prueba, 10 veces con `subprocess`, en línea con la fuente falsa y con `--offline` con un paquete temporal: el texto completo de las 10 salidas es idéntico; incluye la cripta de H1-5) y `test_fr314_verificar_utf8_sin_pythonioencoding` (corre `--verificar` en otro proceso **sin** `PYTHONIOENCODING` en el entorno, con una cripta no resoluble con ciclo, cuyo texto tiene «→», y lee la salida como UTF-8: código 3 y el «→» intacto). Todas las pruebas que corren en otro proceso (SC-303, SC-308 y esta) leen la salida como UTF-8.

### Implementación de la historia 3

- [ ] T047 [US3] (FR-312, FR-314) En `DTO/ConfiguracionDTO.py` agregar, **detrás de `hasta`**, `verificar: str | None = None` y `forzar: bool = False`, y documentarlos en el docstring. En `UIController/LectorArgumentos.py`: `--verificar CRIPTA` **dentro del grupo excluyente** `modo`, con `--replay` y `--bench`, con un tipo que rechaza el texto vacío (`ErrorArgumentos`, código 2); `--forzar` (`store_true`) **fuera** de cualquier grupo excluyente; texto de ayuda de las dos. Sin tocar `--checkpoint-cada` ni `--hasta`. Hace pasar T043.
- [ ] T048 [P] [US3] (FR-314, FR-315) Crear `UIController/TextoResolubilidad.py`: `lineas_reporte(reporte: ReporteResolubilidadDTO) -> list[str]` con el formato del contrato del reporte (encabezado; orden; motivo; llaves no obtenibles; frontera como «puerta a–b (desde la sala a, salida D)»; ciclos numerados con sus dependientes; «la verificación NO CONCLUYÓ» con el mensaje). No calcula nada: solo da formato a lo que trae el DTO. No importa pygame. La vista puede reutilizarlo. Con type hints y docstring. Hace pasar T044.
- [ ] T049 [US3] **(coordinar con el integrante 3)** (FR-314, FR-315) Escribir en `UIController/ControladorBackend.py` (acordado con el integrante 3 el 14/11; ella lo revisa antes del merge), sobre su versión de `origin/kris`, el método nuevo `verificar(id_cripta) -> ReporteResolubilidadDTO`, **al final de la clase** (después de los métodos de la 004; quien suba segundo hace el `merge`), que crea el `ServicioPartida` con la configuración y devuelve `ServicioResolubilidad(partida).verificar(id_cripta)`. No instancia la vista. Sus pruebas son las de `main` de T045 y T046, que pasan por este método. Bloquea T050.
- [ ] T050 [US3] (FR-314) En `main.py`, **sobre la versión con la rama `--hasta` del integrante 3**: rama `--verificar` que, **antes de escribir**, configura la salida estándar en UTF-8 con `sys.stdout.reconfigure(encoding="utf-8")` **solo si** `sys.stdout` tiene `reconfigure` (las pruebas que capturan la salida con `StringIO` o `redirect_stdout` no lo tienen) y **solo en esta rama**, sin cambiar los otros modos (en una consola de Windows con la salida redirigida, `print` de «→» lanza `UnicodeEncodeError` con cp1252, y `--verificar` no debe caerse, FR-314); llama a `ControladorBackend.verificar(config.verificar)`, escribe con `print` las líneas de `TextoResolubilidad.lineas_reporte` en la salida estándar y devuelve **0** si es `RESOLUBLE`, **3** si es `NO_RESOLUBLE` y **1** si es `NO_CONCLUYO`; el **2** sigue siendo solo de argumentos inválidos. No importa pygame ni `View/` en esa rama, no inicia partida y no lee `config.forzar`. El programa no se cae ante ningún error de datos o de red. Depende de T047, T048 (`TextoResolubilidad`) y T049. Hace pasar T045 y T046.
- [ ] T051 **Aviso** al integrante 1: `--verificar` y `--verificar --offline` ya existen. Puede quitar el `skipTest` de `test_h3_7_fr118_fr122_verificar_no_depende_de_costos_ni_cazadores` en `tests/test_terreno_cazador.py` (escenario H3-7 de la 001) y cerrar la **T048 de la 001** (la línea `PENDIENTE` de `--verificar` en `tests/test_modos_sin_vista_terreno.py`). El integrante 2 no edita esos archivos.
- [ ] T052 Correr `python tests/correr_pruebas.py` y seguir [quickstart.md](quickstart.md) §2, pasos 5, 6, 8, 9 y 10 (los que no dependen del paquete regenerado; el paso 8, la cripta inexistente en línea, **necesita red**, porque el 404 lo responde el servicio); con el paquete actual, el paso 1 debe terminar con código **1** y «falta el archivo … llaves.json» (H-3).

---

## Fase 7: Historia 4 — Jugar de todas formas con `--forzar` (P3)

**Objetivo**: la partida normal pasa por la verificación: sin `--forzar` una cripta no resoluble no inicia y se ve el
reporte; con `--forzar` inicia con el reporte como advertencia (FR-311, FR-312, FR-313).

**Prueba independiente**: intentar iniciar una partida con una cripta no resoluble, con y sin `--forzar`, y
comprobar si inicia y si se muestra el reporte.

### Pruebas de la historia 4 ⚠️

- [ ] T053 [US4] Agregar a `tests/test_resolubilidad_cli.py` las pruebas del controlador: `test_fr311_controlador_no_inicia_y_guarda_el_reporte` (`iniciar` con una cripta no resoluble y sin `--forzar` lanza `ErrorOperacion` con un mensaje corto y `resolubilidad()` devuelve el reporte completo), `test_fr312_fr313_controlador_inicia_con_forzar` (`resolubilidad()` devuelve el reporte de advertencia), `test_fr313_controlador_resoluble_muestra_el_orden` y `test_fr301_controlador_resolubilidad_none_al_cargar_y_en_replay` (con y sin `--forzar`).

### Coordinación de la historia 4

- [ ] T054 [US4] **(coordinar con el integrante 3)** (FR-311 a FR-313) Escribir en `UIController/ControladorBackend.py` (acordado con el integrante 3 el 14/11; ella lo revisa antes del merge), sobre su versión de `origin/kris` (quien suba segundo hace el `merge`): que `iniciar` llame a `ServicioResolubilidad.iniciar_partida_nueva(id, nombre, config.forzar)` en lugar de ir directo a `ServicioPartida.iniciar_partida`, y guarde el reporte (el de `contexto.resolubilidad` y también el de `ErrorPartidaNoIniciada.reporte`, que llega como `ErrorOperacion` gracias a T040); método nuevo `resolubilidad() -> ReporteResolubilidadDTO | None`, **al final de la clase** (`None` al cargar una partida y en `--replay`). Cargar y `--replay` no pasan por `ServicioResolubilidad`. Depende de T039 y T040. Hace pasar T053.
- [ ] T055 [US4] **(coordinar con el integrante 3)** (FR-311, FR-312, FR-313, FR-323) Pedir en `View/…` y `UIController/ControladorPygame.py`: mostrar el reporte de `resolubilidad()` **antes de la primera acción del jugador** (resoluble con su orden; no resoluble como advertencia con `--forzar`; completo si la partida no inicia; el mensaje si no concluyó), y el error con contexto de FR-323 si la partida no inicia por el esqueleto. Puede reutilizar `TextoResolubilidad.lineas_reporte` (FR-315). Es la excepción de 002 FR-217: el reporte no toca el mapa conocido. Cómo se dibuja lo decide el integrante 3. Comprobar con [quickstart.md](quickstart.md) §3, pasos 1 a 6.
- [ ] T056 Correr `python tests/correr_pruebas.py` y seguir [quickstart.md](quickstart.md) §3 junto con el integrante 3.

---

## Fase 8: Paquete de la Parte II (hallazgo H-3)

**Propósito**: que `--offline` tenga `llaves.json`, `costo` y `rango` reales. Depende de que el API publique las
criptas de la Parte II; no bloquea las fases anteriores (las pruebas usan paquetes temporales).

- [ ] T057 (FR-318) Cuando el API publique las criptas de la Parte II: **avisar antes a los integrantes 1 y 3** (cambia archivos que usan sus pruebas) y regenerar `paquete/` con `uv run python -m Data.DescargadorPaquete <id>` para cada cripta (`cripta-01` a `cripta-04` y las nuevas que se publiquen). Comprobar que cada carpeta trae `llaves.json`, que las salidas de `salas_p<N>.json` traen `costo` y que los cazadores de `catalogo.json` traen `rango` (001 FR-122). Correr `python tests/correr_pruebas.py` y el replay de `ejemplos/partida_ejemplo.log` con `--offline`; si alguna prueba de otro integrante cambia de resultado por los datos nuevos, avisarle antes de seguir. Commit **propio**, solo con `paquete/` (por ejemplo `datos: paquete de la Parte II con llaves.json, costos y rangos`), y avisar a los tres cuando esté subido.
- [ ] T058 (FR-306, FR-314, FR-318, SC-303, SC-308) Con el paquete regenerado: `uv run python main.py --verificar <id> --offline` para cada cripta del paquete. Ninguna debe terminar con código 1 (la 1 es para datos que faltan); cada una con 0 o 3 y el mismo texto que en línea con la misma versión (quickstart §2, pasos 1 a 4 y 7). Anotar el veredicto de cada cripta para `DECISIONES.md` (T064). Avisar al integrante 1 por si quiere repetir la T048 de la 001 con el paquete real.

---

## Fase 9: Bench B1 a B6 (NFR-301 a NFR-304, §5.4, §6.1, §6.3)

**Propósito**: evidencia de rendimiento con criptas sintéticas deterministas por semilla (Principio VIII) y, si el
paquete local trae criptas con `llaves.json`, con la cripta del paquete con más salas, leída sin red (NFR-301,
SC-306). `--bench` no inicia partidas, no crea `partida.log` ni llama a `ServicioResolubilidad` (FR-301): llama
directamente a `VerificadorResolubilidad`.

- [ ] T059 Agregar a `tests/test_resolubilidad_bench.py` (tamaños chicos; los umbrales de tiempo se leen en la tabla, no en pruebas): `test_nfr304_peine_es_determinista_por_semilla` (`cripta_en_peine(dientes, semilla)`), `test_nfr302_ingenua_da_el_mismo_orden_que_la_incremental` (B2, en cuadrículas resolubles y no resolubles), `test_r3_indice_lineal_da_el_mismo_indice` (B5), `test_r4_frontera_en_una_lista_da_el_mismo_resultado` (B6, en el peine), `test_nfr304_medir_devuelve_b1_a_b6` (`BenchResolubilidad.medir` con tamaños chicos devuelve `ResultadoBenchDTO` del subsistema «resolubilidad» con los casos B1 a B6), `test_nfr304_servicio_bench_incluye_resolubilidad_despues_de_logica` (la lista por defecto de `Service/ServicioBench.py` incluye `BenchResolubilidad.medir` **después** de `BenchLogica.medir`) y `test_nfr301_sc306_bench_mide_la_cripta_con_mas_salas_del_paquete` (con un paquete temporal de `paquete_temporal` con dos criptas de distinta cantidad de salas, las dos con `llaves.json`: la fila mide la de **más salas**, elegida por cantidad de salas y no por id, sin ninguna solicitud de red y sin crear `partida.log`; si el paquete no trae criptas con `llaves.json`, la fila no se agrega y la nota lo dice).
- [ ] T060 (NFR-301, NFR-302, NFR-303, NFR-304) En `Logic/BenchResolubilidad.py`, mediciones **B1** (verificación completa, resoluble), **B2** (alternativa descartada: repetir el recorrido completo desde `sala_inicial` cada vez que se obtienen llaves, con la misma preparación de `GrafoLlaves`; vive solo en el bench), **B3** (verificación completa, no resoluble: un ciclo de una llave y una cadena de unas K/2 dependientes) en las cuadrículas 10 × 10, 10 × 100 y 10 × 1 000 (100, 1 000 y 10 000 salas; 10, 100 y 1 000 llaves), y **B4** (desglose a 1 000 salas: preparación, recorrido, ciclos y armado). Reutiliza de `Logic/BenchLogica.py` solo `_cronometrar`, `_mejor_y_mediana` y `SEMILLA`, **sin modificarlo**. **Dependencia de la 001**: son nombres privados del integrante 1; él confirmó el 14/11 que no les cambia el nombre ni la firma sin avisar: si cambian, el integrante 1 avisa antes. La columna `nota` informa el factor de crecimiento respecto del tamaño anterior; B2 en 10 000 salas con **una sola repetición** y la nota «1 repetición».
- [ ] T061 (NFR-302, research R3 y R4) En `Logic/BenchResolubilidad.py`: el generador `cripta_en_peine(dientes, semilla)` (research R7: pasillo de `dientes` salas abiertas; de la sala *i* sale al sur una puerta a su diente que pide la llave *i*; la llave 0 en la sala inicial y la *i + 1* en el diente *i*; `llave_salida` en el último diente y `sala_salida` detrás de una puerta que la pide; orden de las ubicaciones mezclado con la semilla); **B5** (índice de llaves: ordenar y compactar frente a la búsqueda lineal de ids, que al final ordena los K ids y reescribe los índices) en las tres cuadrículas de B1, con la lineal en 10 000 salas con **una sola repetición**; **B6** (frontera agrupada por llave frente a una sola lista revisada entera al obtener cada llave) en peines de 100, 1 000 y 3 000 dientes, con la lista única en 3 000 con **una sola repetición**. Las variantes descartadas viven solo en el bench. `medir()` junta B1 a B6. Sin `dict` ni `sorted` también en el bench. Hace pasar T059 (salvo la de `ServicioBench`).
- [ ] T062 (NFR-301, NFR-304, SC-306) En `Service/ServicioBench.py` (integrante 2): importar `BenchResolubilidad` desde `Logic`, como ya importa `BenchLogica`, y agregar `BenchResolubilidad.medir` a la lista por defecto **después de `BenchLogica.medir`**. Sin import circular: `BenchResolubilidad` importa de `BenchLogica` solo `_cronometrar`, `_mejor_y_mediana` y `SEMILLA`, y ni `BenchLogica` ni `BenchRutas` importan `BenchResolubilidad` ni `ServicioBench`. `Logic/BenchLogica.py` no se toca. Además (FR-301, NFR-301, SC-306), si el paquete local trae criptas con `llaves.json` (lo que pasa al regenerarlo, T057), `ServicioBench` agrega una fila que mide la verificación de la **cripta con más salas del paquete**, elegida por cantidad de salas, sin nombrar ids (Principio VI) y leída sin red: Service orquesta `FuenteOffline`, `GestorEsqueleto`, `GestorLlaves` **sin almacén** y `VerificadorResolubilidad`, con el mismo cronómetro; no inicia partidas ni crea `partida.log`. `Logic/BenchResolubilidad` no lee Data. Si el paquete no trae criptas con `llaves.json`, la fila no se agrega y la nota lo dice; mientras tanto vale la sintética de 1 000 salas de B1. Hace pasar `test_nfr304_servicio_bench_incluye_resolubilidad_despues_de_logica` y `test_nfr301_sc306_bench_mide_la_cripta_con_mas_salas_del_paquete`.
- [ ] T063 Correr `uv run python main.py --bench` (o `python -m Service.ServicioBench`) y guardar la tabla en `specs/003-resolubilidad/bench-<fecha>.txt`, con la máquina y la versión de Python, como en la 001. Comprobar [quickstart.md](quickstart.md) §4: si el paquete local trae criptas con `llaves.json` (T057), la fila de la cripta con más salas del paquete tiene mediana < 200 ms (SC-306, NFR-301); si no, **B1** a 1 000 salas con mediana < 200 ms (SC-306, NFR-301), y la nota de la fila del paquete dice por qué no se agregó; de 1 000 a 10 000 salas B1 crece ≤ ×20 y B2 crece al menos el doble que B1 (SC-307); B3 crece como B1 (NFR-303); B5 y B6 muestran el crecimiento de su fila de research R7; dos corridas con la misma semilla generan las mismas criptas. Si B1 no baja de 200 ms, mirar B4 antes de cambiar el diseño (riesgo R-6) y, si hace falta ajustar un umbral, corregir primero la spec (Principio IX).

---

## Fase 10: Documentación y cierre

- [ ] T064 (NFR-301 a NFR-304, Principio VIII) En `DECISIONES.md` (raíz del repositorio), sección **«Integrante 2 — 002 y 003»** (hoy «(pendiente)»; las secciones de los integrantes 1 y 3 no se tocan), escribir el apartado **«§5.4 Resolubilidad»** a partir de research R0 a R9 y de los números de T063: por cada decisión (contrato y persistencia de las llaves; índice propio por ordenamiento y compactación; recorrido incremental por oleadas con la frontera agrupada por llave; orden determinista; puerta que bloquea según FR-310 y ciclos iterativos; dónde vive cada parte; nada en el historial ni en la línea), el problema, las alternativas con su complejidad, la decisión, la evidencia de B1 a B6 (enlace al archivo de T063) y si la decisión final coincide con la del plan. Incluir: la revisión de estructuras existentes (R0); la diferencia con el motor en la regla de la puerta de salida, **con un enlace** a «Diferencia conocida entre la verificación y el motor de P1» de la sección del integrante 1 (no se repite); y el **límite conocido en la otra dirección**: en una puerta con cierre automático y llaves distintas por cara, la verificación supone que la puerta puede volver a abrirse (§3.5) y **puede decir «resoluble» y el jugador quedar encerrado**, porque el motor la cierra en sus dos caras y volver pide la llave de la otra cara (decisión del grupo; spec, Suposiciones). Agregar los hallazgos H-2 (la solicitud de llaves gasta presupuesto en vivo y no en el replay) y H-3 (paquete) y los veredictos de T058. Dejar escrita también la **interpretación del Principio I** («Data solo conexión y formato»): comprobar que la sala de una ubicación existe en el esqueleto (FR-321) es integridad de los datos, no una regla del juego, y por eso va en Data (`validar_ubicaciones`), con el precedente de 001 FR-122, cuya validación de costos iguales en las dos caras ya vive en `GestorEsqueleto` (research R1).
- [ ] T065 [P] **(acordar con el equipo quién actualiza el README)** En `README.md`, documentar `--verificar <cripta>` (con y sin `--offline`; códigos 0 resoluble, 3 no resoluble, 1 no concluyó, 2 argumentos inválidos; el resultado va a la salida estándar) y `--forzar` (inicia una cripta no resoluble o cuya verificación no concluyó, con el reporte como advertencia; no permite jugar con un error de datos del esqueleto; no tiene efecto con `--verificar`, `--replay`, `--bench` ni al cargar), y que `--verificar` no se combina con `--replay` ni `--bench` (§7.2).
- [ ] T066 [P] En `specs/003-resolubilidad/spec.md`, tabla «Trazabilidad del Apéndice B», cambiar «Se define en `tasks.md`» por el nombre de cada prueba: caso 1 `test_h2_1_apendiceB_caso1_…` (T026), caso 2 `test_h1_4_apendiceB_caso2_…` (T020), caso 3 `test_h1_5_apendiceB_caso3_…` (T020) y caso 4 `test_h4_1_apendiceB_caso4_…` (T036). En un **commit `spec(003)` aparte**, separado del código (Principio IX).
- [ ] T067 Revisión de restricciones (Principio II): `grep -rnE "import copy|from copy|bisect|heapq|collections|networkx|\bsorted\(|\.sort\(|setrecursionlimit" Logic Estructuras DTO Service` no debe mostrar coincidencias nuevas en el código de esta feature; `grep -rnE "^(from|import) (Data|Service)" Logic` no debe mostrar nada nuevo; `grep -rn "config.offline\|\.offline" Service/ServicioResolubilidad.py Data/GestorLlaves.py` no debe mostrar nada; y `git diff` de la feature no toca los archivos de «No se tocan» (Reglas).
- [ ] T068 Correr `python tests/correr_pruebas.py` (todo en verde, sin regresiones en las pruebas de la primera parte ni de las features 001, 002 y 004) y el replay de ejemplo `uv run python main.py --replay ejemplos/partida_ejemplo.log --offline`, comparando su salida y su código con los de antes de la feature (no verifica ni cambia nada, FR-301). Seguir [quickstart.md](quickstart.md) de punta a punta (pruebas, `--verificar`, iniciar una partida con el integrante 3, `--bench`, determinismo) y comprobar la tabla de cobertura de abajo.
- [ ] T069 (Principio XI) Registrar en `PROMPTS_LLM.md` los prompts de esta feature. El archivo **no tiene secciones por integrante**: las entradas van **al final del archivo, en orden cronológico**, con el formato que ya usa (`**Fecha:**`, `**Herramienta:**`, el prompt textual, `**Uso de la respuesta:**` y la línea de guiones que separa las entradas), sin credenciales ni datos personales. Incluir el prompt de `/speckit-tasks`, el de `/speckit-analyze`, el de la corrección del análisis (parte A en `spec.md` y parte B en `tasks.md`, `plan.md`, `research.md` y `quickstart.md`) y cada prompt usado durante la implementación de la 003, con la fecha y para qué tarea.

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1 (preparación)**: T001 depende de T006 (`UbicacionLlaveDTO`, para `ubic` y `FuenteConLlaves`); sus ayudantes de notación se pueden escribir ya, y `paquete_temporal` sigue el formato del contrato de llaves sin esperar a T013. T001 tiene que estar antes de T009 y de las pruebas de las historias. T002 y T003 están hechas (confirmadas el 14/11) y no bloquean nada.
- **Fase 2 (base, contrato de llaves)**: T004 a T008 no dependen de T001; T009 en adelante usan los ayudantes de T001. Bloquea todas las historias. T008 (Swagger) bloquea T011.
- **Fase 3 (US1)**: depende de la fase 2. Es el MVP de Logic.
- **Fase 4 (US2)**: depende de la fase 3 (extiende `RecorridoLlaves` y `VerificadorResolubilidad`). T028 y T029 (pruebas) se escriben **antes** que el generador y fallan primero; T030 (generador) las hace pasar.
- **Fase 5 (servicio)**: depende de las fases 3 y 4 (el reporte completo de H4-1). Empieza con el **merge de `origin/kris`** (paso previo, sin número), que va antes de T037, T038 y T040. T037 y T038 (las escribe el integrante 2; las revisa el integrante 3) bloquean T039; T040 depende de T039. T041 (aviso) al terminar T039.
- **Fase 6 (US3)**: depende de la fase 5 (`ServicioResolubilidad.verificar`) y de T049 (la escribe el integrante 2; la revisa el integrante 3). T051 (aviso al integrante 1) al terminar T050.
- **Fase 7 (US4)**: depende de la fase 5, de T040 y de T047 (`config.forzar`). T054 la escribe el integrante 2 y la revisa el integrante 3; T055 (vista) es del integrante 3.
- **Revisión del integrante 3**: T037, T038, T040, T049 y T054 no se integran a `origin/derek` sin su revisión.
- **Fase 8 (paquete)**: depende de que el API publique la Parte II y de T013; T058 depende de T057 y de la fase 6. No bloquea las demás fases.
- **Fase 9 (bench)**: depende de las fases 3 y 4 (mide `VerificadorResolubilidad`) y de T030.
- **Fase 10 (cierre)**: depende de todo lo anterior. T064 usa los números de T063 y los veredictos de T058 (si el paquete ya está). T066 depende de que existan los nombres de las pruebas.

### Fuera de esta feature (no son tareas de la 003)

- **T055 de la 001** ([specs/001-terreno-cazador/tasks.md](../001-terreno-cazador/tasks.md), integrante 2; no es la T055 (vista) de esta feature): validación de `cierre_automatico` y de la `duracion` de `ObjetoDTO` en Data. **Se hace antes que esta feature.** Con ella, un `cierre_automatico` inválido en el esqueleto es un error de datos que `GestorEsqueleto.cargar` lanza antes del paso de llaves, y la 003 lo trata como FR-323 (`--verificar` → código 1; la partida no inicia ni con `--forzar`) sin código nuevo, porque ya propaga los `ErrorDatos` del esqueleto (T039). **Sí lleva prueba en la 003**: `test_fr323_fr314_cierre_automatico_invalido_codigo_1` (T045) y `test_fr323_cierre_automatico_invalido_no_inicia_ni_con_forzar` (T036), que dependen de la T055 de la 001.
- **T071 de la 004** ([specs/004-linea-tiempo/tasks.md](../004-linea-tiempo/tasks.md), integrante 2): «ir a» registra la orden como un comentario `# ir a <sala>` en `partida.log`, y **`BitacoraReplayIO.leer` debe ignorar esas líneas** (las que empiezan por `# ir a`, en la sección de acciones), **sin confundirlas con el encabezado `#CRIPTA-REPLAY` ni con `#ACCIONES`**, y reproducirlas sin cambiar el resultado. No afecta a la 003 (`--replay` no verifica), pero el replay de ejemplo de T068 debe seguir pasando cuando se agregue.

### Dentro de cada historia

- Las pruebas primero, y deben fallar.
- DTO y Data antes que Logic; Logic antes que Service; Service antes que la línea de comandos y la interfaz.
- Las tareas **(coordinar con el integrante 3)** que escribe el integrante 2 (T037, T038, T040, T049, T054) llevan su prueba primero, como las demás, y pasan por la revisión del integrante 3 antes del merge; T055 (vista) se le pide al integrante 3 apenas esté T054.
- Correr todas las pruebas al final de cada fase.

### Grafo de dependencias

```text
T002 [x] (integ. 3: contrato del reporte confirmado el 14/11) ─► (no bloquea)
T003 [x] (integ. 1: Mazmorra, sin cambios, confirmado el 14/11) ─► (no bloquea; T022 la usa)
T004 ─► T006 ─► T001 (ayudantes; paquete_temporal con el formato del contrato, sin esperar a T013) ─► T009 y las pruebas de las historias
T005 ─► T007
T008 ─► T011
T009 ─► T010 ─► T011 ─► T012, T013 ─► T014 ─► T015 ─► T016 ─► T017 ─► T018 ─► T019 (fase 2)

Fase 2 ─► US1: T020, T021 ─► T022 ─► T023 ─► T024 ─► T025 (fase 3)
Fase 3 ─► US2: T026, T027, T028, T029 ─► T030 ─► T031 ─► T032 ─► T033 ─► T034 (fase 4)
Fases 3 y 4 ─► merge de origin/kris (paso previo) ─► T035, T036 ─► T037, T038 (integ. 2, revisa integ. 3) ─► T039 ─► T040 (integ. 2, revisa integ. 3) ─► T041 (aviso) ─► T042
          US3: T043–T046 ─► T047, T048 (TextoResolubilidad), T049 (integ. 2, revisa integ. 3) ─► T050 ─► T051 (aviso integ. 1) ─► T052
          US4: T053 ─► T054 (integ. 2, revisa integ. 3), T055 (vista, integ. 3) ─► T056
T055 de la 001 (integ. 2, antes de esta feature) ─► pruebas de cierre_automatico de T036 y T045
          Paquete (cuando publique el API): T057 (avisar a los tres, commit propio) ─► T058
          Bench: T059 ─► T060 ─► T061 ─► T062 ─► T063
          Cierre: T064 (usa T063 y T058) ─► T065, T066 ─► T067 ─► T068 ─► T069
```

## Oportunidades de paralelismo

- **Fase 1**: T002 y T003 ya están hechas; T001 (sus ayudantes de notación) puede empezar ya.
- **Fase 2**: T004 y T005 a la vez (archivos de prueba distintos); luego T006 y T007 a la vez; T012 y T013 a la vez después de T011.
- **Fase 4**: T028 (archivo del bench) a la vez que T026 y T027.
- **Fase 5**: T037 y T038 cambian archivos distintos, pero sus pruebas van en el mismo archivo que T035 y T036, así que no son paralelas; van después del merge de `origin/kris`.
- **Fase 6**: T048 (`TextoResolubilidad`) a la vez que T047 y que T049.
- **Fase 8** puede ocurrir en cualquier momento después de T013, en cuanto el API publique.
- **Fase 9** puede empezar después de la fase 4, en paralelo con las fases 5 a 7 (otros archivos).
- **Fase 10**: T065 y T066 a la vez.
- **No** son paralelas entre sí las tareas que escriben el mismo archivo: `tests/test_resolubilidad_datos.py` (T004, T009, T014, T016), `tests/test_resolubilidad_reporte.py` (T005, T026, T027, T029), `tests/test_resolubilidad_logica.py` (T020, T021), `tests/test_resolubilidad_servicio.py` (T035, T036, T037, T038, T040), `UIController/ControladorBackend.py` (T049, T054), `tests/test_resolubilidad_cli.py` (T043 a T046, T053), `tests/test_resolubilidad_bench.py` (T028, T059), `Logic/RecorridoLlaves.py` (T023, T031), `Logic/VerificadorResolubilidad.py` (T024, T033) y `Logic/BenchResolubilidad.py` (T030, T060, T061).

### Ejemplo de paralelismo: base

```text
Tarea: "Escribir las pruebas de UbicacionLlaveDTO en tests/test_resolubilidad_datos.py"   (T004)
Tarea: "Escribir las pruebas del DTO del reporte en tests/test_resolubilidad_reporte.py"  (T005)
# luego:
Tarea: "Crear DTO/UbicacionLlaveDTO.py"                                                   (T006)
Tarea: "Crear DTO/ReporteResolubilidadDTO.py"                                             (T007)
```

### Ejemplo de paralelismo: historia 2 y bench

```text
Tarea: "Escenarios de no obtenibles y frontera en tests/test_resolubilidad_reporte.py"    (T026)
Tarea: "Pruebas del generador en tests/test_resolubilidad_bench.py"                        (T028)
```

---

## Estrategia de implementación

### Primero el MVP (historia 1)

1. Fases 1 y 2: ayudantes, contrato de llaves y DTO del reporte (entrega atrasada al integrante 3).
2. Fase 3: `GrafoLlaves`, `RecorridoLlaves` y `VerificadorResolubilidad` (veredicto y orden).
3. **Parar y validar**: `python tests/correr_pruebas.py` y los casos 2 y 3 del Apéndice B.

### Entrega incremental

1. + Historia 2: reporte completo, frontera, ciclos iterativos y dependientes (caso 1 del Apéndice B).
2. + Servicio: merge de `origin/kris`; `ServicioResolubilidad` con `ErrorPartidaNoIniciada` (caso 4), con T037, T038 y T040, que escribe el integrante 2 y revisa el integrante 3; avisarle (T041).
3. + Historia 3: `--verificar` y `--forzar` en la línea de comandos, con códigos 0, 3 y 1 (T049 también la revisa el integrante 3); avisar al integrante 1 (T051).
4. + Historia 4: `ControladorBackend.iniciar` con la verificación (T054, la revisa el integrante 3) y el reporte al iniciar en la ventana (T055 (vista), integrante 3).
5. + Paquete de la Parte II cuando el API lo publique (commit propio, avisando a los tres).
6. + Bench B1 a B6, `DECISIONES.md` §5.4, README y trazabilidad.

Cada paso deja todas las pruebas en verde.

### Commits sugeridos (los hace el integrante 2)

Uno por fase o por grupo lógico, por ejemplo: `feat(003): contrato de llaves (DTO, fuentes, almacén y gestor)`,
`feat(003): verificación de resolubilidad en Logic (veredicto y orden)`, `feat(003): reporte, frontera y ciclos`,
`feat(003): ServicioResolubilidad`, `feat(003): --verificar y --forzar`, `bench(003): B1 a B6`,
`datos: paquete de la Parte II` (T057, solo `paquete/`), `spec(003): nombres de las pruebas en la trazabilidad`
(T066, siempre aparte del código) y `docs(003): DECISIONES.md §5.4 y README`. Los cambios a `ServicioPartida`,
`ContextoPartida`, `ErroresServicio` y `ControladorBackend` (T037, T038, T040, T049, T054) **los commitea el
integrante 2** en commits propios (por ejemplo `feat(003): ServicioPartida y ContextoPartida para la verificación`
y `feat(003): ControladorBackend con verificar y resolubilidad`), y **los revisa el integrante 3 antes del merge**;
el merge de `origin/kris` del paso previo de la fase 5 va en su propio commit de merge. La vista (T055 (vista)) la
commitea el integrante 3.

---

## Cobertura: escenarios, casos del Apéndice B y decisiones sin escenario

| Escenario / caso | Prueba | Tarea | FR |
|---|---|---|---|
| H1-1 | `test_h1_1_fr301_fr304_fr305_unica_puerta_cerrada_es_la_de_salida` | T020 | FR-301, FR-304, FR-305 |
| H1-2 | `test_h1_2_fr304_fr322_sin_puertas_cerradas_no_resoluble_con_motivo` | T020 | FR-304, FR-322 |
| H1-3 | `test_h1_3_fr304_fr305_cadena_a_b_llave_salida` | T020 | FR-304, FR-305 |
| H1-4 (Apéndice B, caso 2) | `test_h1_4_apendiceB_caso2_fr303_fr316_llave_de_enemigo_errante` | T020 | FR-303, FR-316 |
| H1-5 (Apéndice B, caso 3) | `test_h1_5_apendiceB_caso3_fr305_fr306_mismo_orden_en_dos_ejecuciones` y `test_sc303_diez_ejecuciones_en_procesos_separados` | T020, T046 | FR-305, FR-306 |
| H1-6 | `test_h1_6_fr302_enemigo_trampa_cierre_y_costo_no_bloquean` | T020 | FR-302 |
| H1-7 | `test_h1_7_fr302_las_llaves_no_se_consumen` | T020 | FR-302 |
| H1-8 | `test_h1_8_fr301_no_descarga_contenido_ni_consume_azar` | T035 | FR-301 |
| H1-9 | `test_h1_9_fr313_reporte_en_el_contexto_antes_de_la_primera_accion`, `test_fr313_controlador_resoluble_muestra_el_orden` y la vista (T055 (vista), integrante 3) | T035, T053, T055 (vista) | FR-313 |
| H1-10 | `test_h1_10_fr302_fr305_llave_declarada_en_una_sola_cara` | T020 | FR-302, FR-305 |
| H1-11 | `test_h1_11_fr316_fr305_copia_alcanzable_de_la_llave` | T020 | FR-316, FR-305 |
| H1-12 | `test_h1_12_fr316_fr309_fr306_ubicaciones_identicas_una_sola_vez` | T026 | FR-316, FR-309, FR-306 |
| H2-1 (Apéndice B, caso 1) | `test_h2_1_apendiceB_caso1_fr304_fr307_fr308_fr309_fr310_llave_salida_detras_de_su_puerta` | T026 | FR-304, FR-307 a FR-310 |
| H2-2 | `test_h2_2_fr307_fr310_ciclo_de_dos_llaves` | T027 | FR-307, FR-310 |
| H2-3 | `test_h2_3_fr306_fr310_reporte_identico_en_cada_ejecucion` | T027 | FR-306, FR-310 |
| H2-4 | `test_h2_4_fr307_fr309_fr310_dependiente_del_ciclo` | T027 | FR-307, FR-309, FR-310 |
| H2-5 | `test_h2_5_fr307_fr308_frontera_sin_repetir` | T026 | FR-307, FR-308 |
| H2-6 | `test_h2_6_fr307_fr308_fr309_fr321_llave_sin_ubicacion` | T026 | FR-307, FR-308, FR-309, FR-321 |
| H2-7 | `test_h2_7_fr321_fr320_sala_inexistente_es_error_de_datos`, `test_h2_7_fr320_fr321_sala_inexistente_inicia_solo_con_forzar` y `test_h2_7_fr321_fr314_verificar_sala_inexistente_codigo_1` | T016, T036, T045 | FR-314, FR-320, FR-321 |
| H2-8 | `test_h2_8_fr321_fr301_enemigo_inexistente_no_se_valida` y `test_h2_8_fr301_fr303_fr321_iniciar_sin_descargar_contenido` | T016, T035 | FR-301, FR-303, FR-321 |
| H2-9 | `test_h2_9_fr302_fr308_llaves_distintas_por_cara` | T026 | FR-302, FR-308 |
| H2-10 | `test_h2_10_fr302_fr308_cara_cerrada_sin_llave` | T026 | FR-302, FR-308 |
| H2-11 | `test_h2_11_fr308_salida_sin_vuelta_hacia_la_region_no_es_frontera` | T026 | FR-308 |
| H2-12 | `test_h2_12_fr307_fr310_fr306_dos_ciclos_independientes` | T027 | FR-306, FR-307, FR-310 |
| H2-13 | `test_h2_13_fr306_fr307_fr308_fr310_puerta_que_bloquea` | T027 | FR-306, FR-307, FR-308, FR-310 |
| H3-1 | `test_h3_1_fr314_fr315_verificar_resoluble_codigo_0` | T045 | FR-314, FR-315 |
| H3-2 | `test_h3_2_fr314_fr315_verificar_no_resoluble_codigo_3` | T045 | FR-314, FR-315 |
| H3-3 | `test_h3_3_fr314_fr318_fr306_verificar_offline_igual_que_en_linea` (y T058 con el paquete real) | T045, T058 | FR-306, FR-314, FR-318 |
| H3-4 | `test_h3_4_fr317_solicitud_de_llaves_cuenta_y_se_persiste` | T016 | FR-317 |
| H3-5 | `test_h3_5_fr317_no_repite_la_solicitud` | T016 | FR-317 |
| H3-6 | `test_h3_6_fr319_datos_de_la_primera_parte_se_invalidan` | T016 | FR-319 |
| H3-7 | `test_h3_7_fr320_no_se_pudo_obtener_la_ubicacion` y `test_h3_7_fr320_fr314_verificar_sin_llaves_codigo_1` | T016, T045 | FR-314, FR-320 |
| H3-8 | `test_h3_8_fr323_fr314_costo_cero_codigo_1` | T045 | FR-314, FR-323 |
| H3-9 | `test_h3_9_fr314_forzar_no_cambia_verificar` | T045 | FR-314 |
| H4-1 (Apéndice B, caso 4) | `test_h4_1_apendiceB_caso4_fr311_no_resoluble_no_inicia` y `test_fr311_controlador_no_inicia_y_guarda_el_reporte` | T036, T053 | FR-311 |
| H4-2 | `test_h4_2_fr312_fr313_forzar_inicia_con_advertencia` y `test_fr312_fr313_controlador_inicia_con_forzar` | T036, T053 | FR-312, FR-313 |
| H4-3 | `test_h4_3_fr312_forzar_con_resoluble_no_cambia_nada` | T036 | FR-312 |
| H4-4 | `test_h4_4_fr301_fr313_cargar_y_replay_no_verifican` y `test_fr301_controlador_resolubilidad_none_al_cargar_y_en_replay` | T036, T053 | FR-301, FR-313 |
| H4-5 | `test_h4_5_fr323_costos_distintos_no_inicia_ni_con_forzar` | T036 | FR-323 |

| Decisión sin escenario propio | Prueba | Tarea | FR |
|---|---|---|---|
| `--forzar` sin efecto con `--replay` | `test_fr312_forzar_con_replay_sin_efecto` | T046 | FR-312 |
| `--forzar` sin efecto con `--bench` | `test_fr312_forzar_con_bench_sin_efecto` | T046 | FR-312 |
| `--forzar` sin efecto al cargar | `test_fr312_forzar_al_cargar_sin_efecto` | T036 | FR-312 |
| `--verificar` con una cripta inexistente → código 1 | `test_fr314_verificar_cripta_inexistente_codigo_1` y `test_fr314_verificar_cripta_inexistente_no_concluyo` | T046, T036 | FR-314 |
| Cadena de más de 1 000 dependientes sin `RecursionError` | `test_fr310_cadena_de_mas_de_1000_dependientes_sin_recursion` | T029 | FR-310 |
| Casos borde de la puerta de salida (H-1) | `test_fr304_…` y `test_fr304_fr322_puerta_con_llave_salida_que_no_lleva_a_sala_salida` | T021 | FR-304, FR-322 |
| Cierre automático con llaves distintas por cara | `test_fr302_cierre_automatico_con_llaves_distintas_por_cara_no_bloquea` | T021 | FR-302 |
| `cierre_automatico` inválido en el esqueleto (001 FR-122, depende de T055 de la 001) | `test_fr323_fr314_cierre_automatico_invalido_codigo_1` y `test_fr323_cierre_automatico_invalido_no_inicia_ni_con_forzar` | T045, T036 | FR-314, FR-323 |
| Salida de `--verificar` en UTF-8 sin `PYTHONIOENCODING` | `test_fr314_verificar_utf8_sin_pythonioencoding` | T046 | FR-314 |
| Nada en el historial, la línea ni el log (R9) | `test_r9_fr301_verificacion_no_registra_en_historial_linea_ni_log` | T035 | FR-301 |

| Criterio | Dónde se verifica |
|---|---|
| SC-301 | Los cuatro casos del Apéndice B: T020, T026, T036 |
| SC-302 | Esta tabla de cobertura (T068) |
| SC-303 | `test_sc303_diez_ejecuciones_en_procesos_separados` (T046) |
| SC-304 | `test_sc304_orden_valido_en_todas_las_criptas_resolubles` (T021) |
| SC-305 | `test_sc305_reporte_completo_en_todas_las_no_resolubles` (T027) |
| SC-306 | La fila de la cripta con más salas del paquete (T062, T063), cuando el paquete de la Parte II está regenerado (T057); mientras tanto, B1 a 1 000 salas en la tabla de T063. `test_nfr301_sc306_bench_mide_la_cripta_con_mas_salas_del_paquete` (T059) |
| SC-307 | B1 y B2 de 1 000 a 10 000 salas en la tabla de T063 |
| SC-308 | `test_sc308_verificar_sin_vista`, `test_sc308_verificar_offline_sin_solicitudes_de_red` y los códigos de T045 y T046 |

| NFR | Dónde se verifica |
|---|---|
| NFR-301 | La fila de la cripta con más salas del paquete (T062, T063) cuando existe; mientras tanto, B1 a 1 000 salas (T060, T063); `test_nfr301_sc306_bench_mide_la_cripta_con_mas_salas_del_paquete` (T059) y `DECISIONES.md` (T064) |
| NFR-302 | B1 frente a B2, B5 y B6 (T060, T061, T063); `test_nfr302_ingenua_da_el_mismo_orden_que_la_incremental` (T059) |
| NFR-303 | B3 (T060, T063); `test_nfr303_cuadricula_no_resoluble_un_ciclo_y_una_cadena` (T028) |
| NFR-304 | T028, T030, T059 a T063 |
