"""
FuenteRed (Integrante 2): implementa FuenteDatos contra el servicio web de Cripta.

Une las dos piezas que ya existen:
  - ClienteHttp hace la solicitud (encabezado, 429, presupuesto, errores) y
    devuelve el JSON decodificado;
  - los DTOs traducen ese JSON con desde_diccionario().
El dict de respuesta.json() nunca sale de esta clase: lo que sale son DTOs.
"""
from urllib.parse import quote

from Data.ClienteHttp import ClienteHttp, ErrorRed
from Data.FuenteDatos import FuenteDatos
from DTO.CriptaDTO import CriptaDTO, ResumenCriptaDTO
from DTO.FichaEnemigoDTO import FichaEnemigoDTO   # Integrante 1
from DTO.FichaTrampaDTO import FichaTrampaDTO     # Integrante 1
from DTO.ObjetoDTO import ObjetoDTO, es_clase_objeto
from DTO.SalaDTO import ContenidoSalaDTO, SalaDTO
from Security.ValidadorAcceso import generar_client_id

URL_BASE = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


class FuenteRed(FuenteDatos):

    def __init__(self, cliente: ClienteHttp | None = None):
        """
        Sin argumentos crea su propio ClienteHttp con el client id de esta ejecución.
        Las pruebas le pasan un cliente falso para no usar la red.
        """
        self._cliente = cliente if cliente is not None else ClienteHttp(URL_BASE, generar_client_id())

    # ------------------------------------------------------------ criptas
    def listar_criptas(self) -> list[ResumenCriptaDTO]:
        op = "listar criptas"
        datos = self._cliente.get_json("criptas", op)
        return self._traducir(op, lambda: [ResumenCriptaDTO.desde_diccionario(c) for c in datos["criptas"]])

    def obtener_datos_generales(self, id_cripta: str) -> CriptaDTO:
        op = f"datos generales de {id_cripta}"
        datos = self._cliente.get_json(f"criptas/{self._id_en_url(id_cripta)}", op)
        cripta = self._traducir(op, lambda: CriptaDTO.desde_diccionario(datos))
        # El presupuesto nunca se escribe a mano en el código: se lee de la cripta.
        self._cliente.fijar_presupuesto(cripta.presupuesto_solicitudes)
        return cripta

    def obtener_version_cripta(self, id_cripta: str) -> str:
        op = f"versión de {id_cripta}"
        datos = self._cliente.get_json(f"criptas/{self._id_en_url(id_cripta)}/version", op)
        return self._traducir(op, lambda: self._texto(datos["version"]))

    # ------------------------------------------------------------ salas
    def obtener_pagina_salas(self, id_cripta: str, pagina: int, version: str) -> list[SalaDTO]:
        if pagina < 1:
            raise ValueError(f"La página empieza en 1 (se pidió {pagina})")
        op = f"esqueleto de {id_cripta}, página {pagina}"
        datos = self._cliente.get_json(f"criptas/{self._id_en_url(id_cripta)}/salas", op,
                                       (("pagina", pagina),))
        return self._traducir(op, lambda: [SalaDTO.desde_diccionario(s, version) for s in datos["salas"]])

    def obtener_contenido(self, id_cripta: str, ids_salas: list[int]) -> list[ContenidoSalaDTO]:
        self._validar_lote(ids_salas, self.MAX_SALAS_POR_CONTENIDO, "salas")
        op = f"contenido de {id_cripta}, salas {self._unir(ids_salas)}"
        datos = self._cliente.get_json(f"criptas/{self._id_en_url(id_cripta)}/contenido", op,
                                       (("salas", self._unir(ids_salas)),))
        recibidos = self._traducir(op, lambda: [ContenidoSalaDTO.desde_diccionario(c) for c in datos["contenido"]])
        return self._en_orden_pedido(op, ids_salas, recibidos, lambda c: c.sala)

    # ------------------------------------------------------------ catálogo
    def obtener_version_catalogo(self) -> str:
        op = "versión del catálogo"
        datos = self._cliente.get_json("catalogo/version", op)
        return self._traducir(op, lambda: self._texto(datos["version"]))

    def obtener_catalogo(self, ids: list[str]) -> list:
        self._validar_lote(ids, self.MAX_IDS_POR_CATALOGO, "ids de catálogo")
        op = f"catálogo de {self._unir(ids)}"
        datos = self._cliente.get_json("catalogo", op, (("ids", self._unir(ids)),))
        recibidos = self._traducir(op, lambda: [self._ficha_desde_diccionario(f) for f in datos["entidades"]])
        return self._en_orden_pedido(op, ids, recibidos, lambda f: f.id)

    @staticmethod
    def _ficha_desde_diccionario(d: dict):
        """Elige el DTO según el campo 'clase' de la ficha."""
        clase = d["clase"]
        if clase == "enemigo":
            return FichaEnemigoDTO.desde_diccionario(d)
        if clase == "trampa":
            return FichaTrampaDTO.desde_diccionario(d)
        if es_clase_objeto(clase):
            return ObjetoDTO.desde_diccionario(d)
        raise ValueError(f"clase de catálogo desconocida: {clase!r}")

    # ------------------------------------------------------------ red
    def solicitudes_realizadas(self) -> int:
        return self._cliente.solicitudes_realizadas

    def presupuesto_solicitudes(self) -> int | None:
        return self._cliente.presupuesto

    # ------------------------------------------------------------ auxiliares
    @staticmethod
    def _traducir(op: str, convertir):
        """
        Ejecuta la conversión JSON -> DTO. Si al JSON le falta un campo obligatorio o
        trae un tipo inesperado, lo informa como ErrorRed de formato (la única validación
        permitida en esta capa), no como un KeyError suelto.
        """
        try:
            return convertir()
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            raise ErrorRed(op, f"la respuesta no tiene el formato esperado ({type(e).__name__}: {e})") from e

    @staticmethod
    def _en_orden_pedido(op: str, pedidos: list, recibidos: list, clave) -> list:
        """
        Devuelve 'recibidos' en el orden de 'pedidos' y verifica que no falte ni sobre nada.
        Búsqueda lineal: O(k^2) con k <= 10 por lote, es decir, a lo sumo 100 comparaciones.
        """
        if len(recibidos) != len(pedidos):
            raise ErrorRed(op, f"se pidieron {len(pedidos)} elementos y llegaron {len(recibidos)}")
        ordenados = []
        for pedido in pedidos:
            encontrado = None
            for elemento in recibidos:
                if clave(elemento) == pedido:
                    encontrado = elemento
                    break
            if encontrado is None:
                raise ErrorRed(op, f"la respuesta no incluye {pedido!r}")
            ordenados.append(encontrado)
        return ordenados

    @staticmethod
    def _validar_lote(ids: list, maximo: int, nombre: str) -> None:
        """El API exige entre 1 y 'maximo' ids distintos por solicitud."""
        if len(ids) < 1 or len(ids) > maximo:
            raise ValueError(f"Se deben pedir entre 1 y {maximo} {nombre} (se pidieron {len(ids)})")
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if ids[i] == ids[j]:
                    raise ValueError(f"{nombre} repetido en la misma solicitud: {ids[i]!r}")

    @staticmethod
    def _unir(ids: list) -> str:
        return ",".join(str(x) for x in ids)

    @staticmethod
    def _id_en_url(id_cripta: str) -> str:
        return quote(id_cripta, safe="")

    @staticmethod
    def _texto(valor) -> str:
        if not isinstance(valor, str):
            raise TypeError(f"se esperaba texto y llegó {type(valor).__name__}")
        return valor