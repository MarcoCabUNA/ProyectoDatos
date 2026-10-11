"""
LectorArgumentos (Integrante 2, con el visto bueno de Integrante 3): lee las banderas de la línea de
comandos con argparse (aprobada por el profesor) y devuelve un ConfiguracionDTO ya validado.

Está en el Controlador porque la arquitectura pone ahí la validación de la ESTRUCTURA de lo que
escribe el usuario (la Guía: "toda validación de estructura del comando vive en el Controlador").
Solo valida forma (bandera conocida, valor presente, número válido); no abre archivos ni usa la red:
si el log de --replay no existe, lo informa quien lo lee (BitacoraReplayIO).

Banderas:
    --offline             usar el paquete guardado en disco en lugar del servicio web
    --cache-size N        tope de fichas del catálogo en memoria (entero >= 1; por defecto 25)
    --replay ARCHIVO      reproducir una partida desde su log, sin intervención del usuario
    --bench               correr las mediciones de rendimiento
    -h, --help, --ayuda   mostrar la ayuda
Los valores se pueden escribir separados ("--cache-size 40") o con igual ("--cache-size=40").
--replay y --bench no se pueden usar juntos (son modos distintos, §9 del enunciado).

Uso desde main.py:
    import sys
    from UIController.LectorArgumentos import ErrorArgumentos, TEXTO_AYUDA, leer_argumentos
    try:
        config = leer_argumentos(sys.argv[1:])
    except ErrorArgumentos as error:
        print(error)
        print(TEXTO_AYUDA)
        sys.exit(2)
    if config.ayuda:
        print(TEXTO_AYUDA)
        sys.exit(0)

Decisiones sobre argparse:
  - Por defecto argparse termina el programa (sys.exit) al encontrar un error o al pedir la ayuda.
    Aquí se cambia para que lance ErrorArgumentos y para que la ayuda sea un campo del DTO: así
    main.py decide qué hacer y las pruebas pueden comprobar cada caso sin cerrar el programa.
  - allow_abbrev=False: "--off" NO se acepta como "--offline" (evita sorpresas con abreviaturas).
  - Si una bandera se repite, vale la última (comportamiento normal de argparse).
  - Los mensajes propios (por ejemplo los de --cache-size) están en español; los que genera
    argparse para errores de forma (opción desconocida, falta el valor) vienen en inglés.
"""
import argparse
import sys
from typing import NoReturn

from DTO.ConfiguracionDTO import CACHE_SIZE_POR_DEFECTO, ConfiguracionDTO


class ErrorArgumentos(ValueError):
    """Lo que escribió el usuario no tiene la forma correcta. El mensaje dice qué corregir."""


class _Analizador(argparse.ArgumentParser):
    """ArgumentParser que lanza ErrorArgumentos en lugar de terminar el programa."""

    def error(self, message: str) -> NoReturn:   # argparse llama a este método ante cualquier error de forma
        raise ErrorArgumentos(f"Error en las opciones: {message}")


def _entero_positivo(texto: str) -> int:
    """Tipo de --cache-size: solo dígitos y al menos 1 (rechaza '2.5', '-5', 'abc', ' 3', '²')."""
    if texto == "":
        raise argparse.ArgumentTypeError("necesita un número entero")
    for caracter in texto:
        if not ("0" <= caracter <= "9"):
            raise argparse.ArgumentTypeError(f"debe ser un número entero mayor o igual a 1 (se recibió {texto!r})")
    numero = int(texto)
    if numero < 1:
        raise argparse.ArgumentTypeError(f"debe ser mayor o igual a 1 (se recibió {texto!r})")
    return numero


def _crear_analizador() -> _Analizador:
    opciones: dict = {}
    if sys.version_info >= (3, 14):
        opciones["color"] = False    # 3.14 colorea la ayuda en la terminal; TEXTO_AYUDA debe ser texto plano
    analizador = _Analizador(
        prog="python main.py",
        description="Cripta: juego de exploración por eventos (Estructuras de Datos II, UNA).",
        add_help=False,          # la ayuda se maneja como un campo del DTO (ver arriba)
        allow_abbrev=False,
        exit_on_error=False,
        **opciones,
    )
    analizador.add_argument("--offline", action="store_true",
                            help="usar el paquete guardado en disco en lugar del servicio web")
    analizador.add_argument("--cache-size", type=_entero_positivo, default=CACHE_SIZE_POR_DEFECTO, metavar="N",
                            help=f"tope de fichas del catálogo en memoria (entero >= 1; por defecto {CACHE_SIZE_POR_DEFECTO})")
    modo = analizador.add_mutually_exclusive_group()
    modo.add_argument("--replay", metavar="ARCHIVO", help="reproducir una partida desde su log")
    modo.add_argument("--bench", action="store_true", help="correr las mediciones de rendimiento")
    analizador.add_argument("-h", "--help", "--ayuda", dest="ayuda", action="store_true", help="mostrar esta ayuda")
    return analizador


TEXTO_AYUDA = _crear_analizador().format_help()


def leer_argumentos(argumentos: list[str]) -> ConfiguracionDTO:
    """
    argumentos: lo que viene después del nombre del programa (sys.argv[1:]).
    Devuelve la configuración, o lanza ErrorArgumentos con un mensaje para el usuario.
    """
    try:
        resultado = _crear_analizador().parse_args(argumentos)
    except argparse.ArgumentError as error:      # según la versión de Python llega por aquí o por error()
        raise ErrorArgumentos(f"Error en las opciones: {error}") from None
    if resultado.replay is not None and resultado.replay.strip() == "":
        raise ErrorArgumentos("Error en las opciones: --replay necesita la ruta del archivo de la partida")
    return ConfiguracionDTO(offline=resultado.offline, cache_size=resultado.cache_size,
                            replay=resultado.replay, bench=resultado.bench, ayuda=resultado.ayuda)