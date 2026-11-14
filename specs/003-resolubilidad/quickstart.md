# Guía rápida de validación: Verificación de resolubilidad

**Feature**: `003-resolubilidad` · **Plan**: [plan.md](plan.md)

Cómo comprobar de punta a punta que la feature funciona. Los detalles de datos están en
[contrato-llaves.md](contracts/contrato-llaves.md) y [contrato-reporte-resolubilidad.md](contracts/contrato-reporte-resolubilidad.md);
las estructuras, en [data-model.md](data-model.md).

## Requisitos previos

- Python 3.11 o superior con las dependencias del proyecto (`uv sync`).
- Desde la raíz del repositorio. En PowerShell, el código de salida se lee con `$LASTEXITCODE`.
- Para las pruebas con paquete: **regenerar el paquete** con las versiones de la Parte II (el actual es de la primera
  parte y no trae `llaves.json`; research, hallazgo H-3):

```powershell
uv run python -m Data.DescargadorPaquete cripta-01
```

## 1. Pruebas automatizadas

```powershell
uv run python -m unittest tests.test_resolubilidad_logica tests.test_resolubilidad_reporte -v
uv run python -m unittest tests.test_resolubilidad_datos tests.test_resolubilidad_servicio -v
uv run python -m unittest tests.test_resolubilidad_cli tests.test_resolubilidad_bench -v
uv run python tests/correr_pruebas.py
```

Esperado: todo pasa; cada prueba cita su FR (Principio X). Los cuatro casos del Apéndice B están en
`test_resolubilidad_reporte` (caso 1, H2-1), `test_resolubilidad_logica` (casos 2 y 3, H1-4 y H1-5) y
`test_resolubilidad_servicio` (caso 4, H4-1) (SC-301).

## 2. `--verificar` sin vista (historia 3)

| Paso | Comando | Esperado |
|---|---|---|
| 1 | `uv run python main.py --verificar cripta-01 --offline` | Con el paquete regenerado: el reporte y código 0 o 3. Con el paquete actual: «la verificación NO CONCLUYÓ … falta el archivo … llaves.json» y código **1** (FR-320) |
| 2 | `uv run python main.py --verificar cripta-01` | Mismo resultado que el paso 1 si la versión coincide (FR-306); hace la solicitud de llaves (FR-317) |
| 3 | Repetir el paso 2 | No repite la solicitud de llaves: queda en `cache/llaves/cripta-01.json` (FR-317, H3-5) |
| 4 | `uv run python main.py --verificar cripta-01 --forzar` | Mismo resultado y código que el paso 2 (H3-9) |
| 5 | `uv run python main.py --verificar` | Error de uso, código 2 |
| 6 | `uv run python main.py --verificar cripta-01 --replay x.log` | Error de uso (grupo excluyente), código 2 |
| 7 | `uv run python main.py --verificar cripta-01 --offline > reporte.txt` | El reporte completo queda en `reporte.txt`: se escribe en la salida estándar (FR-314) |
| 8 | `uv run python main.py --verificar cripta-que-no-existe` | «la verificación NO CONCLUYÓ» con el error del servicio (404) y código **1**, sin caerse (FR-314) |
| 9 | `uv run python main.py --verificar cripta-que-no-existe --offline --forzar` | «la verificación NO CONCLUYÓ» (falta la cripta en el paquete) y código **1**: `--forzar` no cambia nada (FR-314) |
| 10 | `uv run python main.py --bench --forzar` | Las mismas filas que sin `--forzar` y el mismo código; no es error de uso (FR-312) |

En ningún caso se abre una ventana ni se crea `partida.log` (FR-314, SC-308). Es el único modo sin vista que verifica:
`--replay` y `--bench` no lo hacen (FR-301, FR-313).

**Caso de la diferencia con el motor** (Sesión 2026-11-13 de la spec; research, H-1): con una cripta de prueba donde
la única puerta que pide `llave_salida` no lleva a `sala_salida`, `--verificar` da «NO RESOLUBLE» con el motivo de
FR-322 y código 3, aunque el motor de la primera parte permitiría ganar. Es lo esperado: lo cubre
`test_resolubilidad_logica` y la diferencia está registrada en `DECISIONES.md`.

## 3. Iniciar una partida (historias 1 y 4)

| Paso | Qué hacer | Esperado |
|---|---|---|
| 1 | Iniciar una partida normal con una cripta resoluble | Antes de la primera acción del jugador se ve «resoluble» y el orden de llaves (FR-313) |
| 2 | Iniciar con una cripta no resoluble, sin `--forzar` | No inicia; se ve el reporte completo; no hay `partida.log` nuevo en `logs/` (FR-311) |
| 3 | Lo mismo con `uv run python main.py --forzar` | Inicia; el reporte se ve como advertencia (FR-312) |
| 4 | Guardar esa partida y cargarla sin `--forzar`; reproducir su log con `--replay` | No se verifica ni se muestra el reporte (FR-301) |
| 5 | Cargar la misma partida con `--forzar`; `uv run python main.py --replay logs/<log> --forzar` | Lo mismo que en el paso 4: `--forzar` se acepta y no tiene efecto (FR-312) |
| 6 | Iniciar con una cripta no resoluble cuyas llaves tienen ubicaciones idénticas repetidas | En el reporte, cada ubicación idéntica aparece una sola vez (FR-309) |

Las criptas no resolubles de prueba se arman en `tests/ayudas_resolubilidad.py`; en la ventana se validan con una
cripta publicada no resoluble o con un paquete temporal.

## 4. `--bench` (NFR-301, NFR-304)

```powershell
uv run python main.py --bench
```

`--bench` no inicia partidas ni verifica una cripta publicada (FR-301): no hace solicitudes para esta medición. Las
filas de resolubilidad las agrega `Logic/BenchResolubilidad.py`, que `Service/ServicioBench.py` llama después de
`BenchLogica.medir`. Buscar las filas del subsistema «resolubilidad»:

- **B1** (incremental, resoluble) con 1 000 salas: mediana **< 200 ms** (SC-306).
- **B1**: la nota de 10 000 salas indica un crecimiento **≤ ×20** respecto de 1 000 (SC-307).
- **B2** (repetir el recorrido por llave): su crecimiento es **al menos el doble** que el de B1 (SC-307).
- **B3** (no resoluble: un ciclo de una llave y una cadena larga de dependientes) crece como B1: el reporte sale del
  mismo recorrido (NFR-303).
- **B5** (índice de llaves): la búsqueda lineal crece mucho más que ordenar y compactar (R3).
- **B6** (peine): la frontera en una sola lista crece mucho más que la agrupada por llave (R4).
- Dos corridas con la misma semilla generan las mismas criptas (Principio VIII).

Los números se copian a `DECISIONES.md` (Principio VIII).

## 5. Determinismo (SC-303)

`tests/test_resolubilidad_cli.py` ejecuta la verificación de cada cripta de prueba 10 veces, en procesos separados,
en línea (fuente falsa) y con `--offline` (paquete temporal), y compara el texto completo de las 10 salidas.
