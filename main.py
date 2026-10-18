"""
Cripta: punto de entrada. Solo cablea: lee las opciones y elige el modo.

    python main.py                       el juego (ventana de pygame)
    python main.py --offline             el juego con el paquete guardado en disco
    python main.py --replay ARCHIVO      reproduce una partida desde su log, sin ventana
    python main.py --bench               corre las mediciones de rendimiento, sin ventana
    python main.py --ayuda               muestra las opciones

pygame se importa SOLO en el modo interactivo, dentro de jugar(): así --replay y --bench funcionan sin pygame instalado
(arquitectura §6). Código de salida: 0 bien, 1 si falló la operación o no se pudo abrir la interfaz, 2 si las opciones
son inválidas.
"""
import sys

from DTO.ConfiguracionDTO import ConfiguracionDTO
from UIController.ControladorBackend import ControladorBackend, ErrorOperacion
from UIController.LectorArgumentos import TEXTO_AYUDA, ErrorArgumentos, leer_argumentos


def main(argumentos: list[str] | None = None) -> int:
    """Corre el programa con 'argumentos' (por omisión, los de la línea de comandos) y devuelve el código de salida."""
    try:
        config = leer_argumentos(sys.argv[1:] if argumentos is None else argumentos)
    except ErrorArgumentos as error:
        print(error)
        print(TEXTO_AYUDA)
        return 2
    if config.ayuda:
        print(TEXTO_AYUDA)
        return 0
    if config.bench:
        return medir(config)
    if config.replay is not None:
        return reproducir(config)
    return jugar(config)


def medir(config: ConfiguracionDTO) -> int:
    try:
        backend = ControladorBackend(config)
        resultados = backend.medir(lambda numero, total: print(f"Midiendo... grupo {numero} de {total}", flush=True))
        print(backend.tabla_mediciones(resultados))
    except ErrorOperacion as error:
        print(error)
        return 1
    return 0


def reproducir(config: ConfiguracionDTO) -> int:
    def al_avanzar(numero, accion, estado):
        detalle = [str(valor) for valor in (accion.direccion, accion.objetivo, accion.objeto) if valor is not None]
        print(f"{numero:>4}  {accion.tipo:<8} {' '.join(detalle):<22} t={estado.reloj}  {estado.sala.nombre}")

    try:
        resultado = ControladorBackend(config).reproducir(config.replay, al_avanzar)
    except ErrorOperacion as error:
        print(error)
        return 1
    encabezado, final = resultado.encabezado, resultado.estado_final
    print()
    print(f"Cripta: {encabezado.id_cripta} (versión {encabezado.version_cripta}, catálogo {encabezado.version_catalogo})")
    print(f"Semilla: {encabezado.semilla}")
    print(f"Acciones reproducidas: {resultado.acciones_reproducidas}")
    print(f"Resultado: {final.resultado if final.terminado else 'la partida no terminó'} (reloj {final.reloj})")
    if resultado.ultima_linea_descartada:
        print("Aviso: la última línea del log estaba a medio escribir y se ignoró.")
    return 0


def jugar(config: ConfiguracionDTO) -> int:
    """El modo interactivo. Las importaciones están aquí adentro a propósito: ver el docstring del módulo."""
    try:
        from UIController.ControladorPygame import ControladorPygame
        from View.VistaPygame import VistaPygame
    except ModuleNotFoundError as error:
        print(f"No se puede abrir la interfaz gráfica: falta el módulo '{error.name}'")
        if error.name == "pygame":
            print("Instálalo con: uv add pygame-ce")
        return 1
    ControladorPygame(VistaPygame(animaciones=True), config, demora_fin_ms=1500).ejecutar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
