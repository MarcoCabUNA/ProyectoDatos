"""
AlmacenCatalogo (Integrante 2): fichas del catálogo guardadas en DISCO (enunciado §4.4).

Qué exige el enunciado y cómo se cumple:
  - "La caché debe sobrevivir al cierre del programa"   -> cada ficha queda en un archivo.
  - "Una ficha liberada de memoria permanece en el       -> CacheCatalogo (memoria) puede liberarla;
     almacenamiento persistente. Recuperarla cuesta una     aquí sigue estando, y leerla es abrir
     lectura de disco, no una solicitud de red."            UN archivo pequeño.
  - "Solo genera solicitud de red una ficha que nunca se -> carpeta por versión: si la versión del
     persistió o cuya versión de catálogo ya no coincide"   catálogo cambió, la carpeta vieja se
                                                            borra y todo se vuelve a pedir.
  - "La versión del catálogo debe usarse para validar lo -> basta comparar la versión (una consulta
     persistido sin descargarlo todo nuevamente"            liviana) con el nombre de la carpeta.

Formato en disco (la carpeta cache/ no se sube a Git: es de cada computadora):

    cache/catalogo/<version_catalogo>/VERSION              marca: contiene la versión
    cache/catalogo/<version_catalogo>/<id_ficha>.json      una ficha, mismo JSON del API

Por qué un archivo por ficha: recuperar una ficha liberada es abrir y leer un archivo de
unos cientos de bytes, sin cargar el catálogo entero ni mantener un índice en memoria
(no se permite dict). Ubicar el archivo por su nombre lo resuelve el sistema de archivos.

Seguridad e integridad (Datos solo valida formato, nunca reglas del juego):
  - El id se usa como nombre de archivo solo si es_nombre_seguro() (MSI) lo acepta.
  - Se escribe a un .tmp y luego se reemplaza: un cierre a mitad de escritura no deja un
    archivo a medias.
  - Un archivo dañado (JSON inválido o ficha incompleta) se borra y se trata como si no
    estuviera: la ficha se volverá a pedir. Nunca detiene el juego.
  - Solo se borran carpetas de versiones viejas que tengan la marca VERSION de este almacén,
    para no borrar por error otra cosa si la carpeta base se configura mal.

Esta clase no usa la red: quien la crea le dice cuál es la versión vigente del catálogo
(ResolvedorCatalogo, paso 10, la consulta con GET /catalogo/version).
"""
import json
import os
import shutil

from Data.CacheCatalogo import Ficha
from Data.FuenteJson import FuenteJson
from Security.ValidadorAcceso import es_nombre_seguro, validar_version

CARPETA_POR_DEFECTO = os.path.join("cache", "catalogo")
_MARCA = "VERSION"
_EXTENSION = ".json"


class AlmacenCatalogo:

    def __init__(self, version_catalogo: str, carpeta_base: str = CARPETA_POR_DEFECTO):
        if not es_nombre_seguro(version_catalogo):
            raise ValueError(f"Versión de catálogo no válida como nombre de carpeta: {version_catalogo!r}")
        self._version = version_catalogo
        self._base = carpeta_base
        self._carpeta = os.path.join(carpeta_base, version_catalogo)
        # Contadores para el reporte final y --bench.
        self._lecturas = 0
        self._escrituras = 0
        self._danadas = 0

    # ------------------------------------------------------------ preparación
    def preparar(self) -> list[str]:
        """
        Se llama una vez al iniciar. Borra las carpetas de versiones VIEJAS del catálogo (lo
        persistido con otra versión ya no es válido) y crea la de la versión vigente.
        Devuelve las versiones descartadas.
        """
        descartadas: list[str] = []
        if os.path.isdir(self._base):
            for nombre in os.listdir(self._base):
                if nombre == self._version:
                    continue
                ruta = os.path.join(self._base, nombre)
                if self._es_carpeta_de_version(ruta, nombre):
                    shutil.rmtree(ruta)
                    descartadas.append(nombre)
        self._asegurar_carpeta()
        return descartadas

    # ------------------------------------------------------------ consultas
    def contiene(self, id_ficha: str) -> bool:
        """¿Hay un archivo para esta ficha en la versión vigente? No lee el archivo."""
        return es_nombre_seguro(id_ficha) and os.path.isfile(self._ruta(id_ficha))

    def leer(self, id_ficha: str) -> Ficha | None:
        """
        UNA lectura de disco. Devuelve la ficha, o None si no se persistió o si el archivo
        estaba dañado (en ese caso se borra, para volver a pedirla y reescribirla).
        """
        if not self.contiene(id_ficha):
            return None
        ruta = self._ruta(id_ficha)
        self._lecturas += 1
        try:
            with open(ruta, encoding="utf-8") as archivo:
                datos = json.load(archivo)
            ficha = FuenteJson.ficha_desde_diccionario(datos)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self._borrar_danado(ruta)
            return None
        if ficha.id != id_ficha:
            # El archivo no corresponde a ese id (editado a mano, o dos ids que solo difieren
            # en mayúsculas en Windows). No se borra: puede ser la ficha válida del otro id.
            return None
        return ficha

    def version(self) -> str:
        return self._version

    def lecturas(self) -> int:
        return self._lecturas

    def escrituras(self) -> int:
        return self._escrituras

    def danadas(self) -> int:
        return self._danadas

    # ------------------------------------------------------------ cambios
    def guardar(self, ficha: Ficha) -> None:
        """Escribe (o reemplaza) la ficha en disco, en el mismo formato JSON del API."""
        if not es_nombre_seguro(ficha.id):
            raise ValueError(f"Id de ficha no válido como nombre de archivo: {ficha.id!r}")
        self._asegurar_carpeta()
        texto = json.dumps(ficha.a_diccionario(), ensure_ascii=False)
        self._escribir(self._ruta(ficha.id), texto)
        self._escrituras += 1

    # ------------------------------------------------------------ auxiliares
    def _ruta(self, id_ficha: str) -> str:
        return os.path.join(self._carpeta, id_ficha + _EXTENSION)

    def _asegurar_carpeta(self) -> None:
        """Crea la carpeta de la versión vigente con su marca, si no existe."""
        os.makedirs(self._carpeta, exist_ok=True)
        marca = os.path.join(self._carpeta, _MARCA)
        if not os.path.isfile(marca):
            self._escribir(marca, self._version)

    @staticmethod
    def _es_carpeta_de_version(ruta: str, nombre: str) -> bool:
        """Solo es nuestra si es una carpeta con la marca VERSION y la marca dice ese mismo nombre."""
        marca = os.path.join(ruta, _MARCA)
        if not os.path.isdir(ruta) or not os.path.isfile(marca):
            return False
        try:
            with open(marca, encoding="utf-8") as archivo:
                contenido = archivo.read().strip()
        except (OSError, ValueError):
            return False
        return validar_version(contenido, nombre)

    @staticmethod
    def _escribir(ruta: str, texto: str) -> None:
        """Escribe en un archivo temporal y luego lo reemplaza, para no dejar archivos a medias."""
        temporal = ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as archivo:
            archivo.write(texto)
        os.replace(temporal, ruta)

    def _borrar_danado(self, ruta: str) -> None:
        self._danadas += 1
        try:
            os.remove(ruta)
        except OSError:
            pass   # si no se puede borrar, se sobrescribirá al volver a guardarla