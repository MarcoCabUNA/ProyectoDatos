"""
AlmacenLlaves (Integrante 2, feature 003): la ubicación de las llaves guardada en DISCO, por versión de la cripta
(FR-317, FR-319; contracts/contrato-llaves.md, «Persistencia por versión»).

    cache/llaves/<id_cripta>.json   {"id": ..., "version": <versión de la cripta>, "llaves": [...formato del API...]}

Un archivo por cripta con su versión adentro (la versión es por cripta, no global como la del catálogo). La versión
vigente es CriptaDTO.version, que ya llegó con los datos generales: no se pide /version aparte.

Estados: ausente -> guardar -> vigente; vigente -> cambia la versión -> vencido (leer devuelve None) -> guardar ->
vigente; dañado -> leer lo borra -> ausente. Nadie borra archivos a mano: el siguiente guardar reemplaza al vencido.
Seguridad e integridad, como AlmacenCatalogo: un id que no pasa es_nombre_seguro no se lee ni se escribe (se vuelve
a pedir) y se escribe en un .tmp que luego se reemplaza con os.replace.
Con --offline este almacén no se usa: lo decide ServicioPartida.fuente() en el mismo if que elige la fuente.
"""
import json
import os

from Data.FuenteJson import FuenteJson
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO
from Security.ValidadorAcceso import es_nombre_seguro, validar_version

CARPETA_POR_DEFECTO = os.path.join("cache", "llaves")
_EXTENSION = ".json"


class AlmacenLlaves:
    """Persistencia de GET /criptas/{id}/llaves por versión de la cripta."""

    def __init__(self, carpeta: str = CARPETA_POR_DEFECTO):
        self._carpeta = carpeta

    def leer(self, id_cripta: str, version: str) -> list[UbicacionLlaveDTO] | None:
        """
        Las ubicaciones guardadas, solo si el archivo existe, se puede leer, su id coincide y su versión es la
        vigente (validar_version). Un archivo dañado se borra y devuelve None; otra versión o id distinto: None.
        """
        if not es_nombre_seguro(id_cripta):
            return None
        ruta = self._ruta(id_cripta)
        if not os.path.isfile(ruta):
            return None
        try:
            with open(ruta, encoding="utf-8") as archivo:
                datos = json.load(archivo)
            if not isinstance(datos, dict):
                raise ValueError("el archivo no es un objeto")
            id_guardado = datos["id"]
            version_guardada = datos["version"]
            ubicaciones = FuenteJson.ubicaciones_desde_diccionario(datos)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self._borrar(ruta)
            return None
        if id_guardado != id_cripta:
            return None   # no corresponde a esa cripta (editado a mano); no se borra
        if not validar_version(version_guardada, version):
            return None   # vencido: se volverá a pedir y guardar lo reemplaza
        return ubicaciones

    def guardar(self, id_cripta: str, version: str, ubicaciones: list[UbicacionLlaveDTO]) -> None:
        """Escribe (o reemplaza) el archivo de la cripta, en el formato del API más su id y su versión."""
        if not es_nombre_seguro(id_cripta):
            return        # no se persiste: la próxima vez simplemente se vuelve a pedir
        os.makedirs(self._carpeta, exist_ok=True)
        datos = {"id": id_cripta, "version": version, "llaves": [u.a_diccionario() for u in ubicaciones]}
        ruta = self._ruta(id_cripta)
        temporal = ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as archivo:
            archivo.write(json.dumps(datos, ensure_ascii=False))
        os.replace(temporal, ruta)

    # ------------------------------------------------------------ auxiliares
    def _ruta(self, id_cripta: str) -> str:
        return os.path.join(self._carpeta, id_cripta + _EXTENSION)

    @staticmethod
    def _borrar(ruta: str) -> None:
        try:
            os.remove(ruta)
        except OSError:
            pass   # si no se puede borrar, guardar lo sobrescribirá
