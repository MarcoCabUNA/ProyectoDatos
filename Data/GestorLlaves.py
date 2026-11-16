"""
GestorLlaves (Integrante 2, feature 003): obtiene la ubicación de las llaves de una cripta (contracts/contrato-llaves.md).

    1) si hay almacén y tiene la versión vigente de la cripta, la usa (FR-317: no se vuelve a pedir);
    2) si no, una solicitud a la fuente y, si hay almacén, la guarda ANTES de validar (la respuesta es la del API para
       esa versión: volver a pedirla no la arregla, así que la segunda verificación da el mismo error sin gastar otra
       solicitud);
    3) valida FR-321 contra el esqueleto (validar_ubicaciones).

No mira la bandera --offline de la configuración: el almacén llega ya decidido (None con --offline), elegido en el
mismo if que elige la fuente en ServicioPartida.fuente() (Principio I). Los errores salen tal cual: ErrorRed (red, 429, presupuesto, paquete sin
llaves.json, formato) o ErrorDatos (sala inexistente).
"""
from Data.AlmacenLlaves import AlmacenLlaves
from Data.FuenteDatos import FuenteDatos
from Data.GestorEsqueleto import GestorEsqueleto
from Data.ValidacionDatos import validar_ubicaciones
from DTO.CriptaDTO import CriptaDTO
from DTO.UbicacionLlaveDTO import UbicacionLlaveDTO


class GestorLlaves:
    """Ubicación de las llaves: almacén vigente, o una solicitud que se persiste, y luego la validación de FR-321."""

    def __init__(self, fuente: FuenteDatos, almacen: AlmacenLlaves | None):
        self._fuente = fuente
        self._almacen = almacen

    def obtener(self, cripta: CriptaDTO, esqueleto: GestorEsqueleto) -> list[UbicacionLlaveDTO]:
        """Las ubicaciones en el orden de la respuesta. 'esqueleto' ya cargado con la misma cripta."""
        ubicaciones = None
        if self._almacen is not None:
            ubicaciones = self._almacen.leer(cripta.id, cripta.version)
        if ubicaciones is None:
            ubicaciones = self._fuente.obtener_llaves(cripta.id)
            if self._almacen is not None:
                self._almacen.guardar(cripta.id, cripta.version, ubicaciones)
        validar_ubicaciones(f"ubicación de llaves de {cripta.id}", ubicaciones, esqueleto.existe_sala)
        return ubicaciones
