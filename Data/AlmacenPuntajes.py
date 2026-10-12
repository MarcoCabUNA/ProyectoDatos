"""
AlmacenPuntajes (Integrante 2): la tabla de puntajes local en disco (enunciado §2.12).

"Al terminar, la partida se registra en una tabla de puntajes local con: nombre del jugador, id y
versión de la cripta, acciones ejecutadas por el jugador, enemigos derrotados y tiempo final del
reloj virtual" -> exactamente los campos de PuntajeDTO (Integrante 3).

Reparto (acordado con Integrante 3): Datos solo guarda y lee las filas, en el orden en que se
jugaron. Ordenarlas (con el Ordenador, §4.9) y mostrarlas es de Servicios / Vista.

Formato: un archivo de texto UTF-8 con UN PuntajeDTO por línea, en JSON (a_diccionario()):
    {"nombre":"Derek","mazmorra":"cripta-01","version":"fd58f7743b9e","acciones":42,...}
    {"nombre":"Kristel",...}
Decisiones:
  - Solo se ANEXA una línea por partida terminada: agregar no reescribe el archivo, cuesta O(1)
    y una partida vieja nunca se pierde por un error al guardar una nueva.
  - json.dumps escapa los saltos de línea, así que un nombre con "\\n" no puede partir la línea.
  - Si la última línea quedó a medio escribir (el programa se cerró escribiendo) se descarta, igual
    que en BitacoraReplayIO. Cualquier otra línea dañada es un error con su número de línea.
  - Archivo inexistente = tabla vacía (todavía no se ha terminado ninguna partida).
  - Por defecto vive en saves/puntajes.jsonl (saves/ ya está en el .gitignore: es de cada jugador).

Costos (n = partidas registradas): agregar O(1); leer O(n).
"""
import json
import os

from DTO.PuntajeDTO import PuntajeDTO

RUTA_POR_DEFECTO = os.path.join("saves", "puntajes.jsonl")

_CAMPOS_TEXTO = ("nombre", "mazmorra", "version")
_CAMPOS_ENTEROS = ("acciones", "enemigos_derrotados", "tiempo_final")


class ErrorPuntajes(ValueError):
    """La tabla de puntajes no se pudo escribir o leer. El mensaje dice qué pasó."""


class AlmacenPuntajes:

    def __init__(self, ruta: str = RUTA_POR_DEFECTO):
        self._ruta = ruta

    def ruta(self) -> str:
        return self._ruta

    def agregar(self, puntaje: PuntajeDTO) -> None:
        """Registra una partida terminada al final de la tabla. Crea la carpeta y el archivo si faltan."""
        if not isinstance(puntaje, PuntajeDTO):
            raise ErrorPuntajes(f"se esperaba un PuntajeDTO y llegó {type(puntaje).__name__}")
        problema = _problema_de_fila(puntaje.a_diccionario())
        if problema is not None:
            raise ErrorPuntajes(f"el puntaje no se puede guardar: {problema}")
        linea = json.dumps(puntaje.a_diccionario(), ensure_ascii=False, separators=(",", ":"))
        carpeta = os.path.dirname(self._ruta)
        try:
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            with open(self._ruta, "a", encoding="utf-8", newline="") as archivo:
                archivo.write(linea + "\n")
        except OSError as error:
            raise ErrorPuntajes(f"no se pudo escribir la tabla de puntajes {self._ruta!r}: {error}") from None

    def leer(self) -> list[PuntajeDTO]:
        """Todas las partidas registradas, en el orden en que se jugaron (sin ordenar)."""
        try:
            with open(self._ruta, encoding="utf-8", newline="") as archivo:
                texto = archivo.read()
        except FileNotFoundError:
            return []
        except (OSError, UnicodeDecodeError) as error:
            raise ErrorPuntajes(f"no se pudo leer la tabla de puntajes {self._ruta!r}: {error}") from None
        lineas = texto.split("\n")
        lineas.pop()                 # "" si termina en '\n'; si no, una línea a medio escribir: se descarta
        puntajes: list[PuntajeDTO] = []
        for i in range(len(lineas)):
            linea = lineas[i][:-1] if lineas[i].endswith("\r") else lineas[i]
            try:
                fila = json.loads(linea)
            except ValueError:
                raise ErrorPuntajes(f"{self._ruta!r}, línea {i + 1}: fila dañada (no es JSON)") from None
            problema = _problema_de_fila(fila)
            if problema is not None:
                raise ErrorPuntajes(f"{self._ruta!r}, línea {i + 1}: fila dañada ({problema})")
            puntajes.append(PuntajeDTO.desde_diccionario(fila))
        return puntajes


def _problema_de_fila(fila) -> str | None:
    """None si la fila tiene los 6 campos con el tipo correcto; si no, qué está mal."""
    if not isinstance(fila, dict):
        return "no es un objeto"
    for campo in _CAMPOS_TEXTO:
        if not isinstance(fila.get(campo), str):
            return f"'{campo}' debe ser texto"
    for campo in _CAMPOS_ENTEROS:
        valor = fila.get(campo)
        if not isinstance(valor, int) or isinstance(valor, bool):
            return f"'{campo}' debe ser un entero"
    return None