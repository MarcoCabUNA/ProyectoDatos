"""
FuenteRed (Integrante 2): FuenteDatos contra el servicio web de Cripta.

Toda la traducción JSON -> DTO está en FuenteJson (compartida con FuenteOffline).
Aquí solo se decide que el JSON sale de la RED, a través de ClienteHttp, que pone el
encabezado X-Cripta-Client-Id, maneja el 429 y cuenta cada solicitud contra el presupuesto.
"""
from Data.ClienteHttp import ClienteHttp
from Data.FuenteJson import FuenteJson
from Security.ValidadorAcceso import generar_client_id

URL_BASE = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


class FuenteRed(FuenteJson):

    def __init__(self, cliente: ClienteHttp | None = None):
        """
        Sin argumentos crea su propio ClienteHttp con el client id de esta ejecución.
        Las pruebas le pasan un cliente falso para no usar la red.
        """
        super().__init__(cliente if cliente is not None else ClienteHttp(URL_BASE, generar_client_id()))