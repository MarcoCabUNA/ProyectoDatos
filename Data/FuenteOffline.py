"""
FuenteOffline (Integrante 2): FuenteDatos que lee el paquete del modo --offline.

El paquete son las respuestas del API guardadas en disco por DescargadorPaquete:

    paquete/
    ├── criptas.json
    ├── catalogo_version.json
    ├── catalogo.json             {"entidades": [...]}  todas las fichas
    └── <id_cripta>/
        ├── general.json
        ├── salas_p<N>.json       una por página
        └── contenido.json        {"contenido": [...]}  todas las salas

LectorPaquete imita a ClienteHttp: recibe la misma ruta del API y devuelve el mismo
JSON, pero leído de un archivo. Para contenido y catálogo filtra solo lo que se pidió,
así responde cualquier lote aunque el juego lo pida distinto a como se descargó.
Toda la traducción a DTOs la hace FuenteJson, igual que en FuenteRed.

Las lecturas offline NO cuentan como solicitudes de red (enunciado §5.1).
"""
import json
import os
from typing import Any
from urllib.parse import unquote

from Data.ClienteHttp import ErrorRed
from Data.FuenteJson import FuenteJson

CARPETA_POR_DEFECTO = "paquete"


class FuenteOffline(FuenteJson):

    def __init__(self, carpeta: str = CARPETA_POR_DEFECTO):
        super().__init__(LectorPaquete(carpeta))


class LectorPaquete:
    """Proveedor de JSON que lee del paquete en disco (mismo método que ClienteHttp)."""

    def __init__(self, carpeta: str):
        if not os.path.isdir(carpeta):
            raise ErrorRed("abrir paquete offline",
                           f"no existe la carpeta {carpeta!r}; créela con "
                           f"'python -m Data.DescargadorPaquete <id_cripta>'")
        self._carpeta = carpeta

    # Sin red: no hay presupuesto que fijar ni solicitudes que contar.
    def fijar_presupuesto(self, presupuesto: int) -> None:
        pass

    @property
    def solicitudes_realizadas(self) -> int:
        return 0

    @property
    def presupuesto(self) -> int | None:
        return None

    def get_json(self, ruta: str, operacion: str, parametros=()) -> Any:
        partes = ruta.split("/")

        if ruta == "criptas":
            return self._leer(operacion, "criptas.json")
        if ruta == "catalogo/version":
            return self._leer(operacion, "catalogo_version.json")
        if ruta == "catalogo":
            ids = self._parametro(parametros, "ids").split(",")
            todas = self._leer(operacion, "catalogo.json")["entidades"]
            return {"entidades": self._filtrar(todas, "id", ids)}

        if len(partes) >= 2 and partes[0] == "criptas":
            id_cripta = self._id_seguro(operacion, unquote(partes[1]))
            if len(partes) == 2:
                return self._leer(operacion, id_cripta, "general.json")
            if len(partes) == 3 and partes[2] == "version":
                general = self._leer(operacion, id_cripta, "general.json")
                return {"id": general["id"], "version": general["version"]}
            if len(partes) == 3 and partes[2] == "salas":
                pagina = self._parametro(parametros, "pagina")
                return self._leer(operacion, id_cripta, f"salas_p{pagina}.json")
            if len(partes) == 3 and partes[2] == "contenido":
                texto = self._parametro(parametros, "salas")
                ids_salas = [self._entero(operacion, x) for x in texto.split(",")]
                todas = self._leer(operacion, id_cripta, "contenido.json")["contenido"]
                return {"contenido": self._filtrar(todas, "sala", ids_salas)}

        raise ErrorRed(operacion, f"la ruta {ruta!r} no existe en el paquete offline")

    # ------------------------------------------------------------ auxiliares
    def _leer(self, operacion: str, *partes_ruta: str):
        ruta = os.path.join(self._carpeta, *partes_ruta)
        try:
            with open(ruta, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise ErrorRed(operacion, f"falta el archivo {ruta!r} en el paquete offline") from e
        except (OSError, ValueError) as e:   # json.JSONDecodeError hereda de ValueError
            raise ErrorRed(operacion, f"no se pudo leer {ruta!r} ({e})") from e

    @staticmethod
    def _filtrar(elementos: list, campo: str, buscados: list) -> list:
        """
        Los elementos cuyo 'campo' está en 'buscados'. Búsqueda lineal: O(k·n), con
        k <= 10 por lote. Si alguno no está, simplemente no se incluye y FuenteJson
        informa cuál falta (igual que si el API no lo hubiera devuelto).
        """
        resultado = []
        for buscado in buscados:
            for elemento in elementos:
                if elemento[campo] == buscado:
                    resultado.append(elemento)
                    break
        return resultado

    @staticmethod
    def _parametro(parametros, nombre: str) -> str:
        for clave, valor in parametros:
            if clave == nombre:
                return str(valor)
        raise ValueError(f"falta el parámetro {nombre!r}")

    @staticmethod
    def _entero(operacion: str, texto: str) -> int:
        try:
            return int(texto)
        except ValueError as e:
            raise ErrorRed(operacion, f"id de sala no numérico: {texto!r}") from e

    @staticmethod
    def _id_seguro(operacion: str, id_cripta: str) -> str:
        """El id se usa como nombre de carpeta: solo letras, números, '-' y '_'."""
        if id_cripta == "":
            raise ErrorRed(operacion, "id de cripta vacío")
        for caracter in id_cripta:
            if not (caracter.isalnum() or caracter in "-_"):
                raise ErrorRed(operacion, f"id de cripta no válido: {id_cripta!r}")
        return id_cripta