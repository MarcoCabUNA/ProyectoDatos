# Cripta

Juego de exploración por eventos para el Primer Proyecto de Estructuras de Datos II (UNA, II ciclo 2026).
El cliente obtiene la cripta desde el servicio web (o desde un paquete local con `--offline`), simula la partida
con un reloj virtual y guarda partidas, puntajes y bitácoras de replay en disco.

## Requisitos

- **Python 3.11 o superior** (lo exige `pyproject.toml`; probado con 3.11 y 3.14).
- Dependencias:
  - `requests`: acceso al servicio web (`Data/ClienteHttp.py`).
  - `pygame-ce`: interfaz gráfica (solo para jugar; `--replay` y `--bench` no lo necesitan).

## Instalación

Desde la raíz del proyecto (la carpeta donde está `main.py`).

**Opción recomendada: uv.** Instala las mismas versiones que usamos (`uv.lock`) y, si hace falta, descarga un Python compatible:

```
uv sync
```

**Alternativa: pip** (necesita Python 3.11 o superior ya instalado):

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install pygame-ce requests        (Windows)
.venv/bin/python -m pip install pygame-ce requests                (Linux / macOS)
```

## Cómo ejecutar

Con uv, cada comando se antepone con `uv run`. Sin uv, se usa el Python del entorno virtual
(`.venv\Scripts\python.exe` en Windows, `.venv/bin/python` en Linux / macOS); así no hace falta activar el entorno,
algo que PowerShell bloquea por defecto.

| Comando | Qué hace |
|---|---|
| `uv run python main.py` | Abre el juego conectado al servicio web. |
| `uv run python main.py --offline` | Abre el juego con el paquete local de `paquete/`, sin usar la red. |
| `uv run python main.py --cache-size N` | Cambia el tope de fichas del catálogo en memoria (entero mayor o igual a 1; por defecto 25). Se puede combinar con los demás modos. |
| `uv run python main.py --replay logs/partida_001.log` | Reproduce una partida desde su bitácora, sin abrir la ventana, y muestra cada acción y el resultado final. |
| `uv run python main.py --bench` | Corre las mediciones de rendimiento con cargas sintéticas, sin abrir la ventana, y muestra una tabla por subsistema. |
| `uv run python main.py --ayuda` | Muestra las opciones. |

`--replay` y `--bench` no se pueden usar juntos.

**Nota sobre `--bench`:** la tabla es larga. La terminal integrada de PyCharm puede no mostrarla completa;
en una terminal normal sale entera. Para guardarla en un archivo:

```
uv run python main.py --bench > bench.txt
```

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

Lee la cripta desde la carpeta `paquete/`, que viene en el repositorio con `cripta-01`. Las lecturas locales
no cuentan como solicitudes de red, así que el reporte final muestra 0 solicitudes.

Para descargar otra cripta al paquete (esto sí usa la red):

```
uv run python -m Data.DescargadorPaquete <id-de-la-cripta>
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

```
uv run python -m unittest discover -s tests -p "[Tt]est*.py"
```

## Documentación

- `PROMPTS_LLM.md`: bitácora de uso de modelos de lenguaje.
