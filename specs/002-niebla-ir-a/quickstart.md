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
