"""
FuenteDatos (Integrante 2): contrato común de la capa de Datos.

FuenteRed (servicio web) y FuenteOffline (archivos locales del modo --offline)
implementan esta misma interfaz. Así el resto del programa recibe siempre los
mismos DTOs y nunca sabe cuál de las dos está activa.

Reglas del contrato:
  - Todo método devuelve DTOs, arrays (list) de DTOs o un str. Nunca un dict.
  - Ante un fallo de conexión o de formato se lanza ErrorRed (Data/ClienteHttp.py).
  - No se aplica ninguna regla del juego: solo se obtiene y se traduce información.
"""
from abc import ABC, abstractmethod

from DTO.CriptaDTO import CriptaDTO, ResumenCriptaDTO
from DTO.SalaDTO import ContenidoSalaDTO, SalaDTO


class FuenteDatos(ABC):
    # Límites que impone el API por solicitud (enunciado §3.2).
    MAX_SALAS_POR_CONTENIDO = 10
    MAX_IDS_POR_CATALOGO = 10

    # ------------------------------------------------------------ criptas
    @abstractmethod
    def listar_criptas(self) -> list[ResumenCriptaDTO]:
        """Criptas publicadas, para que el jugador elija una."""

    @abstractmethod
    def obtener_datos_generales(self, id_cripta: str) -> CriptaDTO:
        """Datos generales de una cripta (incluye versión y presupuesto)."""

    @abstractmethod
    def obtener_version_cripta(self, id_cripta: str) -> str:
        """Solo la versión de la cripta, para validar lo guardado en disco."""

    # ------------------------------------------------------------ salas
    @abstractmethod
    def obtener_pagina_salas(self, id_cripta: str, pagina: int, version: str) -> list[SalaDTO]:
        """
        Una página del esqueleto (pagina empieza en 1). Las salas vienen sin contenido
        (contenido_cargado=False). 'version' es la de CriptaDTO: /salas no la trae.
        """

    @abstractmethod
    def obtener_contenido(self, id_cripta: str, ids_salas: list[int]) -> list[ContenidoSalaDTO]:
        """
        Contenido de 1 a 10 salas distintas, en el MISMO orden en que se pidieron.
        GestorContenido lo une con el SalaDTO del esqueleto (SalaDTO.con_contenido).
        """

    # ------------------------------------------------------------ catálogo
    @abstractmethod
    def obtener_version_catalogo(self) -> str:
        """Versión global del catálogo, para validar las fichas guardadas en disco."""

    @abstractmethod
    def obtener_catalogo(self, ids: list[str]) -> list:
        """
        Fichas de 1 a 10 ids distintos, en el mismo orden en que se pidieron.
        Cada elemento es, según su 'clase':
            enemigo -> FichaEnemigoDTO  (Integrante 1)
            trampa  -> FichaTrampaDTO   (Integrante 1)
            otra    -> ObjetoDTO        (Integrante 2)
        """

    # ------------------------------------------------------------ red
    # No son abstractos: una fuente sin red (offline) no hace solicitudes.
    def solicitudes_realizadas(self) -> int:
        """Solicitudes enviadas en esta partida (para el reporte final, §5.1)."""
        return 0

    def presupuesto_solicitudes(self) -> int | None:
        """Presupuesto vigente, o None si esta fuente no usa red."""
        return None