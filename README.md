# Crypta

**Intergantes:**
- Kristel Peraza Sánchez
- Derek García Herra
- Marco Cabrera Mora

Juego de exploración por eventos para el Primer Proyecto de Estructuras de Datos (UNA, II ciclo 2026).
El cliente obtiene la cripta desde el servicio web (o desde un paquete local con `--offline`), simula la partida
con un reloj virtual y guarda partidas, puntajes y bitácoras de replay en disco.

## Requisitos

- **Python 3.11 o superior** (lo exige `pyproject.toml`; probado con 3.11 y 3.14).
- Dependencias:
  - `requests`: acceso al servicio web (`Data/ClienteHttp.py`).
  - `pygame-ce`: interfaz gráfica (solo para jugar; `--replay` y `--bench` no lo necesitan).
  - Ambas están en `requirements.txt` (y en `pyproject.toml`).
- **No hace falta `uv`**: es opcional. Solo se necesita Python y `pip`, que vienen con Python.

## Instalación

Desde la raíz del proyecto (la carpeta donde está `main.py`). Se crea un entorno virtual `.venv` y se instalan las dos
dependencias. **No hace falta activar el entorno**: los comandos de este README llaman directamente al Python del entorno
(así tampoco molesta la política de scripts de PowerShell).

**Windows (PowerShell)**

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Linux / macOS**

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Para comprobar que quedó bien (debe mostrar las opciones y no dar error):

| Windows (PowerShell) | Linux / macOS |
|---|---|
| `.venv\Scripts\python.exe main.py --ayuda` | `.venv/bin/python main.py --ayuda` |

**Alternativa con uv** (opcional; instala las mismas versiones de `uv.lock`): `uv sync`, y después cada comando de abajo
se escribe como `uv run python main.py ...`.

### Si algo falla

- *`python` no se reconoce* (Windows): prueba `py -m venv .venv`, o instala Python 3.11 o superior desde python.org
  marcando "Add python.exe to PATH".
- *`uv` no se reconoce*: no se necesita. Usa los comandos de Windows o de Linux / macOS de este README.
- *PowerShell no deja activar el entorno*: no hace falta activarlo; usa `.venv\Scripts\python.exe`.
- Si ya activaste el entorno (`.venv\Scripts\Activate.ps1` o `source .venv/bin/activate`), basta con escribir
  `python main.py ...` en lugar de la ruta completa.

## Cómo ejecutar

| Qué hace | Windows (PowerShell) | Linux / macOS |
|---|---|---|
| Abre el juego conectado al servicio web. | `.venv\Scripts\python.exe main.py` | `.venv/bin/python main.py` |
| Abre el juego con el paquete local de `paquete/`, sin usar la red. | `.venv\Scripts\python.exe main.py --offline` | `.venv/bin/python main.py --offline` |
| Cambia el tope de fichas del catálogo en memoria (entero mayor o igual a 1; por defecto 25). Se puede combinar con los demás modos. | `.venv\Scripts\python.exe main.py --cache-size 10` | `.venv/bin/python main.py --cache-size 10` |
| Reproduce una partida desde su bitácora, sin abrir la ventana, y muestra cada acción y el resultado final. | `.venv\Scripts\python.exe main.py --replay logs/partida_001.log --offline` | `.venv/bin/python main.py --replay logs/partida_001.log --offline` |
| Corre las mediciones de rendimiento con cargas sintéticas, sin abrir la ventana, y muestra una tabla por subsistema. | `.venv\Scripts\python.exe main.py --bench` | `.venv/bin/python main.py --bench` |
| Muestra las opciones. | `.venv\Scripts\python.exe main.py --ayuda` | `.venv/bin/python main.py --ayuda` |

`--replay` y `--bench` no se pueden usar juntos. Con uv, cada comando se escribe `uv run python main.py ...`.

**Sobre `--replay`:** `logs/` está vacía en una copia nueva del repositorio (se llena al jugar). Para probarlo sin jugar
antes, el repositorio incluye una partida de muestra hecha con el paquete local:
`... main.py --replay ejemplos/partida_ejemplo.log --offline`. Sin `--offline`, el replay pide la cripta al servicio web
(y cuenta como solicitudes de red); con `--offline` la lee de `paquete/`.

**Nota sobre `--bench`:** la tabla es larga. La terminal integrada de PyCharm puede no mostrarla completa; en una terminal
normal sale entera. Para guardarla en un archivo:

| Windows (PowerShell) | Linux / macOS |
|---|---|
| `.venv\Scripts\python.exe main.py --bench \| Out-File -Encoding utf8 bench.txt` | `.venv/bin/python main.py --bench > bench.txt` |

### Controles

En los menús: flechas o ratón para elegir, `Enter` o clic para aceptar, `Esc` para volver.

Durante la partida (el inventario está siempre visible; la ventana muestra este resumen abajo a la derecha):

| Acción | Teclado | Ratón |
|---|---|---|
| Moverse | `W A S D` o flechas | |
| Atacar | `Espacio` (ataca al enemigo resaltado) | clic sobre el enemigo |
| Recoger | | clic sobre el objeto del suelo |
| Abrir una puerta | `E` | clic sobre la puerta cerrada |
| Esperar | `Z` | botón `Esperar` |
| Recorrer el inventario | `Tab` (`Mayús + Tab` hacia atrás) | rueda, o clic en una casilla |
| Usar | `U` | doble clic sobre la casilla |
| Equipar | `Q` | clic derecho sobre la casilla |
| Soltar | `G` | `Mayús` + clic sobre la casilla |
| Cambiar la vista del inventario | `V` (real, peso, valor, nombre; el orden real no cambia) | |
| Pergamino de retroceso | `Retroceso` o `Ctrl + Z` | |
| Guardar / Cargar | `Ctrl + S` o `F5` / `Ctrl + L` o `F9` | botones de la pausa |
| Pausa | `Esc` (Continuar, Guardar, Cargar, Salir al menú) | |

Para salir: `Salir` en el menú principal, `Salir al menú` en la pausa, o cerrar la ventana.

### Modo `--offline`

Lee las criptas desde la carpeta `paquete/`, que viene en el repositorio con las cuatro publicadas al 18 de octubre
(`cripta-01` a `cripta-04`, de 6 a 50 salas). Las lecturas locales no cuentan como solicitudes de red, así que el
reporte final muestra 0 solicitudes.

Para agregar o actualizar una cripta en el paquete (esto sí usa la red; el catálogo se comparte entre criptas y se
completa con las fichas nuevas):

```
.venv\Scripts\python.exe -m Data.DescargadorPaquete <id-de-la-cripta>        (Windows)
.venv/bin/python -m Data.DescargadorPaquete <id-de-la-cripta>             (Linux / macOS)
```

### Modo `--replay`

Cada partida escribe su bitácora en `logs/` mientras se juega: un encabezado (cripta, versión de la cripta,
versión del catálogo y semilla) y una línea por cada acción del jugador. `--replay` vuelve a ejecutar esas acciones
con la misma semilla y llega al mismo resultado. Si la versión de la cripta o del catálogo no coincide con la
disponible, se informa la incompatibilidad y no se reproduce. Si la última línea quedó a medio escribir (por
ejemplo, porque el programa se cerró), se ignora y se avisa.

Al cargar una partida guardada, la bitácora continúa en un archivo nuevo que incluye las acciones anteriores,
así que ese log también se puede reproducir completo.

## Archivos que genera el programa

Ninguna de estas carpetas se sube al repositorio (están en `.gitignore`). Se crean solas al usarse.

| Ubicación | Contenido |
|---|---|
| `cache/catalogo/` | Caché del catálogo en disco: una ficha por archivo, dentro de una carpeta por versión del catálogo. Cuando el catálogo cambia de versión, la anterior se borra. |
| `saves/partida.sav` | La partida guardada (formato binario propio). |
| `saves/puntajes.jsonl` | Los puntajes: una línea por partida terminada. |
| `logs/partida_NNN.log` | Bitácora de cada partida para `--replay` (`partida_001.log`, `partida_002.log`, ...). |
| `saves/bench_tmp/` | Archivos temporales de `--bench`; se borran al terminar. |

## Pruebas

Para correr todas de una vez (no abre ventanas; termina con código 0 si todo pasa):

```
.venv\Scripts\python.exe tests/correr_pruebas.py        (Windows)
.venv/bin/python tests/correr_pruebas.py             (Linux / macOS)
```

Hay dos tipos de pruebas, y el script corre los dos:

- **De `unittest`** (`tests/Test*.py` y algunos `tests/test_*.py`):
  `.venv\Scripts\python.exe -m unittest discover -s tests -p "[Tt]est*.py"` (en Linux / macOS, `.venv/bin/python ...`).
- **Scripts `probar_*`** (el resto de `tests/test_*.py`: Servicios, controladores, Vista...). `unittest discover` no los
  encuentra; cada uno se corre por separado y termina con una línea `OK: ...`, por ejemplo
  `.venv\Scripts\python.exe tests/test_servicios.py`.

Las pruebas de la Vista necesitan `pygame-ce`. Los scripts `tests/capturar_*.py` no son pruebas: guardan capturas de
pantalla en `capturas/` para revisarlas a ojo.

## Documentación

- `PROMPTS_LLM.md`: bitácora de uso de modelos de lenguaje.