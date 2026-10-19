"""
Ayudas compartidas por las pruebas de los controladores (no es una prueba).

Todo usa el paquete offline del repositorio y carpetas temporales: nada se escribe en cache/, logs/ ni saves/.
Siempre se usa la fuente offline, sea cual sea config.offline: las pruebas nunca tocan la red.
"""
import json
import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from Data.AlmacenPuntajes import AlmacenPuntajes  # noqa: E402
from Data.FuenteOffline import FuenteOffline  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from Service.ServicioBench import ServicioBench  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402
from Service.ServicioPuntajes import ServicioPuntajes  # noqa: E402
from UIController.ControladorBackend import ControladorBackend  # noqa: E402

CONFIG_OFFLINE = ConfiguracionDTO(offline=True)


def crear_partida(carpeta: str, config: ConfiguracionDTO = CONFIG_OFFLINE, paquete: str | None = None,
                  clase=ServicioPartida) -> ServicioPartida:
    """Un ServicioPartida real que lee el paquete del repositorio (o el de 'paquete') y escribe solo en 'carpeta'.
    'clase' permite probar con una subclase que falla a propósito."""
    return clase(config, fuente=FuenteOffline(paquete if paquete is not None else str(RAIZ / "paquete")),
                 carpeta_cache=os.path.join(carpeta, "cache"), carpeta_logs=os.path.join(carpeta, "logs"))


def crear_backend(carpeta: str, config: ConfiguracionDTO = CONFIG_OFFLINE, bench=None,
                  ruta_puntajes: str | None = None, paquete: str | None = None,
                  partida: ServicioPartida | None = None) -> ControladorBackend:
    """Un ControladorBackend con servicios reales que escribe solo en 'carpeta'."""
    if partida is None:
        partida = crear_partida(carpeta, config, paquete)
    if ruta_puntajes is None:
        ruta_puntajes = os.path.join(carpeta, "puntajes.jsonl")
    puntajes = ServicioPuntajes(AlmacenPuntajes(ruta_puntajes))
    return ControladorBackend(config, partida, puntajes, bench if bench is not None else ServicioBench([]))


def paquete_con_otra_version(destino: str, id_cripta: str = "cripta-01") -> str:
    """Copia el paquete offline a 'destino' cambiándole la versión de la cripta. Sirve para probar que una partida
    guardada o un log grabados con la versión original se rechazan (Apéndice B). Devuelve la ruta del paquete."""
    copia = os.path.join(destino, "paquete_otra_version")
    shutil.copytree(str(RAIZ / "paquete"), copia)
    ruta = os.path.join(copia, id_cripta, "general.json")
    with open(ruta, encoding="utf-8") as archivo:
        general = json.load(archivo)
    general["version"] = "otra-version-distinta"
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(general, archivo)
    return copia